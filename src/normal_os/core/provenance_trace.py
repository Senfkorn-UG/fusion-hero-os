"""
provenance_trace.py — Stufe 3: Execution Provenance (OpenTelemetry + W3C PROV-DM).

Erfasst Agent-Läufe als auditierbare Traces:
  - OpenTelemetry-kompatible Spans (ohne SDK-Pflicht)
  - W3C PROV-DM: Entity / Activity / Agent / Relation
  - Tool-Calls, Quellen, Verifier-Ergebnisse, Output-Herkunft
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def is_enabled() -> bool:
    return os.getenv("FUSION_PROV_TRACE", "1") == "1"


def min_completeness() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("FUSION_PROV_MIN_COMPLETENESS", "0.6"))))
    except ValueError:
        return 0.6


def store_dir() -> Path:
    raw = os.getenv("FUSION_PROV_STORE_DIR", "")
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[3] / ".fusion" / "provenance"


def max_traces() -> int:
    try:
        return max(50, int(os.getenv("FUSION_PROV_MAX_TRACES", "500")))
    except ValueError:
        return 500


_TRACE_INDEX: Dict[str, Dict[str, Any]] = {}
_TRACE_ORDER: List[str] = []


def _now_ns() -> int:
    return int(time.time() * 1_000_000_000)


def _short_id() -> str:
    return uuid.uuid4().hex[:16]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _ensure_store() -> Path:
    d = store_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _persist_trace(trace: Dict[str, Any]) -> None:
    path = _ensure_store() / "traces.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False, default=str) + "\n")


@dataclass
class Span:
    span_id: str
    name: str
    kind: str = "INTERNAL"
    parent_span_id: Optional[str] = None
    start_time_unix_nano: int = 0
    end_time_unix_nano: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    status_code: str = "OK"

    def to_otel(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "start_time_unix_nano": self.start_time_unix_nano,
            "end_time_unix_nano": self.end_time_unix_nano,
            "attributes": self.attributes,
            "status": {"code": self.status_code},
        }


@dataclass
class ProvenanceReport:
    passed: bool
    score: float
    completeness: float
    trace_id: str
    missing: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    skipped: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "completeness": self.completeness,
            "trace_id": self.trace_id,
            "missing": self.missing,
            "notes": self.notes,
            "skipped": self.skipped,
        }


class TraceBuilder:
    """Baut OTel-Spans + PROV-Graph für einen Agent-Lauf."""

    def __init__(
        self,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        dom: Optional[str] = None,
    ):
        self.trace_id = uuid.uuid4().hex
        self.task_id = task_id or _short_id()
        self.agent = agent or "unknown"
        self.dom = dom or "General"
        self.started_at = time.time()
        self.spans: List[Span] = []
        self.prov_entities: List[Dict[str, Any]] = []
        self.prov_activities: List[Dict[str, Any]] = []
        self.prov_agents: List[Dict[str, Any]] = []
        self.prov_relations: List[Dict[str, Any]] = []
        self._root_span = self._open_span("agent.run", {"task_id": self.task_id, "dom": self.dom})

        self.prov_agents.append({
            "id": f"ag:{self.agent}",
            "type": "prov:SoftwareAgent",
            "label": self.agent,
        })
        self.prov_activities.append({
            "id": f"act:{self._root_span.span_id}",
            "type": "fusion:AgentExecution",
            "started_at": self.started_at,
            "agent_id": f"ag:{self.agent}",
        })

    def _open_span(self, name: str, attrs: Optional[Dict[str, Any]] = None, parent: Optional[str] = None) -> Span:
        sp = Span(
            span_id=_short_id(),
            name=name,
            parent_span_id=parent,
            start_time_unix_nano=_now_ns(),
            attributes=dict(attrs or {}),
        )
        self.spans.append(sp)
        return sp

    def _close_span(self, sp: Span, status: str = "OK", extra: Optional[Dict[str, Any]] = None) -> None:
        sp.end_time_unix_nano = _now_ns()
        sp.status_code = status
        if extra:
            sp.attributes.update(extra)

    def record_query(self, query: str) -> str:
        eid = f"ent:query:{_short_id()}"
        self.prov_entities.append({
            "id": eid,
            "type": "fusion:UserQuery",
            "hash": _sha256_text(query)[:16],
            "chars": len(query),
        })
        sp = self._open_span("agent.query", {"query.chars": len(query)}, self._root_span.span_id)
        self.prov_relations.append({
            "type": "used",
            "activity_id": f"act:{self._root_span.span_id}",
            "entity_id": eid,
        })
        self._close_span(sp)
        return eid

    def record_sources(self, sources: Sequence[Dict[str, Any]]) -> List[str]:
        ids: List[str] = []
        sp = self._open_span("retrieval.sources", {"source.count": len(sources)}, self._root_span.span_id)
        for i, src in enumerate(sources):
            text = str(src.get("text") or src.get("snippet") or src.get("content") or "")
            eid = f"ent:source:{src.get('id', i)}"
            self.prov_entities.append({
                "id": eid,
                "type": "prov:Entity",
                "subtype": "SourceDocument",
                "url": src.get("url", ""),
                "title": src.get("title", ""),
                "hash": _sha256_text(text)[:16] if text else "",
            })
            self.prov_relations.append({
                "type": "used",
                "activity_id": f"act:{self._root_span.span_id}",
                "entity_id": eid,
            })
            ids.append(eid)
        self._close_span(sp)
        return ids

    def record_tool_calls(self, tools: Sequence[Dict[str, Any]]) -> None:
        if not tools:
            return
        sp = self._open_span("agent.tools", {"tool.count": len(tools)}, self._root_span.span_id)
        for t in tools:
            name = str(t.get("name") or t.get("tool") or "tool")
            eid = f"ent:tool:{_short_id()}"
            self.prov_entities.append({
                "id": eid,
                "type": "fusion:ToolResult",
                "tool": name,
                "status": t.get("status", "ok"),
            })
            act_id = f"act:tool:{_short_id()}"
            self.prov_activities.append({
                "id": act_id,
                "type": "fusion:ToolInvocation",
                "tool": name,
                "started_at": t.get("ts", time.time()),
            })
            self.prov_relations.append({"type": "wasGeneratedBy", "entity_id": eid, "activity_id": act_id})
            self.prov_relations.append({
                "type": "wasAssociatedWith",
                "activity_id": act_id,
                "agent_id": f"ag:{self.agent}",
            })
            self.prov_relations.append({
                "type": "used",
                "activity_id": act_id,
                "entity_id": eid,
            })
        self._close_span(sp)

    def record_control(self, phase: str, control: Dict[str, Any]) -> None:
        sp = self._open_span(
            f"verification.{phase}",
            {
                "control.passed": control.get("passed"),
                "control.reason": str(control.get("reason", ""))[:120],
            },
            self._root_span.span_id,
        )
        eid = f"ent:control:{phase}:{_short_id()}"
        self.prov_entities.append({
            "id": eid,
            "type": "fusion:VerificationReceipt",
            "phase": phase,
            "passed": control.get("passed"),
        })
        act_id = f"act:verify:{phase}:{_short_id()}"
        self.prov_activities.append({
            "id": act_id,
            "type": "fusion:VerificationPass",
            "phase": phase,
        })
        self.prov_relations.append({"type": "wasGeneratedBy", "entity_id": eid, "activity_id": act_id})
        for strat in control.get("strategies") or []:
            if isinstance(strat, dict):
                sp.attributes[f"verifier.{strat.get('strategy')}"] = strat.get("passed")
        self._close_span(sp, "OK" if control.get("passed") else "ERROR")

    def record_output(self, text: str, source_entity_ids: Optional[Sequence[str]] = None) -> str:
        eid = f"ent:output:{_short_id()}"
        self.prov_entities.append({
            "id": eid,
            "type": "prov:Entity",
            "subtype": "AgentOutput",
            "hash": _sha256_text(text)[:16],
            "chars": len(text),
        })
        self.prov_relations.append({
            "type": "wasGeneratedBy",
            "entity_id": eid,
            "activity_id": f"act:{self._root_span.span_id}",
        })
        self.prov_relations.append({
            "type": "wasAttributedTo",
            "entity_id": eid,
            "agent_id": f"ag:{self.agent}",
        })
        for sid in source_entity_ids or []:
            self.prov_relations.append({
                "type": "wasDerivedFrom",
                "entity_id": eid,
                "other_entity_id": sid,
            })
        sp = self._open_span(
            "agent.output",
            {"output.chars": len(text), "output.hash": _sha256_text(text)[:16]},
            self._root_span.span_id,
        )
        self._close_span(sp)
        return eid

    def finalize(self) -> Dict[str, Any]:
        self._close_span(self._root_span, extra={"duration_ms": round((time.time() - self.started_at) * 1000, 1)})
        doc = {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "agent": self.agent,
            "dom": self.dom,
            "started_at": self.started_at,
            "finished_at": time.time(),
            "otel": {"spans": [s.to_otel() for s in self.spans]},
            "prov": {
                "entities": self.prov_entities,
                "activities": self.prov_activities,
                "agents": self.prov_agents,
                "relations": self.prov_relations,
            },
        }
        return doc


def _extract_tools(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []
    for key in ("tool_calls", "tools", "mcp_calls"):
        val = task.get(key)
        if isinstance(val, list):
            tools.extend(val)
    trace = task.get("execution_trace")
    if isinstance(trace, dict):
        tc = trace.get("tool_calls")
        if isinstance(tc, list):
            tools.extend(tc)
    return tools


def _extract_sources(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for key in ("sources", "references", "retrieved_docs", "documents"):
        val = task.get(key)
        if isinstance(val, list):
            out.extend(val)
    return out


def build_trace_from_task(
    task: Dict[str, Any],
    result: Any = None,
    *,
    control_pre: Optional[Dict[str, Any]] = None,
    control_post: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Erzeugt vollständigen Trace aus Task + Ergebnis + Kontrolle."""
    agent = str(task.get("assigned_agent") or task.get("agent") or "unknown")
    dom = str(task.get("dom") or "General")
    task_id = str(task.get("id") or task.get("task_id") or _short_id())

    builder = TraceBuilder(task_id=task_id, agent=agent, dom=dom)
    query = str(task.get("query") or task.get("original") or "")
    if query:
        builder.record_query(query)

    source_ids = builder.record_sources(_extract_sources(task))
    builder.record_tool_calls(_extract_tools(task))

    if control_pre:
        builder.record_control("pre", control_pre)
    if control_post:
        builder.record_control("post", control_post)

    output = ""
    if isinstance(result, dict):
        output = str(
            result.get("response")
            or result.get("synthesised_response")
            or result.get("text")
            or ""
        )
    elif isinstance(result, str):
        output = result
    if not output:
        output = str(task.get("response") or task.get("text") or "")

    if output:
        builder.record_output(output, source_entity_ids=source_ids)

    return builder.finalize()


def save_trace(trace: Dict[str, Any]) -> str:
    tid = trace["trace_id"]
    _TRACE_INDEX[tid] = trace
    _TRACE_ORDER.append(tid)
    if len(_TRACE_ORDER) > max_traces():
        old = _TRACE_ORDER.pop(0)
        _TRACE_INDEX.pop(old, None)
    try:
        _persist_trace(trace)
    except Exception:
        pass
    return tid


def get_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    if trace_id in _TRACE_INDEX:
        return _TRACE_INDEX[trace_id]
    path = _ensure_store() / "traces.jsonl"
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            if doc.get("trace_id") == trace_id:
                _TRACE_INDEX[trace_id] = doc
                return doc
    except Exception:
        return None
    return None


def list_recent(limit: int = 20) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for tid in reversed(_TRACE_ORDER[-limit:]):
        tr = _TRACE_INDEX.get(tid)
        if tr:
            items.append({
                "trace_id": tr["trace_id"],
                "task_id": tr.get("task_id"),
                "agent": tr.get("agent"),
                "dom": tr.get("dom"),
                "started_at": tr.get("started_at"),
                "span_count": len(tr.get("otel", {}).get("spans", [])),
            })
    return items


def verify_trace(trace: Dict[str, Any]) -> ProvenanceReport:
    """Prüft Vollständigkeit des Execution-Provenance-Graphs."""
    if not is_enabled():
        return ProvenanceReport(True, 1.0, 1.0, trace.get("trace_id", ""), skipped=True, notes=["prov_disabled"])

    tid = trace.get("trace_id", "")
    missing: List[str] = []
    entities = trace.get("prov", {}).get("entities") or []
    relations = trace.get("prov", {}).get("relations") or []
    spans = trace.get("otel", {}).get("spans") or []

    entity_types = {e.get("subtype") or e.get("type") for e in entities}
    rel_types = {r.get("type") for r in relations}

    checks = {
        "has_output": any(e.get("subtype") == "AgentOutput" for e in entities),
        "has_activity": bool(trace.get("prov", {}).get("activities")),
        "has_agent": bool(trace.get("prov", {}).get("agents")),
        "has_wasGeneratedBy": "wasGeneratedBy" in rel_types,
        "has_spans": len(spans) >= 2,
        "has_verification_span": any(s.get("name", "").startswith("verification.") for s in spans),
    }

    sources = _extract_sources_from_entities(entities)
    if sources:
        checks["has_derived_from"] = "wasDerivedFrom" in rel_types
    else:
        checks["has_derived_from"] = True  # nicht erforderlich ohne Quellen

    score_parts = list(checks.values())
    completeness = sum(1 for v in score_parts if v) / max(len(score_parts), 1)

    for key, ok in checks.items():
        if not ok:
            missing.append(key)

    passed = completeness >= min_completeness() and checks["has_output"] and checks["has_wasGeneratedBy"]
    notes = [
        "OpenTelemetry-Span-Export + W3C PROV-DM JSON",
        f"{len(spans)} spans, {len(entities)} entities, {len(relations)} relations",
    ]
    if sources and "wasDerivedFrom" not in rel_types:
        notes.append("Quellen vorhanden aber wasDerivedFrom fehlt")

    return ProvenanceReport(
        passed=passed,
        score=round(completeness, 3),
        completeness=round(completeness, 3),
        trace_id=tid,
        missing=missing,
        notes=notes,
    )


def _extract_sources_from_entities(entities: Sequence[Dict[str, Any]]) -> List[str]:
    return [e["id"] for e in entities if e.get("subtype") == "SourceDocument"]


def capture_task_run(
    task: Dict[str, Any],
    result: Any = None,
    *,
    control_pre: Optional[Dict[str, Any]] = None,
    control_post: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """High-level: Trace bauen, speichern, Verifikation zurückgeben."""
    trace = build_trace_from_task(task, result, control_pre=control_pre, control_post=control_post)
    save_trace(trace)
    report = verify_trace(trace)
    return {
        "trace_id": trace["trace_id"],
        "trace": trace,
        "verification": report.to_dict(),
    }


def verify_task_context(task: Dict[str, Any], text: str = "") -> ProvenanceReport:
    """Für agent_control-Strategie: Trace aus Task bauen und prüfen."""
    if not is_enabled():
        return ProvenanceReport(True, 1.0, 1.0, "", skipped=True, notes=["prov_disabled"])

    existing = task.get("provenance_trace")
    if isinstance(existing, dict) and existing.get("trace_id"):
        report = verify_trace(existing)
        return report

    trace = build_trace_from_task(
        task,
        {"response": text} if text else None,
        control_pre=task.get("control_pre"),
        control_post=task.get("control_post"),
    )
    save_trace(trace)
    task["provenance_trace"] = trace
    task["trace_id"] = trace["trace_id"]
    return verify_trace(trace)
