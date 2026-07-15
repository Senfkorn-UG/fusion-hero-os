# -*- coding: utf-8 -*-
from fusion_hero_os.core.control_instances import (
    run_control_panel,
    status,
    list_instances,
    _parse_json_answer,
    _consensus,
    ControlResult,
)


def test_status_accuracy_force():
    st = status()
    assert st.get("ok")
    assert float(st.get("temperature", 1)) == 0.0
    assert len(list_instances()) >= 3
    # Gemini multi-slot + further providers registered
    ids = [i.get("id") for i in list_instances()]
    assert "control_gemini" in ids
    assert "control_gemini_flash" in ids
    assert "control_huggingface" in ids or "control_nvidia" in ids
    assert st.get("gemini_control_slots", 0) >= 2


def test_parse_json():
    d = _parse_json_answer('{"answer":"yes","confidence":90,"accuracy_self":88,"geltung":"Satz"}')
    assert d["answer"] == "yes"
    assert d["confidence"] == 90


def test_run_internal_control():
    r = run_control_panel(
        "Does deploy mean private in Fusion Hero OS ops vocabulary?",
        providers=["internal"],
    )
    assert r.instances_run >= 1
    assert r.instances_ok >= 1
    assert r.accuracy_force.get("temperature") == 0.0
    assert any(x.provider == "internal" and x.ok for x in r.results)


def test_consensus_majority():
    rs = [
        ControlResult("a", "grok", "g", True, answer="yes", confidence=90, accuracy_self=90),
        ControlResult("b", "claude", "c", True, answer="yes", confidence=85, accuracy_self=88),
        ControlResult("c", "gpt", "p", True, answer="no", confidence=40, accuracy_self=40),
    ]
    c = _consensus(rs)
    assert c["agreement"] is True
    assert "yes" in (c["majority_answer"] or "")
