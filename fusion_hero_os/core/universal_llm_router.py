# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.4 — Universal LLM Router (Grok + Claude + EveryAPI + Internal)

Vollständig refaktoriert auf Provider-Abstraktion (BaseLLMProvider).
- Intelligente Klassifikation + dynamische Routing-Order bleibt im Router
- Alle API-Details sind jetzt in dedizierten Providern (sauber, testbar, erweiterbar)
- Heroic Core Context Injection + Async-Support + Health-Tracking + Fallback-Chain
- Unified LLMResult aus core.models / providers.base

Alles mit allem verdrahtet: Orchestrator ↔ Router ↔ Providers ↔ Heroic Core (MasterSeed/QuadCore)
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .heroic_core_orchestrator import QuadCoreBridge

# Import the new abstraction
try:
    from ..providers.base import LLMResult, BaseLLMProvider
    from ..providers.claude_provider import ClaudeProvider
    from ..providers.grok_provider import GrokProvider
    from ..providers.everyapi_provider import EveryAPIProvider
    from ..providers.internal_provider import InternalFallbackProvider
except Exception:  # graceful for import order during bootstrap
    LLMResult = None  # type: ignore
    BaseLLMProvider = object  # type: ignore
    ClaudeProvider = None
    GrokProvider = None
    EveryAPIProvider = None
    InternalFallbackProvider = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


ProviderName = str


class UniversalLLMRouter:
    """Zentrale KI-Schnittstelle von Fusion Hero OS v8.4

    Der Router orchestriert nur noch:
    - Prompt-Klassifikation
    - Routing-Order nach Kategorie
    - Heroic-Context-Injection
    - Fallback-Logik

    Die eigentlichen API-Calls sind komplett in die Provider ausgelagert.
    """

    def __init__(self, heroic_core: Optional["QuadCoreBridge"] = None) -> None:
        self.heroic_core = heroic_core

        # Instanziiere alle Provider (einige sind None wenn Keys fehlen)
        self._providers: Dict[str, BaseLLMProvider] = {}
        if ClaudeProvider:
            claude = ClaudeProvider()
            if claude.is_available():
                self._providers["claude"] = claude
        if GrokProvider:
            grok = GrokProvider()
            if grok.is_available():
                self._providers["grok"] = grok
        if EveryAPIProvider:
            every = EveryAPIProvider()
            if every.is_available():
                self._providers["everyapi"] = every

        # Internal Fallback ist immer da
        internal = InternalFallbackProvider(heroic_core=heroic_core)
        self._providers["fusion-hero"] = internal

        self.default_order: List[str] = ["claude", "grok", "everyapi", "fusion-hero"]

        self.classification_rules: Dict[str, List[str]] = {
            "code": ["code", "programmier", "script", "funktion", "klasse", "debug", "fehler", "implementier", "refactor", "qubo"],
            "current_events": ["heute", "aktuell", "news", "nachrichten", "was passiert", "grok", "xai", "spacex"],
            "simple_fact": ["was ist", "wie viel", "wann", "wo", "wer ist", "definition"],
            "creative": ["schreib", "erzähl", "gedicht", "geschichte", "kreativ", "meme", "vision", "coal canary"],
            "heroic_core": ["masterseed", "layer 0", "pms", "quadcore", "phoenix", "fail-closed"],
        }

    def _classify_query(self, prompt: str) -> str:
        p = prompt.lower()
        for category, keywords in self.classification_rules.items():
            if any(kw in p for kw in keywords):
                return category
        return "default"

    def _get_routing_order(self, category: str) -> List[str]:
        if category in ("code", "heroic_core"):
            return ["claude", "grok", "everyapi", "fusion-hero"]
        elif category == "current_events":
            return ["grok", "claude", "everyapi", "fusion-hero"]
        elif category == "simple_fact":
            return ["everyapi", "grok", "claude", "fusion-hero"]
        elif category == "creative":
            return ["claude", "grok", "everyapi", "fusion-hero"]
        else:
            return self.default_order.copy()

    def route(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_provider: Optional[str] = None,
    ) -> LLMResult:
        start = time.time()
        category = self._classify_query(prompt)
        order = self._get_routing_order(category)

        if force_provider and force_provider in self._providers:
            order = [force_provider] + [p for p in order if p != force_provider]

        used_chain: List[str] = []
        last_result: Optional[LLMResult] = None

        for provider_name in order:
            if provider_name not in self._providers:
                continue
            provider = self._providers[provider_name]
            used_chain.append(provider_name)
            try:
                result = provider.generate(
                    prompt,
                    system_prompt=system_prompt,
                    category=category,
                )
                result.fallback_chain = used_chain
                if result.success:
                    return result
                last_result = result
            except Exception as e:  # safety net
                last_result = LLMResult(
                    provider_name,
                    "",
                    success=False,
                    error=str(e)[:200],
                    fallback_chain=used_chain,
                )
                continue

        # Total failure – return last error or generic
        if last_result:
            return last_result
        return LLMResult(
            "system-error",
            "Alle Provider fehlgeschlagen oder nicht konfiguriert.",
            (time.time() - start) * 1000,
            used_chain,
            success=False,
            error="no_provider_available",
        )

    async def aroute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_provider: Optional[str] = None,
    ) -> LLMResult:
        """Non-blocking wrapper for Orchestrator and async Agents."""
        return await asyncio.to_thread(self.route, prompt, system_prompt, force_provider)

    def status(self) -> Dict[str, Any]:
        return {
            "version": "v8.4-provider-abstraction",
            "configured_providers": list(self._providers.keys()),
            "heroic_core_connected": self.heroic_core is not None,
            "health": {name: p.health() for name, p in self._providers.items()},
            "default_order": self.default_order,
            "classification_rules": list(self.classification_rules.keys()),
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
    print("Universal LLM Router v8.4 Status:", router.status())
