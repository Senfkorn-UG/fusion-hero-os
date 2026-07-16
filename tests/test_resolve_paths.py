# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "workstation"))

from resolve_paths import _deep_merge, resolve_paths  # noqa: E402


def test_deep_merge_overlays_nested_keys(tmp_path: Path):
    base = {"tailscale": {"nodes": {"mainframe": {"magicdns": "device.example.ts.net"}}}}
    overlay = {"tailscale": {"nodes": {"mainframe": {"hostname": "real-host"}}}}
    merged = _deep_merge(base, overlay)
    assert merged["tailscale"]["nodes"]["mainframe"]["magicdns"] == "device.example.ts.net"
    assert merged["tailscale"]["nodes"]["mainframe"]["hostname"] == "real-host"


def test_resolve_paths_without_local(tmp_path: Path):
    ws = tmp_path / "workstation"
    ws.mkdir()
    (ws / "paths.json").write_text(json.dumps({"version": "1"}), encoding="utf-8")
    data = resolve_paths(ws)
    assert data["version"] == "1"


def test_resolve_paths_with_local_overlay(tmp_path: Path):
    ws = tmp_path / "workstation"
    ws.mkdir()
    (ws / "paths.json").write_text(
        json.dumps({"tailscale": {"tailnet": "public.ts.net"}}),
        encoding="utf-8",
    )
    (ws / "paths.local.json").write_text(
        json.dumps({"tailscale": {"tailnet": "private.ts.net"}}),
        encoding="utf-8",
    )
    data = resolve_paths(ws)
    assert data["tailscale"]["tailnet"] == "private.ts.net"
