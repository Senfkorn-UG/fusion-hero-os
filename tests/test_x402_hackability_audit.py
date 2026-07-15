# -*- coding: utf-8 -*-
from fusion_hero_os.core.x402_hackability_audit import (
    load_config,
    heroic_math_checks,
    audit,
    risk_score,
    GateResult,
)


def test_config_has_attacks_and_gates():
    cfg = load_config()
    assert cfg.get("protocol") == "x402"
    assert len(cfg.get("attack_classes") or []) >= 5
    assert len(cfg.get("control_gates") or []) >= 5


def test_heroic_math_checks_pass_model():
    checks = heroic_math_checks(seed=402)
    assert len(checks) >= 3
    assert all(c.ok for c in checks)


def test_audit_warns_when_gates_missing():
    # honest default: gates false → high risk → warn/critical
    r = audit(emit=False)
    assert r.risk_score >= 45
    assert r.warn is True
    assert r.level in ("warn", "critical")
    assert r.controls_ok == 0


def test_audit_green_when_all_gates():
    cfg = load_config()
    answers = {g["id"]: True for g in (cfg.get("control_gates") or [])}
    r = audit(gate_answers=answers, emit=False)
    assert r.controls_ok == r.controls_total
    assert r.risk_score < 45
    assert r.warn is False
    assert r.level == "ok"


def test_risk_score_weights():
    cfg = load_config()
    gates = [
        GateResult("G_nonce_single_use", False, "A3_replay_idempotency", "x"),
        GateResult("G_finality_before_grant", True, "A1_settlement_optimistic", "y"),
    ]
    score, open_a = risk_score(cfg, gates, [])
    assert score > 0
    assert any(a["id"] == "A3_replay_idempotency" for a in open_a)
