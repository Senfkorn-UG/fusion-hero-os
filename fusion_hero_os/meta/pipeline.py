# -*- coding: utf-8 -*-
"""End-to-end orchestration of the meta-neural vertical slice.

Flow (each step fails closed on missing consent):

    consent grant -> ingest neutral fixture -> activate working memory
    -> update associations -> analyze coupling/convergence -> optimize
    -> retrieve audit trail

The :class:`MetaNeuralService` ties together consent, the property graph,
working memory, Hebbian memory, coupling analysis and the QUBO bridge. It is
local-only and holds all state in memory. Persistence hooks are explicit and
also consent-gated.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from .consent import ConsentStore, Purpose
from .coupling import ContractionResult, is_contraction
from .graph import GraphSchema, GraphSnapshot, PropertyGraph, Provenance
from .hebbian import HebbianAssociationMemory, HebbianConfig
from .qubo_bridge import QUBOResult, build_qubo, solve_qubo
from .working_memory import ActivationReport, WorkingMemorySpace

DEFAULT_SCHEMA = GraphSchema(
    version="1.0.0",
    node_types=frozenset({"concept", "subject", "artifact"}),
    edge_types=frozenset({"relates_to", "derived_from", "associates"}),
    dimensions=frozenset({"salience", "valence", "recency"}),
)


class MetaNeuralService:
    """In-memory, consent-scoped orchestration of the slice."""

    def __init__(
        self,
        *,
        schema: GraphSchema = DEFAULT_SCHEMA,
        consent_store: Optional[ConsentStore] = None,
        wm_capacity: float = 1.0,
        wm_decay: float = 0.9,
    ) -> None:
        self.schema = schema
        self.consent = consent_store or ConsentStore()
        self._graphs: Dict[str, PropertyGraph] = {}
        self._snapshots: Dict[str, GraphSnapshot] = {}
        self._wm: Dict[str, WorkingMemorySpace] = {}
        self._hebbian: Dict[str, HebbianAssociationMemory] = {}
        self._wm_capacity = wm_capacity
        self._wm_decay = wm_decay

    # -- consent ---------------------------------------------------------
    def grant_consent(self, subject_id: str, purpose: Purpose,
                      retention_days: int = 30):
        return self.consent.grant(
            subject_id, Purpose(purpose), retention=timedelta(days=retention_days)
        )

    def _require(self, subject_id: str, grant_id: str, purpose: Purpose, action: str):
        grant = self.consent.authorize(subject_id, Purpose(purpose), action=action)
        if grant.grant_id != grant_id:
            # Grant exists for the purpose but caller referenced a different id.
            self.consent.audit.append(
                action, decision="denied", subject_id=subject_id,
                purpose=Purpose(purpose).value,
                detail={"reason": "grant_id mismatch"},
            )
            from .consent import ConsentError

            raise ConsentError("grant_id does not match the active grant")
        return grant

    # -- ingest ----------------------------------------------------------
    def ingest(
        self,
        subject_id: str,
        grant_id: str,
        nodes: List[dict],
        edges: List[dict],
    ) -> GraphSnapshot:
        grant = self._require(subject_id, grant_id, Purpose.INGEST, "graph.ingest")
        graph = PropertyGraph(self.schema)
        prov = Provenance.now("meta.pipeline", purpose=Purpose.INGEST.value,
                              grant_id=grant.grant_id)
        for nd in nodes:
            graph.add_node(
                nd["node_id"], nd["type"],
                dimensions=nd.get("dimensions"),
                attributes=nd.get("attributes"),
                provenance=prov,
            )
        for ed in edges:
            graph.add_edge(
                ed["edge_id"], ed["type"], ed["source"], ed["target"],
                weight=ed.get("weight", 1.0),
                attributes=ed.get("attributes"),
                provenance=prov,
            )
        snapshot = graph.snapshot()
        self._graphs[subject_id] = graph
        self._snapshots[subject_id] = snapshot
        # working memory slots = node ids (opaque)
        node_ids = [n.node_id for n in graph.nodes()]
        self._wm[subject_id] = WorkingMemorySpace(
            node_ids, capacity=self._wm_capacity, decay=self._wm_decay
        )
        self._hebbian[subject_id] = HebbianAssociationMemory(HebbianConfig())
        self.consent.audit.append(
            "graph.snapshot", decision="granted", subject_id=subject_id,
            purpose=Purpose.INGEST.value,
            detail={"snapshot": snapshot.content_hash,
                    "nodes": len(node_ids), "edges": len(graph.edges())},
        )
        return snapshot

    def snapshot_for(self, subject_id: str) -> GraphSnapshot:
        if subject_id not in self._snapshots:
            raise KeyError(f"no snapshot for subject {subject_id!r}")
        return self._snapshots[subject_id]

    # -- working memory --------------------------------------------------
    def activate(
        self,
        subject_id: str,
        grant_id: str,
        activations: Dict[str, float],
        steps: int = 1,
    ) -> ActivationReport:
        self._require(subject_id, grant_id, Purpose.WORKING_MEMORY, "wm.activate")
        wm = self._wm[subject_id]
        for slot, amount in activations.items():
            wm.activate(slot, amount)
        for _ in range(steps):
            wm.step()
        report = wm.report()
        self.consent.audit.append(
            "wm.report", decision="granted", subject_id=subject_id,
            purpose=Purpose.WORKING_MEMORY.value,
            detail={"active_count": len(report.active), "step_index": report.step_index},
        )
        return report

    # -- associations ----------------------------------------------------
    def associate(self, subject_id: str, grant_id: str) -> HebbianAssociationMemory:
        """Update Hebbian weights from current working-memory co-activations."""
        self._require(subject_id, grant_id, Purpose.ASSOCIATION, "assoc.update")
        wm = self._wm[subject_id]
        heb = self._hebbian[subject_id]
        slots = wm.slots
        acts = wm.vector()
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                if acts[i] != 0.0 and acts[j] != 0.0:
                    heb.update(slots[i], slots[j], acts[i], acts[j])
        self.consent.audit.append(
            "assoc.update", decision="granted", subject_id=subject_id,
            purpose=Purpose.ASSOCIATION.value,
            detail={"pairs": len(heb)},
        )
        return heb

    # -- coupling / convergence -----------------------------------------
    def analyze_convergence(
        self, subject_id: str, grant_id: str
    ) -> ContractionResult:
        """Treat association-weighted decay dynamics as a linear map and test it.

        Dynamics: ``x_{k+1} = decay * (I + A) x`` where ``A`` is the (scaled)
        association matrix. The Jacobian is constant (linear), so the
        contractivity test is exact for this map.
        """
        self._require(subject_id, grant_id, Purpose.ASSOCIATION, "coupling.analyze")
        wm = self._wm[subject_id]
        heb = self._hebbian[subject_id]
        slots = wm.slots
        _, A = heb.to_matrix(slots)
        A = np.asarray(A, dtype=np.float64)
        n = A.shape[0]
        J = wm.decay * (np.eye(n) + A)
        result = is_contraction(J, norm_order="inf")
        self.consent.audit.append(
            "coupling.analyze", decision="granted", subject_id=subject_id,
            purpose=Purpose.ASSOCIATION.value,
            detail=result.to_dict(),
        )
        return result

    # -- optimize --------------------------------------------------------
    def optimize(
        self,
        subject_id: str,
        grant_id: str,
        *,
        selection_dimension: str = "salience",
        cardinality: Optional[int] = None,
        backend: str = "numpy",
        seed: int = 7,
        steps: int = 2000,
    ) -> QUBOResult:
        self._require(subject_id, grant_id, Purpose.OPTIMIZATION, "qubo.optimize")
        snapshot = self.snapshot_for(subject_id)
        heb = self._hebbian.get(subject_id)
        assoc = heb.to_matrix([n.node_id for n in snapshot.nodes]) if heb else None
        problem = build_qubo(
            snapshot,
            selection_dimension=selection_dimension,
            association=assoc,
            cardinality=cardinality,
        )
        result = solve_qubo(problem, backend=backend, seed=seed, steps=steps)
        self.consent.audit.append(
            "qubo.optimize", decision="granted", subject_id=subject_id,
            purpose=Purpose.OPTIMIZATION.value,
            detail={
                "objective": round(result.objective, 12),
                "backend": result.backend,
                "seed": result.seed,
                "source_snapshot": result.source_snapshot,
            },
        )
        return result

    # -- audit -----------------------------------------------------------
    def audit_trail(self, subject_id: str, grant_id: str) -> Tuple[bool, list]:
        self._require(subject_id, grant_id, Purpose.AUDIT_READ, "audit.read")
        return self.consent.audit.verify(), self.consent.audit.events()
