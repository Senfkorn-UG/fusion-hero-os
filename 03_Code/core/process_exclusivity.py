# -*- coding: utf-8 -*-
"""Globale Prozess-Exklusivität — nur ein Worker pro Ressourcen-Key gleichzeitig.

Hybrid aus In-Memory-Sperren (Threads) und Datei-Locks (Prozesse).
Regel: Niemals zweimal gleichzeitig am gleichen Prozess/Ressource arbeiten.
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

_registry_lock = threading.Lock()
_thread_locks: Dict[str, threading.RLock] = {}
_held_keys: set[str] = set()
# Reentranz-Tiefe pro Key: derselbe Thread darf denselben Key verschachtelt
# sperren (z.B. apply_command -> finalize -> push_room_to_server), ohne sich
# selbst auszusperren. Erst der aeusserste release() gibt Datei-Lock + Key frei.
_hold_depth: Dict[str, int] = {}


def enabled() -> bool:
    return os.getenv("FUSION_PROCESS_EXCLUSIVITY", "1") == "1"


def default_ttl_sec() -> float:
    try:
        return float(os.getenv("FUSION_PROCESS_LOCK_TTL_SEC", "300"))
    except ValueError:
        return 300.0


def lock_dir() -> Path:
    override = os.getenv("FUSION_PROCESS_LOCK_DIR", "").strip()
    root = Path(override) if override else Path.home() / ".fusion-hero-os" / "process_locks"
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_key(key: str) -> str:
    text = (key or "").strip()
    if not text:
        raise ValueError("process exclusivity key required")
    return re.sub(r"[^\w\-.:]+", "_", text)[:200]


def _lock_path(key: str) -> Path:
    file_key = normalize_key(key).replace(":", "_")
    return lock_dir() / f"{file_key}.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _is_stale(data: Dict[str, Any]) -> bool:
    pid = int(data.get("pid") or 0)
    acquired = float(data.get("acquired_at") or 0)
    ttl = float(data.get("ttl_sec") or default_ttl_sec())
    if time.time() - acquired > ttl:
        return True
    return not _pid_alive(pid)


def cleanup_stale() -> int:
    removed = 0
    for path in lock_dir().glob("*.lock"):
        data = _read_lock_file(path)
        if data and _is_stale(data):
            try:
                path.unlink(missing_ok=True)
                removed += 1
            except Exception:
                pass
    return removed


def _thread_lock(key: str) -> threading.RLock:
    with _registry_lock:
        if key not in _thread_locks:
            _thread_locks[key] = threading.RLock()
        return _thread_locks[key]


@dataclass
class AcquireResult:
    ok: bool
    key: str
    reason: str = ""
    holder_pid: Optional[int] = None
    holder_owner: str = ""


@dataclass
class ExclusivityStatus:
    enabled: bool
    lock_dir: str
    ttl_sec: float
    pid: int
    held_in_process: List[str] = field(default_factory=list)
    file_locks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "lock_dir": self.lock_dir,
            "ttl_sec": self.ttl_sec,
            "pid": self.pid,
            "held_in_process": list(self.held_in_process),
            "file_locks": list(self.file_locks),
            "stale_cleaned": cleanup_stale(),
        }


def _write_file_lock(path: Path, key: str, owner: str, ttl_sec: float) -> None:
    payload = {
        "key": key,
        "pid": os.getpid(),
        "tid": threading.get_ident(),
        "owner": owner or f"{socket.gethostname()}:{os.getpid()}",
        "acquired_at": time.time(),
        "ttl_sec": ttl_sec,
    }
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    finally:
        os.close(fd)


def _try_file_acquire(key: str, owner: str, ttl_sec: float) -> AcquireResult:
    path = _lock_path(key)
    for _ in range(3):
        try:
            _write_file_lock(path, key, owner, ttl_sec)
            return AcquireResult(ok=True, key=key)
        except FileExistsError:
            data = _read_lock_file(path)
            if data and _is_stale(data):
                try:
                    path.unlink(missing_ok=True)
                    continue
                except Exception:
                    pass
            holder_pid = int(data.get("pid") or 0) if data else None
            holder_owner = str(data.get("owner") or "") if data else ""
            return AcquireResult(
                ok=False,
                key=key,
                reason="held_by_other_process",
                holder_pid=holder_pid,
                holder_owner=holder_owner,
            )
        except Exception as exc:
            return AcquireResult(ok=False, key=key, reason=str(exc)[:120])
    return AcquireResult(ok=False, key=key, reason="retry_exhausted")


def _release_file(key: str) -> None:
    path = _lock_path(key)
    data = _read_lock_file(path)
    if data and int(data.get("pid") or 0) == os.getpid():
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def try_acquire(
    key: str,
    *,
    owner: str = "",
    ttl_sec: Optional[float] = None,
    blocking: bool = False,
    timeout_sec: float = 0.0,
) -> AcquireResult:
    """Sperre eine Ressource exklusiv. Muss mit release() oder exclusive() freigegeben werden."""
    norm = normalize_key(key)
    if not enabled():
        with _registry_lock:
            _held_keys.add(norm)
        return AcquireResult(ok=True, key=norm, reason="disabled")

    ttl = default_ttl_sec() if ttl_sec is None else ttl_sec
    deadline = time.time() + max(0.0, timeout_sec)
    mutex = _thread_lock(norm)

    while True:
        if mutex.acquire(blocking=blocking or timeout_sec > 0):
            # Reentranter Fall: dieser Thread haelt den Key bereits (RLock
            # liess uns durch und die Tiefe ist > 0) -> nur Tiefe erhoehen,
            # Datei-Lock gehoert uns schon.
            with _registry_lock:
                depth = _hold_depth.get(norm, 0)
                if depth > 0:
                    _hold_depth[norm] = depth + 1
                    return AcquireResult(ok=True, key=norm, reason="reentrant")
            file_result = _try_file_acquire(norm, owner, ttl)
            if file_result.ok:
                with _registry_lock:
                    _held_keys.add(norm)
                    _hold_depth[norm] = 1
                return file_result
            mutex.release()
            result = file_result
        else:
            result = AcquireResult(ok=False, key=norm, reason="held_by_other_thread")

        if not blocking and timeout_sec <= 0:
            return result
        if time.time() >= deadline:
            return result
        time.sleep(0.02)


def release(key: str) -> bool:
    norm = normalize_key(key)
    if not enabled():
        with _registry_lock:
            _held_keys.discard(norm)
            _hold_depth.pop(norm, None)
        return True

    with _registry_lock:
        if norm not in _held_keys:
            return False
        depth = _hold_depth.get(norm, 1)
        if depth > 1:
            # Verschachtelter (reentranter) release: nur Tiefe + RLock-Zaehler
            # verringern, Datei-Lock bleibt bestehen.
            _hold_depth[norm] = depth - 1
            nested = True
        else:
            _held_keys.discard(norm)
            _hold_depth.pop(norm, None)
            nested = False

    mutex = _thread_locks.get(norm)
    if nested:
        if mutex:
            try:
                mutex.release()
            except RuntimeError:
                pass
        return True

    _release_file(norm)
    if mutex:
        try:
            mutex.release()
        except RuntimeError:
            pass
    return True


@contextmanager
def exclusive(
    key: str,
    *,
    owner: str = "",
    ttl_sec: Optional[float] = None,
    blocking: bool = False,
    timeout_sec: float = 0.0,
) -> Iterator[AcquireResult]:
    result = try_acquire(
        key,
        owner=owner,
        ttl_sec=ttl_sec,
        blocking=blocking,
        timeout_sec=timeout_sec,
    )
    try:
        yield result
    finally:
        if result.ok:
            release(result.key)


def is_held(key: str) -> bool:
    norm = normalize_key(key)
    with _registry_lock:
        if norm in _held_keys:
            return True
    data = _read_lock_file(_lock_path(norm))
    return bool(data and not _is_stale(data))


def status() -> Dict[str, Any]:
    file_locks: List[Dict[str, Any]] = []
    for path in sorted(lock_dir().glob("*.lock")):
        data = _read_lock_file(path)
        if not data:
            continue
        entry = dict(data)
        entry["stale"] = _is_stale(data)
        entry["path"] = str(path)
        file_locks.append(entry)

    with _registry_lock:
        held = sorted(_held_keys)

    return ExclusivityStatus(
        enabled=enabled(),
        lock_dir=str(lock_dir()),
        ttl_sec=default_ttl_sec(),
        pid=os.getpid(),
        held_in_process=held,
        file_locks=file_locks,
    ).to_dict()


# Standard-Keys für dokumentierte Ressourcen
KEY_DASHBOARD = "dashboard:{port}"
KEY_WATCH_ROOM = "watch-room:{room_id}"
KEY_BG_SUPABASE = "bg:supabase-sync"
KEY_BG_WATCH_REALTIME = "bg:watch-realtime"
KEY_FADEN = "faden:{thread_id}"