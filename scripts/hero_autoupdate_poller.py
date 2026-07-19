# -*- coding: utf-8 -*-
"""Background hero autoupdate poller (1 min default)."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FUSION_REPO_ROOT", str(ROOT))

from fusion_hero_os.core.hero_autoupdate import get_hero_autoupdate  # noqa: E402


def main() -> int:
    svc = get_hero_autoupdate()
    interval = max(30.0, float(svc.config.poll_interval_sec or 60))
    while True:
        try:
            svc.tick(do_fetch=False)
        except Exception:
            pass
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
