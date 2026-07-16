# -*- coding: utf-8 -*-
"""Poly-mesh algorithm orchestrator — coherence and waves."""
from __future__ import annotations

from fusion_hero_os.core.poly_mesh_orchestrator import (
    coherence_score,
    plan_only,
)


def test_plan_has_sole_authority():
    plan = plan_only()
    assert plan["sole_authority"] == "poly_mesh_router"
    assert plan["orchestrator"] == "poly_mesh_orchestrator"
    assert "algorithms" in plan
    assert "waves" in plan
    assert "coherence" in plan


def test_coherence_structure():
    plan = plan_only()
    coh = coherence_score(plan)
    assert 0 <= coh["score"] <= 100
    assert coh["grade"] in ("perfect", "excellent", "good", "degraded", "broken", "empty")
    assert "checks" in coh


def test_waves_ordered():
    plan = plan_only()
    waves = plan["waves"]
    assert waves[0]["name"] == "control_plane_l1"
    assert waves[2]["name"] == "force_cluster_l3"


def test_no_force_cluster_on_l1_in_plan():
    plan = plan_only()
    for a in plan.get("algorithms") or []:
        if a.get("force_cluster") and a.get("chosen") == "L1_mainframe":
            # must be denied dual-start
            assert a.get("deny_local_dual_start") or str(a.get("status", "")).startswith(
                "blocked"
            )
