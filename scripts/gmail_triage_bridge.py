#!/usr/bin/env python3
"""Gmail-Triage-Bridge — prüft MCP/OAuth und liefert strukturierte Triage."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _mcp_gmail_path() -> Path:
    return Path.home() / "mcps" / "gmail"


def _gmail_available() -> Dict[str, Any]:
    mcp = _mcp_gmail_path()
    tools = mcp / "tools"
    has_mcp = tools.is_dir()
    has_google = bool(
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GOOGLE_CLIENT_ID")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    return {
        "mcp_path": str(mcp),
        "mcp_tools": has_mcp,
        "google_credentials": has_google,
        "ready": has_mcp and has_google,
    }


def triage(days: int = 2) -> Dict[str, Any]:
    avail = _gmail_available()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    if not avail["ready"]:
        return {
            "status": "pending_setup",
            "since": since,
            "days": days,
            "availability": avail,
            "important": [],
            "setup_steps": [
                "Gmail MCP unter ~/mcps/gmail/tools einrichten",
                "GOOGLE_API_KEY oder OAuth-Credentials in .env setzen",
                "Cursor MCP: Gmail-Connector verbinden",
                "Alternativ: Inbox-Export als JSON/EML in workstation/inbox_export/ ablegen",
            ],
            "export_drop_dir": "workstation/inbox_export",
        }

    return {
        "status": "ready",
        "since": since,
        "days": days,
        "availability": avail,
        "important": [],
        "note": "MCP bereit — search_emails/list_messages über Gmail-MCP aufrufen",
    }


def main() -> int:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(json.dumps(triage(days), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
