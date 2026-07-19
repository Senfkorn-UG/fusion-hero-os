# -*- coding: utf-8 -*-
"""Tests for Hero Autoupdate (1-min poll, 5-min Android reminder)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from fusion_hero_os.core.hero_autoupdate import (
    DEFAULT_POLL_INTERVAL_SEC,
    DEFAULT_REMINDER_AFTER_SEC,
    HeroAutoupdateConfig,
    HeroAutoupdateService,
    reset_hero_autoupdate_for_tests,
)
from fusion_hero_os.modules.hero_autoupdate import HeroAutoupdateCoreModule


def _svc(tmp_path, **cfg_overrides) -> HeroAutoupdateService:
    cfg = HeroAutoupdateConfig.load()
    cfg.state_path = str(tmp_path / "hero_autoupdate_state.json")
    for k, v in cfg_overrides.items():
        setattr(cfg, k, v)
    return HeroAutoupdateService(cfg)


@pytest.fixture(autouse=True)
def _reset_singleton(tmp_path, monkeypatch):
    reset_hero_autoupdate_for_tests()
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("PHONE_NOTIFY_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("FUSION_HERO_POLL_INTERVAL_SEC", "60")
    monkeypatch.setenv("FUSION_HERO_REMINDER_AFTER_SEC", "300")
    yield
    reset_hero_autoupdate_for_tests()


def test_defaults_one_min_poll_five_min_reminder():
    cfg = HeroAutoupdateConfig.load()
    assert cfg.poll_interval_sec == DEFAULT_POLL_INTERVAL_SEC == 60.0
    assert cfg.reminder_after_sec == DEFAULT_REMINDER_AFTER_SEC == 300.0


def test_touch_resets_idle(tmp_path):
    svc = _svc(tmp_path)
    svc._state.last_interaction_ts = time.time() - 400
    assert svc.idle_sec() >= 399
    out = svc.touch(source="test")
    assert out["ok"] is True
    assert svc.idle_sec() < 2


def test_reminder_fires_after_idle(tmp_path):
    svc = _svc(
        tmp_path,
        reminder_after_sec=5.0,
        reminder_cooldown_sec=1.0,
        poll_interval_sec=15.0,
    )
    svc._state.last_interaction_ts = time.time() - 60
    svc._state.last_reminder_ts = 0.0
    # No webhook: notify returns not delivered but action still recorded
    result = svc.tick()
    assert result["ok"] is True
    assert result["reminder_sent"] is True
    assert any(a["kind"] == "reminder" for a in result["actions"])
    assert svc._state.reminder_count >= 1


def test_module_actions(tmp_path, monkeypatch):
    # Point singleton state into tmp via env HOME/USERPROFILE + empty yaml path override
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    reset_hero_autoupdate_for_tests()
    from fusion_hero_os.core import hero_autoupdate as ha

    svc = _svc(tmp_path)
    ha._instance = svc
    mod = HeroAutoupdateCoreModule()
    st = mod.process({"action": "status"})
    assert st is not None
    assert st["poll_interval_sec"] == 60.0
    assert st["reminder_after_sec"] == 300.0
    assert st["android_channel"] == "system_notification"
    touch = mod.process({"action": "touch", "source": "unit"})
    assert touch["ok"] is True
    cfg = mod.process({"action": "config"})
    assert cfg["poll_interval_sec"] == 60.0


def test_phone_notify_returns_console_only_without_webhook(monkeypatch):
    monkeypatch.delenv("PHONE_NOTIFY_WEBHOOK_URL", raising=False)
    from tailscale_phone_notify import send_phone_notification

    r = send_phone_notification("hello", title="test")
    assert r["delivered"] is False
    assert r["channel"] == "console_only"
