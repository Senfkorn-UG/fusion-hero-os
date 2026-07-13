from typing import Any, Callable, Dict, Type
from normal_os.agents.base import BaseAgent
import structlog

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """Explicit central registry for all agents. Makes implicit agent discovery explicit."""

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        if name in self._agents:
            logger.warning("agent_already_registered", name=name)
        self._agents[name] = agent_class
        logger.info("agent_registered", name=name, class_name=agent_class.__name__)

    def get(self, name: str) -> Type[BaseAgent]:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not registered")
        return self._agents[name]

    def create(self, name: str, **kwargs: Any) -> BaseAgent:
        if name in self._instances:
            return self._instances[name]

        agent_class = self.get(name)
        instance = agent_class(**kwargs)
        self._instances[name] = instance
        return instance

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "class": cls.__name__,
                "doc": cls.__doc__ or "",
            }
            for name, cls in self._agents.items()
        ]


# Global registry instance
registry = AgentRegistry()