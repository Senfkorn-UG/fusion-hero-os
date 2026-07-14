#!/usr/bin/env python3
"""
archiv_anchor_uncommitted.py — Nicht committete Dateien als obfuskierte GPG-Anker.

Erzeugt unter archiv/obfuscated/<stamp>/:
  manifest.json   — Metadaten + Integritaets-Register + KDF-Block
  blobs/*.obf     — GPG-symmetric + Obfuscation
  RECOVER.sh      — Wiederherstellungs-Skript

Kryptographie (archiv_version 2.0):
  * Der GPG-Passphrase wird ueber eine versionierte, langsame Schluessel-
    ableitung (``hashlib.scrypt``) aus geheimem Material und einem
    zufaelligen Per-Archiv-Salt abgeleitet — NICHT ueber ein schnelles
    SHA256. Der Salt ist nicht-geheim und wird im Manifest hinterlegt.
  * Integritaets-Digests ueber die (nicht-geheimen) Dateibytes verwenden
    weiterhin SHA256 und sind bewusst getrennt benannt (``_content_digest``),
    damit klar ist, dass hier keine Credential-Ableitung stattfindet.
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
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]
ARCHIV_ROOT = REPO / "archiv" / "obfuscated"

# Neutral default secret material for NEW archives when no explicit passphrase
# is supplied. Contains no personal, device, or network identifiers. This is a
# low-entropy default only — set FUSION_ARCHIV_GPG_PASSPHRASE for real secrecy.
DEFAULT_PASSPHRASE_SALT = "fusion-hero-os|archiv|v10"

GPG_PASSPHRASE_ENV = "FUSION_ARCHIV_GPG_PASSPHRASE"

# Versioned scrypt KDF parameters (archiv_version 2.0). scrypt is a memory-hard
# key-derivation function; unlike a bare SHA256 it is resistant to brute-force
# on weak/low-entropy secret material. Parameters are stored in the manifest so
# recovery is self-describing. maxmem is raised above scrypt's 32 MiB default so
# the chosen (n, r, p) stays within the limit.
KDF_NAME = "scrypt"
KDF_VERSION = 2
KDF_N = 2 ** 14  # CPU/memory cost
KDF_R = 8        # block size
KDF_P = 1        # parallelism
KDF_DKLEN = 32   # derived key length (bytes)
KDF_MAXMEM = 64 * 1024 * 1024  # 64 MiB

IGNORED_SCAN = {
    ".git",
    "archiv/obfuscated",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}


def _content_digest(data: bytes) -> str:
    """SHA256 over NON-SECRET content bytes, for integrity only.

    This is not a credential/passphrase derivation: the input is the archived
    file's plaintext bytes (or the manifest), never a secret key or salt. It is
    named distinctly from the KDF so static analysis and readers can tell the
    two apart.
    """
    return hashlib.sha256(data).hexdigest()


def _content_digest_file(path: Path) -> str:
    """Streaming SHA256 integrity digest over a file's NON-SECRET bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _secret_material() -> Tuple[bytes, str]:
    """Return (secret_bytes, source_label) for KDF input.

    Precedence:
      1. Explicit ``FUSION_ARCHIV_GPG_PASSPHRASE`` (recommended for real use).
      2. The neutral, non-personal default salt (low entropy — dev/default only).
    The secret is never logged or persisted; only the non-secret KDF salt and
    parameters are recorded in the manifest.
    """
    explicit = os.getenv(GPG_PASSPHRASE_ENV)
    if explicit:
        return explicit.encode("utf-8"), "env:FUSION_ARCHIV_GPG_PASSPHRASE"
    return DEFAULT_PASSPHRASE_SALT.encode("utf-8"), "default-salt"


def _derive_passphrase(secret: bytes, kdf_salt: bytes) -> str:
    """Derive the GPG passphrase from secret material via scrypt (KDF v2).

    Memory-hard, versioned, and salted with a random per-archive salt. Returns
    a base64 text passphrase suitable for GPG's ``--passphrase``.
    """
    derived = hashlib.scrypt(
        secret,
        salt=kdf_salt,
        n=KDF_N,
        r=KDF_R,
        p=KDF_P,
        dklen=KDF_DKLEN,
        maxmem=KDF_MAXMEM,
    )
    return base64.b64encode(derived).decode("ascii")


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
    secret: bytes,
    source_label: str,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    blobs_dir = out_dir / "blobs"
    blobs_dir.mkdir(exist_ok=True)

    # Random, non-secret per-archive KDF salt (stored in the manifest).
    kdf_salt = os.urandom(16)
    passphrase = _derive_passphrase(secret, kdf_salt)

    entries: List[Dict[str, Any]] = []
    for path in files:
        rel = _rel(path)
        data = path.read_bytes()
        digest = _content_digest(data)
        armored = _gpg_encrypt(data, passphrase)
        obf = _obfuscate_armored(armored, digest)
        blob_name = _safe_blob_name(rel, digest)
        blob_path = blobs_dir / blob_name
        header = (
            "-----BEGIN FUSION ARCHIV OBF-----\n"
            f"Version: 2\nSHA256: {digest}\nPath: {rel}\n"
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
        "archiv_version": "2.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo": "fusion-hero-os",
        "algorithm": "scrypt-kdf+gpg-aes256+obfuscation",
        # Non-secret KDF descriptor. The passphrase is derived via scrypt from
        # secret material + this salt; neither the secret nor the derived
        # passphrase is stored here.
        "kdf": {
            "name": KDF_NAME,
            "version": KDF_VERSION,
            "n": KDF_N,
            "r": KDF_R,
            "p": KDF_P,
            "dklen": KDF_DKLEN,
            "salt_b64": base64.b64encode(kdf_salt).decode("ascii"),
            "secret_source": source_label,
            "output": "base64",
        },
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest["manifest_sha256"] = _content_digest(
        json.dumps(entries, sort_keys=True, ensure_ascii=False).encode()
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    recover = """#!/usr/bin/env bash
# RECOVER.sh — Stellt archivierte Dateien aus .obf-Blobs wieder her (archiv_version 2.0).
# Kein Geheimnis im Skript: der GPG-Passphrase wird per scrypt aus geheimem
# Material + dem im manifest.json hinterlegten (nicht-geheimen) Salt abgeleitet.
#   Geheim-Material: FUSION_ARCHIV_GPG_PASSPHRASE, sonst neutraler Default-Salt.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS="$(python3 - "$DIR" <<'PY'
import base64, hashlib, json, os, sys
root = sys.argv[1]
with open(os.path.join(root, "manifest.json"), encoding="utf-8") as fh:
    kdf = json.load(fh)["kdf"]
secret = os.getenv("FUSION_ARCHIV_GPG_PASSPHRASE", "fusion-hero-os|archiv|v10").encode()
derived = hashlib.scrypt(
    secret,
    salt=base64.b64decode(kdf["salt_b64"]),
    n=kdf["n"], r=kdf["r"], p=kdf["p"], dklen=kdf["dklen"],
    maxmem=64 * 1024 * 1024,
)
print(base64.b64encode(derived).decode("ascii"))
PY
)"
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
    secret, source_label = _secret_material()
    manifest = anchor_files(files, out_dir, secret, source_label)

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
