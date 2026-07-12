from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: Dict[str, int] = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class LLMProvider(ABC):
    name: str
    models: List[str]

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def embedding(self, text: str, model: str) -> List[float]:
        pass

    @abstractmethod
    async def vision(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        pass

    def is_available(self) -> bool:
        return bool(self.api_key)

    def supports_model(self, model: str) -> bool:
        return model in self.models or any(model.startswith(m.split(":")[0]) for m in self.models if ":" in m)
