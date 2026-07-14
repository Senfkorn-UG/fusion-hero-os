# -*- coding: utf-8 -*-
"""Businessplan + Subunternehmer API-Token-Preise (an Energie-Daemon gekoppelt)."""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["businessplan"])


@router.get("/api/businessplan")
async def api_businessplan():
    from core.mainframe_energy_pricing_daemon import load_businessplan
    return await asyncio.to_thread(load_businessplan)


@router.get("/api/businessplan/energy-model")
async def api_businessplan_energy_model():
    from core.mainframe_energy_pricing_daemon import get_energy_daemon, load_businessplan
    bp = await asyncio.to_thread(load_businessplan)
    status = await asyncio.to_thread(get_energy_daemon().status)
    return {
        "businessplan": bp,
        "energy_live": status.get("snapshot"),
        "subcontractor_pricing": status.get("subcontractor_pricing"),
    }


@router.get("/api/mainframe/energy/status")
async def api_energy_status():
    from core.mainframe_energy_pricing_daemon import get_energy_daemon
    return await asyncio.to_thread(get_energy_daemon().status)


@router.post("/api/mainframe/energy/tick")
async def api_energy_tick():
    from core.mainframe_energy_pricing_daemon import get_energy_daemon
    snap = await asyncio.to_thread(get_energy_daemon().tick)
    return snap.to_dict()


@router.get("/api/mainframe/energy/pricing/subcontractor")
async def api_subcontractor_pricing(
    tier: Optional[str] = Query(None, description="API-Tier-ID"),
    tokens: int = Query(1000, ge=1, le=10_000_000),
):
    from core.mainframe_energy_pricing_daemon import get_energy_daemon
    daemon = get_energy_daemon()
    if tier:
        return await asyncio.to_thread(daemon.subcontractor_quote, tier, tokens)
    status = await asyncio.to_thread(daemon.status)
    return {
        "subcontractor_pricing": status.get("subcontractor_pricing"),
        "snapshot": status.get("snapshot"),
        "quote_example_1k": await asyncio.to_thread(daemon.subcontractor_quote, "inference_standard", 1000),
    }