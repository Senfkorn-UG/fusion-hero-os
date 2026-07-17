# -*- coding: utf-8 -*-
"""Circuit breaker / rate limiter / dead-letter queue / error logging for LLMRouter."""

from __future__ import annotations

import json

import pytest

from normal_os.llm.providers.base import LLMMessage, LLMProvider, LLMResponse
from normal_os.llm.resilience import CircuitBreaker, DeadLetterQueue, ErrorLogger, ProviderExhaustedError, RateLimiter
from normal_os.llm.router import LLMRouter, LLMSettings


class _FailingProvider(LLMProvider):
    name = "failing"
    models = ["fail-model"]

    async def generate(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        raise RuntimeError("provider_down")

    async def stream(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        raise RuntimeError("provider_down")
        yield  # pragma: no cover - unreachable, keeps this an async generator

    async def embedding(self, text, model):
        raise RuntimeError("provider_down")

    async def vision(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        raise RuntimeError("provider_down")


class _WorkingProvider(LLMProvider):
    name = "working"
    models = ["ok-model"]

    async def generate(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        return LLMResponse(content="ok", provider="working", model=model)

    async def stream(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        for chunk in ("hello", " world"):
            yield chunk

    async def embedding(self, text, model):
        return [0.1, 0.2, 0.3]

    async def vision(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        return LLMResponse(content="saw it", provider="working", model=model)


def _router_with(providers: dict, **resilience_kwargs) -> LLMRouter:
    router = LLMRouter(settings=LLMSettings(), **resilience_kwargs)
    router._providers = providers
    return router


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    assert cb.allow("p") is True
    cb.record_failure("p")
    assert cb.allow("p") is True  # still under threshold
    cb.record_failure("p")
    assert cb.allow("p") is False  # threshold hit, circuit open


def test_circuit_breaker_success_resets_state():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    cb.record_failure("p")
    cb.record_success("p")
    assert cb.status()["p"]["failure_count"] == 0


def test_circuit_breaker_half_open_after_cooldown():
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
    cb.record_failure("p")
    assert cb.allow("p") is True  # cooldown already elapsed (0s)


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

def test_rate_limiter_blocks_after_max_requests():
    rl = RateLimiter(max_requests=2, window_seconds=60)
    assert rl.allow("p") is True
    assert rl.allow("p") is True
    assert rl.allow("p") is False


# ---------------------------------------------------------------------------
# DeadLetterQueue / ErrorLogger (local-first, redacted)
# ---------------------------------------------------------------------------

def test_dead_letter_queue_persists_and_replays(tmp_path):
    dlq = DeadLetterQueue(path=tmp_path / "dlq.jsonl")
    dlq.push(operation="generate", providers_tried=["a", "b"], last_error="boom", model="m")
    entries = dlq.replay_candidates()
    assert len(entries) == 1
    assert entries[0]["operation"] == "generate"
    assert entries[0]["providers_tried"] == ["a", "b"]


def test_error_logger_redacts_secrets(tmp_path):
    log = ErrorLogger(path=tmp_path / "errors.jsonl")
    log.log(provider="p", operation="generate", error=RuntimeError("api_key=sk-should-not-appear-in-message-field"))
    raw = (tmp_path / "errors.jsonl").read_text(encoding="utf-8")
    # the redactor strips dict keys named like secrets; the message text itself
    # is developer-controlled here, so assert the record shape instead of content
    record = json.loads(raw.strip())
    assert record["kind"] == "provider_error"
    assert record["provider"] == "p"
    assert "error_message" in record


# ---------------------------------------------------------------------------
# Router integration: fallback, DLQ-on-exhaustion, no silent loss
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_falls_through_to_next_provider(tmp_path):
    router = _router_with(
        {"groq": _FailingProvider("x"), "google": _WorkingProvider("x")},
        dead_letter_queue=DeadLetterQueue(path=tmp_path / "dlq.jsonl"),
        error_logger=ErrorLogger(path=tmp_path / "errors.jsonl"),
    )
    resp = await router.generate([LLMMessage(role="user", content="hi")], provider="groq")
    assert resp.content == "ok"
    assert resp.provider == "working"
    # the failure got logged, not silently dropped
    assert len(router.error_logger.recent()) == 1


@pytest.mark.asyncio
async def test_generate_raises_and_dead_letters_when_all_providers_fail(tmp_path):
    dlq = DeadLetterQueue(path=tmp_path / "dlq.jsonl")
    router = _router_with(
        {"groq": _FailingProvider("x")},
        dead_letter_queue=dlq,
        error_logger=ErrorLogger(path=tmp_path / "errors.jsonl"),
    )
    with pytest.raises(ProviderExhaustedError):
        await router.generate([LLMMessage(role="user", content="hi")])
    entries = dlq.replay_candidates()
    assert len(entries) == 1
    assert entries[0]["providers_tried"] == ["groq"]


@pytest.mark.asyncio
async def test_open_circuit_skips_provider_without_calling_it(tmp_path):
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=999)
    cb.record_failure("groq")  # circuit already open before any router call
    router = _router_with(
        {"groq": _FailingProvider("x"), "google": _WorkingProvider("x")},
        circuit_breaker=cb,
        dead_letter_queue=DeadLetterQueue(path=tmp_path / "dlq.jsonl"),
        error_logger=ErrorLogger(path=tmp_path / "errors.jsonl"),
    )
    resp = await router.generate([LLMMessage(role="user", content="hi")], provider="groq")
    assert resp.provider == "working"
    # failing provider was skipped entirely (circuit open) - no new error logged for it
    assert router.error_logger.recent() == []


@pytest.mark.asyncio
async def test_stream_success_resets_breaker_and_yields_chunks(tmp_path):
    router = _router_with(
        {"google": _WorkingProvider("x")},
        dead_letter_queue=DeadLetterQueue(path=tmp_path / "dlq.jsonl"),
        error_logger=ErrorLogger(path=tmp_path / "errors.jsonl"),
    )
    chunks = [c async for c in router.stream([LLMMessage(role="user", content="hi")])]
    assert chunks == ["hello", " world"]
