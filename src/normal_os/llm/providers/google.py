"""Google AI Studio (Gemini) Provider"""
import google.generativeai as genai
from typing import AsyncIterator, List, Optional
from .base import LLMProvider, LLMMessage, LLMResponse


class GoogleProvider(LLMProvider):
    name = "google"
    models = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        genai.configure(api_key=api_key)

    async def generate(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        gm = genai.GenerativeModel(model)
        chat = gm.start_chat(history=[
            {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
            for m in messages[:-1]
        ])
        response = await chat.send_message_async(
            messages[-1].content,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return LLMResponse(
            content=response.text,
            provider=self.name,
            model=model,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
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
        gm = genai.GenerativeModel(model)
        chat = gm.start_chat(history=[
            {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
            for m in messages[:-1]
        ])
        async for chunk in chat.send_message_async(
            messages[-1].content,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            stream=True,
        ):
            if chunk.text:
                yield chunk.text

    async def embedding(self, text: str, model: str = "models/embedding-001") -> List[float]:
        result = genai.embed_content(model=model, content=text)
        return result["embedding"]

    async def vision(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        gm = genai.GenerativeModel(model)
        parts = []
        for m in messages:
            if m.role == "user":
                parts.append({"text": m.content})
            elif m.role == "image":
                parts.append({"inline_data": m.content})
        response = await gm.generate_content_async(
            parts,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return LLMResponse(
            content=response.text,
            provider=self.name,
            model=model,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
            },
        )
