#!/usr/bin/env python3
"""Install git pre-push hook that runs layer push guard."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".git" / "hooks" / "pre-push"


HOOK_BODY = r'''#!/bin/sh
# Fusion Hero OS — Push Layer Guard (known identities + layer weave)
# Blocks unwanted pushes; allows wanted via FUSION_PUSH_INTENT / [push-ok] / conventional commits.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  exit 0
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
# Windows-friendly: prefer py/python on PATH
if command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v py >/dev/null 2>&1; then
  PY="py -3"
else
  echo "[push-layer-guard] python not found — allowing push (install python to enforce)"
  exit 0
fi
# Forward remote name + url + stdin refs
exec $PY "$ROOT/scripts/git_push_guard.py" "$@"
'''


def main() -> int:
    if not (ROOT / ".git").exists():
        print("Not a git repo")
        return 1
    HOOK.parent.mkdir(parents=True, exist_ok=True)
    HOOK.write_text(HOOK_BODY, encoding="utf-8", newline="\n")
    try:
        HOOK.chmod(HOOK.stat().st_mode | 0o111)
    except Exception:
        pass
    # also core.hooksPath optional note
    print(f"Installed: {HOOK}")
    print("Wanted push: set FUSION_PUSH_INTENT=1 or use [push-ok] / feat: commits")
    print("Test: python -m fusion_hero_os.core.push_layer_guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
