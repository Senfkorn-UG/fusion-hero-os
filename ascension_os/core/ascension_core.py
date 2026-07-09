# -*- coding: utf-8 -*-
"""
AscensionOS v9.2 - Substantielles AscensionCore (Coevolutionär integriert)

Dieses AscensionCore ist jetzt die zentrale Heimat für:
- Alle grounded epistemischen Komponenten (Sisyphos, FailClosed, Psycholysis, MasterSeed)
- Den GenerationalEvolutionEngine (Inside-Out Evolution)
- Den UnifiedHeroicLLMCore

Es dient als coevolutionärer Kern, der Heroic- und Ascension-Track zusammenführt.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from fusion_hero_os.core.universal_llm_router import get_unified_llm_core, UnifiedHeroicLLMCore
    from fusion_hero_os.core.psycholysis_trigger import PsycholysisTrigger
    from fusion_hero_os.core.universal_llm_router import SisyphosCycle, FailClosed
    from fusion_hero_os.core.heroic_core import MasterSeed
except Exception:
    UnifiedHeroicLLMCore = None
    PsycholysisTrigger = None
    SisyphosCycle = None
    FailClosed = None
    MasterSeed = None

try:
    from ..evolution.generational_engine import GenerationalEvolutionEngine
except Exception:
    GenerationalEvolutionEngine = None


class AscensionCore:
    """
    Das substantielle AscensionCore v9.2.

    Coevolutionär aufgebaut:
    - Hält alle zentralen grounded Komponenten
    - Integriert den GenerationalEvolutionEngine tief
    - Kann im reinen Ascension-Modus oder hybrid betrieben werden
    """

    def __init__(self):
        self.version = "9.2-coevolutionary"

        # Grounded Core Components
        self.llm: Optional[UnifiedHeroicLLMCore] = get_unified_llm_core() if get_unified_llm_core else None
        self.sisyphos: Optional[SisyphosCycle] = getattr(self.llm, "sisyphos", None) if self.llm else None
        self.psycholysis: Optional[PsycholysisTrigger] = getattr(self.llm, "psycholysis", None) if self.llm else None
        self.fail_closed = FailClosed
        self.masterseed: Optional[MasterSeed] = None  # wird bei Bedarf injiziert

        # Generational Evolution Engine (tief integriert)
        self.evolution_engine: Optional[GenerationalEvolutionEngine] = None
        if GenerationalEvolutionEngine:
            self.evolution_engine = GenerationalEvolutionEngine(ascension_core=self)

        self.mode = "ASCENSION"

    def get_sisyphos_state(self) -> Dict[str, Any]:
        if self.sisyphos:
            return self.sisyphos.get_state()
        return {}

    def get_ascension_status(self) -> Dict[str, Any]:
        status = {
            "version": self.version,
            "mode": self.mode,
            "llm_available": self.llm is not None,
            "sisyphos_available": self.sisyphos is not None,
            "evolution_engine_available": self.evolution_engine is not None,
        }

        if self.sisyphos:
            status.update(self.get_sisyphos_state())

        if self.evolution_engine and self.evolution_engine.generations:
            status["evolution_summary"] = self.evolution_engine.get_evolution_summary()

        return status

    def run_generation(self, generations: int = 5) -> Dict[str, Any]:
        """Führt Inside-Out Generationen aus (coevolutionär)."""
        if not self.evolution_engine:
            return {"status": "GenerationalEvolutionEngine nicht verfügbar"}

        current_state = {
            **self.get_sisyphos_state(),
            "fail_closed_active": True,
            "ascension_mode_active": True,
            "cross_layer_integration": 0.8,
        }

        results = self.evolution_engine.run_generations(current_state, generations=generations)
        return {
            "generations_run": len(results),
            "summary": self.evolution_engine.get_evolution_summary(),
        }

    def ask(self, prompt: str, context: str = "ascension") -> Any:
        """Ascension-spezifische LLM-Anfrage (falls LLM verfügbar)."""
        if self.llm:
            return self.llm.ask(prompt, context=context)
        return None

    def register_masterseed(self, masterseed: MasterSeed):
        self.masterseed = masterseed


_ascension_core_instance: Optional[AscensionCore] = None

def get_ascension_core() -> AscensionCore:
    global _ascension_core_instance
    if _ascension_core_instance is None:
        _ascension_core_instance = AscensionCore()
    return _ascension_core_instance
