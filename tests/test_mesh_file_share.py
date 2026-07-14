"""Tests for mesh_file_share phone mirror."""
from __future__ import annotations

import json
from pathlib import Path

import mesh_file_share as mfs


def test_build_file_manifest_has_phone_urls():
    manifest = mfs.build_file_manifest(base_url="http://test-host:8088")
    assert manifest["ok"] is True
    assert manifest["file_count"] >= 0
    assert manifest["phone_portal_url"] == "http://test-host:8088/mesh/files/phone"
    assert manifest["phone_manifest_url"] == "http://test-host:8088/mesh/files/manifest"


def test_resolve_safe_path_blocks_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_HERO_ROOT", str(tmp_path))
    (tmp_path / "docs").mkdir()
    safe = tmp_path / "docs" / "readme.md"
    safe.write_text("hello", encoding="utf-8")

    zones = [{"id": "docs", "label": "Docs", "path": "docs", "max_depth": 1, "max_files": 10}]
    monkeypatch.setattr(mfs, "get_file_share_config", lambda: {
        "enabled": True,
        "zones": zones,
        "phone_hostname_aliases": [],
        "serve_port": 8088,
        "max_file_bytes": 1024 * 1024,
    })

    ok, err = mfs.resolve_safe_path("docs", "docs/readme.md")
    assert err is None
    assert ok == safe

    bad, err2 = mfs.resolve_safe_path("docs", "../secret.txt")
    assert bad is None
    assert err2 is not None


def test_render_phone_portal_html():
    manifest = {
        "file_count": 1,
        "tree_hash": "abc123",
        "phone_manifest_url": "http://x/mesh/files/manifest",
        "zones": [{"id": "docs", "label": "Docs"}],
        "entries": [{
            "zone": "docs",
            "relpath": "docs/a.md",
            "download_url": "http://x/mesh/files/get/docs/docs/a.md",
            "size_bytes": 100,
        }],
        "phone_peer": {"hostname": "redmi-note-13-pro-5g"},
    }
    html = mfs.render_phone_portal_html(manifest)
    assert "Mesh Files" in html
    assert "redmi-note-13-pro-5g" in html
    assert "docs/a.md" in html


def test_receive_filedrop_requires_token(tmp_path, monkeypatch):
    monkeypatch.setenv("MESH_DROP_TOKEN", "secret")
    monkeypatch.setattr(mfs, "get_filedrop_config", lambda: {
        "enabled": True,
        "inbound": tmp_path / "in",
        "outbound": tmp_path / "out",
        "repo_drops": [],
        "gdrive_subpaths": {},
        "journal_ingest_on_sync": False,
        "android_subdir": "android",
    })
    monkeypatch.setattr(mfs, "resolve_gdrive_offload_root", lambda: None)
    bad = mfs.receive_filedrop("x.txt", b"hi", token="wrong")
    assert bad["ok"] is False
    good = mfs.receive_filedrop("x.txt", b"hello", token="secret", source="android")
    assert good["ok"] is True
    assert (tmp_path / "in" / "android").exists()


def test_mirror_to_gdrive_no_mount(monkeypatch):
    monkeypatch.setattr(mfs, "resolve_gdrive_offload_root", lambda: None)
    out = mfs.mirror_to_gdrive({"tree_hash": "abc"})
    assert out["ok"] is False


def test_save_file_manifest_writes_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_HERO_ROOT", str(tmp_path))
    files_root = tmp_path / ".fusion" / "mesh" / "files"
    monkeypatch.setattr(mfs, "FILES_ROOT", files_root)
    monkeypatch.setattr(mfs, "MANIFEST_PATH", files_root / "manifest.json")
    monkeypatch.setattr(mfs, "get_file_share_config", lambda: {
        "enabled": True,
        "zones": [],
        "phone_hostname_aliases": [],
        "serve_port": 8088,
        "max_file_bytes": 1024 * 1024,
    })
    out = mfs.save_file_manifest(base_url="http://test:8088")
    assert out["ok"] is True
    assert (files_root / "manifest.json").exists()
    cached = json.loads((files_root / "manifest.json").read_text(encoding="utf-8"))
    assert cached["base_url"] == "http://test:8088"
