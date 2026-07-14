"""Integration tests for suite → core merge."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CODE_CORE = Path(__file__).resolve().parents[1] / "03_Code" / "core"
_CODE = _CODE_CORE.parent
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
if str(_CODE_CORE) not in sys.path:
    sys.path.insert(0, str(_CODE_CORE))


def _load_core_module(name: str):
    """Load 03_Code/core module deterministically (avoid sys.modules cache pollution)."""
    path = _CODE_CORE / f"{name}.py"
    mod_name = f"_test_core_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_qb_qubo_shim_exports_springloop():
    from qb_qubo import springloop_energy, make_Q
    import numpy as np

    Q = make_Q(4)
    x = np.random.randint(0, 2, 4).astype(float)
    _, e = springloop_energy(Q, x, steps=3)
    assert isinstance(e, (float, np.floating))


def test_ghosthunt_hook_returns_coevo():
    from ghosthunt_hook import ghosthunt_hook

    snap, coevo = ghosthunt_hook("test-layer", context={"events": 5}, steps=3, verbose=False)
    assert "distance" in snap
    assert "emerged" in coevo
    assert "springloop_energy" in coevo


def test_suite_bridge_inventory():
    suite_bridge = _load_core_module("suite_bridge")
    inv = suite_bridge.suite_inventory()
    assert inv["total_py"] > 0
    names = {m["name"] for m in inv["modules"]}
    assert "layers" in names
    assert "qubo" in names


def test_suite_pipeline_status():
    suite_pipeline = _load_core_module("suite_pipeline")
    st = suite_pipeline.pipeline_status()
    assert st["layer_count"] == 8
    assert "00_middle" in st["layers"][0] or any("middle" in l for l in st["layers"])


def test_heroic_orchestration_apply_ghosthunt():
    heroic_orchestration = _load_core_module("heroic_orchestration")
    snap, coevo = heroic_orchestration.apply_ghosthunt_coevo("orch-test", steps=2)
    assert coevo.get("layer") == "orch-test"