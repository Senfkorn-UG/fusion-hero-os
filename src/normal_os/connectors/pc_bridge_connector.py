"""
PCBridgeConnector - Deep implementation

Full connector for the local GrokPCBridge.
Includes token management, connection state, and
clear action contracts for desktop operations.
"""

from typing import Any, Dict, Optional

import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResult


class PCBridgeConnector(BaseConnector):
    """Deep connector for user's local PC via GrokPCBridge."""

    def __init__(self, config: Optional[ConnectorConfig] = None, bridge_url: str = "http://127.0.0.1:8765"):
        super().__init__(config)
        self.name = "PCBridgeConnector"
        self.bridge_url = bridge_url
        self.token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

    def set_token(self, token: str):
        self.token = token

    async def connect(self) -> ConnectorResult:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.bridge_url}/status", headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    self._connected = True
                    return ConnectorResult(
                        success=True,
                        data=resp.json(),
                        metadata={"bridge_url": self.bridge_url, "connected": True}
                    )
                else:
                    return ConnectorResult(success=False, error=f"Bridge returned {resp.status_code}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def disconnect(self) -> ConnectorResult:
        self._connected = False
        if self._client:
            await self._client.aclose()
        return ConnectorResult(success=True, data={"status": "disconnected"})

    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        if not self.token:
            return ConnectorResult(success=False, error="No token set. Call set_token() first.")

        headers = {"Authorization": f"Bearer {self.token}"}
        action = action.lower()

        try:
            async with httpx.AsyncClient() as client:
                if action == "desktop_list":
                    subpath = params.get("subpath", "")
                    resp = await client.get(f"{self.bridge_url}/desktop/list?subpath={subpath}", headers=headers)
                elif action == "desktop_search":
                    query = params.get("query", "")
                    resp = await client.get(f"{self.bridge_url}/desktop/search?query={query}", headers=headers)
                elif action == "desktop_read":
                    path = params.get("path", "")
                    resp = await client.get(f"{self.bridge_url}/desktop/read?path={path}", headers=headers)
                elif action == "system_info":
                    resp = await client.get(f"{self.bridge_url}/system/info", headers=headers)
                elif action == "ping":
                    resp = await client.get(f"{self.bridge_url}/ping", headers=headers)
                else:
                    return ConnectorResult(success=False, error=f"Unknown action: {action}")

                if resp.status_code == 200:
                    return ConnectorResult(success=True, data=resp.json())
                else:
                    return ConnectorResult(success=False, error=f"Bridge error: {resp.status_code} - {resp.text}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))
