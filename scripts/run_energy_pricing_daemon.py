#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone energy/pricing daemon for Docker (Senfkorn UG production).

Writes audit trail under:
  $FUSION_STATE_DIR/mainframe_energy_pricing/history.jsonl
"""
from __future__ import annotations

import os
import sys
import time

# Ensure 03_Code is importable when started from /app
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CODE = os.path.join(_ROOT, "03_Code")
for p in (_CODE, _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.mainframe_energy_pricing_daemon import get_energy_daemon  # noqa: E402


def main() -> None:
    interval = float(os.getenv("FUSION_ENERGY_PRICING_INTERVAL_SEC", "60"))
    daemon = get_energy_daemon()
    daemon.start_background()
    print(
        f"[energy-pricing-daemon] started interval={interval}s "
        f"state={os.getenv('FUSION_STATE_DIR', '~/.fusion-hero-os')} "
        f"bp={os.getenv('FUSION_BUSINESSPLAN_PATH', '')}",
        flush=True,
    )
    while daemon._running:
        try:
            snap = daemon.tick()
            print(
                f"[energy-pricing-daemon] tick ok "
                f"eur_h={getattr(snap, 'eur_hour_real', None)} "
                f"alerts={getattr(snap, 'alerts', None)}",
                flush=True,
            )
        except Exception as exc:
            print(f"[energy-pricing-daemon] tick error: {exc}", flush=True)
        time.sleep(max(5.0, interval))


if __name__ == "__main__":
    main()
