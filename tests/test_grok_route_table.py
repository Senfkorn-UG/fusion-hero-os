"""Tests for Grok canonical route table."""
from fusion_hero_os.core.grok_route_table import (
    LEGACY_REDIRECTS,
    resolve,
    route_message,
    all_routes,
)


def test_resolve_core_intents():
    assert resolve("interconnect").surface == "/mainframe/grok"
    assert resolve("dauer_vr").surface == "/mainframe/vr"
    assert resolve("ide").surface == "/mainframe/ide"
    assert resolve("worktree").surface == "/mainframe/worktree"
    assert resolve("mainframe").surface == "/mainframe"


def test_resolve_aliases():
    assert resolve("portal").intent == "mainframe"
    assert resolve("vernetzung").intent == "interconnect"


def test_route_message_plan():
    plan = route_message("oeffne dauer vr und ide", ["dauer_vr", "ide"])
    assert plan["ok"]
    assert plan["primary"]["intent"] == "dauer_vr"
    assert len(plan["routes"]) >= 2
    assert plan["redirect_hint"] == "/mainframe/vr"


def test_legacy_redirects():
    assert LEGACY_REDIRECTS["/grok"] == "/mainframe/grok"
    assert LEGACY_REDIRECTS["/ide"] == "/mainframe/ide"
    assert LEGACY_REDIRECTS["/vr/persistent"] == "/mainframe/vr"


def test_all_routes_entrypoints():
    a = all_routes()
    assert a["entrypoints"]["control_plane"] == "/mainframe/grok"
    assert "interconnect" in a["table"]
