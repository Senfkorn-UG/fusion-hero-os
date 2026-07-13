"""
echtwelt_verifier.py — Prüfung von Agent-Output gegen Echtweltquellen.

Extrahiert überprüfbare Aussagen und verifiziert sie gegen:
- Erreichbare URLs im Text
- DuckDuckGo Instant Answers (ohne API-Key)
- Optionale Quellen aus dem Task-Kontext (sources / references)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set
from urllib.parse import urlparse

UNCERTAINTY_RE = re.compile(
    r"\b(könnte|könnten|vielleicht|vermutlich|möglicherweise|might|could|may|perhaps|supposedly)\b",
    re.I,
)
GELTUNG_SOFT_RE = re.compile(r"\[(model|frag|modell|fragment|bedingt|cond)\]", re.I)
URL_RE = re.compile(r"https?://[^\s\]\)<>\"']+", re.I)
DATE_RE = re.compile(r"\b(\d{1,2}\.\s?\d{1,2}\.\s?\d{4}|\d{4}-\d{2}-\d{2})\b")
STAT_RE = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s*(%|Prozent|million|Million|milliarden|Milliarden|EUR|USD|€)\b",
    re.I,
)
FACTUAL_SENT_RE = re.compile(
    r"\b(ist|sind|war|waren|wurde|wurden|gibt es|liegt bei|beträgt|zeigt|laut|according to|statistisch)\b",
    re.I,
)

STOPWORDS = {
    "aber", "alle", "als", "also", "and", "auch", "aus", "bei", "bis", "das", "dass",
    "dem", "den", "der", "des", "die", "ein", "eine", "einem", "einen", "einer",
    "eines", "für", "hat", "hier", "ich", "ist", "mit", "nach", "nicht", "nur",
    "oder", "sind", "sich", "sie", "the", "und", "von", "war", "wenn", "wie", "wird",
    "with", "that", "this", "from", "have", "has", "were", "been", "their", "there",
}


def is_enabled() -> bool:
    return os.getenv("FUSION_ECHTWELT_VERIFY", "1") == "1"


def min_score() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("FUSION_ECHTWELT_MIN_SCORE", "0.5"))))
    except ValueError:
        return 0.5


def request_timeout() -> float:
    try:
        return max(1.0, float(os.getenv("FUSION_ECHTWELT_TIMEOUT", "8")))
    except ValueError:
        return 8.0


def max_claims() -> int:
    try:
        return max(1, int(os.getenv("FUSION_ECHTWELT_MAX_CLAIMS", "5")))
    except ValueError:
        return 5


@dataclass
class Claim:
    text: str
    kind: str
    line: int = 0


@dataclass
class ClaimCheck:
    claim: str
    status: str
    source: str
    evidence: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status,
            "source": self.source,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class EchtweltReport:
    passed: bool
    score: float
    claims_found: int = 0
    claims_verified: int = 0
    claims_unverified: int = 0
    claims_contradicted: int = 0
    checks: List[ClaimCheck] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    skipped: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "claims_found": self.claims_found,
            "claims_verified": self.claims_verified,
            "claims_unverified": self.claims_unverified,
            "claims_contradicted": self.claims_contradicted,
            "checks": [c.to_dict() for c in self.checks],
            "notes": self.notes,
            "skipped": self.skipped,
            "error": self.error,
        }


def _significant_terms(text: str) -> Set[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]{4,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _line_is_soft_claim(line: str) -> bool:
    if not line.strip():
        return True
    if GELTUNG_SOFT_RE.search(line):
        return True
    if UNCERTAINTY_RE.search(line):
        return True
    return False


def extract_claims(text: str) -> List[Claim]:
    """Heuristische Extraktion überprüfbarer Aussagen."""
    claims: List[Claim] = []
    seen: Set[str] = set()

    for url in URL_RE.findall(text):
        key = url.rstrip(".,;)")
        if key not in seen:
            seen.add(key)
            claims.append(Claim(key, "url"))

    for i, line in enumerate(text.splitlines(), 1):
        if _line_is_soft_claim(line):
            continue

        for m in DATE_RE.finditer(line):
            snippet = line.strip()[:200]
            key = f"date:{m.group(1)}:{snippet}"
            if key not in seen:
                seen.add(key)
                claims.append(Claim(snippet, "date", i))

        for m in STAT_RE.finditer(line):
            snippet = line.strip()[:200]
            key = f"stat:{m.group(0)}:{snippet}"
            if key not in seen:
                seen.add(key)
                claims.append(Claim(snippet, "stat", i))

        if FACTUAL_SENT_RE.search(line) and len(line.strip()) >= 30:
            snippet = line.strip()[:200]
            key = f"factual:{snippet}"
            if key not in seen:
                seen.add(key)
                claims.append(Claim(snippet, "factual", i))

    return claims[: max_claims() * 2]


def _context_sources(context: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not context:
        return []
    raw = context.get("sources") or context.get("references") or []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            out.append({"text": item, "url": ""})
        elif isinstance(item, dict):
            out.append(
                {
                    "text": str(item.get("snippet") or item.get("text") or item.get("title") or ""),
                    "url": str(item.get("url") or ""),
                }
            )
    return out


def _match_terms_in_corpus(terms: Set[str], corpus: str) -> float:
    if not terms or not corpus:
        return 0.0
    corpus_l = corpus.lower()
    hits = sum(1 for t in terms if t in corpus_l)
    return hits / len(terms)


def _verify_url(url: str, timeout: float) -> ClaimCheck:
    try:
        import httpx

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ClaimCheck(url, "skipped", "url_parse", "Ungültige URL", 0.0)

        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.head(url)
            if resp.status_code >= 400:
                resp = client.get(url)
            ok = 200 <= resp.status_code < 400
            return ClaimCheck(
                url,
                "verified" if ok else "unverified",
                "url_reachability",
                f"HTTP {resp.status_code}",
                1.0 if ok else 0.0,
            )
    except Exception as exc:
        return ClaimCheck(url, "unverified", "url_reachability", str(exc)[:160], 0.0)


def _search_ddg(query: str, timeout: float) -> Dict[str, Any]:
    import httpx

    resp = httpx.get(
        "https://api.duckduckgo.com/",
        params={
            "q": query[:200],
            "format": "json",
            "no_redirect": 1,
            "skip_disambig": 1,
        },
        timeout=timeout,
        headers={"User-Agent": "FusionHeroOS-EchtweltVerifier/1.0"},
    )
    resp.raise_for_status()
    return resp.json()


def _ddg_corpus(data: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("AbstractText", "Heading", "Answer"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    for topic in data.get("RelatedTopics") or []:
        if isinstance(topic, dict):
            text = topic.get("Text")
            if isinstance(text, str):
                parts.append(text)
            for sub in topic.get("Topics") or []:
                if isinstance(sub, dict) and isinstance(sub.get("Text"), str):
                    parts.append(sub["Text"])
    return " ".join(parts)


def _verify_text_claim(claim: str, context_sources: Sequence[Dict[str, str]], timeout: float) -> ClaimCheck:
    terms = _significant_terms(claim)
    if not terms:
        return ClaimCheck(claim, "skipped", "heuristic", "Keine prüfbaren Schlüsselbegriffe", 0.0)

    best_ratio = 0.0
    best_source = ""
    best_evidence = ""

    for src in context_sources:
        corpus = f"{src.get('text', '')} {src.get('url', '')}"
        ratio = _match_terms_in_corpus(terms, corpus)
        if ratio > best_ratio:
            best_ratio = ratio
            best_source = "task_sources"
            best_evidence = corpus[:160]

    if best_ratio >= 0.35:
        return ClaimCheck(claim, "verified", best_source, best_evidence, best_ratio)

    try:
        data = _search_ddg(claim, timeout)
        corpus = _ddg_corpus(data)
        ratio = _match_terms_in_corpus(terms, corpus)
        if ratio >= 0.3 and corpus.strip():
            return ClaimCheck(claim, "verified", "duckduckgo", corpus[:160], ratio)
        if corpus.strip():
            return ClaimCheck(claim, "unverified", "duckduckgo", corpus[:160], ratio)
        return ClaimCheck(claim, "unverified", "duckduckgo", "Keine Echtwelt-Treffer", 0.0)
    except Exception as exc:
        if best_ratio >= 0.25:
            return ClaimCheck(claim, "verified", "task_sources_fallback", best_evidence, best_ratio)
        return ClaimCheck(claim, "unverified", "duckduckgo", str(exc)[:160], 0.0)


def verify_text(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    enabled: Optional[bool] = None,
) -> EchtweltReport:
    """Prüft Text gegen Echtweltquellen und liefert strukturierten Report."""
    if enabled is None:
        enabled = is_enabled()

    if not enabled:
        return EchtweltReport(passed=True, score=1.0, skipped=True, notes=["echtwelt_disabled"])

    check_text = (text or "").strip()
    if not check_text:
        return EchtweltReport(passed=True, score=1.0, skipped=True, notes=["empty_text"])

    if len(check_text) < 40:
        return EchtweltReport(passed=True, score=1.0, skipped=True, notes=["text_too_short"])

    claims = extract_claims(check_text)[: max_claims()]
    if not claims:
        return EchtweltReport(
            passed=True,
            score=1.0,
            skipped=True,
            notes=["no_verifiable_claims"],
        )

    timeout = request_timeout()
    context_sources = _context_sources(context)
    checks: List[ClaimCheck] = []

    for claim in claims:
        if claim.kind == "url":
            checks.append(_verify_url(claim.text, timeout))
        else:
            checks.append(_verify_text_claim(claim.text, context_sources, timeout))

    verified = sum(1 for c in checks if c.status == "verified")
    unverified = sum(1 for c in checks if c.status == "unverified")
    contradicted = sum(1 for c in checks if c.status == "contradicted")
    actionable = verified + unverified + contradicted

    if actionable == 0:
        score = 1.0
    else:
        score = verified / actionable

    threshold = min_score()
    passed = contradicted == 0 and (score >= threshold or actionable == 0)

    notes: List[str] = []
    if unverified:
        notes.append(f"{unverified} Aussage(n) ohne ausreichende Echtwelt-Bestätigung")
    if contradicted:
        notes.append(f"{contradicted} widersprüchliche Aussage(n)")

    return EchtweltReport(
        passed=passed,
        score=round(score, 3),
        claims_found=len(claims),
        claims_verified=verified,
        claims_unverified=unverified,
        claims_contradicted=contradicted,
        checks=checks,
        notes=notes,
    )
