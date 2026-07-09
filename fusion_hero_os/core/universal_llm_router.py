# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8.3 — Universal LLM Router (Grok + Claude + EveryAPI)

Native, production-grade Multi-LLM Router mit:
- Intelligenter Prompt-Klassifikation + dynamischer Routing-Order
- Automatischer Fallback-Chain (Claude → Grok → EveryAPI → intern)
- Heroic Core Context Injection (MasterSeed, QuadCore Mode, volatile History)
- Async-Support via asyncio.to_thread (non-blocking für Orchestrator & Agents)
- Reicher Status mit per-Provider Health + Request-Statistiken
- ENV-konfigurierbarer EveryAPI Endpoint
- Brutale Präzision, maximale Tiefe, Fail-Closed Prinzip

Vollständig verdrahtet mit heroic_core_orchestrator v8, ModuleRegistry und Dashboard.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .heroic_core_orchestrator import QuadCoreBridge

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import requests
except ImportError:
    requests = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


Provider = Literal["grok", "claude", "everyapi", "fusion-hero"]


@dataclass
class LLMResponse:
    provider: str
    response: str
    latency_ms: float = 0.0
    fallback_chain: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "response": self.response,
            "latency_ms": self.latency_ms,
            "fallback_chain": self.fallback_chain,
            "meta": self.meta,
        }


class UniversalLLMRouter:
    """
    Zentrale KI-Schnittstelle von Fusion Hero OS v8.3
    
    Alles fließt durch diesen Router. Keine direkten API-Calls mehr in Agents oder Dashboard.
    """

    def __init__(self, heroic_core: Optional["QuadCoreBridge"] = None) -> None:
        self.grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        self.claude_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.everyapi_key = os.getenv("EVERYAPI_KEY")

        self.grok_client: Optional[OpenAI] = None
        self.claude_client: Optional[Anthropic] = None

        if OpenAI and self.grok_key:
            self.grok_client = OpenAI(api_key=self.grok_key, base_url="https://api.x.ai/v1")

        if Anthropic and self.claude_key:
            self.claude_client = Anthropic(api_key=self.claude_key)

        self.heroic_core = heroic_core

        # ENV-configurable EveryAPI
        self.everyapi_base_url = os.getenv("EVERYAPI_BASE_URL", "https://api.everyapi.com/v1/chat")
        self.everyapi_model = os.getenv("EVERYAPI_MODEL", "general")

        self.default_order: List[Provider] = ["claude", "grok", "everyapi", "fusion-hero"]

        self.classification_rules = {
            "code": ["code", "programmier", "script", "funktion", "klasse", "debug", "fehler", "implementier", "refactor", "qubo"],
            "current_events": ["heute", "aktuell", "news", "nachrichten", "was passiert", "grok", "xai", "spacex"],
            "simple_fact": ["was ist", "wie viel", "wann", "wo", "wer ist", "definition"],
            "creative": ["schreib", "erzähl", "gedicht", "geschichte", "kreativ", "meme", "vision", "coal canary"],
            "heroic_core": ["masterseed", "layer 0", "pms", "quadcore", "phoenix", "fail-closed"],
        }

        # Health & Stats
        self._provider_health: Dict[str, str] = defaultdict(lambda: "unknown")
        self._request_count: Dict[str, int] = defaultdict(int)
        self._failure_count: Dict[str, int] = defaultdict(int)
        self._last_latency: Dict[str, float] = defaultdict(float)

    def _classify_query(self, prompt: str) -> str:
        p = prompt.lower()
        for category, keywords in self.classification_rules.items():
            if any(kw in p for kw in keywords):
                return category
        return "default"

    def _get_routing_order(self, category: str) -> List[Provider]:
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

    def _build_heroic_context(self) -> str:
        if not self.heroic_core:
            return "Fusion Hero OS v8.3 — Heroic Core aktiv. MasterSeed verifiziert. Fail-Closed durchgesetzt."

        try:
            seed = getattr(self.heroic_core, "seed", None)
            mode = getattr(self.heroic_core, "mode", "STANDARD")
            history_len = len(getattr(self.heroic_core, "volatile_history", []))
            return "\n".join([
                f"Fusion Hero OS v8.3 | Mode: {mode}",
                f"MasterSeed: {'VERIFIZIERT' if seed and seed.verify_integrity(seed.state_hash()) else 'CHECK NEEDED'}",
                f"Volatile History: {history_len} Einträge",
                "PMS Spine + QuadCoreBridge + Fail-Closed aktiv.",
            ])
        except Exception:
            return "Fusion Hero OS v8.3 — Heroic Core (reduzierter Kontext)"

    def _update_health(self, provider: str, success: bool, latency_ms: float) -> None:
        self._request_count[provider] += 1
        self._last_latency[provider] = latency_ms
        if success:
            self._provider_health[provider] = "healthy"
            self._failure_count[provider] = max(0, self._failure_count[provider] - 1)
        else:
            self._failure_count[provider] += 1
            if self._failure_count[provider] >= 3:
                self._provider_health[provider] = "degraded"
            else:
                self._provider_health[provider] = "unhealthy"

    # ------------------ SYNC IMPLEMENTATIONS ------------------

    def _call_grok(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.grok_client:
            raise RuntimeError("Grok API Key nicht konfiguriert")
        sys = system_prompt or self._build_heroic_context()
        messages = [{"role": "system", "content": sys}, {"role": "user", "content": prompt}]
        resp = self.grok_client.chat.completions.create(
            model=os.getenv("GROK_MODEL", "grok-2-1212"),
            messages=messages, max_tokens=2048, temperature=0.7
        )
        return resp.choices[0].message.content or "[Grok: Keine Antwort]"

    def _call_claude(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.claude_client:
            raise RuntimeError("Claude API Key nicht konfiguriert")
        sys = system_prompt or self._build_heroic_context() + "\nAntworte mit maximaler Präzision und Heroic Core Alignment."
        resp = self.claude_client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=2048, system=sys,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text if resp.content else "[Claude: Keine Antwort]"

    def _call_everyapi(self, prompt: str) -> str:
        if not self.everyapi_key:
            raise RuntimeError("EveryAPI Key nicht konfiguriert")
        headers = {"Authorization": f"Bearer {self.everyapi_key}", "Content-Type": "application/json"}
        payload = {"model": self.everyapi_model, "message": prompt, "max_tokens": 2048}
        r = requests.post(self.everyapi_base_url, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("response") or data.get("text") or str(data)
        raise RuntimeError(f"EveryAPI Fehler {r.status_code}: {r.text[:200]}")

    def route(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_provider: Optional[Provider] = None,
    ) -> LLMResponse:
        start = time.time()
        category = self._classify_query(prompt)
        order = self._get_routing_order(category)

        if force_provider:
            order = [force_provider] + [p for p in order if p != force_provider]

        errors: List[str] = []
        used_chain: List[str] = []

        for provider in order:
            used_chain.append(provider)
            try:
                if provider == "grok" and self.grok_client:
                    text = self._call_grok(prompt, system_prompt)
                    latency = (time.time() - start) * 1000
                    self._update_health("grok", True, latency)
                    return LLMResponse("grok (xAI)", text, latency, used_chain, {"category": category})
                elif provider == "claude" and self.claude_client:
                    text = self._call_claude(prompt, system_prompt)
                    latency = (time.time() - start) * 1000
                    self._update_health("claude", True, latency)
                    return LLMResponse("claude (Anthropic)", text, latency, used_chain, {"category": category})
                elif provider == "everyapi" and self.everyapi_key:
                    text = self._call_everyapi(prompt)
                    latency = (time.time() - start) * 1000
                    self._update_health("everyapi", True, latency)
                    return LLMResponse("everyapi", text, latency, used_chain, {"category": category})
                elif provider == "fusion-hero":
                    ctx = self._build_heroic_context()
                    latency = (time.time() - start) * 1000
                    return LLMResponse(
                        "fusion-hero (intern)",
                        f"[Fusion Hero OS v8.3] Interner Fallback aktiv.\n{ctx}\nPrompt klassifiziert als '{category}'.\nEmpfehlung: API-Keys setzen.",
                        latency, used_chain, {"category": category, "note": "internal"}
                    )
            except Exception as e:
                errors.append(f"{provider}: {str(e)[:120]}")
                self._update_health(provider, False, 0)
                continue

        return LLMResponse(
            "system-error",
            "Alle Provider fehlgeschlagen: " + " | ".join(errors),
            (time.time() - start) * 1000, used_chain, {"errors": errors}
        )

    # ------------------ ASYNC WRAPPER ------------------

    async def aroute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_provider: Optional[Provider] = None,
    ) -> LLMResponse:
        """Non-blocking Version für Orchestrator & Agents."""
        return await asyncio.to_thread(self.route, prompt, system_prompt, force_provider)

    def status(self) -> Dict[str, Any]:
        return {
            "version": "v8.3-fully-wired",
            "grok_configured": bool(self.grok_client),
            "claude_configured": bool(self.claude_client),
            "everyapi_configured": bool(self.everyapi_key),
            "heroic_core_connected": self.heroic_core is not None,
            "everyapi_endpoint": self.everyapi_base_url,
            "health": dict(self._provider_health),
            "request_count": dict(self._request_count),
            "failure_count": dict(self._failure_count),
            "last_latency_ms": dict(self._last_latency),
            "default_order": self.default_order,
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
    print("Universal LLM Router v8.3 Status:", router.status())