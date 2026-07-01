# -*- coding: utf-8 -*-
"""Fusion Hero OS — Hyperthreading / Parallel-Worker Konfiguration."""
from __future__ import annotations

import os


def is_hyperthreading_enabled() -> bool:
    return os.getenv("FUSION_HYPERTHREADING", "1") != "0"


def logical_cpu_count() -> int:
    return os.cpu_count() or 4


def performance_ratio() -> float:
    env = os.getenv("FUSION_PERFORMANCE_RATIO", "").strip()
    if env:
        try:
            return max(0.1, min(1.0, float(env)))
        except ValueError:
            pass
    try:
        from fusion_profile import get_profile_config
        return float(get_profile_config().get("worker_cap_ratio", 1.0))
    except Exception:
        return 1.0


def parallel_workers(override: int | None = None) -> int:
    if override is not None and override > 0:
        return override
    base = logical_cpu_count() if is_hyperthreading_enabled() else 1
    try:
        from fusion_profile import get_profile_config
        cfg = get_profile_config()
        ratio = performance_ratio()
        reserve = int(cfg.get("reserve_workers", 0))
        return max(1, int(base * ratio) - reserve)
    except Exception:
        return base


def status() -> dict:
    cpus = logical_cpu_count()
    enabled = is_hyperthreading_enabled()
    return {
        "enabled": enabled,
        "logical_cpus": cpus,
        "workers": parallel_workers(),
        "performance_ratio": performance_ratio(),
        "env": os.getenv("FUSION_HYPERTHREADING", "1"),
    }