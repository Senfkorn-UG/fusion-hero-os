"""Tests für echtwelt_verifier und agent_control echtwelt-Strategie."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

_CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from echtwelt_verifier import extract_claims, verify_text as verify_echtwelt  # noqa: E402


def test_extract_claims_finds_url_and_stat():
    text = (
        "Laut Statistik liegt die Rate bei 42 Prozent.\n"
        "Quelle: https://example.com/report\n"
        "[model] Dies könnte sich ändern."
    )
    claims = extract_claims(text)
    kinds = {c.kind for c in claims}
    assert "url" in kinds
    assert "stat" in kinds


def test_extract_claims_skips_soft_model_lines():
    text = "[model] Dies könnte vielleicht irgendwann relevant werden."
    claims = extract_claims(text)
    assert claims == []


def test_verify_text_skips_short_text():
    report = verify_echtwelt("kurz", enabled=True)
    assert report.passed
    assert report.skipped


def test_verify_text_uses_task_sources():
    text = (
        "Die Fusion Hero OS Version 9.5.0 ist im Repository dokumentiert "
        "und wurde im Juli 2026 veröffentlicht."
    )
    context = {
        "sources": [
            {
                "title": "AscensionOS",
                "snippet": "Fusion Hero OS Version 9.5.0 released July 2026",
                "url": "https://example.com/docs",
            }
        ]
    }
    with patch("echtwelt_verifier._search_ddg") as mock_ddg:
        mock_ddg.return_value = {"AbstractText": "", "RelatedTopics": []}
        report = verify_echtwelt(text, context, enabled=True)
    assert report.claims_found >= 1
    assert report.score > 0


def test_verify_url_reachability_mocked():
    text = "Siehe https://example.com für Details zur aktuellen Version."
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.Client") as mock_client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.head.return_value = mock_resp
        mock_client_cls.return_value = client
        report = verify_echtwelt(text, enabled=True)

    url_checks = [c for c in report.checks if c.source == "url_reachability"]
    assert url_checks
    assert url_checks[0].status == "verified"


def test_agent_control_echtwelt_strategy_post_only():
    os.environ["FUSION_AGENT_CONTROL"] = "1"
    os.environ["FUSION_AGENT_CONTROL_STRATEGIES"] = "echtwelt"
    os.environ["FUSION_ECHTWELT_VERIFY"] = "1"

    from agent_control import post_dispatch, pre_dispatch  # noqa: E402

    task = {"query": "[model] Test", "dom": "Info", "geltung": "model", "id": 1}
    pre = pre_dispatch(task)
    echtwelt_pre = next(s for s in pre.strategies if s.strategy == "echtwelt")
    assert echtwelt_pre.passed
    assert echtwelt_pre.details.get("skipped")

    with patch("echtwelt_verifier.verify_text") as mock_verify:
        from echtwelt_verifier import EchtweltReport

        mock_verify.return_value = EchtweltReport(
            passed=True,
            score=1.0,
            claims_found=0,
            skipped=True,
            notes=["no_verifiable_claims"],
        )
        post = post_dispatch(task, {"response": "[model] Kurze Antwort ohne harte Fakten."})

    echtwelt_post = next(s for s in post.strategies if s.strategy == "echtwelt")
    assert echtwelt_post.passed


def main():
    test_extract_claims_finds_url_and_stat()
    test_extract_claims_skips_soft_model_lines()
    test_verify_text_skips_short_text()
    test_verify_text_uses_task_sources()
    test_verify_url_reachability_mocked()
    test_agent_control_echtwelt_strategy_post_only()
    print("ALL ECHTWELT TESTS PASSED")


if __name__ == "__main__":
    main()
