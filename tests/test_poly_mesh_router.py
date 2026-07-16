# -*- coding: utf-8 -*-
from fusion_hero_os.core.poly_mesh_router import (
    _pick_tier,
    load_catalog,
    route,
    assert_not_local_dual_start,
)


def test_prefer_l3_over_l1():
    chosen, status = _pick_tier(
        ["L1_mainframe", "L3_cluster"],
        {"L1_mainframe", "L3_cluster"},
        force_cluster=False,
        prefer_high=True,
    )
    assert chosen == "L3_cluster"
    assert status == "routed"


def test_force_cluster_blocks_without_l3():
    chosen, status = _pick_tier(
        ["L3_cluster", "L1_mainframe"],
        {"L1_mainframe"},
        force_cluster=True,
        prefer_high=True,
    )
    assert chosen is None
    assert status == "blocked_cluster_required"


def test_force_cluster_routes_to_l3():
    chosen, status = _pick_tier(
        ["L3_cluster", "L1_mainframe"],
        {"L1_mainframe", "L3_cluster"},
        force_cluster=True,
        prefer_high=True,
    )
    assert chosen == "L3_cluster"
    assert status == "cluster_routed"


def test_catalog_force_flags():
    cat = load_catalog()
    train = (cat.get("inhouse") or {}).get("fusion-stability-train") or {}
    assert train.get("force_cluster") is True
    assert train.get("placement") == "L3_cluster"


def test_assert_local_denies_training():
    # May be blocked or must-run-on-cluster depending on GKE probe
    r = assert_not_local_dual_start("fusion-stability-train")
    # Never allow free dual local start for training
    if r.get("decision", {}).get("gke_live"):
        assert r.get("allowed") is False
        assert r.get("run_on") == "L3_cluster" or "cluster" in str(r.get("reason", "")).lower()
    else:
        assert r.get("allowed") is False
