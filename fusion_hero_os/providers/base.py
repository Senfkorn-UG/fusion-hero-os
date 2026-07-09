"""Abstract Base + unified LLMResult for all LLM providers in Fusion Hero OS v8.4.

This is the key hardening that makes the core symmetric:
- Every provider has the same interface (is_available, generate, health).
- Router only orchestrates order + heroic context + classification.
- Easy to add local models or cost-optimized providers later.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResult:
    """Unified, serializable result for every LLM call (Claude, Grok, EveryAPI, internal).

    Replaces the previous inline LLMResponse. Used everywhere in Orchestrator, Dashboard and Agents.
    """
    provider: str
    response: str
    latency_ms: float = 0.0
    fallback_chain: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "response": self.response,
            "latency_ms": self.latency_ms,
            "fallback_chain": self.fallback_chain,
            "meta": self.meta,
            "success": self.success,
            "error": self.error,
        }


class BaseLLMProvider(ABC):
    """Common contract every concrete provider must fulfill."""

    name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._request_count: int = 0
        self._failure_count: int = 0
        self._last_latency: float = 0.0
        self._last_error: Optional[str] = None

    @abstractmethod
    def is_available(self) -> bool:
        """True if this provider can serve requests right now (keys + client ready)."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Perform the actual call. Must always return an LLMResult (never raise to caller)."""
        ...

    def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "available": self.is_available(),
            "request_count": self._request_count,
            "failure_count": self._failure_count,
            "last_latency_ms": self._last_latency,
            "last_error": self._last_error,
        }

    def _record(self, success: bool, latency_ms: float, error: Optional[str] = None) -> None:
        self._request_count += 1
        self._last_latency = latency_ms
        if success:
            self._failure_count = max(0, self._failure_count - 1)
        else:
            self._failure_count += 1
            self._last_error = error[:200] if error else None
