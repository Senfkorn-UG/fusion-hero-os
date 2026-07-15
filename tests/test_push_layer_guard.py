# -*- coding: utf-8 -*-
import os

from fusion_hero_os.core.push_layer_guard import evaluate_push, load_config, status


def test_config_identities():
    c = load_config()
    assert c.get("freemium") is False
    ids = c.get("identities") or {}
    assert "95guknow/fusion-hero-os" in str(ids.get("remote_urls"))
    assert ids.get("platform_version") == "10.0.0"


def test_block_auto_save_without_intent(monkeypatch):
    monkeypatch.delenv("FUSION_PUSH_INTENT", raising=False)
    monkeypatch.delenv("FUSION_ALLOW_PUSH", raising=False)
    # no operator secrets for this test
    for k in (
        "FUSION_PUSH_SECRET",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GROQ_API_KEY",
        "OPENROUTER_API_KEY",
        "XAI_API_KEY",
        "GROK_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        "fusion_hero_os.core.push_layer_guard._load_dotenv_files",
        lambda cfg: [],
    )
    monkeypatch.setattr(
        "fusion_hero_os.core.push_layer_guard._secret_intent",
        lambda cfg: (False, []),
    )
    d = evaluate_push(
        remote="origin",
        branch="main",
        remote_url="https://github.com/95guknow/fusion-hero-os.git",
        files=["docs/mesh/README.md"],
        subjects=["auto-save [2026-07-15] main - M docs"],
    )
    assert d.allow is False
    assert d.unwanted is True
    assert d.auto_save is True


def test_allow_with_intent_env(monkeypatch):
    monkeypatch.setenv("FUSION_PUSH_INTENT", "1")
    d = evaluate_push(
        remote="origin",
        branch="main",
        remote_url="https://github.com/95guknow/fusion-hero-os.git",
        files=["docs/mesh/README.md"],
        subjects=["auto-save [2026-07-15] main - M docs"],
    )
    assert d.allow is True
    assert d.wanted is True
    assert d.intent is True


def test_allow_conventional_feat(monkeypatch):
    monkeypatch.delenv("FUSION_PUSH_INTENT", raising=False)
    d = evaluate_push(
        remote="origin",
        branch="main",
        remote_url="https://github.com/95guknow/fusion-hero-os.git",
        files=["fusion_hero_os/core/push_layer_guard.py"],
        subjects=["feat: add push layer guard"],
    )
    assert d.allow is True
    assert d.wanted is True


def test_block_secrets_even_with_intent(monkeypatch):
    monkeypatch.setenv("FUSION_PUSH_INTENT", "1")
    d = evaluate_push(
        remote="origin",
        branch="main",
        remote_url="https://github.com/95guknow/fusion-hero-os.git",
        files=[".env", "docs/x.md"],
        subjects=["feat: oops secrets"],
    )
    assert d.allow is False
    assert d.deny_hits


def test_block_unknown_remote(monkeypatch):
    monkeypatch.setenv("FUSION_PUSH_INTENT", "1")
    d = evaluate_push(
        remote="evil",
        branch="main",
        remote_url="https://github.com/evil/not-ours.git",
        files=["README.md"],
        subjects=["feat: leak"],
    )
    assert d.allow is False
    assert d.remote_ok is False


def test_status():
    st = status()
    assert st.get("ok") is True
    assert "L0_foundation" in (st.get("layers") or []) or st.get("layers")


def test_wanted_via_secret_env(monkeypatch):
    monkeypatch.delenv("FUSION_PUSH_INTENT", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-not-a-real-key-but-nonempty")
    d = evaluate_push(
        remote="origin",
        branch="main",
        remote_url="https://github.com/95guknow/fusion-hero-os.git",
        files=["docs/mesh/README.md"],
        subjects=["auto-save [x] main - M docs"],
    )
    assert d.allow is True
    assert d.secret_intent is True
    assert "GROQ_API_KEY" in d.secret_keys_present
