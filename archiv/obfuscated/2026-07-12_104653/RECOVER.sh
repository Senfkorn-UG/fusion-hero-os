#!/usr/bin/env bash
# RECOVER.sh — Stellt archivierte Dateien aus .obf-Blobs wieder her.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS="${FUSION_ARCHIV_GPG_PASSPHRASE:-}"
if [ -z "$PASS" ]; then
  PASS="$(python3 - <<'PY'
import hashlib
print(hashlib.sha256(b"fusion-hero-os|archiv|desktop-kpki9e4|tail391adb.ts.net").hexdigest())
PY
)"
fi
python3 "$(dirname "$DIR")/recover_obfuscated.py" --root "$DIR" --passphrase "$PASS" "$@"
