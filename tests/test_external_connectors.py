# -*- coding: utf-8 -*-
"""Tests for the external connector integration layer.

Covers the registry, spec-driven routing, input validation, mutating-tool
gating, and failure handling (auth/rate-limit/connector/transport errors).
Uses a fake CLI client for deterministic offline runs. Optional live smoke
tests run only when FUSION_LIVE_CONNECTOR_TESTS=1 and the `external-tool`
binary is present.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from normal_os.connectors import (  # noqa: E402
    ConnectorRegistry,
    ExternalToolConnector,
    ExternalToolError,
)
from normal_os.connectors.specs import CONNECTOR_SPECS  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class FakeClient:
    """Stand-in for ExternalToolClient with scriptable behaviour."""

    def __init__(self, available=True, responses=None, raise_map=None):
        self._available = available
        self._responses = responses or {}
        self._raise_map = raise_map or {}
        self.calls = []

    def is_available(self):
        return self._available

    def call(self, source_id, tool_name, arguments=None):
        self.calls.append((source_id, tool_name, arguments))
        if tool_name in self._raise_map:
            raise self._raise_map[tool_name]
        return self._responses.get(tool_name, {"ok": True, "tool": tool_name})


# -- registry ---------------------------------------------------------------

def test_registry_registers_all_specced_connectors():
    reg = ConnectorRegistry(client=FakeClient())
    for name in CONNECTOR_SPECS:
        assert name in reg.list_connectors()
        assert isinstance(reg.get(name), ExternalToolConnector)


def test_registry_status_and_capabilities():
    reg = ConnectorRegistry(client=FakeClient())
    status = reg.status("slack")
    assert status["source_id"] == "slack_direct"
    caps = reg.capabilities("slack")
    names = {c["name"] for c in caps}
    assert "slack_search_channels" in names
    # mutating flag is exposed for gating decisions
    assert any(c["mutating"] for c in caps)


def test_registry_unknown_connector_returns_none():
    reg = ConnectorRegistry(client=FakeClient())
    assert reg.get("does_not_exist") is None
    assert reg.status("does_not_exist") is None


# -- routing ----------------------------------------------------------------

def test_execute_routes_to_client_with_source_id():
    client = FakeClient(responses={"finance_market_sentiment": {"content": "BULLISH"}})
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("finance").execute("finance_market_sentiment", {}))
    assert res.success
    assert res.data == {"content": "BULLISH"}
    assert client.calls == [("finance", "finance_market_sentiment", {})]


# -- validation -------------------------------------------------------------

def test_missing_required_arg_is_validation_error():
    reg = ConnectorRegistry(client=FakeClient())
    res = run(reg.get("slack").execute("slack_search_channels", {}))
    assert not res.success
    assert res.metadata["kind"] == "validation_error"
    assert "query" in res.error


def test_unknown_tool_is_rejected():
    reg = ConnectorRegistry(client=FakeClient())
    res = run(reg.get("slack").execute("slack_delete_everything", {"x": 1}))
    assert not res.success
    assert "unknown tool" in res.error


def test_mutating_tool_blocked_by_default():
    client = FakeClient()
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("slack").execute(
        "slack_send_message", {"channel_id": "C1", "message": "hi"}))
    assert not res.success
    assert res.metadata["kind"] == "validation_error"
    assert client.calls == []  # never reached the client


def test_mutating_tool_allowed_when_opted_in():
    client = FakeClient(responses={"slack_send_message": {"ok": True}})
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("slack").execute(
        "slack_send_message", {"channel_id": "C1", "message": "hi"},
        allow_mutating=True))
    assert res.success
    assert client.calls and client.calls[0][1] == "slack_send_message"


def test_opticodds_post_blocked_in_read_only():
    client = FakeClient()
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("opticodds").execute(
        "opticodds", {"path": "/parlay", "method": "POST"}))
    assert not res.success
    assert client.calls == []


# -- failure handling -------------------------------------------------------

@pytest.mark.parametrize("kind", ["auth_required", "rate_limited",
                                  "connector_error", "transport_error"])
def test_client_errors_are_surfaced_with_kind(kind):
    err = ExternalToolError(kind, f"boom-{kind}", source_id="finance")
    client = FakeClient(raise_map={"finance_market_sentiment": err})
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("finance").execute("finance_market_sentiment", {}))
    assert not res.success
    assert res.metadata["kind"] == kind


def test_health_check_records_and_never_raises():
    err = ExternalToolError("auth_required", "no creds")
    client = FakeClient(raise_map={"jira__get_current_user": err})
    reg = ConnectorRegistry(client=client)
    res = run(reg.get("jira").health_check())
    assert not res.success
    assert reg.get("jira").status()["last_health"]["kind"] == "auth_required"


def test_unavailable_transport_marks_not_available():
    reg = ConnectorRegistry(client=FakeClient(available=False))
    res = run(reg.get("finance").health_check())
    assert not res.success
    assert res.metadata["kind"] == "not_available"


def test_health_check_all_aggregates():
    responses = {spec.health.tool_name: {"ok": True}
                 for spec in CONNECTOR_SPECS.values()
                 if spec.transport == "external_tool" and spec.health}
    reg = ConnectorRegistry(client=FakeClient(responses=responses))
    results = run(reg.health_check_all())
    # every specced connector reports a boolean ok
    for name in CONNECTOR_SPECS:
        assert name in results
        assert "ok" in results[name]


# -- client error classification (no subprocess) ----------------------------

def test_client_classifies_stderr_json_auth():
    from normal_os.connectors.external_tool_client import ExternalToolClient
    c = ExternalToolClient()
    with pytest.raises(ExternalToolError) as ei:
        c._raise_from_stderr('error: {"error": "auth_required", "auth_url": "https://x"}', "call")
    assert ei.value.kind == "auth_required"
    assert ei.value.auth_url == "https://x"


def test_client_redacts_secrets_in_messages():
    from normal_os.connectors.external_tool_client import redact
    out = redact("token=ghp_" + "a" * 30)
    assert "ghp_" not in out and "[REDACTED]" in out


# -- optional live smoke -----------------------------------------------------

LIVE = os.getenv("FUSION_LIVE_CONNECTOR_TESTS") == "1"


@pytest.mark.skipif(not LIVE, reason="set FUSION_LIVE_CONNECTOR_TESTS=1 to run")
def test_live_finance_sentiment():
    reg = ConnectorRegistry()
    res = run(reg.get("finance").execute("finance_market_sentiment", {}))
    assert res.success
