# api_extensions.py — fehlende Endpunkte freigeben (alle Module)

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ProfilePayload(BaseModel):
    name: str = "admin"


class GatePayload(BaseModel):
    text: str = ""


class ChatPayload(BaseModel):
    message: str = ""


class ValidatePayload(BaseModel):
    text: str = ""


def _orch():
    from core.dynamic_orchestration_core import DynamicOrchestrationCoreModule
    return DynamicOrchestrationCoreModule()


@router.post("/api/load-all")
async def api_load_all(force: bool = False):
    from core.module_registry import load_all
    return await asyncio.to_thread(load_all, force)


@router.get("/api/modules")
async def api_modules():
    from core.module_registry import list_modules
    return {"modules": list_modules(), "all_enabled": os.getenv("FUSION_ALL_MODULES", "1") == "1"}


@router.post("/api/agents/{agent_id}/use")
async def api_agent_use(agent_id: str, payload: dict = None):
    from core.heroic_orchestration import assign_task_to_agent
    task = {"dom": "General", "id": agent_id, **(payload or {})}
    agent = assign_task_to_agent(task)
    return {"status": "ok", "agent_id": agent_id, "assigned": agent}


@router.post("/api/mainframe/load")
async def api_mainframe_load():
    from core.module_registry import load_all
    result = await asyncio.to_thread(load_all, True)
    return {"status": "loaded", "version": "v7.4/v7.5", "boot_phase": "full", **result}


@router.get("/api/layer4/status")
async def api_layer4_status():
    try:
        import sys
        from pathlib import Path
        p = Path(r"C:\Users\Admin\heroic-highest-layer")
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        from highest_layer import load  # type: ignore
        return load().status()
    except Exception as exc:
        return {"status": "fallback", "error": str(exc)}


@router.post("/api/foundation/gate")
async def api_foundation_gate(payload: GatePayload):
    try:
        import sys
        from pathlib import Path
        p = Path(r"C:\Users\Admin\heroic-core-foundation")
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        from foundation import check_foundation_gate  # type: ignore
        return check_foundation_gate({"text": payload.text})
    except Exception as exc:
        return {"passed": False, "error": str(exc)}


@router.post("/api/v12/sync")
async def api_v12_sync():
    try:
        from core.google_multi_account_sync_core import GoogleMultiAccountSyncCoreModule
        mod = GoogleMultiAccountSyncCoreModule()
        if hasattr(mod, "sync_all"):
            return mod.sync_all()
        return {"status": "ok", "note": "sync module loaded", "module": type(mod).__name__}
    except Exception as exc:
        return {"status": "fallback", "error": str(exc)}


@router.post("/api/mod/validate")
async def api_mod_validate(payload: ValidatePayload):
    from core.CriticalMetaAnalysisCoreModule import CriticalMetaAnalysisCoreModule
    from core.SelfModifyCoreModule import SelfModifyCoreModule
    issues = CriticalMetaAnalysisCoreModule().analyze(payload.text)
    proposal = None
    if issues:
        proposal = SelfModifyCoreModule().propose_modification(
            description="PeerReview finding", diff="", risk_level="low",
        )
    return {
        "status": "ok",
        "issues": issues,
        "peer_review_passed": len(issues) == 0,
        "proposal": proposal,
        "dimensions": 5,
    }


@router.get("/api/grok/status")
async def api_grok_status():
    from core.local_llama import get_local_llama, default_model_pool
    llama = get_local_llama().status()
    return {
        "bridge": "grok-intern",
        "skill": "fusion-hero-os",
        "llama_local": llama,
        "default_model_pool": default_model_pool(),
        "endpoints": ["/api/grok/chat", "/api/v12/orchestrate", "/api/input"],
    }


@router.post("/api/grok/chat")
async def api_grok_chat(payload: ChatPayload):
    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    from core.heroic_orchestration import classify_and_normalize
    from core.local_llama import get_local_llama, default_model_pool
    normalized, cat, _, dom = classify_and_normalize(msg)
    llama = get_local_llama()
    response = ""
    backend = "grok-intern"
    if llama.active or os.getenv("FUSION_LLM_BACKEND") == "llama-local":
        try:
            response = await asyncio.to_thread(llama.generate, normalized)
            backend = "llama-local"
        except Exception as exc:
            response = f"[Llama error: {exc}] Fallback zu Fusion Hero."
    if not response:
        result = await asyncio.to_thread(_orch().orchestrate, normalized, default_model_pool())
        response = result.get("synthesised_response", "")
        backend = result.get("backend", "fusion-hero")
    return {
        "status": "ok",
        "query": normalized,
        "response": response,
        "backend": backend,
        "category": cat,
        "dom": dom,
        "model_pool": default_model_pool(),
    }


@router.get("/api/meta-layer/status")
async def api_meta_layer_status():
    from core.windows_substrate import get_substrate
    return get_substrate().status()


@router.get("/api/meta-layer/windows")
async def api_meta_layer_windows():
    from core.windows_substrate import get_substrate
    return get_substrate().scan()


@router.post("/api/meta-layer/attach")
async def api_meta_layer_attach():
    from core.windows_substrate import get_substrate
    return get_substrate().attach()


@router.post("/api/windows/substrate/tune")
async def api_windows_substrate_tune():
    from core.windows_substrate import get_substrate
    return get_substrate().tune_substrate()


@router.post("/api/windows/cyber-layer/activate")
async def api_windows_cyber_activate():
    from core.windows_substrate import get_substrate
    return get_substrate().activate_cyber_layer()


@router.get("/api/profile/status")
async def api_profile_status():
    return {
        "name": os.getenv("FUSION_PROFILE", "admin"),
        "performance_ratio": float(os.getenv("FUSION_PERFORMANCE_RATIO", "1.0")),
        "hyperthreading": os.getenv("FUSION_HYPERTHREADING", "1") == "1",
        "all_modules": os.getenv("FUSION_ALL_MODULES", "1") == "1",
    }


@router.post("/api/profile/set")
async def api_profile_set(payload: ProfilePayload):
    name = payload.name.lower()
    os.environ["FUSION_PROFILE"] = name
    ratio = {"admin": 1.0, "balanced": 0.67, "eco": 0.5}.get(name, 0.67)
    os.environ["FUSION_PERFORMANCE_RATIO"] = str(ratio)
    return {"status": "ok", "profile": name, "performance_ratio": ratio}


@router.get("/api/resources/plan")
async def api_resources_plan():
    from core.module_registry import resource_plan
    return resource_plan()


@router.get("/api/signal/health")
async def api_signal_health(layer: str = "full"):
    from core.module_registry import signal_health
    return signal_health(layer)


@router.get("/api/jobs/{job_id}")
async def api_job_get(job_id: str):
    from app import JOBS, TASK_QUEUE
    job = JOBS.get(job_id)
    if job:
        return {"status": "ok", "job": job}
    for t in TASK_QUEUE:
        if t.get("id") == job_id:
            return {"status": "ok", "job": t}
    return {"status": "not_found", "job_id": job_id}


@router.get("/api/llama/status")
async def api_llama_status():
    from local_llama import get_local_llama
    return get_local_llama().status()


@router.post("/api/llama/chat")
async def api_llama_chat(payload: ChatPayload):
    from local_llama import get_local_llama
    llama = get_local_llama()
    msg = (payload.message or "").strip()
    if not msg:
        return {"status": "error", "error": "empty message"}
    response = await asyncio.to_thread(llama.generate, msg)
    return {"status": "ok", "response": response, "backend": "llama-local"}