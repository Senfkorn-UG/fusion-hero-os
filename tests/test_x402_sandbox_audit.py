# -*- coding: utf-8 -*-
from fusion_hero_os.core.x402_sandbox_audit import (
    SandboxConfig,
    MockX402Server,
    MockClient,
    run_sandbox_audit,
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
