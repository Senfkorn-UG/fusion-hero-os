# -*- coding: utf-8 -*-
"""
Full dissertation appendix pipeline with automatic v10 activation.

  1) activate_v10 (env + package + dashboard load-all/autoload/interconnect)
  2) generate A10 catalog (core + Dashboard)
  3) embed anhaenge into DOCX
  4) export PDF (LibreOffice)

Usage:
  python scripts/pipeline_dissertation_v10.py
  python scripts/pipeline_dissertation_v10.py --force
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Re-embed even if marker present")
    ap.add_argument("--no-http", action="store_true", help="Skip dashboard HTTP activation")
    ap.add_argument(
        "--base",
        default="http://127.0.0.1:8000",
        help="Dashboard URL",
    )
    args = ap.parse_args()

    py = sys.executable
    steps = []

    # 1 activate
    cmd = [py, str(ROOT / "scripts" / "activate_v10.py"), "--base", args.base]
    if args.no_http:
        cmd.append("--no-http")
    steps.append(("activate_v10", cmd))

    # 2 catalog
    steps.append(
        ("catalog", [py, str(ROOT / "scripts" / "generate_anhang_katalog.py")])
    )

    # 3 embed + pdf (activate again inside embed is ok; use --activate-v10)
    embed = [
        py,
        str(ROOT / "scripts" / "embed_dissertation_anhaenge.py"),
        "--regen-catalog",
        "--pdf",
        "--activate-v10",
        "--dashboard-url",
        args.base,
    ]
    if args.force:
        embed.append("--force")
    # If force needed to re-embed, user passes --force; without force embed may no-op if marker
    steps.append(("embed_pdf", embed))

    for name, cmd in steps:
        print(f"\n######## {name} ########")
        print(">", " ".join(cmd))
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode != 0 and name == "activate_v10" and r.returncode == 2:
            print("FATAL: platform not v10.0.0")
            return 2
        if r.returncode != 0 and name != "activate_v10":
            print(f"FAIL {name} exit {r.returncode}")
            return r.returncode
        if r.returncode != 0:
            print(f"WARN {name} exit {r.returncode} — continuing")

    print("\n=== pipeline_dissertation_v10 complete ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
