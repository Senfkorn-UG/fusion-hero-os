# -*- coding: utf-8 -*-
"""Tests for pseudo-inhouse creative hub (no freemium)."""
from pathlib import Path

from fusion_hero_os.core.pseudo_inhouse_creative import (
    catalog,
    create,
    create_image,
    create_pdf,
    create_video,
    create_graphics,
    status,
)


def test_policy_no_freemium():
    st = status()
    assert st.get("freemium") is False
    assert st.get("policy") == "pseudo_inhouse_only"
    assert st.get("pseudo_inhouse") is True
    c = catalog()
    assert c.get("freemium") is False


def test_create_image_png():
    r = create_image("test campfire", size="256x256")
    assert r.ok, r.error
    assert r.path and Path(r.path).is_file()
    assert r.path.endswith(".png")
    assert r.freemium is False


def test_create_pdf():
    r = create_pdf("Dissertation abstract line", title="Test", pages=2)
    assert r.ok, r.error
    assert r.path and Path(r.path).is_file()
    assert r.path.endswith(".pdf")


def test_create_graphics_svg():
    r = create_graphics("mesh diagram", kind="diagram", size="512x384")
    assert r.ok, r.error
    assert any(p.endswith(".svg") or p.endswith(".png") for p in r.paths)


def test_create_video_gif():
    r = create_video("motion test", frames=4, size="320x180", fps=2)
    assert r.ok, r.error
    assert r.path and Path(r.path).is_file()


def test_create_dispatcher():
    r = create("pdf", "hello pages", pages=1)
    assert r.ok
    assert r.modality == "pdf"
