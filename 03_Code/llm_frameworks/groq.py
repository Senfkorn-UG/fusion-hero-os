# -*- coding: utf-8 -*-
"""Groq free-tier LLM Framework (OpenAI-compatible)."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class GroqFramework(LLMFramework):
    provider_id = "groq"
    display_name = "Groq (Free Tier)"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("GROQ_API_KEY",)

    def base_url(self):
        return os.getenv("FUSION_GROQ_BASE", "https://api.groq.com/openai/v1")

    def default_model(self):
        return os.getenv("FUSION_GROQ_MODEL", "llama-3.3-70b-versatile")

    def aliases(self):
        return ("groq", "groq-cloud")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("GROQ_API_KEY nicht gesetzt")
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="groq",
        )


framework = GroqFramework()
