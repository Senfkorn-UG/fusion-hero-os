#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Port Fusion Hero OS into the poly-mesh (L0–L4 Tailscale + GKE).

Steps:
  1. Inventory Tailscale peers + GKE probe
  2. Bind organs from mesh_os_port.yaml to live mesh IPs
  3. Optional: tailscale serve dashboard on mesh
  4. Run mesh_cluster_coordinator
  5. Enforce headset mesh_only
  6. Write public artifact + operator-local registry

Usage::

    python scripts/port_os_poly_mesh.py
    python scripts/port_os_poly_mesh.py --no-serve
    python scripts/port_os_poly_mesh.py --status
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Port OS to poly-mesh")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--no-coordinator", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from fusion_hero_os.core.poly_mesh_os_port import port_os, port_status

    if args.status:
        r = port_status()
    else:
        r = port_os(
            serve=not args.no_serve,
            run_coordinator=not args.no_coordinator,
        )
        # public artifact (no secrets)
        art = ROOT / "artifacts" / "2026-07-16_os_poly_mesh_port.md"
        lines = [
            "# OS → Poly-Mesh Port Report",
            "",
            f"**UTC:** {datetime.now(timezone.utc).isoformat()}",
            f"**Platform:** Fusion Hero OS v10.0.0",
            f"**Banner:** {r.get('banner')}",
            "",
            "## Self",
            "",
            f"- hostname: `{(r.get('inventory') or {}).get('self', {}).get('hostname')}`",
            f"- mesh_ip: `{(r.get('inventory') or {}).get('self', {}).get('mesh_ip')}`",
            f"- tiers_online: `{', '.join((r.get('inventory') or {}).get('tiers_online') or [])}`",
            f"- peers: `{(r.get('inventory') or {}).get('peer_count')}`",
            "",
            "## Organs",
            "",
            f"Count: **{r.get('organ_count')}**",
            "",
        ]
        for u in r.get("mesh_urls") or []:
            lines.append(f"- `{u}`")
        lines.extend(
            [
                "",
                "## Steps",
                "",
                f"- mesh_serve: `{json.dumps((r.get('steps') or {}).get('mesh_serve', {}), ensure_ascii=False)[:200]}`",
                f"- coordinator: ok=`{((r.get('steps') or {}).get('coordinator') or {}).get('ok')}`",
                f"- headset_mesh_only: `{((r.get('steps') or {}).get('headset_mesh_only') or {})}`",
                "",
                "## CLI",
                "",
                "```powershell",
                "python scripts/port_os_poly_mesh.py",
                "python -m fusion_hero_os.core.poly_mesh_os_port --status",
                "python scripts/mesh_cluster_coordinator.py --mode all",
                "```",
                "",
                "## Notes",
                "",
                "- Secrets/MCP stay **L1**.",
                "- Dashboard mesh URLs need `:8000` process up.",
                "- AudioRelay phone path: **mesh only** (100.x).",
                "- Tailscale **Apps** UI is SaaS routing — not required for this port.",
                "",
            ]
        )
        art.write_text("\n".join(lines), encoding="utf-8")
        r["artifact"] = str(art)

    print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get("banner"):
        print(r["banner"], file=sys.stderr)
    return 0 if r.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
