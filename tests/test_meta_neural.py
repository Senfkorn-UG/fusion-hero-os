# -*- coding: utf-8 -*-
"""Tests for the meta-neural vertical slice (fusion_hero_os.meta)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from fusion_hero_os.meta.consent import (
    AuditLog,
    ConsentError,
    ConsentStore,
    Purpose,
)
from fusion_hero_os.meta.coupling import (
    is_contraction,
    iterate_to_fixed_point,
    jacobian_fd,
    spectral_radius,
)
from fusion_hero_os.meta.graph import (
    GraphError,
    GraphSchema,
    PropertyGraph,
    Provenance,
)
from fusion_hero_os.meta.hebbian import HebbianAssociationMemory, HebbianConfig
from fusion_hero_os.meta.pipeline import DEFAULT_SCHEMA, MetaNeuralService
from fusion_hero_os.meta.qubo_bridge import build_qubo, solve_qubo, _brute_force
from fusion_hero_os.meta.vault import (
    InMemoryVaultResolver,
    NullVaultResolver,
    SubjectRef,
    VaultAuthorizationError,
    VaultUnavailableError,
)
from fusion_hero_os.meta.working_memory import WorkingMemorySpace, WorkingMemoryError


UTC = timezone.utc


def _schema() -> GraphSchema:
    return GraphSchema(
        version="1.0.0",
        node_types=frozenset({"concept", "artifact"}),
        edge_types=frozenset({"relates_to"}),
        dimensions=frozenset({"salience", "valence"}),
    )


def _prov(ts: str = "2020-01-01T00:00:00+00:00") -> Provenance:
    return Provenance(created_by="test", created_at=ts, purpose="ingest")


# --------------------------------------------------------------------------
# Graph invariants
# --------------------------------------------------------------------------
def test_graph_rejects_unknown_types_and_dimensions():
    g = PropertyGraph(_schema())
    with pytest.raises(GraphError):
        g.add_node("n1", "unknown_type", provenance=_prov())
    g.add_node("n1", "concept", dimensions={"salience": 1.0}, provenance=_prov())
    with pytest.raises(GraphError):
        g.add_node("n2", "concept", dimensions={"bogus": 1.0}, provenance=_prov())
    with pytest.raises(GraphError):
        g.add_node("n1", "concept", provenance=_prov())  # duplicate id


def test_edge_requires_existing_endpoints():
    g = PropertyGraph(_schema())
    g.add_node("a", "concept", provenance=_prov())
    with pytest.raises(GraphError):
        g.add_edge("e1", "relates_to", "a", "missing", provenance=_prov())


def test_snapshot_is_immutable_and_content_addressed():
    g = PropertyGraph(_schema())
    g.add_node("a", "concept", dimensions={"salience": 0.5}, provenance=_prov())
    snap = g.snapshot()
    assert isinstance(snap.nodes, tuple)
    assert snap.content_hash and len(snap.content_hash) == 64
    with pytest.raises(AttributeError):
        snap.nodes[0].node_id = "x"  # frozen dataclass


def test_deterministic_serialization_ignores_timestamp_and_order():
    def build(ts, order):
        g = PropertyGraph(_schema())
        ids = ["a", "b"] if order else ["b", "a"]
        for nid in ids:
            g.add_node(nid, "concept", dimensions={"salience": 1.0},
                       provenance=_prov(ts))
        return g.snapshot()

    s1 = build("2020-01-01T00:00:00+00:00", True)
    s2 = build("2021-06-06T12:00:00+00:00", False)
    assert s1.content_hash == s2.content_hash
    # Canonical JSON is byte-stable across runs.
    assert s1.to_canonical_json() == build("2020-01-01T00:00:00+00:00", True).to_canonical_json()


def test_node_matrix_and_adjacency_deterministic():
    g = PropertyGraph(_schema())
    g.add_node("b", "concept", dimensions={"salience": 0.2}, provenance=_prov())
    g.add_node("a", "concept", dimensions={"salience": 0.9}, provenance=_prov())
    g.add_edge("e1", "relates_to", "a", "b", weight=0.7, provenance=_prov())
    snap = g.snapshot()
    ids, mat = snap.node_matrix(["salience"])
    assert ids == ["a", "b"]
    assert mat == [[0.9], [0.2]]
    aids, adj = snap.adjacency()
    assert adj[0][1] == pytest.approx(0.7)
    assert adj[1][0] == pytest.approx(0.7)


# --------------------------------------------------------------------------
# Consent + audit
# --------------------------------------------------------------------------
def test_consent_denial_is_fail_closed_and_audited():
    store = ConsentStore()
    with pytest.raises(ConsentError):
        store.authorize("subj_1", Purpose.INGEST, action="graph.ingest")
    events = store.audit.events()
    assert events[-1].decision == "denied"
    assert store.audit.verify()


def test_consent_grant_authorize_revoke_expiry():
    store = ConsentStore()
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    grant = store.grant("subj_1", Purpose.INGEST, retention=timedelta(days=1), at=t0)
    assert store.authorize("subj_1", Purpose.INGEST, action="x", at=t0).grant_id == grant.grant_id
    # Expired.
    with pytest.raises(ConsentError):
        store.authorize("subj_1", Purpose.INGEST, action="x",
                        at=t0 + timedelta(days=2))
    # Revoked.
    store.revoke(grant.grant_id, at=t0)
    with pytest.raises(ConsentError):
        store.authorize("subj_1", Purpose.INGEST, action="x", at=t0)


def test_purpose_limitation():
    store = ConsentStore()
    store.grant("subj_1", Purpose.INGEST)
    with pytest.raises(ConsentError):
        store.authorize("subj_1", Purpose.OPTIMIZATION, action="x")


def test_audit_chain_tamper_detection():
    log = AuditLog()
    log.append("a", decision="granted")
    log.append("b", decision="granted")
    assert log.verify()
    # Tamper with an internal event -> chain breaks.
    object.__setattr__(log._events[0], "action", "mutated")
    assert not log.verify()


# --------------------------------------------------------------------------
# Vault boundary
# --------------------------------------------------------------------------
def test_null_vault_fails_closed():
    v = NullVaultResolver()
    assert not v.is_configured()
    with pytest.raises(VaultUnavailableError):
        v.resolve("subj_1", authorized=True)


def test_inmemory_vault_requires_authorization():
    v = InMemoryVaultResolver()
    v.put("subj_1", {"trait": 1})
    with pytest.raises(VaultAuthorizationError):
        v.resolve("subj_1", authorized=False)
    assert v.resolve("subj_1", authorized=True) == {"trait": 1}
    with pytest.raises(VaultUnavailableError):
        v.resolve("unknown", authorized=True)


def test_subject_ref_is_opaque_and_stable():
    a = SubjectRef.derive("alice@example.com")
    b = SubjectRef.derive("alice@example.com")
    assert a.subject_id == b.subject_id
    assert a.subject_id.startswith("subj_")
    assert "alice" not in a.subject_id and "@" not in a.subject_id


# --------------------------------------------------------------------------
# Working memory
# --------------------------------------------------------------------------
def test_working_memory_capacity_clamp():
    wm = WorkingMemorySpace(["x"], capacity=1.0, decay=1.0)
    wm.activate("x", 5.0)
    assert wm.activation("x") == 1.0
    wm.activate("x", -10.0)
    assert wm.activation("x") == -1.0


def test_working_memory_geometric_decay():
    wm = WorkingMemorySpace(["x"], capacity=10.0, decay=0.5)
    wm.activate("x", 1.0)
    wm.step()
    wm.step()
    assert wm.activation("x") == pytest.approx(0.25)  # 0.5**2


def test_working_memory_reportability_sorted():
    wm = WorkingMemorySpace(["x", "y", "z"], capacity=1.0, decay=1.0)
    wm.activate("x", 0.2)
    wm.activate("y", 0.9)
    report = wm.report()
    assert [s for s, _ in report.active] == ["y", "x"]  # z below threshold


def test_working_memory_validation():
    with pytest.raises(WorkingMemoryError):
        WorkingMemorySpace([], capacity=1.0)
    with pytest.raises(WorkingMemoryError):
        WorkingMemorySpace(["a"], decay=2.0)


# --------------------------------------------------------------------------
# Hebbian association memory
# --------------------------------------------------------------------------
def test_hebbian_update_forget_delete_reproducible():
    cfg = HebbianConfig(learning_rate=0.5, decay=0.0, w_max=10.0)
    h1 = HebbianAssociationMemory(cfg)
    h2 = HebbianAssociationMemory(cfg)
    updates = [("a", "b", 1.0, 1.0), ("a", "b", 1.0, 1.0)]
    h1.update_many(updates)
    h2.update_many(updates)
    assert h1.items() == h2.items()  # deterministic
    assert h1.weight("a", "b") == pytest.approx(1.0)  # 0.5 + 0.5

    # Forget.
    hf = HebbianAssociationMemory(HebbianConfig(decay=0.5, learning_rate=0.0))
    hf.update("a", "b", 0.0, 0.0)  # no-op create? pruned since 0
    hf._w[("a", "b")] = 1.0  # seed
    hf.decay_all()
    assert hf.weight("a", "b") == pytest.approx(0.5)

    # Delete.
    assert h1.delete("a", "b") is True
    assert h1.delete("a", "b") is False


def test_hebbian_clamp_and_delete_slot():
    h = HebbianAssociationMemory(HebbianConfig(learning_rate=100.0, w_max=1.0))
    h.update("a", "b", 1.0, 1.0)
    assert abs(h.weight("a", "b")) <= 1.0
    h.update("a", "c", 1.0, 1.0)
    removed = h.delete_slot("a")
    assert removed == 2
    assert len(h) == 0


# --------------------------------------------------------------------------
# Coupling / Jacobian / convergence
# --------------------------------------------------------------------------
def test_jacobian_dimensions_and_fd_agreement():
    # F(x) = A x with known A; Jacobian should equal A.
    A = np.array([[0.1, 0.2], [-0.3, 0.4]])

    def F(x):
        return A @ x

    J = jacobian_fd(F, np.zeros(2))
    assert J.shape == (2, 2)
    assert np.allclose(J, A, atol=1e-6)


def test_banach_contraction_detection():
    contract = np.array([[0.1, 0.2], [0.05, 0.3]])  # row sums < 1 -> inf-norm < 1
    res = is_contraction(contract, norm_order="inf")
    assert res.is_contraction
    assert res.spectral_radius < 1.0

    expand = np.array([[1.5, 0.0], [0.0, 0.9]])
    res2 = is_contraction(expand, norm_order="inf")
    assert not res2.is_contraction


def test_fixed_point_iteration_converges_for_contraction():
    A = np.array([[0.5, 0.1], [0.0, 0.5]])
    b = np.array([1.0, 2.0])

    def F(x):
        return A @ x + b  # unique fixed point x* = (I-A)^-1 b

    res = iterate_to_fixed_point(F, np.zeros(2), tol=1e-10, max_iter=500)
    assert res.converged
    expected = np.linalg.solve(np.eye(2) - A, b)
    assert np.allclose(res.x, expected, atol=1e-6)


# --------------------------------------------------------------------------
# QUBO bridge
# --------------------------------------------------------------------------
def _demo_snapshot():
    g = PropertyGraph(DEFAULT_SCHEMA)
    prov = Provenance.now("test", purpose="ingest")
    for nid, s in [("a", 0.9), ("b", 0.6), ("c", 0.3), ("d", 0.7)]:
        g.add_node(nid, "concept", dimensions={"salience": s}, provenance=prov)
    return g.snapshot()


def test_qubo_bridge_determinism_and_provenance():
    snap = _demo_snapshot()
    prob = build_qubo(snap, selection_dimension="salience", cardinality=2)
    r1 = solve_qubo(prob, backend="numpy", seed=7, steps=1000)
    r2 = solve_qubo(prob, backend="numpy", seed=7, steps=1000)
    assert r1.assignment == r2.assignment
    assert r1.objective == pytest.approx(r2.objective)
    assert r1.backend == "numpy"
    assert r1.seed == 7
    assert r1.source_snapshot == snap.content_hash  # provenance
    assert r1.constraints["cardinality"] == 2


def test_qubo_bridge_matches_brute_force_small():
    snap = _demo_snapshot()
    prob = build_qubo(snap, selection_dimension="salience", cardinality=2)
    ann = solve_qubo(prob, backend="numpy", seed=7, steps=5000)
    _, bf_energy = _brute_force(prob.Q)
    assert ann.objective == pytest.approx(bf_energy, abs=1e-6)
    assert sum(ann.solution_vector) == 2  # cardinality respected at optimum


# --------------------------------------------------------------------------
# Pipeline happy path + unsafe-path denial
# --------------------------------------------------------------------------
def _fixture_nodes_edges():
    nodes = [
        {"node_id": "a", "type": "concept", "dimensions": {"salience": 0.9}},
        {"node_id": "b", "type": "concept", "dimensions": {"salience": 0.6}},
    ]
    edges = [{"edge_id": "e1", "type": "relates_to", "source": "a",
              "target": "b", "weight": 0.5}]
    return nodes, edges


def test_pipeline_happy_path():
    svc = MetaNeuralService()
    subj = "subj_demo"
    grants = {p: svc.grant_consent(subj, p).grant_id
              for p in (Purpose.INGEST, Purpose.WORKING_MEMORY, Purpose.ASSOCIATION,
                        Purpose.OPTIMIZATION, Purpose.AUDIT_READ)}
    nodes, edges = _fixture_nodes_edges()
    snap = svc.ingest(subj, grants[Purpose.INGEST], nodes, edges)
    assert len(snap.nodes) == 2
    svc.activate(subj, grants[Purpose.WORKING_MEMORY], {"a": 0.9, "b": 0.7}, steps=1)
    svc.associate(subj, grants[Purpose.ASSOCIATION])
    conv = svc.analyze_convergence(subj, grants[Purpose.ASSOCIATION])
    assert isinstance(conv.is_contraction, bool)
    result = svc.optimize(subj, grants[Purpose.OPTIMIZATION], cardinality=1,
                          backend="numpy", seed=7, steps=1000)
    assert result.source_snapshot == snap.content_hash
    valid, events = svc.audit_trail(subj, grants[Purpose.AUDIT_READ])
    assert valid and len(events) > 5


def test_pipeline_denies_without_consent():
    svc = MetaNeuralService()
    nodes, edges = _fixture_nodes_edges()
    with pytest.raises(ConsentError):
        svc.ingest("subj_x", "bogus-grant", nodes, edges)


def test_pipeline_denies_on_grant_id_mismatch():
    svc = MetaNeuralService()
    subj = "subj_y"
    svc.grant_consent(subj, Purpose.INGEST)
    nodes, edges = _fixture_nodes_edges()
    with pytest.raises(ConsentError):
        svc.ingest(subj, "wrong-grant-id", nodes, edges)
