"""Tests for Grok interconnect capture/evolve."""
from __future__ import annotations

from fusion_hero_os.core.grok_interconnect import capture, evolve, get_graph


def test_capture_has_core_nodes():
    g = capture(dash_base="http://127.0.0.1:9")  # dashboard likely offline — still builds graph
    ids = {n.id for n in g.nodes}
    assert "grok-cli" in ids or "grok-skill" in ids
    assert "grok-llm" in ids
    assert "mcp-host" in ids
    assert len(g.edges) >= 5


def test_evolve_adds_intent_map():
    g = evolve(capture(dash_base="http://127.0.0.1:9"))
    d = g.to_dict()
    assert "intent_map" in d["evolved"]
    assert "mainframe" in d["evolved"]["intent_map"]
    assert isinstance(d["health_score"], float)
    assert 0.0 <= d["health_score"] <= 1.0


def test_get_graph_dict():
    d = get_graph(refresh=True)
    assert "nodes" in d and "edges" in d
    assert "summary" in d
