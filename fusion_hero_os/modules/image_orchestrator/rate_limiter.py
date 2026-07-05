"""Separat testbarer Rate-Limiter für Bildgenerierungs-Jobs."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Tuple


@dataclass
class RateLimitConfig:
    max_requests: int = 10
    window_seconds: float = 60.0


class TokenBucketRateLimiter:
    """Sliding-window Rate-Limiter — rein lokal, kein Netzwerk."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self.config = config or RateLimitConfig()
        self._timestamps: Deque[float] = deque()

    def _prune(self, now: float) -> None:
        cutoff = now - self.config.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def allow(self, now: float | None = None) -> Tuple[bool, float]:
        now = now if now is not None else time.time()
        self._prune(now)
        if len(self._timestamps) < self.config.max_requests:
            self._timestamps.append(now)
            return True, 0.0
        wait = self.config.window_seconds - (now - self._timestamps[0])
        return False, max(0.0, wait)

    def status(self) -> dict:
        now = time.time()
        self._prune(now)
        return {
            "used": len(self._timestamps),
            "max": self.config.max_requests,
            "window_seconds": self.config.window_seconds,
        }