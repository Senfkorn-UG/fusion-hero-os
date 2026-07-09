"""
BaseConnector - Deepened version

Added connection state tracking, better error contracts,
and standardized metadata.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ConnectorConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    log_level: str = "INFO"
    auto_connect: bool = True


class ConnectorResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    connector_name: Optional[str] = None


class BaseConnector(ABC):
    """Deep base class for all connectors."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config or ConnectorConfig()
        self.name = self.__class__.__name__
        self._connected = False

    @abstractmethod
    async def connect(self) -> ConnectorResult:
        pass

    @abstractmethod
    async def disconnect(self) -> ConnectorResult:
        pass

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        pass

    def is_connected(self) -> bool:
        return self._connected

    def is_enabled(self) -> bool:
        return self.config.enabled
