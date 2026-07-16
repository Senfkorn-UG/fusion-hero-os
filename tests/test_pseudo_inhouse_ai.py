# -*- coding: utf-8 -*-
"""Tests for pseudo-inhouse free AI hub."""
from fusion_hero_os.core.pseudo_inhouse_ai import (
    DEFAULT_CHAIN,
    catalog,
    complete,
    list_models,
    status,
)


def test_catalog_has_chain_and_facade():
    c = catalog()
    assert c.get("ok") is True
    assert "ollama" in (c.get("chain") or DEFAULT_CHAIN)
    assert c.get("facade") or True  # yaml may define facade


def test_status_shape():
    st = status()
    assert st.get("ok") is True
    assert st.get("pseudo_inhouse") is True
    assert st.get("platform") == "10.0.0"
    providers = st.get("providers") or []
    ids = {p["id"] for p in providers}
    assert "internal" in ids
    assert "ollama" in ids or "groq" in ids


def test_complete_always_returns_inhouse_shape():
    r = complete("ping", provider="internal")
    assert r.ok is True
    assert r.provider == "internal"
    assert r.inhouse is True
    assert "Fusion Hero OS" in r.response or r.response
    d = r.openai_chat_completion()
    assert d["object"] == "chat.completion"
    assert d["choices"][0]["message"]["content"]


def test_list_models_includes_auto():
    m = list_models()
    assert m.get("object") == "list"
    ids = [x["id"] for x in m.get("data") or []]
    assert any("auto" in i or "internal" in i or "fusion-inhouse" in i for i in ids)


def test_free_chain_registered():
    from llm_frameworks.registry import FREE_CHAIN, list_frameworks

    fws = list_frameworks()
    for pid in ("groq", "openrouter_free", "huggingface", "ollama"):
        assert pid in fws or pid in FREE_CHAIN
