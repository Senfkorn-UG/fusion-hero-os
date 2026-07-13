"""
ConnectorRegistry for normalOS (expanded)

Now also registers the PCBridgeConnector by default.
"""

from typing import Dict, Type, Optional
from .base import BaseConnector, ConnectorConfig
from .github_connector import GitHubConnector
from .google_drive_connector import GoogleDriveConnector
from .notion_connector import NotionConnector
from .pc_bridge_connector import PCBridgeConnector


class ConnectorRegistry:
    """Registry holding all active connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("github", GitHubConnector())
        self.register("google_drive", GoogleDriveConnector())
        self.register("notion", NotionConnector())
        self.register("pc_bridge", PCBridgeConnector())
        # Gmail, Calendar, Canva etc. will be added autonomously

    def register(self, name: str, connector: BaseConnector):
        self._connectors[name.lower()] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        return self._connectors.get(name.lower())

    def list_connectors(self) -> list[str]:
        return list(self._connectors.keys())

    async def connect_all(self):
        results = {}
        for name, conn in self._connectors.items():
            if conn.is_enabled():
                results[name] = await conn.connect()
        return results
