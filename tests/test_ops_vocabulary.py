# -*- coding: utf-8 -*-
from fusion_hero_os.core.ops_vocabulary import OPS, meaning_of, status


def test_canonical_meanings():
    assert meaning_of("deploy") == "private"
    assert meaning_of("push") == "public"
    assert meaning_of("merge") in ("both_via_timeline", "both")
    assert OPS["deploy"] == "private"
    assert OPS["push"] == "public"


def test_status_vocab():
    st = status()
    assert st["vocabulary"]["deploy"] == "private"
    assert st["vocabulary"]["push"] == "public"
    assert "timeline" in st["vocabulary"]["merge"] or st["vocabulary"]["merge"] == "both_via_timeline"
