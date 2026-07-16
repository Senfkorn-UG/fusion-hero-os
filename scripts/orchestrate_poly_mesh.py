#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perfect poly-mesh algorithm orchestration entrypoint.

Usage::

    python scripts/orchestrate_poly_mesh.py              # plan + dry hooks
    python scripts/orchestrate_poly_mesh.py --execute    # run coordinator + asserts
    python scripts/orchestrate_poly_mesh.py --plan       # plan only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Orchestrate algorithms on poly-mesh")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    from fusion_hero_os.core.poly_mesh_orchestrator import (
        orchestrate,
        plan_only,
        status,
    )

    if args.status:
        r = status()
    elif args.plan:
        r = plan_only()
    else:
        r = orchestrate(execute=args.execute)

    # short public artifact
    art = ROOT / "artifacts" / "2026-07-16_poly_mesh_orchestration.md"
    coh = r.get("coherence") or {}
    lines = [
        "# Poly-Mesh Algorithm Orchestration",
        "",
        f"**UTC:** {datetime.now(timezone.utc).isoformat()}",
        f"**Score:** {coh.get('score')} / 100 · **Grade:** {coh.get('grade')} · **Perfect:** {coh.get('perfect')}",
        f"**Banner:** {r.get('banner')}",
        f"**Sole authority:** {r.get('sole_authority')}",
        f"**Online tiers:** {', '.join(r.get('online_tiers') or [])}",
        f"**Counts:** {json.dumps(r.get('counts') or {})}",
        "",
        "## Waves",
        "",
    ]
    for w in r.get("waves") or []:
        lines.append(f"- Wave {w.get('wave')} **{w.get('name')}**: {len(w.get('ids') or [])} algorithms")
        for i in (w.get("ids") or [])[:12]:
            lines.append(f"  - `{i}`")
    lines.extend(["", "## Violations", ""])
    viol = coh.get("violations") or []
    if viol:
        for v in viol:
            lines.append(f"- {v}")
    else:
        lines.append("_none_")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- force_cluster → L3 only (no silent L1 dual-start)",
            "- control plane → L1",
            "- audio → mesh-only 100.x",
            "- SaaS → membrane, never source of truth",
            "",
            "```powershell",
            "python scripts/orchestrate_poly_mesh.py --execute",
            "python -m fusion_hero_os.core.poly_mesh_orchestrator --plan",
            "```",
            "",
        ]
    )
    art.write_text("\n".join(lines), encoding="utf-8")
    r["artifact"] = str(art)

    print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get("banner"):
        print(r["banner"], file=sys.stderr)
    print(f"artifact: {art}", file=sys.stderr)
    score = (r.get("coherence") or {}).get("score", 0)
    return 0 if score >= 75 else 1


if __name__ == "__main__":
    raise SystemExit(main())
