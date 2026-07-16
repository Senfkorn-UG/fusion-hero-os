# -*- coding: utf-8 -*-
"""API: multi-model control instances with forced max accuracy."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "03_Code")):
    if p not in sys.path:
        sys.path.insert(0, p)

router = APIRouter(tags=["control-instances"])


class ControlIn(BaseModel):
    prompt: str = Field(..., min_length=1)
    providers: Optional[List[str]] = None


@router.get("/api/control/instances/status")
async def control_status():
    from fusion_hero_os.core.control_instances import status

    return status()


@router.post("/api/control/instances/run")
async def control_run(body: ControlIn):
    import asyncio

    from fusion_hero_os.core.control_instances import run_control_panel

    report = await asyncio.to_thread(
        run_control_panel, body.prompt, providers=body.providers
    )
    return report.to_dict()
