#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI: Meister Hasch Fable5+Mythos5 optimize (Hypertarnkappe + Hyperpanzerknacker).

Usage:
  python scripts/meister_hasch_fable_mythos_optimize.py
  python scripts/meister_hasch_fable_mythos_optimize.py --json
  python scripts/meister_hasch_fable_mythos_optimize.py --no-write

Always sandbox_only / dry_run. No exploit payloads. No external targets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fusion_hero_os.core.meister_hasch_optimize import (  # noqa: E402
    OptimizeConfig,
    run_optimize,
    status,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Meister Hasch bifocal optimize (Fable5/Mythos5 + cloak/probe)"
    )
    p.add_argument("--json", action="store_true", help="Print full JSON report")
    p.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write summary JSON files",
    )
    p.add_argument(
        "--status-only",
        action="store_true",
        help="Print module status only",
    )
    args = p.parse_args(argv)

    if args.status_only:
        print(json.dumps(status(), indent=2))
        return 0

    cfg = OptimizeConfig(dry_run=True, write_report=not args.no_write, sandbox_only=True)
    report = run_optimize(cfg)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(
            f"Meister Hasch optimize · platform={report.platform_version} · "
            f"overall={'PASS' if report.overall_passed else 'FAIL'} · "
            f"integrity={'OK' if report.integrity_ok else 'FAIL'}"
        )
        print(f"  sha256={report.asset_sha256}")
        print(f"  size={report.asset_size} · dry_run={report.dry_run} · sandbox_only={report.sandbox_only}")
        for name, lr in report.lenses.items():
            mark = "PASS" if lr.passed else "FAIL"
            print(f"  [{mark}] {name} score={lr.score:.0%} — {lr.role}")
            for pr in lr.probes:
                m = "✓" if pr.passed else "✗"
                print(f"      {m} {pr.id}: {pr.title}")
        print("Optimizations:")
        for tip in report.optimizations:
            print(f"  · {tip}")
        if cfg.write_report:
            print("Wrote: docs/dissertation/meister_hasch_optimize.summary.json")
            print("Wrote: docs/security/meister_hasch_optimize.summary.json")

    return 0 if report.overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
