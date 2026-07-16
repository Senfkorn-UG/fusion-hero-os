# -*- coding: utf-8 -*-
"""GitHub Models free tier (OpenAI-compatible inference endpoint)."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class GitHubModelsFramework(LLMFramework):
    provider_id = "github_models"
    display_name = "GitHub Models (Free)"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("GITHUB_TOKEN", "GH_TOKEN")

    def base_url(self):
        return os.getenv(
            "FUSION_GITHUB_MODELS_BASE",
            "https://models.inference.ai.azure.com",
        )

    def default_model(self):
        return os.getenv("FUSION_GITHUB_MODELS_MODEL", "gpt-4o-mini")

    def aliases(self):
        return ("github_models", "github-models", "gh-models")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("GITHUB_TOKEN nicht gesetzt")
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="github_models",
            extra_headers={"api-key": api_key},
        )


framework = GitHubModelsFramework()
