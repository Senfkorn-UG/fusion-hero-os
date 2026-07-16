# -*- coding: utf-8 -*-
"""OpenRouter free-model pool — pseudo-inhouse free gateway slice."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class OpenRouterFreeFramework(LLMFramework):
    provider_id = "openrouter_free"
    display_name = "OpenRouter Free Models"
    api_kind = "openai"

    FREE_DEFAULTS = (
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "qwen/qwen-2.5-7b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
    )

    def api_key_env_vars(self):
        return ("OPENROUTER_API_KEY",)

    def base_url(self):
        return os.getenv("FUSION_OPENROUTER_BASE", "https://openrouter.ai/api/v1")

    def default_model(self):
        return os.getenv("FUSION_OPENROUTER_FREE_MODEL", self.FREE_DEFAULTS[0])

    def aliases(self):
        return ("openrouter_free", "or-free", "free-router")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY nicht gesetzt")
        extra = {
            "HTTP-Referer": os.getenv(
                "FUSION_OPENROUTER_REF", "https://fusion-hero-os.local"
            ),
            "X-Title": "Fusion Hero OS v10 Pseudo-Inhouse Free",
        }
        # Prefer :free model id
        model = self.model
        if ":free" not in model and os.getenv("FUSION_FORCE_FREE_MODELS", "1") == "1":
            model = self.default_model()
        return openai_chat(
            self.base_url(),
            api_key,
            model,
            messages,
            timeout,
            provider="openrouter_free",
            extra_headers=extra,
        )


framework = OpenRouterFreeFramework()
