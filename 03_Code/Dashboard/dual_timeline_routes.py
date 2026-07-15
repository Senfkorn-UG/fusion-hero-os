# -*- coding: utf-8 -*-
"""Dual-timeline auto-training API (real t ∥ imaginary τ)."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Query

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

router = APIRouter(tags=["dual-timeline-training"])


@router.get("/api/training/dual-timeline/status")
async def dt_status():
    from fusion_hero_os.core.dual_timeline_training import status

    return status()


@router.post("/api/training/dual-timeline/run")
async def dt_run(dry: bool = Query(False)):
    import asyncio

    from fusion_hero_os.core.dual_timeline_training import run_auto_train

    return await asyncio.to_thread(run_auto_train, write=not dry)


@router.get("/api/training/dual-timeline/catalog")
async def dt_catalog():
    from fusion_hero_os.core.dual_timeline_training import load_config

    return {"ok": True, "config": load_config()}
