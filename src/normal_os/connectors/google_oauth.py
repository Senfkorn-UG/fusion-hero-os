# -*- coding: utf-8 -*-
"""
google_oauth.py — Gemeinsame Google OAuth-Schicht fuer Gmail / Drive / Calendar.

Aequivalent zu PHP ``$client->setIncludeGrantedScopes(true)``:
Neue Scopes werden inkrementell angefragt; bereits erteilte Scopes bleiben im Token.

Credentials:
  - ``GOOGLE_OAUTH_CREDENTIALS`` oder ``~/.fusion/google-oauth/credentials.json``
  - Alternativ ``GOOGLE_CLIENT_ID`` + ``GOOGLE_CLIENT_SECRET`` in .env

Tokens:
  - ``~/.fusion/google-oauth/token.json`` (kumuliert, include_granted_scopes)
  - ``~/.fusion/google-oauth/token_{connector_id}.json`` (Fallback)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

CONTRACT_VERSION = "1.0"

CONNECTOR_SCOPES: Dict[str, List[str]] = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ],
    "google_drive": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
    ],
    "google_calendar": [
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
}

GOOGLE_CONNECTOR_IDS = frozenset(CONNECTOR_SCOPES.keys())


def _oauth_dir() -> Path:
    custom = os.getenv("FUSION_GOOGLE_OAUTH_DIR")
    if custom:
        return Path(custom)
    return Path.home() / ".fusion" / "google-oauth"


def _credentials_path() -> Path:
    env = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "").strip()
    if env:
        return Path(env)
    return _oauth_dir() / "credentials.json"


def _unified_token_path() -> Path:
    return _oauth_dir() / "token.json"


def _connector_token_path(connector_id: str) -> Path:
    return _oauth_dir() / f"token_{connector_id}.json"


def _library_available() -> bool:
    try:
        import google.auth  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
        return True
    except ImportError:
        return False


def _client_configured() -> bool:
    if _credentials_path().exists():
        return True
    return bool(
        os.getenv("GOOGLE_CLIENT_ID", "").strip()
        and os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    )


def _load_token_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        return Credentials.from_authorized_user_file(str(path))
    except Exception:
        return None


def _save_credentials(creds: Any, connector_id: Optional[str] = None) -> None:
    _oauth_dir().mkdir(parents=True, exist_ok=True)
    _unified_token_path().write_text(creds.to_json(), encoding="utf-8")
    if connector_id:
        _connector_token_path(connector_id).write_text(creds.to_json(), encoding="utf-8")


def _scopes_satisfied(granted: List[str], required: List[str]) -> bool:
    granted_set = set(granted or [])
    return all(s in granted_set for s in required)


def get_credentials(connector_id: str, scopes: Optional[List[str]] = None) -> Any:
    """Laedt gueltige Credentials oder gibt None zurueck (kein interaktiver Flow)."""
    if connector_id not in CONNECTOR_SCOPES:
        return None
    if not _library_available() or not _client_configured():
        return None

    required = scopes or CONNECTOR_SCOPES[connector_id]
    creds = _load_token_file(_unified_token_path()) or _load_token_file(
        _connector_token_path(connector_id)
    )
    if creds is None:
        return None

    try:
        from google.auth.transport.requests import Request

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds, connector_id)
    except Exception:
        return None

    if not creds.valid:
        return None
    if not _scopes_satisfied(list(creds.scopes or []), required):
        return None
    return creds


def oauth_status(connector_id: str) -> Dict[str, Any]:
    """Ehrlicher OAuth-Status fuer einen Google-Konnektor."""
    if connector_id not in CONNECTOR_SCOPES:
        return {
            "connector_id": connector_id,
            "ready": False,
            "reason": "unknown_google_connector",
        }

    required = CONNECTOR_SCOPES[connector_id]
    creds_path = _credentials_path()
    token_path = _unified_token_path()
    lib_ok = _library_available()
    client_ok = _client_configured()

    token_present = token_path.exists() or _connector_token_path(connector_id).exists()
    granted: List[str] = []
    token_valid = False

    if lib_ok and token_present:
        creds = _load_token_file(token_path) or _load_token_file(
            _connector_token_path(connector_id)
        )
        if creds is not None:
            granted = list(creds.scopes or [])
            token_valid = bool(creds.valid)
            if creds.expired and creds.refresh_token and lib_ok:
                try:
                    from google.auth.transport.requests import Request

                    creds.refresh(Request())
                    _save_credentials(creds, connector_id)
                    token_valid = bool(creds.valid)
                    granted = list(creds.scopes or [])
                except Exception:
                    token_valid = False

    ready = lib_ok and client_ok and token_valid and _scopes_satisfied(granted, required)

    return {
        "connector_id": connector_id,
        "contract_version": CONTRACT_VERSION,
        "include_granted_scopes": True,
        "library_installed": lib_ok,
        "client_configured": client_ok,
        "credentials_file": str(creds_path),
        "credentials_present": creds_path.exists(),
        "token_file": str(token_path),
        "token_present": token_present,
        "token_valid": token_valid,
        "scopes_required": required,
        "scopes_granted": granted,
        "ready": ready,
        "reason": None if ready else _not_ready_reason(lib_ok, client_ok, token_present, token_valid, granted, required),
    }


def _not_ready_reason(
    lib_ok: bool,
    client_ok: bool,
    token_present: bool,
    token_valid: bool,
    granted: List[str],
    required: List[str],
) -> str:
    if not lib_ok:
        return "nicht verfuegbar: pip install google-auth google-auth-oauthlib google-api-python-client"
    if not client_ok:
        return "nicht verfuegbar: credentials.json oder GOOGLE_CLIENT_ID/SECRET fehlt"
    if not token_present:
        return "nicht verfuegbar: OAuth-Token fehlt (setup-google-oauth ausfuehren)"
    if not token_valid:
        return "nicht verfuegbar: Token abgelaufen oder ungueltig"
    if not _scopes_satisfied(granted, required):
        missing = [s for s in required if s not in set(granted)]
        return f"nicht verfuegbar: Scopes fehlen ({len(missing)}): re-auth mit include_granted_scopes"
    return "nicht verfuegbar"


def all_connectors_status() -> Dict[str, Any]:
    connectors = {cid: oauth_status(cid) for cid in CONNECTOR_SCOPES}
    ready = sum(1 for c in connectors.values() if c.get("ready"))
    return {
        "contract_version": CONTRACT_VERSION,
        "include_granted_scopes": True,
        "oauth_dir": str(_oauth_dir()),
        "ready_count": ready,
        "connector_count": len(connectors),
        "connectors": connectors,
    }


def probe(connector_id: str) -> Dict[str, Any]:
    """Leichter API-Check wenn OAuth bereit."""
    status = oauth_status(connector_id)
    result: Dict[str, Any] = {
        **status,
        "probed": False,
        "api_ok": False,
        "error": None,
    }
    if not status.get("ready"):
        result["error"] = status.get("reason")
        return result

    creds = get_credentials(connector_id)
    if creds is None:
        result["error"] = "credentials_unavailable"
        return result

    try:
        from googleapiclient.discovery import build

        if connector_id == "gmail":
            svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
            profile = svc.users().getProfile(userId="me").execute()
            result["probed"] = True
            result["api_ok"] = True
            result["profile"] = {
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal"),
            }
        elif connector_id == "google_drive":
            svc = build("drive", "v3", credentials=creds, cache_discovery=False)
            about = svc.about().get(fields="user,storageQuota").execute()
            result["probed"] = True
            result["api_ok"] = True
            result["profile"] = {
                "user": (about.get("user") or {}).get("emailAddress"),
            }
        elif connector_id == "google_calendar":
            svc = build("calendar", "v3", credentials=creds, cache_discovery=False)
            cal = svc.calendarList().list(maxResults=1).execute()
            result["probed"] = True
            result["api_ok"] = True
            result["profile"] = {"calendars": len(cal.get("items") or [])}
    except ImportError:
        result["error"] = "google-api-python-client not installed"
    except Exception as exc:
        result["probed"] = True
        result["api_ok"] = False
        result["error"] = str(exc)

    return result


def run_auth(connector_id: str, port: int = 0) -> Dict[str, Any]:
    """Interaktiver OAuth-Flow (Browser) mit include_granted_scopes."""
    if connector_id not in CONNECTOR_SCOPES:
        return {"ok": False, "error": f"unknown connector: {connector_id}"}
    if not _library_available():
        return {
            "ok": False,
            "error": "pip install google-auth google-auth-oauthlib google-api-python-client",
        }
    if not _client_configured():
        return {
            "ok": False,
            "error": f"credentials missing: {_credentials_path()}",
        }

    from google_auth_oauthlib.flow import InstalledAppFlow

    scopes = CONNECTOR_SCOPES[connector_id]
    creds_path = _credentials_path()

    if creds_path.exists():
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
    else:
        client_config = {
            "installed": {
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "redirect_uris": ["http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        _oauth_dir().mkdir(parents=True, exist_ok=True)
        tmp = _oauth_dir() / "client_config.json"
        tmp.write_text(json.dumps(client_config), encoding="utf-8")
        flow = InstalledAppFlow.from_client_secrets_file(str(tmp), scopes)

    creds = flow.run_local_server(
        port=port,
        prompt="consent",
        authorization_url_params={"include_granted_scopes": "true"},
    )
    _save_credentials(creds, connector_id)
    st = oauth_status(connector_id)
    return {
        "ok": True,
        "connector_id": connector_id,
        "token_file": str(_unified_token_path()),
        "scopes_granted": st.get("scopes_granted"),
        "ready": st.get("ready"),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Google OAuth setup for Fusion connectors")
    parser.add_argument("--status", action="store_true", help="Status aller Google-Konnektoren")
    parser.add_argument("--auth", metavar="CONNECTOR", help="OAuth-Flow (gmail|google_drive|google_calendar)")
    parser.add_argument("--probe", metavar="CONNECTOR", help="API-Probe fuer einen Konnektor")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()

    if args.auth:
        out = run_auth(args.auth, port=args.port)
    elif args.probe:
        out = probe(args.probe)
    else:
        out = all_connectors_status()

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
