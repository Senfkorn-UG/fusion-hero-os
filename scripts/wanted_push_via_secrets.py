#!/usr/bin/env python3
"""
Trigger a *wanted* git push using operator secrets from .env / environment.

Never prints secret values. Hard denylist still blocks .env itself from being pushed.

Usage:
  python scripts/wanted_push_via_secrets.py
  python scripts/wanted_push_via_secrets.py --dry
  python scripts/wanted_push_via_secrets.py --remote origin --branch main
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="")
    ap.add_argument("--dry", action="store_true", help="Evaluate only, do not push")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from fusion_hero_os.core.push_layer_guard import evaluate_push, load_config, _load_dotenv_files

    cfg = load_config()
    loaded = _load_dotenv_files(cfg)
    # Mark intent after secrets load (secret_intent handles unlock)
    d = evaluate_push(remote=args.remote, branch=args.branch or None)

    report = {
        "allow": d.allow,
        "reason": d.reason,
        "wanted": d.wanted,
        "secret_intent": d.secret_intent,
        "secret_keys_present": d.secret_keys_present,  # names only
        "dotenv_loaded": d.dotenv_loaded or loaded,
        "layers": d.layers_touched,
        "advice": d.advice,
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"[{'ALLOW' if d.allow else 'BLOCK'}] {d.reason}")
        if d.secret_keys_present:
            print("secret keys present (names):", ", ".join(d.secret_keys_present))
        if d.dotenv_loaded:
            print("dotenv loaded:", ", ".join(d.dotenv_loaded))
        if d.layers_touched:
            print("layers:", ", ".join(d.layers_touched))
        if d.advice:
            print("advice:", d.advice)

    if not d.allow:
        return 2
    if args.dry:
        print("dry-run: push not executed")
        return 0

    branch = args.branch or subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=str(ROOT), text=True
    ).strip()
    # Ensure child git pre-push also sees secrets already loaded in this process env
    env = os.environ.copy()
    # Also set explicit intent so hooks that only check FUSION_PUSH_INTENT still pass
    if d.secret_intent:
        env["FUSION_PUSH_INTENT"] = "1"
    cmd = ["git", "push", args.remote, f"HEAD:{branch}"]
    print("running:", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
