#!/usr/bin/env python3
"""One-shot repo health / repair verification for Fusion Hero OS v10."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

def run(args: list[str]) -> int:
    print(f"\n=== {' '.join(args)} ===", flush=True)
    r = subprocess.run([PY, *args], cwd=ROOT)
    print(f"exit={r.returncode}", flush=True)
    return r.returncode

def main() -> int:
    steps = [
        ["scripts/bump_version.py", "--check"],
        ["scripts/check_proof_registry.py"],
        ["scripts/check_erkenntnisse_index.py"],
        ["scripts/check_doc_versions.py"],
        ["scripts/check_pii_scanner.py"],
        ["-m", "fusion_hero_os.core.dependency_atlas", "--check"],
        ["-m", "pytest", "tests/", "-q", "--tb=line", "--ignore=tests/integration"],
    ]
    failed = []
    for s in steps:
        code = run(s)
        if code != 0:
            failed.append((s, code))
    print("\n========== SUMMARY ==========")
    if not failed:
        print("ALL GATES GREEN")
        return 0
    print(f"FAILED {len(failed)} step(s):")
    for s, c in failed:
        print(f"  exit={c}  {s}")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
