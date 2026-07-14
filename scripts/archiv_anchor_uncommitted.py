#!/usr/bin/env python3
"""
archiv_anchor_uncommitted.py — Nicht committete Dateien als obfuskierte SHA256+GPG-Anker.

Erzeugt unter archiv/obfuscated/<stamp>/:
  manifest.json   — Metadaten + SHA256-Register
  blobs/*.obf     — GPG-symmetric + Obfuscation
  RECOVER.sh      — Wiederherstellungs-Skript
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
ARCHIV_ROOT = REPO / "archiv" / "obfuscated"
<<<<<<< HEAD
DEFAULT_PASSPHRASE_SALT = "fusion-hero-os|archiv|desktop-kpki9e4|tail391adb.ts.net"
=======
DEFAULT_PASSPHRASE_SALT = "fusion-hero-os|archiv|desktop-kpki9e4|example.ts.net"
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09

IGNORED_SCAN = {
    ".git",
    "archiv/obfuscated",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _default_passphrase() -> str:
    return os.getenv("FUSION_ARCHIV_GPG_PASSPHRASE") or _sha256_bytes(
        DEFAULT_PASSPHRASE_SALT.encode()
    )


def _gpg_encrypt(data: bytes, passphrase: str) -> str:
    proc = subprocess.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--pinentry-mode", "loopback",
            "--passphrase", passphrase,
            "--symmetric",
            "--cipher-algo", "AES256",
            "--armor",
            "-o", "-",
        ],
        input=data,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    return proc.stdout.decode("utf-8")


def _obfuscate_armored(armored: str, digest: str) -> str:
    """Interleave SHA256-Fragmente in Base64-Zeilen (reversibel)."""
    body = armored.strip()
    b64 = base64.b64encode(body.encode("utf-8")).decode("ascii")
    chunk = 48
    lines: List[str] = []
    for i in range(0, len(b64), chunk):
        part = b64[i : i + chunk]
        marker = digest[(i // chunk) * 8 : (i // chunk) * 8 + 8]
        if len(marker) < 8:
            marker = (digest + digest)[:8]
        lines.append(f"{marker}:{part[::-1]}")
    return "\n".join(lines)


def _deobfuscate_armored(obf: str) -> str:
    parts: List[str] = []
    for line in obf.strip().splitlines():
        if ":" not in line:
            continue
        _, rev = line.split(":", 1)
        parts.append(rev[::-1])
    raw = base64.b64decode("".join(parts)).decode("utf-8")
    return raw


def _safe_blob_name(rel: str, digest: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", rel)[:120]
    return f"{digest[:12]}_{slug}.obf"


def _git_uncommitted(include_ignored: bool) -> List[Path]:
    proc = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    paths: List[Path] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path_str = line[3:].strip().strip('"')
        if " -> " in path_str:
            path_str = path_str.split(" -> ", 1)[1].strip('"')
        p = REPO / path_str
        if p.is_file():
            paths.append(p)

    if include_ignored:
        extras = [
            REPO / ".fusion",
            REPO / "src/normal_os/internal_llm",
            REPO / "workstation/.env",
        ]
        for root in extras:
            if not root.exists():
                continue
            if root.is_file():
                paths.append(root)
            else:
                for f in root.rglob("*"):
                    if f.is_file() and not any(x in f.parts for x in IGNORED_SCAN):
                        paths.append(f)

    # dedupe, stable sort
    uniq = sorted({p.resolve() for p in paths})
    out: List[Path] = []
    for p in uniq:
        try:
            p.relative_to(REPO.resolve())
            if p.is_file():
                out.append(p)
        except ValueError:
            continue
    return out


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO.resolve()))


def anchor_files(
    files: List[Path],
    out_dir: Path,
    passphrase: str,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    blobs_dir = out_dir / "blobs"
    blobs_dir.mkdir(exist_ok=True)

    entries: List[Dict[str, Any]] = []
    for path in files:
        rel = _rel(path)
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        armored = _gpg_encrypt(data, passphrase)
        obf = _obfuscate_armored(armored, digest)
        blob_name = _safe_blob_name(rel, digest)
        blob_path = blobs_dir / blob_name
        header = (
            "-----BEGIN FUSION ARCHIV OBF-----\n"
            f"Version: 1\nSHA256: {digest}\nPath: {rel}\n"
            "Cipher: AES256\nObfuscation: interleaved_sha256_b64rev\n"
            "-----BEGIN OBFUSCATED PAYLOAD-----\n"
        )
        footer = "\n-----END OBFUSCATED PAYLOAD-----\n-----END FUSION ARCHIV OBF-----\n"
        blob_path.write_text(header + obf + footer, encoding="utf-8")

        entries.append({
            "path": rel,
            "sha256": digest,
            "size_bytes": len(data),
            "blob": f"blobs/{blob_name}",
            "gpg": "symmetric-aes256",
            "obfuscation": "interleaved_sha256_b64rev",
        })

    manifest = {
        "archiv_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo": "fusion-hero-os",
        "algorithm": "sha256+gpg-aes256+obfuscation",
        "passphrase_hint": "sha256(FUSION_ARCHIV_GPG_PASSPHRASE or default salt)",
        "passphrase_sha256": _sha256_bytes(passphrase.encode()),
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest["manifest_sha256"] = _sha256_bytes(
        json.dumps(entries, sort_keys=True, ensure_ascii=False).encode()
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    recover = """#!/usr/bin/env bash
# RECOVER.sh — Stellt archivierte Dateien aus .obf-Blobs wieder her.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS="${FUSION_ARCHIV_GPG_PASSPHRASE:-}"
if [ -z "$PASS" ]; then
  PASS="$(python3 - <<'PY'
import hashlib
<<<<<<< HEAD
print(hashlib.sha256(b"fusion-hero-os|archiv|desktop-kpki9e4|tail391adb.ts.net").hexdigest())
=======
print(hashlib.sha256(b"fusion-hero-os|archiv|desktop-kpki9e4|example.ts.net").hexdigest())
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
PY
)"
fi
python3 "$(dirname "$DIR")/recover_obfuscated.py" --root "$DIR" --passphrase "$PASS" "$@"
"""
    (out_dir / "RECOVER.sh").write_text(recover, encoding="utf-8")
    os.chmod(out_dir / "RECOVER.sh", 0o755)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Anchor uncommitted files to archiv/obfuscated")
    parser.add_argument("--include-ignored", action="store_true", help="Also archive .fusion, internal_llm, workstation/.env")
    parser.add_argument("--stamp", default=datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S"))
    args = parser.parse_args()

    files = _git_uncommitted(include_ignored=args.include_ignored)
    if not files:
        print("No uncommitted files to anchor.", file=sys.stderr)
        return 0

    out_dir = ARCHIV_ROOT / args.stamp
    passphrase = _default_passphrase()
    manifest = anchor_files(files, out_dir, passphrase)

    latest = ARCHIV_ROOT / "latest"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(out_dir.name)

    print(json.dumps({
        "status": "ok",
        "out_dir": str(out_dir.relative_to(REPO)),
        "files": manifest["entry_count"],
        "manifest_sha256": manifest["manifest_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
