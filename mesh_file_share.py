#!/usr/bin/env python3
"""
Mesh file sharing + filedrops + GDrive mirror for phone/Android sync.

Flow:
  Mainframe zones (repo + archiv + journal) -> manifest -> hero-docs (Tailscale)
  Filedrops (Android POST, journal/inbox) -> local + Google Drive FusionHero_Offload
  Phone reads MagicDNS portal; Google Drive app mirrors cold copies natively on Android.
"""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
ROLES_PATH = ROOT / "src" / "normal_os" / "integration" / "mesh_roles.yaml"
FILES_ROOT = Path(os.environ.get("FUSION_MESH_FILES_DIR", Path.home() / ".fusion" / "mesh" / "files"))
MANIFEST_PATH = FILES_ROOT / "manifest.json"
SYNC_STATE_PATH = FILES_ROOT / "sync_state.json"

GDRIVE_OFFLOAD_CANDIDATES = [
    Path.home() / "Google Drive-Streaming" / "Meine Ablage" / "FusionHero_Offload",
    Path.home() / "Google Drive" / "Meine Ablage" / "FusionHero_Offload",
]

PHONE_HOST_ALIASES = ["phone-node", "redmi", "android"]

DEFAULT_ZONES = [
    {"id": "docs", "label": "Dokumentation", "path": "docs", "max_depth": 3, "max_files": 200},
    {"id": "journal", "label": "Journal", "path": "journal", "max_depth": 2, "max_files": 100},
    {"id": "journal_tagebuch", "label": "Tagebuch", "path": "journal/tagebuch", "max_depth": 1,
     "max_files": 90, "extensions": [".md"]},
    {"id": "mathematik", "label": "Aktualisierte Mathematik", "path": "02_Mathematik",
     "max_depth": 2, "max_files": 40, "extensions": [".json", ".py", ".txt", ".md"]},
    {"id": "mathematik_core", "label": "Math Engine + QPT", "path": ".", "max_depth": 0,
     "max_files": 12, "names": [
         "fusion_hero_os/core/heroic_math_engine.py",
         "fusion_hero_os/core/quantum_cognition.py",
         "src/normal_os/integration/proof_registry.yaml",
         "docs/v8/GROK_DEEP_RESEARCH_EXPORT_Empirical_Mathematical_Anchors_v8.md",
     ]},
    {"id": "archiv", "label": "Archiv", "path": "archiv", "max_depth": 4, "max_files": 80,
     "extensions": [".md", ".json", ".sh", ".py"], "exclude_extensions": [".obf"]},
    {"id": "workstation", "label": "Workstation Config", "path": "workstation", "max_depth": 1,
     "extensions": [".json", ".yaml", ".yml", ".example", ".md", ".sh", ".ps1"], "max_files": 80},
    {"id": "filedrops_out", "label": "Filedrops", "kind": "absolute", "path": "~/.fusion/mesh/filedrops/outbound",
     "max_depth": 3, "max_files": 150},
    {"id": "mesh_config", "label": "Mesh Config", "path": ".", "max_depth": 0, "max_files": 24,
     "names": ["mesh_connectors.yaml", "fusion_unified.yaml", "mesh_virtual_exit_nodes.yaml",
               "src/normal_os/integration/mesh_roles.yaml"]},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _expand_path(raw: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


def _tailscale_json() -> dict:
    try:
        r = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception:
        pass
    return {}


def _repo_root() -> Path:
    return Path(os.environ.get("FUSION_HERO_ROOT", str(ROOT)))


def get_filedrop_config() -> dict:
    roles = _load_yaml(ROLES_PATH)
    cfg = roles.get("filedrop_sync") or {}
    local = cfg.get("local_roots") or {}
    return {
        "enabled": cfg.get("enabled", True),
        "inbound": _expand_path(local.get("inbound", "~/.fusion/mesh/filedrops/inbound")),
        "outbound": _expand_path(local.get("outbound", "~/.fusion/mesh/filedrops/outbound")),
        "repo_drops": cfg.get("repo_drops") or ["journal/inbox", "workstation/inbox_export"],
        "gdrive_subpaths": cfg.get("gdrive_subpaths") or {
            "mirror": "mesh/mirror",
            "filedrops": "mesh/filedrops",
            "archives": "mesh/archives",
            "mathematik": "mesh/mathematik",
        },
        "journal_ingest_on_sync": cfg.get("journal_ingest_on_sync", True),
        "android_subdir": cfg.get("android_subdir", "android"),
    }


def get_file_share_config() -> dict:
    roles = _load_yaml(ROLES_PATH)
    cfg = roles.get("file_share") or {}
    return {
        "enabled": cfg.get("enabled", True),
        "zones": cfg.get("zones") or DEFAULT_ZONES,
        "phone_hostname_aliases": cfg.get("phone_hostname_aliases") or PHONE_HOST_ALIASES,
        "serve_port": int(os.environ.get("FUSION_HERO_DOCS_PORT") or cfg.get("serve_port") or os.environ.get("FUSION_HERO_DOCS_PORT", 8088)),
        "max_file_bytes": int(cfg.get("max_file_bytes", 25 * 1024 * 1024)),
    }


def resolve_gdrive_offload_root() -> Optional[Path]:
    env = os.environ.get("FUSION_GDRIVE_OFFLOAD")
    if env:
        p = _expand_path(env)
        if p.is_dir():
            return p
    for cand in GDRIVE_OFFLOAD_CANDIDATES:
        if cand.is_dir():
            return cand
    try:
        ws = ROOT / "workstation"
        if str(ws) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(ws))
        from resolve_paths import resolve_paths
        paths = resolve_paths(ws)
        resolved = (paths.get("storage") or {}).get("google_drive", {}).get("resolved_offload")
        if resolved:
            p = Path(resolved)
            if p.is_dir():
                return p
    except Exception:
        pass
    return None


def ensure_filedrop_dirs() -> dict:
    cfg = get_filedrop_config()
    roots = {
        "inbound": cfg["inbound"],
        "outbound": cfg["outbound"],
        "inbound_android": cfg["inbound"] / cfg["android_subdir"],
        "outbound_android": cfg["outbound"] / cfg["android_subdir"],
    }
    for p in roots.values():
        p.mkdir(parents=True, exist_ok=True)
    repo = _repo_root()
    for rel in cfg["repo_drops"]:
        (repo / rel).mkdir(parents=True, exist_ok=True)
    return {k: str(v) for k, v in roots.items()}


def resolve_mainframe_base_url() -> str:
    port = get_file_share_config()["serve_port"]
    data = _tailscale_json()
    self_dns = (data.get("Self") or {}).get("DNSName", "").rstrip(".")
    if self_dns:
        return f"http://{self_dns}:{port}"
    try:
        sys_path = ROOT / "src" / "normal_os" / "integration"
        import sys
        if str(sys_path) not in sys.path:
            sys.path.insert(0, str(sys_path))
        from mesh_roles import get_mainframe_hostname
        host = get_mainframe_hostname()
        data = _tailscale_json()
        for _pk, p in (data.get("Peer") or {}).items():
            hn = (p.get("HostName") or "").lower()
            if host.lower() in hn:
                dns = (p.get("DNSName") or "").rstrip(".")
                if dns:
                    port = get_file_share_config()["serve_port"]
                    return f"http://{dns}:{port}"
        port = get_file_share_config()["serve_port"]
        return f"http://{host}.tail391adb.ts.net:{port}"
    except Exception:
        port = get_file_share_config()["serve_port"]
        return f"http://127.0.0.1:{port}"


def resolve_phone_peer() -> Optional[dict]:
    cfg = get_file_share_config()
    aliases = [a.lower() for a in cfg["phone_hostname_aliases"]]
    data = _tailscale_json()
    roles = _load_yaml(ROLES_PATH)
    expected = ((roles.get("role_assignments") or {}).get("mobile") or {}).get("hostname", "phone-node").lower()
    best: Optional[dict] = None
    for _pk, p in (data.get("Peer") or {}).items():
        hn = (p.get("HostName") or "").lower()
        dns = (p.get("DNSName") or "").rstrip(".")
        os_name = (p.get("OS") or "").lower()
        if not (os_name == "android" or expected in hn or any(a in hn for a in aliases)):
            continue
        entry = {
            "hostname": p.get("HostName"),
            "magicdns": dns,
            "tailscale_ip": (p.get("TailscaleIPs") or [None])[0],
            "online": p.get("Online", False),
            "os": p.get("OS"),
        }
        if entry["online"]:
            return entry
        if best is None:
            best = entry
    return best


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _zone_base(zone: dict, repo: Path) -> Optional[Path]:
    kind = zone.get("kind", "repo")
    if kind == "absolute":
        raw = zone.get("path", "")
        if not raw:
            return None
        base = _expand_path(raw)
        return base if base.is_dir() else None
    rel = zone.get("path", ".")
    base = (repo / rel).resolve()
    repo_resolved = repo.resolve()
    if not str(base).startswith(str(repo_resolved)):
        return None
    return base


def _iter_zone_files(zone: dict, repo: Path) -> List[Path]:
    cfg = get_file_share_config()
    max_depth = int(zone.get("max_depth", 2))
    max_files = int(zone.get("max_files", 150))
    extensions = zone.get("extensions")
    exclude_ext = {e.lower() if e.startswith(".") else f".{e.lower()}"
                   for e in (zone.get("exclude_extensions") or [".obf"])}
    names_only = zone.get("names")
    base = _zone_base(zone, repo)
    if base is None:
        return []

    found: List[Path] = []
    kind = zone.get("kind", "repo")
    repo_resolved = repo.resolve()

    if names_only:
        for name in names_only:
            if kind == "absolute":
                continue
            p = (base / name).resolve() if zone.get("path") != "." else (repo / name).resolve()
            if p.is_file() and str(p).startswith(str(repo_resolved)):
                found.append(p)
        return found[:max_files]

    if not base.is_dir():
        return []

    for dirpath, dirnames, filenames in os.walk(base, followlinks=True):
        depth = len(Path(dirpath).relative_to(base).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            p = Path(dirpath) / fn
            if p.suffix.lower() in exclude_ext:
                continue
            if extensions and p.suffix.lower() not in extensions:
                continue
            try:
                if p.stat().st_size > cfg["max_file_bytes"]:
                    continue
            except OSError:
                continue
            found.append(p)
            if len(found) >= max_files:
                return found
    return found


def _entry_for_file(
    fp: Path,
    zone: dict,
    zone_id: str,
    base: str,
    *,
    repo: Path,
) -> dict:
    kind = zone.get("kind", "repo")
    zone_base = _zone_base(zone, repo)
    if kind == "absolute" and zone_base is not None:
        relpath = f"filedrops/{fp.relative_to(zone_base).as_posix()}"
    else:
        relpath = fp.relative_to(repo).as_posix()
    st = fp.stat()
    return {
        "zone": zone_id,
        "label": zone.get("label", zone_id),
        "relpath": relpath,
        "size_bytes": st.st_size,
        "sha256": _sha256_file(fp),
        "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
        "download_url": f"{base}/mesh/files/get/{quote(zone_id)}/{quote(relpath, safe='/')}",
        "mime": mimetypes.guess_type(fp.name)[0] or "application/octet-stream",
        "source": "mesh",
    }


def _gdrive_manifest_entries(gdrive_root: Path, base_url: str) -> List[dict]:
    """Virtual entries for files mirrored to Google Drive (Android native app)."""
    cfg = get_filedrop_config()
    sub = cfg["gdrive_subpaths"]
    entries: List[dict] = []
    for key, rel in sub.items():
        zone_dir = gdrive_root / rel
        if not zone_dir.is_dir():
            continue
        count = 0
        for fp in sorted(zone_dir.rglob("*")):
            if not fp.is_file() or fp.name.startswith("."):
                continue
            if fp.suffix.lower() == ".obf":
                continue
            try:
                if fp.stat().st_size > get_file_share_config()["max_file_bytes"]:
                    continue
            except OSError:
                continue
            rel_path = fp.relative_to(gdrive_root).as_posix()
            entries.append({
                "zone": f"gdrive_{key}",
                "label": f"Google Drive / {rel}",
                "relpath": rel_path,
                "size_bytes": fp.stat().st_size,
                "sha256": _sha256_file(fp),
                "modified": datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
                "download_url": f"{base_url}/mesh/files/gdrive/{quote(rel_path, safe='/')}",
                "mime": mimetypes.guess_type(fp.name)[0] or "application/octet-stream",
                "source": "google_drive",
                "gdrive_path": rel_path,
            })
            count += 1
            if count >= 120:
                break
    return entries


def build_file_manifest(*, base_url: Optional[str] = None) -> dict:
    cfg = get_file_share_config()
    repo = _repo_root()
    base = (base_url or resolve_mainframe_base_url()).rstrip("/")
    phone = resolve_phone_peer()
    gdrive_root = resolve_gdrive_offload_root()
    entries: List[dict] = []

    for zone in cfg["zones"]:
        zone_id = zone["id"]
        for fp in _iter_zone_files(zone, repo):
            entries.append(_entry_for_file(fp, zone, zone_id, base, repo=repo))

    gdrive_entries: List[dict] = []
    if gdrive_root:
        gdrive_entries = _gdrive_manifest_entries(gdrive_root, base)
        entries.extend(gdrive_entries)

    tree_hash = hashlib.sha256(
        json.dumps([e["sha256"] for e in entries], sort_keys=True).encode()
    ).hexdigest()

    fd_cfg = get_filedrop_config()
    return {
        "ok": True,
        "version": "1.1",
        "timestamp": _utc_now(),
        "tree_hash": tree_hash,
        "base_url": base,
        "file_count": len(entries),
        "entries": entries,
        "phone_peer": phone,
        "phone_portal_url": f"{base}/mesh/files/phone",
        "phone_manifest_url": f"{base}/mesh/files/manifest",
        "filedrop_upload_url": f"{base}/mesh/files/drop",
        "zones": [{"id": z["id"], "label": z.get("label", z["id"])} for z in cfg["zones"]],
        "google_drive": {
            "offload_root": str(gdrive_root) if gdrive_root else None,
            "mounted": gdrive_root is not None,
            "entry_count": len(gdrive_entries),
            "android_hint": "Google Drive App: FusionHero_Offload/mesh/mirror + mesh/filedrops",
        },
        "filedrops": {
            "inbound": str(fd_cfg["inbound"]),
            "outbound": str(fd_cfg["outbound"]),
            "repo_drops": fd_cfg["repo_drops"],
        },
    }


def save_file_manifest(*, base_url: Optional[str] = None) -> dict:
    manifest = build_file_manifest(base_url=base_url)
    FILES_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest["manifest_path"] = str(MANIFEST_PATH)
    return manifest


def load_file_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            data["ok"] = True
            data["source"] = "cache"
            return data
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return build_file_manifest()


def resolve_safe_path(zone_id: str, relpath: str) -> Tuple[Optional[Path], Optional[str]]:
    cfg = get_file_share_config()
    zone = next((z for z in cfg["zones"] if z["id"] == zone_id), None)
    if not zone:
        return None, "unknown zone"
    repo = _repo_root().resolve()
    if zone.get("kind") == "absolute":
        base = _zone_base(zone, repo)
        if base is None:
            return None, "zone unavailable"
        target = (base / Path(relpath.replace("filedrops/", ""))).resolve()
        if not str(target).startswith(str(base.resolve())):
            return None, "path traversal denied"
    else:
        target = (repo / relpath).resolve()
        if not str(target).startswith(str(repo)):
            return None, "path traversal denied"
    allowed = _iter_zone_files(zone, repo)
    if target not in allowed:
        return None, "file not in shared zone"
    if not target.is_file():
        return None, "not a file"
    if target.stat().st_size > cfg["max_file_bytes"]:
        return None, "file too large"
    return target, None


def resolve_gdrive_path(relpath: str) -> Tuple[Optional[Path], Optional[str]]:
    root = resolve_gdrive_offload_root()
    if not root:
        return None, "google drive not mounted"
    target = (root / relpath).resolve()
    if not str(target).startswith(str(root.resolve())):
        return None, "path traversal denied"
    if not target.is_file():
        return None, "not found"
    if target.suffix.lower() == ".obf":
        return None, "obfuscated blob not served"
    if target.stat().st_size > get_file_share_config()["max_file_bytes"]:
        return None, "file too large"
    return target, None


def _safe_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^\w.\-+]", "_", name)
    return name[:180] or "drop.bin"


def _check_drop_token(token: Optional[str]) -> bool:
    expected = os.environ.get("MESH_DROP_TOKEN") or os.environ.get("JOURNAL_TOKEN")
    if not expected:
        return False
    return token == expected


def receive_filedrop(
    filename: str,
    data: bytes,
    *,
    source: str = "android",
    token: Optional[str] = None,
) -> dict:
    if not _check_drop_token(token):
        return {"ok": False, "error": "invalid or missing drop token (MESH_DROP_TOKEN / JOURNAL_TOKEN)"}
    if not data:
        return {"ok": False, "error": "empty payload"}
    cfg = get_filedrop_config()
    ensure_filedrop_dirs()
    safe = _safe_filename(filename)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_name = f"{ts}_{source}_{safe}"
    local_dir = cfg["inbound"] / cfg["android_subdir"] if source == "android" else cfg["inbound"]
    local_path = local_dir / dest_name
    local_path.write_bytes(data)

    gdrive_root = resolve_gdrive_offload_root()
    gdrive_path = None
    if gdrive_root:
        sub = cfg["gdrive_subpaths"].get("filedrops", "mesh/filedrops")
        gdest = gdrive_root / sub / "inbound" / cfg["android_subdir"] / dest_name
        gdest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, gdest)
        gdrive_path = str(gdest.relative_to(gdrive_root))

    return {
        "ok": True,
        "stored": str(local_path),
        "gdrive_path": gdrive_path,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source": source,
    }


def _copy_tree_limited(src: Path, dst: Path, *, max_files: int = 80, extensions: Optional[List[str]] = None) -> int:
    if not src.is_dir():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for fp in sorted(src.rglob("*")):
        if not fp.is_file() or fp.suffix.lower() == ".obf":
            continue
        if extensions and fp.suffix.lower() not in extensions:
            continue
        rel = fp.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fp, out)
        n += 1
        if n >= max_files:
            break
    return n


def mirror_to_gdrive(manifest: Optional[dict] = None) -> dict:
    gdrive_root = resolve_gdrive_offload_root()
    if not gdrive_root:
        return {"ok": False, "error": "no_google_drive_mount", "hint": "Install Google Drive for desktop"}

    cfg = get_filedrop_config()
    sub = cfg["gdrive_subpaths"]
    repo = _repo_root()
    man = manifest or load_file_manifest()

    mirror_dir = gdrive_root / sub.get("mirror", "mesh/mirror")
    archive_dir = gdrive_root / sub.get("archives", "mesh/archives")
    filedrops_dir = gdrive_root / sub.get("filedrops", "mesh/filedrops")
    mirror_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    filedrops_dir.mkdir(parents=True, exist_ok=True)

    (mirror_dir / "manifest.json").write_text(
        json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    copied = {
        "journal_tagebuch": _copy_tree_limited(
            repo / "journal" / "tagebuch", mirror_dir / "journal_tagebuch", extensions=[".md"]
        ),
        "archiv_meta": _copy_tree_limited(
            repo / "archiv", archive_dir / "repo_archiv", extensions=[".md", ".json", ".sh"]
        ),
        "filedrops_outbound": _copy_tree_limited(
            _expand_path(str(cfg["outbound"])), filedrops_dir / "outbound"
        ),
    }

    latest = repo / "archiv" / "obfuscated" / "latest"
    if latest.exists():
        _copy_tree_limited(latest, archive_dir / "obfuscated_latest", extensions=[".md", ".json", ".sh"])

    math_mirror: Dict[str, Any] = {"ok": False, "skipped": True}
    try:
        from mesh_mathematics_sync import mirror_mathematics_to_gdrive
        math_mirror = mirror_mathematics_to_gdrive(gdrive_root=gdrive_root)
    except Exception as exc:
        math_mirror = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "gdrive_root": str(gdrive_root),
        "paths": {
            "mirror": str(mirror_dir),
            "archives": str(archive_dir),
            "filedrops": str(filedrops_dir),
            "mathematik": str(gdrive_root / sub.get("mathematik", "mesh/mathematik")),
        },
        "copied_counts": copied,
        "mathematics_mirror": math_mirror,
        "tree_hash": man.get("tree_hash"),
    }


def process_journal_inbox() -> dict:
    try:
        from journal.pipeline import JournalPipeline
        stats = JournalPipeline(base_dir=_repo_root() / "journal").process_inbox()
        return {"ok": True, **stats}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sync_mesh_all(*, notify_phone: bool = True) -> dict:
    """Full mesh file sync: journal inbox, manifest, GDrive mirror, phone notify."""
    ensure_filedrop_dirs()
    fd_cfg = get_filedrop_config()
    steps: List[str] = []
    out: Dict[str, Any] = {"timestamp": _utc_now(), "steps": steps}

    if fd_cfg.get("journal_ingest_on_sync", True):
        out["journal_inbox"] = process_journal_inbox()
        steps.append("journal_inbox")

    manifest = save_file_manifest()
    out["manifest"] = {
        "tree_hash": manifest.get("tree_hash"),
        "file_count": manifest.get("file_count"),
        "phone_portal_url": manifest.get("phone_portal_url"),
    }
    steps.append("manifest")

    out["gdrive_mirror"] = mirror_to_gdrive(manifest)
    steps.append("gdrive_mirror")

    try:
        from mesh_mathematics_sync import sync_mathematics_google
        out["mathematics_google"] = sync_mathematics_google(include_gdrive=True)
        steps.append("mathematics_google")
    except Exception as exc:
        out["mathematics_google"] = {"ok": False, "error": str(exc)}

    out["phone_peer"] = resolve_phone_peer()
    out["ok"] = True

    state = {
        "timestamp": out["timestamp"],
        "tree_hash": manifest.get("tree_hash"),
        "gdrive": out["gdrive_mirror"],
        "phone_portal_url": manifest.get("phone_portal_url"),
    }
    FILES_ROOT.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    if notify_phone:
        out["notify"] = notify_phone_mirror_updated(manifest)
        steps.append("notify")

    return out


def get_mirror_status() -> dict:
    cfg = get_file_share_config()
    manifest = load_file_manifest()
    phone = resolve_phone_peer()
    gdrive = resolve_gdrive_offload_root()
    sync_state = {}
    if SYNC_STATE_PATH.exists():
        try:
            sync_state = json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "timestamp": _utc_now(),
        "enabled": cfg["enabled"],
        "mainframe_base_url": resolve_mainframe_base_url(),
        "phone_peer": phone,
        "phone_visible": phone is not None and phone.get("online", False),
        "google_drive": {
            "mounted": gdrive is not None,
            "offload_root": str(gdrive) if gdrive else None,
        },
        "filedrops": ensure_filedrop_dirs(),
        "manifest": {
            "tree_hash": manifest.get("tree_hash"),
            "file_count": manifest.get("file_count", 0),
            "timestamp": manifest.get("timestamp"),
            "cached": manifest.get("source") == "cache",
        },
        "last_sync": sync_state,
        "urls": {
            "portal": manifest.get("phone_portal_url"),
            "manifest": manifest.get("phone_manifest_url"),
            "drop": manifest.get("filedrop_upload_url"),
            "sync": f"{resolve_mainframe_base_url().rstrip('/')}/mesh/sync/run",
            "status": f"{resolve_mainframe_base_url().rstrip('/')}/mesh/files/status",
        },
    }


def render_phone_portal_html(manifest: dict) -> str:
    entries = manifest.get("entries") or []
    by_zone: Dict[str, List[dict]] = {}
    for e in entries:
        by_zone.setdefault(e["zone"], []).append(e)

    sections = []
    for zone in manifest.get("zones") or []:
        zid = zone["id"]
        items = by_zone.get(zid, [])
        if not items:
            continue
        rows = "\n".join(
            f'<li><a href="{e["download_url"]}">{e["relpath"]}</a> '
            f'<span class="meta">({e["size_bytes"] // 1024} KB)</span></li>'
            for e in items[:40]
        )
        sections.append(f"<section><h2>{zone.get('label', zid)}</h2><ul>{rows}</ul></section>")

    gdrive_items = [e for e in entries if e.get("source") == "google_drive"][:30]
    if gdrive_items:
        grow = "\n".join(
            f'<li>{e["gdrive_path"]} <span class="meta">({e["size_bytes"] // 1024} KB, Drive)</span></li>'
            for e in gdrive_items
        )
        sections.append(f"<section><h2>Google Drive Spiegel</h2><ul>{grow}</ul></section>")

    phone = manifest.get("phone_peer") or {}
    gdrive = manifest.get("google_drive") or {}
    drop_url = manifest.get("filedrop_upload_url", "#")
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fusion Hero — Mesh Files</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem; background: #0f1419; color: #e6edf3; }}
    h1 {{ font-size: 1.25rem; }}
    h2 {{ font-size: 1rem; color: #58a6ff; margin-top: 1.5rem; }}
    a {{ color: #79c0ff; word-break: break-all; }}
    .meta {{ color: #8b949e; font-size: 0.85rem; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; background: #238636; font-size: 0.75rem; }}
    ul {{ padding-left: 1.2rem; }}
  </style>
</head>
<body>
  <h1>Fusion Hero Mesh — Dateien &amp; Archive</h1>
  <p><span class="badge">Tailscale</span> {manifest.get('file_count', 0)} Dateien · Hash {str(manifest.get('tree_hash', ''))[:12]}</p>
  <p class="meta">Handy: {phone.get('hostname', '—')} · GDrive: {'ja' if gdrive.get('mounted') else 'nein'} · <a href="{manifest.get('phone_manifest_url', '#')}">JSON</a></p>
  <p class="meta">Filedrop (POST): {drop_url}</p>
  {''.join(sections) if sections else '<p>Keine geteilten Dateien im Manifest.</p>'}
</body>
</html>"""


def notify_phone_mirror_updated(manifest: dict) -> dict:
    try:
        from tailscale_phone_notify import send_phone_notification
        count = manifest.get("file_count", 0)
        url = manifest.get("phone_portal_url", "")
        send_phone_notification(
            f"Mesh-Sync: {count} Dateien, Archive+Filedrops. Portal: {url}",
            title="Fusion Hero Files",
        )
        return {"ok": True, "notified": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sync_phone_mirror(*, refresh: bool = True, notify: bool = True) -> dict:
    if refresh:
        return sync_mesh_all(notify_phone=notify)
    manifest = load_file_manifest()
    out = {
        "ok": True,
        "timestamp": _utc_now(),
        "manifest": {
            "tree_hash": manifest.get("tree_hash"),
            "file_count": manifest.get("file_count"),
            "phone_portal_url": manifest.get("phone_portal_url"),
        },
        "phone_peer": resolve_phone_peer(),
    }
    if notify:
        out["notify"] = notify_phone_mirror_updated(manifest)
    return out


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(get_mirror_status(), indent=2, ensure_ascii=False))
    elif cmd == "build":
        print(json.dumps(build_file_manifest(), indent=2, ensure_ascii=False))
    elif cmd == "sync":
        print(json.dumps(sync_mesh_all(), indent=2, ensure_ascii=False))
    elif cmd == "gdrive":
        print(json.dumps(mirror_to_gdrive(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"error": f"unknown: {cmd}"}, indent=2))
        sys.exit(1)
