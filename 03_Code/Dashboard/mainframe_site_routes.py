# -*- coding: utf-8 -*-
"""
Mainframe Website — Dauer-VR + IDE + hyperlinked worktree.

Operational surfaces:
  /mainframe              hub (GUI portal)
  /mainframe/vr           always-on A-Frame VR (Dauer-VR)
  /mainframe/ide          browser IDE shell (file tree + preview + terminals status)
  /mainframe/worktree     full repo tree hyperlinked
  /mainframe/worktree/view  safe file viewer
  /api/mainframe/worktree/*  JSON for tree, worktrees, file meta
"""
from __future__ import annotations

import html
import mimetypes
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

router = APIRouter(tags=["mainframe-site"])
_BASE = Path(__file__).resolve().parent
_TEMPLATES = _BASE / "templates"

# Repo root: 03_Code/Dashboard -> parents[2] = fusion-hero-os
_DEFAULT_REPO = Path(os.getenv("FUSION_REPO_ROOT", _BASE.parents[1])).resolve()
_SKIP_DIR = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", "dist", "build", ".cursor", ".cargo", ".npm",
}
_TEXT_EXTS = {
    ".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".html", ".css",
    ".js", ".ts", ".tsx", ".jsx", ".rs", ".c", ".h", ".cpp", ".go", ".sh",
    ".ps1", ".bat", ".env", ".ini", ".cfg", ".xml", ".svg", ".csv", ".sql",
    ".dockerfile", ".gitignore", ".editorconfig",
}
_MAX_PREVIEW_BYTES = 400_000


def _repo() -> Path:
    return _DEFAULT_REPO


def _safe_join(root: Path, rel: str) -> Path:
    """Resolve rel under root; block path traversal."""
    rel = (rel or "").replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise HTTPException(status_code=400, detail="path traversal denied")
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="path outside worktree")
    return target


def _tpl(name: str) -> str:
    p = _TEMPLATES / name
    if not p.is_file():
        return f"<!-- missing template {name} -->"
    return p.read_text(encoding="utf-8")


def _git_worktrees(repo: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if proc.returncode != 0:
            # fallback simple list
            proc2 = subprocess.run(
                ["git", "-C", str(repo), "worktree", "list"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            for line in (proc2.stdout or "").splitlines():
                parts = line.split()
                if parts:
                    out.append({"path": parts[0], "branch": parts[1] if len(parts) > 1 else "", "raw": line})
            return out
        cur: Dict[str, Any] = {}
        for line in (proc.stdout or "").splitlines():
            if line.startswith("worktree "):
                if cur:
                    out.append(cur)
                cur = {"path": line[len("worktree "):]}
            elif line.startswith("HEAD "):
                cur["head"] = line[5:]
            elif line.startswith("branch "):
                cur["branch"] = line[len("branch "):].replace("refs/heads/", "")
            elif line == "bare":
                cur["bare"] = True
            elif line == "detached":
                cur["detached"] = True
        if cur:
            out.append(cur)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        out.append({"error": str(exc)})
    return out


def _related_trees() -> List[Dict[str, str]]:
    """Known sibling trees under Admin (operational map, not full FS crawl)."""
    home = Path.home()
    candidates = [
        _repo(),
        home / "fusion-hero-os",
        home / "fusion-hero-core",
        home / "heroic-highest-layer",
        home / "heroic-core-foundation",
        home / ".fusion",
    ]
    seen = set()
    rows = []
    for p in candidates:
        try:
            rp = p.resolve()
        except OSError:
            continue
        key = str(rp).lower()
        if key in seen or not rp.exists():
            continue
        seen.add(key)
        rows.append({
            "name": rp.name,
            "path": str(rp),
            "href": f"/mainframe/worktree?root={html.escape(str(rp))}" if rp == _repo()
            else f"/mainframe/worktree?root={rp.as_posix()}",
            "is_primary": str(rp) == str(_repo()),
        })
    return rows


def _list_dir(root: Path, rel: str = "", max_entries: int = 500) -> Dict[str, Any]:
    base = _safe_join(root, rel) if rel else root
    if not base.exists():
        raise HTTPException(status_code=404, detail="path not found")
    if base.is_file():
        return {"type": "file", "path": rel or base.name, "name": base.name}
    entries: List[Dict[str, Any]] = []
    try:
        kids = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    for i, child in enumerate(kids):
        if i >= max_entries:
            break
        if child.name in _SKIP_DIR:
            continue
        crel = f"{rel}/{child.name}".lstrip("/") if rel else child.name
        try:
            st = child.stat()
            size = st.st_size
            mtime = st.st_mtime
        except OSError:
            size, mtime = 0, 0
        entries.append({
            "name": child.name,
            "path": crel.replace("\\", "/"),
            "type": "dir" if child.is_dir() else "file",
            "size": size,
            "mtime": mtime,
            "href": f"/mainframe/worktree?path={crel}" if child.is_dir()
            else f"/mainframe/worktree/view?path={crel}",
            "api_href": f"/api/mainframe/worktree/file?path={crel}",
        })
    return {
        "ok": True,
        "root": str(root),
        "path": rel.replace("\\", "/"),
        "type": "dir",
        "entries": entries,
        "parent": "/".join(rel.replace("\\", "/").split("/")[:-1]) if rel else None,
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get("/mainframe", response_class=HTMLResponse)
async def mainframe_hub():
    tpl = _TEMPLATES / "mainframe_site.html"
    if tpl.is_file():
        return HTMLResponse(tpl.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>mainframe_site.html missing</h1>", status_code=500)


@router.get("/mainframe/vr", response_class=HTMLResponse)
async def mainframe_vr_persistent():
    """Dauer-VR: always-on A-Frame shell with live HUD."""
    tpl = _TEMPLATES / "mainframe_vr_persistent.html"
    if tpl.is_file():
        return HTMLResponse(tpl.read_text(encoding="utf-8"))
    # fallback redirect
    return RedirectResponse("/vr/viewer", status_code=302)


@router.get("/mainframe/ide", response_class=HTMLResponse)
async def mainframe_ide():
    tpl = _TEMPLATES / "mainframe_ide.html"
    if tpl.is_file():
        return HTMLResponse(tpl.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>mainframe_ide.html missing</h1>", status_code=500)


@router.get("/mainframe/worktree", response_class=HTMLResponse)
async def mainframe_worktree_page(
    path: str = Query(""),
    root: Optional[str] = Query(None),
):
    tpl = _TEMPLATES / "mainframe_worktree.html"
    body = tpl.read_text(encoding="utf-8") if tpl.is_file() else "<h1>worktree template missing</h1>"
    body = body.replace("{{INITIAL_PATH}}", html.escape(path or ""))
    body = body.replace("{{REPO_ROOT}}", html.escape(str(_repo())))
    return HTMLResponse(body)


@router.get("/mainframe/worktree/view", response_class=HTMLResponse)
async def mainframe_worktree_view(path: str = Query(...)):
    repo = _repo()
    target = _safe_join(repo, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="not a file")
    ext = target.suffix.lower()
    rel = path.replace("\\", "/")
    nav = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(target.name)}</title>
<style>
body{{background:#0a0a0f;color:#e2e8f0;font-family:ui-monospace,Consolas,monospace;margin:0}}
header{{padding:12px 20px;background:#11121a;border-bottom:1px solid #1e293b;display:flex;gap:16px;flex-wrap:wrap;align-items:center}}
a{{color:#40e0d0;text-decoration:none}} a:hover{{text-decoration:underline}}
pre{{padding:20px;overflow:auto;line-height:1.45;font-size:13px;white-space:pre-wrap;word-break:break-word}}
.meta{{color:#94a3b8;font-size:12px}}
img,video{{max-width:100%;height:auto;display:block;margin:20px auto}}
</style></head><body>
<header>
  <a href="/mainframe">◈ Mainframe</a>
  <a href="/mainframe/worktree?path={html.escape('/'.join(rel.split('/')[:-1]))}">← Tree</a>
  <a href="/mainframe/ide?path={html.escape(rel)}">IDE</a>
  <strong>{html.escape(rel)}</strong>
  <span class="meta">{target.stat().st_size} bytes</span>
</header>"""
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return HTMLResponse(
            nav + f'<img src="/api/mainframe/worktree/raw?path={html.escape(rel)}" alt="">'
            "</body></html>"
        )
    if ext not in _TEXT_EXTS and target.stat().st_size > 64_000:
        return HTMLResponse(
            nav + f'<p class="meta" style="padding:20px">Binary/large file. '
            f'<a href="/api/mainframe/worktree/raw?path={html.escape(rel)}">Download raw</a></p></body></html>'
        )
    try:
        data = target.read_bytes()
        if len(data) > _MAX_PREVIEW_BYTES:
            data = data[:_MAX_PREVIEW_BYTES]
            truncated = True
        else:
            truncated = False
        text = data.decode("utf-8", errors="replace")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    note = f'<p class="meta" style="padding:0 20px">truncated to {_MAX_PREVIEW_BYTES} bytes</p>' if truncated else ""
    return HTMLResponse(
        nav + note + f"<pre>{html.escape(text)}</pre></body></html>"
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@router.get("/api/mainframe/site/status")
async def api_site_status():
    repo = _repo()
    worktrees = _git_worktrees(repo)
    return {
        "ok": True,
        "ts": time.time(),
        "repo": str(repo),
        "surfaces": {
            "hub": "/mainframe",
            "vr_dauer": "/mainframe/vr",
            "ide": "/mainframe/ide",
            "worktree": "/mainframe/worktree",
            "ops": "/mainframe/ops",
            "dashboard": "/",
            "vr_viewer": "/vr/viewer",
            "highest_layer_vr": "/highest-layer-vr",
            "architecture": "/architecture",
            "publish_gce": "http://100.103.188.54:8088/docs/publish/v10/",
        },
        "worktrees": worktrees,
        "related": _related_trees(),
        "vr": {"dauer": True, "viewer": "/mainframe/vr", "assets_api": "/api/vr/assets"},
    }


@router.get("/api/mainframe/worktree/list")
async def api_worktree_list(path: str = Query("")):
    return _list_dir(_repo(), path)


@router.get("/api/mainframe/worktree/git")
async def api_worktree_git():
    return {"ok": True, "worktrees": _git_worktrees(_repo()), "related": _related_trees()}


@router.get("/api/mainframe/worktree/file")
async def api_worktree_file_meta(path: str = Query(...)):
    target = _safe_join(_repo(), path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="not found")
    st = target.stat()
    return {
        "ok": True,
        "path": path.replace("\\", "/"),
        "name": target.name,
        "is_dir": target.is_dir(),
        "size": st.st_size,
        "mtime": st.st_mtime,
        "view": f"/mainframe/worktree/view?path={path}",
        "raw": f"/api/mainframe/worktree/raw?path={path}",
        "ide": f"/mainframe/ide?path={path}",
    }


@router.get("/api/mainframe/worktree/raw")
async def api_worktree_raw(path: str = Query(...)):
    target = _safe_join(_repo(), path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="not a file")
    media, _ = mimetypes.guess_type(str(target))
    return FileResponse(target, media_type=media or "application/octet-stream", filename=target.name)


@router.get("/api/mainframe/worktree/content")
async def api_worktree_content(path: str = Query(...), max_bytes: int = Query(200_000, ge=1000, le=_MAX_PREVIEW_BYTES)):
    target = _safe_join(_repo(), path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="not a file")
    data = target.read_bytes()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    try:
        text = data.decode("utf-8")
        binary = False
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
        binary = True
    return {
        "ok": True,
        "path": path.replace("\\", "/"),
        "text": text,
        "truncated": truncated,
        "binary_hint": binary,
        "size": target.stat().st_size,
    }


@router.get("/api/mainframe/ide/status")
async def api_ide_status():
    """IDE operational status: bridge ports, kernel paths, worktree."""
    kernel_ide = _repo() / "kernel" / "ide"
    return {
        "ok": True,
        "repo": str(_repo()),
        "kernel_ide": {
            "path": str(kernel_ide),
            "exists": kernel_ide.is_dir(),
            "files": [p.name for p in kernel_ide.glob("*") if p.is_file()] if kernel_ide.is_dir() else [],
        },
        "endpoints": {
            "tree": "/api/mainframe/worktree/list",
            "content": "/api/mainframe/worktree/content",
            "health": "/api/health",
            "bridge": "/api/bridge/ipc/status",
            "vr": "/api/vr/status",
            "ops": "/api/mainframe/ops/summary",
        },
        "ui": "/mainframe/ide",
    }
