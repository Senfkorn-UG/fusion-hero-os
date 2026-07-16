#!/usr/bin/env python3
"""CLI: auto-train dual timeline (real t ∥ imaginary τ) from all available files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from fusion_hero_os.core.dual_timeline_training import run_auto_train, status

    if "--status" in sys.argv:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    dry = "--dry" in sys.argv
    report = run_auto_train(write=not dry)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
