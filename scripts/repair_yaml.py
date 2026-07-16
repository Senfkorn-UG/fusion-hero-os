#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair / normalize public YAML configs (placeholders, sync, validate)."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "legacy_sources", "archiv", "node_modules", "__pycache__", "site", ".venv", "venv"}


def dump(path: Path, data: object) -> None:
    text = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"rewrote {path.relative_to(ROOT)}")


def normalize_mesh_connectors(path: Path) -> None:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    d["mesh_version"] = "1.2"
    d["platform_version"] = "10.0.0"
    d["tailnet"] = "example.ts.net"
    d["live_inventory"] = False
    for nid, n in (d.get("nodes") or {}).items():
        if not isinstance(n, dict):
            continue
        if nid == "desktop":
            n.setdefault("hostname", "mainframe")
            n.setdefault("same_as", "mainframe")
            n["platform"] = "windows"
        elif nid == "mainframe":
            n.setdefault("hostname", "mainframe")
            n["platform"] = "windows"
        elif nid == "phone":
            n["hostname"] = "phone"
            n["platform"] = "android"
            n["hostname_aliases"] = ["phone-node"]
        elif nid in ("mesh-exit", "fusion-mesh-exit", "wsl"):
            n.setdefault("hostname", "mesh-exit" if "exit" in nid else "mainframe-wsl")
            n.setdefault("platform", "linux")
        else:
            n.setdefault("hostname", nid)
        host = n.get("hostname") or nid
        n["magicdns"] = f"{host}.example.ts.net"
        n.pop("tailscale_ip", None)
    routing = d.setdefault("routing", {})
    routing["base_url"] = "https://mainframe.example.ts.net"
    dump(path, d)


def normalize_exit_nodes(path: Path) -> None:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    d["mesh_exit_version"] = "1.1"
    d["platform_version"] = "10.0.0"
    d["tailnet"] = "example.ts.net"
    for name, c in (d.get("physical_candidates") or {}).items():
        if not isinstance(c, dict):
            continue
        host = c.get("hostname") or name
        c["hostname"] = host
        c["magicdns"] = f"{host}.example.ts.net"
        for k in ("tailscale_ip", "gce_external_ip", "gce_project", "gce_zone", "gce_instance"):
            # keep logical hostname keys; drop live infra IDs from public tree
            if k in ("gce_instance",) and c.get(k):
                continue
            c.pop("tailscale_ip", None)
            c.pop("gce_external_ip", None)
            c.pop("gce_project", None)
        if "fractal_replica_url" in c:
            c["fractal_replica_url"] = f"http://{host}.example.ts.net:8088/mesh/fractal/replica"
    cb = d.setdefault("cloud_backends", {})
    sb = cb.setdefault("supabase", {})
    sb["project_ref"] = "YOUR_SUPABASE_PROJECT_REF"
    sb["url"] = "https://YOUR_SUPABASE_PROJECT_REF.supabase.co"
    gs = cb.setdefault("google_server", {})
    gs["hostname"] = gs.get("hostname") or "mesh-exit"
    gs.pop("gce_project", None)
    gs.pop("gce_external_ip", None)
    gs.pop("gce_zone", None)
    dump(path, d)


def normalize_mesh_roles(path: Path) -> None:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    d["mesh_roles_version"] = "1.3"
    d["platform_version"] = "10.0.0"
    d["tailnet"] = "example.ts.net"
    d["live_inventory"] = False
    for _role, cfg in (d.get("role_assignments") or {}).items():
        if not isinstance(cfg, dict):
            continue
        cfg.pop("tailscale_ip", None)
        host = cfg.get("hostname") or cfg.get("node_id") or "mainframe"
        cfg["magicdns"] = f"{host}.example.ts.net"
    routing = d.setdefault("routing", {})
    routing["base_url"] = "https://mainframe.example.ts.net"
    routing["mainframe_hostname"] = "mainframe"
    cb = d.setdefault("cloud_backends", {})
    if isinstance(cb.get("supabase"), dict):
        cb["supabase"]["project_ref"] = "YOUR_SUPABASE_PROJECT_REF"
    if isinstance(cb.get("google_server"), dict):
        cb["google_server"].pop("tailscale_ip", None)
        cb["google_server"]["hostname"] = "mesh-exit"
        cb["google_server"]["magicdns"] = "mesh-exit.example.ts.net"
    dump(path, d)


def normalize_k8s_placeholders() -> None:
    for p in (ROOT / "infra" / "k8s" / "fusion-training").rglob("*.yaml"):
        text = p.read_text(encoding="utf-8")
        new = text.replace("YOUR_GCE_PROJECT", "${GCP_PROJECT_ID}")
        if new != text:
            p.write_text(new, encoding="utf-8", newline="\n")
            print(f"placeholder-fix {p.relative_to(ROOT)}")


def validate_all() -> int:
    bad = 0
    for p in sorted(ROOT.rglob("*")):
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if any(x in p.parts for x in SKIP):
            continue
        try:
            list(yaml.safe_load_all(p.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"FAIL {p.relative_to(ROOT)}: {exc}")
            bad += 1
    print(f"validate_all bad={bad}")
    return bad


def main() -> int:
    normalize_mesh_connectors(ROOT / "mesh_connectors.yaml")
    normalize_mesh_connectors(ROOT / "src/normal_os/integration/mesh_connectors.yaml")
    normalize_exit_nodes(ROOT / "mesh_virtual_exit_nodes.yaml")
    normalize_exit_nodes(ROOT / "src/normal_os/integration/mesh_virtual_exit_nodes.yaml")
    normalize_mesh_roles(ROOT / "src/normal_os/integration/mesh_roles.yaml")
    # keep dual copies of unified in sync (root is source of truth)
    unified = ROOT / "fusion_unified.yaml"
    if unified.exists():
        target = ROOT / "src/normal_os/integration/fusion_unified.yaml"
        target.write_text(unified.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        print(f"synced {target.relative_to(ROOT)}")
    llm = ROOT / "llm_frameworks.yaml"
    if llm.exists():
        t = ROOT / "src/normal_os/integration/llm_frameworks.yaml"
        # bump version header only if parseable
        d = yaml.safe_load(llm.read_text(encoding="utf-8")) or {}
        d["version"] = d.get("version") or "1.0"
        d["platform_version"] = "10.0.0"
        dump(llm, d)
        t.write_text(llm.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        print(f"synced {t.relative_to(ROOT)}")
    normalize_k8s_placeholders()
    # terraform
    tf = ROOT / "infra/terraform/senfkorn-fusion-stack/variables.tf"
    if tf.exists():
        text = tf.read_text(encoding="utf-8")
        text2 = text.replace('default     = "fusion-ai-data-YOUR_GCE_PROJECT"', 'default     = ""')
        text2 = text2.replace('default     = "YOUR_GCE_PROJECT"', 'default     = ""')
        if text2 != text:
            tf.write_text(text2, encoding="utf-8", newline="\n")
            print("repaired terraform variables defaults")
    return validate_all()


if __name__ == "__main__":
    sys.exit(main())
