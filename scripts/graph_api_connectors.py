#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI: Graph API hub for all connectors.

Examples:
  python scripts/graph_api_connectors.py --list
  python scripts/graph_api_connectors.py --status instagram
  python scripts/graph_api_connectors.py --instagram-publish \\
      --image-url https://raw.githubusercontent.com/.../IG_meister_hasch.png \\
      --caption-file docs/security/media/meister_hasch_v12/IG_CAPTION.txt

Live: set tokens + FUSION_GRAPH_LIVE=1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fusion_hero_os.connectors.graph_api import build_default_hub  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Graph API hub — all connectors")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--status", metavar="CONNECTOR")
    ap.add_argument("--dispatch", nargs=2, metavar=("CONNECTOR", "ACTION"))
    ap.add_argument("--instagram-publish", action="store_true")
    ap.add_argument("--image-url", default="")
    ap.add_argument("--caption", default="")
    ap.add_argument("--caption-file", default="")
    ap.add_argument("--force-live", action="store_true")
    ap.add_argument("--path", default="")
    ap.add_argument("--method", default="GET")
    args = ap.parse_args()

    hub = build_default_hub()

    if args.list:
        print(json.dumps(hub.list_connectors(), indent=2, ensure_ascii=False))
        return 0

    if args.status:
        print(json.dumps(hub.status(args.status), indent=2, ensure_ascii=False))
        return 0

    if args.instagram_publish:
        caption = args.caption
        if args.caption_file:
            caption = Path(args.caption_file).read_text(encoding="utf-8")
        image_url = args.image_url or (
            "https://raw.githubusercontent.com/95guknow/fusion-hero-os/main/"
            "docs/security/media/IG_meister_hasch.png"
        )
        if not caption:
            cap = ROOT / "docs/security/media/meister_hasch_v12/IG_CAPTION.txt"
            if cap.is_file():
                caption = cap.read_text(encoding="utf-8")
        out = hub.instagram_publish(
            image_url=image_url,
            caption=caption,
            force_live=args.force_live,
        )
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 2

    if args.dispatch:
        cid, action = args.dispatch
        kwargs = {"force_live": args.force_live}
        if args.path:
            kwargs["path"] = args.path
            kwargs["method"] = args.method
        out = hub.dispatch(cid, action, **kwargs)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") is not False else 2

    print(json.dumps(hub.list_connectors(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
