#!/usr/bin/env python3
"""
Fusion Hero OS — Mesh Connector Registry
Jeder Konnektor ist ein eigenständiges Mesh-Segment mit eigener Identität und Health-Probe.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "mesh_connectors.yaml"


def _load_registry():
    try:
        import yaml
    except ImportError:
        return _load_registry_fallback()

    if not REGISTRY_PATH.exists():
        return {"error": f"Registry not found: {REGISTRY_PATH}"}

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_registry_fallback():
    """Minimal inline fallback if PyYAML is not installed."""
    try:
        from mesh_roles import mesh_nodes_for_registry, get_roles_registry
        reg = get_roles_registry()
        nodes = mesh_nodes_for_registry()
        tailnet = reg.get("tailnet", "example.ts.net")
    except Exception:
        nodes = {
            "mainframe": {
                "role": "orchestrator",
                "hostname": "mainframe",
                "platform": "windows",
            },
            "desktop": {"role": "grok-workstation", "hostname": "mainframe"},
        }
        tailnet = "example.ts.net"

    connectors = [
        "github", "gmail", "google_drive", "google_calendar",
        "canva", "gamma", "notion", "vercel", "hyperframes", "tasks",
    ]
    return {
        "mesh_version": "1.1",
        "tailnet": tailnet,
        "nodes": nodes,
        "connectors": {
            name: {
                "mesh_id": f"mesh-connector-{name.replace('_', '-')}",
                "type": "mcp",
                "host_node": "desktop",
                "health_path": f"/mesh/{name}/status",
            }
            for name in connectors
        },
    }


def _get_tailscale_self():
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
            "peers": len(data.get("Peer") or {}),
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


def _load_yaml_file(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


def _get_connector_llm_links() -> dict:
    base = Path(__file__).parent
    unified = _load_yaml_file(base / "fusion_unified.yaml")
    if unified.get("connector_llm_links"):
        return unified["connector_llm_links"]
    llm_cfg = _load_yaml_file(base / "llm_frameworks.yaml")
    return llm_cfg.get("connector_links", {})


# Connector-ID → Ordner unter ~/mcps (wenn abweichend)
MCP_PATH_ALIASES = {
    "hyperframes": "hyperframes_by_heygen",
}

GOOGLE_OAUTH_CONNECTORS = frozenset({"gmail", "google_drive", "google_calendar"})


def _google_oauth_status(connector_id: str) -> dict:
    try:
        from connectors.google_oauth import oauth_status
        return oauth_status(connector_id)
    except ImportError:
        normal_os = Path(__file__).resolve().parents[1]
        if str(normal_os) not in sys.path:
            sys.path.insert(0, str(normal_os))
        from connectors.google_oauth import oauth_status
        return oauth_status(connector_id)
    except Exception as exc:
        return {"ready": False, "reason": str(exc)}


def _probe_mcp_connector(connector_id: str, config: dict) -> dict:
    """Probe a single connector mesh segment."""
    folder = MCP_PATH_ALIASES.get(connector_id, connector_id)
    mcp_path = Path.home() / "mcps" / folder
    tools_exist = (mcp_path / "tools").is_dir() if mcp_path.exists() else False
    links = _get_connector_llm_links()
    linked_llm = links.get(connector_id)

    oauth = _google_oauth_status(connector_id) if connector_id in GOOGLE_OAUTH_CONNECTORS else None
    oauth_ready = bool(oauth and oauth.get("ready"))
    if oauth_ready:
        segment_status = "registered"
    elif tools_exist:
        segment_status = "registered"
    elif oauth and oauth.get("token_present"):
        segment_status = "oauth_partial"
    else:
        segment_status = "pending"

    result = {
        "mesh_id": config.get("mesh_id", f"mesh-connector-{connector_id}"),
        "connector_id": connector_id,
        "type": config.get("type", "mcp"),
        "host_node": config.get("host_node"),
        "health_path": config.get("health_path", f"/mesh/{connector_id}/status"),
        "tailscale_tag": config.get("tailscale_tag"),
        "description": config.get("description", ""),
        "linked_llm": linked_llm,
        "linked_llm_path": f"/llm/{linked_llm}/status" if linked_llm else None,
        "segment_status": segment_status,
        "mcp_tools_available": tools_exist,
        "mcp_path": str(mcp_path),
        "timestamp": datetime.now().isoformat(),
    }
    if oauth is not None:
        result["oauth"] = oauth
        result["oauth_ready"] = oauth_ready
    return result


def get_mesh_status() -> dict:
    """Return full mesh overview — nodes + all connector segments."""
    registry = _load_registry()
    if "error" in registry:
        return registry

    tailscale = _get_tailscale_self()
    connectors = registry.get("connectors", {})

    segments = {
        cid: _probe_mcp_connector(cid, cfg)
        for cid, cfg in connectors.items()
    }

    registered = sum(1 for s in segments.values() if s["segment_status"] == "registered")

    mainframe_role = {}
    try:
        from mesh_roles import get_mainframe, is_mainframe_self
        mainframe_role = {
            "node": get_mainframe(),
            "is_self": is_mainframe_self(),
        }
    except Exception:
        pass

    return {
        "timestamp": datetime.now().isoformat(),
        "mesh_version": registry.get("mesh_version"),
        "tailnet": registry.get("tailnet"),
        "principle": registry.get("principle"),
        "mainframe_role": mainframe_role,
        "tailscale": tailscale,
        "nodes": registry.get("nodes", {}),
        "connector_count": len(segments),
        "connectors_registered": registered,
        "connectors": segments,
    }


def get_connector_status(connector_id: str) -> dict:
    """Return status for a single connector mesh segment."""
    registry = _load_registry()
    if "error" in registry:
        return registry

    connectors = registry.get("connectors", {})
    if connector_id not in connectors:
        return {
            "error": f"Unknown connector: {connector_id}",
            "available": list(connectors.keys()),
        }

    segment = _probe_mcp_connector(connector_id, connectors[connector_id])
    segment["tailscale"] = _get_tailscale_self()
    return segment


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        status = get_connector_status(sys.argv[1])
    else:
        status = get_mesh_status()

    print(json.dumps(status, indent=2, ensure_ascii=False))
    sys.exit(1 if "error" in status else 0)
