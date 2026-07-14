#!/usr/bin/env python3
"""
Fusion Hero OS — Cloud backends for fractal mainframe mesh persistence.

Backends:
  1. Supabase (swmmoxhdzarmoupyssqe) — structured manifests + exit state
  2. Google Drive cold storage — FusionHero_Offload/mesh/fractal/
  3. Google server (GCE cs-724978827604-default) — Tailscale replica + exit node
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "03_Code" / "Dashboard"
PENDING_GOOGLE = Path.home() / ".fusion" / "mesh" / "fractal" / "pending_google_server.json"

GOOGLE_SERVER = {
    "hostname": os.environ.get("FUSION_GCE_MESH_HOSTNAME", "fusion-mesh-exit"),
    "gce_instance": os.environ.get("FUSION_GCE_INSTANCE", "fusion-mesh-exit"),
    "gce_project": os.environ.get("FUSION_GCE_PROJECT", "project-bbf0e6db-52e1-462b-8e3"),
    "gce_zone": os.environ.get("FUSION_GCE_ZONE", "europe-west3-a"),
    "gce_external_ip": os.environ.get("FUSION_GCE_EXTERNAL_IP", "34.40.58.207"),
    "tailscale_ip": os.environ.get("FUSION_GCE_TAILSCALE_IP", ""),
    "magicdns": os.environ.get(
        "FUSION_GCE_MAGICDNS",
        f"{os.environ.get('FUSION_GCE_MESH_HOSTNAME', 'fusion-mesh-exit')}.tail391adb.ts.net",
    ),
    "platform": "google_compute_engine",
    "replica_url": os.environ.get(
        "FUSION_GCE_REPLICA_URL",
        f"http://{os.environ.get('FUSION_GCE_MESH_HOSTNAME', 'fusion-mesh-exit')}.tail391adb.ts.net:8088/mesh/fractal/replica",
    ),
    "remote_fractal_dir": "~/.fusion/mesh/fractal",
    "legacy_hostname": "cs-724978827604-default",
}

GOOGLE_DRIVE_COLD_ROOTS = [
    Path.home() / "Google Drive-Streaming" / "Meine Ablage" / "FusionHero_Offload" / "mesh" / "fractal",
    Path.home() / "Google Drive" / "Meine Ablage" / "FusionHero_Offload" / "mesh" / "fractal",
]


def _utc_epoch() -> float:
    return time.time()


def _load_manifest(manifest: Optional[dict] = None) -> dict:
    if manifest:
        return manifest
    from fractal_mainframe_mesh import load_fractal_manifest
    loaded = load_fractal_manifest()
    if not loaded.get("ok"):
        raise ValueError(loaded.get("error", "no fractal manifest"))
    return loaded


def _supabase_store():
    if str(DASHBOARD) not in sys.path:
        sys.path.insert(0, str(DASHBOARD))
    import supabase_store as store
    return store


def sync_to_supabase(manifest: Optional[dict] = None) -> Dict[str, Any]:
    """Upsert fractal manifest + exit state to Supabase."""
    try:
        store = _supabase_store()
        man = _load_manifest(manifest)
        man["ts_epoch"] = _utc_epoch()

        if not store.is_configured():
            return {
                "ok": False,
                "backend": "supabase",
                "error": "not_configured",
                "hint": f"Create {DASHBOARD / '.env'} with SUPABASE_URL + SUPABASE_PUBLISHABLE_KEY",
                "project": "swmmoxhdzarmoupyssqe",
                "schema": "03_Code/Dashboard/supabase/schema_migration_v5_fractal_mesh.sql",
            }

        saved = store.save_fractal_manifest(man)
        exit_state = None
        try:
            from fractal_mainframe_mesh import get_fractal_status, load_exit_config
            status = get_fractal_status()
            cfg = load_exit_config()
            profile = cfg.get("default_profile", "direct")
            exit_state = store.save_mesh_exit_state(
                profile,
                status.get("virtual_exit", {}).get("active_resolution", {}),
                status.get("tailscale", {}).get("peers", []),
            )
        except Exception as exc:
            exit_state = {"ok": False, "error": str(exc)}

        return {
            "ok": bool(saved.get("ok")),
            "backend": "supabase",
            "manifest": saved,
            "exit_state": exit_state,
            "tree_hash": man.get("tree_hash"),
        }
    except Exception as exc:
        return {"ok": False, "backend": "supabase", "error": str(exc)}


def sync_to_google_drive(manifest: Optional[dict] = None) -> Dict[str, Any]:
    """Mirror manifest + slices to Google Drive cold storage (local streaming mount)."""
    try:
        man = _load_manifest(manifest)
        tree_hash = man.get("tree_hash", "unknown")
        copied_to: List[str] = []

        for root in GOOGLE_DRIVE_COLD_ROOTS:
            # cold_base = .../FusionHero_Offload (mesh/fractal may not exist yet)
            cold_base = root.parent.parent
            if not cold_base.exists():
                continue
            root.mkdir(parents=True, exist_ok=True)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
            history = root / "history"
            history.mkdir(exist_ok=True)
            hist_path = history / f"{tree_hash[:16]}.json"
            shutil.copy2(manifest_path, hist_path)
            copied_to.append(str(root))

        if not copied_to:
            return {
                "ok": False,
                "backend": "google_drive",
                "error": "no_google_drive_mount",
                "hint": "Install Google Drive for desktop or use Google Drive MCP",
            }

        return {
            "ok": True,
            "backend": "google_drive",
            "paths": copied_to,
            "tree_hash": tree_hash,
        }
    except Exception as exc:
        return {"ok": False, "backend": "google_drive", "error": str(exc)}


def _google_server_online() -> bool:
    try:
        r = subprocess.run(
            ["tailscale", "ping", "-c", "1", GOOGLE_SERVER["tailscale_ip"]],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return r.returncode == 0 and "no reply" not in (r.stdout + r.stderr).lower()
    except Exception:
        return False


def sync_to_google_server(manifest: Optional[dict] = None, *, queue_if_offline: bool = True) -> Dict[str, Any]:
    """Push fractal manifest to Google GCE node via hero-docs replica endpoint."""
    try:
        man = _load_manifest(manifest)
        if not _google_server_online():
            if queue_if_offline:
                PENDING_GOOGLE.parent.mkdir(parents=True, exist_ok=True)
                PENDING_GOOGLE.write_text(json.dumps({
                    "queued_at": _utc_epoch(),
                    "tree_hash": man.get("tree_hash"),
                    "manifest": man,
                    "target": GOOGLE_SERVER,
                }, indent=2), encoding="utf-8")
            return {
                "ok": False,
                "backend": "google_server",
                "error": "offline",
                "queued": queue_if_offline,
                "pending_path": str(PENDING_GOOGLE),
                "hostname": GOOGLE_SERVER["hostname"],
            }

        import urllib.request
        body = json.dumps({"type": "fractal_manifest_replica", "manifest": man}).encode("utf-8")
        req = urllib.request.Request(
            GOOGLE_SERVER["replica_url"],
            data=body,
            headers={"Content-Type": "application/json", "X-Mesh-Peer": "desktop-kpki9e4"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if PENDING_GOOGLE.exists():
            PENDING_GOOGLE.unlink(missing_ok=True)
        return {
            "ok": True,
            "backend": "google_server",
            "status": resp.status,
            "response": data,
            "hostname": GOOGLE_SERVER["hostname"],
        }
    except Exception as exc:
        return {"ok": False, "backend": "google_server", "error": str(exc)}


def flush_pending_google_server() -> Dict[str, Any]:
    if not PENDING_GOOGLE.exists():
        return {"ok": True, "flushed": False, "reason": "no_pending"}
    try:
        payload = json.loads(PENDING_GOOGLE.read_text(encoding="utf-8"))
        result = sync_to_google_server(payload.get("manifest"), queue_if_offline=False)
        result["flushed"] = result.get("ok", False)
        return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def sync_all_cloud_backends(manifest: Optional[dict] = None) -> Dict[str, Any]:
    """Sync fractal mesh to Supabase + Google Drive + Google server."""
    results = {
        "timestamp": _utc_epoch(),
        "supabase": sync_to_supabase(manifest),
        "google_drive": sync_to_google_drive(manifest),
        "google_server": sync_to_google_server(manifest),
    }
    pending = flush_pending_google_server()
    if pending.get("flushed"):
        results["google_server_pending_flush"] = pending
    results["ok"] = any(r.get("ok") for r in results.values() if isinstance(r, dict))
    return results


def cloud_backends_status() -> Dict[str, Any]:
    store = None
    supa_cfg = False
    try:
        store = _supabase_store()
        supa_cfg = store.is_configured()
    except Exception:
        pass

    drive_roots = [str(p) for p in GOOGLE_DRIVE_COLD_ROOTS if p.parent.exists()]
    return {
        "supabase": {
            "project": "swmmoxhdzarmoupyssqe",
            "configured": supa_cfg,
            "schema_v5": "03_Code/Dashboard/supabase/schema_migration_v5_fractal_mesh.sql",
        },
        "google_drive": {
            "cold_roots_available": drive_roots,
            "policy": "FusionHero_Offload/mesh/fractal",
        },
        "google_server": {
            **GOOGLE_SERVER,
            "online": _google_server_online(),
            "pending_queue": PENDING_GOOGLE.exists(),
            "pending_path": str(PENDING_GOOGLE),
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    cmd = argv[0] if argv else "sync"

    if cmd in ("status", "-h", "--help", "help"):
        print(json.dumps(cloud_backends_status(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "sync":
        print(json.dumps(sync_all_cloud_backends(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "supabase":
        print(json.dumps(sync_to_supabase(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "google-drive":
        print(json.dumps(sync_to_google_drive(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "google-server":
        print(json.dumps(sync_to_google_server(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "flush-pending":
        print(json.dumps(flush_pending_google_server(), indent=2, ensure_ascii=False))
        return 0

    print(json.dumps({"error": f"unknown command: {cmd}"}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())