#!/usr/bin/env python3
"""
Fusion Hero OS — Mesh / Service / Cluster Coordinator

Unifies:
  - Tailscale live topology
  - mesh_service_coordination.yaml (external vs in-house + placement)
  - optional GKE/GCS write-back for cluster compute cycles

Modes:
  inventory  — snapshot nodes + catalog roles
  plan       — apply routing_rules → placement plan
  atlas      — light structure drift report (paths + tiers)
  all        — inventory + plan + atlas

Does not require kubectl in-process; cluster CronJob invokes this script.
Secrets stay on the operator mainframe; cluster job should use Workload Identity + GCS only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "mesh_service_coordination.yaml"
CONNECTORS_PATH = ROOT / "mesh_connectors.yaml"
LOCAL_OUT = Path.home() / ".fusion" / "mesh" / "coordination"
DEFAULT_GCS_PREFIX = os.environ.get(
    "FUSION_COORD_GCS_PREFIX",
    "gs://fusion-ai-data/coordination",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        # Minimal fallback: refuse rather than silent wrong parse
        raise SystemExit(
            f"PyYAML required to load {path}. Install: pip install pyyaml"
        )
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be a mapping")
    return data


def _run_tailscale_status() -> Dict[str, Any]:
    """Parse `tailscale status --json` when available; else plain status."""
    out: Dict[str, Any] = {"ok": False, "self": {}, "peers": [], "raw_lines": []}
    try:
        proc = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip().startswith("{"):
            data = json.loads(proc.stdout)
            self_node = data.get("Self") or {}
            out["ok"] = True
            out["self"] = {
                "hostname": (self_node.get("HostName") or self_node.get("DNSName") or "").rstrip("."),
                "online": bool(self_node.get("Online", True)),
                "ips": self_node.get("TailscaleIPs") or [],
                "os": self_node.get("OS"),
            }
            peers = []
            for _id, peer in (data.get("Peer") or {}).items():
                peers.append(
                    {
                        "hostname": (peer.get("HostName") or peer.get("DNSName") or "").rstrip("."),
                        "online": bool(peer.get("Online")),
                        "ips": peer.get("TailscaleIPs") or [],
                        "os": peer.get("OS"),
                        "exit_node": bool(peer.get("ExitNode")),
                        "last_seen": peer.get("LastSeen"),
                    }
                )
            out["peers"] = peers
            return out
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        out["json_error"] = str(exc)

    # Fallback: text status
    try:
        proc = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        lines = (proc.stdout or "").splitlines()
        out["raw_lines"] = lines
        out["ok"] = proc.returncode == 0
        for line in lines:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            entry = {
                "ip": parts[0],
                "hostname": parts[1],
                "user": parts[2],
                "os": parts[3],
                "online": "offline" not in line.lower(),
                "raw": line,
            }
            if not out["self"]:
                out["self"] = entry
            else:
                out["peers"].append(entry)
    except FileNotFoundError:
        out["error"] = "tailscale not installed or not on PATH"
    return out


def inventory(catalog: Dict[str, Any]) -> Dict[str, Any]:
    ts = _run_tailscale_status()
    roles = catalog.get("topology_roles") or {}
    matched: List[Dict[str, Any]] = []
    unmatched: List[str] = []

    hostnames = []
    if ts.get("self"):
        hostnames.append((ts["self"].get("hostname") or "").lower())
    for p in ts.get("peers") or []:
        hostnames.append((p.get("hostname") or "").lower())

    role_keys = {k.lower(): k for k in roles.keys()}
    for h in hostnames:
        if not h:
            continue
        key = role_keys.get(h)
        if key:
            meta = dict(roles[key])
            meta["hostname"] = key
            meta["live"] = True
            matched.append(meta)
        else:
            unmatched.append(h)

    offline_required = []
    for key, meta in roles.items():
        if key.lower() not in hostnames and meta.get("status_hint") not in (
            "often-offline",
            "offline-often",
            "optional",
        ):
            # still list expected but missing
            offline_required.append(key)

    return {
        "ok": bool(ts.get("ok")),
        "ts": _utc_now(),
        "tailscale": ts,
        "matched_roles": matched,
        "unmatched_hosts": unmatched,
        "expected_missing": offline_required,
        "catalog_version": catalog.get("version"),
        "inhouse_count": len(catalog.get("inhouse") or {}),
        "external_count": len(catalog.get("external") or {}),
    }


def plan(catalog: Dict[str, Any], inv: Dict[str, Any]) -> Dict[str, Any]:
    """Build placement via poly_mesh_router sole authority (no silent L1 for L3 work)."""
    # Prefer dedicated router — highest tier wins; force_cluster never falls back to L1
    try:
        sys.path.insert(0, str(ROOT))
        from fusion_hero_os.core.poly_mesh_router import probe_gke, route_all

        gke = probe_gke()
        routed = route_all()
        placements = []
        for r in routed.get("routes") or []:
            placements.append(
                {
                    "id": r.get("id"),
                    "kind": r.get("kind"),
                    "placement": r.get("chosen"),
                    "candidates": r.get("candidates"),
                    "status": r.get("status"),
                    "path": r.get("path"),
                    "force_cluster": r.get("force_cluster"),
                    "router": "poly_mesh_router",
                }
            )
        # external targets still listed from catalog
        for name, svc in (catalog.get("external") or {}).items():
            placements.append(
                {
                    "id": name,
                    "kind": "external",
                    "placement": svc.get("placement", "L4_external_saas"),
                    "owner_inhouse": svc.get("owner_inhouse"),
                    "type": svc.get("type"),
                    "status": "external-target",
                    "router": "poly_mesh_router",
                }
            )
        flags = []
        for ap in catalog.get("anti_patterns") or []:
            flags.append(
                {"id": ap.get("id"), "description": ap.get("description"), "severity": "policy"}
            )
        cluster_jobs = []
        if gke.get("ok"):
            for job_id, job in ((catalog.get("cluster_coordination") or {}).get("jobs") or {}).items():
                cluster_jobs.append(
                    {
                        "id": job_id,
                        "description": job.get("description"),
                        "cpu": job.get("cpu"),
                        "memory": job.get("memory"),
                        "args": job.get("args"),
                        "status": "schedulable_on_cluster_only",
                    }
                )
        else:
            cluster_jobs.append(
                {
                    "id": "_gate",
                    "status": "blocked",
                    "reason": gke.get("error") or "GKE not live (kubectl Ready nodes required)",
                }
            )
        return {
            "ts": _utc_now(),
            "online_tiers": (routed.get("routes") or [{}])[0].get("online_tiers")
            or sorted({t for t in (routed.get("routes") or []) for t in (t.get("online_tiers") or [])}),
            "placements": placements,
            "cluster_jobs": cluster_jobs,
            "anti_patterns": flags,
            "routing_rules": catalog.get("routing_rules") or [],
            "gke_probe": {
                "ok": gke.get("ok"),
                "ready_nodes": gke.get("ready_nodes"),
                "context": gke.get("context"),
                "error": gke.get("error"),
            },
            "router_counts": routed.get("counts"),
            "sole_authority": "poly_mesh_router",
            "no_local_dual_start": True,
        }
    except Exception as exc:  # noqa: BLE001
        # Fail closed: do not invent L3 from bare kubeconfig
        return {
            "ts": _utc_now(),
            "online_tiers": [],
            "placements": [],
            "cluster_jobs": [
                {"id": "_gate", "status": "blocked", "reason": f"router_import_failed:{exc}"}
            ],
            "anti_patterns": [],
            "routing_rules": catalog.get("routing_rules") or [],
            "error": str(exc)[:400],
            "sole_authority": "poly_mesh_router",
            "no_local_dual_start": True,
        }


def atlas(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Structure drift: catalog paths that should exist in repo."""
    missing = []
    present = []
    for name, svc in (catalog.get("inhouse") or {}).items():
        rel = svc.get("path")
        if not rel:
            continue
        p = ROOT / rel
        if p.exists():
            present.append({"id": name, "path": rel})
        else:
            missing.append({"id": name, "path": rel})

    connectors = {}
    if CONNECTORS_PATH.is_file():
        try:
            connectors = _load_yaml(CONNECTORS_PATH)
        except Exception as exc:  # noqa: BLE001
            connectors = {"error": str(exc)}

    return {
        "ts": _utc_now(),
        "repo_root": str(ROOT),
        "inhouse_present": present,
        "inhouse_missing_paths": missing,
        "connector_keys": list((connectors.get("connectors") or {}).keys()),
        "drift_score": len(missing),
    }


def write_local(report: Dict[str, Any], name: str) -> Path:
    """Race-safe write: exclusive lock + atomic replace (desktop + GCE cron)."""
    LOCAL_OUT.mkdir(parents=True, exist_ok=True)
    path = LOCAL_OUT / f"{name}.json"
    latest = LOCAL_OUT / "latest.json"
    try:
        from fusion_hero_os.core.race_guard import locked_atomic_write_json
    except ImportError:
        # GCE / thin checkout: load sibling package path
        sys.path.insert(0, str(ROOT))
        from fusion_hero_os.core.race_guard import locked_atomic_write_json  # type: ignore

    payload = dict(report)
    payload.setdefault("race_guard", True)
    locked_atomic_write_json(path, payload)
    locked_atomic_write_json(latest, payload)
    return path


def upload_gcs(local_path: Path, prefix: str = DEFAULT_GCS_PREFIX) -> Dict[str, Any]:
    """Best-effort GCS upload via google-cloud-storage (WI) or gsutil fallback.

    On GKE Autopilot the image uses Workload Identity → ADC; gsutil is optional.
    Never fails the whole run hard if offline.
    """
    if not prefix.startswith("gs://"):
        return {"ok": False, "error": "invalid gcs prefix"}
    raw = prefix[len("gs://") :].rstrip("/")
    if "/" in raw:
        bucket_name, blob_prefix = raw.split("/", 1)
    else:
        bucket_name, blob_prefix = raw, ""
    object_name = f"{blob_prefix.rstrip('/')}/{local_path.name}".lstrip("/")
    dest = f"gs://{bucket_name}/{object_name}"
    latest_name = f"{blob_prefix.rstrip('/')}/latest.json".lstrip("/")
    client_err: Optional[str] = None

    # Prefer official client (ADC / Workload Identity on GKE)
    try:
        from google.cloud import storage  # type: ignore

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        bucket.blob(object_name).upload_from_filename(
            str(local_path),
            content_type="application/json",
        )
        if latest_name and latest_name != object_name:
            bucket.blob(latest_name).upload_from_filename(
                str(local_path),
                content_type="application/json",
            )
        return {
            "ok": True,
            "dest": dest,
            "backend": "google-cloud-storage",
            "latest": f"gs://{bucket_name}/{latest_name}" if latest_name else None,
        }
    except ImportError:
        client_err = "google-cloud-storage not installed"
    except Exception as exc:  # noqa: BLE001
        client_err = str(exc)[:400]

    try:
        proc = subprocess.run(
            ["gsutil", "cp", str(local_path), dest],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "dest": dest,
            "backend": "gsutil",
            "stderr": (proc.stderr or "")[:500],
            "client_error": client_err,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "neither google-cloud-storage nor gsutil available",
            "client_error": client_err,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "gsutil timeout", "client_error": client_err}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fusion mesh/service/cluster coordinator")
    parser.add_argument(
        "--mode",
        choices=["inventory", "plan", "atlas", "all"],
        default="all",
    )
    parser.add_argument("--upload-gcs", action="store_true")
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    catalog = _load_yaml(args.catalog)
    report: Dict[str, Any] = {
        "mode": args.mode,
        "generated_at": _utc_now(),
        "platform_version": catalog.get("platform_version"),
        "catalog_id": catalog.get("catalog_id"),
        "epoch": time.time(),
    }

    inv = None
    if args.mode in ("inventory", "plan", "all"):
        inv = inventory(catalog)
        report["inventory"] = inv

    if args.mode in ("plan", "all"):
        if inv is None:
            inv = inventory(catalog)
            report["inventory"] = inv
        report["plan"] = plan(catalog, inv)

    if args.mode in ("atlas", "all"):
        report["atlas"] = atlas(catalog)

    out_name = f"coordination_{args.mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    path = write_local(report, out_name)
    report["local_path"] = str(path)

    if args.upload_gcs:
        report["gcs"] = upload_gcs(path, args.gcs_prefix)
        # rewrite with gcs result (race-safe)
        write_local(report, path.stem)
        write_local(report, "latest")

    if not args.quiet:
        summary = {
            "mode": args.mode,
            "local_path": str(path),
            "inventory_ok": (report.get("inventory") or {}).get("ok"),
            "matched_roles": len((report.get("inventory") or {}).get("matched_roles") or []),
            "online_tiers": (report.get("plan") or {}).get("online_tiers"),
            "drift_score": (report.get("atlas") or {}).get("drift_score"),
            "gcs": report.get("gcs"),
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
