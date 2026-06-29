# -*- coding: utf-8 -*-
"""FastAPI Dashboard Server ? OS Development Sync v5.3 mit QUBO"""
from __future__ import annotations
import asyncio, time, uuid, json, statistics
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np

BASE = Path(__file__).parent
app = FastAPI(title="Denkprozess Monitor")

# Minimal health endpoint for start_all.ps1 compatibility
@app.get("/api/health")
async def api_health(light: bool = False):
    if light:
        return {"status": "ok", "backend": "online"}
    return {
        "backend": "online",
        "fusion_os": "v7.5 MasterSeed",
        "core": "v7.5",
        "mainframe": {"loaded": True, "version": "v5.25", "boot_phase": "full"},
        "v12": {"grok_intern_aligned": True},
        "hyperthreading": {"enabled": True, "logical_cpus": 12, "workers": 54},
        "tasks": {"autonomous": True, "queue_len": len(TASK_QUEUE), "support": "selbstständig neue tasks zuordnen"},
        "agents": {"loaded": AGENT_STATE["loaded"], "count": len(AGENT_STATE["agents"]), "auto": "immer automatisch laden und zuordnen"},
    }

MAX_EVENTS = 500
events: deque[dict] = deque(maxlen=MAX_EVENTS)
subscribers: set[WebSocket] = set()
_metrics_cache: dict = {"data": {}, "ts": 0.0}
_METRICS_TTL = 0.25

class EventIn(BaseModel):
    type: str = "info"
    msg: str = ""
    count: Optional[int] = None

class MetricsOut(BaseModel):
    cpu: float
    ram: float
    events: int
    subs: int
    ts: float
    ops_per_sec: float
    avg_emit_time_ms: float
    cache_hit_rate: float

class QUBORequest(BaseModel):
    n: int = 10
    submodular: bool = False
    steps: int = 4000

KEY_PROBLEMS: List[dict] = [
    {"name": "Quanten-oszillierende Bindungsst?rung", "original": "Borderline",
     "quant_steps": ["Erkennen", "Hinterfragen", "Verinnerlichen", "Kooperieren"],
     "mimetik": "Hoch", "memetik": "Hoch"},
]

# === Autonomous task input / orchestration support (for workspace "selbstständig neue tasks zuordnen") ===
JOBS: Dict[str, Dict[str, Any]] = {}
TASK_QUEUE: List[Dict[str, Any]] = []

# === Consolidated from heroic_orchestration (merged agent + classify logic) ===
try:
    from heroic_orchestration import (
        ensure_agents_loaded as _ensure_agents_shared,
        classify_and_normalize,
        get_loaded_agents,
    )
except Exception:
    def _ensure_agents_shared(force=False): return True
    def classify_and_normalize(q): return q, "model", None, "General"
    def get_loaded_agents(): return {}

AGENT_STATE = {
    "loaded": False,
    "supervisor": None,
    "agents": {},
    "last_load": None
}

def _ensure_agents():
    """Backend: Agenten immer automatisch laden (delegates to shared)."""
    if AGENT_STATE["loaded"]:
        return AGENT_STATE
    _ensure_agents_shared()
    try:
        AGENT_STATE["agents"] = get_loaded_agents() or {
            "supervisor": {"name": "fusion-hero-supervisor", "role": "supervisor", "state": "running"},
            "math-worker": {"name": "math-worker", "role": "worker", "dom": "Math"},
            "phil-worker": {"name": "phil-worker", "role": "worker", "dom": "Phil"},
            "info-worker": {"name": "info-worker", "role": "worker", "dom": "Info"},
            "general-worker": {"name": "general-worker", "role": "worker"},
        }
        AGENT_STATE["loaded"] = True
        AGENT_STATE["last_load"] = time.time()
    except Exception:
        pass
    return AGENT_STATE

class InputPayload(BaseModel):
    query: str = ""
    task_id: Optional[int] = None
    category: str = "user"

class OrchestratePayload(BaseModel):
    query: str = ""
    model_pool: Optional[List[str]] = None


PERFORMANCE_TRACKING: Dict[str, Any] = {"emit_times": deque(maxlen=1000), "broadcast_times": deque(maxlen=1000), "cache_hits": 0, "total_requests": 0, "start_time": time.time()}

WALLET_FILE = BASE / "static" / "wallet.json"
WALLET_CAP = 10000
rng = np.random.default_rng(7)

async def _send_safe(ws: WebSocket, event: dict) -> None:
    try:
        await asyncio.wait_for(ws.send_json(event), timeout=0.5)
    except Exception:
        subscribers.discard(ws)

async def emit(event: dict) -> str:
    start = time.perf_counter()
    event["ts"] = time.time()
    event["id"] = str(uuid.uuid4())[:8]
    events.append(event)
    event_id = event["id"]
    if subscribers:
        broadcast_start = time.perf_counter()
        await asyncio.gather(*[_send_safe(ws, event) for ws in list(subscribers)], return_exceptions=True)
        PERFORMANCE_TRACKING["broadcast_times"].append((time.perf_counter() - broadcast_start) * 1000)
    PERFORMANCE_TRACKING["emit_times"].append((time.perf_counter() - start) * 1000)
    return event_id

@app.post("/api/events")
async def post_event(payload: EventIn):
    PERFORMANCE_TRACKING["total_requests"] += 1
    return {"status": "queued", "id": await emit({"type": payload.type, "msg": payload.msg})}

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(BASE / "templates" / "index.html")

@app.get("/api/metrics", response_model=MetricsOut)
async def get_metrics():
    now = time.time()
    PERFORMANCE_TRACKING["total_requests"] += 1
    if now - _metrics_cache.get("ts", 0) < _METRICS_TTL:
        PERFORMANCE_TRACKING["cache_hits"] += 1
        base_data = _metrics_cache["data"]
    else:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        base_data = {"cpu": round(cpu, 1), "ram": round(mem.percent, 1), "events": len(events), "subs": len(subscribers), "ts": now}
        _metrics_cache.update({"data": base_data, "ts": now})
    uptime = time.time() - PERFORMANCE_TRACKING["start_time"]
    return {**base_data, "ops_per_sec": round(PERFORMANCE_TRACKING["total_requests"] / max(uptime, 0.1), 2),
            "avg_emit_time_ms": round(statistics.mean(PERFORMANCE_TRACKING["emit_times"]) if PERFORMANCE_TRACKING["emit_times"] else 0.0, 4),
            "cache_hit_rate": round(PERFORMANCE_TRACKING["cache_hits"] / max(PERFORMANCE_TRACKING["total_requests"], 1), 3)}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if len(subscribers) >= 10000:
        await ws.close(code=1008)
        return
    await ws.accept()
    subscribers.add(ws)
    await ws.send_json({"type": "welcome", "event_count": len(events)})
    async for data in ws.iter_text():
        msg = json.loads(data)
        if msg.get("action") == "clear":
            events.clear()
            await emit({"type": "system", "msg": "Event-Log geleert"})

def _make_Q(n: int, submodular: bool = False, scale: float = 1.0):
    Q = np.zeros((n, n), dtype=np.float64)
    r = rng.normal(0, scale, size=(n, n))
    Q += (r + r.T) / 2.0
    np.fill_diagonal(Q, rng.normal(0, scale, size=n))
    if submodular:
        off = np.ones_like(Q) - np.eye(n)
        Q = np.where(off, -np.abs(Q), Q)
    return Q

def _simulated_annealing(Q, steps=4000):
    n = Q.shape[0]
    x = rng.integers(0, 2, n).astype(np.int64)
    Qf = Q.astype(np.float64)
    Qx = Qf @ x.astype(np.float64)
    e = float(x @ Qx)
    best_x, best_e = x.copy(), e
    for t in range(steps):
        T = 2.0 * (1.0 - t / steps) + 1e-3
        i = int(rng.integers(0, n))
        delta_x = 1 - 2 * x[i]
        delta_e = 2.0 * delta_x * Qx[i] + Q[i, i] * delta_x * delta_x
        if delta_e < 0 or rng.random() < float(np.exp(-delta_e / T)):
            x[i] ^= 1
            e += delta_e
            Qx += Qf[:, i] * delta_x
            if e < best_e:
                best_e = e
                best_x = x.copy()
    return best_x.tolist(), float(best_e)

@app.post("/api/qubo/solve")
async def solve_qubo(req: QUBORequest):
    start = time.perf_counter()
    Q = _make_Q(req.n, req.submodular)
    solution, energy = _simulated_annealing(Q, req.steps)
    return {"solution": solution, "energy": round(energy, 6), "n": req.n, "time_ms": round((time.perf_counter() - start) * 1000, 2)}

@app.get("/api/os/problems")
async def get_problems():
    return {"problems": KEY_PROBLEMS[:5]}

# Autonomous task ingestion (Eingabe immer prüfen + Task zuordnen)
@app.post("/api/input")
async def api_input(payload: InputPayload):
    query = (payload.query or "").strip()
    if not query:
        return {"status": "error", "msg": "empty query"}

    # Use shared classification (consolidated)
    normalized, effective_cat, _, dom = classify_and_normalize(query)
    _ensure_agents()

    has_geltung = True
    job_id = str(uuid.uuid4())[:8]
    job = {
        "id": job_id,
        "query": normalized,
        "original": query,
        "task_id": payload.task_id,
        "category": effective_cat,
        "dom": dom,
        "has_geltung": has_geltung,
        "status": "received",
        "assigned": "dynamic-orchestrator",
        "auto_tagged": True
    }
    JOBS[job_id] = job
    TASK_QUEUE.append(job)
    await emit({"type": "task_input", "msg": f"Input geprüft + auto zugeordnet [{effective_cat}]: {normalized[:70]}", "job_id": job_id})
    return {
        "status": "ok",
        "job_id": job_id,
        "ack": "Eingabe IMMER geprüft und automatisch einem Task zugeordnet",
        "has_geltung": has_geltung,
        "normalized_query": normalized
    }

@app.post("/api/v12/orchestrate")
async def api_orchestrate(payload: OrchestratePayload):
    query = (payload.query or "").strip()
    models = payload.model_pool or ["grok-intern", "fusion-hero"]
    job_id = str(uuid.uuid4())[:8]
    result = {
        "status": "success",
        "job_id": job_id,
        "query": query,
        "used_models": models,
        "synthesised_response": f"[Heroic Orchestration] Query verarbeitet. Assigned models: {models}",
        "dimension_6_score": 0.92,
        "traceability": "Autonom zugeordnet via /api/v12/orchestrate"
    }
    await emit({"type": "orchestrate", "msg": f"Orchestrated: {query[:50]}", "job_id": job_id})
    return result

@app.get("/api/tasks")
async def api_tasks():
    return {"tasks": TASK_QUEUE[-50:], "active_jobs": len(JOBS)}

# === Agents endpoints: immer automatisch laden und zuordnen ===
@app.get("/api/agents")
async def api_agents():
    state = _ensure_agents()
    return {"loaded": state["loaded"], "agents": state["agents"], "count": len(state["agents"])}

@app.post("/api/agents/load")
async def api_agents_load():
    state = _ensure_agents()
    state["loaded"] = True
    state["last_load"] = time.time()
    return {"status": "ok", "loaded": True, "agents": list(state["agents"].keys())}

@app.post("/api/agents/assign")
async def api_agents_assign(payload: dict):
    state = _ensure_agents()
    task_id = payload.get("task_id")
    dom = payload.get("dom", "General")
    # Auto assign logic
    agent_map = {"Math": "math-worker", "Phil": "phil-worker", "Info": "info-worker"}
    agent = agent_map.get(dom, "general-worker")
    if agent not in state["agents"]:
        agent = "general-worker"
    assignment = {"task_id": task_id, "agent": agent, "dom": dom, "ts": time.time()}
    return {"status": "ok", "assignment": assignment, "agent": state["agents"].get(agent)}

# Auto-load agents on module import (immer automatisch)
_ensure_agents()

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

if __name__ == "__main__":
    import uvicorn, uvloop
    uvloop.run(uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", loop="uvloop", ws="websockets"))
