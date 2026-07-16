# -*- coding: utf-8 -*-
"""API Plane routes — Hyperraum vs Business entrypoints (additive).

Canonical:
  GET  /api/planes
  GET  /api/planes/classify?path=...
  GET  /api/v1/business
  GET  /api/v1/business/health
  GET  /api/v1/business/pricing
  GET  /api/v1/business/businessplan
  GET  /api/hyperraum
  GET  /api/hyperraum/status
  GET  /api/hyperraum/operator
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["api-planes"])


def _planes():
    from fusion_hero_os.core.api_plane import (
        classify_path,
        planes_status,
        assert_plane_safe_payload,
        PLANE_BUSINESS,
        PLANE_HYPERRAUM,
    )

    return classify_path, planes_status, assert_plane_safe_payload, PLANE_BUSINESS, PLANE_HYPERRAUM


@router.get("/api/planes")
async def api_planes_status() -> Dict[str, Any]:
    _, planes_status, *_ = _planes()
    return await asyncio.to_thread(planes_status)


@router.get("/api/planes/classify")
async def api_planes_classify(
    path: str = Query(..., description="HTTP path to classify, e.g. /api/health"),
) -> Dict[str, Any]:
    classify_path, *_ = _planes()
    return await asyncio.to_thread(classify_path, path)


# ---------------------------------------------------------------------------
# Business plane (classical product API)
# ---------------------------------------------------------------------------


@router.get("/api/v1/business")
async def business_root() -> Dict[str, Any]:
    return {
        "plane": "business",
        "label": "Klassische Business-API",
        "privacy": "product",
        "version": "v1",
        "endpoints": {
            "health": "/api/v1/business/health",
            "pricing": "/api/v1/business/pricing",
            "businessplan": "/api/v1/business/businessplan",
            "energy": "/api/v1/business/energy",
        },
        "legacy_aliases": {
            "businessplan": "/api/businessplan",
            "health": "/api/health?light=true",
            "pricing": "/api/mainframe/energy/pricing/subcontractor",
        },
        "note": "No Hyperraum control plane; no operator vault; no consent bodies.",
    }


@router.get("/api/v1/business/health")
async def business_health() -> Dict[str, Any]:
    """Product health — light, no module dump."""
    body = {
        "plane": "business",
        "ok": True,
        "status": "up",
        "service": "fusion-hero-os-business-api",
        "platform_version": "10.0.0",
    }
    _, _, assert_safe, PLANE_BUSINESS, _ = _planes()
    ok, issues = assert_safe(PLANE_BUSINESS, body)
    body["plane_guard"] = {"ok": ok, "issues": issues}
    return body


@router.get("/api/v1/business/businessplan")
async def business_businessplan() -> Dict[str, Any]:
    try:
        from core.mainframe_energy_pricing_daemon import load_businessplan

        bp = await asyncio.to_thread(load_businessplan)
    except Exception as exc:  # noqa: BLE001
        return {"plane": "business", "ok": False, "error": str(exc)[:200]}
    body = {"plane": "business", "ok": True, "businessplan": bp}
    _, _, assert_safe, PLANE_BUSINESS, _ = _planes()
    ok, issues = assert_safe(PLANE_BUSINESS, body)
    body["plane_guard"] = {"ok": ok, "issues": issues}
    return body


@router.get("/api/v1/business/pricing")
async def business_pricing(
    tier: Optional[str] = Query(None),
    tokens: int = Query(1000, ge=1, le=10_000_000),
) -> Dict[str, Any]:
    try:
        from core.mainframe_energy_pricing_daemon import get_energy_daemon

        daemon = get_energy_daemon()
        if tier:
            quote = await asyncio.to_thread(daemon.subcontractor_quote, tier, tokens)
            body = {"plane": "business", "ok": True, "tier": tier, "tokens": tokens, "quote": quote}
        else:
            status = await asyncio.to_thread(daemon.status)
            body = {
                "plane": "business",
                "ok": True,
                "subcontractor_pricing": status.get("subcontractor_pricing"),
                "snapshot": {
                    # only product-safe energy summary if present
                    k: status.get("snapshot", {}).get(k)
                    for k in ("ts", "eur_per_hour", "feu_per_hour", "source")
                    if isinstance(status.get("snapshot"), dict)
                }
                if isinstance(status.get("snapshot"), dict)
                else status.get("snapshot"),
                "quote_example_1k": await asyncio.to_thread(
                    daemon.subcontractor_quote, "inference_standard", 1000
                ),
            }
    except Exception as exc:  # noqa: BLE001
        return {"plane": "business", "ok": False, "error": str(exc)[:200]}
    _, _, assert_safe, PLANE_BUSINESS, _ = _planes()
    ok, issues = assert_safe(PLANE_BUSINESS, body)
    body["plane_guard"] = {"ok": ok, "issues": issues}
    return body


@router.get("/api/v1/business/energy")
async def business_energy() -> Dict[str, Any]:
    try:
        from core.mainframe_energy_pricing_daemon import get_energy_daemon

        status = await asyncio.to_thread(get_energy_daemon().status)
        snap = status.get("snapshot") if isinstance(status, dict) else None
        body = {
            "plane": "business",
            "ok": True,
            "energy": snap,
            "subcontractor_pricing_available": bool(
                isinstance(status, dict) and status.get("subcontractor_pricing")
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"plane": "business", "ok": False, "error": str(exc)[:200]}
    return body


# ---------------------------------------------------------------------------
# Hyperraum plane (half-private operator hyperspace)
# ---------------------------------------------------------------------------


@router.get("/api/hyperraum")
async def hyperraum_root() -> Dict[str, Any]:
    return {
        "plane": "hyperraum",
        "label": "Halbprivater Hyperraum",
        "privacy": "half_private",
        "audience": "operator",
        "endpoints": {
            "status": "/api/hyperraum/status",
            "operator": "/api/hyperraum/operator",
            "classify": "/api/planes/classify?path=/api/grok/interconnect",
        },
        "related_legacy": {
            "interconnect": "/api/grok/interconnect",
            "mainframe": "/api/mainframe/site/status",
            "autoload": "/api/autoload/status",
            "control": "/mainframe/grok",
        },
        "note": (
            "Operator hyperspace. Not a public product API. "
            "Person (legal name) is extracted from role — see operator_identity."
        ),
    }


@router.get("/api/hyperraum/status")
async def hyperraum_status() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "plane": "hyperraum",
        "privacy": "half_private",
        "platform_version": "10.0.0",
        "ok": True,
        "organs": {},
    }
    # operator membrane
    try:
        from fusion_hero_os.core.operator_identity import public_operator_view, extract_status

        out["organs"]["operator_identity"] = {
            "public": public_operator_view(),
            "extract": {
                k: extract_status().get(k)
                for k in (
                    "membrane",
                    "person_bound_in_vault",
                    "author_bind_active",
                    "vault_exists",
                )
            },
        }
    except Exception as exc:  # noqa: BLE001
        out["organs"]["operator_identity"] = {"ok": False, "error": str(exc)[:160]}

    # plane catalog self-ref
    try:
        from fusion_hero_os.core.api_plane import classify_path

        out["organs"]["self_class"] = classify_path("/api/hyperraum/status")
    except Exception as exc:  # noqa: BLE001
        out["organs"]["self_class"] = {"error": str(exc)[:120]}

    # light mesh hint without dumping peer PII
    try:
        from fusion_hero_os.core.poly_mesh_router import probe_gke

        gke = probe_gke()
        out["organs"]["gke"] = {
            "ok": bool(gke.get("ok")),
            "ready_nodes": gke.get("ready_nodes"),
            "error": gke.get("error"),
        }
    except Exception as exc:  # noqa: BLE001
        out["organs"]["gke"] = {"ok": False, "error": str(exc)[:120]}

    return out


@router.get("/api/hyperraum/operator")
async def hyperraum_operator() -> Dict[str, Any]:
    """Public-safe operator role view (never legal name)."""
    try:
        from fusion_hero_os.core.operator_identity import (
            public_operator_view,
            extract_status,
        )

        return {
            "plane": "hyperraum",
            "ok": True,
            "operator": public_operator_view(),
            "membrane": extract_status().get("membrane"),
            "rule": extract_status().get("rule"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"plane": "hyperraum", "ok": False, "error": str(exc)[:200]}
