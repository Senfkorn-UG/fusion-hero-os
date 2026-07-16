# -*- coding: utf-8 -*-
"""
Dauerhafte Kostenanalyse — Mainframe Daemon (GCP + Mesh + lokale EWMA).
Schreibt Snapshots nach ~/.fusion-hero-os/mainframe_cost_analysis/
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_INTERVAL = float(os.getenv("FUSION_COST_ANALYSIS_INTERVAL_SEC", "60"))
_STATE = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os"))) / "mainframe_cost_analysis"

# EUR rates v2.0 (Senfkorn UG / europe-west3 / poly-mesh L0–L4) — 2026-07
_RATES = {
    "gce_e2_micro_month": 7.50,
    "gce_e2_micro_hour": 7.50 / 730.0,
    "gcs_storage_gb_month": 0.023,
    "gke_autopilot_mgmt_month": 0.0,  # Freibetrag 1 Cluster
    "l4_gpu_hour": 0.70,
    "a100_gpu_hour": 3.90,
    "cpu_pod_hour": 0.06,
    "cpu_light_job_hour": 0.03,  # coordination / poly-mesh orchestration
    "l1_desk_power_hour": 0.08,
    "l4_saas_api_est_hour": 0.02,
}
_COST_FUNCTION_VERSION = "2.0.0"


def _state_dir() -> Path:
    p = _STATE
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class CostSnapshot:
    ts: float
    total_eur_month_est: float
    total_eur_hour_burn: float
    breakdown: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MainframeCostAnalysisDaemon:
    def __init__(self) -> None:
        self._last: Optional[CostSnapshot] = None
        self._history_path = _state_dir() / "history.jsonl"
        self._snapshot_path = _state_dir() / "snapshot.json"
        self._running = False
        self._ticks = 0

    def _kubectl_bin(self) -> str:
        env = os.getenv("KUBECTL_PATH", "").strip()
        if env:
            return env
        local = Path.home() / ".local" / "bin" / "kubectl.exe"
        if local.is_file():
            return str(local)
        return "kubectl"

    def _kubectl_pods(self, namespace: str) -> List[Dict[str, Any]]:
        kubectl = self._kubectl_bin()
        try:
            r = subprocess.run(
                [kubectl, "get", "pods", "-n", namespace, "-o", "json"],
                capture_output=True, text=True, timeout=12,
                env={**os.environ, "USE_GKE_GCLOUD_AUTH_PLUGIN": "True"},
            )
            if r.returncode != 0:
                return []
            data = json.loads(r.stdout)
            return data.get("items", [])
        except Exception:
            return []

    def _estimate_gke_burn(self, pods: List[Dict[str, Any]], *, light: bool = False) -> Dict[str, Any]:
        running = 0
        pending = 0
        gpu_l4 = 0
        gpu_a100 = 0
        for pod in pods:
            phase = (pod.get("status") or {}).get("phase", "")
            if phase == "Running":
                running += 1
            elif phase == "Pending":
                pending += 1
            for c in (pod.get("spec") or {}).get("containers", []):
                limits = (c.get("resources") or {}).get("limits", {})
                gpus = limits.get("nvidia.com/gpu", "0")
                try:
                    n = int(str(gpus))
                except ValueError:
                    n = 0
                sel = (pod.get("spec") or {}).get("nodeSelector", {})
                acc = sel.get("cloud.google.com/gke-accelerator", "")
                if "l4" in acc:
                    gpu_l4 += n
                elif "a100" in acc:
                    gpu_a100 += n

        cpu_rate = _RATES["cpu_light_job_hour"] if light else _RATES["cpu_pod_hour"]
        hour = (
            running * cpu_rate
            + gpu_l4 * _RATES["l4_gpu_hour"]
            + gpu_a100 * _RATES["a100_gpu_hour"]
        )
        return {
            "pods_running": running,
            "pods_pending": pending,
            "gpu_l4": gpu_l4,
            "gpu_a100": gpu_a100,
            "eur_hour": round(hour, 4),
            "eur_day_if_constant": round(hour * 24, 2),
            "light": light,
        }

    def _estimate_infra_fixed(self) -> Dict[str, Any]:
        bucket_gb = float(os.getenv("FUSION_GCS_BUCKET_GB", "10"))
        # L2: mesh-exit + optional subnet-router (env override)
        exits = int(os.getenv("FUSION_MESH_EXIT_NODES", "2"))
        return {
            "gce_fusion_mesh_exit_eur_month": round(
                exits * _RATES["gce_e2_micro_month"], 2
            ),
            "mesh_exit_nodes": exits,
            "gcs_storage_eur_month": round(bucket_gb * _RATES["gcs_storage_gb_month"], 2),
            "gke_mgmt_eur_month": _RATES["gke_autopilot_mgmt_month"],
        }

    def _local_ewma(self) -> Dict[str, Any]:
        try:
            from core.cost_estimator_node import CostEstimatorNode
            node = CostEstimatorNode()
            stats = [s.to_dict() for s in node.stats.values()]
            return {"keys": len(stats), "top": sorted(stats, key=lambda x: -x.get("ewma", 0))[:8]}
        except Exception as exc:
            return {"error": str(exc)}

    def tick(self) -> CostSnapshot:
        train_ns = os.getenv("FUSION_TRAINING_NAMESPACE", "fusion-training")
        coord_ns = os.getenv("FUSION_COORD_NAMESPACE", "fusion-coordination")
        pods_train = self._kubectl_pods(train_ns)
        pods_coord = self._kubectl_pods(coord_ns)
        gke_train = self._estimate_gke_burn(pods_train, light=False)
        gke_coord = self._estimate_gke_burn(pods_coord, light=True)
        fixed = self._estimate_infra_fixed()
        ewma = self._local_ewma()

        # Poly-mesh C_h = C_L1 + C_L2 + C_L3 (+ soft L4)
        l1 = _RATES["l1_desk_power_hour"]
        l2 = fixed.get("mesh_exit_nodes", 1) * _RATES["gce_e2_micro_hour"]
        l3 = gke_train["eur_hour"] + gke_coord["eur_hour"]
        l4 = _RATES["l4_saas_api_est_hour"] if os.getenv("FUSION_SAAS_ACTIVE", "0") == "1" else 0.0
        hour_burn = l1 + l2 + l3 + l4
        month_est = (
            fixed["gce_fusion_mesh_exit_eur_month"]
            + fixed["gcs_storage_eur_month"]
            + fixed["gke_mgmt_eur_month"]
            + hour_burn * 24 * 30
        )

        alerts: List[str] = []
        if gke_train["pods_pending"] > 0 and gke_train["pods_running"] == 0:
            alerts.append("GKE training pending — GPU Kapazität/Quota prüfen")
        if hour_burn > 5.0:
            alerts.append(f"Hoher Stunden-Burn: ~{hour_burn:.2f} EUR/h")

        try:
            from core.cost_estimator_node import CostEstimatorNode
            CostEstimatorNode().observe("gcp", "gke_training_burn", hour_burn)
        except Exception:
            pass

        # unified cost function module (optional enrich)
        poly = {}
        try:
            from fusion_hero_os.core.poly_mesh_cost_function import compute_burn

            b = compute_burn(
                gke_pods_running=gke_train["pods_running"],
                gke_pods_pending=gke_train["pods_pending"],
                gpu_l4=gke_train["gpu_l4"],
                gpu_a100=gke_train["gpu_a100"],
                coordination_jobs_running=gke_coord["pods_running"],
                mesh_exit_nodes=int(fixed.get("mesh_exit_nodes") or 1),
                l1_power_eur_h=l1,
                l4_saas_active=l4 > 0,
            )
            poly = b.to_dict()
            hour_burn = b.total_eur_h
            month_est = b.total_eur_month
        except Exception as exc:
            poly = {"note": f"poly_mesh_cost_function unavailable: {exc}"[:160]}

        snap = CostSnapshot(
            ts=time.time(),
            total_eur_month_est=round(month_est, 2),
            total_eur_hour_burn=round(hour_burn, 4),
            breakdown={
                "cost_function_version": _COST_FUNCTION_VERSION,
                "layers": {
                    "L1_eur_h": round(l1, 6),
                    "L2_eur_h": round(l2, 6),
                    "L3_eur_h": round(l3, 6),
                    "L4_eur_h": round(l4, 6),
                    "formula": "C_h = C_L1 + C_L2 + C_L3 + C_L4",
                },
                "gke_training": gke_train,
                "gke_coordination": gke_coord,
                "fixed": fixed,
                "ewma": ewma,
                "poly_mesh": poly,
            },
            alerts=alerts,
        )
        self._last = snap
        self._ticks += 1
        payload = snap.to_dict()
        self._snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with self._history_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return snap

    def status(self) -> Dict[str, Any]:
        hist: List[Dict[str, Any]] = []
        if self._history_path.exists():
            try:
                lines = self._history_path.read_text(encoding="utf-8").strip().splitlines()
                for line in lines[-120:]:
                    hist.append(json.loads(line))
            except Exception:
                pass
        return {
            "daemon": "mainframe_cost_analysis",
            "running": self._running,
            "ticks": self._ticks,
            "interval_sec": _INTERVAL,
            "snapshot": self._last.to_dict() if self._last else None,
            "history_points": len(hist),
            "history": hist[-60:],
            "rates": _RATES,
            "cost_function_version": _COST_FUNCTION_VERSION,
        }

    def start_background(self) -> bool:
        if self._running:
            return False
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False


_daemon: Optional[MainframeCostAnalysisDaemon] = None


def get_cost_daemon() -> MainframeCostAnalysisDaemon:
    global _daemon
    if _daemon is None:
        _daemon = MainframeCostAnalysisDaemon()
    return _daemon