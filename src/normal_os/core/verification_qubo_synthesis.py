"""
verification_qubo_synthesis.py — SOTA-Juli-2026-Synthese für skalierbare Output-Prüfung.

Vergleicht drei grundverschiedene Verifikationsparadigmen und wählt per QUBO
eine gangbare, budget-bewusste Pipeline (parallel skalierbar via Claim-Clustering).

Paradigmen (Literatur/Produktion Juli 2026):
  A) Provenance-Trace — strukturierte Execution-Provenance (W3C PROV / OpenTelemetry)
  B) Backward-Pass Grounding — unabhängiger Verifier gegen Quellen (NLI / GroundGuard)
  C) Fail-Closed Harness — Pre-Action-Gates, Solver+Verifier (Maestro / verification.*)

Skalierung (QUBO-Literatur Juni 2026):
  - DQAOA: federierte Teilprobleme + Aggregation
  - HADOF: Hamiltonian-Decomposition → parallele Claim-Cluster
  - NISQ-Hybrid: QUBO nur für Routing, Ausführung klassisch
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    from qb_qubo import parallel_anneal
except ImportError:
    from core.qb_qubo import parallel_anneal  # type: ignore


# --- Verifikationsmodule (binäre QUBO-Variablen) ---

MODULES: Tuple[str, ...] = (
    "provenance_trace",   # A: strukturierte Traces, Tool-Call-Kette
    "span_attribution",   # B: Satz→Quellen-Span (RAG-Loops)
    "nli_backward",       # B: NLI backward-pass gegen Dokumente
    "echtwelt_web",       # B+: offene Echtwelt (URLs, DDG) — Fusion echtwelt_verifier
    "deterministic_entity",  # A/C: literal token match (SHOR-Stil)
    "fail_closed_gate",   # C: harter Pre/Post-Gate, abstain bei Ambiguität
    "recovery_loop",      # B/C: retrieve-revise-reverify bei Fail
    "parallel_cluster",   # Skalierung: Claim-Batches parallel (HADOF/DQAOA-Mapping)
)

MODULE_INDEX = {name: i for i, name in enumerate(MODULES)}


@dataclass
class TaskProfile:
    """Profil eines zu prüfenden Outputs."""
    stakes: str = "medium"  # low | medium | high
    latency_budget_ms: int = 900
    has_retrieved_docs: bool = True
    needs_real_world: bool = True
    claim_count: int = 5
    output_chars: int = 2000

    def stakes_weight(self) -> float:
        return {"low": 0.3, "medium": 0.6, "high": 1.0}.get(self.stakes, 0.6)


@dataclass
class ArchetypeProfile:
    """Ein SOTA-Archetyp als Gewichtungsvektor über MODULES."""
    id: str
    name: str
    source: str
    weights: Dict[str, float]
    cost_ms: Dict[str, float]
    notes: str = ""


ARCHETYPES: Tuple[ArchetypeProfile, ...] = (
    ArchetypeProfile(
        id="provenance_trace_arch",
        name="Provenance-Trace (Execution Provenance)",
        source="arxiv:2606.04990 — Evidence Tracing & Execution Provenance in LLM Agents",
        weights={
            "provenance_trace": 1.0,
            "deterministic_entity": 0.7,
            "fail_closed_gate": 0.8,
            "parallel_cluster": 0.6,
            "span_attribution": 0.3,
            "nli_backward": 0.2,
            "echtwelt_web": 0.1,
            "recovery_loop": 0.4,
        },
        cost_ms={
            "provenance_trace": 80,
            "deterministic_entity": 40,
            "fail_closed_gate": 30,
            "parallel_cluster": 50,
            "span_attribution": 120,
            "nli_backward": 150,
            "echtwelt_web": 200,
            "recovery_loop": 250,
        },
        notes="Semantische + prozedurale Herkunft; auditierbar, skaliert über Trace-Sharding.",
    ),
    ArchetypeProfile(
        id="backward_grounding_arch",
        name="Backward-Pass Grounding (Independent Verifier)",
        source="GroundGuard / RAG Verification Loops / Provenance NLI (EMNLP-Industry)",
        weights={
            "span_attribution": 1.0,
            "nli_backward": 0.95,
            "echtwelt_web": 0.75,
            "recovery_loop": 0.85,
            "parallel_cluster": 0.7,
            "provenance_trace": 0.25,
            "deterministic_entity": 0.5,
            "fail_closed_gate": 0.6,
        },
        cost_ms={
            "span_attribution": 100,
            "nli_backward": 180,
            "echtwelt_web": 220,
            "recovery_loop": 300,
            "parallel_cluster": 60,
            "provenance_trace": 70,
            "deterministic_entity": 35,
            "fail_closed_gate": 25,
        },
        notes="Generator und Verifier getrennt; Claim→Span→NLI; Recovery-Loop bei dünnen Belegen.",
    ),
    ArchetypeProfile(
        id="fail_closed_harness_arch",
        name="Fail-Closed Orchestration Harness",
        source="Maestro Order (arxiv:2606.23983) / verification.* IETF draft / agent-dag-pipeline",
        weights={
            "fail_closed_gate": 1.0,
            "recovery_loop": 0.9,
            "deterministic_entity": 0.8,
            "provenance_trace": 0.5,
            "parallel_cluster": 0.55,
            "nli_backward": 0.45,
            "span_attribution": 0.4,
            "echtwelt_web": 0.35,
        },
        cost_ms={
            "fail_closed_gate": 20,
            "recovery_loop": 280,
            "deterministic_entity": 30,
            "provenance_trace": 90,
            "parallel_cluster": 45,
            "nli_backward": 160,
            "span_attribution": 110,
            "echtwelt_web": 190,
        },
        notes="Pre-Action-Gates; Fehler/Timeout = Reject; geometrische Verlässlichkeitsverstärkung.",
    ),
)


@dataclass
class SynthesisResult:
    """Ergebnis der QUBO-Pipeline-Synthese."""
    selected_modules: List[str]
    energy: float
    estimated_latency_ms: float
    coverage_score: float
    archetype_blend: Dict[str, float]
    pipeline_stages: List[str]
    scalability: Dict[str, Any]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_modules": self.selected_modules,
            "energy": self.energy,
            "estimated_latency_ms": self.estimated_latency_ms,
            "coverage_score": self.coverage_score,
            "archetype_blend": self.archetype_blend,
            "pipeline_stages": self.pipeline_stages,
            "scalability": self.scalability,
            "notes": self.notes,
        }


def _blend_weights(profile: TaskProfile) -> Tuple[np.ndarray, Dict[str, float]]:
    """Gewichtet die drei Archetypen nach Task-Profil."""
    w = profile.stakes_weight()
    blends = {
        ARCHETYPES[0].id: 0.25 + 0.15 * w + (0.1 if profile.claim_count > 8 else 0),
        ARCHETYPES[1].id: 0.35 + (0.2 if profile.has_retrieved_docs else -0.1),
        ARCHETYPES[2].id: 0.25 + 0.25 * w,
    }
    if profile.needs_real_world:
        blends[ARCHETYPES[1].id] += 0.15
    total = sum(blends.values())
    blends = {k: v / total for k, v in blends.items()}

    benefit = np.zeros(len(MODULES))
    cost = np.zeros(len(MODULES))
    for arch in ARCHETYPES:
        coef = blends[arch.id]
        for mod in MODULES:
            benefit[MODULE_INDEX[mod]] += coef * arch.weights.get(mod, 0.0)
            cost[MODULE_INDEX[mod]] += coef * arch.cost_ms.get(mod, 0.0)
    return benefit, blends


def build_verification_qubo(profile: TaskProfile) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    QUBO x^T Q x + c^T x minimieren (x_i ∈ {0,1} = Modul aktiv).

    Linear c: Nutzen − Latenzstrafe
    Quadratisch Q: Synergien (+) und Redundanz (−)
    """
    n = len(MODULES)
    benefit, _ = _blend_weights(profile)
    stakes = profile.stakes_weight()
    budget = max(200, profile.latency_budget_ms)

    # Latenzstrafe pro Modul (skaliert mit Budget)
    latency_penalty = np.array(
        [
            ARCHETYPES[1].cost_ms.get(m, 50) / budget
            for m in MODULES
        ],
        dtype=np.float64,
    )

    c = -(benefit * (1.0 + 0.3 * stakes) - latency_penalty * 1.2)

    Q = np.zeros((n, n), dtype=np.float64)

    synergies = [
        ("provenance_trace", "fail_closed_gate", -0.35),
        ("span_attribution", "nli_backward", -0.45),
        ("nli_backward", "recovery_loop", -0.30),
        ("echtwelt_web", "recovery_loop", -0.25),
        ("parallel_cluster", "provenance_trace", -0.20),
        ("parallel_cluster", "span_attribution", -0.20),
        ("parallel_cluster", "nli_backward", -0.20),
        ("parallel_cluster", "echtwelt_web", -0.15),
        ("deterministic_entity", "fail_closed_gate", -0.28),
    ]
    redundancies = [
        ("span_attribution", "echtwelt_web", 0.12),
        ("nli_backward", "echtwelt_web", 0.10),
        ("provenance_trace", "span_attribution", 0.08),
    ]

    for a, b, w in synergies:
        i, j = MODULE_INDEX[a], MODULE_INDEX[b]
        Q[i, j] += w
        Q[j, i] += w
    for a, b, w in redundancies:
        i, j = MODULE_INDEX[a], MODULE_INDEX[b]
        Q[i, j] += w
        Q[j, i] += w

    # Pflichtmodule bei high stakes
    if stakes >= 0.9:
        c[MODULE_INDEX["fail_closed_gate"]] -= 0.8
    if profile.needs_real_world:
        c[MODULE_INDEX["echtwelt_web"]] -= 0.5
    if profile.has_retrieved_docs:
        c[MODULE_INDEX["nli_backward"]] -= 0.4
        c[MODULE_INDEX["span_attribution"]] -= 0.35

    # Skalierung: parallel_cluster lohnt sich ab vielen Claims
    if profile.claim_count >= 4:
        c[MODULE_INDEX["parallel_cluster"]] -= 0.45 * math.log1p(profile.claim_count)

    return Q, c, benefit


def _estimate_latency(selected: Sequence[str], profile: TaskProfile) -> float:
    _, blends = _blend_weights(profile)
    ms = 0.0
    for arch in ARCHETYPES:
        for mod in selected:
            ms += blends[arch.id] * arch.cost_ms.get(mod, 0.0)
    # Recovery nur wenn andere Checker aktiv
    if "recovery_loop" in selected and len(selected) > 2:
        ms *= 1.05
    if "parallel_cluster" in selected and profile.claim_count > 1:
        ms *= 0.55 + 0.45 / math.sqrt(profile.claim_count)
    return round(ms, 1)


def _pipeline_stages(selected: Sequence[str]) -> List[str]:
    stages: List[str] = []
    if "provenance_trace" in selected:
        stages.append("trace_capture: OpenTelemetry/PROV — Tool-Calls, Spans, Agent-Messages")
    if "parallel_cluster" in selected:
        stages.append("hadof_decompose: Claims in unabhängige Cluster → parallele Worker")
    if "deterministic_entity" in selected:
        stages.append("entity_match: Literal-Tokens (Datum, Zahl, Eigenname) gegen Kontext")
    if "span_attribution" in selected:
        stages.append("span_attribution: Satz → [source_id, start, end]")
    if "nli_backward" in selected:
        stages.append("nli_backward: passage ⇒ sentence (entails/contradicts/unknown)")
    if "echtwelt_web" in selected:
        stages.append("echtwelt_web: URL-Reachability + DuckDuckGo + Task-Sources")
    if "fail_closed_gate" in selected:
        stages.append("fail_closed_gate: Ambiguität/Timeout = HALT (verification.*-Semantik)")
    if "recovery_loop" in selected:
        stages.append("recovery_loop: re-retrieve → revise → reverify (budget-bounded)")
    return stages


def synthesize_verification_pipeline(
    profile: Optional[TaskProfile] = None,
    *,
    force_modules: Optional[Sequence[str]] = None,
) -> SynthesisResult:
    """
    QUBO-Synthese: wählt minimale Energie-Konfiguration unter Task-Profil.

    Skalierungsmodell (DQAOA/HADOF/NISQ-Hybrid):
      - QUBO = Routing-Layer (welche Module)
      - parallel_cluster = federierte Ausführung
      - klassische Merge + fail_closed = NISQ-Refinement-Äquivalent
    """
    profile = profile or TaskProfile()
    Q, c, benefit = build_verification_qubo(profile)
    n = len(MODULES)

    # Diagonale aus linearen Termen: x^T Q x mit Q_ii = c_i wenn off-diagonal separat
    Q_full = Q.copy()
    np.fill_diagonal(Q_full, np.diag(Q_full) + c)

    result = parallel_anneal(Q_full, steps=4000, n_restarts=8, n_samples=20)
    x = result["solution"].astype(np.int64)
    energy = float(result["energy"])

    selected = [MODULES[i] for i in range(n) if x[i] == 1]

    # Mindestpipeline: bei leerer Lösung Fallback
    if not selected:
        selected = ["fail_closed_gate", "echtwelt_web", "parallel_cluster"]

    if force_modules:
        for m in force_modules:
            if m in MODULE_INDEX and m not in selected:
                selected.append(m)

    # Budget-Repair: günstigste Module behalten wenn über Budget
    est = _estimate_latency(selected, profile)
    while est > profile.latency_budget_ms * 1.15 and len(selected) > 2:
        removable = [m for m in selected if m != "fail_closed_gate"]
        if not removable:
            break
        costs = {m: sum(a.cost_ms.get(m, 0) for a in ARCHETYPES) for m in removable}
        drop = max(removable, key=lambda m: costs[m])
        selected.remove(drop)
        est = _estimate_latency(selected, profile)

    coverage = float(
        sum(benefit[MODULE_INDEX[m]] for m in selected)
        / max(benefit.sum(), 1e-6)
    )
    _, blends = _blend_weights(profile)

    clusters = max(1, min(profile.claim_count, 16))
    notes = [
        "QUBO-Routing (NISQ-Äquivalent): nur Modulwahl, Ausführung klassisch.",
        f"DQAOA-Mapping: bis zu {clusters} parallele Claim-Cluster.",
        "HADOF-Mapping: unabhängige Subprobleme pro Cluster, federierte Aggregation.",
    ]
    if profile.stakes == "high":
        notes.append("High-stakes: fail_closed_gate priorisiert (Maestro/verification.*).")

    return SynthesisResult(
        selected_modules=selected,
        energy=energy,
        estimated_latency_ms=_estimate_latency(selected, profile),
        coverage_score=round(min(coverage, 1.0), 3),
        archetype_blend={k: round(v, 3) for k, v in blends.items()},
        pipeline_stages=_pipeline_stages(selected),
        scalability={
            "claim_clusters": clusters,
            "parallel_workers": min(clusters, 8),
            "routing_solver": "parallel_anneal",
            "execution_mode": "hybrid_classical",
            "federation": "per_cluster_verdict_merge",
        },
        notes=notes,
    )


def compare_archetypes() -> List[Dict[str, Any]]:
    """Liefert Vergleich der drei Grundparadigmen für Dokumentation/API."""
    return [
        {
            "id": a.id,
            "name": a.name,
            "source": a.source,
            "core_idea": a.notes,
            "top_modules": sorted(a.weights, key=lambda k: a.weights[k], reverse=True)[:4],
        }
        for a in ARCHETYPES
    ]


if __name__ == "__main__":
    import json

    prof = TaskProfile(
        stakes="high",
        latency_budget_ms=900,
        has_retrieved_docs=True,
        needs_real_world=True,
        claim_count=8,
        output_chars=4000,
    )
    syn = synthesize_verification_pipeline(prof)
    print("=== Archetyp-Vergleich (Juli 2026 SOTA) ===")
    print(json.dumps(compare_archetypes(), indent=2, ensure_ascii=False))
    print("\n=== QUBO-Synthese (gangbar + skalierbar) ===")
    print(json.dumps(syn.to_dict(), indent=2, ensure_ascii=False))
