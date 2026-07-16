# -*- coding: utf-8 -*-
"""Hugging Face Inference (OpenAI-compatible router) — free tier limited."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class HuggingFaceFramework(LLMFramework):
    provider_id = "huggingface"
    display_name = "Hugging Face (Free Inference)"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("HF_TOKEN", "HUGGINGFACE_API_KEY", "HUGGING_FACE_HUB_TOKEN")

    def base_url(self):
        return os.getenv(
            "FUSION_HF_BASE",
            "https://router.huggingface.co/v1",
        )

    def default_model(self):
        return os.getenv(
            "FUSION_HF_MODEL",
            "meta-llama/Meta-Llama-3-8B-Instruct",
        )

    def aliases(self):
        return ("huggingface", "hf", "hugging-face")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("HF_TOKEN / HUGGINGFACE_API_KEY nicht gesetzt")
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="huggingface",
        )


framework = HuggingFaceFramework()
