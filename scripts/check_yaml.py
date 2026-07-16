#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YAML parse + schema gate for Fusion Hero OS public configs."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "legacy_sources", "archiv", "node_modules", "__pycache__", "site", ".venv", "venv"}


def main() -> int:
    bad = 0
    multi = 0
    count = 0
    for p in sorted(ROOT.rglob("*")):
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if any(x in p.parts for x in SKIP):
            continue
        count += 1
        try:
            docs = [d for d in yaml.safe_load_all(p.read_text(encoding="utf-8")) if d is not None]
        except Exception as exc:
            print(f"[FAIL] {p.relative_to(ROOT)}: {exc}")
            bad += 1
            continue
        if len(docs) > 1:
            multi += 1
            for i, d in enumerate(docs):
                if not isinstance(d, dict) or "apiVersion" not in d or "kind" not in d:
                    # multi-doc only expected for k8s manifests
                    if "k8s" not in p.parts and "kubernetes" not in p.parts:
                        print(f"[FAIL] {p.relative_to(ROOT)} multi-doc outside k8s")
                        bad += 1
                        break
                    if not isinstance(d, dict) or "apiVersion" not in d:
                        print(f"[FAIL] {p.relative_to(ROOT)} k8s doc[{i}] incomplete")
                        bad += 1
    # critical schema
    critical = {
        "mesh_connectors.yaml": ("nodes", "connectors", "tailnet"),
        "src/normal_os/integration/mesh_roles.yaml": ("role_assignments", "tailnet"),
        "docs/business/senfkorn_businessplan.yaml": ("company", "energy_model"),
        "docker-compose.yml": ("services", "volumes"),
        "fusion_unified.yaml": ("layers", "nodes", "version"),
    }
    for rel, keys in critical.items():
        p = ROOT / rel
        if not p.exists():
            print(f"[FAIL] missing {rel}")
            bad += 1
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for k in keys:
            if k not in d:
                print(f"[FAIL] {rel} missing key {k}")
                bad += 1
        # no live CGNAT IPs in public yaml
        text = p.read_text(encoding="utf-8")
        if "100.64.104." in text or "tail391adb" in text:
            print(f"[FAIL] {rel} still contains scrubbed live topology tokens")
            bad += 1
    # dual-copy sync
    pairs = [
        ("mesh_connectors.yaml", "src/normal_os/integration/mesh_connectors.yaml"),
        ("mesh_virtual_exit_nodes.yaml", "src/normal_os/integration/mesh_virtual_exit_nodes.yaml"),
        ("fusion_unified.yaml", "src/normal_os/integration/fusion_unified.yaml"),
    ]
    for a, b in pairs:
        pa, pb = ROOT / a, ROOT / b
        if pa.exists() and pb.exists():
            if pa.read_text(encoding="utf-8") != pb.read_text(encoding="utf-8"):
                print(f"[FAIL] out of sync: {a} != {b}")
                bad += 1
    print(f"YAML files scanned: {count} multi-doc: {multi} failures: {bad}")
    if bad:
        return 1
    print("[OK] YAML gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
