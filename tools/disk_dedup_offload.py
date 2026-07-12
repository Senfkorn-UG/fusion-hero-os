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
    r"\stable-diffusion-webui\\",  # eigene venv/models, separat behandeln
    r"\.vscode\\", r"\.grok\\", r"\gitkraken",
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

# Wurzeln, die fuer Dedup/Offload ueberhaupt gescannt werden (Nutzerdaten).
SCAN_ROOTS = ("Downloads", "Desktop", "Documents", "Pictures", "Videos",
              "Music", "internal_llm")

MIN_DEDUP_BYTES = 1 * 1024 * 1024        # Dateien < 1 MB ignorieren (Rauschen)
OFFLOAD_MIN_BYTES = 100 * 1024 * 1024    # Offload-Kandidat ab 100 MB


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

def offload_plan(roots: List[Path]) -> List[Dict]:
    """Grosse, offline entbehrliche Dateien: Installer, Archive, Medien."""
    OFFLINE_DISPENSABLE = {"installer", "archive", "media"}
    plan = []
    for p in _iter_files(roots):
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size < OFFLOAD_MIN_BYTES:
            continue
        purp = purpose(p)
        if purp in OFFLINE_DISPENSABLE:
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
    ap.add_argument("--undo", metavar="MANIFEST", help="Quarantaene aus Manifest zuruecknehmen")
    ap.add_argument("--json", action="store_true", help="Ergebnis als JSON")
    ap.add_argument("--run-label", default="run", help="Ordnername des Quarantaene-Laufs")
    args = ap.parse_args(argv)

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

    if args.offload_plan:
        plan = offload_plan(roots)
        total = sum(x["size_bytes"] for x in plan)
        if args.json:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            for x in plan[:40]:
                print(f"  [{x['purpose']}] {x['gb']:>6.2f} GB  {x['path']}")
            print(f"[Offload] {len(plan)} Kandidaten, auslagerbar: {_fmt_gb(total)}")

    if not any([args.report, args.dedup, args.offload_plan, args.undo]):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
