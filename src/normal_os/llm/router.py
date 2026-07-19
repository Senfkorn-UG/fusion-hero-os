"""LLMRouter - Multi-provider LLM router with free tier support

Supports: Google AI Studio (Gemini), OpenRouter, Groq, Cerebras, Mistral,
Hugging Face Inference, Github Models, and more.

Resilience (circuit breaker + rate limiter + dead-letter queue + error
logging) lives in-house in ``resilience.py`` — provider outages/rate
limits get handled by falling through the priority list instead of
needing a human to notice a red check on GitHub and intervene.
"""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional

from pydantic_settings import BaseSettings

from .providers import (
    CerebrasProvider,
    GitHubModelsProvider,
    GoogleProvider,
    GroqProvider,
    HuggingFaceProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    MistralProvider,
    OpenRouterProvider,
)
from .resilience import CircuitBreaker, DeadLetterQueue, ErrorLogger, ProviderExhaustedError, RateLimiter

# Bevorzugte Reihenfolge: schnelle/kostenlose Provider zuerst.
_PROVIDER_PRIORITY = ("groq", "cerebras", "openrouter", "github", "google", "mistral", "huggingface")

_PROVIDER_CLASSES: Dict[str, type] = {
    "google": GoogleProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "huggingface": HuggingFaceProvider,
    "github": GitHubModelsProvider,
    "cerebras": CerebrasProvider,
}


class LLMSettings(BaseSettings):
    """API-Keys je Provider aus Env-Variablen (leer = Provider nicht verfuegbar)."""

    google_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""
    huggingface_api_key: str = ""
    github_api_key: str = ""
    cerebras_api_key: str = ""


class LLMRouter:
    """Waehlt automatisch einen verfuegbaren Provider (per konfiguriertem API-Key).

    Faellt bei Rate-Limits, offenem Circuit-Breaker oder Fehlern auf den
    naechsten Provider in ``_PROVIDER_PRIORITY`` zurueck. Schlagen alle
    Kandidaten fehl, landet der Request in der Dead-Letter-Queue statt
    stillschweigend verloren zu gehen.
    """

    def __init__(self, settings: Optional[LLMSettings] = None,
                 circuit_breaker: Optional[CircuitBreaker] = None,
                 rate_limiter: Optional[RateLimiter] = None,
                 dead_letter_queue: Optional[DeadLetterQueue] = None,
                 error_logger: Optional[ErrorLogger] = None):
        self.settings = settings or LLMSettings()
        self._providers: Dict[str, LLMProvider] = {}
        keys = {
            "google": self.settings.google_api_key,
            "openrouter": self.settings.openrouter_api_key,
            "groq": self.settings.groq_api_key,
            "mistral": self.settings.mistral_api_key,
            "huggingface": self.settings.huggingface_api_key,
            "github": self.settings.github_api_key,
            "cerebras": self.settings.cerebras_api_key,
        }
        for name, api_key in keys.items():
            if api_key:
                self._providers[name] = _PROVIDER_CLASSES[name](api_key)

        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.dead_letter_queue = dead_letter_queue or DeadLetterQueue()
        self.error_logger = error_logger or ErrorLogger()

    @property
    def available_providers(self) -> List[str]:
        return [name for name in _PROVIDER_PRIORITY if name in self._providers]

    def _candidates(self, prefer: Optional[str] = None) -> List[str]:
        """Ordered list of provider names to try for one request."""
        if prefer:
            if prefer not in self._providers:
                raise ValueError(f"Provider '{prefer}' nicht verfuegbar (kein API-Key konfiguriert).")
            rest = [n for n in self.available_providers if n != prefer]
            return [prefer, *rest]
        if not self._providers:
            raise RuntimeError(
                "Kein LLM-Provider verfuegbar - keine API-Keys konfiguriert "
                f"(erwartet Env-Variablen wie {', '.join(n.upper() + '_API_KEY' for n in _PROVIDER_PRIORITY)})."
            )
        return list(self.available_providers)

    async def _with_resilience(self, operation: str, candidates: List[str], model: Optional[str],
                                call):
        """Try ``call(provider_obj, resolved_model)`` across candidates in order."""
        tried: List[str] = []
        last_error: Optional[BaseException] = None
        for name in candidates:
            if not self.circuit_breaker.allow(name):
                continue
            if not self.rate_limiter.allow(name):
                continue
            provider = self._providers[name]
            resolved_model = model or provider.models[0]
            tried.append(name)
            try:
                result = await call(provider, resolved_model)
            except Exception as exc:  # noqa: BLE001 - provider SDKs raise many types
                self.circuit_breaker.record_failure(name)
                self.error_logger.log(provider=name, operation=operation, error=exc, model=resolved_model)
                last_error = exc
                continue
            else:
                self.circuit_breaker.record_success(name)
                return result

        self.dead_letter_queue.push(
            operation=operation,
            providers_tried=tried,
            last_error=str(last_error) if last_error else "no candidate available (rate-limited or circuit-open)",
            model=model,
        )
        raise ProviderExhaustedError(
            f"{operation}: alle Kandidaten erschoepft (versucht: {tried or 'keine - alle rate-limited/circuit-open'})."
        ) from last_error

    async def generate(self, messages: List[LLMMessage], model: Optional[str] = None,
                        provider: Optional[str] = None, temperature: float = 0.7,
                        max_tokens: Optional[int] = None, **kwargs) -> LLMResponse:
        candidates = self._candidates(prefer=provider)

        async def call(p: LLMProvider, resolved_model: str) -> LLMResponse:
            return await p.generate(messages, model=resolved_model, temperature=temperature,
                                     max_tokens=max_tokens, **kwargs)

        return await self._with_resilience("generate", candidates, model, call)

    async def stream(self, messages: List[LLMMessage], model: Optional[str] = None,
                      provider: Optional[str] = None, temperature: float = 0.7,
                      max_tokens: Optional[int] = None, **kwargs) -> AsyncIterator[str]:
        # Streaming can't transparently fall through mid-stream once chunks have
        # already been yielded to the caller, so resilience applies to *picking*
        # the provider (breaker/rate-limit aware), not to recovering mid-stream.
        candidates = self._candidates(prefer=provider)
        name = next((n for n in candidates if self.circuit_breaker.allow(n) and self.rate_limiter.allow(n)), None)
        if name is None:
            self.dead_letter_queue.push(
                operation="stream", providers_tried=[], model=model,
                last_error="no candidate available (rate-limited or circuit-open)",
            )
            raise ProviderExhaustedError("stream: kein Kandidat verfuegbar (rate-limited/circuit-open).")
        p = self._providers[name]
        resolved_model = model or p.models[0]
        try:
            async for chunk in p.stream(messages, model=resolved_model, temperature=temperature,
                                         max_tokens=max_tokens, **kwargs):
                yield chunk
        except Exception as exc:
            self.circuit_breaker.record_failure(name)
            self.error_logger.log(provider=name, operation="stream", error=exc, model=resolved_model)
            self.dead_letter_queue.push(
                operation="stream", providers_tried=[name], last_error=str(exc), model=model,
            )
            raise
        else:
            self.circuit_breaker.record_success(name)

    async def embedding(self, text: str, model: Optional[str] = None,
                         provider: Optional[str] = None) -> List[float]:
        candidates = self._candidates(prefer=provider)

        async def call(p: LLMProvider, resolved_model: str) -> List[float]:
            return await p.embedding(text, model=resolved_model)

        return await self._with_resilience("embedding", candidates, model, call)

    async def vision(self, messages: List[LLMMessage], model: Optional[str] = None,
                      provider: Optional[str] = None, temperature: float = 0.7,
                      max_tokens: Optional[int] = None, **kwargs) -> LLMResponse:
        candidates = self._candidates(prefer=provider)

        async def call(p: LLMProvider, resolved_model: str) -> LLMResponse:
            return await p.vision(messages, model=resolved_model, temperature=temperature,
                                   max_tokens=max_tokens, **kwargs)

        return await self._with_resilience("vision", candidates, model, call)
