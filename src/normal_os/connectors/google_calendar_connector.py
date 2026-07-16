# -*- coding: utf-8 -*-
"""Google Calendar Connector — OAuth ueber google_oauth.py."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseConnector, ConnectorConfig, ConnectorResult
from .google_oauth import get_credentials, oauth_status, probe


class GoogleCalendarConnector(BaseConnector):
    CONNECTOR_ID = "google_calendar"

    def __init__(self, config: Optional[ConnectorConfig] = None):
        super().__init__(config)
        self.name = "GoogleCalendarConnector"

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
            data={"status": "connected", "service": "google_calendar", "oauth": st},
            metadata={"connector": self.name},
        )

    async def disconnect(self) -> ConnectorResult:
        self._connected = False
        return ConnectorResult(success=True, data={"status": "disconnected"})

    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        st = oauth_status(self.CONNECTOR_ID)
        if not st.get("ready"):
            return ConnectorResult(
                success=False,
                error=st.get("reason") or "nicht verfuegbar",
                data={"oauth": st},
                metadata={"connector": self.name},
            )

        creds = get_credentials(self.CONNECTOR_ID)
        if creds is None:
            return ConnectorResult(success=False, error="credentials_unavailable")

        try:
            from googleapiclient.discovery import build

            svc = build("calendar", "v3", credentials=creds, cache_discovery=False)
            if action == "list_calendars":
                resp = svc.calendarList().list(maxResults=int(params.get("max_results", 10))).execute()
                return ConnectorResult(success=True, data=resp, metadata={"connector": self.name})
            if action == "list_events":
                calendar_id = params.get("calendar_id", "primary")
                resp = (
                    svc.events()
                    .list(calendarId=calendar_id, maxResults=int(params.get("max_results", 10)))
                    .execute()
                )
                return ConnectorResult(success=True, data=resp, metadata={"connector": self.name})
            return ConnectorResult(
                success=False,
                error=f"unsupported action: {action}",
                data={"supported": ["list_calendars", "list_events"]},
            )
        except Exception as exc:
            return ConnectorResult(success=False, error=str(exc), metadata={"connector": self.name})

    def probe_sync(self) -> Dict[str, Any]:
        return probe(self.CONNECTOR_ID)
