"""OpenRouter Provider - Access 100+ models including free ones"""
import httpx
from typing import AsyncIterator, List, Optional
from .base import LLMProvider, LLMMessage, LLMResponse


class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    # Popular free models on OpenRouter
    models = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "meta-llama/llama-3.1-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "mistralai/mistral-nemo:free",
        "google/gemma-2-9b-it:free",
        "qwen/qwen-2.5-7b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "deepseek/deepseek-chat:free",
        "deepseek/deepseek-r1:free",
        "microsoft/phi-3.5-mini-instruct:free",
        "z-ai/glm-4.5-air:free",
        "nousresearch/hermes-3-llama-3.1-8b:free",
        "gryphe/mythomax-l2-13b:free",
        "undi95/toppy-m-7b:free",
        "cognitivecomputations/dolphin-2.9-llama-3-8b:free",
    ]
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": kwargs.get("referer", "https://fusion-hero.local"),
                "X-Title": kwargs.get("title", "Fusion Hero OS"),
            },
            timeout=120.0,
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        model: str = "meta-llama/llama-3.1-8b-instruct:free",
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
        model: str = "meta-llama/llama-3.1-8b-instruct:free",
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

    async def embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        response = await self.client.post(
            "/embeddings",
            json={"model": model, "input": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def vision(
        self,
        messages: List[LLMMessage],
        model: str = "qwen/qwen-2.5-vl-7b-instruct:free",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        return await self.generate(messages, model, temperature, max_tokens, **kwargs)
