#!/usr/bin/env python3
"""
Google-Durchlauf fuer aktualisierte Mathematik (v8).

Spiegelt kanonische Math-Artefakte nach Google Drive (FusionHero_Offload/mesh/mathematik)
und stellt sie im Mesh-File-Share-Manifest bereit (Handy + Tailscale).

Quellen:
  - 02_Mathematik/ (hero-guide, qb_qubo, extrahierte Formale Mathematik)
  - fusion_hero_os/core/heroic_math_engine.py (Knoten 16-20, bewiesene Fassung)
  - fusion_hero_os/core/quantum_cognition.py (Busemeyer-QPT)
  - proof_registry.yaml (QPT-* / heroic_math Claims)
  - docs/v8/GROK_DEEP_RESEARCH_EXPORT_Empirical_Mathematical_Anchors_v8.md
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent

# Repo-relative Pfade der aktualisierten Mathematik (Single Source of Truth)
MATH_ARTIFACT_PATHS: Tuple[str, ...] = (
    "02_Mathematik/hero-guide_geltungsstand.json",
    "02_Mathematik/qb_qubo.py",
    "02_Mathematik/qubo_qdrant_cache.py",
    "02_Mathematik/requirements.txt",
    "02_Mathematik/extracted/Formale_Mathematik.txt",
    "fusion_hero_os/core/heroic_math_engine.py",
    "fusion_hero_os/core/quantum_cognition.py",
    "src/normal_os/integration/proof_registry.yaml",
    "docs/v8/GROK_DEEP_RESEARCH_EXPORT_Empirical_Mathematical_Anchors_v8.md",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo_root() -> Path:
    return Path(os.environ.get("FUSION_HERO_ROOT", str(ROOT)))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_math_artifacts(repo: Optional[Path] = None) -> List[Path]:
    """Existierende Math-Artefakte im Repo aufloesen."""
    repo = repo or _repo_root()
    found: List[Path] = []
    for rel in MATH_ARTIFACT_PATHS:
        p = (repo / rel).resolve()
        if p.is_file():
            found.append(p)
    return found


def build_mathematics_manifest(*, repo: Optional[Path] = None) -> Dict[str, Any]:
    """Manifest der aktualisierten Mathematik mit tree_hash."""
    repo = repo or _repo_root()
    entries: List[Dict[str, Any]] = []
    for fp in resolve_math_artifacts(repo):
        rel = fp.relative_to(repo).as_posix()
        st = fp.stat()
        entries.append({
            "relpath": rel,
            "size_bytes": st.st_size,
            "sha256": _sha256_file(fp),
            "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
        })
    entries.sort(key=lambda e: e["relpath"])
    tree_hash = hashlib.sha256(
        json.dumps([e["sha256"] for e in entries], sort_keys=True).encode()
    ).hexdigest()
    return {
        "ok": True,
        "version": "1.0",
        "timestamp": _utc_now(),
        "tree_hash": tree_hash,
        "artifact_count": len(entries),
        "entries": entries,
        "sources": list(MATH_ARTIFACT_PATHS),
        "google_drive_subpath": "mesh/mathematik",
    }


def mirror_mathematics_to_gdrive(
    manifest: Optional[dict] = None,
    *,
    gdrive_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Kopiert Math-Artefakte nach FusionHero_Offload/mesh/mathematik."""
    try:
        from mesh_file_share import get_filedrop_config, resolve_gdrive_offload_root
    except ImportError:
        get_filedrop_config = None  # type: ignore
        resolve_gdrive_offload_root = None  # type: ignore

    root = gdrive_root
    if root is None and resolve_gdrive_offload_root:
        root = resolve_gdrive_offload_root()

    if root is None or not root.is_dir():
        return {
            "ok": False,
            "error": "no_google_drive_mount",
            "hint": "Google Drive Desktop oder FUSION_GDRIVE_OFFLOAD setzen",
        }

    sub = "mesh/mathematik"
    if get_filedrop_config:
        sub = (get_filedrop_config().get("gdrive_subpaths") or {}).get("mathematik", sub)

    dest_root = root / sub
    dest_root.mkdir(parents=True, exist_ok=True)
    repo = _repo_root()
    man = manifest or build_mathematics_manifest(repo=repo)
    copied: List[str] = []

    for entry in man.get("entries", []):
        rel = entry["relpath"]
        src = repo / rel
        if not src.is_file():
            continue
        out = dest_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        copied.append(rel)

    manifest_path = dest_root / "mathematics_manifest.json"
    manifest_path.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    history = dest_root / "history"
    history.mkdir(exist_ok=True)
    hist_name = f"{man.get('tree_hash', 'unknown')[:16]}.json"
    shutil.copy2(manifest_path, history / hist_name)

    return {
        "ok": True,
        "gdrive_root": str(root),
        "dest": str(dest_root),
        "copied": copied,
        "copied_count": len(copied),
        "tree_hash": man.get("tree_hash"),
        "manifest_path": str(manifest_path),
    }


def sync_mathematics_google(*, include_gdrive: bool = True) -> Dict[str, Any]:
    """Vollstaendiger Google-Durchlauf: Manifest bauen + optional GDrive spiegeln."""
    man = build_mathematics_manifest()
    out: Dict[str, Any] = {
        "ok": True,
        "timestamp": _utc_now(),
        "manifest": man,
    }
    if include_gdrive:
        gdrive = mirror_mathematics_to_gdrive(man)
        out["google_drive"] = gdrive
        out["ok"] = bool(gdrive.get("ok"))
    return out


def main() -> int:
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd in ("-h", "--help", "help"):
        print(json.dumps({"commands": ["sync", "manifest", "gdrive"]}, indent=2))
        return 0
    if cmd == "manifest":
        print(json.dumps(build_mathematics_manifest(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "gdrive":
        print(json.dumps(mirror_mathematics_to_gdrive(), indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(sync_mathematics_google(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
