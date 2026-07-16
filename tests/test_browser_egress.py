# -*- coding: utf-8 -*-
from fusion_hero_os.core.browser_egress import load_config, resolve_profile, status


def test_config_and_status():
    cfg = load_config()
    assert cfg.get("default_progid") == "CometHTM" or "profiles" in cfg
    st = status()
    assert st.get("ok")
    assert "bug_and_feature" in st
    # Comädchen = Nummer 2, exclusive operator channel
    cm = st.get("comaedchen") or cfg.get("comaedchen") or {}
    assert cm.get("rank") == "nummer_2" or cm.get("reports_only_to") == "operator"
    if cfg.get("comaedchen"):
        assert cfg["comaedchen"].get("input_only_from") == "operator"
        assert cfg["comaedchen"].get("reports_only_to") == "operator"


def test_google_routes_to_chrome():
    p = resolve_profile(url="https://one.google.com/storage")
    assert p.get("id") in ("chrome_personal", "chrome_work", "default")
    # policy prefers chrome_personal for google one
    assert p.get("id") == "chrome_personal" or p.get("kind") in ("chrome", "shell")


def test_local_can_use_default():
    p = resolve_profile(url="http://127.0.0.1:8000/mainframe")
    assert p.get("id") in ("default", "chrome_personal", "comet")
