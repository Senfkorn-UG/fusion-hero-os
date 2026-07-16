# -*- coding: utf-8 -*-
"""
Repo-Spiegelung + OS-Daemon-Korrektur (ohne Mauseingabe).
Erkennt Drift, korrigiert auf Dateisystem/Git-Ebene, protokolliert alles.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.repo_structure_registry import repo_root, scan_structure

_INTERVAL = float(os.getenv("FUSION_REPO_MIRROR_INTERVAL_SEC", "45"))
_AUTO_CORRECT = os.getenv("FUSION_REPO_MIRROR_AUTO_CORRECT", "1") == "1"
_STATE = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os"))) / "repo_mirror"


@dataclass
class CorrectionEvent:
    ts: float
    action: str
    target: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RepoMirrorCorrectionDaemon:
    def __init__(self) -> None:
        self._state_dir = _STATE
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._state_dir / "golden_manifest.json"
        self._log_path = self._state_dir / "corrections.jsonl"
        self._status_path = self._state_dir / "status.json"
        self._running = False
        self._ticks = 0
        self._last_corrections: List[CorrectionEvent] = []

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo_root()), *args],
            capture_output=True, text=True, timeout=30,
        )

    def _ensure_golden_manifest(self, scan: Dict[str, Any]) -> None:
        if self._manifest_path.exists():
            return
        self._manifest_path.write_text(
            json.dumps({"tree_hash": scan["tree_hash"], "root": scan["root"], "created_at": time.time()}, indent=2),
            encoding="utf-8",
        )

    def _detect_drift(self, scan: Dict[str, Any]) -> Dict[str, Any]:
        golden = {}
        if self._manifest_path.exists():
            try:
                golden = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        tree_drift = golden.get("tree_hash") != scan.get("tree_hash")
        git_dirty: List[str] = []
        r = self._git("status", "--porcelain")
        if r.returncode == 0 and r.stdout.strip():
            git_dirty = [ln.strip() for ln in r.stdout.strip().splitlines()[:50]]
        return {
            "tree_hash": scan.get("tree_hash"),
            "golden_hash": golden.get("tree_hash"),
            "tree_drift": tree_drift,
            "git_dirty_count": len(git_dirty),
            "git_dirty_sample": git_dirty[:12],
        }

    def _apply_corrections(self, drift: Dict[str, Any]) -> List[CorrectionEvent]:
        events: List[CorrectionEvent] = []
        if not _AUTO_CORRECT:
            return events

        for line in drift.get("git_dirty_sample", []):
            if len(line) < 4:
                continue
            path = line[3:].strip().split(" -> ")[-1].strip()
            if not path or path.startswith(".."):
                continue
            # Nur tracked modified/deleted — keine untracked löschen
            if line.startswith("??"):
                continue
            r = self._git("checkout", "--", path)
            ev = CorrectionEvent(
                ts=time.time(),
                action="git_checkout_restore",
                target=path,
                ok=r.returncode == 0,
                detail=(r.stderr or r.stdout or "")[:200],
            )
            events.append(ev)
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")

        if drift.get("tree_drift"):
            try:
                root = repo_root()
                manifest = root / ".fusion" / "mesh" / "fractal" / "manifest.json"
                if manifest.exists():
                    r = subprocess.run(
                        ["python", str(root / "fractal_mainframe_mesh.py"), "save"],
                        cwd=str(root), capture_output=True, text=True, timeout=120,
                    )
                    ev = CorrectionEvent(
                        ts=time.time(),
                        action="fractal_resync",
                        target=str(manifest),
                        ok=r.returncode == 0,
                        detail=(r.stderr or r.stdout or "")[:200],
                    )
                    events.append(ev)
                    with self._log_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
            except Exception as exc:
                events.append(CorrectionEvent(
                    ts=time.time(), action="fractal_resync", target="fractal_mainframe_mesh",
                    ok=False, detail=str(exc)[:200],
                ))
        return events

    def tick(self) -> Dict[str, Any]:
        scan = scan_structure()
        self._ensure_golden_manifest(scan)
        drift = self._detect_drift(scan)
        corrections = self._apply_corrections(drift) if drift.get("git_dirty_count") or drift.get("tree_drift") else []
        self._last_corrections = corrections
        self._ticks += 1

        status = {
            "daemon": "repo_mirror_correction",
            "ts": time.time(),
            "ticks": self._ticks,
            "auto_correct": _AUTO_CORRECT,
            "repo_root": str(repo_root()),
            "scan": {k: scan[k] for k in ("tree_hash", "file_count", "dir_count", "layers") if k in scan},
            "drift": drift,
            "corrections_last": [c.to_dict() for c in corrections],
            "mirror_mode": "os_daemon_no_mouse",
        }
        self._status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
        return status

    def status(self) -> Dict[str, Any]:
        if self._status_path.exists():
            try:
                return json.loads(self._status_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "daemon": "repo_mirror_correction",
            "running": self._running,
            "ticks": self._ticks,
            "interval_sec": _INTERVAL,
        }

    def start_background(self) -> bool:
        if self._running:
            return False
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False


_daemon: Optional[RepoMirrorCorrectionDaemon] = None


def get_mirror_daemon() -> RepoMirrorCorrectionDaemon:
    global _daemon
    if _daemon is None:
        _daemon = RepoMirrorCorrectionDaemon()
    return _daemon