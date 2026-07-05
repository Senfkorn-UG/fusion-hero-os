"""HeroicLLM-EA Orchestrator — Proposal Engine + Evolutionary Selector."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from fusion_hero_os.core.base_module import BaseModule, ReviewResult


class LLMProvider(Protocol):
    """Austauschbares LLM-Interface — kein hartkodierter Provider."""

    def propose(self, prompt: str, n: int = 1) -> List[str]: ...


@dataclass
class ProposalRecord:
    text: str
    generation: int
    fitness: float
    peer_review_score: float
    performance_score: float
    consistency_score: float
    created_at: float = field(default_factory=time.time)

    @property
    def proposal_id(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:12]


class StubLLMProvider:
    """Deterministischer Stub für Tests — kein Netzwerk."""

    def propose(self, prompt: str, n: int = 1) -> List[str]:
        base = prompt.strip() or "empty-prompt"
        return [f"{base}::variant-{i}" for i in range(max(1, n))]


class MutationMemory:
    """Hierarchisches Mutations-Gedächtnis (Generation → Elite-Proposals)."""

    def __init__(self, max_per_generation: int = 20) -> None:
        self._store: Dict[int, List[ProposalRecord]] = {}
        self.max_per_generation = max_per_generation

    def remember(self, record: ProposalRecord) -> None:
        bucket = self._store.setdefault(record.generation, [])
        bucket.append(record)
        bucket.sort(key=lambda r: r.fitness, reverse=True)
        if len(bucket) > self.max_per_generation:
            del bucket[self.max_per_generation:]

    def best(self, generation: Optional[int] = None) -> Optional[ProposalRecord]:
        if generation is not None:
            items = self._store.get(generation, [])
            return items[0] if items else None
        all_items = [r for gen in sorted(self._store) for r in self._store[gen]]
        return max(all_items, key=lambda r: r.fitness, default=None)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generations": len(self._store),
            "total": sum(len(v) for v in self._store.values()),
            "best_fitness": (self.best().fitness if self.best() else None),
        }


def fitness_function(
    text: str,
    *,
    peer_review_score: float,
    performance_score: float,
    consistency_score: float,
) -> float:
    """
    Fitness = gewichtete Kombination aus Konsistenz, Performance, PeerReview.
    Dokumentiert und testbar — kein versteckter LLM-Qualitätsanspruch.
    """
    w_cons, w_perf, w_peer = 0.35, 0.35, 0.30
    length_penalty = min(1.0, len(text) / 500.0)
    return (
        w_cons * consistency_score
        + w_perf * performance_score
        + w_peer * peer_review_score
    ) * length_penalty


class HeroicLLMEAOrchestrator(BaseModule):
    """LLM Proposal Engine + Evolutionary Selector (BaseModule-kompatibel)."""

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        super().__init__()
        self.llm: LLMProvider = llm or StubLLMProvider()
        self.memory = MutationMemory()
        self.generation = 0

    def _score_proposal(self, text: str, context: Dict[str, Any]) -> ProposalRecord:
        peer = float(context.get("peer_review_score", 0.5))
        perf = float(context.get("performance_score", 0.5))
        cons = float(context.get("consistency_score", 0.7))
        fit = fitness_function(text, peer_review_score=peer, performance_score=perf, consistency_score=cons)
        return ProposalRecord(
            text=text,
            generation=self.generation,
            fitness=fit,
            peer_review_score=peer,
            performance_score=perf,
            consistency_score=cons,
        )

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        prompt = str(payload.get("prompt", ""))
        n_proposals = int(payload.get("n_proposals", 3))
        select_top = int(payload.get("select_top", 1))

        proposals = self.llm.propose(prompt, n=n_proposals)
        scored = [self._score_proposal(p, payload) for p in proposals]
        scored.sort(key=lambda r: r.fitness, reverse=True)
        elites = scored[: max(1, select_top)]

        for record in scored:
            self.memory.remember(record)

        self.generation += 1
        best = elites[0]
        return {
            "generation": self.generation - 1,
            "best": {
                "id": best.proposal_id,
                "text": best.text,
                "fitness": best.fitness,
            },
            "elites": [
                {"id": e.proposal_id, "fitness": e.fitness, "text": e.text[:120]}
                for e in elites
            ],
            "memory": self.memory.snapshot(),
            "status": "stub_llm" if isinstance(self.llm, StubLLMProvider) else "external_llm",
        }

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        from fusion_hero_os.core.base_module import ReviewCriterion

        has_llm = not isinstance(self.llm, StubLLMProvider)
        criteria = [
            ReviewCriterion("LLM-Interface austauschbar", True, "Protocol + StubLLMProvider"),
            ReviewCriterion("Fitness dokumentiert", True, "consistency+performance+peer_review"),
            ReviewCriterion("Echter LLM-Provider", has_llm, "Default ist Stub — kein Netzwerk"),
            ReviewCriterion("Mutations-Gedächtnis", True, f"generations={self.memory.snapshot()['generations']}"),
        ]
        return ReviewResult(module=self.name, criteria=criteria)