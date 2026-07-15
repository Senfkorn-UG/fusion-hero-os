#!/usr/bin/env python3
"""
Fusion Hero OS — Fractal Mainframe Mesh Persistence + Virtual Exit Nodes

Fractal save: mainframe state is decomposed into self-similar slices (L0 anchor
→ L1 nodes → L2 segments → L3 exit profiles), content-addressed and persisted
under ~/.fusion/mesh/fractal/.

Virtual exit nodes: logical egress profiles mapped to physical Tailscale exit
peers (see mesh_virtual_exit_nodes.yaml).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
EXIT_CONFIG_PATH = ROOT / "mesh_virtual_exit_nodes.yaml"
ROLES_PATH = ROOT / "src" / "normal_os" / "integration" / "mesh_roles.yaml"
if not ROLES_PATH.exists():
    ROLES_PATH = ROOT / "mesh_roles.yaml"
CONNECTORS_PATH = ROOT / "mesh_connectors.yaml"
UNIFIED_PATH = ROOT / "fusion_unified.yaml"

FRACTAL_ROOT = Path(os.environ.get("FUSION_FRACTAL_MESH_DIR", Path.home() / ".fusion" / "mesh" / "fractal"))
SLICES_DIR = FRACTAL_ROOT / "slices"
REPLICAS_DIR = FRACTAL_ROOT / "replicas"
MANIFEST_PATH = FRACTAL_ROOT / "manifest.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_obj(obj: Any) -> str:
    return _sha256_text(_canonical_json(obj))


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


def _tailscale_json() -> dict:
    try:
        r = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception:
        pass
    return {}


def _get_masterseed_anchor() -> dict:
    try:
        from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
        seed = MasterSeed()
        h = seed.state_hash()
        return {
            "layer": 0,
            "type": "anchor",
            "masterseed_hash": h,
            "integrity_ok": seed.verify_integrity(h),
            "criticality_target": seed.criticality_target,
        }
    except Exception as e:
        return {"layer": 0, "type": "anchor", "error": str(e), "integrity_ok": False}


def _config_fingerprints() -> dict:
    files = {
        "mesh_roles": ROLES_PATH,
        "mesh_connectors": CONNECTORS_PATH,
        "fusion_unified": UNIFIED_PATH,
        "virtual_exit_nodes": EXIT_CONFIG_PATH,
    }
    out = {}
    for name, path in files.items():
        if path.exists():
            raw = path.read_bytes()
            out[name] = {
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        else:
            out[name] = {"path": str(path), "missing": True}
    return out


def _mesh_roles_nodes() -> dict:
    try:
        sys.path.insert(0, str(ROOT / "src" / "normal_os" / "integration"))
        from mesh_roles import mesh_nodes_for_registry, get_mainframe, status as roles_status
        return {
            "nodes": mesh_nodes_for_registry(),
            "mainframe": get_mainframe(),
            "roles_status": roles_status(),
        }
    except Exception:
        roles = _load_yaml(ROLES_PATH)
        return {"nodes": roles.get("role_assignments", {}), "source": "yaml_fallback"}


def _mesh_connectors() -> dict:
    reg = _load_yaml(CONNECTORS_PATH)
    return {
        "connectors": list((reg.get("connectors") or {}).keys()),
        "agents": list((reg.get("agents") or {}).keys()),
        "nodes": list((reg.get("nodes") or {}).keys()),
    }


def _tailscale_peers() -> List[dict]:
    data = _tailscale_json()
    self_data = data.get("Self") or {}
    peers = []
    for _pk, p in (data.get("Peer") or {}).items():
        ips = p.get("TailscaleIPs") or []
        peers.append({
            "hostname": p.get("HostName"),
            "os": p.get("OS"),
            "online": p.get("Online", False),
            "tailscale_ip": ips[0] if ips else None,
            "magicdns": (p.get("DNSName") or "").rstrip("."),
            "exit_node_option": p.get("ExitNodeOption", False),
            "active_exit": p.get("ExitNode", False),
        })
    return peers


def _self_tailscale() -> dict:
    data = _tailscale_json()
    s = data.get("Self") or {}
    return {
        "hostname": s.get("HostName"),
        "online": s.get("Online", False),
        "tailscale_ip": (s.get("TailscaleIPs") or [None])[0],
        "magicdns": (s.get("DNSName") or "").rstrip("."),
        "using_exit_node": s.get("ExitNode", False),
        "exit_node_ip": s.get("ExitNodeIP"),
    }


def load_exit_config() -> dict:
    cfg = _load_yaml(EXIT_CONFIG_PATH)
    if not cfg:
        return {
            "mesh_exit_version": "1.0",
            "default_profile": "direct",
            "virtual_profiles": {"direct": {"clear_exit": True}},
            "physical_candidates": {},
            "segment_routing": {},
        }
    return cfg


def resolve_physical_exit(hostname: str, peers: List[dict], cfg: dict) -> Optional[dict]:
    candidates = cfg.get("physical_candidates") or {}
    static = candidates.get(hostname) or {}
    for p in peers:
        if (p.get("hostname") or "").lower() == hostname.lower():
            merged = {**static, **p}
            merged["resolved"] = True
            return merged
    if static:
        static["resolved"] = False
        static["offline"] = True
        return static
    return None


def resolve_virtual_profile(profile_id: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_exit_config()
    profiles = cfg.get("virtual_profiles") or {}
    if profile_id not in profiles:
        return {"error": f"Unknown profile: {profile_id}", "available": list(profiles.keys())}

    profile = dict(profiles[profile_id])
    peers = _tailscale_peers()
    primary_name = profile.get("primary")
    fallbacks = profile.get("fallbacks") or []

    chain = []
    if primary_name:
        chain.append(primary_name)
    chain.extend(fallbacks)

    selected = None
    for name in chain:
        phys = resolve_physical_exit(name, peers, cfg)
        if not phys:
            continue
        if profile.get("require_online") and not phys.get("online"):
            continue
        offers = phys.get("exit_node_option") or phys.get("offers_exit")
        if not offers:
            continue
        selected = phys
        selected["profile_id"] = profile_id
        selected["selected_via"] = name
        break

    return {
        "profile_id": profile_id,
        "label": profile.get("label"),
        "clear_exit": profile.get("clear_exit", False),
        "selected_physical": selected,
        "candidate_chain": chain,
        "peers_online": sum(1 for p in peers if p.get("online")),
    }


def apply_virtual_exit(profile_id: str, *, dry_run: bool = False) -> dict:
    """Apply a virtual exit profile via tailscale set."""
    resolved = resolve_virtual_profile(profile_id)
    if resolved.get("error"):
        return resolved

    cfg = load_exit_config()
    profile = (cfg.get("virtual_profiles") or {}).get(profile_id, {})
    self_ts = _self_tailscale()
    platform = (self_ts.get("os") or os.name).lower()

    blocked = profile.get("blocked_on_platforms") or []
    if any(b in platform for b in blocked):
        return {
            "ok": False,
            "profile_id": profile_id,
            "error": f"Profile blocked on platform {platform}",
            "dry_run": dry_run,
        }

    if not resolved.get("selected_physical"):
        if not resolved.get("clear_exit"):
            return {
                "ok": False,
                "profile_id": profile_id,
                "error": "No online exit-capable peer for this profile",
                "resolved": resolved,
                "hint": "Bring legacy-exit online or advertise exit on WSL/desktop",
                "dry_run": dry_run,
            }
        cmd = ["tailscale", "set", "--exit-node="]
        action = "clear_exit"
    elif resolved.get("clear_exit"):
        cmd = ["tailscale", "set", "--exit-node="]
        action = "clear_exit"
    else:
        ip = resolved["selected_physical"].get("tailscale_ip")
        if not ip:
            return {"ok": False, "error": "No tailscale IP for selected exit", "resolved": resolved}
        cmd = ["tailscale", "set", f"--exit-node={ip}"]
        action = "set_exit"

    result = {
        "ok": True,
        "profile_id": profile_id,
        "action": action,
        "command": cmd,
        "resolved": resolved,
        "dry_run": dry_run,
        "timestamp": _utc_now(),
    }

    if dry_run:
        result["note"] = "Dry-run — no tailscale changes applied"
        return result

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        result["exit_code"] = proc.returncode
        result["stdout"] = (proc.stdout or "").strip()
        result["stderr"] = (proc.stderr or "").strip()
        result["ok"] = proc.returncode == 0
        if not result["ok"] and "access denied" in (proc.stderr or "").lower():
            result["hint"] = "Run with elevated privileges: sudo tailscale set ... (Linux/WSL) or Admin shell (Windows)"
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)

    return result


def _make_slice(layer: int, slice_type: str, payload: dict, parent_hash: Optional[str]) -> dict:
    body = {
        "fractal_version": "1.0",
        "layer": layer,
        "type": slice_type,
        "parent_hash": parent_hash,
        "timestamp": _utc_now(),
        "payload": payload,
    }
    body["slice_hash"] = _sha256_obj({k: v for k, v in body.items() if k != "slice_hash"})
    return body


def build_fractal_tree() -> dict:
    """Build self-similar fractal tree of mainframe mesh state."""
    anchor_payload = {
        "masterseed": _get_masterseed_anchor(),
        "config_fingerprints": _config_fingerprints(),
        "principle": "fractal_mainframe_mesh_v1",
        "child_levels": ["node", "segment", "exit"],
    }
    anchor = _make_slice(0, "anchor", anchor_payload, None)
    anchor_hash = anchor["slice_hash"]

    roles_data = _mesh_roles_nodes()
    node_slices = []
    for node_id, node_cfg in (roles_data.get("nodes") or {}).items():
        if isinstance(node_cfg, dict):
            node_slices.append(_make_slice(1, "node", {
                "node_id": node_id,
                "config": node_cfg,
                "tailscale_self": _self_tailscale() if node_id in ("mainframe", "desktop") else None,
            }, anchor_hash))

    conn = _mesh_connectors()
    segment_slices = []
    for seg_type, ids in (("connector", conn.get("connectors", [])), ("agent", conn.get("agents", []))):
        for seg_id in ids:
            exit_cfg = load_exit_config()
            seg_route = (exit_cfg.get("segment_routing") or {}).get(seg_id, {})
            segment_slices.append(_make_slice(2, "segment", {
                "segment_type": seg_type,
                "segment_id": seg_id,
                "virtual_exit_default": seg_route.get("default_profile", exit_cfg.get("default_profile")),
                "virtual_exit_elevated": seg_route.get("elevated_profile"),
            }, anchor_hash))

    exit_cfg = load_exit_config()
    exit_slices = []
    for profile_id in (exit_cfg.get("virtual_profiles") or {}):
        exit_slices.append(_make_slice(3, "exit_profile", {
            "profile_id": profile_id,
            "resolution": resolve_virtual_profile(profile_id, exit_cfg),
        }, anchor_hash))

    all_slices = [anchor] + node_slices + segment_slices + exit_slices
    tree_hash = _sha256_obj([s["slice_hash"] for s in all_slices])

    return {
        "fractal_version": "1.0",
        "timestamp": _utc_now(),
        "tree_hash": tree_hash,
        "anchor_hash": anchor_hash,
        "slice_count": len(all_slices),
        "layers": {
            "L0_anchor": 1,
            "L1_nodes": len(node_slices),
            "L2_segments": len(segment_slices),
            "L3_exit_profiles": len(exit_slices),
        },
        "slices": all_slices,
        "mesh_snapshot": {
            "tailscale_self": _self_tailscale(),
            "peers": _tailscale_peers(),
            "mainframe": roles_data.get("mainframe"),
        },
    }


def save_fractal_tree(*, replicate_peers: bool = False) -> dict:
    """Persist fractal tree to ~/.fusion/mesh/fractal/."""
    tree = build_fractal_tree()
    FRACTAL_ROOT.mkdir(parents=True, exist_ok=True)
    SLICES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from fusion_hero_os.core.race_guard import locked_atomic_write_json
    except ImportError:
        locked_atomic_write_json = None  # type: ignore

    for sl in tree["slices"]:
        slice_path = SLICES_DIR / f"{sl['slice_hash']}.json"
        if locked_atomic_write_json is not None:
            locked_atomic_write_json(slice_path, sl)
        else:
            slice_path.write_text(json.dumps(sl, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {k: v for k, v in tree.items() if k != "slices"}
    manifest["slice_hashes"] = [s["slice_hash"] for s in tree["slices"]]
    manifest["storage_root"] = str(FRACTAL_ROOT)
    if locked_atomic_write_json is not None:
        locked_atomic_write_json(MANIFEST_PATH, manifest)
    else:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    replicas = []
    if replicate_peers:
        replicas = _replicate_manifest_to_peers(manifest)

    return {
        "ok": True,
        "tree_hash": tree["tree_hash"],
        "slice_count": tree["slice_count"],
        "manifest_path": str(MANIFEST_PATH),
        "replicas": replicas,
        "timestamp": _utc_now(),
    }


def load_fractal_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"ok": False, "error": "No fractal manifest — run save first", "path": str(MANIFEST_PATH)}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        data["ok"] = True
        return data
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _replicate_manifest_to_peers(manifest: dict) -> List[dict]:
    """Best-effort HTTP mirror of manifest to online mesh peers (hero-docs /fusion/status probe)."""
    results = []
    peers = _tailscale_peers()
    body = _canonical_json({"type": "fractal_manifest_replica", "manifest": manifest})
    for p in peers:
        if not p.get("online"):
            results.append({"peer": p.get("hostname"), "skipped": "offline"})
            continue
        dns = p.get("magicdns")
        if not dns:
            results.append({"peer": p.get("hostname"), "skipped": "no_dns"})
            continue
        url = f"http://{dns}:8088/mesh/fractal/replica"
        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                results.append({"peer": p.get("hostname"), "status": resp.status, "url": url})
        except Exception as e:
            results.append({"peer": p.get("hostname"), "error": str(e), "url": url, "dry_note": "peer may not run hero-docs yet"})
    return results


def sync_cloud_backends(manifest: Optional[dict] = None) -> dict:
    """Push fractal manifest to Supabase + Google Drive + Google GCE server."""
    try:
        from mesh_cloud_backends import sync_all_cloud_backends
        return sync_all_cloud_backends(manifest)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def setup_mainframe_mesh(
    *,
    save: bool = True,
    exit_profile: Optional[str] = None,
    apply_exit: bool = False,
    dry_run: bool = False,
    cloud_sync: bool = True,
) -> dict:
    """Full setup: fractal save + optional virtual exit apply."""
    exit_cfg = load_exit_config()
    profile = exit_profile or exit_cfg.get("default_profile", "direct")

    out: Dict[str, Any] = {
        "timestamp": _utc_now(),
        "steps": [],
        "exit_profile": profile,
    }

    if save:
        saved = save_fractal_tree(replicate_peers=not dry_run)
        out["fractal_save"] = saved
        out["steps"].append("fractal_save")

    if apply_exit:
        applied = apply_virtual_exit(profile, dry_run=dry_run)
        out["exit_apply"] = applied
        out["steps"].append("apply_exit")

    if cloud_sync and not dry_run:
        out["cloud_sync"] = sync_cloud_backends()
        out["steps"].append("cloud_sync")

    if not dry_run:
        try:
            from mesh_file_share import sync_mesh_all
            out["file_mirror_sync"] = sync_mesh_all(notify_phone=False)
            out["steps"].append("file_mirror_sync")
        except Exception as e:
            out["file_mirror_sync"] = {"ok": False, "error": str(e)}

    out["virtual_exit_catalog"] = {
        pid: resolve_virtual_profile(pid)
        for pid in (exit_cfg.get("virtual_profiles") or {})
    }
    out["fractal_status"] = get_fractal_status()
    out["ok"] = True
    return out


def get_fractal_status() -> dict:
    manifest = load_fractal_manifest()
    exit_cfg = load_exit_config()
    return {
        "timestamp": _utc_now(),
        "fractal_manifest": manifest,
        "storage_root": str(FRACTAL_ROOT),
        "virtual_exit": {
            "default_profile": exit_cfg.get("default_profile"),
            "profiles": list((exit_cfg.get("virtual_profiles") or {}).keys()),
            "active_resolution": resolve_virtual_profile(
                exit_cfg.get("default_profile", "direct"), exit_cfg
            ),
        },
        "tailscale": {
            "self": _self_tailscale(),
            "peers": _tailscale_peers(),
        },
        "mainframe_mesh_ready": manifest.get("ok", False) and _self_tailscale().get("online", False),
    }


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("Commands: status | save [--replicate] | build | apply-exit <profile> [--dry-run] | cloud-sync | setup [--exit <profile>] [--apply-exit] [--dry-run]")
        return 0

    cmd = argv[0]

    if cmd == "status":
        print(json.dumps(get_fractal_status(), indent=2, ensure_ascii=False))
        return 0

    if cmd == "build":
        print(json.dumps(build_fractal_tree(), indent=2, ensure_ascii=False))
        return 0

    if cmd == "save":
        replicate = "--replicate" in argv
        out = save_fractal_tree(replicate_peers=replicate)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1

    if cmd == "apply-exit":
        if len(argv) < 2:
            print(json.dumps({"error": "Usage: apply-exit <profile>"}, indent=2))
            return 1
        dry = "--dry-run" in argv
        out = apply_virtual_exit(argv[1], dry_run=dry)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1

    if cmd == "cloud-sync":
        out = sync_cloud_backends()
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1

    if cmd == "setup":
        exit_profile = None
        if "--exit" in argv:
            idx = argv.index("--exit")
            if idx + 1 < len(argv):
                exit_profile = argv[idx + 1]
        out = setup_mainframe_mesh(
            save=True,
            exit_profile=exit_profile,
            apply_exit="--apply-exit" in argv,
            dry_run="--dry-run" in argv,
            cloud_sync="--no-cloud" not in argv,
        )
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out.get("ok") else 1

    print(json.dumps({"error": f"Unknown command: {cmd}"}, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())