# -*- coding: utf-8 -*-
"""Gmail Connector — OAuth ueber google_oauth.py, ausfuehrbar via ConnectorRegistry."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseConnector, ConnectorConfig, ConnectorResult
from .google_oauth import get_credentials, oauth_status, probe


class GmailConnector(BaseConnector):
    """Gmail via Google OAuth (include_granted_scopes)."""

    CONNECTOR_ID = "gmail"

    def __init__(self, config: Optional[ConnectorConfig] = None):
        super().__init__(config)
        self.name = "GmailConnector"

    def status(self) -> Dict[str, Any]:
        return oauth_status(self.CONNECTOR_ID)

    async def connect(self) -> ConnectorResult:
        st = oauth_status(self.CONNECTOR_ID)
        if not st.get("ready"):
            return ConnectorResult(
                success=False,
                error=st.get("reason") or "nicht verfuegbar",
                data=st,
                metadata={"connector": self.name},
            )
        self._connected = True
        return ConnectorResult(
            success=True,
            data={"status": "connected", "service": "gmail", "oauth": st},
            metadata={"connector": self.name},
        )

    async def disconnect(self) -> ConnectorResult:
        self._connected = False
        return ConnectorResult(success=True, data={"status": "disconnected"})

    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        action = action.lower()
        st = oauth_status(self.CONNECTOR_ID)
        if not st.get("ready"):
            return ConnectorResult(
                success=False,
                error=st.get("reason") or "nicht verfuegbar",
                data={"action": action, "params": params, "oauth": st},
                metadata={"connector": self.name},
            )

        creds = get_credentials(self.CONNECTOR_ID)
        if creds is None:
            return ConnectorResult(
                success=False,
                error="credentials_unavailable",
                metadata={"connector": self.name},
            )

        try:
            from googleapiclient.discovery import build

            svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
            if action in ("list_messages", "search", "parse_replies"):
                query = params.get("query", "is:unread")
                max_results = int(params.get("max_results", 10))
                resp = (
                    svc.users()
                    .messages()
                    .list(userId="me", q=query, maxResults=max_results)
                    .execute()
                )
                return ConnectorResult(
                    success=True,
                    data={"messages": resp.get("messages", []), "result_size": resp.get("resultSizeEstimate")},
                    metadata={"connector": self.name, "action": action},
                )
            if action == "get_profile":
                profile = svc.users().getProfile(userId="me").execute()
                return ConnectorResult(
                    success=True,
                    data=profile,
                    metadata={"connector": self.name, "action": action},
                )
            return ConnectorResult(
                success=False,
                error=f"unsupported action: {action}",
                data={"supported": ["list_messages", "search", "parse_replies", "get_profile"]},
                metadata={"connector": self.name},
            )
        except ImportError:
            return ConnectorResult(
                success=False,
                error="google-api-python-client not installed",
                metadata={"connector": self.name},
            )
        except Exception as exc:
            return ConnectorResult(
                success=False,
                error=str(exc),
                metadata={"connector": self.name, "action": action},
            )

    def probe_sync(self) -> Dict[str, Any]:
        return probe(self.CONNECTOR_ID)
