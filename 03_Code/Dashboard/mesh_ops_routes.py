# -*- coding: utf-8 -*-
"""Mesh Ops API — unified poly-mesh + Tailscale + entwicklungsquant surface (P1)."""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["mesh-ops"])


def _ts_exe() -> Optional[str]:
    candidates = [
        r"C:\Program Files\Tailscale\tailscale.exe",
        "tailscale",
    ]
    for c in candidates:
        if Path(c).is_file() or shutil.which(c):
            return c if Path(c).is_file() else shutil.which(c)
    return None


def _tailscale_status() -> Dict[str, Any]:
    exe = _ts_exe()
    if not exe:
        return {"ok": False, "error": "tailscale CLI not found"}
    try:
        raw = subprocess.check_output(
            [exe, "status", "--json"],
            timeout=12,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(raw.decode("utf-8", errors="replace"))
        self = data.get("Self") or {}
        peers = data.get("Peer") or {}
        online = sum(1 for p in peers.values() if p.get("Online"))
        return {
            "ok": True,
            "backend": data.get("BackendState"),
            "self": {
                "hostname": self.get("HostName"),
                "ips": self.get("TailscaleIPs"),
                "online": self.get("Online"),
                "dns": self.get("DNSName"),
            },
            "peer_count": len(peers),
            "peers_online": online,
            "magic_dns": (data.get("CurrentTailnet") or {}).get("MagicDNSSuffix"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _funnel_status() -> Dict[str, Any]:
    exe = _ts_exe()
    if not exe:
        return {"ok": False, "error": "tailscale CLI not found"}
    try:
        raw = subprocess.check_output(
            [exe, "funnel", "status", "--json"],
            timeout=10,
            stderr=subprocess.DEVNULL,
        )
        return {"ok": True, "config": json.loads(raw.decode("utf-8", errors="replace"))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:160]}


def _poly_mesh() -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": True}
    try:
        from fusion_hero_os.core.poly_mesh_router import probe_gke

        out["gke"] = probe_gke()
    except Exception as exc:  # noqa: BLE001
        out["gke"] = {"ok": False, "error": str(exc)[:160]}
    try:
        from fusion_hero_os.core import poly_mesh_os_port as port

        if hasattr(port, "status"):
            out["os_port"] = port.status()
        elif hasattr(port, "port_status"):
            out["os_port"] = port.port_status()
        else:
            out["os_port"] = {"ok": True, "module": "poly_mesh_os_port"}
    except Exception as exc:  # noqa: BLE001
        out["os_port"] = {"ok": False, "error": str(exc)[:160]}
    try:
        from fusion_hero_os.core.poly_mesh_cost_function import cost_function_status

        out["cost"] = cost_function_status()
    except Exception as exc:  # noqa: BLE001
        out["cost"] = {"ok": False, "error": str(exc)[:120]}
    return out


def _entwicklungsquant_status() -> Dict[str, Any]:
    import sys
    from pathlib import Path

    code = Path(__file__).resolve().parents[1] / "core"
    if str(code) not in sys.path:
        sys.path.insert(0, str(code.parent))
        sys.path.insert(0, str(code))
    try:
        from entwicklungsquant_bus import EntwicklungsquantBus  # type: ignore

        bus = EntwicklungsquantBus()
        if hasattr(bus, "status") and callable(bus.status):
            return {"ok": True, "bus": bus.status()}
        return {
            "ok": True,
            "available": True,
            "class": type(bus).__name__,
            "note": "Bus importable",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _registry_stubs_cleared() -> Dict[str, Any]:
    try:
        from fusion_hero_os.registry import Registry

        reg = Registry()
        names = [
            "modules.mainframe_laden",
            "modules.builder_profile",
            "modules.skill_creator",
        ]
        out = {}
        for n in names:
            spec = reg.load(n)
            out[n] = {
                "status": spec.status.value,
                "stub_flag": spec.stub,
                "error": spec.error,
            }
        return {"ok": True, "modules": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


@router.get("/api/mesh/ops")
async def mesh_ops_root() -> Dict[str, Any]:
    """Unified mesh ops snapshot (poly-mesh + tailscale + quant bus + P1 stubs)."""
    ts, funnel, poly, quant, stubs = await asyncio.gather(
        asyncio.to_thread(_tailscale_status),
        asyncio.to_thread(_funnel_status),
        asyncio.to_thread(_poly_mesh),
        asyncio.to_thread(_entwicklungsquant_status),
        asyncio.to_thread(_registry_stubs_cleared),
    )
    return {
        "ok": True,
        "platform_version": "10.0.0",
        "plane": "hyperraum",
        "tailscale": ts,
        "funnel": funnel,
        "poly_mesh": poly,
        "entwicklungsquant": quant,
        "p1_wiring": stubs,
        "endpoints": {
            "tailscale": "/api/mesh/ops/tailscale",
            "funnel": "/api/mesh/ops/funnel",
            "poly": "/api/mesh/ops/poly",
            "quant": "/api/mesh/ops/entwicklungsquant",
            "p1": "/api/mesh/ops/p1",
        },
    }


@router.get("/api/mesh/ops/tailscale")
async def mesh_ops_tailscale() -> Dict[str, Any]:
    return await asyncio.to_thread(_tailscale_status)


@router.get("/api/mesh/ops/funnel")
async def mesh_ops_funnel() -> Dict[str, Any]:
    return await asyncio.to_thread(_funnel_status)


@router.get("/api/mesh/ops/poly")
async def mesh_ops_poly() -> Dict[str, Any]:
    return await asyncio.to_thread(_poly_mesh)


@router.get("/api/mesh/ops/entwicklungsquant")
async def mesh_ops_quant() -> Dict[str, Any]:
    return await asyncio.to_thread(_entwicklungsquant_status)


@router.get("/api/mesh/ops/p1")
async def mesh_ops_p1() -> Dict[str, Any]:
    return await asyncio.to_thread(_registry_stubs_cleared)


@router.post("/api/mesh/ops/mainframe-laden")
async def mesh_ops_mainframe_laden(
    include_code_registry: bool = Query(True),
) -> Dict[str, Any]:
    def _run():
        from fusion_hero_os.modules.mainframe_laden import load_all

        return load_all(include_code_registry=include_code_registry)

    return await asyncio.to_thread(_run)
