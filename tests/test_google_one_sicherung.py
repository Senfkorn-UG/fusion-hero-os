# -*- coding: utf-8 -*-
from fusion_hero_os.core.google_one_sicherung import (
    activate,
    status,
    run_snapshot,
    load_config,
)


def test_config_drive_folder():
    cfg = load_config()
    assert cfg.get("provider") == "google_one"
    assert (cfg.get("drive") or {}).get("folder_id")


def test_activate_no_browser():
    r = activate(open_browser=False)
    assert r.get("ok") and r.get("activated")
    st = status()
    assert st.get("activated") is True


def test_snapshot_public_safe():
    m = run_snapshot()
    assert m.get("ok")
    assert m.get("file_count", 0) >= 1
    assert m.get("secrets_excluded") is True
    # no secret path names
    for f in m.get("files") or []:
        rel = (f.get("rel") or "").lower()
        assert "secret" not in rel
        assert not rel.endswith(".env")


def test_desktop_and_phone_setup():
    from fusion_hero_os.core.google_one_sicherung import setup_desktop, setup_phone

    d = setup_desktop(open_browser=False, start_app=False)
    assert d.get("ok")
    assert "drivefs_exe" in d or d.get("drivefs_running") is not None
    p = setup_phone(open_browser=False)
    assert p.get("ok")
    assert p.get("links", {}).get("drive_android")
    st = status()
    assert "desktop" in st
