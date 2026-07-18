#!/usr/bin/env python3
"""
Fusion Hero OS — Mesh Connector Registry
Jeder Konnektor ist ein eigenständiges Mesh-Segment mit eigener Identität und Health-Probe.
"""

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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
    connectors = [
        "github", "gmail", "google_drive", "google_calendar",
        "canva", "gamma", "notion", "vercel", "hyperframes", "tasks",
    ]
    return {
        "mesh_version": "1.0",
        "tailnet": "example.ts.net",
        "nodes": {
            "mainframe": {"role": "orchestrator", "hostname": "mainframe"},
            "desktop": {"role": "grok-workstation", "hostname": "mainframe"},
        },
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


def _probe_mcp_connector(connector_id: str, config: dict) -> dict:
    """Probe a single connector mesh segment."""
    folder = MCP_PATH_ALIASES.get(connector_id, connector_id)
    mcp_path = Path.home() / "mcps" / folder
    tools_exist = (mcp_path / "tools").is_dir() if mcp_path.exists() else False
    links = _get_connector_llm_links()
    linked_llm = links.get(connector_id)

    return {
        "mesh_id": config.get("mesh_id", f"mesh-connector-{connector_id}"),
        "connector_id": connector_id,
        "type": config.get("type", "mcp"),
        "host_node": config.get("host_node"),
        "health_path": config.get("health_path", f"/mesh/{connector_id}/status"),
        "tailscale_tag": config.get("tailscale_tag"),
        "description": config.get("description", ""),
        "linked_llm": linked_llm,
        "linked_llm_path": f"/llm/{linked_llm}/status" if linked_llm else None,
        "segment_status": "registered" if tools_exist else "pending",
        "mcp_tools_available": tools_exist,
        "mcp_path": str(mcp_path),
        "timestamp": datetime.now().isoformat(),
    }


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

    return {
        "timestamp": datetime.now().isoformat(),
        "mesh_version": registry.get("mesh_version"),
        "tailnet": registry.get("tailnet"),
        "principle": registry.get("principle"),
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


# ---------------------------------------------------------------------------
# Layer-ω Bifurkale Synchronisation (Direktive 2026-07-15)
# register_hyper4d_node() + bifurcal_sync() — von der Direktive gefordert.
# Registry-State liegt operator-lokal (~/.fusion/mesh/hyper4d/registry.json),
# race-sicher via race_guard-CAS wenn das Paket verfügbar ist.
# ---------------------------------------------------------------------------

HYPER4D_TAG = "tag:fusion-hyper4d-node"
HYPER4D_CAPABILITIES = [
    "hyper4d_coevolution",
    "layer_omega_fixedpoint",
    "autopoietic_morphing",
    "bifurcal_sync",
]


def _hyper4d_registry_path() -> Path:
    base = os.environ.get("FUSION_HYPER4D_DIR") or str(
        Path.home() / ".fusion" / "mesh" / "hyper4d"
    )
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p / "registry.json"


def _cas_update(
    path: Path,
    mutate: Callable[[Optional[Dict[str, Any]]], Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        from fusion_hero_os.core.race_guard import compare_and_swap_json

        return compare_and_swap_json(path, mutate)
    except ImportError:
        # Fallback ohne Lock für Umgebungen ohne installiertes Paket
        current: Dict[str, Any] = {}
        if path.is_file():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                current = {}
        new_obj = mutate(current or None)
        new_obj["_generation"] = int((current or {}).get("_generation") or 0) + 1
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(new_obj, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, path)
        return new_obj


def _node_identity() -> Dict[str, Any]:
    ts = _get_tailscale_self()
    hostname = (
        ts.get("hostname")
        or os.environ.get("COMPUTERNAME")
        or os.environ.get("HOSTNAME")
        or "local-node"
    )
    return {"hostname": str(hostname), "tailscale": ts}


def _file_sha256(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_hyper4d_registry() -> Dict[str, Any]:
    path = _hyper4d_registry_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def hyper4d_status() -> Dict[str, Any]:
    """Status-Payload für /mesh/hyper4d/status (Direktive §3)."""
    reg = _read_hyper4d_registry()
    ident = _node_identity()
    node = (reg.get("nodes") or {}).get(ident["hostname"]) or {}
    return {
        "ok": True,
        "protocol": "hyper4d",
        "node": ident["hostname"],
        "registered": ident["hostname"] in (reg.get("nodes") or {}),
        "phase_sec": round(time.time() % 16, 3),  # Co-Evolution Phase (0–15s)
        "feedback_strength": float(node.get("feedback_strength") or 0.0),
        "fixedpoint": node.get("fixedpoint")
        or {"anchor": "identity-fixpoint", "stable": True},
        "generation": int(reg.get("_generation") or 0),
        "registry": str(_hyper4d_registry_path()),
    }


def register_hyper4d_node() -> Dict[str, Any]:
    """Direktive §1: diese Instanz als hyper4d-Node registrieren."""
    ident = _node_identity()

    def mut(cur: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        base = dict(cur or {})
        nodes = dict(base.get("nodes") or {})
        entry = dict(nodes.get(ident["hostname"]) or {})
        entry.update(
            {
                "tailscale_tag": HYPER4D_TAG,
                "capabilities": list(HYPER4D_CAPABILITIES),
                "registered_at": entry.get("registered_at")
                or datetime.now().isoformat(),
                "status_path": "/mesh/hyper4d/status",
                "online": bool((ident["tailscale"] or {}).get("online")),
            }
        )
        nodes[ident["hostname"]] = entry
        base["nodes"] = nodes
        base["tag"] = HYPER4D_TAG
        return base

    result = _cas_update(_hyper4d_registry_path(), mut)
    return {
        "ok": True,
        "node": ident["hostname"],
        "tag": HYPER4D_TAG,
        "capabilities": list(HYPER4D_CAPABILITIES),
        "generation": int(result.get("_generation") or 0),
        "registry": str(_hyper4d_registry_path()),
    }


def bifurcal_sync() -> Dict[str, Any]:
    """Direktive §2: Pfad A (Pull) + Pfad B (Push) in einer CAS-Transaktion.

    Pull: Stand von mesh_connectors.yaml + fusion_unified.yaml (sha256/mtime)
    in den Node-Eintrag übernehmen. Push: lokale Phase, Feedback-Stärke und
    Fixed-Point-Status ins Registry-State zurückspielen. Co-evolutionär:
    die Feedback-Stärke wächst gedämpft pro Sync (Ceiling 1.0).
    """
    base_dir = Path(__file__).parent
    pulled: Dict[str, Any] = {}
    for name in ("mesh_connectors.yaml", "fusion_unified.yaml"):
        f = base_dir / name
        pulled[name] = {
            "present": f.is_file(),
            "sha256": _file_sha256(f),
            "mtime": f.stat().st_mtime if f.is_file() else None,
        }
    ident = _node_identity()
    phase = round(time.time() % 16, 3)

    def mut(cur: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        base = dict(cur or {})
        nodes = dict(base.get("nodes") or {})
        entry = dict(nodes.get(ident["hostname"]) or {})
        prev = float(entry.get("feedback_strength") or 0.0)
        entry.update(
            {
                "last_sync": datetime.now().isoformat(),
                "phase_sec": phase,
                "feedback_strength": round(min(1.0, prev * 0.9 + 0.1), 4),
                "fixedpoint": {"anchor": "identity-fixpoint", "stable": True},
                "pulled": pulled,  # Pfad A
            }
        )
        nodes[ident["hostname"]] = entry  # Pfad B
        base["nodes"] = nodes
        return base

    result = _cas_update(_hyper4d_registry_path(), mut)
    node = (result.get("nodes") or {}).get(ident["hostname"]) or {}
    return {
        "ok": True,
        "node": ident["hostname"],
        "pull": pulled,
        "push": {
            "phase_sec": node.get("phase_sec"),
            "feedback_strength": node.get("feedback_strength"),
        },
        "generation": int(result.get("_generation") or 0),
        "status": hyper4d_status(),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "hyper4d-register":
        status = register_hyper4d_node()
    elif len(sys.argv) > 1 and sys.argv[1] == "hyper4d-sync":
        status = bifurcal_sync()
    elif len(sys.argv) > 1 and sys.argv[1] == "hyper4d-status":
        status = hyper4d_status()
    elif len(sys.argv) > 1:
        status = get_connector_status(sys.argv[1])
    else:
        status = get_mesh_status()

    print(json.dumps(status, indent=2, ensure_ascii=False))
    sys.exit(1 if "error" in status else 0)
