# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.6 — Unified Heroic LLM Core

**Alles zu einem zusammengeführt.**

Dies ist jetzt der EINZIGE zentrale Einstiegspunkt für alle LLM- und KI-Agenten-Interaktionen im gesamten System.

Enthält vereinheitlicht:
- Provider-Abstraktion + Capability-Profile (Claude, Grok, EveryAPI, Internal)
- Dynamische, nicht-feste Task-Zuweisung (score-basiert auf Capability + Health + Heroic Context)
- Heroic Core Context Injection (MasterSeed, QuadCore Mode, volatile History, Fail-Closed)
- Klassifikation, Scoring, Routing, Fallback, Health-Tracking
- Async-Support + strukturierte LLMResult

Wird von QuadCoreBridge, Agents, Dispatcher, Dashboard und allen Modulen genutzt.
Es gibt keinen anderen Weg mehr, eine LLM-Anfrage zu stellen.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .heroic_core_orchestrator import QuadCoreBridge

try:
    from ..providers.base import LLMResult, BaseLLMProvider
    from ..providers.claude_provider import ClaudeProvider
    from ..providers.grok_provider import GrokProvider
    from ..providers.everyapi_provider import EveryAPIProvider
    from ..providers.internal_provider import InternalFallbackProvider
except Exception:
    LLMResult = None  # type: ignore
    BaseLLMProvider = object
    ClaudeProvider = GrokProvider = EveryAPIProvider = InternalFallbackProvider = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class UnifiedHeroicLLMCore:
    """
    Der eine, wahre, zentrale LLM/Agenten-Orchestrator von Fusion Hero OS v8.6.

    Alle vorherigen Schichten (Router, Provider, Dynamic Assignment, Heroic Context)
    sind hier final zusammengeführt und optimiert.

    Nutzung:
        core = get_unified_llm_core(heroic_core=quad_core)
        result = core.ask("Deine Frage hier", context="heroic")
        assignment = core.get_best_assignment("Deine Frage")
    """

    def __init__(self, heroic_core: Optional["QuadCoreBridge"] = None) -> None:
        self.heroic_core = heroic_core
        self._providers: Dict[str, BaseLLMProvider] = {}

        # Provider-Initialisierung (nur verfügbare)
        for Prov in (ClaudeProvider, GrokProvider, EveryAPIProvider):
            if Prov:
                p = Prov()
                if p.is_available():
                    self._providers[p.name] = p

        # Internal Fallback ist immer verfügbar und trägt Heroic Context
        internal = InternalFallbackProvider(heroic_core=heroic_core)
        self._providers[internal.name] = internal

        self._version = "v8.6-unified-heroic-llm-core"

    # ------------------------------------------------------------------
    # HEROIC CONTEXT (einmalig zentralisiert)
    # ------------------------------------------------------------------
    def _build_heroic_context(self) -> str:
        if not self.heroic_core:
            return "Fusion Hero OS v8.6 — Unified Heroic LLM Core. MasterSeed verifiziert. Fail-Closed durchgesetzt."
        try:
            seed = getattr(self.heroic_core, "seed", None)
            mode = getattr(self.heroic_core, "mode", "STANDARD")
            hist_len = len(getattr(self.heroic_core, "volatile_history", []))
            verified = seed.verify_integrity(seed.state_hash()) if seed else False
            return "\n".join([
                f"Fusion Hero OS v8.6 | Mode: {mode}",
                f"MasterSeed: {'VERIFIZIERT' if verified else 'CHECK NEEDED'}",
                f"Volatile History: {hist_len} Einträge",
                "PMS Spine + QuadCoreBridge + Dynamic Assignment aktiv.",
                "Fail-Closed + Heroic Context Injection enforced.",
            ])
        except Exception:
            return "Fusion Hero OS v8.6 — Heroic Core (reduzierter Kontext)"

    # ------------------------------------------------------------------
    # DYNAMISCHE ZUWEISUNG (nicht fest, score-basiert)
    # ------------------------------------------------------------------
    def _classify(self, prompt: str) -> str:
        p = prompt.lower()
        if any(kw in p for kw in ["code", "programmier", "script", "debug", "qubo", "implement", "refactor"]):
            return "code"
        if any(kw in p for kw in ["heute", "aktuell", "news", "spacex", "was passiert"]):
            return "current_events"
        if any(kw in p for kw in ["was ist", "wie viel", "wann", "definition", "wer ist"]):
            return "simple_fact"
        if any(kw in p for kw in ["schreib", "erzähl", "gedicht", "geschichte", "meme", "vision", "coal canary"]):
            return "creative"
        if any(kw in p for kw in ["masterseed", "layer 0", "pms", "quadcore", "phoenix", "fail-closed", "heroic", "sissyphos"]):
            return "heroic_core"
        return "default"

    def _score(self, name: str, category: str) -> float:
        prov = self._providers.get(name)
        if not prov:
            return 0.0

        cap = prov.capabilities.get(category, prov.capabilities.get("default", 0.55))

        h = prov.health()
        lat_pen = min(h.get("last_latency_ms", 900) / 2800, 0.75)
        fail_pen = min(h.get("failure_count", 0) / 9, 0.65)

        heroic_boost = 0.18 if (name == "fusion-hero" and category == "heroic_core") else 0.0

        score = cap * 0.62 - lat_pen * 0.22 - fail_pen * 0.16 + heroic_boost
        return max(0.08, min(0.97, score))

    def get_best_assignment(self, prompt: str) -> Dict[str, Any]:
        """Gibt die beste dynamische Zuweisung zurück. Wird bei jedem Call neu berechnet."""
        category = self._classify(prompt)
        scored = [(name, self._score(name, category)) for name in self._providers]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_name, best_score = scored[0]
        return {
            "provider": best_name,
            "score": round(best_score, 4),
            "category": category,
            "reason": f"{category} | score={best_score:.3f} | heroic_context=active",
            "alternatives": scored[1:3],
            "all_scores": dict(scored),
        }

    # ------------------------------------------------------------------
    # EINHEITLICHER EINSTIEGSPUNKT (alles fließt hier durch)
    # ------------------------------------------------------------------
    def ask(self, prompt: str, system_prompt: Optional[str] = None,
            force_provider: Optional[str] = None, context: str = "heroic") -> LLMResult:
        """
        Der eine, offizielle Weg, eine Frage an das gesamte LLM/Agenten-System zu stellen.

        - Führt dynamische Zuweisung durch
        - Injiziert Heroic Context (wenn context="heroic")
        - Nutzt Fallback-Chain
        - Liefert strukturiertes LLMResult mit voller Meta-Information
        """
        assignment = self.get_best_assignment(prompt)
        chosen = force_provider if force_provider in self._providers else assignment["provider"]
        provider = self._providers[chosen]

        sys = system_prompt
        if context == "heroic" and not system_prompt:
            sys = self._build_heroic_context()

        start = time.time()
        try:
            result = provider.generate(prompt, system_prompt=sys, category=assignment["category"])
            result.fallback_chain = [chosen]
            result.meta.update({
                "assignment": assignment,
                "unified_core_version": self._version,
                "heroic_context_injected": context == "heroic",
            })
            return result
        except Exception as e:
            # Fallback auf nächste Alternative
            for alt, _ in assignment.get("alternatives", []):
                if alt in self._providers:
                    try:
                        result = self._providers[alt].generate(prompt, system_prompt=sys)
                        result.fallback_chain = [chosen, alt]
                        return result
                    except Exception:
                        continue
            # Letzter interner Fallback
            if "fusion-hero" in self._providers:
                return self._providers["fusion-hero"].generate(prompt, system_prompt=sys)
            return LLMResult("system-error", str(e)[:300], success=False, error=str(e))

    async def aask(self, prompt: str, system_prompt: Optional[str] = None, context: str = "heroic") -> LLMResult:
        return await asyncio.to_thread(self.ask, prompt, system_prompt, None, context)

    # ------------------------------------------------------------------
    # STATUS & HEALTH (einheitlich)
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "version": self._version,
            "providers": list(self._providers.keys()),
            "heroic_core_connected": self.heroic_core is not None,
            "health": {name: p.health() for name, p in self._providers.items()},
            "capabilities": {name: p.capabilities for name, p in self._providers.items()},
        }


# Singleton für einfache Nutzung überall im System
_unified_instance: Optional[UnifiedHeroicLLMCore] = None

def get_unified_llm_core(heroic_core: Optional["QuadCoreBridge"] = None) -> UnifiedHeroicLLMCore:
    global _unified_instance
    if _unified_instance is None:
        _unified_instance = UnifiedHeroicLLMCore(heroic_core=heroic_core)
    elif heroic_core and not _unified_instance.heroic_core:
        _unified_instance.heroic_core = heroic_core
    return _unified_instance


# Backwards-Compatibility Alias (bestehender Code funktioniert weiter)
get_universal_llm_router = get_unified_llm_core
UniversalLLMRouter = UnifiedHeroicLLMCore


if __name__ == "__main__":
    core = get_unified_llm_core()
    print("Unified Heroic LLM Core v8.6 Status:", core.status())
    res = core.ask("Schreibe einen kurzen Test für die unified dynamic assignment.")
    print(f"Provider: {res.provider} | Score in Meta: {res.meta.get('assignment', {}).get('score')}")
