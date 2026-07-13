#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fusion Hero OS — Disk Dedup + Offload-Planer (v1.0 · 2026-07-11).

Drei Aufgaben fuer den knappen C:-Speicher, ALLE standardmaessig zerstoerungsfrei:

  1. VERMESSEN  (--report): Kategorisiert Nutzerdaten unter C:\\Users\\Admin nach
     Verwendungszweck (installer/media/archive/document/project/cache/other).

  2. DEDUP      (--dedup [--quarantine]): Findet Datei-Duplikate BOTTOM-UP —
     erst nach Groesse gruppiert, dann SHA-256 nur bei Groessenkollision.
     Zwei Dateien gelten NUR dann als Dublette, wenn Hash UND Verwendungszweck
     uebereinstimmen (Zweck aus dem Pfad abgeleitet). Kanonisch behalten wird
     das Original mit dem kuerzesten/aeltesten Pfad; der Rest wandert mit
     --quarantine nach _dedup_quarantine/<lauf>/ samt Undo-Manifest (JSON).
     Hartes Loeschen macht dieses Tool NIE — Quarantaene ist reversibel.

  3. OFFLOAD    (--offload-plan): Listet Kandidaten, die offline nicht
     gebraucht werden (grosse Installer, alte Archive, Medien) — als Plan
     fuer die Auslagerung nach Google Drive. Fuehrt KEINEN Upload aus
     (Senden an externen Dienst braucht ausdrueckliche Freigabe).

Undo: --undo <manifest.json> stellt alle quarantaenierten Dateien zurueck.

Sicherheit: SAFE_EXCLUDE haelt System-/Programm-/Cache-Pfade komplett aus
Dedup und Offload heraus (dort sind Hash-Gleichheiten normal und ein
Verschieben wuerde Software beschaedigen).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

USER_ROOT = Path(os.environ.get("USERPROFILE", r"C:\Users\Admin"))
QUARANTINE_ROOT = USER_ROOT / "_dedup_quarantine"

# Pfad-Substrings (lowercase), die KOMPLETT ausgeschlossen sind — dort sind
# Duplikate systembedingt normal und Verschieben ist gefaehrlich.
SAFE_EXCLUDE = (
    r"\appdata\local\packages", r"\appdata\local\programs",
    r"\appdata\local\microsoft", r"\appdata\locallow",
    r"\node_modules\\", r"\.git\\", r"\venv\\", r"\.venv\\",
    r"\.rustup\\", r"\.cargo\\", r"\site-packages\\",
    r"\npm-cache", r"\pip\cache", r"\.cache\\",
    r"\appdata\local\wsl", r"\appdata\local\google\drivefs",
    r"\_dedup_quarantine\\", r"\onedrive\\", r"\google drive-streaming\\",
    r"\stable-diffusion-webui\\venv\\",
    r"\stable-diffusion-webui\\repositories\\",
    r"\.grok\\bin\\", r"\.grok\\skills\\",
    # Build-Artefakte: dort sind gleiche Hashes normal (Kopien/Hardlinks),
    # ein Verschieben wuerde ein Build zerstoeren.
    r"\target\release\\", r"\target\debug\\", r"\build\\", r"\deps\\",
)

# Verwendungszweck aus Pfad/Endung.
INSTALLER_EXT = {".exe", ".msi", ".deb", ".appimage", ".dmg", ".pkg"}
ARCHIVE_EXT = {".zip", ".7z", ".rar", ".tar", ".gz", ".iso"}
MEDIA_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".mp3", ".wav", ".flac"}
DOC_EXT = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".odt", ".epub"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff", ".bmp"}
CODE_EXT = {".py", ".rs", ".js", ".ts", ".c", ".cpp", ".java", ".go"}
MODEL_EXT = {".gguf", ".safetensors", ".ckpt", ".pt", ".bin", ".onnx", ".pth"}

# Wurzeln fuer Dedup/Offload (Nutzerdaten, kein System)
SCAN_ROOTS = (
    "Downloads", "Desktop", "Documents", "Pictures", "Videos", "Music",
    "internal_llm", "private-hacking-suite", "src", "kepler",
    "stable-diffusion-webui/models", ".grok", ".codex", ".gemini",
)

# Ganze Ordner nach GDrive (relativ zu USER_ROOT -> Unterordner unter FusionHero_Offload)
OFFLOAD_FOLDERS = (
    ("stable-diffusion-webui/models", "SD_models"),
    ("internal_llm/models", "LLM_models"),
    ("private-hacking-suite", "Archives/private-hacking-suite"),
    (".grok/sessions", "Archives/grok_sessions"),
    (".grok/downloads", "Archives/grok_downloads"),
)

MIN_DEDUP_BYTES = 1 * 1024 * 1024        # Dateien < 1 MB ignorieren (Rauschen)
OFFLOAD_MIN_BYTES = 100 * 1024 * 1024    # Offload-Kandidat ab 100 MB
GDRIVE_OFFLOAD_REL = Path("Meine Ablage") / "FusionHero_Offload"


def _gdrive_dest_root() -> Optional[Path]:
    """Google Drive Streaming/ Mirror Ziel fuer FusionHero_Offload."""
    env = os.environ.get("FUSION_GDRIVE_OFFLOAD")
    if env:
        return Path(env)
    profile = Path(os.environ.get("USERPROFILE", r"C:\Users\Admin"))
    for base in (
        profile / "Google Drive-Streaming",
        profile / "Google Drive",
        Path("G:"),
    ):
        if not base.is_dir():
            continue
        for sub in (GDRIVE_OFFLOAD_REL, Path("My Drive") / "FusionHero_Offload"):
            candidate = base / sub
            if candidate.parent.is_dir():
                return candidate
    return None


def purpose(path: Path) -> str:
    ext = path.suffix.lower()
    low = str(path).lower()
    if ext in INSTALLER_EXT:
        return "installer"
    if ext in ARCHIVE_EXT:
        return "archive"
    if ext in MEDIA_EXT:
        return "media"
    if ext in DOC_EXT:
        return "document"
    if ext in IMAGE_EXT:
        return "image"
    if ext in CODE_EXT:
        return "project"
    if ext in MODEL_EXT:
        return "model"
    if "cache" in low or "temp" in low:
        return "cache"
    return "other"


def _excluded(path: Path) -> bool:
    low = str(path).lower()
    return any(sub.replace("\\\\", "\\") in low for sub in SAFE_EXCLUDE)


def _iter_files(roots: List[Path]):
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dp = Path(dirpath)
            if _excluded(dp):
                dirnames[:] = []
                continue
            for fn in filenames:
                p = dp / fn
                if _excluded(p):
                    continue
                try:
                    if p.is_symlink() or not p.is_file():
                        continue
                    yield p
                except OSError:
                    continue


def _sha256(path: Path, cap: int = 512 * 1024 * 1024) -> Optional[str]:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            read = 0
            while read < cap:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
                read += len(chunk)
        return h.hexdigest()
    except OSError:
        return None


@dataclass
class DupGroup:
    sha256: str
    purpose: str
    size_bytes: int
    keep: str
    remove: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Vermessung
# ---------------------------------------------------------------------------

def report(roots: List[Path]) -> Dict[str, Dict[str, int]]:
    cats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    for p in _iter_files(roots):
        try:
            size = p.stat().st_size
        except OSError:
            continue
        slot = cats[purpose(p)]
        slot["files"] += 1
        slot["bytes"] += size
    return dict(cats)


# ---------------------------------------------------------------------------
# Dedup (Hash + Verwendungszweck)
# ---------------------------------------------------------------------------

def find_duplicates(roots: List[Path]) -> List[DupGroup]:
    # 1) nach (Groesse, Zweck) vorgruppieren — Hash nur bei Kollision
    by_size_purpose: Dict[Tuple[int, str], List[Path]] = defaultdict(list)
    for p in _iter_files(roots):
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size < MIN_DEDUP_BYTES:
            continue
        by_size_purpose[(size, purpose(p))].append(p)

    groups: List[DupGroup] = []
    for (size, purp), paths in by_size_purpose.items():
        if len(paths) < 2:
            continue
        by_hash: Dict[str, List[Path]] = defaultdict(list)
        for p in paths:
            digest = _sha256(p)
            if digest:
                by_hash[digest].append(p)
        for digest, dupes in by_hash.items():
            if len(dupes) < 2:
                continue
            # kanonisch behalten: kuerzester Pfad, bei Gleichstand aeltester
            dupes.sort(key=lambda p: (len(str(p)), p.stat().st_mtime))
            keep = dupes[0]
            groups.append(DupGroup(
                sha256=digest, purpose=purp, size_bytes=size,
                keep=str(keep), remove=[str(p) for p in dupes[1:]],
            ))
    groups.sort(key=lambda g: g.size_bytes * len(g.remove), reverse=True)
    return groups


def quarantine(groups: List[DupGroup], run_label: str) -> Path:
    run_dir = QUARANTINE_ROOT / run_label
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"run": run_label, "moves": []}
    for g in groups:
        for src_str in g.remove:
            src = Path(src_str)
            if not src.is_file():
                continue
            # Zielpfad kollisionsfrei unter Beibehaltung der Struktur
            try:
                rel = src.relative_to(USER_ROOT)
            except ValueError:
                rel = Path(src.name)
            dst = run_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            n = 1
            while dst.exists():
                dst = dst.with_name(f"{dst.stem}__{n}{dst.suffix}")
                n += 1
            shutil.move(str(src), str(dst))
            manifest["moves"].append({
                "original": str(src), "quarantine": str(dst),
                "kept": g.keep, "sha256": g.sha256, "bytes": g.size_bytes,
            })
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    return manifest_path


def undo(manifest_path: Path) -> int:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored = 0
    for mv in data.get("moves", []):
        q, orig = Path(mv["quarantine"]), Path(mv["original"])
        if q.is_file() and not orig.exists():
            orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(q), str(orig))
            restored += 1
    return restored


# ---------------------------------------------------------------------------
# Offload-Plan (offline nicht benoetigt)
# ---------------------------------------------------------------------------

def _offload_eligible(p: Path, size: int, purp: str, *, include_images: bool,
                      min_bytes: int = OFFLOAD_MIN_BYTES) -> bool:
    if size < min_bytes:
        return False
    low = str(p).lower().replace("/", "\\")
    downloads = str(USER_ROOT / "Downloads").lower()
    desktop = str(USER_ROOT / "Desktop").lower()
    # Installer, Archive, Medien, Modelle — offline entbehrlich
    if purp in {"installer", "archive", "media", "model"}:
        return True
    # Grosse Downloads/Desktop-Dateien (Spiele, ISOs, Setups)
    if (downloads in low or desktop in low) and purp in {"other", "image", "document"}:
        return True
    # Handy-Fotos/DCIM optional nach GDrive
    if include_images and "\\pictures\\" in low and purp == "image":
        return True
    # Alte Grok-Session-Logs
    if "\\.grok\\sessions\\" in low and purp in {"other", "project"}:
        return True
    return False


def offload_plan(roots: List[Path], *, include_images: bool = False,
                 min_bytes: int = OFFLOAD_MIN_BYTES) -> List[Dict]:
    """Grosse, offline entbehrliche Dateien: Installer, Archive, Medien, Downloads."""
    plan = []
    for p in _iter_files(roots):
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size < min_bytes:
            continue
        purp = purpose(p)
        if _offload_eligible(p, size, purp, include_images=include_images, min_bytes=min_bytes):
            plan.append({"path": str(p), "purpose": purp,
                         "size_bytes": size, "gb": round(size / 1024**3, 2)})
    plan.sort(key=lambda x: x["size_bytes"], reverse=True)
    return plan


def offload_execute(plan: List[Dict], dest_root: Path, index_out: Path) -> Dict:
    """Sicher auslagern: KOPIEREN -> Groesse verifizieren -> erst dann Original loeschen.

    Kein Datenverlust: das lokale Original wird nur entfernt, wenn die Kopie
    am Ziel existiert und byte-genau die gleiche Groesse hat. Schreibt einen
    Auslagerungs-Index (fuer die Verankerung im Vault-Repo).
    """
    dest_root.mkdir(parents=True, exist_ok=True)
    index = {"dest_root": str(dest_root), "entries": [], "freed_bytes": 0, "skipped": []}
    for item in plan:
        src = Path(item["path"])
        if not src.is_file():
            index["skipped"].append({"path": item["path"], "reason": "verschwunden"})
            continue
        try:
            rel = src.relative_to(USER_ROOT)
        except ValueError:
            rel = Path(src.name)
        dst = dest_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        src_size = src.stat().st_size
        src_hash = _sha256(src)
        try:
            shutil.copy2(str(src), str(dst))
        except OSError as e:
            index["skipped"].append({"path": item["path"], "reason": f"copy-fehler: {e}"})
            continue
        # Verifikation: Ziel existiert + gleiche Groesse
        if not dst.is_file() or dst.stat().st_size != src_size:
            index["skipped"].append({"path": item["path"], "reason": "verify-fehler, Original bleibt"})
            continue
        src.unlink()  # erst jetzt sicher loeschen
        index["freed_bytes"] += src_size
        index["entries"].append({
            "original": str(src), "offloaded_to": str(dst),
            "sha256": src_hash, "size_bytes": src_size, "purpose": item["purpose"],
        })
    index_out.parent.mkdir(parents=True, exist_ok=True)
    index_out.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return index


def _folder_size(path: Path) -> Tuple[int, int]:
    total, count = 0, 0
    if not path.is_dir():
        return 0, 0
    for p in path.rglob("*"):
        if p.is_file() and not _excluded(p):
            try:
                total += p.stat().st_size
                count += 1
            except OSError:
                pass
    return total, count


def offload_folders_execute(dest_root: Path, index_out: Path,
                            folders: Tuple[Tuple[str, str], ...] = OFFLOAD_FOLDERS) -> Dict:
    """Ganze Ordner sicher nach GDrive kopieren, verifizieren, lokal entfernen."""
    index = {"dest_root": str(dest_root), "folders": [], "freed_bytes": 0, "skipped": []}
    for rel_src, rel_dest in folders:
        src = USER_ROOT / rel_src.replace("/", os.sep)
        if not src.is_dir():
            index["skipped"].append({"folder": rel_src, "reason": "nicht vorhanden"})
            continue
        dst = dest_root / rel_dest.replace("/", os.sep)
        src_bytes, src_files = _folder_size(src)
        if src_files == 0:
            index["skipped"].append({"folder": rel_src, "reason": "leer"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        except OSError as e:
            index["skipped"].append({"folder": rel_src, "reason": f"copy-fehler: {e}"})
            continue
        dst_bytes, dst_files = _folder_size(dst)
        if dst_files < src_files or dst_bytes < src_bytes:
            index["skipped"].append({
                "folder": rel_src,
                "reason": f"verify: {dst_files}/{src_files} Dateien, {dst_bytes}/{src_bytes} bytes",
            })
            continue
        shutil.rmtree(src, ignore_errors=True)
        index["freed_bytes"] += src_bytes
        index["folders"].append({
            "original": str(src), "offloaded_to": str(dst),
            "files": src_files, "size_bytes": src_bytes,
        })
    index_out.parent.mkdir(parents=True, exist_ok=True)
    index_out.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt_gb(b: int) -> str:
    return f"{b / 1024**3:.2f} GB"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Disk Dedup + Offload-Planer (zerstoerungsfrei)")
    ap.add_argument("--report", action="store_true", help="Kategorien-Vermessung")
    ap.add_argument("--dedup", action="store_true", help="Duplikate finden (Hash + Zweck)")
    ap.add_argument("--quarantine", action="store_true",
                    help="mit --dedup: Duplikate in Quarantaene verschieben (reversibel)")
    ap.add_argument("--offload-plan", action="store_true", help="GDrive-Auslagerungskandidaten")
    ap.add_argument("--offload-execute", action="store_true",
                    help="Kandidaten nach FusionHero_Offload kopieren + verifizieren + lokal loeschen")
    ap.add_argument("--include-images", action="store_true",
                    help="Pictures/DCIM-Bilder (>min) mit auslagern")
    ap.add_argument("--offload-min-mb", type=int, default=100,
                    help="Mindestgroesse fuer Offload-Kandidaten in MB (default 100)")
    ap.add_argument("--offload-dest", metavar="PATH",
                    help="GDrive-Ziel (default: Meine Ablage/FusionHero_Offload)")
    ap.add_argument("--offload-folders", action="store_true",
                    help="Ganze Offload-Ordner (SD-Modelle, LLM, Archive) auslagern")
    ap.add_argument("--full-sweep", action="store_true",
                    help="Dedup + Ordner-Offload + Datei-Offload (min 20MB)")
    ap.add_argument("--undo", metavar="MANIFEST", help="Quarantaene aus Manifest zuruecknehmen")
    ap.add_argument("--json", action="store_true", help="Ergebnis als JSON")
    ap.add_argument("--run-label", default="run", help="Ordnername des Quarantaene-Laufs")
    args = ap.parse_args(argv)

    if args.full_sweep:
        args.dedup = True
        args.quarantine = True
        args.offload_folders = True
        args.offload_execute = True
        if args.offload_min_mb == 100:
            args.offload_min_mb = 20

    roots = [USER_ROOT / r for r in SCAN_ROOTS]

    if args.undo:
        n = undo(Path(args.undo))
        print(f"[Undo] {n} Dateien wiederhergestellt aus {args.undo}")
        return 0

    if args.report:
        cats = report(roots)
        if args.json:
            print(json.dumps(cats, indent=2, ensure_ascii=False))
        else:
            total = sum(c["bytes"] for c in cats.values())
            for name, c in sorted(cats.items(), key=lambda kv: -kv[1]["bytes"]):
                print(f"  {name:10s} {_fmt_gb(c['bytes']):>10s}  ({c['files']} Dateien)")
            print(f"  {'GESAMT':10s} {_fmt_gb(total):>10s}")

    if args.dedup:
        groups = find_duplicates(roots)
        reclaimable = sum(g.size_bytes * len(g.remove) for g in groups)
        if args.json:
            print(json.dumps([vars(g) for g in groups], indent=2, ensure_ascii=False))
        else:
            for g in groups[:40]:
                print(f"  [{g.purpose}] {_fmt_gb(g.size_bytes)} x{len(g.remove)} "
                      f"behalten: {g.keep}")
                for r in g.remove:
                    print(f"      dup: {r}")
            print(f"[Dedup] {len(groups)} Gruppen, rueckgewinnbar: {_fmt_gb(reclaimable)}")
        if args.quarantine and groups:
            mp = quarantine(groups, args.run_label)
            print(f"[Dedup] Duplikate in Quarantaene verschoben. Undo-Manifest: {mp}")

    min_bytes = max(1, args.offload_min_mb) * 1024 * 1024
    do_offload = args.offload_plan or args.offload_execute

    if do_offload:
        plan = offload_plan(roots, include_images=args.include_images, min_bytes=min_bytes)
        total = sum(x["size_bytes"] for x in plan)
        if args.offload_plan or not args.offload_execute:
            if args.json:
                print(json.dumps(plan, indent=2, ensure_ascii=False))
            else:
                for x in plan[:40]:
                    print(f"  [{x['purpose']}] {x['gb']:>6.2f} GB  {x['path']}")
                print(f"[Offload] {len(plan)} Kandidaten, auslagerbar: {_fmt_gb(total)}")

        if args.offload_execute:
            dest = Path(args.offload_dest) if args.offload_dest else _gdrive_dest_root()
            if not dest:
                print("[Offload] FEHLER: Google Drive nicht gefunden. "
                      "Setze FUSION_GDRIVE_OFFLOAD oder --offload-dest.", file=sys.stderr)
                return 2
            stamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d_%H%M%S")
            index_out = USER_ROOT / "_dedup_quarantine" / f"offload_{stamp}" / "offload_index.json"
            result = offload_execute(plan, dest, index_out)
            freed = result.get("freed_bytes", 0)
            skipped = len(result.get("skipped", []))
            done = len(result.get("entries", []))
            print(f"[Offload] {done} Dateien ausgelagert, {_fmt_gb(freed)} freigegeben, "
                  f"{skipped} uebersprungen")
            print(f"[Offload] Ziel: {dest}")
            print(f"[Offload] Index: {index_out}")
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.offload_folders:
        dest = Path(args.offload_dest) if args.offload_dest else _gdrive_dest_root()
        if not dest:
            print("[Folders] FEHLER: Google Drive nicht gefunden.", file=sys.stderr)
            return 2
        stamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d_%H%M%S")
        index_out = USER_ROOT / "_dedup_quarantine" / f"offload_folders_{stamp}" / "index.json"
        result = offload_folders_execute(dest, index_out)
        freed = result.get("freed_bytes", 0)
        done = len(result.get("folders", []))
        print(f"[Folders] {done} Ordner ausgelagert, {_fmt_gb(freed)} freigegeben")
        for f in result.get("folders", []):
            print(f"  -> {f['offloaded_to']} ({f['files']} Dateien)")
        print(f"[Folders] Index: {index_out}")
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    if not any([args.report, args.dedup, do_offload, args.offload_folders, args.undo]):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
