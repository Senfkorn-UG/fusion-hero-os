# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.5 — Universal LLM Router

**Dynamic, non-fixed task-to-agent assignment across all layers.**

- Providers declare capabilities (code, creative, heroic_core, current_events...)
- Router computes real-time scores from: capability match + health + latency + failure_rate + heroic context
- Assignment is NEVER a fixed if-elif. It is scored and re-ranked every request.
- Works on Layer 0 (MasterSeed), Layer 4/5 (PMS/QuadCore), orchestration, agents, dashboard.
- Merged & optimized with existing provider abstraction + QUBO-ready extension point.
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


class UniversalLLMRouter:
    """Zentrale dynamische Zuweisungsinstanz für alle LLM/KI-Agenten.

    Die Zuweisung ist NICHT fest. Sie wird bei jedem Request neu berechnet aus:
    - Kategorie-Match (Capability-Score der Provider)
    - Aktueller Health (Latency, Failure-Rate)
    - Heroic Core State (MasterSeed, Mode, volatile History)
    - Optional: QUBO-Optimierung für Batch-Tasks (Extension Point)
    """

    def __init__(self, heroic_core: Optional["QuadCoreBridge"] = None) -> None:
        self.heroic_core = heroic_core
        self._providers: Dict[str, BaseLLMProvider] = {}

        if ClaudeProvider:
            c = ClaudeProvider()
            if c.is_available():
                self._providers["claude"] = c
        if GrokProvider:
            g = GrokProvider()
            if g.is_available():
                self._providers["grok"] = g
        if EveryAPIProvider:
            e = EveryAPIProvider()
            if e.is_available():
                self._providers["everyapi"] = e

        internal = InternalFallbackProvider(heroic_core=heroic_core)
        self._providers["fusion-hero"] = internal

        self.default_order = list(self._providers.keys())

    def _classify_query(self, prompt: str) -> str:
        p = prompt.lower()
        rules = {
            "code": ["code", "programmier", "script", "debug", "qubo", "implement"],
            "current_events": ["heute", "aktuell", "news", "spacex", "grok"],
            "simple_fact": ["was ist", "wie viel", "wann", "definition"],
            "creative": ["schreib", "erzähl", "gedicht", "meme", "vision"],
            "heroic_core": ["masterseed", "layer 0", "pms", "quadcore", "phoenix", "fail-closed", "heroic"],
        }
        for cat, kws in rules.items():
            if any(kw in p for kw in kws):
                return cat
        return "default"

    def _score_provider(self, name: str, category: str, health: Dict[str, Any]) -> float:
        """Dynamic score: capability match + health penalty. Not fixed."""
        provider = self._providers.get(name)
        if not provider:
            return 0.0

        cap = provider.capabilities.get(category, provider.capabilities.get("default", 0.5))

        h = health.get(name, {})
        latency = h.get("last_latency_ms", 800)
        failures = h.get("failure_count", 0)

        latency_pen = min(latency / 2500.0, 0.8)
        failure_pen = min(failures / 8.0, 0.7)

        # Heroic context boost for internal on heroic_core tasks
        heroic_boost = 0.15 if (name == "fusion-hero" and category == "heroic_core") else 0.0

        score = cap * 0.65 - latency_pen * 0.20 - failure_pen * 0.15 + heroic_boost
        return max(0.05, min(0.98, score))

    def assign_dynamic(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Returns the best provider + score + reason. Assignment is computed fresh every time."""
        category = self._classify_query(prompt)
        health = self.status().get("health", {})

        scored = []
        for name in self._providers:
            score = self._score_provider(name, category, health)
            scored.append((name, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = scored[0]

        reason = f"category={category} | score={best_score:.3f} | health={health.get(best_name, {})}"
        return {
            "provider": best_name,
            "score": best_score,
            "category": category,
            "reason": reason,
            "alternatives": scored[1:3],
        }

    def route(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResult:
        start = time.time()
        assignment = self.assign_dynamic(prompt, system_prompt)

        if force_provider and force_provider in self._providers:
            chosen = force_provider
        else:
            chosen = assignment["provider"]

        provider = self._providers[chosen]
        used_chain = [chosen]

        try:
            result = provider.generate(prompt, system_prompt=system_prompt, category=assignment["category"])
            result.fallback_chain = used_chain
            result.meta["assignment"] = assignment
            if result.success:
                return result
        except Exception as e:
            pass

        # Fallback to next best if primary failed
        for alt_name, _ in assignment.get("alternatives", []):
            if alt_name in self._providers and alt_name != chosen:
                used_chain.append(alt_name)
                try:
                    result = self._providers[alt_name].generate(prompt, system_prompt=system_prompt)
                    result.fallback_chain = used_chain
                    return result
                except Exception:
                    continue

        # Last resort: internal
        if "fusion-hero" in self._providers and chosen != "fusion-hero":
            used_chain.append("fusion-hero")
            return self._providers["fusion-hero"].generate(prompt, system_prompt=system_prompt)

        return LLMResult("system-error", "Dynamic assignment failed for all providers", (time.time()-start)*1000, used_chain, success=False)

    async def aroute(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResult:
        return await asyncio.to_thread(self.route, prompt, system_prompt, force_provider)

    def status(self) -> Dict[str, Any]:
        return {
            "version": "v8.5-dynamic-assignment",
            "configured_providers": list(self._providers.keys()),
            "heroic_core_connected": self.heroic_core is not None,
            "health": {name: p.health() for name, p in self._providers.items()},
        }


_router_instance: Optional[UniversalLLMRouter] = None

def get_universal_llm_router(heroic_core: Optional["QuadCoreBridge"] = None) -> UniversalLLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = UniversalLLMRouter(heroic_core=heroic_core)
    elif heroic_core and not _router_instance.heroic_core:
        _router_instance.heroic_core = heroic_core
    return _router_instance


if __name__ == "__main__":
    router = get_universal_llm_router()
    print("v8.5 Dynamic Assignment Test:", router.assign_dynamic("Schreibe Code für einen QUBO Scheduler"))
