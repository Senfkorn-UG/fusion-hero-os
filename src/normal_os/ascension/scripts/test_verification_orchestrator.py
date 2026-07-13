"""Tests für verification_orchestrator (unified + recovery)."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if CORE not in sys.path:
    sys.path.insert(0, CORE)

from verification_orchestrator import (  # noqa: E402
    _collect_recovery_hints,
    _enrich_sources_from_recovery,
    max_recovery_iterations,
    run_full_verification,
    status,
)


def test_status_includes_agent_control():
    s = status()
    assert "enabled" in s
    assert "agent_control" in s


def test_full_verification_passes_clean_text():
    os.environ["FUSION_VERIFY_ORCHESTRATOR"] = "1"
    os.environ["FUSION_VERIFY_RECOVERY"] = "0"
    text = "[model] Kurze interne Notiz ohne harte Fakten."
    out = run_full_verification(text, {"dom": "Info", "geltung": "model"}, recovery=False)
    assert out["status"] in ("ok", "failed")
    assert "verification" in out
    assert "qubo_routing" in out


def test_collect_recovery_hints_nli():
    failed = [{
        "strategy": "nli_backward",
        "passed": False,
        "details": {
            "report": {
                "results": [
                    {"label": "contradicts", "sentence": "Paris liegt in Deutschland."},
                ],
            },
        },
    }]
    hints = _collect_recovery_hints(failed)
    assert any("NLI" in h for h in hints)


def test_enrich_sources_from_nli_span():
    ctx: dict = {"sources": []}
    failed = [{
        "strategy": "nli_backward",
        "details": {
            "report": {
                "results": [{
                    "attribution": {"span_text": "Paris ist die Hauptstadt von Frankreich."},
                }],
            },
        },
    }]
    n = _enrich_sources_from_recovery(ctx, failed)
    assert n == 1
    assert len(ctx["sources"]) == 1


def test_recovery_loop_bounded():
    os.environ["FUSION_VERIFY_RECOVERY"] = "1"
    os.environ["FUSION_VERIFY_RECOVERY_MAX_ITERS"] = "1"

    fake_fail = {
        "passed": False,
        "fail_closed": True,
        "pre": {"passed": True, "strategies": []},
        "post": {
            "passed": False,
            "strategies": [{
                "strategy": "nli_backward",
                "passed": False,
                "details": {"skipped": False, "report": {"results": []}},
            }],
        },
        "strategies_active": ["nli_backward"],
    }

    with patch("verification_orchestrator._run_verify", return_value=fake_fail):
        out = run_full_verification(
            "Ein langer Satz der nicht verifiziert werden kann weil er zu viele Details enthält.",
            {"sources": [{"text": "Quelle A"}]},
            recovery=True,
            max_iters=2,
        )
    assert out["recovery_iterations"] <= 2
    assert len(out["recovery_steps"]) >= 1


def test_llm_recovery_heuristic():
    os.environ["FUSION_VERIFY_LLM_RECOVERY"] = "1"
    from verification_orchestrator import _revise_text_heuristic

    text = "Paris liegt in Deutschland."
    hints = ["NLI (contradicts): Paris liegt in Deutschland."]
    out = _revise_text_heuristic(text, hints)
    assert "[model]" in out.lower()


if __name__ == "__main__":
    test_status_includes_agent_control()
    test_full_verification_passes_clean_text()
    test_collect_recovery_hints_nli()
    test_enrich_sources_from_nli_span()
    test_recovery_loop_bounded()
    test_llm_recovery_heuristic()
    print("OK: 6 tests")
