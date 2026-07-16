#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract Operator-person (Urban) from operative role — full automation.

What this does:
  1. Ensures ``~/.fusion/operator/identity.local.json`` vault exists (empty person fields).
  2. Scans operative surfaces for hard-coded legal/publication person tokens.
  3. Writes a public-safe status report under ``artifacts/`` and operator-local detail.
  4. Optionally migrates known vault fields from env without printing secrets.

Does **not** rewrite dissertation publication documents (author there is correct).
Does **not** put legal names into the git tree.

Usage::

    python scripts/extract_operator_urban.py
    python scripts/extract_operator_urban.py --json
    python scripts/extract_operator_urban.py --bind-from-env
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Tokens assembled so this script itself does not embed full legal name as a
# single contiguous default for re-injection into code — patterns are for scan.
_SCAN_PATTERNS = [
    re.compile(r"Stephan\s+Hagen\s+Urban", re.I),
    re.compile(r"\bStephan\s+Urban\b", re.I),
    re.compile(r"\bHagen\s+Urban\b", re.I),
    re.compile(r"StephanUrban1", re.I),
    re.compile(r"Stephan_Hagen_Urban"),
]

# Operative trees that should stay person-clean (role=operator only)
OPERATIVE_PREFIXES = (
    "fusion_hero_os/",
    "ascension_os/",
    "03_Code/Dashboard/",
    "kernel/",
    "infra/k8s/",
)

# Publication trees may keep author (not "extraction targets" for delete)
PUBLICATION_PREFIXES = (
    "docs/dissertation/",
    "docs/training/",
    "docs/kompendium/",
    "04_Buch_und_Archiv/",
    "scripts/generate_dissertation",
    "scripts/expand_dissertation",
    "scripts/band3_academia",
    "scripts/build_geisteskrankheiten",
    "scripts/build_heroische",
)

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "legacy_sources",
    "archiv",
    "archive",
    "06_Master_Archive",
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(p: Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def _under(rel: str, prefixes: tuple) -> bool:
    return any(rel.startswith(p) for p in prefixes)


def scan_tree() -> Dict[str, Any]:
    hits_operative: List[Dict[str, Any]] = []
    hits_publication: List[Dict[str, Any]] = []
    hits_other: List[Dict[str, Any]] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".ps1",
            ".txt",
            ".toml",
        }:
            continue
        rel = _rel(path)
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue
        for pat in _SCAN_PATTERNS:
            for m in pat.finditer(text):
                # line number
                line_no = text.count("\n", 0, m.start()) + 1
                entry = {
                    "path": rel,
                    "line": line_no,
                    "match": m.group(0)[:80],
                    "rule": pat.pattern[:40],
                }
                if _under(rel, OPERATIVE_PREFIXES):
                    hits_operative.append(entry)
                elif _under(rel, PUBLICATION_PREFIXES):
                    hits_publication.append(entry)
                else:
                    hits_other.append(entry)
                break  # one hit class per file line enough for status

    return {
        "operative_hits": hits_operative,
        "publication_hits_count": len(hits_publication),
        "other_hits_count": len(hits_other),
        "operative_count": len(hits_operative),
        "operative_clean": len(hits_operative) == 0,
    }


def bind_from_env() -> Dict[str, Any]:
    """Optional: seed vault from env without logging values."""
    from fusion_hero_os.core.operator_identity import VAULT_PATH, save_identity_template

    save_identity_template(force=False)
    legal = os.environ.get("FUSION_AUTHOR_LEGAL_NAME", "").strip()
    pub = os.environ.get("FUSION_AUTHOR_PUBLICATION_NAME", "").strip()
    handle = os.environ.get("FUSION_AUTHOR_ACADEMIA_HANDLE", "").strip()
    if not (legal or pub or handle):
        return {"ok": True, "bound": False, "note": "no FUSION_AUTHOR_* env set"}
    data = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    author = data.setdefault("author", {})
    if legal:
        author["legal_name"] = legal
    if pub:
        author["publication_name"] = pub
    if handle:
        author["academia_handle"] = handle
    author["bind_to_publication"] = os.environ.get("FUSION_AUTHOR_BIND", "0") in (
        "1",
        "true",
        "yes",
    )
    data["extracted_at"] = _utc()
    VAULT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "bound": True,
        "vault": str(VAULT_PATH),
        "fields_set": {
            "legal_name": bool(legal),
            "publication_name": bool(pub),
            "academia_handle": bool(handle),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract Operator person from role")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bind-from-env", action="store_true")
    ap.add_argument("--init-vault", action="store_true", default=True)
    args = ap.parse_args()

    from fusion_hero_os.core.operator_identity import (
        extract_status,
        save_identity_template,
    )

    vault = save_identity_template(force=False)
    scan = scan_tree()
    bind = bind_from_env() if args.bind_from_env else {"ok": True, "bound": False}
    status = extract_status()

    report = {
        "ok": scan["operative_clean"],
        "action": "extract_operator_urban",
        "ts": _utc(),
        "platform": "10.0.0",
        "membrane": status.get("membrane"),
        "vault": str(vault),
        "status": status,
        "scan": {
            "operative_clean": scan["operative_clean"],
            "operative_count": scan["operative_count"],
            "operative_hits": scan["operative_hits"][:50],
            "publication_hits_count": scan["publication_hits_count"],
            "other_hits_count": scan["other_hits_count"],
            "note": (
                "Publication hits are expected (dissertation author). "
                "Operative hits must be zero after extraction."
            ),
        },
        "bind": bind,
        "rules": [
            "Runtime role = operator (abstract)",
            "Legal person only in ~/.fusion/operator/identity.local.json or publication docs",
            "Comädchen / mesh / agents address role only",
            "FUSION_AUTHOR_BIND=1 required to surface vault author in tools",
        ],
    }

    # public artifact (no legal names)
    art = ROOT / "artifacts" / "2026-07-16_operator_urban_extracted.md"
    lines = [
        "# Operator Urban — Extraction Report",
        "",
        f"**UTC:** {report['ts']}",
        f"**Platform:** Fusion Hero OS v{report['platform']}",
        f"**Membrane:** `{report['membrane']}`",
        f"**Operative clean:** **{scan['operative_clean']}** "
        f"({scan['operative_count']} hits in operative prefixes)",
        f"**Publication surface hits (expected):** {scan['publication_hits_count']}",
        f"**Other tree hits:** {scan['other_hits_count']}",
        f"**Vault:** `{vault}` (git-ignored via ~/.fusion/)",
        "",
        "## Separation",
        "",
        "| Layer | Identity |",
        "|-------|----------|",
        "| Runtime / mesh / Comädchen | role=`operator` |",
        "| Operator-local vault | optional legal/publication bind |",
        "| Dissertation / Academia | author (publication surface) |",
        "",
        "## Rules",
        "",
    ]
    for r in report["rules"]:
        lines.append(f"- {r}")
    lines.extend(
        [
            "",
            "## CLI",
            "",
            "```powershell",
            "python -m fusion_hero_os.core.operator_identity --status",
            "python scripts/extract_operator_urban.py",
            "# optional local bind (never commit):",
            '$env:FUSION_AUTHOR_LEGAL_NAME="…"',
            '$env:FUSION_AUTHOR_PUBLICATION_NAME="…"',
            '$env:FUSION_AUTHOR_BIND="1"',
            "python scripts/extract_operator_urban.py --bind-from-env",
            "```",
            "",
            "## Operative hits (must be empty)",
            "",
        ]
    )
    if scan["operative_hits"]:
        for h in scan["operative_hits"][:30]:
            lines.append(f"- `{h['path']}:{h['line']}` — `{h['match']}`")
    else:
        lines.append("_none — person extracted from operative package._")
    lines.append("")
    art.write_text("\n".join(lines), encoding="utf-8")
    report["artifact"] = str(art)

    # private detail
    priv = Path.home() / ".fusion" / "operator" / "extract_report.json"
    priv.parent.mkdir(parents=True, exist_ok=True)
    priv.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["private_report"] = str(priv)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"membrane: {report['membrane']}")
        print(f"operative_clean: {scan['operative_clean']} (hits={scan['operative_count']})")
        print(f"publication_hits: {scan['publication_hits_count']} (expected non-zero)")
        print(f"vault: {vault}")
        print(f"artifact: {art}")
        if scan["operative_hits"]:
            print("OPERATIVE HITS:")
            for h in scan["operative_hits"][:20]:
                print(f"  {h['path']}:{h['line']}  {h['match']}")
    return 0 if scan["operative_clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
