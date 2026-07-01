# -*- coding: utf-8 -*-
"""Supabase-Integration für Fusion Hero OS Dashboard (FastAPI).

Projekt: https://supabase.com/dashboard/project/swmmoxhdzarmoupyssqe
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except Exception:
    pass

def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


SUPABASE_URL = _env("SUPABASE_URL", "PUBLIC_SUPABASE_URL")
SUPABASE_KEY = _env("SUPABASE_PUBLISHABLE_KEY", "PUBLIC_SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = _env("SUPABASE_SECRET_KEY")
SUPABASE_JWKS_URL = _env("SUPABASE_JWKS_URL")
SUPABASE_PROJECT_REF = _env("SUPABASE_PROJECT_REF", "PUBLIC_SUPABASE_PROJECT_REF", default="swmmoxhdzarmoupyssqe")

try:
    from supabase import Client, create_client  # type: ignore
    import supabase as _supabase_pkg

    _SUPABASE_VERSION: Optional[str] = getattr(_supabase_pkg, "__version__", None)
    _PACKAGE_AVAILABLE = True
    _IMPORT_ERROR = ""
except Exception as e:
    create_client = None  # type: ignore
    Client = Any  # type: ignore
    _SUPABASE_VERSION = None
    _PACKAGE_AVAILABLE = False
    _IMPORT_ERROR = str(e)

_client: "Optional[Client]" = None
_client_error: str = ""


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_client() -> "Optional[Client]":
    global _client, _client_error
    if _client is not None:
        return _client
    if not _PACKAGE_AVAILABLE or create_client is None:
        _client_error = f"supabase package not available: {_IMPORT_ERROR}"
        return None
    if not is_configured():
        _client_error = "missing SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY"
        return None
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _client_error = ""
    except Exception as e:
        _client = None
        _client_error = f"create_client failed: {e}"
    return _client


def probe(timeout: float = 4.0) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "reachable": False,
        "key_accepted": False,
        "http_status": None,
        "latency_ms": None,
        "error": None,
        "project_ref": SUPABASE_PROJECT_REF,
    }
    if not is_configured():
        result["error"] = "not configured"
        return result
    try:
        import httpx
    except Exception as e:
        result["error"] = f"httpx not available: {e}"
        return result

    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/settings"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    start = time.perf_counter()
    try:
        resp = httpx.get(url, headers=headers, timeout=timeout)
        result["http_status"] = resp.status_code
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["reachable"] = resp.status_code < 500
        result["key_accepted"] = resp.status_code == 200
    except Exception as e:
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["error"] = str(e)
    return result


def status(do_probe: bool = False, timeout: float = 4.0) -> Dict[str, Any]:
    client = get_client()
    info: Dict[str, Any] = {
        "configured": is_configured(),
        "package_available": _PACKAGE_AVAILABLE,
        "package_version": _SUPABASE_VERSION,
        "url": SUPABASE_URL or None,
        "jwks_url": SUPABASE_JWKS_URL or None,
        "secret_key_configured": bool(SUPABASE_SECRET_KEY),
        "project_ref": SUPABASE_PROJECT_REF,
        "dashboard_url": f"https://supabase.com/dashboard/project/{SUPABASE_PROJECT_REF}",
        "client_initialized": client is not None,
        "error": _client_error or None,
    }
    if do_probe:
        info["probe"] = probe(timeout=timeout)
    return info