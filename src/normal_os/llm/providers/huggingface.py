"""Hugging Face Inference Provider - Thousands of open-source models"""
import httpx
from typing import AsyncIterator, List, Optional
from .base import LLMProvider, LLMMessage, LLMResponse


class HuggingFaceProvider(LLMProvider):
    name = "huggingface"
    models = [
        "meta-llama/Llama-3.2-3B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.1-70B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "google/gemma-2-9b-it",
        "microsoft/Phi-3.5-mini-instruct",
        "nvidia/Nemotron-3-Ultra",
    ]
    base_url = "https://api-inference.huggingface.co"

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        model: str = "meta-llama/Llama-3.1-8B-Instruct",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens or 1024,
                "return_full_text": False,
            },
        }
        response = await self.client.post(f"/models/{model}", json=payload)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            content = data[0].get("generated_text", "")
        else:
            content = str(data)
        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(content), "total_tokens": len(prompt) + len(content)},
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        model: str = "meta-llama/Llama-3.1-8B-Instruct",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        # HF Inference API does not support streaming well for chat
        response = await self.generate(messages, model, temperature, max_tokens, **kwargs)
        for word in response.content.split():
            yield word + " "

    async def embedding(self, text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
        response = await self.client.post(
            f"/models/{model}",
            json={"inputs": text},
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else []

    async def vision(
        self,
        messages: List[LLMMessage],
        model: str = "llava-hf/llava-1.5-7b-hf",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        # Not implemented for HF Inference API
        return await self.generate(messages, model, temperature, max_tokens, **kwargs)

    def _messages_to_prompt(self, messages: List[LLMMessage]) -> str:
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"<|system|>\n{msg.content}\n"
            elif msg.role == "user":
                prompt += f"<|user|>\n{msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"<|assistant|>\n{msg.content}\n"
        prompt += "<|assistant|>\n"
        return prompt
