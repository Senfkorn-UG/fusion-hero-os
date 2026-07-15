# -*- coding: utf-8 -*-
"""Grok Interconnect API + HTML surface + global re-routes."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["grok-interconnect"])
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _capture_evolve(refresh: bool = True):
    from fusion_hero_os.core.grok_interconnect import capture, evolve, get_graph

    if refresh:
        return evolve(capture()).to_dict()
    return get_graph(refresh=False)


@router.get("/api/grok/interconnect")
async def api_grok_interconnect(refresh: bool = Query(True)):
    return await asyncio.to_thread(_capture_evolve, refresh)


@router.post("/api/grok/interconnect/capture")
async def api_grok_interconnect_capture():
    from fusion_hero_os.core.grok_interconnect import capture, evolve

    g = await asyncio.to_thread(lambda: evolve(capture()).to_dict())
    return {"ok": True, "graph": g}


@router.get("/api/grok/route")
async def api_grok_route(
    intent: str = Query(""),
    message: str = Query(""),
):
    """Resolve intent/message through canonical route table (alles umgeroutet)."""
    from fusion_hero_os.core.grok_route_table import all_routes, resolve, route_message

    if intent:
        rt = resolve(intent)
        return {
            "ok": bool(rt),
            "intent": intent,
            "target": rt.to_dict() if rt else None,
            "table_entrypoints": all_routes()["entrypoints"],
        }
    intents = []
    if message:
        try:
            from grok_bridge import get_grok_bridge

            intents = get_grok_bridge()._detect_intents(message)
        except Exception:  # noqa: BLE001
            intents = []
    plan = route_message(message, intents)
    plan["intents"] = intents
    plan["entrypoints"] = all_routes()["entrypoints"]
    return plan


@router.get("/api/grok/routes")
async def api_grok_routes_table():
    from fusion_hero_os.core.grok_route_table import all_routes

    return all_routes()


# --- Legacy path re-routes (alles entsprechend umrouten) ---
# Keep in sync with fusion_hero_os.core.grok_route_table.LEGACY_REDIRECTS

@router.get("/grok")
async def redir_grok():
    return RedirectResponse("/mainframe/grok", status_code=307)


@router.get("/grok/status")
async def redir_grok_status():
    return RedirectResponse("/api/grok/status", status_code=307)


@router.get("/grok/chat")
async def redir_grok_chat():
    return RedirectResponse("/api/grok/chat", status_code=307)


@router.get("/interconnect")
async def redir_interconnect():
    return RedirectResponse("/mainframe/grok", status_code=307)


@router.get("/ide")
async def redir_ide():
    return RedirectResponse("/mainframe/ide", status_code=307)


@router.get("/worktree")
async def redir_worktree():
    return RedirectResponse("/mainframe/worktree", status_code=307)


@router.get("/portal")
async def redir_portal():
    return RedirectResponse("/mainframe", status_code=307)


@router.get("/mainframe/website")
async def redir_mainframe_website():
    return RedirectResponse("/mainframe", status_code=307)


@router.get("/vr/persistent")
async def redir_vr_persistent():
    return RedirectResponse("/mainframe/vr", status_code=307)


@router.get("/api/interconnect")
async def redir_api_interconnect():
    return RedirectResponse("/api/grok/interconnect", status_code=307)


@router.get("/api/grok/route/redirect")
async def api_route_redirect(intent: str = Query("interconnect")):
    """HTTP redirect to surface for an intent (for browsers / deep links)."""
    from fusion_hero_os.core.grok_route_table import resolve

    rt = resolve(intent) or resolve("interconnect")
    target = (rt.surface if rt else "/mainframe/grok")
    if target.startswith("http"):
        return RedirectResponse(target, status_code=307)
    return RedirectResponse(target, status_code=307)


@router.get("/mainframe/grok", response_class=HTMLResponse)
async def mainframe_grok_page():
    html = """<!DOCTYPE html>
<html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grok Interconnect · Mainframe</title>
<link rel="stylesheet" href="/static/mainframe_site.css">
<style>
.ic-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1200px;margin:0 auto;padding:16px 20px}
@media(max-width:900px){.ic-grid{grid-template-columns:1fr}}
.ic-node{display:inline-block;margin:4px;padding:6px 10px;border-radius:999px;border:1px solid #1e293b;font-size:12px}
.ic-node.on{border-color:#00d4aa;color:#00d4aa}
.ic-node.off{border-color:#7f1d1d;color:#fca5a5;opacity:.85}
.ic-edge{font-size:12px;color:#94a3b8;padding:2px 0}
.ic-edge.live{color:#40e0d0}
.score{font-size:2rem;font-weight:700;color:#00d4aa}
</style>
</head><body class="mf-body">
<header class="mf-header compact">
  <div class="mf-brand"><span class="mf-logo">G</span>
    <div><h1>GROK INTERCONNECT</h1>
    <p class="mf-sub">Abgreifen · Weiterentwickeln · Live-Graph</p></div>
  </div>
  <nav class="mf-nav">
    <a href="/mainframe">Hub</a>
    <a href="/mainframe/vr">Dauer-VR</a>
    <a href="/mainframe/ide">IDE</a>
    <a href="/">Dashboard</a>
    <a href="/api/grok/interconnect">JSON</a>
  </nav>
</header>
<main class="ic-grid">
  <section class="mf-card">
    <h2>Health Score</h2>
    <div class="score" id="ic-score">—</div>
    <p class="muted" id="ic-summary"></p>
    <button class="btn-mini" type="button" id="ic-refresh">↻ Capture + Evolve</button>
  </section>
  <section class="mf-card">
    <h2>Recommendations</h2>
    <ul id="ic-rec" class="mf-links"></ul>
  </section>
  <section class="mf-card">
    <h2>Nodes</h2>
    <div id="ic-nodes"></div>
  </section>
  <section class="mf-card">
    <h2>Edges</h2>
    <div id="ic-edges"></div>
  </section>
  <section class="mf-card" style="grid-column:1/-1">
    <h2>Evolved Architecture</h2>
    <pre class="mf-pre" id="ic-evolved">…</pre>
  </section>
  <section class="mf-card" style="grid-column:1/-1">
    <h2>Raw Graph</h2>
    <pre class="mf-pre" id="ic-raw">…</pre>
  </section>
</main>
<script>
async function load(refresh=true){
  const r = await fetch('/api/grok/interconnect?refresh='+refresh, {cache:'no-store'});
  const g = await r.json();
  document.getElementById('ic-score').textContent = g.health_score;
  const s = g.summary || {};
  document.getElementById('ic-summary').textContent =
    `nodes ${s.online_nodes||0}/${s.nodes||0} online · edges ${s.live_edges||0}/${s.edges||0} live`;
  const rec = document.getElementById('ic-rec');
  rec.innerHTML = (g.recommendations||[]).map(x=>'<li>'+x+'</li>').join('') || '<li>none</li>';
  document.getElementById('ic-nodes').innerHTML = (g.nodes||[]).map(n =>
    `<span class="ic-node ${n.online?'on':'off'}" title="${(n.path_or_url||'').replace(/"/g,'')}">${n.id} · ${n.kind}</span>`
  ).join('');
  document.getElementById('ic-edges').innerHTML = (g.edges||[]).map(e =>
    `<div class="ic-edge ${e.live?'live':''}">${e.source} —${e.relation}→ ${e.target}${e.note?' · '+e.note:''}</div>`
  ).join('');
  document.getElementById('ic-evolved').textContent = JSON.stringify(g.evolved||{}, null, 2);
  document.getElementById('ic-raw').textContent = JSON.stringify(g, null, 2);
}
document.getElementById('ic-refresh').onclick = () => load(true);
load(true);
setInterval(() => load(false), 30000);
</script>
</body></html>"""
    return HTMLResponse(html)
