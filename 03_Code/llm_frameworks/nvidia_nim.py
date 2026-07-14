# -*- coding: utf-8 -*-
"""NVIDIA NIM LLM Framework — integrate.api.nvidia.com (OpenAI-compatible)."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class NvidiaNimFramework(LLMFramework):
    provider_id = "nvidia"
    display_name = "NVIDIA NIM"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("NVIDIA_API_KEY", "NGC_API_KEY", "NVAPI_KEY")

    def base_url(self):
        return os.getenv(
            "FUSION_NVIDIA_BASE",
            "https://integrate.api.nvidia.com/v1",
        )

    def default_model(self):
        return os.getenv(
            "FUSION_NVIDIA_MODEL",
            "meta/llama-3.1-8b-instruct",
        )

    def aliases(self):
        return ("nvidia", "nvidia-nim", "nim", "nvidia_nim")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError(
                "NVIDIA_API_KEY (oder NGC_API_KEY / NVAPI_KEY) nicht gesetzt"
            )
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="nvidia",
        )


framework = NvidiaNimFramework()