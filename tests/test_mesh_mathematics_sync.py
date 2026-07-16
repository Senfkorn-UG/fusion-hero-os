"""Tests for mesh_mathematics_sync Google path."""
from __future__ import annotations

import json
from pathlib import Path

import mesh_mathematics_sync as mms


def test_build_mathematics_manifest_lists_core_artifacts():
    man = mms.build_mathematics_manifest()
    assert man["ok"] is True
    assert man["artifact_count"] >= 5
    rels = {e["relpath"] for e in man["entries"]}
    assert "02_Mathematik/hero-guide_geltungsstand.json" in rels
    assert "fusion_hero_os/core/heroic_math_engine.py" in rels
    assert "fusion_hero_os/core/quantum_cognition.py" in rels
    assert len(man["tree_hash"]) == 64


def test_mirror_mathematics_to_gdrive_no_mount(monkeypatch):
    monkeypatch.setattr(
        "mesh_file_share.resolve_gdrive_offload_root",
        lambda: None,
        raising=False,
    )
    out = mms.mirror_mathematics_to_gdrive()
    assert out["ok"] is False
    assert out["error"] == "no_google_drive_mount"


def test_mirror_mathematics_to_gdrive_copies_files(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    math_dir = repo / "02_Mathematik"
    math_dir.mkdir()
    (math_dir / "hero-guide_geltungsstand.json").write_text("[]", encoding="utf-8")
    core = repo / "fusion_hero_os" / "core"
    core.mkdir(parents=True)
    (core / "heroic_math_engine.py").write_text("# math", encoding="utf-8")

    gdrive = tmp_path / "gdrive"
    gdrive.mkdir()

    monkeypatch.setenv("FUSION_HERO_ROOT", str(repo))
    # Nur die erzeugten Testdateien spiegeln
    monkeypatch.setattr(mms, "MATH_ARTIFACT_PATHS", (
        "02_Mathematik/hero-guide_geltungsstand.json",
        "fusion_hero_os/core/heroic_math_engine.py",
    ))

    out = mms.mirror_mathematics_to_gdrive(gdrive_root=gdrive)
    assert out["ok"] is True
    assert out["copied_count"] == 2
    dest = gdrive / "mesh" / "mathematik"
    assert (dest / "mathematics_manifest.json").exists()
    manifest = json.loads((dest / "mathematics_manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifact_count"] == 2


def test_sync_mathematics_google_manifest_only():
    out = mms.sync_mathematics_google(include_gdrive=False)
    assert out["ok"] is True
    assert "manifest" in out
    assert "google_drive" not in out
