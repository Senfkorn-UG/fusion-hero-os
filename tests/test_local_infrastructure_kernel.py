# -*- coding: utf-8 -*-
"""Tests fuer local_infrastructure_kernel (Vertrag v1.0)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "src" / "normal_os" / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from local_infrastructure_kernel import (  # noqa: E402
    CONTRACT_VERSION,
    MODULE_ID,
    evaluate,
    is_available,
    load_thresholds,
    run_cycle,
    status,
)


def test_module_is_available():
    assert is_available() is True


def test_status_has_contract_fields():
    info = status()
    assert info["available"] is True
    assert info["module"] == MODULE_ID
    assert info["contract_version"] == CONTRACT_VERSION
    assert "probe_targets" in info


def test_load_thresholds_has_metrics():
    cfg = load_thresholds()
    assert "metrics" in cfg
    assert "ram_util_pct" in cfg["metrics"]


def test_evaluate_ok_on_synthetic_probe():
    synthetic = {
        "substrate": {
            "ram_util_pct": 40.0,
            "disk_c_util_pct": 50.0,
            "tailscale_online": True,
        },
        "services": {
            "service_dashboard": {"online": True},
            "service_hero_docs": {"online": True},
            "service_bridge": {"online": True},
        },
    }
    result = evaluate(synthetic)
    assert result["escalation"]["level"] == "ok"
    assert result["contract_version"] == CONTRACT_VERSION


def test_evaluate_critical_ram():
    synthetic = {
        "substrate": {"ram_util_pct": 95.0, "disk_c_util_pct": 50.0, "tailscale_online": True},
        "services": {},
    }
    result = evaluate(synthetic)
    assert result["escalation"]["level"] == "critical"
    assert "stop_llama_server" in result["escalation"]["actions"]


def test_evaluate_offline_dashboard_is_alert():
    synthetic = {
        "substrate": {"ram_util_pct": 40.0, "disk_c_util_pct": 50.0, "tailscale_online": True},
        "services": {"service_dashboard": {"online": False}},
    }
    result = evaluate(synthetic)
    assert result["escalation"]["level"] == "alert"


def test_run_cycle_writes_state(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_LOCAL_KERNEL_STATE", str(tmp_path))
    out = run_cycle(timeout=0.5, apply_actions=False)
    assert out["available"] is True
    assert (tmp_path / "status.json").exists()
    saved = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert saved["module"] == MODULE_ID
    assert "probe" in saved
    assert "escalation" in saved


def test_contract_file_exists():
    contract = ROOT / "workstation" / "contracts" / "local_infrastructure_kernel.v1.json"
    assert contract.exists()
    data = json.loads(contract.read_text(encoding="utf-8"))
    assert data["module_id"] == MODULE_ID
    assert data["contract_version"] == CONTRACT_VERSION
