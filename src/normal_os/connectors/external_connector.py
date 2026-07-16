"""Adapter connector that fulfils :class:`BaseConnector` via a spec.

One :class:`ExternalToolConnector` instance wraps one :class:`ConnectorSpec`.
It validates inputs against the declared capabilities, refuses unknown or
mutating tools unless explicitly allowed, and routes the call through the
correct transport (`external-tool` CLI or `gh` CLI for GitHub). It never holds
credentials; auth is resolved by the underlying CLI on the server side.

Health checks are lazy and safe: they only ever run the spec's read-only probe,
and any failure is captured (not raised) so that startup stays robust when a
service is temporarily unavailable, unauthenticated, or rate limited.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, List, Optional

from .base import BaseConnector, ConnectorConfig, ConnectorResult
from .external_tool_client import ExternalToolClient, ExternalToolError
from .specs import (
    TRANSPORT_GH_CLI,
    ConnectorSpec,
)


class ExternalToolConnector(BaseConnector):
    """Spec-driven connector routed through a server-side CLI."""

    def __init__(self, spec: ConnectorSpec,
                 config: Optional[ConnectorConfig] = None,
                 client: Optional[ExternalToolClient] = None):
        super().__init__(config)
        self.spec = spec
        self.name = f"{spec.display_name} ({spec.source_id})"
        self._client = client or ExternalToolClient(timeout=self.config.timeout_seconds)
        self._last_health: Dict[str, Any] = {"checked": False}

    # -- metadata ---------------------------------------------------------
    def capabilities(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": c.name,
                "description": c.description,
                "required": list(c.required),
                "mutating": c.mutating,
            }
            for c in self.spec.capabilities
        ]

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.spec.name,
            "source_id": self.spec.source_id,
            "display_name": self.spec.display_name,
            "transport": self.spec.transport,
            "enabled": self.is_enabled(),
            "connected": self.is_connected(),
            "capabilities": len(self.spec.capabilities),
            "last_health": self._last_health,
        }

    # -- lifecycle --------------------------------------------------------
    async def connect(self) -> ConnectorResult:
        """Lazy connect: mark available if the transport is reachable.

        Does not perform any connector traffic (that is what `health_check`
        is for), so it is cheap and side-effect free.
        """
        available = self._transport_available()
        self._connected = available
        return ConnectorResult(
            success=available,
            data={"status": "available" if available else "unavailable",
                  "transport": self.spec.transport},
            error=None if available else f"transport '{self.spec.transport}' not available",
            connector_name=self.spec.name,
        )

    async def disconnect(self) -> ConnectorResult:
        self._connected = False
        return ConnectorResult(success=True, data={"status": "disconnected"},
                               connector_name=self.spec.name)

    def _transport_available(self) -> bool:
        if self.spec.transport == TRANSPORT_GH_CLI:
            try:
                import shutil
                return shutil.which("gh") is not None
            except Exception:
                return False
        return self._client.is_available()

    # -- validation -------------------------------------------------------
    def _validate(self, action: str, params: Dict[str, Any],
                  allow_mutating: bool) -> Optional[str]:
        cap = self.spec.capability(action)
        if cap is None:
            known = ", ".join(c.name for c in self.spec.capabilities)
            return f"unknown tool '{action}' for {self.spec.name}. Known: {known}"
        if cap.mutating and not allow_mutating:
            return (f"tool '{action}' is mutating and blocked in read-only mode; "
                    f"pass allow_mutating=True to permit it")
        missing = [r for r in cap.required if r not in params]
        if missing:
            return f"missing required argument(s) for '{action}': {', '.join(missing)}"
        # OpticOdds passthrough: block state-changing POST unless explicitly allowed.
        if self.spec.name == "opticodds":
            method = str(params.get("method", "GET")).upper()
            if method != "GET" and not allow_mutating:
                return "OpticOdds non-GET method blocked in read-only mode"
        return None

    # -- execution --------------------------------------------------------
    async def execute(self, action: str, params: Dict[str, Any],
                      allow_mutating: bool = False) -> ConnectorResult:
        params = params or {}
        err = self._validate(action, params, allow_mutating)
        if err:
            return ConnectorResult(success=False, error=err,
                                   metadata={"kind": "validation_error"},
                                   connector_name=self.spec.name)
        try:
            data = self._dispatch(action, params)
            return ConnectorResult(success=True, data=data,
                                   metadata={"transport": self.spec.transport},
                                   connector_name=self.spec.name)
        except ExternalToolError as exc:
            return ConnectorResult(
                success=False,
                error=str(exc),
                metadata={"kind": exc.kind, "auth_url": exc.auth_url},
                connector_name=self.spec.name,
            )

    def _dispatch(self, action: str, params: Dict[str, Any]) -> Any:
        if self.spec.transport == TRANSPORT_GH_CLI:
            return self._dispatch_gh(action, params)
        return self._client.call(self.spec.source_id, action, params)

    def _dispatch_gh(self, action: str, params: Dict[str, Any]) -> Any:
        """Route GitHub read-only actions through the authenticated gh CLI."""
        if action == "get_me":
            cmd = ["gh", "api", "user"]
        elif action == "list_repos":
            cmd = ["gh", "repo", "list", "--json", "name,owner,url", "--limit",
                   str(params.get("limit", 30))]
        elif action == "get_repo":
            cmd = ["gh", "api", f"repos/{params['owner']}/{params['repo']}"]
        elif action == "list_pull_requests":
            cmd = ["gh", "api",
                   f"repos/{params['owner']}/{params['repo']}/pulls"]
        else:  # defensive: validation should have caught this
            raise ExternalToolError("connector_error", f"unsupported gh action '{action}'",
                                    source_id=self.spec.source_id, tool_name=action)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise ExternalToolError("timeout", "gh CLI timed out",
                                    source_id=self.spec.source_id) from exc
        except OSError as exc:
            raise ExternalToolError("transport_error", str(exc),
                                    source_id=self.spec.source_id) from exc
        if proc.returncode != 0:
            raise ExternalToolError("connector_error", (proc.stderr or "gh failed").strip(),
                                    source_id=self.spec.source_id, tool_name=action)
        out = (proc.stdout or "").strip()
        try:
            return json.loads(out)
        except (json.JSONDecodeError, ValueError):
            return out

    # -- health -----------------------------------------------------------
    async def health_check(self) -> ConnectorResult:
        """Run the spec's safe read-only probe. Never raises; records result."""
        probe = self.spec.health
        if probe is None:
            self._last_health = {"checked": True, "ok": None, "reason": "no probe"}
            return ConnectorResult(success=True, data=self._last_health,
                                   connector_name=self.spec.name)
        if not self._transport_available():
            self._last_health = {"checked": True, "ok": False, "kind": "not_available"}
            return ConnectorResult(success=False, error="transport not available",
                                   metadata={"kind": "not_available"},
                                   connector_name=self.spec.name)
        result = await self.execute(probe.tool_name, dict(probe.arguments),
                                    allow_mutating=False)
        self._connected = result.success
        self._last_health = {
            "checked": True,
            "ok": result.success,
            "kind": (result.metadata or {}).get("kind") if not result.success else None,
        }
        return result
