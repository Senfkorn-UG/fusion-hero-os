#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI: Pure-Core Langzeit-Coevolution — Status + optional mutual cycle.

  python scripts/pure_core_coevolution_status.py
  python scripts/pure_core_coevolution_status.py --cycle 5
  python scripts/pure_core_coevolution_status.py --reject-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Pure-Core Coevolution membrane")
    ap.add_argument(
        "--cycle",
        type=int,
        default=0,
        help="Run mutual coevolution cycle for N generations",
    )
    ap.add_argument(
        "--reject-test",
        action="store_true",
        help="Demonstrate foreign claim_source_of_truth is rejected",
    )
    args = ap.parse_args()

    from fusion_hero_os.core.pure_core_coevolution import (
        assert_core_not_replaced,
        mutual_cycle,
        status,
    )

    st = status()
    print(json.dumps(st, indent=2, ensure_ascii=False))

    if args.reject_test:
        ok, msg = assert_core_not_replaced("llm")
        print("\n--- reject-test (llm as source of truth) ---")
        print(json.dumps({"accepted": ok, "message": msg}, indent=2))
        ok2, msg2 = assert_core_not_replaced("pure_core")
        print(json.dumps({"accepted": ok2, "message": msg2}, indent=2))

    if args.cycle > 0:
        print(f"\n--- mutual cycle ({args.cycle} gens) ---")
        out = mutual_cycle(args.cycle)
        print(
            json.dumps(
                {
                    "ok": out["ok"],
                    "trajectory": out["trajectory"],
                    "mutual_score": out["final"]["mutual_score"],
                    "integrity_ok": out["final"]["integrity_ok"],
                    "core_ids": out["final"]["core_ids"],
                    "foreign_ids": out["final"]["foreign_ids"],
                    "crosspoll_sources": out["final"]["crosspoll_sources"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
