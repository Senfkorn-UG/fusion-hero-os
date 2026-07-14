#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge workstation/paths.json with optional paths.local.json (gitignored overlay)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Union

JsonDict = Dict[str, Any]


def _deep_merge(base: JsonDict, overlay: Mapping[str, Any]) -> JsonDict:
    out: JsonDict = dict(base)
    for key, value in overlay.items():
        if key.startswith("_"):
            continue
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, Mapping)
        ):
            out[key] = _deep_merge(out[key], value)  # type: ignore[arg-type]
        else:
            out[key] = value
    return out


def workstation_dir(start: Optional[Path] = None) -> Path:
    if start is not None:
        return start
    env = Path(__file__).resolve().parent
    return env


def resolve_paths(workstation: Optional[Path] = None) -> JsonDict:
    ws = workstation_dir(workstation)
    base_file = ws / "paths.json"
    if not base_file.exists():
        return {}
    data = json.loads(base_file.read_text(encoding="utf-8"))
    local_file = ws / "paths.local.json"
    if local_file.exists():
        overlay = json.loads(local_file.read_text(encoding="utf-8"))
        data = _deep_merge(data, overlay)
    return data


def write_merged_snapshot(
    destination: Union[str, Path],
    workstation: Optional[Path] = None,
) -> Path:
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(resolve_paths(workstation), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return dest


if __name__ == "__main__":
    print(json.dumps(resolve_paths(), indent=2, ensure_ascii=False))
