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


# -- review-fix regressions --------------------------------------------------

def _seed_subject(svc: MetaNeuralService, subj: str):
    """Grant every data purpose and ingest the demo fixture for ``subj``."""
    grants = {p: svc.grant_consent(subj, p).grant_id
              for p in (Purpose.INGEST, Purpose.WORKING_MEMORY, Purpose.ASSOCIATION,
                        Purpose.OPTIMIZATION, Purpose.AUDIT_READ)}
    nodes, edges = _fixture_nodes_edges()
    svc.ingest(subj, grants[Purpose.INGEST], nodes, edges)
    return grants


def test_audit_trail_is_subject_scoped():
    """H1: a subject with AUDIT_READ sees only its own audit records."""
    svc = MetaNeuralService()
    ga = _seed_subject(svc, "subj_a")
    gb = _seed_subject(svc, "subj_b")

    valid_a, events_a = svc.audit_trail("subj_a", ga[Purpose.AUDIT_READ])
    valid_b, events_b = svc.audit_trail("subj_b", gb[Purpose.AUDIT_READ])
    assert valid_a and valid_b
    assert events_a and events_b
    assert all(e.subject_id == "subj_a" for e in events_a)
    assert all(e.subject_id == "subj_b" for e in events_b)
    # No cross-subject leakage.
    assert not any(e.subject_id == "subj_b" for e in events_a)


def test_audit_cross_subject_requires_admin_capability():
    """H1: global read is denied unless the explicit admin token matches."""
    svc = MetaNeuralService()  # admin capability disabled by default
    ga = _seed_subject(svc, "subj_a")
    _seed_subject(svc, "subj_b")
    with pytest.raises(ConsentError):
        svc.audit_trail("subj_a", ga[Purpose.AUDIT_READ], include_all=True)

    admin_svc = MetaNeuralService(admin_token="s3cret")
    ga2 = _seed_subject(admin_svc, "subj_a")
    _seed_subject(admin_svc, "subj_b")
    # Wrong token still denied.
    with pytest.raises(ConsentError):
        admin_svc.audit_trail("subj_a", ga2[Purpose.AUDIT_READ],
                              include_all=True, admin_token="wrong")
    valid, events = admin_svc.audit_trail(
        "subj_a", ga2[Purpose.AUDIT_READ], include_all=True, admin_token="s3cret"
    )
    subs = {e.subject_id for e in events}
    assert valid and {"subj_a", "subj_b"}.issubset(subs)


def test_revocation_purges_subject_state():
    """M2: explicit revocation removes derived state and leaves a tombstone."""
    svc = MetaNeuralService()
    grants = _seed_subject(svc, "subj_r")
    assert "subj_r" in svc._graphs and "subj_r" in svc._wm

    removed = svc.revoke_consent("subj_r", grants[Purpose.INGEST])
    assert removed["graph"] == 1 and removed["working_memory"] == 1
    assert "subj_r" not in svc._graphs
    assert "subj_r" not in svc._wm
    assert "subj_r" not in svc._hebbian
    assert "subj_r" not in svc._snapshots
    # Data is now inaccessible: snapshot lookup raises.
    with pytest.raises(KeyError):
        svc.snapshot_for("subj_r")
    # Non-PII deletion tombstone recorded.
    tombstones = [e for e in svc.consent.audit.events()
                  if e.action == "subject.purge" and e.subject_id == "subj_r"]
    assert tombstones and tombstones[-1].detail["reason"] == "revocation"


def test_expiry_purges_subject_state():
    """M2: detected expiry (not just revocation) purges derived state."""
    svc = MetaNeuralService()
    subj = "subj_e"
    # Short retention grants; ingest while active.
    ingest_grant = svc.consent.grant(subj, Purpose.INGEST,
                                      retention=timedelta(seconds=1))
    wm_grant = svc.consent.grant(subj, Purpose.WORKING_MEMORY,
                                 retention=timedelta(seconds=1))
    nodes, edges = _fixture_nodes_edges()
    svc.ingest(subj, ingest_grant.grant_id, nodes, edges)
    assert subj in svc._graphs

    # Simulate all grants having expired.
    future = datetime.now(UTC) + timedelta(days=1)
    removed = svc._purge_if_expired(subj, at=future)
    assert removed.get("graph") == 1
    assert subj not in svc._graphs
    tombstones = [e for e in svc.consent.audit.events()
                  if e.action == "subject.purge" and e.subject_id == subj]
    assert tombstones and tombstones[-1].detail["reason"] == "expiry"


def test_grant_id_mismatch_single_audit_decision():
    """LOW: a grant_id mismatch is one ``denied`` event, never granted->denied."""
    svc = MetaNeuralService()
    subj = "subj_m"
    svc.grant_consent(subj, Purpose.INGEST)
    nodes, edges = _fixture_nodes_edges()
    with pytest.raises(ConsentError):
        svc.ingest(subj, "wrong-grant-id", nodes, edges)
    decisions = [e.decision for e in svc.consent.audit.events()
                 if e.action == "graph.ingest"]
    assert decisions == ["denied"]


def test_adjacency_self_loop_not_double_counted():
    """LOW: a self-loop weight lands once on the diagonal."""
    schema = _schema()
    g = PropertyGraph(schema)
    g.add_node("a", "concept", provenance=_prov())
    g.add_edge("self", "relates_to", "a", "a", weight=0.7, provenance=_prov())
    ids, adj = g.snapshot().adjacency()
    i = ids.index("a")
    assert adj[i][i] == pytest.approx(0.7)


def test_solve_qubo_symmetrizes_asymmetric_matrix():
    """LOW: asymmetric Q is symmetrised; energy matches for binary vectors."""
    node_ids = ["a", "b"]
    Q_asym = np.array([[-1.0, 2.0], [0.0, -1.0]], dtype=np.float64)
    from fusion_hero_os.meta.qubo_bridge import QUBOProblem, energy
    problem = QUBOProblem(node_ids=node_ids, Q=Q_asym, constraints={},
                          source_snapshot="deadbeef")
    result = solve_qubo(problem, backend="brute", seed=1, steps=10)
    Q_sym = 0.5 * (Q_asym + Q_asym.T)
    x = np.array(result.solution_vector, dtype=np.float64)
    assert result.objective == pytest.approx(float(x @ Q_sym @ x))
    # x^T Q x is invariant under symmetrisation for binary x.
    assert float(x @ Q_asym @ x) == pytest.approx(float(x @ Q_sym @ x))


def test_service_concurrent_ingest_thread_safe():
    """M1: concurrent per-subject ingests keep the state maps consistent."""
    import threading

    svc = MetaNeuralService()
    subjects = [f"subj_{i}" for i in range(16)]
    grants = {s: svc.grant_consent(s, Purpose.INGEST).grant_id for s in subjects}
    nodes, edges = _fixture_nodes_edges()
    errors: list = []

    def _worker(s: str):
        try:
            svc.ingest(s, grants[s], nodes, edges)
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(s,)) for s in subjects]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert set(svc._graphs) == set(subjects)
    assert len(svc._snapshots) == len(subjects)
