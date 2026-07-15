# -*- coding: utf-8 -*-
from fusion_hero_os.core.x402_sandbox_audit import (
    SandboxConfig,
    MockX402Server,
    MockClient,
    run_sandbox_audit,
    simulate_successful_attack,
    _case_replay,
    _case_binding,
)


def test_secure_rejects_replay():
    s = MockX402Server(SandboxConfig())
    c = MockClient(s)
    auth, g1 = c.pay_and_request()
    _, g2 = c.pay_and_request(reuse_auth=auth)
    assert g1["granted"] is True
    assert g2["granted"] is False


def test_insecure_allows_replay():
    s = MockX402Server(SandboxConfig(nonce_single_use=False))
    c = MockClient(s)
    auth, g1 = c.pay_and_request()
    _, g2 = c.pay_and_request(reuse_auth=auth)
    assert g1["granted"] and g2["granted"]


def test_evidence_cases_prove():
    assert _case_replay().proved
    assert _case_binding().proved


def test_full_sandbox_audit():
    r = run_sandbox_audit(budget_eur=500.0)
    assert r["sandbox"] is True
    assert r["external_targets"] is False
    assert r["exploit_payloads"] is False
    assert r["proved_count"] == r["case_count"]
    assert r["ok"] is True


def test_simulate_attack_goes_through_insecure_only():
    sim = simulate_successful_attack()
    assert sim["attack_succeeded_on_insecure_mock"] is True
    assert sim["attack_blocked_on_secure_mock"] is True
    assert sim["impact"]["unpaid_or_unbound_grants"] >= 2
    assert sim["impact"]["replay_worked"] is True
    assert sim["external_targets"] is False
