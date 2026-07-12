"""
nli_backward_verifier.py — Stufe 2: Backward-Pass Grounding gegen RAG-Quellen.

Paradigma B (Juli 2026 SOTA):
  1. Span-Attribution: Satz → [source_id, start, end]
  2. NLI backward-pass: passage ⇒ sentence (entails / contradicts / neutral)

Default: lexikalischer NLI-Proxy (offline, schnell).
Optional: Hugging Face Inference (FUSION_NLI_USE_HF=1 + HUGGINGFACE_API_KEY).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

GELTUNG_SOFT_RE = re.compile(r"\[(model|frag|modell|fragment|bedingt|cond)\]", re.I)
UNCERTAINTY_RE = re.compile(
    r"\b(könnte|könnten|vielleicht|vermutlich|möglicherweise|might|could|may|perhaps)\b",
    re.I,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
NEGATION_RE = re.compile(
    r"\b(nicht|kein|keine|never|no\b|without|ohne|weder|nor)\b",
    re.I,
)

STOPWORDS = {
    "aber", "als", "also", "and", "auch", "aus", "bei", "das", "dass", "dem", "den",
    "der", "des", "die", "ein", "eine", "für", "hat", "ist", "mit", "nach", "nicht",
    "nur", "oder", "sind", "the", "und", "von", "war", "wenn", "wie", "wird", "with",
    "that", "this", "from", "have", "has", "were", "their", "there", "einer", "eines",
}

HF_NLI_MODEL = os.getenv(
    "FUSION_NLI_HF_MODEL",
    "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
)


def is_enabled() -> bool:
    return os.getenv("FUSION_NLI_VERIFY", "1") == "1"


def use_hf() -> bool:
    return os.getenv("FUSION_NLI_USE_HF", "0") == "1" and bool(
        os.getenv("HUGGINGFACE_API_KEY", "").strip()
    )


def min_attribution_rate() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("FUSION_NLI_MIN_ATTRIBUTION", "0.5"))))
    except ValueError:
        return 0.5


def min_entails_rate() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("FUSION_NLI_MIN_ENTAILS", "0.5"))))
    except ValueError:
        return 0.5


def max_sentences() -> int:
    try:
        return max(1, int(os.getenv("FUSION_NLI_MAX_SENTENCES", "12")))
    except ValueError:
        return 12


def span_window_chars() -> int:
    try:
        return max(80, int(os.getenv("FUSION_NLI_SPAN_WINDOW", "280")))
    except ValueError:
        return 280


def request_timeout() -> float:
    try:
        return max(1.0, float(os.getenv("FUSION_NLI_TIMEOUT", "12")))
    except ValueError:
        return 12.0


@dataclass
class SourceDoc:
    id: str
    text: str
    url: str = ""
    title: str = ""


@dataclass
class SpanAttribution:
    sentence: str
    source_id: str
    start: int
    end: int
    span_text: str
    overlap_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence": self.sentence,
            "source_id": self.source_id,
            "start": self.start,
            "end": self.end,
            "span_text": self.span_text[:240],
            "overlap_score": round(self.overlap_score, 3),
        }


@dataclass
class NLIResult:
    sentence: str
    label: str  # entails | contradicts | neutral | unverifiable
    confidence: float
    attribution: Optional[SpanAttribution] = None
    backend: str = "lexical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence": self.sentence,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "attribution": self.attribution.to_dict() if self.attribution else None,
            "backend": self.backend,
        }


@dataclass
class BackwardGroundingReport:
    passed: bool
    score: float
    attribution_rate: float
    entails_rate: float
    sentences_checked: int
    results: List[NLIResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    skipped: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "attribution_rate": self.attribution_rate,
            "entails_rate": self.entails_rate,
            "sentences_checked": self.sentences_checked,
            "results": [r.to_dict() for r in self.results],
            "notes": self.notes,
            "skipped": self.skipped,
            "error": self.error,
        }


def _significant_terms(text: str) -> Set[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]{4,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def parse_sources(context: Optional[Dict[str, Any]]) -> List[SourceDoc]:
    if not context:
        return []
    docs: List[SourceDoc] = []
    keys = ("sources", "references", "retrieved_docs", "documents", "context_chunks")
    raw_items: List[Any] = []
    for key in keys:
        val = context.get(key)
        if isinstance(val, list) and val:
            raw_items.extend(val)
    if not raw_items:
        rag = context.get("rag")
        if isinstance(rag, dict):
            chunks = rag.get("chunks") or rag.get("documents")
            if isinstance(chunks, list):
                raw_items.extend(chunks)

    for i, item in enumerate(raw_items):
        if isinstance(item, str) and item.strip():
            docs.append(SourceDoc(id=f"doc_{i}", text=item.strip()))
        elif isinstance(item, dict):
            text = str(
                item.get("text")
                or item.get("snippet")
                or item.get("content")
                or item.get("body")
                or ""
            ).strip()
            if not text:
                continue
            sid = str(item.get("id") or item.get("source_id") or f"doc_{i}")
            docs.append(
                SourceDoc(
                    id=sid,
                    text=text,
                    url=str(item.get("url") or ""),
                    title=str(item.get("title") or ""),
                )
            )
    return docs


def extract_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    for block in text.splitlines():
        block = block.strip()
        if not block or GELTUNG_SOFT_RE.search(block):
            continue
        if UNCERTAINTY_RE.search(block) and len(block) < 120:
            continue
        for part in SENTENCE_SPLIT_RE.split(block):
            s = part.strip()
            if len(s) < 25:
                continue
            if s.startswith(("#", "-", "*", "[")):
                continue
            sentences.append(s[:400])
    return sentences[: max_sentences()]


def _span_candidates(doc_text: str, window: int) -> List[Tuple[int, int, str]]:
    text = doc_text.strip()
    if not text:
        return []
    if len(text) <= window:
        return [(0, len(text), text)]
    spans: List[Tuple[int, int, str]] = []
    step = max(40, window // 2)
    for start in range(0, len(text), step):
        end = min(len(text), start + window)
        chunk = text[start:end]
        if chunk.strip():
            spans.append((start, end, chunk))
        if end >= len(text):
            break
    return spans


def attribute_span(sentence: str, docs: Sequence[SourceDoc]) -> Optional[SpanAttribution]:
    terms = _significant_terms(sentence)
    if not terms:
        return None

    best: Optional[SpanAttribution] = None
    best_score = 0.0
    window = span_window_chars()

    for doc in docs:
        for start, end, chunk in _span_candidates(doc.text, window):
            chunk_l = chunk.lower()
            hits = sum(1 for t in terms if t in chunk_l)
            score = hits / len(terms)
            if score > best_score:
                best_score = score
                best = SpanAttribution(
                    sentence=sentence,
                    source_id=doc.id,
                    start=start,
                    end=end,
                    span_text=chunk,
                    overlap_score=score,
                )
    if best and best_score >= 0.2:
        return best
    return None


def _lexical_nli(sentence: str, span_text: str) -> Tuple[str, float]:
    """Offline NLI-Proxy: passage ⇒ sentence."""
    s_terms = _significant_terms(sentence)
    p_terms = _significant_terms(span_text)
    if not s_terms:
        return "unverifiable", 0.0

    overlap = len(s_terms & p_terms) / len(s_terms)
    s_nums = set(NUMBER_RE.findall(sentence))
    p_nums = set(NUMBER_RE.findall(span_text))
    if s_nums and p_nums and not s_nums.issubset(p_nums):
        return "contradicts", min(0.95, 0.55 + overlap)

    s_neg = bool(NEGATION_RE.search(sentence))
    p_neg = bool(NEGATION_RE.search(span_text))
    if s_neg != p_neg and overlap >= 0.35:
        return "contradicts", min(0.9, 0.5 + overlap)

    if overlap >= 0.55:
        return "entails", min(0.98, 0.45 + overlap)
    if overlap >= 0.3:
        return "neutral", 0.35 + overlap * 0.4
    return "unverifiable", overlap


def _hf_nli(premise: str, hypothesis: str, timeout: float) -> Optional[Tuple[str, float]]:
    """Optional Hugging Face zero-shot NLI."""
    token = os.getenv("HUGGINGFACE_API_KEY", "").strip()
    if not token:
        return None
    try:
        import httpx

        resp = httpx.post(
            f"https://api-inference.huggingface.co/models/{HF_NLI_MODEL}",
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": f"{premise} </s></s> {hypothesis}"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not isinstance(data, list) or not data:
            return None
        labels = data[0] if isinstance(data[0], list) else data
        if not labels:
            return None
        top = max(labels, key=lambda x: float(x.get("score", 0)))
        raw = str(top.get("label", "")).upper()
        score = float(top.get("score", 0))
        if "ENTAIL" in raw or raw == "LABEL_0":
            return "entails", score
        if "CONTRAD" in raw or raw == "LABEL_2":
            return "contradicts", score
        return "neutral", score
    except Exception:
        return None


def classify_nli(sentence: str, attribution: SpanAttribution) -> NLIResult:
    premise = attribution.span_text
    if use_hf():
        hf = _hf_nli(premise, sentence, request_timeout())
        if hf:
            label, conf = hf
            return NLIResult(sentence, label, conf, attribution, backend="huggingface")
    label, conf = _lexical_nli(sentence, premise)
    return NLIResult(sentence, label, conf, attribution, backend="lexical")


def verify_text(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    enabled: Optional[bool] = None,
) -> BackwardGroundingReport:
    """Backward-pass gegen bereitgestellte Quellen."""
    if enabled is None:
        enabled = is_enabled()
    if not enabled:
        return BackwardGroundingReport(
            passed=True, score=1.0, attribution_rate=0.0, entails_rate=0.0,
            sentences_checked=0, skipped=True, notes=["nli_disabled"],
        )

    check_text = (text or "").strip()
    if len(check_text) < 40:
        return BackwardGroundingReport(
            passed=True, score=1.0, attribution_rate=0.0, entails_rate=0.0,
            sentences_checked=0, skipped=True, notes=["text_too_short"],
        )

    docs = parse_sources(context)
    if not docs:
        return BackwardGroundingReport(
            passed=True, score=1.0, attribution_rate=0.0, entails_rate=0.0,
            sentences_checked=0, skipped=True, notes=["no_source_documents"],
        )

    sentences = extract_sentences(check_text)
    if not sentences:
        return BackwardGroundingReport(
            passed=True, score=1.0, attribution_rate=0.0, entails_rate=0.0,
            sentences_checked=0, skipped=True, notes=["no_checkable_sentences"],
        )

    results: List[NLIResult] = []
    attributed = 0
    entails = 0
    contradictions = 0

    for sentence in sentences:
        attr = attribute_span(sentence, docs)
        if not attr:
            results.append(NLIResult(sentence, "unverifiable", 0.0, None, "none"))
            continue
        attributed += 1
        nli = classify_nli(sentence, attr)
        results.append(nli)
        if nli.label == "entails":
            entails += 1
        elif nli.label == "contradicts":
            contradictions += 1

    n = len(sentences)
    attr_rate = attributed / n
    entails_rate = entails / max(attributed, 1)
    neutral_ok = sum(1 for r in results if r.label == "neutral") / max(attributed, 1)

    score = 0.5 * attr_rate + 0.4 * entails_rate + 0.1 * (1.0 - contradictions / max(n, 1))
    passed = (
        contradictions == 0
        and attr_rate >= min_attribution_rate()
        and (entails_rate >= min_entails_rate() or (entails_rate + neutral_ok) >= min_entails_rate())
    )

    notes: List[str] = []
    if attr_rate < min_attribution_rate():
        notes.append(f"Attribution {attr_rate:.0%} unter Schwelle {min_attribution_rate():.0%}")
    if entails_rate < min_entails_rate():
        notes.append(f"Entails {entails_rate:.0%} unter Schwelle {min_entails_rate():.0%}")
    if contradictions:
        notes.append(f"{contradictions} widersprüchliche Satz-Span-Paare")
    if use_hf():
        notes.append(f"HF-NLI aktiv ({HF_NLI_MODEL})")
    else:
        notes.append("Lexikalischer NLI-Proxy (offline); HF mit FUSION_NLI_USE_HF=1")

    return BackwardGroundingReport(
        passed=passed,
        score=round(score, 3),
        attribution_rate=round(attr_rate, 3),
        entails_rate=round(entails_rate, 3),
        sentences_checked=n,
        results=results,
        notes=notes,
    )
