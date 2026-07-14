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

# EUR/h Schätzungen (Senfkorn UG / europe-west3)
_RATES = {
    "gce_e2_micro_month": 7.50,
    "gcs_storage_gb_month": 0.02,
    "gke_autopilot_mgmt_month": 0.0,  # Freibetrag 1 Cluster
    "l4_gpu_hour": 0.55,
    "a100_gpu_hour": 3.75,
    "cpu_pod_hour": 0.05,
}


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

    def _kubectl_pods(self) -> List[Dict[str, Any]]:
        kubectl = os.getenv("KUBECTL_PATH", "kubectl")
        ns = os.getenv("FUSION_TRAINING_NAMESPACE", "fusion-training")
        try:
            r = subprocess.run(
                [kubectl, "get", "pods", "-n", ns, "-o", "json"],
                capture_output=True, text=True, timeout=12,
                env={**os.environ, "USE_GKE_GCLOUD_AUTH_PLUGIN": "True"},
            )
            if r.returncode != 0:
                return []
            data = json.loads(r.stdout)
            return data.get("items", [])
        except Exception:
            return []

    def _estimate_gke_burn(self, pods: List[Dict[str, Any]]) -> Dict[str, Any]:
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

        hour = (
            running * _RATES["cpu_pod_hour"]
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
        }

    def _estimate_infra_fixed(self) -> Dict[str, Any]:
        bucket_gb = float(os.getenv("FUSION_GCS_BUCKET_GB", "10"))
        return {
            "gce_fusion_mesh_exit_eur_month": _RATES["gce_e2_micro_month"],
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
        pods = self._kubectl_pods()
        gke = self._estimate_gke_burn(pods)
        fixed = self._estimate_infra_fixed()
        ewma = self._local_ewma()

        hour_burn = gke["eur_hour"]
        month_est = (
            fixed["gce_fusion_mesh_exit_eur_month"]
            + fixed["gcs_storage_eur_month"]
            + fixed["gke_mgmt_eur_month"]
            + hour_burn * 24 * 30
        )

        alerts: List[str] = []
        if gke["pods_pending"] > 0 and gke["pods_running"] == 0:
            alerts.append("GKE training pending — GPU Kapazität/Quota prüfen")
        if hour_burn > 5.0:
            alerts.append(f"Hoher Stunden-Burn: ~{hour_burn:.2f} EUR/h")

        try:
            from core.cost_estimator_node import CostEstimatorNode
            CostEstimatorNode().observe("gcp", "gke_training_burn", hour_burn)
        except Exception:
            pass

        snap = CostSnapshot(
            ts=time.time(),
            total_eur_month_est=round(month_est, 2),
            total_eur_hour_burn=round(hour_burn, 4),
            breakdown={"gke": gke, "fixed": fixed, "ewma": ewma},
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