#!/usr/bin/env python3
"""
Run full inside-out extension pipeline until inventory + training + merge are current.

Order (inside → out):
  1) identity / inventory (what exists, storage-agnostic)
  2) deploy = private (vault seal + dual timeline train)
  3) merge = both via timeline (public ↔ private links)
  4) optional: expand dissertation band note from inventory

Usage:
  python scripts/run_inside_out_extension.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from fusion_hero_os.core.inside_out_inventory import run_inventory
    from fusion_hero_os.core.ops_deploy import deploy
    from fusion_hero_os.core.ops_merge import merge_both
    from fusion_hero_os.core.dual_timeline_training import run_auto_train

    print("=== 1/4 inside-out inventory ===", flush=True)
    inv = run_inventory(write=True)
    print(
        json.dumps(
            {
                "items": inv["counts"]["items"],
                "files": inv["counts"]["files"],
                "bytes": inv["counts"]["bytes_total"],
                "by_ring": inv["counts"]["by_ring"],
                "paths": inv.get("paths"),
            },
            indent=2,
            ensure_ascii=False,
        ),
        flush=True,
    )

    print("=== 2/4 dual-timeline train (all available knowledge) ===", flush=True)
    train = run_auto_train(write=True)
    print(
        json.dumps(
            {
                "files": train.get("files"),
                "samples": train.get("samples"),
                "consistency_ok": (train.get("consistency") or {}).get("ok"),
            },
            indent=2,
        ),
        flush=True,
    )

    print("=== 3/4 deploy = private ===", flush=True)
    dep = deploy(seal_masterseed=True, train_timeline=False)  # train already done
    print(json.dumps({"ok": dep.get("ok"), "steps": dep.get("steps")}, indent=2), flush=True)

    print("=== 4/4 merge = both via timeline ===", flush=True)
    mer = merge_both(run_deploy=False, include_timeline=False)
    print(
        json.dumps(
            {
                "ok": mer.get("ok"),
                "public_display_id": (mer.get("public") or {}).get("display_id"),
                "private_ref_count": (mer.get("private") or {}).get("ref_count"),
                "link_count": len(mer.get("links") or []),
                "manifest": mer.get("manifest"),
            },
            indent=2,
        ),
        flush=True,
    )

    # Extension note into dissertation folder
    note = ROOT / "docs" / "dissertation" / "INSIDE_OUT_EXTENSION_RUN.md"
    note.write_text(
        "\n".join(
            [
                "# Inside-Out Extension Run",
                "",
                f"**Items inventoried:** {inv['counts']['items']}",
                f"**Files:** {inv['counts']['files']}",
                f"**Training samples:** {train.get('samples')}",
                f"**MasterSeed public:** {(mer.get('public') or {}).get('display_id')}",
                f"**Private refs linked:** {(mer.get('private') or {}).get('ref_count')}",
                "",
                "Method: **inside-out** (MasterSeed → core → modules → surfaces → docs → local state).",
                "Not outside-in. Storage location is metadata; existence is primary.",
                "",
                f"Full inventory: `{inv.get('paths', {}).get('full_jsonl')}`",
                f"Summary: `docs/inventory/INSIDE_OUT_INVENTORY.md`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    final = {
        "ok": bool(inv.get("ok") and train.get("ok") and dep.get("ok") and mer.get("ok")),
        "inventory_files": inv["counts"]["files"],
        "inventory_items": inv["counts"]["items"],
        "train_samples": train.get("samples"),
        "merge_links": len(mer.get("links") or []),
        "note": str(note),
    }
    print("=== DONE ===", flush=True)
    print(json.dumps(final, indent=2), flush=True)
    return 0 if final["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
