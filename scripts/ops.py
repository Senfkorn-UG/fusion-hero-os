#!/usr/bin/env python3
"""
Unified ops CLI — deploy=private · push=public · merge=both(timeline)

  python scripts/ops.py vocabulary
  python scripts/ops.py deploy
  python scripts/ops.py push [--dry]
  python scripts/ops.py merge
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fusion ops: deploy/push/merge")
    ap.add_argument(
        "command",
        choices=["vocabulary", "vocab", "deploy", "push", "merge"],
    )
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    cmd = args.command
    if cmd in ("vocabulary", "vocab"):
        from fusion_hero_os.core.ops_vocabulary import status

        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "deploy":
        from fusion_hero_os.core.ops_deploy import deploy, status

        if args.status:
            print(json.dumps(status(), indent=2, ensure_ascii=False))
            return 0
        r = deploy()
        print(json.dumps({k: r[k] for k in r if k != "steps"}, indent=2, ensure_ascii=False))
        print("steps:", json.dumps(r.get("steps"), indent=2, ensure_ascii=False)[:2000])
        return 0 if r.get("ok") else 1
    if cmd == "push":
        from fusion_hero_os.core.ops_push import push_public, status

        if args.status:
            print(json.dumps(status(), indent=2, ensure_ascii=False))
            return 0
        r = push_public(dry=args.dry)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 2
    if cmd == "merge":
        from fusion_hero_os.core.ops_merge import merge_both, status

        if args.status:
            print(json.dumps(status(), indent=2, ensure_ascii=False))
            return 0
        r = merge_both()
        print(
            json.dumps(
                {
                    "ok": r.get("ok"),
                    "operation": "merge",
                    "meaning": "both_via_timeline",
                    "public_display_id": (r.get("public") or {}).get("display_id"),
                    "private_ref_count": (r.get("private") or {}).get("ref_count"),
                    "link_count": len(r.get("links") or []),
                    "manifest": r.get("manifest"),
                    "docs_summary": r.get("docs_summary"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if r.get("ok") else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
