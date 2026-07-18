"""In-house resilience layer for LLM provider calls.

Circuit breaker + rate limiter + dead-letter queue + structured error
logging, all local-first (state lives under ``~/.fusion/llm_resilience/``,
matching the existing ``~/.fusion/operator/`` convention). Provider
outages and rate limits get handled by the router itself instead of
needing a human to notice a red check on GitHub and intervene.
"""
from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Deque, Dict, List, Optional

_STATE_DIR = Path.home() / ".fusion" / "llm_resilience"
_DLQ_PATH = _STATE_DIR / "dead_letter.jsonl"
_ERROR_LOG_PATH = _STATE_DIR / "errors.jsonl"

# Never let a secret reach disk, regardless of where it shows up in a record.
_REDACT_KEYS = {"api_key", "apikey", "authorization", "key", "token", "secret"}


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: ("***" if k.lower() in _REDACT_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_redact(record), ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


@dataclass
class _BreakerState:
    failure_count: int = 0
    opened_at: Optional[float] = None


class CircuitBreaker:
    """Per-provider closed -> open -> half-open -> closed state machine.

    Stops hammering a provider that's clearly down so the router can fall
    through to the next one instead of failing the whole request.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._states: Dict[str, _BreakerState] = {}
        self._lock = Lock()

    def _state(self, provider: str) -> _BreakerState:
        return self._states.setdefault(provider, _BreakerState())

    def allow(self, provider: str) -> bool:
        with self._lock:
            st = self._state(provider)
            if st.opened_at is None:
                return True
            if time.monotonic() - st.opened_at >= self.cooldown_seconds:
                return True  # half-open: let one probe through
            return False

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._states[provider] = _BreakerState()

    def record_failure(self, provider: str) -> None:
        with self._lock:
            st = self._state(provider)
            st.failure_count += 1
            if st.failure_count >= self.failure_threshold:
                st.opened_at = time.monotonic()

    def status(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            now = time.monotonic()
            return {
                name: {
                    "failure_count": st.failure_count,
                    "open": st.opened_at is not None and (now - st.opened_at) < self.cooldown_seconds,
                }
                for name, st in self._states.items()
            }


class RateLimiter:
    """Per-provider sliding-window request-rate limiter."""

    def __init__(self, max_requests: int = 20, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def allow(self, provider: str) -> bool:
        with self._lock:
            now = time.monotonic()
            window = self._windows.setdefault(provider, deque())
            while window and now - window[0] > self.window_seconds:
                window.popleft()
            if len(window) >= self.max_requests:
                return False
            window.append(now)
            return True


class DeadLetterQueue:
    """Persists requests that failed on every available provider."""

    def __init__(self, path: Path = _DLQ_PATH):
        self.path = path

    def push(self, *, operation: str, providers_tried: List[str], last_error: str,
              model: Optional[str] = None, preview: str = "") -> None:
        _append_jsonl(self.path, {
            "ts": time.time(),
            "kind": "dead_letter",
            "operation": operation,
            "model": model,
            "providers_tried": providers_tried,
            "last_error": last_error[:1000],
            "preview": preview[:500],
        })

    def replay_candidates(self) -> List[Dict[str, Any]]:
        return _read_jsonl(self.path)


class ErrorLogger:
    """Structured, secret-redacted error logging — local-first, no GitHub dependency."""

    def __init__(self, path: Path = _ERROR_LOG_PATH):
        self.path = path

    def log(self, *, provider: str, operation: str, error: BaseException,
             model: Optional[str] = None) -> None:
        _append_jsonl(self.path, {
            "ts": time.time(),
            "kind": "provider_error",
            "provider": provider,
            "operation": operation,
            "model": model,
            "error_type": type(error).__name__,
            "error_message": str(error)[:1000],
        })

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return _read_jsonl(self.path)[-limit:]


class ProviderExhaustedError(RuntimeError):
    """Raised when every candidate provider failed for one request."""
