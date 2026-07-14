#!/usr/bin/env python3
"""
Fusion AI durability training — QUBO stability until convergence.

Tier 2 target: 2x A100 80GB on GKE Autopilot.
Writes checkpoints to GCS mount (or local /quantum-data).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Repo root on path when run from container with copied qb_qubo
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qb_qubo import energy, make_Q, simulated_annealing  # noqa: E402

DATA_ROOT = Path(os.environ.get("FUSION_DATA_ROOT", "/quantum-data"))
CHECKPOINT_DIR = DATA_ROOT / "checkpoints"
METRICS_PATH = DATA_ROOT / "metrics" / "training_metrics.jsonl"

STABILITY_WINDOW = int(os.environ.get("FUSION_STABILITY_WINDOW", "50"))
STABILITY_EPS = float(os.environ.get("FUSION_STABILITY_EPS", "1e-4"))
MAX_EPOCHS = int(os.environ.get("FUSION_MAX_EPOCHS", "100000"))
PROBLEM_SIZE = int(os.environ.get("FUSION_QUBO_N", "256"))
ANNEAL_STEPS = int(os.environ.get("FUSION_ANNEAL_STEPS", "4000"))
SEED_BASE = int(os.environ.get("FUSION_SEED_BASE", "42"))


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gpu_info() -> dict:
    info = {"cuda_available": False, "device_count": 0}
    try:
        import torch

        info["cuda_available"] = torch.cuda.is_available()
        info["device_count"] = torch.cuda.device_count() if info["cuda_available"] else 0
        if info["device_count"]:
            info["devices"] = [torch.cuda.get_device_name(i) for i in range(info["device_count"])]
    except Exception as exc:
        info["error"] = str(exc)
    return info


def _stability_score(history: list[float]) -> tuple[bool, float]:
    if len(history) < STABILITY_WINDOW:
        return False, float("inf")
    window = history[-STABILITY_WINDOW:]
    spread = max(window) - min(window)
    return spread <= STABILITY_EPS, spread


def train_until_stable() -> dict:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED_BASE)
    history: list[float] = []
    best_energy = float("inf")
    best_x = None
    stable = False
    epoch = 0
    started = time.time()

    print(f"[{_utc()}] Fusion stability training start n={PROBLEM_SIZE}", flush=True)
    print(json.dumps({"gpu": _gpu_info(), "config": {
        "stability_window": STABILITY_WINDOW,
        "stability_eps": STABILITY_EPS,
        "max_epochs": MAX_EPOCHS,
        "anneal_steps": ANNEAL_STEPS,
    }}), flush=True)

    while epoch < MAX_EPOCHS and not stable:
        seed = int(rng.integers(0, 2**31 - 1))
        Q = make_Q(PROBLEM_SIZE, submodular=True, scale=1.0)
        x, e = simulated_annealing(Q, steps=ANNEAL_STEPS, seed=seed)
        history.append(float(e))

        if e < best_energy:
            best_energy = float(e)
            best_x = x.copy()

        stable, spread = _stability_score(history)
        epoch += 1

        record = {
            "ts": _utc(),
            "epoch": epoch,
            "energy": float(e),
            "best_energy": best_energy,
            "stability_spread": spread,
            "stable": stable,
            "elapsed_s": round(time.time() - started, 2),
        }
        with METRICS_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        if epoch % 10 == 0 or stable:
            print(json.dumps(record), flush=True)

        if stable:
            ckpt = CHECKPOINT_DIR / f"fusion_stable_{int(time.time())}.npz"
            np.savez(
                ckpt,
                Q=Q,
                x=best_x,
                best_energy=best_energy,
                epochs=epoch,
                history=np.array(history[-STABILITY_WINDOW:]),
            )
            manifest = {
                "ok": True,
                "stable": True,
                "epochs": epoch,
                "best_energy": best_energy,
                "checkpoint": str(ckpt),
                "finished_at": _utc(),
                "gpu": _gpu_info(),
            }
            (DATA_ROOT / "fusion_training_manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            print(json.dumps(manifest), flush=True)
            return manifest

    manifest = {
        "ok": False,
        "stable": False,
        "epochs": epoch,
        "best_energy": best_energy,
        "reason": "max_epochs_without_stability",
        "finished_at": _utc(),
    }
    (DATA_ROOT / "fusion_training_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    result = train_until_stable()
    raise SystemExit(0 if result.get("stable") else 1)