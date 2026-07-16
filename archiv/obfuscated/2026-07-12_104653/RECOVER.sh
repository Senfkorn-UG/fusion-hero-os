#!/usr/bin/env bash
# RECOVER.sh — Stellt archivierte Dateien aus .obf-Blobs wieder her.
# Passphrase-Ableitung (kein Geheimnis im Skript):
#   1. FUSION_ARCHIV_GPG_PASSPHRASE (verbatim), sonst
#   2. sha256(FUSION_ARCHIVE_LEGACY_SALT) fuer pre-v10 Archive, sonst
#   3. sha256 des neutralen Default-Salts.
# Dieser Anker stammt aus pre-v10 und benoetigt den privaten Legacy-Salt via
# FUSION_ARCHIVE_LEGACY_SALT (der historische Wert ist nicht im Baum hinterlegt).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS="${FUSION_ARCHIV_GPG_PASSPHRASE:-}"
if [ -z "$PASS" ]; then
  SALT="${FUSION_ARCHIVE_LEGACY_SALT:-fusion-hero-os|archiv|v10}"
  PASS="$(SALT="$SALT" python3 - <<'PY'
import hashlib, os
print(hashlib.sha256(os.environ["SALT"].encode()).hexdigest())
PY
)"
fi
python3 "$(dirname "$DIR")/recover_obfuscated.py" --root "$DIR" --passphrase "$PASS" "$@"
