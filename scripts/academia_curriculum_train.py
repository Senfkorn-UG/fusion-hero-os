#!/usr/bin/env python3
"""
Build / refresh Academia-aligned training state from:
  - docs/training/ACADEMIA_CURRICULUM_v1.md (human curriculum)
  - docs/Heroismus/*.md (in-house axioms)
  - optional phone filedrop markers

Does not call Academia login APIs (no keypass). Gmail is used offline via
the curriculum doc (operator-approved mail-derived reading clusters).

Parallel to mesh_cluster_coordinator: places heavy re-embed work on L3 when flagged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "docs" / "training" / "ACADEMIA_CURRICULUM_v1.md"
HEROISMUS = ROOT / "docs" / "Heroismus"
OUT = Path.home() / ".fusion" / "mesh" / "coordination"
PHONE_IN = Path.home() / ".fusion" / "mesh" / "filedrops" / "inbound" / "android"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def load_heroismus() -> List[Dict[str, Any]]:
    items = []
    if not HEROISMUS.is_dir():
        return items
    for p in sorted(HEROISMUS.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        leitsatz = ""
        m = re.search(r"\*\*Leitsatz:\*\*\s*(.+)", text)
        if m:
            leitsatz = m.group(1).strip()
        items.append(
            {
                "id": p.stem,
                "path": str(p.relative_to(ROOT)),
                "chars": len(text),
                "leitsatz": leitsatz[:400],
                "hash": _sha(text),
            }
        )
    return items


def load_curriculum_meta() -> Dict[str, Any]:
    if not CURRICULUM.is_file():
        return {"ok": False, "error": "curriculum missing"}
    text = CURRICULUM.read_text(encoding="utf-8", errors="replace")
    clusters = {
        "existenzphilosophie": bool(re.search(r"Existenzphilosophie", text)),
        "agentic_ai": bool(re.search(r"Agentic AI", text, re.I)),
        "name_collision_gate": bool(re.search(r"Namenskollision", text)),
    }
    # extract markdown links as paper/author hints
    links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", text)
    bullets = [
        line.strip("- ").strip()
        for line in text.splitlines()
        if line.strip().startswith("- ") and len(line) > 8
    ]
    return {
        "ok": True,
        "path": str(CURRICULUM.relative_to(ROOT)),
        "hash": _sha(text),
        "chars": len(text),
        "clusters": clusters,
        "links": [{"label": a, "url": b} for a, b in links],
        "bullet_count": len(bullets),
        "sample_bullets": bullets[:25],
    }


def phone_signal() -> Dict[str, Any]:
    files = []
    if PHONE_IN.is_dir():
        for p in PHONE_IN.rglob("*"):
            if p.is_file():
                files.append(
                    {
                        "name": p.name,
                        "bytes": p.stat().st_size,
                        "mtime": datetime.fromtimestamp(
                            p.stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )
    return {
        "path": str(PHONE_IN),
        "file_count": len(files),
        "files": files[:50],
        "ready": len(files) > 0,
    }


def alignment_score(hero: List[Dict[str, Any]], cur: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic: curriculum clusters present + axioms loaded → training readiness."""
    axioms = len(hero)
    clusters = sum(1 for v in (cur.get("clusters") or {}).values() if v)
    phone = 0
    score = min(1.0, 0.15 * axioms + 0.2 * clusters + 0.1 * phone)
    if cur.get("ok") and axioms >= 4 and clusters >= 2:
        phase = "curriculum_active"
    elif cur.get("ok"):
        phase = "curriculum_partial"
    else:
        phase = "blocked"
    return {
        "score": round(score, 3),
        "phase": phase,
        "axioms_loaded": axioms,
        "clusters_active": clusters,
        "notes": [
            "Gmail reading trail is source for cluster A/B",
            "Public HBV uploads on name profiles not ingested",
            "Phone export missing until filedrop non-empty",
        ],
    }


def build_state() -> Dict[str, Any]:
    hero = load_heroismus()
    cur = load_curriculum_meta()
    phone = phone_signal()
    align = alignment_score(hero, cur)
    return {
        "generated_at": _utc(),
        "epoch": time.time(),
        "account": {
            "display_name": "Stephan Urban",
            "mail_hint": "stephan95g@…",
            "premium": True,
            "public_profile_candidate": "https://independent.academia.edu/StephanUrban1",
            "profile_confidence": "low-medium",
            "profile_note": "Virology uploads likely name collision; confirm with operator",
        },
        "curriculum": cur,
        "heroismus_axioms": hero,
        "phone": phone,
        "alignment": align,
        "training_targets": [
            {
                "id": "sisyphos_cec",
                "from_cluster": "A",
                "inhouse": "Axiom_IV_CEC",
                "status": "active",
            },
            {
                "id": "existenz_1st_tier",
                "from_cluster": "A",
                "inhouse": "Axiom_I_1stTier",
                "status": "active",
            },
            {
                "id": "somatic_embodiment",
                "from_cluster": "A",
                "inhouse": "Axiom_II_Somatic",
                "status": "active",
            },
            {
                "id": "agentic_safety_placement",
                "from_cluster": "B",
                "inhouse": "mesh_service_coordination L1/L3",
                "status": "active",
            },
            {
                "id": "meta_reasoning_orchestrator",
                "from_cluster": "B",
                "inhouse": "heroic_core_orchestrator",
                "status": "active",
            },
        ],
        "placement": {
            "curriculum_refresh": "L1_mainframe",
            "heavy_embed_batch": "L3_cluster",
            "phone_ingest": "L0_edge",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    state = build_state()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "academia_training_state.json"
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    # also stamp next to curriculum
    stamp = ROOT / "docs" / "training" / "academia_training_state.latest.json"
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.quiet:
        print(
            json.dumps(
                {
                    "ok": True,
                    "path": str(path),
                    "phase": state["alignment"]["phase"],
                    "score": state["alignment"]["score"],
                    "axioms": state["alignment"]["axioms_loaded"],
                    "phone_files": state["phone"]["file_count"],
                    "targets": len(state["training_targets"]),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
