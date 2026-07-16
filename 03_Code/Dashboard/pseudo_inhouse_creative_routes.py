# -*- coding: utf-8 -*-
"""Pseudo-Inhouse Creative Server — image/video/PDF/graphics facade.

Policy: freemium=false. All creative creation goes through local Mainframe.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "03_Code")):
    if p not in sys.path:
        sys.path.insert(0, p)

router = APIRouter(tags=["pseudo-inhouse-creative"])


class CreateIn(BaseModel):
    modality: str = Field("image", description="image|graphics|pdf|video")
    prompt: str = Field(..., min_length=1)
    title: Optional[str] = None
    size: Optional[str] = "1024x768"
    style: Optional[str] = "poster"
    kind: Optional[str] = "diagram"
    pages: Optional[int] = 2
    frames: Optional[int] = 8
    fps: Optional[int] = 4


class OpenAIImageRequest(BaseModel):
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    model: str = "fusion-inhouse/creative"
    response_format: Optional[str] = "url"


@router.get("/api/creative/inhouse/status")
async def creative_status():
    from fusion_hero_os.core.pseudo_inhouse_creative import status

    return status()


@router.get("/api/creative/inhouse/catalog")
async def creative_catalog():
    from fusion_hero_os.core.pseudo_inhouse_creative import catalog

    return catalog()


@router.get("/api/creative/inhouse/artifacts")
async def creative_artifacts(limit: int = 30):
    from fusion_hero_os.core.pseudo_inhouse_creative import list_artifacts

    return list_artifacts(limit=limit)


@router.post("/api/creative/inhouse/create")
async def creative_create(body: CreateIn):
    from fusion_hero_os.core.pseudo_inhouse_creative import create

    kw: Dict[str, Any] = {}
    if body.size:
        kw["size"] = body.size
    if body.title:
        kw["title"] = body.title
    if body.style:
        kw["style"] = body.style
    if body.kind:
        kw["kind"] = body.kind
    if body.pages is not None:
        kw["pages"] = body.pages
    if body.frames is not None:
        kw["frames"] = body.frames
    if body.fps is not None:
        kw["fps"] = body.fps
    return create(body.modality, body.prompt, **kw).to_dict()


@router.post("/api/creative/inhouse/image")
async def creative_image(body: CreateIn):
    from fusion_hero_os.core.pseudo_inhouse_creative import create_image

    return create_image(
        body.prompt, size=body.size or "1024x768", style=body.style or "poster", title=body.title
    ).to_dict()


@router.post("/api/creative/inhouse/pdf")
async def creative_pdf(body: CreateIn):
    from fusion_hero_os.core.pseudo_inhouse_creative import create_pdf

    return create_pdf(body.prompt, title=body.title, pages=body.pages or 2).to_dict()


@router.post("/api/creative/inhouse/video")
async def creative_video(body: CreateIn):
    from fusion_hero_os.core.pseudo_inhouse_creative import create_video

    return create_video(
        body.prompt,
        frames=body.frames or 8,
        size=body.size or "640x360",
        fps=body.fps or 4,
    ).to_dict()


@router.post("/api/creative/inhouse/graphics")
async def creative_graphics(body: CreateIn):
    from fusion_hero_os.core.pseudo_inhouse_creative import create_graphics

    return create_graphics(
        body.prompt, kind=body.kind or "diagram", size=body.size or "1024x768"
    ).to_dict()


@router.get("/api/creative/inhouse/file")
async def creative_file(path: str):
    """Serve artifact if under creative output dir (path safety)."""
    from fusion_hero_os.core.pseudo_inhouse_creative import output_dir

    root = output_dir().resolve()
    target = Path(path).resolve()
    if root not in target.parents and target != root:
        # also allow direct child
        try:
            target.relative_to(root)
        except ValueError:
            return {"ok": False, "error": "path outside creative output dir"}
    if not target.is_file():
        return {"ok": False, "error": "not found"}
    return FileResponse(str(target))


@router.post("/v1/images/generations")
async def openai_images(body: OpenAIImageRequest):
    from fusion_hero_os.core.pseudo_inhouse_creative import create_image, openai_image_response

    # OpenAI size like 1024x1024
    size = body.size if "x" in (body.size or "") else "1024x1024"
    r = create_image(body.prompt, size=size, style="poster")
    return openai_image_response(r)
