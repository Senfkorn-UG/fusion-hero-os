"""ConnectorRegistry for normalOS.

Registers the externally connected services (Slack, Jira, Files, Gmail/Calendar,
GitHub, Finance, OpticOdds) as spec-driven :class:`ExternalToolConnector`
instances, plus the legacy local connectors (PC bridge) for backward
compatibility. Connectors are created lazily and cheaply — no network/CLI
traffic happens at construction time, only when `health_check`/`execute` is
called — so importing or instantiating the registry is always safe.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .base import BaseConnector, ConnectorConfig
from .external_connector import ExternalToolConnector
from .external_tool_client import ExternalToolClient
from .pc_bridge_connector import PCBridgeConnector
from .specs import CONNECTOR_SPECS


class ConnectorRegistry:
    """Registry holding all active connectors."""

    def __init__(self, client: Optional[ExternalToolClient] = None,
                 config: Optional[ConnectorConfig] = None):
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
        # Legacy local connector (not an external SaaS tool).
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
        return {"name": name, "connected": conn.is_connected(),
                "enabled": conn.is_enabled()}

    def statuses(self) -> Dict[str, Dict[str, Any]]:
        return {name: self.status(name) for name in self._connectors}

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
        """Run every enabled connector's safe read-only probe concurrently."""
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
                out[name] = {"ok": res.success,
                             "kind": (res.metadata or {}).get("kind")}
        return out


_default_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Return a process-wide default registry (created lazily)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ConnectorRegistry()
    return _default_registry
