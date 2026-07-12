# -*- coding: utf-8 -*-
"""
AscensionOS v9.4 - Substantielles AscensionCore (Coevolutionaer integriert)

Dieses AscensionCore ist die zentrale Heimat fuer:
- Alle grounded epistemischen Komponenten (Sisyphos, FailClosed, Psycholysis, MasterSeed)
- Den GenerationalEvolutionEngine (Inside-Out Evolution)
- Den UnifiedHeroicLLMCore
- Die CoEvolutionaryClosure (CEC, v9.3)
- Den PersistentSisyphosCycle (v9.4)

Wiederhergestellt in der v8.3-Konsolidierung: Die Datei war durch
Delta-Fragmente (5cd32ab, 781269f) ersetzt worden; Basis ist der letzte
vollstaendige v9.2-Stand (8f747dc) plus die CEC- und
PersistentSisyphos-Erweiterungen, jetzt korrekt ausformuliert.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from fusion_hero_os.core.universal_llm_router import (
        get_unified_llm_core,
        UnifiedHeroicLLMCore,
        SisyphosCycle,
        FailClosed,
    )
    from fusion_hero_os.core.psycholysis_trigger import PsycholysisTrigger
    from fusion_hero_os.core.heroic_core import MasterSeed
except Exception:
    UnifiedHeroicLLMCore = None
    PsycholysisTrigger = None
    SisyphosCycle = None
    FailClosed = None
    MasterSeed = None
    get_unified_llm_core = None

try:
    from ..evolution.generational_engine import GenerationalEvolutionEngine
except Exception:
    GenerationalEvolutionEngine = None

try:
    from .coevolutionary_closure import get_coevolutionary_closure, CoEvolutionaryClosure
except Exception:
    CoEvolutionaryClosure = None
    get_coevolutionary_closure = None

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None


class AscensionCore:
    """
    Das substantielle AscensionCore v9.4.

    Coevolutionaer aufgebaut:
    - Haelt alle zentralen grounded Komponenten
    - Integriert den GenerationalEvolutionEngine tief
    - Ist ueber die CoEvolutionaryClosure (CEC) mit anderen Tracks verbunden
    - Fuehrt den persistenten, stateful Sisyphos-Zyklus
    """

    def __init__(self):
        self.version = "9.4-coevolutionary"

        # Grounded Core Components
        self.llm: Optional["UnifiedHeroicLLMCore"] = (
            get_unified_llm_core() if get_unified_llm_core else None
        )
        self.sisyphos: Optional["SisyphosCycle"] = (
            getattr(self.llm, "sisyphos", None) if self.llm else None
        )
        self.psycholysis: Optional["PsycholysisTrigger"] = (
            getattr(self.llm, "psycholysis", None) if self.llm else None
        )
        self.fail_closed = FailClosed
        self.masterseed: Optional["MasterSeed"] = None  # wird bei Bedarf injiziert

        # Generational Evolution Engine (tief integriert)
        self.evolution_engine: Optional["GenerationalEvolutionEngine"] = None
        if GenerationalEvolutionEngine:
            self.evolution_engine = GenerationalEvolutionEngine(ascension_core=self)

        # CoevolutionaryClosure Integration (v9.3)
        self.cec: Optional["CoEvolutionaryClosure"] = None
        if get_coevolutionary_closure:
            self.cec = get_coevolutionary_closure()

        # Persistent Sisyphos (v9.4)
        self.persistent_sisyphos: Optional["PersistentSisyphosCycle"] = None
        if PersistentSisyphosCycle:
            self.persistent_sisyphos = PersistentSisyphosCycle()

        self.mode = "ASCENSION"

    # ------------------------------------------------------------------
    # Sisyphos
    # ------------------------------------------------------------------

    def get_sisyphos_state(self) -> Dict[str, Any]:
        if self.sisyphos:
            return self.sisyphos.get_state()
        return {}

    def step_sisyphos(self, load: float, notes: str = ""):
        """Persistenter Sisyphos-Schritt (v9.4) mit Historie."""
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.step(load, notes)
        return None

    def get_sisyphos_history(self, last_n: int = 10):
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.get_history(last_n)
        return []

    # ------------------------------------------------------------------
    # Status + Coevolution
    # ------------------------------------------------------------------

    def get_ascension_status(self) -> Dict[str, Any]:
        status = {
            "version": self.version,
            "mode": self.mode,
            "llm_available": self.llm is not None,
            "sisyphos_available": self.sisyphos is not None,
            "persistent_sisyphos_available": self.persistent_sisyphos is not None,
            "evolution_engine_available": self.evolution_engine is not None,
        }

        if self.sisyphos:
            status.update(self.get_sisyphos_state())

        if self.evolution_engine and self.evolution_engine.generations:
            status["evolution_summary"] = self.evolution_engine.get_evolution_summary()

        if self.cec:
            status["cec_status"] = self.cec.get_status()

        return status

    def notify_coevolutionary_change(self, source: str, change_type: str,
                                     payload: Dict[str, Any]) -> None:
        """Propagiert eine Aenderung in die CoEvolutionaryClosure (v9.3)."""
        if self.cec:
            self.cec.notify_change(source, change_type, payload)

    # ------------------------------------------------------------------
    # Evolution + LLM + MasterSeed
    # ------------------------------------------------------------------

    def run_generation(self, generations: int = 5) -> Dict[str, Any]:
        """Fuehrt Inside-Out Generationen aus (coevolutionaer)."""
        if not self.evolution_engine:
            return {"status": "GenerationalEvolutionEngine nicht verfuegbar"}

        current_state = {
            **self.get_sisyphos_state(),
            "fail_closed_active": True,
            "ascension_mode_active": True,
            "cross_layer_integration": 0.8,
        }

        results = self.evolution_engine.run_generations(current_state, generations=generations)
        summary = {
            "generations_run": len(results),
            "summary": self.evolution_engine.get_evolution_summary(),
        }
        self.notify_coevolutionary_change("ascension_core", "generation_run", summary)
        return summary

    def ask(self, prompt: str, context: str = "ascension") -> Any:
        """Ascension-spezifische LLM-Anfrage (falls LLM verfuegbar)."""
        if self.llm:
            return self.llm.ask(prompt, context=context)
        return None

    def register_masterseed(self, masterseed: "MasterSeed") -> None:
        self.masterseed = masterseed


_ascension_core_instance: Optional[AscensionCore] = None


def get_ascension_core() -> AscensionCore:
    global _ascension_core_instance
    if _ascension_core_instance is None:
        _ascension_core_instance = AscensionCore()
    return _ascension_core_instance
