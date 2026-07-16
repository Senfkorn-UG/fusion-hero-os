# -*- coding: utf-8 -*-
"""FastAPI routes exposing the external connector layer.

Thin HTTP surface over ``normal_os.connectors``. All connector traffic happens
server-side through the registry (which uses the `external-tool` / `gh` CLIs);
no credentials are ever handled here or exposed to the frontend. Mutating tools
are blocked unless the caller explicitly opts in via ``allow_mutating``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

# Make the src-layout `normal_os` package importable when this router is loaded
# by the dashboard (which runs from 03_Code/Dashboard).
_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from normal_os.connectors import get_registry  # noqa: E402

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


class CallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}
    allow_mutating: bool = False


@router.get("")
async def list_connectors() -> Dict[str, Any]:
    reg = get_registry()
    return {"connectors": reg.list_connectors(), "statuses": reg.statuses()}


@router.get("/{name}")
async def connector_detail(name: str) -> Dict[str, Any]:
    reg = get_registry()
    status = reg.status(name)
    if status is None:
        return {"error": f"unknown connector '{name}'"}
    return {"status": status, "capabilities": reg.capabilities(name)}


@router.get("/{name}/health")
async def connector_health(name: str) -> Dict[str, Any]:
    reg = get_registry()
    conn = reg.get(name)
    if conn is None or not hasattr(conn, "health_check"):
        return {"error": f"unknown connector '{name}'"}
    result = await conn.health_check()
    return {"ok": result.success, "error": result.error, "metadata": result.metadata}


@router.post("/{name}/call")
async def connector_call(name: str, req: CallRequest) -> Dict[str, Any]:
    reg = get_registry()
    conn = reg.get(name)
    if conn is None:
        return {"success": False, "error": f"unknown connector '{name}'"}
    result = await conn.execute(req.tool, req.arguments, allow_mutating=req.allow_mutating)
    return {
        "success": result.success,
        "data": result.data if result.success else None,
        "error": result.error,
        "metadata": result.metadata,
    }
