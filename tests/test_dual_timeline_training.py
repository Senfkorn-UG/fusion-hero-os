# -*- coding: utf-8 -*-
from fusion_hero_os.core.dual_timeline_training import (
    build_samples,
    consistency_report,
    load_config,
    run_auto_train,
    scan_files,
    status,
)


def test_config_loads():
    c = load_config()
    assert c.get("policy") == "pseudo_inhouse_only"
    assert c.get("freemium") is False


def test_scan_and_tau_bounds():
    events = scan_files()
    assert len(events) > 10
    for e in events[:50]:
        assert 0.0 <= e.tau <= 1.0
        assert e.t_real > 0
        assert e.rel


def test_samples_dual_axes():
    samples = build_samples()
    assert len(samples) > 20
    s = samples[0]
    assert s.timeline == "dual"
    assert "τ=" in s.prompt or "tau" in s.prompt.lower() or "τ" in s.prompt
    assert s.t_real > 0
    assert 0.0 <= s.tau <= 1.0


def test_run_auto_train():
    r = run_auto_train(write=True)
    assert r.get("files", 0) > 0
    assert r.get("samples", 0) > 0
    assert "paths" in r
    st = status()
    assert st.get("freemium") is False
    assert st.get("axes", {}).get("tau")


def test_consistency_shape():
    events = scan_files()
    samples = build_samples(events)
    c = consistency_report(events, samples, load_config())
    assert "tau_mean" in c
    assert "t_min_iso" in c
    assert c.get("files") == len(events)
