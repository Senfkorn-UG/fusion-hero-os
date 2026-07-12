# vr_routes.py — Highest Layer VR + A-Frame 360° viewer

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter(tags=["vr"])

CODE_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = Path(__file__).resolve().parent
FUSION_ROOT = Path(os.environ.get("FUSION_HERO_ROOT", CODE_ROOT.parent))
VR_ASSETS = Path(os.environ.get("FUSION_VR_ASSETS_ROOT", FUSION_ROOT / "03_VR_Assets"))
HL_PATHS = [
    CODE_ROOT / "heroic-highest-layer",
    Path(os.environ.get("HEROIC_HIGHEST_LAYER", r"C:\Users\Admin\heroic-highest-layer")),
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _scan_scene_files() -> list[dict]:
    """Dynamically list every image in VR_ASSETS instead of two hardcoded filenames."""
    if not VR_ASSETS.exists():
        return []
    out = []
    for p in sorted(VR_ASSETS.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            out.append({
                "file": p.name,
                "url": f"/vr/assets/{p.name}",
                "size_bytes": p.stat().st_size,
            })
    return out


def _hl_path() -> Path:
    for p in HL_PATHS:
        if (p / "highest_layer.py").exists():
            return p.resolve()
    return HL_PATHS[0]


def _ensure_hl_import():
    p = str(_hl_path())
    if p not in sys.path:
        sys.path.insert(0, p)


@router.get("/highest-layer", response_class=HTMLResponse)
async def highest_layer_page():
    spec_path = _hl_path() / "HIGHEST_LAYER.md"
    content = spec_path.read_text(encoding="utf-8") if spec_path.exists() else "Spec not found."
    live_status = "Layer not loadable."
    try:
        _ensure_hl_import()
        from highest_layer import load as _load
        live_status = json.dumps(_load().status(), indent=2, default=str)
    except Exception as e:
        live_status = f"Load error: {e}"

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Heroic Highest Layer (Layer 4)</title>
<style>body{{background:#0a0a0f;color:#e2e8f0;font-family:ui-sans-serif,system-ui;margin:40px;line-height:1.6}}
pre{{background:#11121a;padding:20px;border-radius:12px;overflow:auto;border:1px solid #1e1e2e}}a{{color:#40e0d0}}</style>
</head><body>
<h1>Heroic Highest Layer — Layer 4 (ohne VR)</h1>
<p><a href="/">← Dashboard</a> · <a href="/heroic">Heroic</a> · <a href="/highest-layer-vr">Mit VR</a> · <a href="/vr/viewer">360° Viewer</a></p>
<h2>Live Load Status</h2><pre>{live_status}</pre>
<h2>Spec</h2><pre>{content}</pre>
</body></html>"""
    return HTMLResponse(html)


@router.get("/highest-layer-vr", response_class=HTMLResponse)
async def highest_layer_vr_page():
    spec_path = _hl_path() / "vr" / "VR_PROTOCOL.md"
    content = spec_path.read_text(encoding="utf-8") if spec_path.exists() else "VR Protocol not found."
    live_status = "VR layer not loadable."
    vr_visual = ""
    try:
        _ensure_hl_import()
        from highest_layer import load_vr as _load_vr
        hl = _load_vr()
        live_status = json.dumps(hl.get_vr_status(), indent=2, default=str)
        vr_visual = hl.render_roadmap_visual().replace("\n", "<br>")
    except Exception as e:
        live_status = f"Load error: {e}"

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Heroic Highest Layer — MIT VR</title>
<style>body{{background:#0a0a0f;color:#e2e8f0;font-family:ui-sans-serif,system-ui;margin:40px;line-height:1.6}}
pre{{background:#11121a;padding:20px;border-radius:12px;overflow:auto;border:1px solid #1e1e2e}}a{{color:#40e0d0}}
.vr-panel{{background:#0f111a;padding:16px;border:1px solid #40e0d0;border-radius:12px}}</style>
</head><body>
<h1>Heroic Highest Layer — Layer 4 (MIT VR)</h1>
<p><a href="/">← Dashboard</a> · <a href="/highest-layer">Ohne VR</a> · <a href="/vr/viewer">360° Viewer</a></p>
<h2>Live VR Status</h2><pre>{live_status}</pre>
<div class="vr-panel"><h3>VR Roadmap Visual</h3><p>{vr_visual}</p></div>
<h2>VR Protocol</h2><pre>{content}</pre>
<p style="color:#94a3b8;font-size:12px">Assets: {VR_ASSETS}</p>
</body></html>"""
    return HTMLResponse(html)


@router.get("/vr/viewer", response_class=HTMLResponse)
async def vr_viewer(request: Request, pano: str | None = None, overlay: str | None = None):
    tpl = DASHBOARD / "templates" / "vr_viewer.html"
    if not tpl.exists():
        return HTMLResponse("<h1>vr_viewer.html missing</h1>", status_code=500)

    scenes = _scan_scene_files()
    names = [s["file"] for s in scenes]

    # Default pano = an "equirectangular"/360°-tagged file if present, else first found.
    # (Plain alphabetical order would silently swap pano/overlay when file names change.)
    default_pano = next((n for n in names if "equirectangular" in n.lower() or "360" in n.lower()), names[0] if names else None)
    remaining = [n for n in names if n != default_pano]
    default_overlay = remaining[0] if remaining else default_pano

    def _resolve(requested: str | None, default: str | None) -> str | None:
        if requested and Path(requested).name in names:
            return Path(requested).name
        return default

    pano_file = _resolve(pano, default_pano)
    overlay_file = _resolve(overlay, default_overlay)

    base = str(request.base_url).rstrip("/")
    pano_url = f"{base}/vr/assets/{pano_file}" if pano_file else ""
    overlay_url = f"{base}/vr/assets/{overlay_file}" if overlay_file else ""

    html = tpl.read_text(encoding="utf-8")
    html = html.replace("{{PANORAMA_URL}}", pano_url).replace("{{OVERLAY_URL}}", overlay_url)
    return HTMLResponse(html)


@router.get("/vr/assets/{filename}")
async def vr_asset_file(filename: str):
    safe = Path(filename).name
    if Path(safe).suffix.lower() not in IMAGE_EXTS:
        raise HTTPException(status_code=404, detail=f"Unsupported asset type: {safe}")
    path = VR_ASSETS / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"VR asset not found: {safe}")
    media = {
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/jpeg")
    return FileResponse(path, media_type=media)


@router.get("/api/vr/assets")
async def api_vr_assets():
    """Full dynamic scene list for the in-viewer asset picker (task 4)."""
    return {"vr_assets_root": str(VR_ASSETS), "scenes": _scan_scene_files()}


@router.get("/api/vr/roadmap")
async def api_vr_roadmap():
    """Roadmap milestones for rendering as spherical nodes in the VR scene (VR_PROTOCOL.md)."""
    try:
        _ensure_hl_import()
        from highest_layer import load_vr
        return load_vr().get_roadmap()
    except Exception as e:
        return {"version": "unknown", "milestones": [], "error": str(e)}


@router.get("/api/vr/status")
async def api_vr_status():
    scenes = _scan_scene_files()
    vr_layer = {}
    try:
        _ensure_hl_import()
        from highest_layer import load_vr
        vr_layer = load_vr().get_vr_status()
    except Exception as e:
        vr_layer = {"error": str(e)}
    return {
        "vr_assets_root": str(VR_ASSETS),
        "assets": scenes,
        "viewer": "/vr/viewer",
        "layer": vr_layer,
    }