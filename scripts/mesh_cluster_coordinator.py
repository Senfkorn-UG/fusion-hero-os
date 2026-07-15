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
    """Build a placement plan for each in-house + external capability."""
    online_tiers = set()
    for m in inv.get("matched_roles") or []:
        if m.get("live"):
            online_tiers.add(m.get("tier"))

    # Cluster is "available" if kubeconfig exists (may still fail auth)
    kube = Path.home() / ".kube" / "config"
    if kube.is_file():
        online_tiers.add("L3_cluster")

    placements: List[Dict[str, Any]] = []
    for name, svc in (catalog.get("inhouse") or {}).items():
        raw = svc.get("placement")
        candidates = raw if isinstance(raw, list) else [raw]
        chosen = None
        for c in candidates:
            if c in online_tiers or c == "L4_external_saas":
                chosen = c
                break
        if chosen is None:
            chosen = candidates[0] if candidates else "L1_mainframe"
            status = "deferred-offline"
        else:
            status = "ready"
        placements.append(
            {
                "id": name,
                "kind": "inhouse",
                "placement": chosen,
                "candidates": candidates,
                "status": status,
                "path": svc.get("path"),
            }
        )

    for name, svc in (catalog.get("external") or {}).items():
        placements.append(
            {
                "id": name,
                "kind": "external",
                "placement": svc.get("placement", "L4_external_saas"),
                "owner_inhouse": svc.get("owner_inhouse"),
                "type": svc.get("type"),
                "status": "external-target",
            }
        )

    # Anti-pattern checks
    flags = []
    for ap in catalog.get("anti_patterns") or []:
        flags.append({"id": ap.get("id"), "description": ap.get("description"), "severity": "policy"})

    # Prefer cluster for heavy jobs if L3 available
    cluster_jobs = []
    if "L3_cluster" in online_tiers:
        for job_id, job in ((catalog.get("cluster_coordination") or {}).get("jobs") or {}).items():
            cluster_jobs.append(
                {
                    "id": job_id,
                    "description": job.get("description"),
                    "cpu": job.get("cpu"),
                    "memory": job.get("memory"),
                    "args": job.get("args"),
                    "status": "schedulable",
                }
            )
    else:
        cluster_jobs.append(
            {
                "id": "_gate",
                "status": "blocked",
                "reason": "L3_cluster health gate not satisfied (no kubeconfig or no auth)",
            }
        )

    return {
        "ts": _utc_now(),
        "online_tiers": sorted(t for t in online_tiers if t),
        "placements": placements,
        "cluster_jobs": cluster_jobs,
        "anti_patterns": flags,
        "routing_rules": catalog.get("routing_rules") or [],
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
    """Best-effort gsutil upload; never fails the whole run hard if offline."""
    if not prefix.startswith("gs://"):
        return {"ok": False, "error": "invalid gcs prefix"}
    dest = f"{prefix.rstrip('/')}/{local_path.name}"
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
            "stderr": (proc.stderr or "")[:500],
        }
    except FileNotFoundError:
        return {"ok": False, "error": "gsutil not on PATH"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "gsutil timeout"}


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
