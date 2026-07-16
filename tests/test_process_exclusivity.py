"""Tests für globale Prozess-Exklusivität."""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_CODE = _ROOT / "03_Code"
_DASHBOARD = _CODE / "Dashboard"
_PE_PATH = _CODE / "core" / "process_exclusivity.py"

for p in (_CODE, _DASHBOARD):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_process_exclusivity():
    """Frisch laden — vermeidet sys.modules-Kollisionen in der Voll-Suite."""
    spec = importlib.util.spec_from_file_location("_test_process_exclusivity", _PE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _use_temp_lock_dir(tmp_path: Path, monkeypatch, pe):
    lock_root = tmp_path / "locks"
    monkeypatch.setenv("FUSION_PROCESS_LOCK_DIR", str(lock_root))
    monkeypatch.setenv("FUSION_PROCESS_EXCLUSIVITY", "1")
    monkeypatch.setattr(pe, "_thread_locks", {}, raising=False)
    monkeypatch.setattr(pe, "_held_keys", set(), raising=False)
    monkeypatch.setattr(pe, "_hold_depth", {}, raising=False)
    monkeypatch.setattr(pe, "_hold_thread", {}, raising=False)
    pe.lock_dir()


@pytest.fixture
def pe(tmp_path, monkeypatch):
    mod = _load_process_exclusivity()
    _use_temp_lock_dir(tmp_path, monkeypatch, mod)
    yield mod


def test_try_acquire_and_release_reentrant(pe):
    """Derselbe Thread darf denselben Key verschachtelt sperren (reentrant)."""
    first = pe.try_acquire("test:resource")
    assert first.ok is True
    second = pe.try_acquire("test:resource")
    assert second.ok is True
    assert second.reason == "reentrant"
    assert pe.release("test:resource") is True
    assert pe.is_held("test:resource") is True
    assert pe.release("test:resource") is True
    assert pe.is_held("test:resource") is False
    third = pe.try_acquire("test:resource")
    assert third.ok is True
    assert third.reason != "reentrant"
    pe.release("test:resource")


def test_exclusive_context_manager(pe):
    with pe.exclusive("ctx:key") as lock:
        assert lock.ok is True
        with pe.exclusive("ctx:key") as inner:
            assert inner.ok is True
            assert inner.reason == "reentrant"
        assert pe.is_held("ctx:key") is True
    after = pe.try_acquire("ctx:key")
    assert after.ok is True
    assert after.reason != "reentrant"
    pe.release("ctx:key")


def test_disabled_mode_allows_parallel(pe, monkeypatch):
    monkeypatch.setenv("FUSION_PROCESS_EXCLUSIVITY", "0")
    a = pe.try_acquire("free:key")
    b = pe.try_acquire("free:key")
    assert a.ok is True
    assert b.ok is True
    pe.release("free:key")
    pe.release("free:key")


def test_stale_lock_cleanup(pe, tmp_path, monkeypatch):
    path = pe._lock_path("stale:key")
    payload = {
        "key": "stale:key",
        "pid": 999999999,
        "acquired_at": time.time() - 10_000,
        "ttl_sec": 1,
    }
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    assert path.exists()
    data = pe._read_lock_file(path)
    assert data is not None
    assert pe._is_stale(data) is True
    removed = pe.cleanup_stale()
    assert removed >= 1
    assert not path.exists()
    result = pe.try_acquire("stale:key")
    assert result.ok is True
    pe.release("stale:key")


def test_thread_parallel_blocks(pe):
    results: list[bool] = []

    def worker():
        with pe.exclusive("thread:key") as lock:
            results.append(lock.ok)
            time.sleep(0.05)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    assert results.count(True) == 1
    assert results.count(False) == 1


def test_status_reports_locks(pe):
    pe.try_acquire("status:key", owner="pytest")
    st = pe.status()
    assert st["enabled"] is True
    assert "status:key" in st["held_in_process"]
    assert st["pid"] == os.getpid()
    pe.release("status:key")
