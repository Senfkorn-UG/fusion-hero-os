# -*- coding: utf-8 -*-
"""Beweise fuer den Dependency Atlas (Claim DEP-ATLAS in proof_registry.yaml).

Der Atlas ist nur dann eine Antwort auf 'epistemische Platzhalter', wenn seine
eigenen Aussagen geprueft sind: Zyklen werden gefunden, unaufgeloeste Imports
werden gefunden, das Layer-Mapping ist deterministisch, und der echte
Repo-Graph haelt die Gates ein.
"""

from __future__ import annotations

import json

import pytest

from fusion_hero_os.core.dependency_atlas import (
    Atlas,
    Edge,
    assign_layer,
    build_atlas,
    find_cycles,
    render_markdown,
    render_mermaid,
)


# ---------------------------------------------------------------------------
# Analyse-Primitive (synthetische Graphen)
# ---------------------------------------------------------------------------

def _atlas_with_edges(edges):
    atlas = Atlas()
    atlas.edges = [Edge(s, d, deferred=deferred) for s, d, deferred in edges]
    return atlas


def test_cycle_detection_finds_direct_cycle():
    atlas = _atlas_with_edges([("a", "b", False), ("b", "a", False)])
    cycles = find_cycles(atlas)
    assert cycles == [["a", "b"]]


def test_cycle_detection_finds_transitive_cycle():
    atlas = _atlas_with_edges([("a", "b", False), ("b", "c", False), ("c", "a", False)])
    assert find_cycles(atlas) == [["a", "b", "c"]]


def test_deferred_edges_do_not_form_cycles():
    # Funktions-lokale Imports sind zur Import-Zeit unkritisch — genau das
    # Muster, mit dem QuadCoreBridge den heroic/ascension-Zyklus aufloest.
    atlas = _atlas_with_edges([("a", "b", False), ("b", "a", True)])
    assert find_cycles(atlas) == []


def test_acyclic_graph_has_no_cycles():
    atlas = _atlas_with_edges([("a", "b", False), ("b", "c", False), ("a", "c", False)])
    assert find_cycles(atlas) == []


# ---------------------------------------------------------------------------
# Layer-Mapping (Fraktal-Layer, Longest-Prefix, deterministisch)
# ---------------------------------------------------------------------------

def test_layer_assignment_longest_prefix_wins():
    prefixes = [("ascension_os/core", "ascension-core"), ("ascension_os", "ascension")]
    assert assign_layer("ascension_os/core/x.py", prefixes) == "ascension-core"
    assert assign_layer("ascension_os/evolution/y.py", prefixes) == "ascension"


def test_layer_assignment_falls_back_honestly():
    # Unbekannte Pfade werden NICHT geraten, sondern als unassigned gefuehrt
    assert assign_layer("voellig/unbekannt.py", []) == "unassigned"


def test_layer_assignment_uses_fallback_table():
    assert assign_layer("kernel/bridge/x.py", []) == "kernel"
    assert assign_layer("tests/test_x.py", []) == "proof"


# ---------------------------------------------------------------------------
# Echter Repo-Graph: die Gates, die auch die CI erzwingt
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def repo_atlas():
    return build_atlas()


def test_repo_atlas_scans_substantial_codebase(repo_atlas):
    assert len(repo_atlas.nodes) > 100, "Atlas hat den aktiven Code nicht erfasst"
    assert len(repo_atlas.edges) > 100
    kinds = {n.kind for n in repo_atlas.nodes.values()}
    assert {"python", "rust-crate", "js-package"} <= kinds, "polyglott heisst: alle drei Welten"


def test_repo_has_no_unresolved_rooted_imports(repo_atlas):
    assert repo_atlas.unresolved == [], (
        "Unaufgeloeste interne Imports sind epistemische Platzhalter auf "
        f"Dependency-Ebene: {repo_atlas.unresolved}"
    )


def test_repo_has_no_toplevel_import_cycles(repo_atlas):
    assert repo_atlas.cycles == [], (
        f"Neue Import-Zyklen eingefuehrt: {repo_atlas.cycles} — "
        "lazy import verwenden (Muster: QuadCoreBridge.__init__)"
    )


def test_repo_atlas_assigns_layers(repo_atlas):
    layers = {n.layer for n in repo_atlas.nodes.values()}
    # Kern-Layer der Fraktal-Architektur muessen belegt sein
    assert {"ascension", "kernel", "vr", "knowledge"} <= layers
    unassigned = [n.path for n in repo_atlas.nodes.values() if n.layer == "unassigned"]
    total = len(repo_atlas.nodes)
    assert len(unassigned) / total < 0.25, (
        f"{len(unassigned)}/{total} Knoten ohne Layer — Mapping erweitern: {unassigned[:10]}"
    )


def test_repo_atlas_serializes_and_renders(repo_atlas):
    payload = repo_atlas.to_dict()
    json.dumps(payload)  # muss serialisierbar sein (Dashboard-Endpunkt)
    assert payload["epistemik"]["placeholder_marker_total"] >= 0
    mermaid = render_mermaid(repo_atlas)
    assert mermaid.startswith("```mermaid") and "subgraph" in mermaid
    md = render_markdown(repo_atlas)
    assert "Dependency Atlas" in md and "```mermaid" in md
