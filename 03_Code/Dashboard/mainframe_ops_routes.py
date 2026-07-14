# -*- coding: utf-8 -*-
"""Mainframe Ops — Kostenanalyse + Repo-Spiegelung (graphisch + API)."""
from __future__ import annotations

import asyncio
import html
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["mainframe-ops"])
_BASE = Path(__file__).parent


@router.get("/api/mainframe/cost/status")
async def api_cost_status():
    from core.mainframe_cost_analysis_daemon import get_cost_daemon
    return await asyncio.to_thread(get_cost_daemon().status)


@router.post("/api/mainframe/cost/tick")
async def api_cost_tick():
    from core.mainframe_cost_analysis_daemon import get_cost_daemon
    snap = await asyncio.to_thread(get_cost_daemon().tick)
    return snap.to_dict()


@router.get("/api/mainframe/repo/status")
async def api_repo_status():
    from core.repo_mirror_correction_daemon import get_mirror_daemon
    from core.repo_structure_registry import echarts_sunburst_data, scan_structure

    status = await asyncio.to_thread(get_mirror_daemon().status)
    scan = await asyncio.to_thread(scan_structure)
    status["sunburst"] = await asyncio.to_thread(echarts_sunburst_data, scan)
    status["structure"] = scan
    return status


@router.post("/api/mainframe/repo/tick")
async def api_repo_tick():
    from core.repo_mirror_correction_daemon import get_mirror_daemon
    return await asyncio.to_thread(get_mirror_daemon().tick)


@router.get("/api/mainframe/ops/summary")
async def api_ops_summary():
    from core.mainframe_cost_analysis_daemon import get_cost_daemon
    from core.repo_mirror_correction_daemon import get_mirror_daemon

    cost = await asyncio.to_thread(get_cost_daemon().status)
    repo = await asyncio.to_thread(get_mirror_daemon().status)
    return {
        "cost": cost,
        "repo_mirror": repo,
        "mode": "mirror_and_os_daemon_correction",
        "ui": "read_only_display",
    }


@router.get("/mainframe/ops", response_class=HTMLResponse)
async def mainframe_ops_page():
    tpl = _BASE / "templates" / "mainframe_ops.html"
    if tpl.exists():
        return HTMLResponse(tpl.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>mainframe_ops.html missing</h1>", status_code=500)