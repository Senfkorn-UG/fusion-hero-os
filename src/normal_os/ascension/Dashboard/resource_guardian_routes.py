# -*- coding: utf-8 -*-
"""resource_guardian_routes.py — API + GUI-Anbindung fuer den Layered Resource
Guardian (Temperatur/Kuehlung/CPU/GPU/SSD, 3 Layer: sofort/kurzfristig/
mittelfristig, Kreuz-Check bei Eskalation).

WICHTIG (IDE/GUI-Trennung): Die eigentliche Probing-/Schwellenwert-/
Eskalationslogik (`src/normal_os/core/layered_resource_guardian.py`) wird
NICHT hier implementiert, sondern lokal ueber Windows-Coding-Tools. Dieses
Modul ist nur die API/GUI-Schicht, siehe
docs/02_architecture/LAYERED_RESOURCE_GUARDIAN_SPEC.md fuer den vollstaendigen
Schnittstellen-Vertrag. Solange das Kernmodul nicht existiert, liefern alle
Routen sauber "nicht verfuegbar" statt zu crashen (gleiches Muster wie
api_extensions.py / vr_routes.py: eigener APIRouter, per app.include_router()
eingehaengt).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

BASE = Path(__file__).parent

_NORMAL_OS = str(Path(__file__).resolve().parents[2])  # Dashboard -> ascension -> normal_os
if _NORMAL_OS not in sys.path:
    sys.path.insert(0, _NORMAL_OS)

try:
    from core.layered_resource_guardian import get_layered_resource_guardian
except Exception:
    get_layered_resource_guardian = None

router = APIRouter()

VALID_LAYERS = ("sofort", "kurzfristig", "mittelfristig")


@router.get("/resources", response_class=HTMLResponse)
async def resources_page():
    """GUI fuer den Layered Resource Guardian."""
    path = BASE / "templates" / "resources.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>resources.html not found</h1>", status_code=404)


def _guardian():
    if get_layered_resource_guardian is None:
        return None
    return get_layered_resource_guardian()


def _unavailable() -> Dict[str, Any]:
    return {
        "status": "LayeredResourceGuardian nicht verfuegbar - Kernmodul noch nicht implementiert",
        "spec": "docs/02_architecture/LAYERED_RESOURCE_GUARDIAN_SPEC.md",
        "expected_module": "src/normal_os/core/layered_resource_guardian.py",
    }


def _invalid_layer(layer: str) -> Dict[str, Any]:
    return {"error": f"layer muss einer von {VALID_LAYERS} sein, nicht {layer!r}"}


@router.get("/api/resources/status")
async def resources_status():
    g = _guardian()
    if not g:
        return _unavailable()
    return g.get_status()


@router.get("/api/resources/layer/{layer}")
async def resources_layer_snapshot(layer: str):
    if layer not in VALID_LAYERS:
        return _invalid_layer(layer)
    g = _guardian()
    if not g:
        return _unavailable()
    return g.get_layer_snapshot(layer)


class TriggerPayload(BaseModel):
    layer: str


@router.post("/api/resources/trigger")
async def resources_trigger(payload: TriggerPayload):
    if payload.layer not in VALID_LAYERS:
        return _invalid_layer(payload.layer)
    g = _guardian()
    if not g:
        return _unavailable()
    return g.trigger_check(payload.layer)


@router.get("/api/resources/history")
async def resources_history(layer: Optional[str] = None, last_n: Optional[int] = None):
    if layer is not None and layer not in VALID_LAYERS:
        return _invalid_layer(layer)
    g = _guardian()
    if not g:
        return {"history": [], **_unavailable()}
    return {"history": g.get_history(layer=layer, last_n=last_n)}


@router.get("/api/resources/escalations")
async def resources_escalations(last_n: Optional[int] = None):
    g = _guardian()
    if not g:
        return {"escalations": [], **_unavailable()}
    return {"escalations": g.get_escalation_log(last_n=last_n)}


@router.post("/api/resources/start")
async def resources_start():
    g = _guardian()
    if not g:
        return _unavailable()
    return {"started": g.start()}


@router.post("/api/resources/stop")
async def resources_stop():
    g = _guardian()
    if not g:
        return _unavailable()
    g.stop()
    return {"stopped": True}
