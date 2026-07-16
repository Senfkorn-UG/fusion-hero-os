# -*- coding: utf-8 -*-
"""Headset multi-layer — one ACTIVE level, clear banner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from fusion_hero_os.core import headset_layers as hl


@pytest.fixture()
def isolated_state(monkeypatch, tmp_path):
    path = tmp_path / "headset_layers.json"
    monkeypatch.setattr(hl, "STATE_PATH", path)
    # no real audio routing in unit tests
    monkeypatch.setattr(
        hl,
        "apply_active_route",
        lambda: {"ok": True, "active": hl.load_state()["active"], "skipped": True},
    )
    return path


def test_default_state_has_active(isolated_state):
    st = hl.status()
    assert st["active"] in hl.LAYERS
    assert "ACTIVE" in st["banner"]
    assert st["banner_one_line"].startswith("HEADSET ACTIVE LEVEL")


def test_set_active_l2(isolated_state):
    out = hl.set_active("L2_phone", apply_route=True)
    assert out["active"] == "L2_phone"
    assert out["active_short"] == "L2"
    assert "PHONE RELAY" in out["banner"]
    assert "L2:ACTIVE" in out["banner"].replace(" ", "")


def test_aliases(isolated_state):
    assert hl.set_active("phone")["active"] == "L2_phone"
    assert hl.set_active("local")["active"] == "L1_local"
    assert hl.set_active("3")["active"] == "L3_comaedchen"
    assert hl.set_active("hyperraum")["active"] == "L4_hyperraum"


def test_multi_layer_armed(isolated_state):
    hl.activate_stack(active="L2_phone", enable_all=True)
    st = hl.status()
    assert set(st["enabled"]) == set(hl.LAYER_ORDER)
    assert st["active"] == "L2_phone"
    # all armed markers present
    for lid in hl.LAYER_ORDER:
        short = hl.LAYERS[lid]["short"]
        assert short in st["banner"]


def test_cannot_disable_last(isolated_state):
    hl.set_active("L1_local")
    st = hl.load_state()
    st["enabled"] = ["L1_local"]
    hl.save_state(st)
    out = hl.disable("L1_local")
    assert out.get("ok") is False


def test_banner_clarity(isolated_state):
    hl.set_active("L4_hyperraum")
    b = hl.banner()
    assert "HYPERRAUM" in b
    assert "ACTIVE LEVEL" in b
    assert "L4" in b
