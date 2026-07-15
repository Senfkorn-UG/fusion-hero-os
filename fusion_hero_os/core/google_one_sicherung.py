# -*- coding: utf-8 -*-
"""
Google One Sicherung — activate + local snapshot for Fusion Hero OS.

- Opens Google One landing / storage (operator confirms product backup)
- Marks local activation under ~/.fusion/sicherung
- Creates public-safe snapshot (no secrets) of dissertation/control docs
- Records Drive folder target (Google One storage)

Geltung: Spezifikation (local backup) · Google One product state = operator/Bedingt
Policy: pseudo_inhouse_only · freemium=false · secrets never copied
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shutil
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]

__all__ = ["activate", "status", "run_snapshot", "load_config"]


def load_config() -> Dict[str, Any]:
    path = ROOT / "google_one_sicherung.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(str(p)))


def _local_root(cfg: Optional[Dict[str, Any]] = None) -> Path:
    cfg = cfg or load_config()
    p = _expand((cfg.get("local") or {}).get("root") or "~/.fusion/sicherung")
    p.mkdir(parents=True, exist_ok=True)
    for sub in ("local", "snapshots", "manifests", "google_one"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def _is_excluded(rel: str, exclude: List[str]) -> bool:
    rel_f = rel.replace("\\", "/")
    low = rel_f.lower()
    if any(x in low for x in (".env", "secret", "credential", ".pem", "id_rsa", "push_secret")):
        return True
    for pat in exclude:
        if fnmatch.fnmatch(rel_f, pat) or fnmatch.fnmatch(Path(rel_f).name, pat):
            return True
    return False


def _match_include(rel: str, includes: List[str]) -> bool:
    rel_f = rel.replace("\\", "/")
    for pat in includes:
        if fnmatch.fnmatch(rel_f, pat):
            return True
        # simple ** prefix support via pathlib parts
        if pat.endswith("/**"):
            prefix = pat[:-3].rstrip("/")
            if rel_f == prefix or rel_f.startswith(prefix + "/"):
                return True
    return False


def _sha16_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def activate(*, open_browser: bool = True) -> Dict[str, Any]:
    """Activate local sicherung + open Google One URLs."""
    cfg = load_config()
    root = _local_root(cfg)
    now = datetime.now(timezone.utc).isoformat()
    drive = cfg.get("drive") or {}
    flag = {
        "activated": True,
        "activated_at": now,
        "provider": "google_one",
        "landing_url": cfg.get("landing_url") or "https://one.google.com/?g1_landing_page=1",
        "storage_url": cfg.get("storage_url") or "https://one.google.com/storage",
        "drive_folder_name": drive.get("folder_name") or "Fusion_Hero_OS_Sicherung",
        "drive_folder_id": drive.get("folder_id"),
        "drive_web_view_link": drive.get("web_view_link"),
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "secrets_excluded": True,
        "platform": cfg.get("platform_version") or "10.0.0",
        "notes": (
            "Local Fusion sicherung ACTIVE. "
            "Confirm Google One plan/device backup in browser if needed."
        ),
    }
    flag_path = root / "google_one" / "ACTIVATED.json"
    flag_path.write_text(json.dumps(flag, indent=2, ensure_ascii=False), encoding="utf-8")
    # also public-safe status in docs
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    pub = {
        "activated": True,
        "activated_at": now,
        "provider": "google_one",
        "landing_url": flag["landing_url"],
        "storage_url": flag["storage_url"],
        "drive_folder_name": flag["drive_folder_name"],
        "drive_web_view_link": flag.get("drive_web_view_link"),
        "secrets_excluded": True,
        "local_root": str(root),
    }
    (docs / "GOOGLE_ONE_SICHERUNG.md").write_text(
        "\n".join(
            [
                "# Google One Sicherung — aktiv",
                "",
                f"**Status:** ACTIVATED (`{now}`)",
                f"**Provider:** Google One + Drive",
                f"**Landing:** {flag['landing_url']}",
                f"**Storage:** {flag['storage_url']}",
                f"**Drive-Ordner:** [{flag['drive_folder_name']}]({flag.get('drive_web_view_link') or '#'})",
                f"**Lokal:** `{root}`",
                "",
                "## Operator (Browser)",
                "",
                "1. https://one.google.com/?g1_landing_page=1 — Plan / Geräte-Backup prüfen",
                "2. https://one.google.com/storage — Speicherplatz prüfen",
                "3. Drive-Ordner `Fusion_Hero_OS_Sicherung` für public-safe Snapshots",
                "4. Google Drive for Desktop: optional Ordner spiegeln",
                "",
                "## CLI",
                "",
                "```powershell",
                "python -m fusion_hero_os.core.google_one_sicherung --activate",
                "python -m fusion_hero_os.core.google_one_sicherung --snapshot",
                "python -m fusion_hero_os.core.google_one_sicherung --status",
                "```",
                "",
                "**Policy:** secrets NEVER · freemium=false · pseudo_inhouse_only",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (docs / "last_activation.summary.json").write_text(
        json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    opened: List[str] = []
    if open_browser:
        for key in ("landing_url", "storage_url"):
            url = cfg.get(key) or flag.get(key)
            if url:
                try:
                    webbrowser.open(url)
                    opened.append(url)
                except Exception:
                    pass
        link = drive.get("web_view_link")
        if link:
            try:
                webbrowser.open(link)
                opened.append(link)
            except Exception:
                pass

    return {
        "ok": True,
        "activated": True,
        "flag_path": str(flag_path),
        "drive_folder_id": flag.get("drive_folder_id"),
        "drive_web_view_link": flag.get("drive_web_view_link"),
        "browser_opened": opened,
        "local_root": str(root),
        "docs": str(docs / "GOOGLE_ONE_SICHERUNG.md"),
    }


def run_snapshot() -> Dict[str, Any]:
    """Copy public-safe includes into a timestamped local snapshot."""
    cfg = load_config()
    root = _local_root(cfg)
    includes = list(cfg.get("include_globs") or [])
    excludes = list(cfg.get("exclude_globs") or [])
    max_mb = float((cfg.get("policy") or {}).get("max_file_mb") or 25)
    max_b = int(max_mb * 1024 * 1024)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = root / "snapshots" / f"snap_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    files: List[Dict[str, Any]] = []
    skipped: List[str] = []
    total = 0
    t0 = time.time()

    for dirpath, _dirnames, filenames in os.walk(ROOT):
        # skip heavy/unwanted trees early
        rel_dir = str(Path(dirpath).relative_to(ROOT)).replace("\\", "/")
        if rel_dir.startswith((".git", "node_modules", "__pycache__", "legacy_sources", ".venv")):
            continue
        for name in filenames:
            path = Path(dirpath) / name
            try:
                rel = str(path.relative_to(ROOT)).replace("\\", "/")
            except ValueError:
                continue
            if _is_excluded(rel, excludes):
                continue
            if includes and not _match_include(rel, includes):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > max_b:
                skipped.append(f"too_large:{rel}")
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(path, target)
            except OSError as e:
                skipped.append(f"copy_fail:{rel}:{e}")
                continue
            sha = _sha16_file(target)
            files.append({"rel": rel, "bytes": size, "sha16": sha})
            total += size

    manifest = {
        "ok": True,
        "snapshot_id": stamp,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "bytes_total": total,
        "files": files,
        "skipped": skipped[:50],
        "dest": str(dest),
        "provider": "google_one",
        "drive_folder": (cfg.get("drive") or {}).get("folder_name"),
        "drive_web_view_link": (cfg.get("drive") or {}).get("web_view_link"),
        "secrets_excluded": True,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }
    man_path = root / "manifests" / f"manifest_{stamp}.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "manifests" / "last_snapshot.summary.json").write_text(
        json.dumps(
            {
                "snapshot_id": stamp,
                "file_count": len(files),
                "bytes_total": total,
                "created_at": manifest["created_at"],
                "dest": str(dest),
                "drive_web_view_link": manifest["drive_web_view_link"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    # public docs summary
    docs = ROOT / "docs" / "sicherung"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "last_snapshot.summary.json").write_text(
        json.dumps(
            {
                "snapshot_id": stamp,
                "file_count": len(files),
                "bytes_total": total,
                "created_at": manifest["created_at"],
                "secrets_excluded": True,
                "provider": "google_one",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest


def status() -> Dict[str, Any]:
    cfg = load_config()
    root = _local_root(cfg)
    flag_path = root / "google_one" / "ACTIVATED.json"
    flag = None
    if flag_path.is_file():
        try:
            flag = json.loads(flag_path.read_text(encoding="utf-8"))
        except Exception:
            flag = {"raw": True}
    last = root / "manifests" / "last_snapshot.summary.json"
    last_snap = None
    if last.is_file():
        try:
            last_snap = json.loads(last.read_text(encoding="utf-8"))
        except Exception:
            pass
    drive = cfg.get("drive") or {}
    return {
        "ok": True,
        "activated": bool(flag and flag.get("activated")),
        "flag": flag,
        "provider": "google_one",
        "landing_url": cfg.get("landing_url"),
        "storage_url": cfg.get("storage_url"),
        "drive_folder_id": drive.get("folder_id"),
        "drive_web_view_link": drive.get("web_view_link"),
        "local_root": str(root),
        "last_snapshot": last_snap,
        "config_version": cfg.get("version"),
        "freemium": False,
        "secrets_excluded": True,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Google One Sicherung (Fusion Hero OS)")
    ap.add_argument("--activate", action="store_true", help="activate + open Google One URLs")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status and not (args.activate or args.snapshot):
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    out: Dict[str, Any] = {}
    do_all = not (args.activate or args.snapshot or args.status)

    if args.activate or do_all:
        out["activate"] = activate(open_browser=not args.no_browser)
    if args.snapshot or do_all:
        m = run_snapshot()
        out["snapshot"] = {
            "ok": m["ok"],
            "snapshot_id": m["snapshot_id"],
            "file_count": m["file_count"],
            "bytes_total": m["bytes_total"],
            "dest": m["dest"],
            "drive_web_view_link": m.get("drive_web_view_link"),
            "latency_ms": m["latency_ms"],
        }
    if args.status or do_all:
        out["status"] = status()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
