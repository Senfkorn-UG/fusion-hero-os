#!/usr/bin/env python3
"""Pre-push entrypoint — layer-woven push guard with known identities."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    # git pre-push passes: remote_name remote_url on argv; refs on stdin
    remote = "origin"
    url = ""
    if len(sys.argv) >= 2:
        remote = sys.argv[1]
    if len(sys.argv) >= 3:
        url = sys.argv[2]

    force = os.environ.get("GIT_PUSH_OPTION_COUNT")  # not always set
    # detect force via env used by some wrappers
    is_force = os.environ.get("FUSION_PUSH_FORCE", "").strip() in ("1", "true")

    from fusion_hero_os.core.push_layer_guard import evaluate_push

    # parse stdin ref lines: local_ref local_sha remote_ref remote_sha
    branch = ""
    stdin = sys.stdin.read() if not sys.stdin.isatty() else ""
    for line in stdin.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            remote_ref = parts[2]
            if remote_ref.startswith("refs/heads/"):
                branch = remote_ref.split("/", 2)[-1]
            if parts[0] == "(delete)":
                print("[BLOCK] branch delete pushes blocked by layer guard")
                return 1

    d = evaluate_push(
        remote=remote,
        branch=branch or None,
        remote_url=url or None,
        force=is_force,
    )
    mark = "ALLOW" if d.allow else "BLOCK"
    print(f"[push-layer-guard] {mark}: {d.reason}")
    if d.layers_touched:
        print(f"  layers: {', '.join(d.layers_touched)}")
    if d.advice:
        print(f"  advice: {d.advice}")
    if d.deny_hits:
        print(f"  deny: {d.deny_hits}")
    return 0 if d.allow else 1


if __name__ == "__main__":
    raise SystemExit(main())
