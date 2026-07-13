# -*- coding: utf-8 -*-
"""ascension_v9_routes.py — Dashboard-Endpunkte fuer AscensionCore v9.5/v9.6.

Folgt demselben Muster wie api_extensions.py / vr_routes.py (eigener
APIRouter, in app.py per app.include_router() eingehaengt) statt die
1300+ Zeilen lange app.py direkt zu erweitern.

Exponiert Stage9-Tracker, Sisyphos-Oszillation, Psycholyse-Logger, den
QUBO-Devil-Christus-Optimizer, HarmonisierungsCoreModule und Geisterjagdmodul
(ascension_os/core/, siehe dortige Modul-Docstrings fuer den jeweiligen
Ehrlicher-Status-Hinweis) als JSON-API fuer die neue /ascension-Seite.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel

BASE = Path(__file__).parent

_ROOT = str(Path(__file__).resolve().parents[4])  # Dashboard -> ascension -> normal_os -> src -> repo root
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from ascension_os.core.ascension_core import get_ascension_core
except Exception:
    get_ascension_core = None

router = APIRouter()


@router.get("/ascension", response_class=HTMLResponse)
async def ascension_page():
    """AscensionOS-Statusseite (Stage9/Sisyphos/Psycholyse/QUBO/Harmonisierung/Geisterjagd)."""
    path = BASE / "templates" / "ascension.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>ascension.html not found</h1>", status_code=404)


def _core():
    if get_ascension_core is None:
        return None
    return get_ascension_core()


def _unavailable(what: str) -> Dict[str, Any]:
    return {"status": f"{what} nicht verfuegbar (siehe ascension_os/core/ascension_core.py)"}


# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------

@router.get("/api/ascension/status")
async def ascension_status():
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.get_ascension_status()


# ------------------------------------------------------------------
# Stage9
# ------------------------------------------------------------------

@router.get("/api/ascension/stage9")
async def ascension_stage9():
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.get_stage9_status()


# ------------------------------------------------------------------
# Sisyphos (Sparkline/SVG/Step)
# ------------------------------------------------------------------

class SisyphosStepPayload(BaseModel):
    load: float
    notes: str = ""


@router.get("/api/ascension/oscillation")
async def ascension_oscillation(last_n: int = 40):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.get_oscillation_report(last_n=last_n)


@router.get("/api/ascension/oscillation.svg")
async def ascension_oscillation_svg(last_n: int = 40):
    core = _core()
    if not core or not core.oscillation_visualizer:
        return Response(content="<svg xmlns='http://www.w3.org/2000/svg' width='480' height='40'>"
                                 "<text x='10' y='20'>SisyphosOscillationVisualizer nicht verfuegbar</text></svg>",
                         media_type="image/svg+xml")
    svg = core.oscillation_visualizer.render_svg(last_n=last_n)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/api/ascension/sisyphos/step")
async def ascension_sisyphos_step(payload: SisyphosStepPayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    result = core.step_sisyphos(payload.load, notes=payload.notes)
    return result or _unavailable("PersistentSisyphosCycle")


@router.get("/api/ascension/sisyphos/history")
async def ascension_sisyphos_history(last_n: int = 20):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return {"history": core.get_sisyphos_history(last_n=last_n)}


# ------------------------------------------------------------------
# Psycholyse
# ------------------------------------------------------------------

class PsycholyseSessionPayload(BaseModel):
    protocol_type: str
    status: str  # self_reported | observed | unverified
    pre_state: Optional[Dict[str, Any]] = None
    post_state: Optional[Dict[str, Any]] = None
    breakthrough_effects: Optional[List[str]] = None
    notes: str = ""


@router.post("/api/ascension/psycholyse/log")
async def ascension_psycholyse_log(payload: PsycholyseSessionPayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    try:
        entry = core.log_psycholyse_session(
            payload.protocol_type, payload.status,
            pre_state=payload.pre_state, post_state=payload.post_state,
            breakthrough_effects=payload.breakthrough_effects, notes=payload.notes,
        )
    except ValueError as e:
        return {"error": str(e)}
    return entry or _unavailable("PsycholyseProtocolLogger")


@router.get("/api/ascension/psycholyse/entries")
async def ascension_psycholyse_entries(last_n: int = 20):
    core = _core()
    if not core or not core.psycholyse_logger:
        return _unavailable("PsycholyseProtocolLogger")
    return {"entries": core.psycholyse_logger.get_entries(last_n=last_n),
            "coal_canary": core.psycholyse_logger.monitor_coal_canary()}


# ------------------------------------------------------------------
# QUBO Devil-vs-Christus
# ------------------------------------------------------------------

class QuboSolvePayload(BaseModel):
    n_checkpoints: int = 12
    steps: int = 4000


@router.post("/api/ascension/qubo/solve")
async def ascension_qubo_solve(payload: QuboSolvePayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.run_qubo_ascension_optimization(n_checkpoints=payload.n_checkpoints, steps=payload.steps)


# ------------------------------------------------------------------
# Harmonisierung + Geisterjagd (v9.6)
# ------------------------------------------------------------------

class HarmonizePayload(BaseModel):
    state_a: List[float]
    state_b: List[float]
    label_a: str = "A"
    label_b: str = "B"


@router.post("/api/ascension/harmonize")
async def ascension_harmonize(payload: HarmonizePayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.run_harmonization(payload.state_a, payload.state_b,
                                   participant_labels=(payload.label_a, payload.label_b))


class GeisterjagdPayload(BaseModel):
    latent_state: List[float]
    A: List[List[float]]
    c: List[float]


@router.post("/api/ascension/geisterjagd")
async def ascension_geisterjagd(payload: GeisterjagdPayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.run_geisterjagd(payload.latent_state, payload.A, payload.c)


# ------------------------------------------------------------------
# Sisyphos-Simulation (nicht-persistent)
# ------------------------------------------------------------------

class SimulatePayload(BaseModel):
    generations: int = 200
    n_runs: int = 8


@router.post("/api/ascension/simulate")
async def ascension_simulate(payload: SimulatePayload):
    core = _core()
    if not core:
        return _unavailable("AscensionCore")
    return core.run_sisyphos_simulation(generations=payload.generations, n_runs=payload.n_runs)
