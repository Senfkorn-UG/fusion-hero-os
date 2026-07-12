"""
verification_orchestrator.py — Unified Verification + Recovery Loop.

Kombiniert agent_control (alle Strategien), QUBO-Routing und budget-bounded Recovery.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from verification_qubo_synthesis import TaskProfile, synthesize_verification_pipeline
except ImportError:
    from core.verification_qubo_synthesis import TaskProfile, synthesize_verification_pipeline  # type: ignore


def is_enabled() -> bool:
    return os.getenv("FUSION_VERIFY_ORCHESTRATOR", "1") == "1"


def recovery_enabled() -> bool:
    return os.getenv("FUSION_VERIFY_RECOVERY", "1") == "1"


def max_recovery_iterations() -> int:
    try:
        return max(0, min(5, int(os.getenv("FUSION_VERIFY_RECOVERY_MAX_ITERS", "2"))))
    except ValueError:
        return 2


def llm_recovery_enabled() -> bool:
    return os.getenv("FUSION_VERIFY_LLM_RECOVERY", "1") == "1"


@dataclass
class RecoveryStep:
    iteration: int
    action: str
    hints: List[str] = field(default_factory=list)
    sources_added: int = 0
    text_revised: bool = False
    revised_text: str = ""
    passed: bool = False
    verification: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "action": self.action,
            "hints": self.hints,
            "sources_added": self.sources_added,
            "text_revised": self.text_revised,
            "revised_text": self.revised_text[:500] if self.revised_text else "",
            "passed": self.passed,
            "verification": self.verification,
        }


def _task_profile_from_context(context: Optional[Dict[str, Any]]) -> TaskProfile:
    ctx = context or {}
    sources = ctx.get("sources") or ctx.get("references") or []
    text = str(ctx.get("text") or ctx.get("query") or "")
    return TaskProfile(
        stakes=str(ctx.get("stakes") or os.getenv("FUSION_VERIFY_STAKES", "medium")),
        latency_budget_ms=int(ctx.get("latency_budget_ms") or os.getenv("FUSION_VERIFY_LATENCY_MS", "900")),
        has_retrieved_docs=bool(ctx.get("has_retrieved_docs", bool(sources))),
        needs_real_world=bool(ctx.get("needs_real_world", True)),
        claim_count=int(ctx.get("claim_count") or max(1, len(text) // 400)),
        output_chars=len(text),
    )


def _failed_post_strategies(verification: Dict[str, Any]) -> List[Dict[str, Any]]:
    post = verification.get("post") or {}
    return [
        s for s in (post.get("strategies") or [])
        if not s.get("passed") and not (s.get("details") or {}).get("skipped")
    ]


def _collect_recovery_hints(failed: List[Dict[str, Any]]) -> List[str]:
    hints: List[str] = []
    for strat in failed:
        name = strat.get("strategy", "")
        details = strat.get("details") or {}
        report = details.get("report") or {}

        if name == "nli_backward":
            for item in report.get("results") or []:
                label = item.get("label")
                sentence = (item.get("sentence") or "")[:200]
                if label in ("contradicts", "neutral", "unverifiable") and sentence:
                    hints.append(f"NLI ({label}): {sentence}")

        elif name == "echtwelt":
            for check in report.get("checks") or []:
                if check.get("status") in ("unverified", "contradicted"):
                    claim = (check.get("claim") or "")[:200]
                    if claim:
                        hints.append(f"Echtwelt ({check.get('status')}): {claim}")

        elif name == "provenance":
            missing = report.get("missing") or []
            if missing:
                hints.append(f"Provenance fehlt: {', '.join(str(m) for m in missing[:5])}")

        elif name in ("geltung", "peer_review", "meta"):
            reason = details.get("reason") or strat.get("error") or name
            hints.append(f"{name}: {reason}")

    return hints[:12]


def _enrich_sources_from_recovery(
    context: Dict[str, Any],
    failed: List[Dict[str, Any]],
) -> int:
    """Ergänzt sources aus Verifikations-Evidence (budget-bounded, kein LLM)."""
    existing = list(context.get("sources") or [])
    seen = {str(s.get("text", s) if isinstance(s, dict) else s)[:80] for s in existing}
    added = 0

    for strat in failed:
        details = strat.get("details") or {}
        report = details.get("report") or {}

        if strat.get("strategy") == "nli_backward":
            for item in report.get("results") or []:
                attr = item.get("attribution") or {}
                span = (attr.get("span_text") or "").strip()
                if span and span[:80] not in seen:
                    existing.append({"text": span, "source": "recovery_nli_span"})
                    seen.add(span[:80])
                    added += 1

        elif strat.get("strategy") == "echtwelt":
            for check in report.get("checks") or []:
                if check.get("status") == "verified":
                    evidence = (check.get("evidence") or "").strip()
                    if evidence and evidence[:80] not in seen:
                        existing.append({"text": evidence, "source": "recovery_echtwelt"})
                        seen.add(evidence[:80])
                        added += 1

    if added:
        context["sources"] = existing
        context["recovery_sources_added"] = context.get("recovery_sources_added", 0) + added
    return added


def _retrieve_web_sources(hints: List[str], timeout: float = 6.0) -> List[Dict[str, str]]:
    """Re-retrieve: DuckDuckGo für Echtwelt/NLI-Hinweise."""
    sources: List[Dict[str, str]] = []
    seen: set = set()
    try:
        from echtwelt_verifier import _search_ddg, _ddg_corpus
    except ImportError:
        try:
            from core.echtwelt_verifier import _search_ddg, _ddg_corpus  # type: ignore
        except ImportError:
            return sources

    for hint in hints[:6]:
        query = hint.split(":", 1)[-1].strip()[:180]
        if len(query) < 8:
            continue
        try:
            data = _search_ddg(query, timeout)
            corpus = _ddg_corpus(data).strip()
            if corpus and corpus[:80] not in seen:
                sources.append({"text": corpus[:1200], "source": "recovery_ddg", "query": query})
                seen.add(corpus[:80])
        except Exception:
            continue
    return sources


def _revise_text_heuristic(text: str, hints: List[str]) -> str:
    """Fallback: weiche Formulierung für problematische Sätze."""
    lines = text.splitlines()
    out: List[str] = []
    for line in lines:
        soft = line
        for hint in hints:
            fragment = hint.split(":", 1)[-1].strip()
            if len(fragment) > 12 and fragment in line and "[model]" not in line.lower():
                soft = f"[model] {line}"
                break
        out.append(soft)
    return "\n".join(out)


def _revise_text_llm(text: str, hints: List[str], sources: List[Dict[str, Any]]) -> tuple[str, str]:
    """
    LLM-Revise: Quellen + Hinweise → korrigierte Antwort.
    Returns (revised_text, backend_used).
    """
    src_block = "\n".join(
        f"- {(s.get('text') or '')[:400]}"
        for s in (sources or [])[:8]
        if isinstance(s, dict)
    )
    hint_block = "\n".join(f"- {h}" for h in hints[:10])
    prompt = (
        "Korrigiere den Antworttext anhand der Quellen. "
        "Entferne oder markiere unbelegte Aussagen mit [model]. "
        "Gib nur den korrigierten Text zurück.\n\n"
        f"HINWEISE:\n{hint_block}\n\nQUELLEN:\n{src_block}\n\nTEXT:\n{text[:4000]}"
    )

    # 1) Ollama
    ollama = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        import httpx

        model = os.getenv("FUSION_OLLAMA_MODEL", "llama3.2")
        r = httpx.post(
            f"{ollama.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=float(os.getenv("FUSION_VERIFY_LLM_TIMEOUT", "45")),
        )
        if r.status_code == 200:
            out = (r.json().get("response") or "").strip()
            if len(out) > 20:
                return out, "ollama"
    except Exception:
        pass

    # 2) Local Llama
    try:
        from local_llama import get_local_llama

        llama = get_local_llama()
        if llama.active:
            out = llama.generate(prompt, system="Du bist ein Verifikations-Editor. Nur korrigierter Text.")
            if out and len(out.strip()) > 20:
                return out.strip(), "llama-local"
    except Exception:
        pass

    # 3) Heuristic
    return _revise_text_heuristic(text, hints), "heuristic"


def _run_verify(text: str, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from agent_control import verify_text
    except ImportError:
        from core.agent_control import verify_text  # type: ignore
    return verify_text(text, context)


def run_full_verification(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    recovery: Optional[bool] = None,
    max_iters: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Unified Verification: QUBO-Routing + alle agent_control-Strategien (+ optional Recovery).
    """
    if not is_enabled():
        return {
            "passed": True,
            "status": "skipped",
            "reason": "orchestrator_disabled",
            "ts": time.time(),
        }

    ctx = dict(context or {})
    ctx["text"] = text
    ctx["query"] = text
    profile = _task_profile_from_context(ctx)

    try:
        synthesis = synthesize_verification_pipeline(profile)
        qubo = synthesis.to_dict() if hasattr(synthesis, "to_dict") else {
            "selected_modules": getattr(synthesis, "selected_modules", []),
            "pipeline_stages": getattr(synthesis, "pipeline_stages", []),
            "estimated_latency_ms": getattr(synthesis, "estimated_latency_ms", 0),
        }
    except Exception as exc:
        qubo = {"error": str(exc)}

    do_recovery = recovery if recovery is not None else recovery_enabled()
    limit = max_iters if max_iters is not None else max_recovery_iterations()
    use_llm = llm_recovery_enabled()
    working_text = text

    verification = _run_verify(working_text, ctx)
    recovery_steps: List[RecoveryStep] = []

    if not verification.get("passed") and do_recovery and limit > 0:
        for i in range(1, limit + 1):
            failed = _failed_post_strategies(verification)
            if not failed:
                break

            hints = _collect_recovery_hints(failed)
            added = _enrich_sources_from_recovery(ctx, failed)
            web_sources = _retrieve_web_sources(hints)
            if web_sources:
                ctx.setdefault("sources", [])
                ctx["sources"].extend(web_sources)
                added += len(web_sources)

            revised = False
            backend = ""
            if use_llm and hints:
                working_text, backend = _revise_text_llm(
                    working_text, hints, list(ctx.get("sources") or [])
                )
                revised = working_text != text or i > 0
                ctx["text"] = working_text
                ctx["query"] = working_text

            ctx["recovery_hints"] = hints
            ctx["recovery_iteration"] = i

            verification = _run_verify(working_text, ctx)
            action = "re-retrieve → enrich-sources"
            if use_llm:
                action += f" → llm-revise({backend or 'skip'})"
            action += " → reverify"

            step = RecoveryStep(
                iteration=i,
                action=action,
                hints=hints,
                sources_added=added,
                text_revised=revised,
                revised_text=working_text if revised else "",
                passed=bool(verification.get("passed")),
                verification=verification,
            )
            recovery_steps.append(step)
            if step.passed:
                break

    passed = bool(verification.get("passed"))
    return {
        "passed": passed,
        "status": "ok" if passed else "failed",
        "fail_closed": verification.get("fail_closed"),
        "text_final": working_text,
        "text_revised": working_text != text,
        "verification": verification,
        "qubo_routing": qubo,
        "recovery_enabled": do_recovery,
        "llm_recovery_enabled": use_llm,
        "recovery_steps": [s.to_dict() for s in recovery_steps],
        "recovery_iterations": len(recovery_steps),
        "strategies_active": verification.get("strategies_active"),
        "profile": {
            "stakes": profile.stakes,
            "latency_budget_ms": profile.latency_budget_ms,
            "has_retrieved_docs": profile.has_retrieved_docs,
            "needs_real_world": profile.needs_real_world,
        },
        "ts": time.time(),
    }


def status() -> Dict[str, Any]:
    try:
        from agent_control import status as ac_status
    except ImportError:
        from core.agent_control import status as ac_status  # type: ignore

    return {
        "enabled": is_enabled(),
        "recovery_enabled": recovery_enabled(),
        "llm_recovery_enabled": llm_recovery_enabled(),
        "max_recovery_iterations": max_recovery_iterations(),
        "agent_control": ac_status(),
    }
