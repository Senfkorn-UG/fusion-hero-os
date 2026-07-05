"""HeroicImageOrchestrator — Visual Identity + Rate-Limit + Dry-Run-Jobs."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from fusion_hero_os.core.base_module import BaseModule, ReviewCriterion, ReviewResult
from fusion_hero_os.modules.image_orchestrator.rate_limiter import (
    RateLimitConfig,
    TokenBucketRateLimiter,
)


_CONFIG_PATH = Path(__file__).parent / "config" / "visual_identity.yaml"


class HeroicImageOrchestrator(BaseModule):
    """Bild-Pipeline-Orchestrator — Dry-Run by default (Code-Honesty)."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        super().__init__()
        self.config_path = config_path or _CONFIG_PATH
        self._config = self._load_config()
        rl = self._config.get("rate_limits", {}).get("default", {})
        self.rate_limiter = TokenBucketRateLimiter(
            RateLimitConfig(
                max_requests=int(rl.get("max_requests", 10)),
                window_seconds=float(rl.get("window_seconds", 60.0)),
            )
        )
        self._jobs: List[Dict[str, Any]] = []

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"identity": {}, "rate_limits": {}, "pipeline": {"mode": "dry_run"}}
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        prompt = str(payload.get("prompt", ""))
        allowed, wait = self.rate_limiter.allow()
        job_id = str(uuid.uuid4())[:8]
        identity = self._config.get("identity", {})
        job = {
            "job_id": job_id,
            "prompt": prompt,
            "allowed": allowed,
            "wait_seconds": wait,
            "would_execute": allowed and bool(prompt),
            "mode": self._config.get("pipeline", {}).get("mode", "dry_run"),
            "style_tags": identity.get("style_tags", []),
            "primary_seed": identity.get("primary_seed"),
        }
        self._jobs.append(job)
        if len(self._jobs) > 100:
            self._jobs.pop(0)
        return job

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        criteria = [
            ReviewCriterion("Visual Identity als Daten (YAML)", self.config_path.exists()),
            ReviewCriterion("Rate-Limiter separat", True, "rate_limiter.py"),
            ReviewCriterion("Dry-Run default", self._config.get("pipeline", {}).get("mode") == "dry_run"),
            ReviewCriterion("Echte Bild-API", False, "Nicht implementiert — explizites Opt-in nötig"),
        ]
        return ReviewResult(module=self.name, criteria=criteria)