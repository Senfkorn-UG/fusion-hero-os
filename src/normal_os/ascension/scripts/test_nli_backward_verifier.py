"""Tests für nli_backward_verifier (Stufe 2)."""

from __future__ import annotations

import os
import sys

_CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from nli_backward_verifier import (  # noqa: E402
    attribute_span,
    extract_sentences,
    parse_sources,
    verify_text,
)


SOURCES = [
    {
        "id": "policy_1",
        "title": "Refund Policy",
        "snippet": (
            "Customers may request a full refund within 30 days of purchase. "
            "The refund rate in 2025 was 4.2 percent across all product lines."
        ),
    }
]


def test_parse_sources_from_context():
    docs = parse_sources({"sources": SOURCES})
    assert len(docs) == 1
    assert docs[0].id == "policy_1"
    assert "30 days" in docs[0].text


def test_extract_sentences_skips_soft_lines():
    text = "[model] Vielleicht könnte das relevant sein.\nDie Rückerstattung ist innerhalb von 30 Tagen möglich."
    sents = extract_sentences(text)
    assert any("30 Tagen" in s for s in sents)


def test_attribute_span_finds_overlap():
    sentence = "Customers may request a full refund within 30 days of purchase."
    docs = parse_sources({"sources": SOURCES})
    attr = attribute_span(sentence, docs)
    assert attr is not None
    assert attr.source_id == "policy_1"
    assert attr.overlap_score >= 0.3


def test_verify_entails_supported_sentence():
    output = (
        "Laut der Policy können Kunden innerhalb von 30 days eine full refund anfordern. "
        "Die refund rate betrug 4.2 percent im Jahr 2025."
    )
    report = verify_text(output, {"sources": SOURCES}, enabled=True)
    assert report.sentences_checked >= 1
    assert report.attribution_rate > 0
    assert not report.skipped


def test_verify_fails_contradiction():
    output = "Die refund rate betrug 99 percent im Jahr 2025 laut interner Auswertung."
    report = verify_text(output, {"sources": SOURCES}, enabled=True)
    labels = [r.label for r in report.results if r.attribution]
    assert "contradicts" in labels or not report.passed


def test_verify_skips_without_sources():
    report = verify_text("Ein langer Satz ohne passende Quelle im Kontext der Prüfung.", {}, enabled=True)
    assert report.skipped
    assert report.passed


def test_agent_control_nli_strategy():
    os.environ["FUSION_AGENT_CONTROL"] = "1"
    os.environ["FUSION_AGENT_CONTROL_STRATEGIES"] = "nli_backward"
    os.environ["FUSION_NLI_VERIFY"] = "1"

    from agent_control import post_dispatch  # noqa: E402

    task = {
        "query": "[cond] Test",
        "dom": "Info",
        "geltung": "cond",
        "sources": SOURCES,
    }
    text = "Customers may request a full refund within 30 days of purchase."
    post = post_dispatch(task, {"response": text})
    nli = next(s for s in post.strategies if s.strategy == "nli_backward")
    assert not nli.details.get("skipped") or nli.details.get("report")


def main():
    test_parse_sources_from_context()
    test_extract_sentences_skips_soft_lines()
    test_attribute_span_finds_overlap()
    test_verify_entails_supported_sentence()
    test_verify_fails_contradiction()
    test_verify_skips_without_sources()
    test_agent_control_nli_strategy()
    print("ALL NLI BACKWARD TESTS PASSED")


if __name__ == "__main__":
    main()
