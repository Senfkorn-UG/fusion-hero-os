"""Mistral AI Provider - Mistral models including free tier"""
import httpx
from typing import AsyncIterator, List, Optional
from .base import LLMProvider, LLMMessage, LLMResponse


class MistralProvider(LLMProvider):
    name = "mistral"
    models = [
        "mistral-small-latest",
        "mistral-large-latest",
        "mistral-nemo",
        "codestral-latest",
        "ministral-3b-latest",
        "ministral-8b-latest",
    ]
    base_url = "https://api.mistral.ai/v1"

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        model: str = "mistral-small-latest",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            provider=self.name,
            model=data.get("model", model),
            usage=data.get("usage", {}),
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        model: str = "mistral-small-latest",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    if chunk["choices"][0]["delta"].get("content"):
                        yield chunk["choices"][0]["delta"]["content"]

    async def embedding(self, text: str, model: str = "mistral-embed") -> List[float]:
        response = await self.client.post(
            "/embeddings",
            json={"model": model, "input": [text]},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def vision(
        self,
        messages: List[LLMMessage],
        model: str = "pixtral-12b-2409",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        raise NotImplementedError("Mistral vision not yet supported")
