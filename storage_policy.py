# -*- coding: utf-8 -*-
"""Fusion Hero OS — Google-Drive-Speicherpolitik (Single Source of Truth)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

POLICY_REL = Path("workstation") / "storage_policy.json"


def _fusion_root() -> Path:
    env = os.environ.get("FUSION_HERO_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent.parent
    return here


def _expand(path: str) -> str:
    return path.replace("{USERPROFILE}", os.environ.get("USERPROFILE", r"C:\Users\Admin"))


def load_policy(fusion_root: Optional[Path] = None) -> Dict[str, Any]:
    root = fusion_root or _fusion_root()
    policy_path = root / POLICY_REL
    if not policy_path.is_file():
        return {}
    with open(policy_path, encoding="utf-8") as f:
        return json.load(f)


def resolve_gdrive_paths(policy: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Path], Optional[Path]]:
    """Returns (library_root, cold_offload_root)."""
    policy = policy or load_policy()
    gd = policy.get("google_drive", {})
    library = gd.get("library", "Meine Ablage")
    cold = gd.get("cold_root", "FusionHero_Offload")
    for mount in gd.get("mount_candidates", []):
        base = Path(_expand(mount))
        if not base.is_dir():
            continue
        lib_path = base / library
        if lib_path.is_dir() or base.is_dir():
            cold_path = lib_path / cold
            return lib_path, cold_path
    return None, None


def resolve_gdrive_offload_root(policy: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    env = os.environ.get("FUSION_GDRIVE_OFFLOAD")
    if env:
        return Path(env)
    _, cold = resolve_gdrive_paths(policy)
    return cold


def offload_folder_map(policy: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
    policy = policy or load_policy()
    rows = policy.get("offload_folders", [])
    out: List[Tuple[str, str]] = []
    for row in rows:
        out.append((row["src"], row["dst"]))
    return out


def thresholds(policy: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    policy = policy or load_policy()
    return policy.get("thresholds", {})
