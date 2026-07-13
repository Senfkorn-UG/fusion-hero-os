#!/usr/bin/env python3
"""Gmail-Triage-Bridge — prüft MCP/OAuth und liefert strukturierte Triage."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parents[1]
_ENV = _REPO / "workstation" / ".env"
if _ENV.exists():
    for line in _ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip()


def _mcp_gmail_path() -> Path:
    return Path.home() / "mcps" / "gmail"


def _gmail_available() -> Dict[str, Any]:
    mcp = _mcp_gmail_path()
    tools = mcp / "tools"
    has_mcp = tools.is_dir()
    has_google = bool(
        os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GOOGLE_CLIENT_ID", "").strip()
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    )
    return {
        "mcp_path": str(mcp),
        "mcp_tools": has_mcp,
        "google_credentials": has_google,
        "ready": has_mcp and has_google,
    }


def _scan_inbox_export() -> List[Dict[str, Any]]:
    """Liest manuelle Exports aus workstation/inbox_export/."""
    export_dir = Path(__file__).resolve().parents[1] / "workstation" / "inbox_export"
    items: List[Dict[str, Any]] = []
    if not export_dir.is_dir():
        return items
    for f in sorted(export_dir.iterdir()):
        if f.name.startswith(".") or f.suffix not in (".json", ".eml", ".mbox", ".txt"):
            continue
        try:
            if f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    items.extend(data[:50])
                elif isinstance(data, dict) and "messages" in data:
                    items.extend(data["messages"][:50])
            else:
                items.append({
                    "file": f.name,
                    "preview": f.read_text(encoding="utf-8", errors="replace")[:500],
                    "source": "inbox_export",
                })
        except Exception as exc:
            items.append({"file": f.name, "error": str(exc)[:120]})
    return items


def triage(days: int = 2) -> Dict[str, Any]:
    avail = _gmail_available()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    exported = _scan_inbox_export()

    if exported:
        return {
            "status": "from_export",
            "since": since,
            "days": days,
            "availability": avail,
            "important": exported[:20],
            "export_count": len(exported),
            "export_drop_dir": "workstation/inbox_export",
            "note": "Manuelle Exports gefunden — Triage aus Dateien",
        }

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
