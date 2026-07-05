"""Tests für GROK_EXPORT_REQUEST-Scaffolds (Timespace, LLM-EA, Image)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "03_Code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from timespace_token_management import (  # noqa: E402
    TimespaceCoordinate,
    TimespaceTokenManager,
    TimespaceTrack,
)
from TokenManagementSystem import ResourceState  # noqa: E402

from fusion_hero_os.modules.heroic_llm_ea import HeroicLLMEAOrchestrator
from fusion_hero_os.modules.image_orchestrator import HeroicImageOrchestrator
from fusion_hero_os.modules.image_orchestrator.rate_limiter import TokenBucketRateLimiter


def test_timespace_allocation():
    manager = TimespaceTokenManager(base_tokens=1000)
    tracks = [
        TimespaceTrack(
            "near",
            TimespaceCoordinate(0.0, 0.0),
            ResourceState(0.9, 0.1, 1, 0.1, 0.1),
        ),
        TimespaceTrack(
            "far",
            TimespaceCoordinate(6.0, 4.0),
            ResourceState(0.7, 0.3, 2, 0.2, 0.2),
        ),
    ]
    alloc = manager.allocate(tracks)
    assert alloc["near"] >= alloc["far"]


def test_heroic_llm_ea_stub():
    orch = HeroicLLMEAOrchestrator()
    result = orch.process({"prompt": "campfire", "n_proposals": 2})
    assert "best" in result
    assert result["status"] == "stub_llm"
    assert result["best"]["fitness"] > 0


def test_image_orchestrator_dry_run():
    orch = HeroicImageOrchestrator()
    job = orch.process({"prompt": "cyberpunk campfire"})
    assert job["mode"] == "dry_run"
    assert "job_id" in job


def test_rate_limiter_blocks():
    limiter = TokenBucketRateLimiter()
    limiter.config.max_requests = 1
    assert limiter.allow()[0] is True
    assert limiter.allow()[0] is False