# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8 — Universal LLM Router (Grok + Claude + EveryAPI)
Native Integration mit intelligentem Routing, Fallback-Chain und Heroic Core Alignment.

Layer 0 verankert: ALTE_Frau_95g Heroic Core v8 + HorkruxSelfUpdateProtocol
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI  # xAI Grok ist OpenAI-kompatibel
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


Provider = Literal["grok", "claude", "everyapi", "fusion-hero", "llama-local"]


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
    Heroischer Multi-LLM Router für Fusion Hero OS v8.
    
    - Intelligente Klassifikation des Prompts (Code, Current Events, Simple, Creative, Default)
    - Primär-Routing + automatische Fallback-Chain
    - Native Unterstützung für:
        * Grok (xAI) via OpenAI-kompatible API
        * Claude (Anthropic) via offizielles SDK
        * EveryAPI (generische/universelle API)
    - Vollständig kompatibel mit Heroic Core, QUBO, Hyperthreading und ALTE_Frau_95g Framework
    - Brutale Ehrlichkeit, maximale Präzision, kein Pandering
    """

    def __init__(self) -> None:
        self.grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        self.claude_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.everyapi_key = os.getenv("EVERYAPI_KEY")

        self.grok_client: Optional[OpenAI] = None
        self.claude_client: Optional[Anthropic] = None

        if OpenAI and self.grok_key:
            self.grok_client = OpenAI(
                api_key=self.grok_key,
                base_url="https://api.x.ai/v1"
            )

        if Anthropic and self.claude_key:
            self.claude_client = Anthropic(api_key=self.claude_key)

        # Standard-Routing-Prioritäten (können via ENV überschrieben werden)
        self.default_order: List[Provider] = ["claude", "grok", "everyapi", "fusion-hero"]

        # Query-Klassifikations-Heuristiken (erweiterbar mit QUBO oder kleinem Classifier)
        self.classification_rules = {
            "code": ["code", "programmier", "script", "funktion", "klasse", "debug", "fehler", "implementier", "refactor"],
            "current_events": ["heute", "aktuell", "news", "nachrichten", "was passiert", "grok", "xai", "spaceX", "trump", "wahl"],
            "simple_fact": ["was ist", "wie viel", "wann", "wo", "wer ist", "definition", "übersetz"],
            "creative": ["schreib", "erzähl", "gedicht", "geschichte", "kreativ", "meme", "vision"],
        }

    def _classify_query(self, prompt: str) -> str:
        p = prompt.lower()
        for category, keywords in self.classification_rules.items():
            if any(kw in p for kw in keywords):
                return category
        return "default"

    def _get_routing_order(self, category: str) -> List[Provider]:
        if category == "code":
            return ["claude", "grok", "everyapi", "fusion-hero"]
        elif category == "current_events":
            return ["grok", "claude", "everyapi", "fusion-hero"]
        elif category == "simple_fact":
            return ["everyapi", "grok", "claude", "fusion-hero"]
        elif category == "creative":
            return ["claude", "grok", "everyapi", "fusion-hero"]
        else:
            return self.default_order.copy()

    def _call_grok(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.grok_client:
            raise RuntimeError("Grok API Key nicht konfiguriert (GROK_API_KEY / XAI_API_KEY)")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        resp = self.grok_client.chat.completions.create(
            model=os.getenv("GROK_MODEL", "grok-2-1212"),
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return resp.choices[0].message.content or "[Grok: Keine Antwort]"

    def _call_claude(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.claude_client:
            raise RuntimeError("Claude API Key nicht konfiguriert (ANTHROPIC_API_KEY)")

        resp = self.claude_client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=2048,
            system=system_prompt or "Du bist der native KI-Assistent von Fusion Hero OS v8. Antworte präzise, tiefgründig und im Einklang mit dem Heroic Core.",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text if resp.content else "[Claude: Keine Antwort]"

    def _call_everyapi(self, prompt: str) -> str:
        if not self.everyapi_key:
            raise RuntimeError("EveryAPI Key nicht konfiguriert (EVERYAPI_KEY)")

        # Passe Endpoint & Payload an deine EveryAPI-Dokumentation an
        url = os.getenv("EVERYAPI_URL", "https://api.everyapi.com/v1/chat")
        headers = {
            "Authorization": f"Bearer {self.everyapi_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": os.getenv("EVERYAPI_MODEL", "general"),
            "message": prompt,
            "max_tokens": 2048,
        }

        if not requests:
            raise RuntimeError("requests nicht installiert")

        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("response") or data.get("text") or str(data)
        else:
            raise RuntimeError(f"EveryAPI Fehler {r.status_code}: {r.text[:200]}")

    def route(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_provider: Optional[Provider] = None,
    ) -> LLMResponse:
        """
        Haupt-Routing-Methode.
        Analysiert den Prompt, wählt besten Provider, führt Fallback bei Fehler aus.
        """
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
                    return LLMResponse(
                        provider="grok (xAI)",
                        response=text,
                        latency_ms=(time.time() - start) * 1000,
                        fallback_chain=used_chain,
                        meta={"category": category},
                    )
                elif provider == "claude" and self.claude_client:
                    text = self._call_claude(prompt, system_prompt)
                    return LLMResponse(
                        provider="claude (Anthropic)",
                        response=text,
                        latency_ms=(time.time() - start) * 1000,
                        fallback_chain=used_chain,
                        meta={"category": category},
                    )
                elif provider == "everyapi" and self.everyapi_key:
                    text = self._call_everyapi(prompt)
                    return LLMResponse(
                        provider="everyapi",
                        response=text,
                        latency_ms=(time.time() - start) * 1000,
                        fallback_chain=used_chain,
                        meta={"category": category},
                    )
                elif provider == "fusion-hero":
                    # Fallback auf interne Heroic Logic / lokale Bridge
                    return LLMResponse(
                        provider="fusion-hero (intern)",
                        response=f"[Fusion Hero OS v8 intern] Keine externe API verfügbar. Prompt klassifiziert als '{category}'. "
                               "Empfehlung: API-Keys setzen oder lokalen Llama verwenden.",
                        latency_ms=(time.time() - start) * 1000,
                        fallback_chain=used_chain,
                        meta={"category": category, "note": "internal_fallback"},
                    )
            except Exception as e:
                errors.append(f"{provider}: {str(e)[:150]}")
                continue

        # Alles gescheitert
        return LLMResponse(
            provider="system-error",
            response="Alle LLM-Provider fehlgeschlagen. Details: " + " | ".join(errors),
            latency_ms=(time.time() - start) * 1000,
            fallback_chain=used_chain,
            meta={"errors": errors, "category": category},
        )

    def status(self) -> Dict[str, Any]:
        return {
            "grok_configured": bool(self.grok_client),
            "claude_configured": bool(self.claude_client),
            "everyapi_configured": bool(self.everyapi_key),
            "default_order": self.default_order,
            "classification_rules": list(self.classification_rules.keys()),
            "version": "v8.1-native-router",
            "heroic_core_aligned": True,
        }


# Globale Instanz (Singleton-Style für Core Integration)
_router_instance: Optional[UniversalLLMRouter] = None


def get_universal_llm_router() -> UniversalLLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = UniversalLLMRouter()
    return _router_instance


if __name__ == "__main__":
    router = get_universal_llm_router()
    print("Universal LLM Router Status:", router.status())

    test_prompts = [
        "Schreibe eine Python-Funktion für Fibonacci mit Memoization.",
        "Was sind die neuesten Nachrichten zu xAI und Grok heute?",
        "Was ist der Sinn des Lebens?",
        "Erzähl mir eine kurze Geschichte über einen Coal Canary in Fusion Hero OS.",
    ]

    for p in test_prompts:
        print(f"\n=== Prompt: {p[:60]}... ===")
        result = router.route(p)
        print(f"Provider: {result.provider} | Latency: {result.latency_ms:.0f}ms")
        print(f"Antwort (Ausschnitt): {result.response[:300]}...")