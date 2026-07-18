"""Tests für multimodale Pseudohorkruxe + AutosaveDaemon."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from fusion_hero_os.core.pseudo_horcrux import (
    MODALITIES,
    AutosaveDaemon,
    PseudoHorcruxStore,
)

STATE = {"hero": "fusion", "level": 42, "mesh": ["cpu", "mem", "gpu", "qpu"], "zitter": 0.05}


def test_preserve_writes_all_modalities(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path, copies=2)
    manifest = store.preserve(STATE)
    assert manifest["generation"] == 1
    assert len(manifest["shards"]) == len(MODALITIES) * 2
    for modality in MODALITIES:
        assert (tmp_path / f"horcrux-{modality}-c0.hx").is_file()


def test_restore_roundtrip_and_generation_increments(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    store.preserve(STATE)
    m2 = store.preserve({**STATE, "level": 43})
    assert m2["generation"] == 2
    restored = store.restore()
    assert restored == {**STATE, "level": 43}


def test_restore_survives_corrupted_shard(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    store.preserve(STATE)
    # JSON-Shard zerstören → CSV/B64 müssen tragen
    json_shard = tmp_path / "horcrux-json-c0.hx"
    json_shard.write_text(json_shard.read_text(encoding="utf-8")[: 40], encoding="utf-8")
    report = store.integrity_report()
    assert report["restorable"] is True
    assert report["valid_shards"] == len(MODALITIES) - 1
    assert store.restore() == STATE


def test_restore_from_single_surviving_shard_each_modality(tmp_path: Path):
    for survivor in MODALITIES:
        store_dir = tmp_path / survivor
        store = PseudoHorcruxStore(store_dir)
        store.preserve(STATE)
        for modality in MODALITIES:
            if modality != survivor:
                (store_dir / f"horcrux-{modality}-c0.hx").unlink()
        assert store.restore() == STATE, f"Restore aus {survivor}-Shard fehlgeschlagen"


def test_tampered_payload_is_detected_by_checksum(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    store.preserve(STATE)
    csv_shard = tmp_path / "horcrux-csv-c0.hx"
    text = csv_shard.read_text(encoding="utf-8").replace('"fusion"', '"tampered"')
    csv_shard.write_text(text, encoding="utf-8")
    report = store.integrity_report()
    bad = [s for s in report["shards"] if s["file"] == "horcrux-csv-c0.hx"][0]
    assert bad["valid"] is False
    assert "Checksumme" in bad["error"]
    # restore ignoriert den manipulierten Shard
    assert store.restore() == STATE


def test_empty_store_restores_none(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    assert store.restore() is None
    assert store.integrity_report()["restorable"] is False


def test_concurrent_preserve_is_race_safe(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    n_workers, n_writes = 6, 5
    errors: list[str] = []
    barrier = threading.Barrier(n_workers, timeout=10.0)

    def writer(wid: int) -> None:
        try:
            barrier.wait()
            for i in range(n_writes):
                store.preserve({**STATE, "writer": wid, "i": i})
        except Exception as exc:  # noqa: BLE001
            errors.append(f"w{wid}: {exc}")

    threads = [threading.Thread(target=writer, args=(w,)) for w in range(n_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors
    report = store.integrity_report()
    # Generationszähler == Gesamtzahl Writes → kein Lost Update
    assert report["best_generation"] == n_workers * n_writes
    assert report["valid_shards"] == report["total_shards"]
    assert store.restore() is not None


def test_autosave_daemon_saves_on_dirty_and_interval(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    state = {"tick": 0}

    daemon = AutosaveDaemon(store, lambda: dict(state), interval=0.15, debounce=0.02)
    with daemon:
        state["tick"] = 1
        daemon.mark_dirty()
        deadline = time.monotonic() + 5.0
        while daemon.snapshot_stats()["saves"] < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
    stats = daemon.snapshot_stats()
    assert stats["saves"] >= 2  # dirty-Trigger + Intervall/Final-Save
    assert stats["errors"] == 0
    assert store.restore() == {"tick": 1}


def test_autosave_daemon_survives_provider_errors(tmp_path: Path):
    store = PseudoHorcruxStore(tmp_path)
    calls = {"n": 0}

    def provider():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("provider kaputt")
        return {"ok": True}

    daemon = AutosaveDaemon(store, provider, interval=0.05, debounce=0.0)
    with daemon:
        deadline = time.monotonic() + 5.0
        while daemon.snapshot_stats()["saves"] < 1 and time.monotonic() < deadline:
            time.sleep(0.02)
    stats = daemon.snapshot_stats()
    assert stats["errors"] >= 1
    assert stats["saves"] >= 1
    assert "provider kaputt" in stats["last_error"] or stats["saves"] >= 1
    assert store.restore() == {"ok": True}
