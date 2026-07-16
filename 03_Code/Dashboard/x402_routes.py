# -*- coding: utf-8 -*-
"""API: x402 full security stack status + run."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "03_Code")):
    if p not in sys.path:
        sys.path.insert(0, p)

router = APIRouter(tags=["x402-security"])


class X402RunIn(BaseModel):
    budget_eur: float = Field(default=500.0, ge=0)
    broadcast_onchain: bool = False


@router.get("/api/x402/status")
async def x402_status():
    from fusion_hero_os.core.x402_hackability_audit import status as threat_status
    from fusion_hero_os.core.x402_sandbox_audit import status as sandbox_status

    master = Path.home() / ".fusion" / "x402" / "x402_stack_master.json"
    master_data = None
    if master.is_file():
        import json

        try:
            master_data = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            master_data = None
    return {
        "ok": True,
        "threat": threat_status(),
        "sandbox": sandbox_status(),
        "master": master_data,
        "github": "https://github.com/95guknow/fusion-hero-os",
        "instagram": "https://www.instagram.com/95guknow/",
        "docs": "docs/security/X402_STACK.md",
    }


@router.post("/api/x402/run")
async def x402_run(body: X402RunIn):
    import asyncio
    import subprocess

    def _run():
        cmd = [sys.executable, str(_ROOT / "scripts" / "run_x402_stack.py"), "--json-only"]
        if body.broadcast_onchain:
            cmd.append("--broadcast-onchain")
        r = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True, timeout=180)
        import json

        try:
            return json.loads(r.stdout)
        except Exception:
            return {
                "ok": r.returncode == 0,
                "stdout": (r.stdout or "")[:4000],
                "stderr": (r.stderr or "")[:1000],
                "returncode": r.returncode,
            }

    return await asyncio.to_thread(_run)
