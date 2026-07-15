# -*- coding: utf-8 -*-
"""
Pseudo-Inhouse AI Server facade — OpenAI-compatible + Fusion status APIs.

Links free SOTA services (Ollama, OpenRouter free, Groq, Gemini, HF, …)
behind local endpoints so clients treat the mainframe as the AI server.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_CODE = _ROOT / "03_Code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

router = APIRouter(tags=["pseudo-inhouse-ai"])


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1)
    system: Optional[str] = None
    provider: Optional[str] = None  # auto | groq | ollama | …
    role: str = "worker"


class OpenAIMessage(BaseModel):
    role: str
    content: Any = ""


class OpenAIChatRequest(BaseModel):
    model: str = "fusion-inhouse/auto"
    messages: List[OpenAIMessage] = Field(default_factory=list)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


def _hub():
    from fusion_hero_os.core.pseudo_inhouse_ai import (
        catalog,
        complete,
        list_models,
        status,
    )

    return status, catalog, complete, list_models


@router.get("/api/ai/inhouse/status")
async def api_inhouse_status():
    status, *_ = _hub()
    return status()


@router.get("/api/ai/inhouse/catalog")
async def api_inhouse_catalog():
    _, catalog, *_ = _hub()
    return catalog()


@router.post("/api/ai/inhouse/chat")
async def api_inhouse_chat(body: ChatIn):
    *_, complete, _lm = _hub()
    # complete is 3rd
    from fusion_hero_os.core.pseudo_inhouse_ai import complete as do_complete

    r = do_complete(
        body.message,
        system=body.system,
        provider=body.provider,
        role=body.role,
    )
    return r.to_dict()


@router.get("/v1/models")
async def openai_list_models():
    from fusion_hero_os.core.pseudo_inhouse_ai import list_models

    return list_models()


@router.post("/v1/chat/completions")
async def openai_chat_completions(body: OpenAIChatRequest):
    """OpenAI-compatible facade — point clients at http://127.0.0.1:8000/v1."""
    from fusion_hero_os.core.pseudo_inhouse_ai import complete

    if body.stream:
        # streaming not implemented — return full completion with note
        pass

    system_parts: List[str] = []
    user_parts: List[str] = []
    for m in body.messages:
        content = m.content
        if isinstance(content, list):
            # multimodal content parts
            texts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    texts.append(str(part.get("text") or ""))
                elif isinstance(part, str):
                    texts.append(part)
            content = "\n".join(texts)
        text = str(content or "")
        if m.role == "system":
            system_parts.append(text)
        else:
            user_parts.append(f"{m.role}: {text}" if m.role != "user" else text)

    prompt = "\n\n".join(user_parts).strip() or "(empty)"
    system = "\n".join(system_parts) if system_parts else None
    provider = None
    model = body.model or "fusion-inhouse/auto"
    if model.startswith("fusion-inhouse/"):
        provider = model.split("/", 1)[1]
        if provider == "auto":
            provider = None
    elif "/" in model and not model.startswith("fusion"):
        # allow raw provider id as model
        provider = model.split("/")[0]

    r = complete(prompt, system=system, provider=provider)
    return r.openai_chat_completion()


@router.get("/api/ai/inhouse/health")
async def api_inhouse_health():
    from fusion_hero_os.core.pseudo_inhouse_ai import status

    st = status()
    return {
        "ok": True,
        "pseudo_inhouse": True,
        "any_external_live": st.get("any_external_live"),
        "providers_live": [
            p["id"] for p in st.get("providers") or [] if p.get("live")
        ],
    }
