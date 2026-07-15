# -*- coding: utf-8 -*-
"""Cloudflare Workers AI free tier (OpenAI-compatible when account set)."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat, resolve_api_key


class CloudflareAIFramework(LLMFramework):
    provider_id = "cloudflare_ai"
    display_name = "Cloudflare Workers AI"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("CLOUDFLARE_API_TOKEN", "CF_API_TOKEN")

    def account_id(self) -> str:
        return (
            os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
            or os.getenv("CF_ACCOUNT_ID", "").strip()
        )

    def base_url(self):
        acc = self.account_id()
        if not acc:
            return "https://api.cloudflare.com/client/v4/accounts/MISSING/ai/v1"
        return (
            f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/v1"
        )

    def default_model(self):
        return os.getenv(
            "FUSION_CF_AI_MODEL",
            "@cf/meta/llama-3.1-8b-instruct",
        )

    def aliases(self):
        return ("cloudflare_ai", "cloudflare", "workers-ai", "cf-ai")

    def configured(self) -> bool:
        return bool(self.get_api_key() and self.account_id())

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key or not self.account_id():
            raise RuntimeError(
                "CLOUDFLARE_API_TOKEN und CLOUDFLARE_ACCOUNT_ID erforderlich"
            )
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="cloudflare_ai",
        )


framework = CloudflareAIFramework()
