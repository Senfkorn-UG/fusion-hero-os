from abc import ABC, abstractmethod
from typing import Any
from normal_os.core.models import Task

import structlog

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Explicit base class for all agents. Forces clear interface."""

    name: str = "base"
    capabilities: list[str] = []

    def __init__(self, **kwargs: Any):
        self.config = kwargs
        logger.info("agent_initialized", name=self.name)

    @abstractmethod
    async def run(self, task: Task) -> dict[str, Any]:
        """Execute a task and return result. Must be implemented by subclasses."""
        pass

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "status": "idle",
        }

    async def health_check(self) -> bool:
        return True