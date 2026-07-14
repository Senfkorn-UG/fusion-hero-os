# -*- coding: utf-8 -*-
"""Async background loops: cost analysis + repo mirror correction daemons."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

_running = False


async def cost_analysis_loop(interval_sec: float) -> None:
    from core.mainframe_cost_analysis_daemon import get_cost_daemon

    daemon = get_cost_daemon()
    daemon.start_background()
    while daemon._running:
        await asyncio.sleep(max(15.0, interval_sec))
        try:
            await asyncio.to_thread(daemon.tick)
        except Exception:
            pass


async def repo_mirror_loop(interval_sec: float) -> None:
    from core.repo_mirror_correction_daemon import get_mirror_daemon

    daemon = get_mirror_daemon()
    daemon.start_background()
    while daemon._running:
        await asyncio.sleep(max(10.0, interval_sec))
        try:
            await asyncio.to_thread(daemon.tick)
        except Exception:
            pass


async def energy_pricing_loop(interval_sec: float) -> None:
    from core.mainframe_energy_pricing_daemon import get_energy_daemon

    daemon = get_energy_daemon()
    daemon.start_background()
    while daemon._running:
        await asyncio.sleep(max(15.0, interval_sec))
        try:
            await asyncio.to_thread(daemon.tick)
        except Exception:
            pass


def start_mainframe_daemons() -> Dict[str, Any]:
    global _running
    if _running:
        return {"started": False, "reason": "already_running"}
    if os.getenv("FUSION_MAINFRAME_DAEMONS", "1") != "1":
        return {"started": False, "reason": "FUSION_MAINFRAME_DAEMONS=0"}

    cost_int = float(os.getenv("FUSION_COST_ANALYSIS_INTERVAL_SEC", "60"))
    mirror_int = float(os.getenv("FUSION_REPO_MIRROR_INTERVAL_SEC", "45"))
    energy_int = float(os.getenv("FUSION_ENERGY_PRICING_INTERVAL_SEC", "60"))

    asyncio.create_task(cost_analysis_loop(cost_int))
    asyncio.create_task(repo_mirror_loop(mirror_int))
    asyncio.create_task(energy_pricing_loop(energy_int))
    _running = True
    return {
        "started": True,
        "cost_interval_sec": cost_int,
        "mirror_interval_sec": mirror_int,
        "energy_interval_sec": energy_int,
        "mirror_auto_correct": os.getenv("FUSION_REPO_MIRROR_AUTO_CORRECT", "1") == "1",
    }