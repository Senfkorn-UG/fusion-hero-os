# -*- coding: utf-8 -*-
"""Repository structure registry for mainframe mirror + visualization."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(os.getenv("FUSION_REPO_ROOT", Path(__file__).resolve().parents[2]))
_SKIP = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", "dist", "build", ".fusion", ".cursor",
}
_LAYER_MAP = {
    "03_Code": "L2_application",
    "fusion_hero_os": "L2_application",
    "src": "L2_application",
    "kernel": "L1_kernel",
    "infra": "L3_infrastructure",
    "workstation": "L3_infrastructure",
    "01_Framework": "L0_framework",
    "02_Mathematik": "L1_math",
    "mesh_": "L3_mesh",
    "hero-docs": "L2_services",
}


def repo_root() -> Path:
    return _REPO


def _layer_for(path: Path) -> str:
    name = path.name
    for prefix, layer in _LAYER_MAP.items():
        if name.startswith(prefix) or name == prefix.rstrip("_"):
            return layer
    return "L2_application"


def scan_structure(*, max_depth: int = 4) -> Dict[str, Any]:
    root = repo_root()
    if not root.exists():
        return {"ok": False, "error": f"repo missing: {root}"}

    nodes: List[Dict[str, Any]] = []
    file_count = 0
    dir_count = 0

    def walk(base: Path, depth: int, parent_id: str) -> None:
        nonlocal file_count, dir_count
        if depth > max_depth:
            return
        try:
            entries = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for entry in entries:
            if entry.name in _SKIP or entry.name.startswith("."):
                continue
            rel = entry.relative_to(root).as_posix()
            node_id = rel or "."
            if entry.is_dir():
                dir_count += 1
                layer = _layer_for(entry)
                nodes.append({
                    "id": node_id,
                    "name": entry.name,
                    "type": "dir",
                    "parent": parent_id,
                    "layer": layer,
                    "depth": depth,
                })
                walk(entry, depth + 1, node_id)
            else:
                file_count += 1
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                nodes.append({
                    "id": node_id,
                    "name": entry.name,
                    "type": "file",
                    "parent": parent_id,
                    "layer": _layer_for(entry.parent),
                    "depth": depth,
                    "size": size,
                })

    walk(root, 0, "")
    tree_hash = hashlib.sha256(
        json.dumps(nodes, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    layers: Dict[str, int] = {}
    for n in nodes:
        if n["type"] == "dir":
            layers[n["layer"]] = layers.get(n["layer"], 0) + 1

    return {
        "ok": True,
        "root": str(root),
        "tree_hash": tree_hash,
        "file_count": file_count,
        "dir_count": dir_count,
        "layers": layers,
        "nodes": nodes,
        "scanned_at": time.time(),
    }


def echarts_sunburst_data(scan: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    scan = scan or scan_structure()
    if not scan.get("ok"):
        return []
    root = {"name": "fusion-hero-os", "children": []}
    index: Dict[str, Dict[str, Any]] = {".": root}

    for node in sorted(scan["nodes"], key=lambda n: (n["depth"], n["id"])):
        if node["type"] != "dir":
            continue
        name = node["name"]
        parent_id = node["parent"] or "."
        parent = index.get(parent_id, root)
        child = {"name": name, "value": 1, "children": [], "layer": node.get("layer")}
        parent.setdefault("children", []).append(child)
        index[node["id"]] = child

    for node in scan["nodes"]:
        if node["type"] != "file":
            continue
        parent = index.get(node["parent"] or ".", root)
        parent.setdefault("children", []).append({
            "name": node["name"],
            "value": max(1, node.get("size", 1) // 1024),
            "layer": node.get("layer"),
        })
    return [root]