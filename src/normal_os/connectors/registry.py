"""ConnectorRegistry for normalOS.

Registers:
  - Spec-driven external-tool connectors (Slack, Jira, Files, GCal, GitHub MCP,
    Finance, OpticOdds) via :class:`ExternalToolConnector`
  - Native Google OAuth connectors (Gmail, Drive, Calendar) + GitHub/Notion
  - Legacy local PC bridge

Connectors are created lazily — no network/CLI traffic at construction time.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .base import BaseConnector, ConnectorConfig
from .external_connector import ExternalToolConnector
from .external_tool_client import ExternalToolClient
from .github_connector import GitHubConnector
from .gmail_connector import GmailConnector
from .google_calendar_connector import GoogleCalendarConnector
from .google_drive_connector import GoogleDriveConnector
from .google_oauth import all_connectors_status
from .notion_connector import NotionConnector
from .pc_bridge_connector import PCBridgeConnector
from .specs import CONNECTOR_SPECS


class ConnectorRegistry:
    """Registry holding all active connectors."""

    def __init__(
        self,
        client: Optional[ExternalToolClient] = None,
        config: Optional[ConnectorConfig] = None,
    ):
        self._connectors: Dict[str, BaseConnector] = {}
        self._client = client
        self._config = config
        self._register_defaults()

    def _register_defaults(self) -> None:
        for name, spec in CONNECTOR_SPECS.items():
            self.register(
                name,
                ExternalToolConnector(spec, config=self._config, client=self._client),
            )
        # Native OAuth / first-party connectors (not only external-tool CLI).
        self.register("github_native", GitHubConnector())
        self.register("gmail", GmailConnector())
        self.register("google_drive", GoogleDriveConnector())
        self.register("google_calendar", GoogleCalendarConnector())
        self.register("notion", NotionConnector())
        self.register("pc_bridge", PCBridgeConnector())

    def register(self, name: str, connector: BaseConnector) -> None:
        self._connectors[name.lower()] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        return self._connectors.get(name.lower())

    def list_connectors(self) -> List[str]:
        return list(self._connectors.keys())

    def status(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self.get(name)
        if conn is None:
            return None
        if isinstance(conn, ExternalToolConnector):
            return conn.status()
        entry: Dict[str, Any] = {
            "name": name,
            "connected": conn.is_connected(),
            "enabled": conn.is_enabled(),
        }
        status_fn = getattr(conn, "status", None)
        if callable(status_fn):
            try:
                entry["oauth"] = status_fn()
            except Exception as exc:  # noqa: BLE001 — status must not raise
                entry["oauth_error"] = str(exc)
        return entry

    def statuses(self) -> Dict[str, Dict[str, Any]]:
        return {name: self.status(name) for name in self._connectors}

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
                try:
                    entry["oauth"] = status_fn()
                    entry["ready"] = bool(
                        (entry.get("oauth") or {}).get("ready", conn.is_connected())
                    )
                except Exception:  # noqa: BLE001
                    entry["ready"] = conn.is_connected()
            else:
                entry["ready"] = conn.is_connected()
            items[name] = entry
        google = all_connectors_status()
        return {
            "connectors": items,
            "google_oauth": google,
            "ready_count": sum(1 for v in items.values() if v.get("ready")),
        }

    def capabilities(self, name: str) -> Optional[List[Dict[str, Any]]]:
        conn = self.get(name)
        if isinstance(conn, ExternalToolConnector):
            return conn.capabilities()
        return None

    async def connect_all(self) -> Dict[str, Any]:
        results = {}
        for name, conn in self._connectors.items():
            if conn.is_enabled():
                results[name] = await conn.connect()
        return results

    async def health_check_all(self) -> Dict[str, Any]:
        """Run every enabled external-tool connector's safe read-only probe."""
        names, coros = [], []
        for name, conn in self._connectors.items():
            if isinstance(conn, ExternalToolConnector) and conn.is_enabled():
                names.append(name)
                coros.append(conn.health_check())
        results = await asyncio.gather(*coros, return_exceptions=True)
        out: Dict[str, Any] = {}
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                out[name] = {"ok": False, "error": str(res)}
            else:
                out[name] = {
                    "ok": res.success,
                    "kind": (res.metadata or {}).get("kind"),
                }
        return out


_default_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Return a process-wide default registry (created lazily)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ConnectorRegistry()
    return _default_registry
