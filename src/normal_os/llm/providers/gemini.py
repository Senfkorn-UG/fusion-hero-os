"""Google AI Studio (Gemini) Provider"""
import httpx
from typing import AsyncIterator, List, Optional
from .base import LLMProvider, LLMMessage, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"
    models = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-1.5-flash-8b",
    ]
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": api_key},
            timeout=120.0,
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        contents = self._messages_to_contents(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 8192,
            },
        }
        response = await self.client.post(f"/models/{model}:generateContent", json=payload)
        response.raise_for_status()
        data = response.json()
        candidate = data["candidates"][0]
        content = candidate["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            usage={
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            },
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        contents = self._messages_to_contents(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 8192,
            },
        }
        async with self.client.stream("POST", f"/models/{model}:streamGenerateContent", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    import json
                    chunk = json.loads(line)
                    if "candidates" in chunk and chunk["candidates"]:
                        parts = chunk["candidates"][0]["content"]["parts"]
                        for part in parts:
                            if "text" in part:
                                yield part["text"]

    async def embedding(self, text: str, model: str = "text-embedding-004") -> List[float]:
        response = await self.client.post(
            f"/models/{model}:embedContent",
            json={"content": {"parts": [{"text": text}]}},
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]["values"]

    async def vision(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        return await self.generate(messages, model, temperature, max_tokens, **kwargs)

    def _messages_to_contents(self, messages: List[LLMMessage]) -> List[dict]:
        contents = []
        for msg in messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}],
            })
        return contents
