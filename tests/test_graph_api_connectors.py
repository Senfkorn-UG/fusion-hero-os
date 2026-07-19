# -*- coding: utf-8 -*-
"""Graph API hub — dry-run guarantees."""

from __future__ import annotations

import os

from fusion_hero_os.connectors.graph_api import GraphAPIHub, build_default_hub
from fusion_hero_os.methodology.connectors import ConnectorRegistry, InstagramConnector


def test_list_connectors_has_instagram_and_github():
    hub = build_default_hub()
    listing = hub.list_connectors()
    assert listing["ok"] is True
    assert "instagram" in listing["connectors"]
    assert "github_graphql" in listing["connectors"]
    assert "vercel" in listing["connectors"]


def test_instagram_publish_dry_run_without_live(monkeypatch):
    monkeypatch.delenv("FUSION_GRAPH_LIVE", raising=False)
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("IG_USER_ID", raising=False)
    hub = build_default_hub()
    out = hub.instagram_publish(
        image_url="https://example.com/a.png",
        caption="test",
        force_live=False,
    )
    assert out.get("would_execute") is False
    assert out.get("ok") is True


def test_registry_includes_instagram():
    reg = ConnectorRegistry.default()
    assert "InstagramConnector" in reg.connectors
    assert reg.connectors["InstagramConnector"].available is False
    plan = reg.connectors["InstagramConnector"].publish(
        "https://example.com/a.png", "cap"
    )
    assert plan.get("would_execute") is False


def test_dispatch_status():
    hub = build_default_hub()
    st = hub.dispatch("github_rest", "status")
    assert st.get("ok") is True
