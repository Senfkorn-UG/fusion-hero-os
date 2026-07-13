#!/usr/bin/env python3
"""recover_obfuscated.py — De-obfuscate + GPG decrypt archiv blobs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _deobfuscate(text: str) -> str:
    import base64

    m = re.search(
        r"-----BEGIN OBFUSCATED PAYLOAD-----\n(.*)\n-----END OBFUSCATED PAYLOAD-----",
        text,
        re.DOTALL,
    )
    if not m:
        raise ValueError("missing obfuscated payload block")
    obf = m.group(1).strip()
    parts = []
    for line in obf.splitlines():
        if ":" not in line:
            continue
        _, rev = line.split(":", 1)
        parts.append(rev[::-1])
    return base64.b64decode("".join(parts)).decode("utf-8")


def _gpg_decrypt(armored: str, passphrase: str) -> bytes:
    proc = subprocess.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--pinentry-mode", "loopback",
            "--passphrase", passphrase,
            "--decrypt",
        ],
        input=armored.encode(),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--passphrase", required=True)
    parser.add_argument("--target", default="restored")
    args = parser.parse_args()

    root = Path(args.root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    target = root / args.target
    target.mkdir(parents=True, exist_ok=True)

    for entry in manifest.get("entries", []):
        blob = root / entry["blob"]
        text = blob.read_text(encoding="utf-8")
        armored = _deobfuscate(text)
        data = _gpg_decrypt(armored, args.passphrase)
        out = target / entry["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"restored: {entry['path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
