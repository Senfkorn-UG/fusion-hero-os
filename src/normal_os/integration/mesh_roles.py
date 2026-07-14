#!/usr/bin/env python3
"""Kanonische Tailscale-Mesh-Rollen — Windows-Desktop = Mainframe."""

from __future__ import annotations

import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

ROLES_PATH = Path(__file__).parent / "mesh_roles.yaml"

_FALLBACK = {
    "mesh_roles_version": "1.1",
    "tailnet": "example.ts.net",
    "role_assignments": {
        "mainframe": {
            "node_id": "mainframe",
            "role": "orchestrator",
            "hostname": "mainframe-host",
            "magicdns": "mainframe-host.example.ts.net",
            "platform": "windows",
            "canonical": True,
            "aliases": ["desktop"],
        },
        "workstation": {
            "node_id": "desktop",
            "role": "grok-workstation",
            "same_as": "mainframe",
            "hostname": "mainframe-host",
            "magicdns": "mainframe-host.example.ts.net",
            "platform": "windows",
        },
        "mobile": {
            "node_id": "phone",
            "role": "mobile-client",
            "hostname": "mobile-node",
            "magicdns": "mobile-node.example.ts.net",
            "platform": "android",
        },
        "legacy": {
            "node_id": "legacy-linux",
            "role": "archived",
            "hostname": "mainframe",
            "magicdns": "mainframe-host.example.ts.net",
            "platform": "linux",
            "status": "offline",
        },
    },
    "routing": {
        "base_url": "https://mainframe-host.example.ts.net",
        "mainframe_hostname": "mainframe-host",
        "funnel_port": 8088,
    },
}


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


@lru_cache(maxsize=1)
def get_roles_registry() -> dict:
    data = _load_yaml(ROLES_PATH)
    if not data:
        data = dict(_FALLBACK)
    env_host = os.getenv("FUSION_MESH_MAINFRAME_HOSTNAME")
    if env_host:
        mf = data.setdefault("role_assignments", {}).setdefault("mainframe", {})
        mf["hostname"] = env_host
        mf["magicdns"] = os.getenv(
            "FUSION_MESH_MAINFRAME_MAGICDNS",
            f"{env_host}.example.ts.net",
        )
        routing = data.setdefault("routing", {})
        routing["mainframe_hostname"] = env_host
        routing["base_url"] = os.getenv(
            "FUSION_MESH_BASE_URL",
            f"https://{env_host}.example.ts.net",
        )
    return data


def get_mainframe() -> dict:
    reg = get_roles_registry()
    return dict(reg.get("role_assignments", {}).get("mainframe", {}))


def get_mainframe_hostname() -> str:
    return get_mainframe().get("hostname", "mainframe-host")


def get_mainframe_magicdns() -> str:
    mf = get_mainframe()
    return mf.get("magicdns") or f"{get_mainframe_hostname()}.example.ts.net"


def get_routing_base_url() -> str:
    reg = get_roles_registry()
    return reg.get("routing", {}).get("base_url", get_mainframe_magicdns().replace("http", "https"))


def get_tailscale_self() -> dict:
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return {"online": False, "error": "tailscale unavailable"}
        data = json.loads(result.stdout)
        self_data = data.get("Self", {})
        return {
            "online": self_data.get("Online", False),
            "hostname": self_data.get("HostName"),
            "tailscale_ip": (self_data.get("TailscaleIPs") or [None])[0],
            "magicdns": (self_data.get("DNSName") or "").rstrip("."),
            "peers": len(data.get("Peer") or {}),
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


def is_mainframe_self() -> bool:
    mf_host = get_mainframe_hostname().lower()
    self_data = get_tailscale_self()
    host = (self_data.get("hostname") or "").lower()
    dns = (self_data.get("magicdns") or "").lower()
    return mf_host in host or mf_host in dns


def resolve_node(node_id: str) -> Optional[dict]:
    reg = get_roles_registry()
    for _key, cfg in (reg.get("role_assignments") or {}).items():
        if cfg.get("node_id") == node_id:
            return dict(cfg)
    return None


def mesh_nodes_for_registry() -> Dict[str, Any]:
    """Knoten-Dict im Format von mesh_connectors.yaml."""
    reg = get_roles_registry()
    nodes: Dict[str, Any] = {}
    for _key, cfg in (reg.get("role_assignments") or {}).items():
        node_id = cfg.get("node_id")
        if not node_id:
            continue
        entry = {k: v for k, v in cfg.items() if k not in ("node_id", "same_as", "aliases")}
        if cfg.get("same_as"):
            entry["alias_of"] = cfg["same_as"]
        nodes[node_id] = entry
    return nodes


def status() -> dict:
    mf = get_mainframe()
    return {
        "mesh_roles_version": get_roles_registry().get("mesh_roles_version"),
        "tailnet": get_roles_registry().get("tailnet"),
        "mainframe": mf,
        "routing_base_url": get_routing_base_url(),
        "is_mainframe_self": is_mainframe_self(),
        "tailscale_self": get_tailscale_self(),
        "principle": get_roles_registry().get("principle"),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
