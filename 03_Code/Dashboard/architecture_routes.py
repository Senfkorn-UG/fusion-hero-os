# architecture_routes.py — Dependency Atlas im Dashboard (Plot + JSON-API)

from __future__ import annotations

import html
import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["architecture"])

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_atlas():
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from fusion_hero_os.core.dependency_atlas import build_atlas_cached, render_mermaid
    atlas = build_atlas_cached()  # Quanten-Wörterbuch: Rescan nur bei geändertem Repo-Zustand
    return atlas, render_mermaid(atlas)


@router.get("/api/architecture/atlas")
async def api_architecture_atlas():
    """Vollstaendiger maschinell abgeleiteter Abhaengigkeitsgraph als JSON."""
    try:
        atlas, _ = _load_atlas()
        payload = atlas.to_dict()
        try:
            from fusion_hero_os.core.quantum_dictionaries import registry_stats
            payload["quantum_dictionaries"] = registry_stats()
        except Exception:
            pass
        return payload
    except Exception as e:
        return {"error": str(e)}


@router.get("/architecture", response_class=HTMLResponse)
async def architecture_page():
    """Live-Plot des Dependency Atlas (Mermaid, Layer-geclustert)."""
    try:
        atlas, mermaid_block = _load_atlas()
        epi = atlas.epistemik_summary()
        # ```mermaid ... ``` -> nackter Mermaid-Text fuer das <pre class=mermaid>
        mermaid_src = "\n".join(mermaid_block.splitlines()[1:-1])
        stats = (
            f"Knoten: {len(atlas.nodes)} · Kanten: {len(atlas.edges)} · "
            f"unaufgeloest: {epi['unresolved_count']} · Zyklen: {epi['cycle_count']} · "
            f"Platzhalter-Marker: {epi['placeholder_marker_total']} "
            f"in {epi['files_with_markers']} Dateien"
        )
        marker_rows = "".join(
            f"<tr><td><code>{html.escape(i['path'])}</code></td><td>{i['markers']}</td></tr>"
            for i in epi["top_marker_files"]
        )
        body = f"""
<p class="stats">{html.escape(stats)}</p>
<pre class="mermaid">{html.escape(mermaid_src)}</pre>
<h2>Epistemische Schuld — Top-Dateien</h2>
<table><tr><th>Datei</th><th>Marker</th></tr>{marker_rows}</table>"""
    except Exception as e:
        body = f"<p>Atlas nicht ladbar: {html.escape(str(e))}</p>"

    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Dependency Atlas — Fraktal-Layer</title>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'dark', maxTextSize: 200000 }});
</script>
<style>
  body {{ background:#0a0a0f; color:#e2e8f0; font-family:ui-sans-serif,system-ui; margin:40px; line-height:1.6 }}
  a {{ color:#40e0d0 }} .stats {{ color:#94a3b8 }}
  table {{ border-collapse:collapse }} td,th {{ border:1px solid #1e293b; padding:4px 10px }}
  pre.mermaid {{ background:#11121a; padding:20px; border-radius:12px; border:1px solid #1e1e2e; overflow:auto }}
</style></head><body>
<h1>Dependency Atlas — polyglotte Fraktal-Layer-Architektur</h1>
<p><a href="/">← Dashboard</a> · <a href="/api/architecture/atlas">JSON</a> ·
<a href="/highest-layer-vr">Highest Layer VR</a></p>
{body}
</body></html>"""
    return HTMLResponse(page)
