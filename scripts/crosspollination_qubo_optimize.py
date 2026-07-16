#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crosspollination QUBO — Wichtungen / Assoziationsgewichte optimieren (klassisch).

Maps multi-source "cross-pollination" weights into QUBO and solves
    min_x  x^T Q x   over x in {0,1}^n
with parallel restarts (Numba / HT). Not quantum hardware — classical SA/QAOA-class.

Env:
  FUSION_QUBO_N              problem size (default 512 best-of-best; 256 light)
  FUSION_ANNEAL_STEPS        SA steps (default 12000)
  FUSION_N_RESTARTS          parallel restarts (default = CPU count)
  FUSION_CROSS_SOURCES       comma labels for cross-pollination sources
  FUSION_WEIGHT_SEED         RNG seed
  FUSION_DATA_ROOT           output root (default /quantum-data)
  FUSION_CARDINALITY_K       optional select-k soft constraint
  FUSION_CARDINALITY_PENALTY default 5.0

Output: metrics JSON + best assignment under FUSION_DATA_ROOT/crosspollination/
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "03_Code"))

N = int(os.environ.get("FUSION_QUBO_N", "512"))
STEPS = int(os.environ.get("FUSION_ANNEAL_STEPS", "12000"))
RESTARTS = os.environ.get("FUSION_N_RESTARTS")
SEED = int(os.environ.get("FUSION_WEIGHT_SEED", "42"))
DATA = Path(os.environ.get("FUSION_DATA_ROOT", "/quantum-data"))
OUT = DATA / "crosspollination"
def _default_cross_sources() -> str:
    """Core-first sources: pure-core membrane (formal math + algos + foreign)."""
    try:
        from fusion_hero_os.core.pure_core_coevolution import crosspoll_sources

        return ",".join(crosspoll_sources())
    except Exception:
        return (
            "formal_math,diverse_algorithms,pure_core,"
            "mesh,cluster,llm,saas,ascension,operator"
        )


SOURCES = [
    s.strip()
    for s in os.environ.get(
        "FUSION_CROSS_SOURCES",
        _default_cross_sources(),
    ).split(",")
    if s.strip()
]
K = os.environ.get("FUSION_CARDINALITY_K")
K_PEN = float(os.environ.get("FUSION_CARDINALITY_PENALTY", "5.0"))


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_crosspollination_Q(
    n: int,
    sources: list[str],
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict]:
    """
    Cross-pollination weight QUBO:
      - diagonal: source-affinity / node value (to maximize → negative on diag)
      - off-diag: symmetric association (cross-source pollination rewards)
      - optional cardinality soft constraint
    """
    Q = np.zeros((n, n), dtype=np.float64)
    # node values: multi-source score
    n_src = max(1, len(sources))
    # each node gets a value vector over sources → mean + variance bonus (diversity)
    V = rng.random((n, n_src))
    values = V.mean(axis=1) + 0.15 * V.std(axis=1)
    for i in range(n):
        Q[i, i] -= float(values[i])

    # Hebbian-like association: outer product of normalized value vectors
    # rewards co-selecting nodes that cross-pollinate strongly
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    A = Vn @ Vn.T  # cosine similarity
    np.fill_diagonal(A, 0.0)
    # only upper triangle contribution (symmetrize into Q)
    w_assoc = 0.35
    for i in range(n):
        for j in range(i + 1, n):
            w = w_assoc * float(A[i, j])
            Q[i, j] -= 0.5 * w
            Q[j, i] -= 0.5 * w

    meta = {
        "sources": sources,
        "n": n,
        "assoc_scale": w_assoc,
        "value_mean": float(values.mean()),
        "value_std": float(values.std()),
    }

    if K is not None:
        k = int(K)
        # soft (sum x_i - k)^2 → expand into Q
        # (1^T x - k)^2 = sum_i sum_j x_i x_j - 2k sum_i x_i + k^2
        for i in range(n):
            Q[i, i] += K_PEN * (1.0 - 2.0 * k)
            for j in range(i + 1, n):
                Q[i, j] += K_PEN
                Q[j, i] += K_PEN
        meta["cardinality_k"] = k
        meta["cardinality_penalty"] = K_PEN

    # ensure symmetry
    Q = 0.5 * (Q + Q.T)
    return Q, meta


def solve(Q: np.ndarray) -> dict:
    n_restarts = int(RESTARTS) if RESTARTS else None
    try:
        from qb_qubo import parallel_anneal, simulated_annealing, energy

        t0 = time.time()
        if n_restarts and n_restarts > 1:
            res = parallel_anneal(
                Q, steps=STEPS, T0=2.0, n_restarts=n_restarts, n_samples=80
            )
            # parallel_anneal returns dict: solution, energy, ...
            if isinstance(res, dict):
                x = np.asarray(
                    res.get("solution")
                    if res.get("solution") is not None
                    else res.get("x", res.get("best_x")),
                    dtype=np.float64,
                ).reshape(-1)
                e = float(res.get("energy", energy(Q, x)))
                backend = "qb_qubo.parallel_anneal"
                n_restarts = int(res.get("n_restarts") or n_restarts or 1)
            else:
                x, e = res if isinstance(res, tuple) else (res, energy(Q, res))
                x = np.asarray(x, dtype=np.float64).reshape(-1)
                backend = "qb_qubo.parallel_anneal"
        else:
            x, e = simulated_annealing(Q, steps=STEPS, T0=2.0)
            x = np.asarray(x, dtype=np.float64).reshape(-1)
            backend = "qb_qubo.simulated_annealing"
        x_int = np.clip(np.rint(x), 0, 1).astype(int)
        return {
            "ok": True,
            "backend": backend,
            "energy": float(e),
            "x": x_int.tolist(),
            "ones": int(x_int.sum()),
            "seconds": round(time.time() - t0, 3),
            "n_restarts": n_restarts or 1,
            "steps": STEPS,
        }
    except Exception as exc:
        # numpy fallback
        rng = np.random.default_rng(SEED)
        n = Q.shape[0]
        x = rng.integers(0, 2, size=n).astype(np.float64)
        e = float(x @ Q @ x)
        T0, T1 = 2.0, 0.02
        t0 = time.time()
        best_x, best_e = x.copy(), e
        for step in range(STEPS):
            T = T0 * (T1 / T0) ** (step / max(STEPS - 1, 1))
            i = int(rng.integers(0, n))
            # delta for flip
            dE = float((1 - 2 * x[i]) * (2 * (Q[i] @ x) - Q[i, i] * (2 * x[i] - 1) * 0 + Q[i, i]))
            # exact delta: e' - e for flip x_i
            s = 0.0
            for j in range(n):
                if j != i:
                    s += Q[i, j] * x[j]
            dE = (1 - 2 * x[i]) * (Q[i, i] + 2 * s)
            if dE <= 0 or rng.random() < np.exp(-dE / max(T, 1e-12)):
                x[i] = 1.0 - x[i]
                e += dE
                if e < best_e:
                    best_e, best_x = e, x.copy()
        return {
            "ok": True,
            "backend": "numpy_sa_fallback",
            "energy": float(best_e),
            "x": best_x.astype(int).tolist(),
            "ones": int(best_x.sum()),
            "seconds": round(time.time() - t0, 3),
            "n_restarts": 1,
            "steps": STEPS,
            "fallback_error": str(exc)[:200],
        }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    print(json.dumps({
        "task": "crosspollination_qubo_optimize",
        "started_at": _utc(),
        "n": N,
        "steps": STEPS,
        "sources": SOURCES,
        "tier_hint": "L3_cluster force_cluster",
        "note": "Classical SA — not quantum hardware",
    }, indent=2), flush=True)

    Q, meta = build_crosspollination_Q(N, SOURCES, rng)
    sol = solve(Q)

    weights_selected = {
        "n_selected": sol["ones"],
        "fraction": round(sol["ones"] / max(N, 1), 6),
        "indices": [i for i, v in enumerate(sol["x"]) if v == 1][:64],
        "indices_truncated": sol["ones"] > 64,
    }

    receipt = {
        "ok": sol.get("ok", False),
        "task": "crosspollination_qubo_weights",
        "platform_version": "10.0.0",
        "cost_function_version": "2.0.0",
        "algo_class": "force_cluster_compute",
        "sole_authority": "poly_mesh_router",
        "tier": "L3_cluster",
        "no_local_dual_start": True,
        "finished_at": _utc(),
        "problem": meta,
        "solution": sol,
        "weights": weights_selected,
        "server_class": os.environ.get("FUSION_SERVER_CLASS", "a100-best-of-best"),
    }

    out_path = OUT / f"crosspoll_{_utc().replace(':', '').replace('+', 'p')}.json"
    latest = OUT / "latest.json"
    text = json.dumps(receipt, indent=2)
    out_path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps(receipt, indent=2), flush=True)
    print(
        f"BANNER: CROSSPOLL QUBO ok={receipt['ok']} E={sol.get('energy')} "
        f"backend={sol.get('backend')} n={N} selected={sol.get('ones')} "
        f"sec={sol.get('seconds')}",
        flush=True,
    )
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
