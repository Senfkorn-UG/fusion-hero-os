# -*- coding: utf-8 -*-
"""Hintergrund-Sync: Auto-Metriken + Phone-Link-Snapshots → Supabase."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable, Dict, Optional

_running = False


def _sync_enabled() -> bool:
    return os.getenv("FUSION_SUPABASE_SYNC", "1") == "1"


async def metrics_loop(get_metrics: Callable[[], Awaitable[Any]], interval_sec: float) -> None:
    import supabase_store as store

    while True:
        await asyncio.sleep(max(5.0, interval_sec))
        if not _sync_enabled():
            continue
        try:
            metrics = await get_metrics()
            if hasattr(metrics, "model_dump"):
                payload = metrics.model_dump()
            elif isinstance(metrics, dict):
                payload = metrics
            else:
                payload = dict(metrics)
            await asyncio.to_thread(store.save_metrics, payload)
        except Exception:
            pass


async def phone_link_snapshot_loop(interval_sec: float) -> None:
    import supabase_store as store

    while True:
        await asyncio.sleep(max(30.0, interval_sec))
        if not _sync_enabled() or not store.cloud_sync_enabled():
            continue
        try:
            from fusion_hero_os.integrations.phone_link import phone_link_status

            snap = await asyncio.to_thread(phone_link_status)
            if isinstance(snap, dict):
                await asyncio.to_thread(store.save_phone_link_snapshot, snap)
        except Exception:
            pass


def start_background_tasks(
    get_metrics: Callable[[], Awaitable[Any]],
    *,
    metrics_interval: Optional[float] = None,
    phone_link_interval: Optional[float] = None,
) -> Dict[str, Any]:
    global _running
    if _running:
        return {"started": False, "reason": "already_running"}
    if not _sync_enabled():
        return {"started": False, "reason": "FUSION_SUPABASE_SYNC=0"}

    m_int = metrics_interval or float(os.getenv("FUSION_SUPABASE_METRICS_INTERVAL_SEC", "30"))
    p_int = phone_link_interval or float(os.getenv("FUSION_PHONE_LINK_SNAPSHOT_INTERVAL_SEC", "300"))

    asyncio.create_task(metrics_loop(get_metrics, m_int))
    asyncio.create_task(phone_link_snapshot_loop(p_int))
    _running = True
    return {"started": True, "metrics_interval_sec": m_int, "phone_link_interval_sec": p_int}