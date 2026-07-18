# -*- coding: utf-8 -*-
"""Tests für register_hyper4d_node() + bifurcal_sync() (Layer-ω-Direktive)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_registry_module():
    spec = importlib.util.spec_from_file_location(
        "tailscale_mesh_registry", REPO_ROOT / "tailscale_mesh_registry.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["tailscale_mesh_registry"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_register_hyper4d_node_writes_registry(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("FUSION_HYPER4D_DIR", str(tmp_path))
    reg = _load_registry_module()
    result = reg.register_hyper4d_node()
    assert result["ok"] is True
    assert result["tag"] == "tag:fusion-hyper4d-node"
    assert set(result["capabilities"]) == {
        "hyper4d_coevolution",
        "layer_omega_fixedpoint",
        "autopoietic_morphing",
        "bifurcal_sync",
    }
    assert (tmp_path / "registry.json").is_file()
    status = reg.hyper4d_status()
    assert status["registered"] is True
    assert 0.0 <= status["phase_sec"] < 16.0  # Direktive §3: Phase 0–15s


def test_bifurcal_sync_pull_and_push(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("FUSION_HYPER4D_DIR", str(tmp_path))
    reg = _load_registry_module()
    reg.register_hyper4d_node()
    first = reg.bifurcal_sync()
    second = reg.bifurcal_sync()
    # Pfad A: beide Shared-Configs wurden gezogen
    assert set(first["pull"]) == {"mesh_connectors.yaml", "fusion_unified.yaml"}
    assert first["pull"]["mesh_connectors.yaml"]["present"] is True
    assert first["pull"]["mesh_connectors.yaml"]["sha256"]
    # Pfad B: Push aktualisiert Phase + Feedback-Stärke, Generation wächst
    assert second["generation"] > first["generation"]
    # co-evolutionär gedämpft: wächst, bleibt unter Ceiling 1.0
    assert 0.0 < first["push"]["feedback_strength"] <= 1.0
    assert second["push"]["feedback_strength"] >= first["push"]["feedback_strength"]
    assert second["status"]["fixedpoint"]["anchor"] == "identity-fixpoint"


def test_hyper4d_status_unregistered_is_honest(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("FUSION_HYPER4D_DIR", str(tmp_path / "leer"))
    reg = _load_registry_module()
    status = reg.hyper4d_status()
    assert status["registered"] is False
    assert status["feedback_strength"] == 0.0
    assert status["generation"] == 0


def test_mesh_connectors_declares_hyper4d_node_type():
    import yaml

    data = yaml.safe_load((REPO_ROOT / "mesh_connectors.yaml").read_text(encoding="utf-8"))
    nt = data["node_types"]["hyper4d-coevo"]
    assert nt["tailscale_tag"] == "tag:fusion-hyper4d-node"
    assert "bifurcal_sync" in nt["capabilities"]
