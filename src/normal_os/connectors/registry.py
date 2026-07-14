"""
ConnectorRegistry for normalOS (expanded)

Registers runtime connectors including Google OAuth (Gmail, Drive, Calendar).
"""

from typing import Any, Dict, Optional, Type

from .base import BaseConnector, ConnectorConfig
from .github_connector import GitHubConnector
from .gmail_connector import GmailConnector
from .google_calendar_connector import GoogleCalendarConnector
from .google_drive_connector import GoogleDriveConnector
from .google_oauth import GOOGLE_CONNECTOR_IDS, all_connectors_status
from .notion_connector import NotionConnector
from .pc_bridge_connector import PCBridgeConnector


class ConnectorRegistry:
    """Registry holding all active connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("github", GitHubConnector())
        self.register("gmail", GmailConnector())
        self.register("google_drive", GoogleDriveConnector())
        self.register("google_calendar", GoogleCalendarConnector())
        self.register("notion", NotionConnector())
        self.register("pc_bridge", PCBridgeConnector())

    def register(self, name: str, connector: BaseConnector):
        self._connectors[name.lower()] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        return self._connectors.get(name.lower())

    def list_connectors(self) -> list[str]:
        return list(self._connectors.keys())

    def status_report(self) -> Dict[str, Any]:
        """Status aller Runtime-Konnektoren inkl. Google OAuth."""
        items: Dict[str, Any] = {}
        for name, conn in self._connectors.items():
            entry: Dict[str, Any] = {
                "name": name,
                "enabled": conn.is_enabled(),
                "connected": conn.is_connected(),
            }
            status_fn = getattr(conn, "status", None)
            if callable(status_fn):
                entry["oauth"] = status_fn()
                entry["ready"] = entry["oauth"].get("ready", False)
            else:
                entry["ready"] = conn.is_connected()
            items[name] = entry
        google = all_connectors_status()
        return {
            "connectors": items,
            "google_oauth": google,
            "ready_count": sum(1 for v in items.values() if v.get("ready")),
        }

    async def connect_all(self):
        results = {}
        for name, conn in self._connectors.items():
            if conn.is_enabled():
                results[name] = await conn.connect()
        return results
