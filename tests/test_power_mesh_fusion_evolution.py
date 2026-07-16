# -*- coding: utf-8 -*-
from fusion_hero_os.core.power_mesh_fusion_evolution import (
    load_config,
    scan_strata,
    run_evolution,
    status,
    fitness,
    _default_genome,
)


def test_config_and_strata():
    cfg = load_config()
    assert cfg.get("direction") == "bottom_up"
    strata = scan_strata(cfg)
    assert len(strata) >= 6
    ids = [s.id for s in strata]
    assert "S0" in ids and "S6" in ids
    # core evidence should largely exist in this repo
    s0 = next(s for s in strata if s.id == "S0")
    assert s0.coverage > 0.5


def test_status():
    st = status()
    assert st.get("ok")
    assert st.get("direction") == "bottom_up"
    assert st.get("baseline_fitness", 0) > 0


def test_short_evolution():
    r = run_evolution(generations=8, seed=42)
    assert r.ok
    assert r.generations == 8
    assert 0.0 <= r.best_fitness <= 1.0
    assert len(r.trajectory) == 8
    assert r.mesh_score >= 0.0
    assert r.dissertation_score >= 0.0
    # fitness non-decreasing elite path is not guaranteed on flat landscape;
    # at least initial and best defined
    assert r.initial_fitness >= 0.0


def test_fitness_normalized():
    strata = scan_strata()
    g = _default_genome(strata)
    fit, comps, tau = fitness(g, strata, {})
    assert 0.0 <= fit <= 1.0
    assert 0.0 <= tau <= 1.0
    assert "stratum_coverage" in comps
