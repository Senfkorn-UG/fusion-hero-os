# -*- coding: utf-8 -*-
import sys

import pytest

from fusion_hero_os.core import comaedchen_audio as ca


def test_status_shape():
    s = ca.status()
    assert s.get("ok") is True
    assert s.get("channel") == "comaedchen_audio"
    assert "comet" in s
    assert "audiorelay" in s


@pytest.mark.skipif(
    sys.platform != "win32" or not ca.COMET_EXE.exists(),
    reason="comaedchen_audio activates a real local Comet-Browser process; "
    "only meaningful on the operator's actual Windows machine",
)
def test_activate_no_route_no_surface():
    r = ca.activate(mode="local", open_surface=False, route_audio=False)
    assert r.get("channel") == "comaedchen_audio"
    assert r.get("mode") == "local"
    assert r.get("policy", {}).get("rank") == "nummer_2"
    assert r.get("steps", {}).get("comet", {}).get("ok") is True
    assert r.get("state_path")
