"""Tests für provenance_trace (Stufe 3)."""

from __future__ import annotations

import os
import sys

_CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core"))
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from provenance_trace import (  # noqa: E402
    build_trace_from_task,
    capture_task_run,
    list_recent,
    verify_trace,
)


SOURCES = [{"id": "doc_a", "snippet": "Fusion Hero OS Version 9.5.0 released July 2026."}]


def test_build_trace_has_otel_and_prov():
    task = {
        "id": "t1",
        "assigned_agent": "test_agent",
        "dom": "Info",
        "query": "Was ist die Version?",
        "sources": SOURCES,
        "tool_calls": [{"name": "search_emails", "status": "ok"}],
    }
    trace = build_trace_from_task(
        task,
        {"response": "Die Version ist 9.5.0."},
        control_pre={"passed": True, "reason": "ok", "strategies": []},
        control_post={"passed": True, "reason": "ok", "strategies": [{"strategy": "echtwelt", "passed": True}]},
    )
    assert trace["trace_id"]
    spans = trace["otel"]["spans"]
    assert len(spans) >= 3
    entities = trace["prov"]["entities"]
    assert any(e.get("subtype") == "AgentOutput" for e in entities)
    assert any(e.get("subtype") == "SourceDocument" for e in entities)
    rels = {r["type"] for r in trace["prov"]["relations"]}
    assert "wasGeneratedBy" in rels
    assert "wasDerivedFrom" in rels


def test_verify_trace_passes_complete():
    task = {
        "id": "t2",
        "assigned_agent": "agent",
        "query": "Test",
        "sources": SOURCES,
    }
    trace = build_trace_from_task(task, {"response": "Antwort mit Kontext."})
    report = verify_trace(trace)
    assert report.completeness >= 0.6
    assert report.trace_id == trace["trace_id"]


def test_capture_task_run_persists():
    os.environ["FUSION_PROV_TRACE"] = "1"
    task = {
        "id": "t3",
        "assigned_agent": "agent",
        "query": "Capture test",
        "sources": SOURCES,
    }
    cap = capture_task_run(task, {"response": "Output text."})
    assert cap["trace_id"]
    assert cap["verification"]["trace_id"] == cap["trace_id"]
    recent = list_recent(5)
    assert any(r["trace_id"] == cap["trace_id"] for r in recent)


def test_agent_control_provenance_strategy():
    os.environ["FUSION_AGENT_CONTROL"] = "1"
    os.environ["FUSION_AGENT_CONTROL_STRATEGIES"] = "provenance"
    os.environ["FUSION_PROV_TRACE"] = "1"

    from agent_control import post_dispatch  # noqa: E402

    task = {
        "query": "[cond] Provenance test",
        "dom": "Info",
        "geltung": "cond",
        "sources": SOURCES,
        "assigned_agent": "unit_test",
    }
    post = post_dispatch(task, {"response": "Fusion Hero OS Version 9.5.0 ist dokumentiert."})
    prov = next(s for s in post.strategies if s.strategy == "provenance")
    assert prov.passed or prov.details.get("skipped")
    assert task.get("trace_id") or task.get("provenance_trace")


def main():
    test_build_trace_has_otel_and_prov()
    test_verify_trace_passes_complete()
    test_capture_task_run_persists()
    test_agent_control_provenance_strategy()
    print("ALL PROVENANCE TESTS PASSED")


if __name__ == "__main__":
    main()
