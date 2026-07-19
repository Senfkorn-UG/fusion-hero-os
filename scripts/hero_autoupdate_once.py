# -*- coding: utf-8 -*-
"""One-shot hero autoupdate tick (used by autoload_controller)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FUSION_REPO_ROOT", str(ROOT))

from fusion_hero_os.core.hero_autoupdate import get_hero_autoupdate  # noqa: E402


def main() -> int:
    svc = get_hero_autoupdate()
    n = svc.notify_startup()
    t = svc.tick(do_fetch=True)
    print(
        json.dumps(
            {
                "startup": n.get("ok", True),
                "tick": t.get("ok", True),
                "git_head": t.get("git_head"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
