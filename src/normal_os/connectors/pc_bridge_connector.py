"""
PCBridgeConnector for normalOS

Wraps the GrokPCBridge as a first-class connector.
This allows the Fusion Hero OS / Orchestrator to directly
interact with the user's local PC (Desktop inspection,
file operations, system info) through the bridge.

This is the explicit integration of the PC-Bridge concept
into the connector architecture.
"""

from typing import Any, Dict, Optional

from .base import BaseConnector, ConnectorConfig, ConnectorResult


class PCBridgeConnector(BaseConnector):
    """Connector for the local GrokPCBridge (user's PC)."""

    def __init__(self, config: Optional[ConnectorConfig] = None, bridge_url: str = "http://127.0.0.1:8765"):
        super().__init__(config)
        self.name = "PCBridgeConnector"
        self.bridge_url = bridge_url
        self.token: Optional[str] = None

    def set_token(self, token: str):
        self.token = token

    async def connect(self) -> ConnectorResult:
        # In real usage this would test /status endpoint
        return ConnectorResult(
            success=True,
            data={
                "status": "connected",
                "bridge_url": self.bridge_url,
                "note": "Connect to local GrokPCBridge"
            }
        )

    async def disconnect(self) -> ConnectorResult:
        return ConnectorResult(success=True, data={"status": "disconnected"})

    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        """
        Supported actions:
        - desktop_list
        - desktop_search (query=...)
        - desktop_read (path=...)
        - system_info
        - ping
        """
        action = action.lower()
        return ConnectorResult(
            success=True,
            data={
                "action": action,
                "params": params,
                "note": "Would call local GrokPCBridge at " + self.bridge_url,
                "token_set": bool(self.token)
            },
            metadata={"connector": self.name}
        )
