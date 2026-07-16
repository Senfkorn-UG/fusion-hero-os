# -*- coding: utf-8 -*-
"""Google Drive Connector — OAuth ueber google_oauth.py."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseConnector, ConnectorConfig, ConnectorResult
from .google_oauth import get_credentials, oauth_status, probe


class GoogleDriveConnector(BaseConnector):
    """Connector for Google Drive operations via OAuth."""

    CONNECTOR_ID = "google_drive"

    def __init__(self, config: Optional[ConnectorConfig] = None):
        super().__init__(config)
        self.name = "GoogleDriveConnector"

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
            data={"status": "connected", "service": "google_drive", "oauth": st},
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

            svc = build("drive", "v3", credentials=creds, cache_discovery=False)
            if action in ("search_files", "find_by_name", "list_recent"):
                q = params.get("query") or params.get("name") or ""
                if action == "list_recent":
                    q = q or "mimeType != 'application/vnd.google-apps.folder'"
                resp = (
                    svc.files()
                    .list(q=q, pageSize=int(params.get("page_size", 10)), fields="files(id,name,mimeType,modifiedTime)")
                    .execute()
                )
                return ConnectorResult(
                    success=True,
                    data={"files": resp.get("files", [])},
                    metadata={"connector": self.name, "action": action},
                )
            if action == "read_file":
                file_id = params.get("file_id")
                if not file_id:
                    return ConnectorResult(success=False, error="file_id required")
                meta = svc.files().get(fileId=file_id, fields="id,name,mimeType").execute()
                return ConnectorResult(
                    success=True,
                    data={"file": meta},
                    metadata={"connector": self.name, "action": action},
                )
            return ConnectorResult(
                success=False,
                error=f"unsupported action: {action}",
                data={"supported": ["search_files", "find_by_name", "list_recent", "read_file"]},
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
