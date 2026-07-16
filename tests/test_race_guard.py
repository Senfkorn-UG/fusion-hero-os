"""Tests for fusion_hero_os.core.race_guard — concurrent-safe IO."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from fusion_hero_os.core.race_guard import (
    FileLock,
    RaceConditionGuard,
    atomic_write_json,
    atomic_write_text,
    compare_and_swap_json,
    locked_atomic_write_json,
    race_stress_test,
)


def test_atomic_write_text_roundtrip(tmp_path: Path):
    p = tmp_path / "a.txt"
    atomic_write_text(p, "hello\n")
    assert p.read_text(encoding="utf-8") == "hello\n"
    assert not list(tmp_path.glob("*.tmp"))


def test_atomic_write_json_roundtrip(tmp_path: Path):
    p = tmp_path / "b.json"
    atomic_write_json(p, {"x": 1, "y": [2, 3]})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["x"] == 1
    assert data["y"] == [2, 3]


def test_file_lock_exclusive(tmp_path: Path):
    target = tmp_path / "c.json"
    order = []

    def holder():
        with FileLock(target, timeout=5.0):
            order.append("a-in")
            # hold long enough for waiter to block
            import time

            time.sleep(0.2)
            order.append("a-out")

    t = threading.Thread(target=holder)
    t.start()
    import time

    time.sleep(0.05)
    with FileLock(target, timeout=5.0):
        order.append("b-in")
        order.append("b-out")
    t.join(timeout=5)
    assert order[0] == "a-in"
    assert "a-out" in order
    assert order.index("a-out") < order.index("b-in")


def test_locked_atomic_write_json(tmp_path: Path):
    p = tmp_path / "d.json"
    locked_atomic_write_json(p, {"ok": True})
    assert json.loads(p.read_text(encoding="utf-8"))["ok"] is True


def test_compare_and_swap_generation(tmp_path: Path):
    p = tmp_path / "e.json"

    def mut1(cur):
        return {"v": 1}

    out1 = compare_and_swap_json(p, mut1)
    assert out1["_generation"] == 1

    def mut2(cur):
        assert cur is not None
        return {"v": cur.get("v", 0) + 1}

    out2 = compare_and_swap_json(p, mut2)
    assert out2["_generation"] == 2
    assert out2["v"] == 2


def test_race_stress_test_integrity(tmp_path: Path):
    p = tmp_path / "stress.json"
    result = race_stress_test(p, n_workers=6, n_writes_each=15)
    assert result["ok"] is True, result
    assert result["actual_generation"] == 6 * 15


def test_guard_stats(tmp_path: Path):
    g = RaceConditionGuard()
    g.write_json(tmp_path / "g.json", {"a": 1})
    assert g.stats["writes"] >= 1
    assert g.stats["locks"] >= 1
