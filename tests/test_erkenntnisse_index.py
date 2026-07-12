# -*- coding: utf-8 -*-
"""Tests für den v8.3 Erkenntnis-Index (docs/v8/erkenntnisse_index.yaml)
und sein CI-Gate scripts/check_erkenntnisse_index.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "docs" / "v8" / "erkenntnisse_index.yaml"
GATE = REPO_ROOT / "scripts" / "check_erkenntnisse_index.py"


def _index() -> dict:
    return yaml.safe_load(INDEX.read_text(encoding="utf-8")) or {}


def test_index_exists_and_parses():
    assert INDEX.exists()
    data = _index()
    assert data.get("docs"), "Index ohne docs-Einträge"


def test_all_indexed_docs_exist():
    missing = [
        d["path"] for d in _index()["docs"] if not (REPO_ROOT / d["path"]).exists()
    ]
    assert not missing, f"Indexierte Docs fehlen: {missing}"


def test_recent_v82_erkenntnisse_indexed():
    """Die jüngsten Erkenntnis-Docs (Tarnkappe, Tails, Android) sind erfasst."""
    paths = {d["path"] for d in _index()["docs"]}
    for expected in (
        "docs/Tarnkappe_Cloak_Practical_Guide_v8.2.md",
        "docs/Tails_as_Ultimate_Tarnkappe_v8.2.md",
        "docs/android/Heroic-Extension-Node-NonRoot-v1.0.md",
        "docs/architecture/2026-07-09-three-mesh-heroic-fusion-android.md",
        "docs/v8/ERKENNTNISSE_LETZTE_TAGE_2026-07-05.md",
    ):
        assert expected in paths, f"nicht indexiert: {expected}"


def test_conflicts_all_resolved():
    conflicts = _index().get("resolved_conflicts") or []
    assert conflicts, "keine Konflikt-Auflösungen dokumentiert"
    open_ = [c["id"] for c in conflicts if c.get("state") != "resolved"]
    assert not open_, f"offene Widersprüche: {open_}"
    ids = {c["id"] for c in conflicts}
    # Die drei in der v8.3-Konsolidierung aufgelösten Widersprüche
    for expected in ("bestversion-vs-ascension", "android-root-vs-nonroot", "root-v7x-duplikate"):
        assert expected in ids, f"Konflikt-Auflösung fehlt: {expected}"


def test_root_v7x_files_are_redirect_stubs():
    """Die Root-Kopien der v7.x-Docs sind Stubs; Volltexte liegen im Archiv."""
    for fname in (
        "FUSION_HERO_OS_v7.4_COMPLETE_DELTA_SUMMARY.md",
        "FUSION_HERO_OS_v7.5_MASTER_UNIFIED.md",
        "Fusion_MasterSeed_v7.11.md",
    ):
        root_file = REPO_ROOT / fname
        archive_file = REPO_ROOT / "docs" / "99_archive" / fname
        assert root_file.exists() and archive_file.exists()
        root_text = root_file.read_text(encoding="utf-8")
        assert "Redirect-Stub" in root_text, f"{fname}: Root-Kopie ist kein Stub"
        assert len(archive_file.read_text(encoding="utf-8")) > len(root_text), (
            f"{fname}: Archiv-Kopie ist kein Volltext"
        )


def test_gate_script_passes():
    proc = subprocess.run(
        [sys.executable, str(GATE)], cwd=REPO_ROOT, capture_output=True, text=True
    )
    assert proc.returncode == 0, f"Gate rot:\n{proc.stdout}\n{proc.stderr}"
    assert "[OK]" in proc.stdout


def test_summary_via_layer_registry():
    from fusion_hero_os.core.layer_registry import erkenntnisse_summary

    summary = erkenntnisse_summary()
    assert summary["ok"] is True
    assert summary["doc_count"] >= 15
    assert summary["open_conflicts"] == 0
    assert not summary["missing_files"]
