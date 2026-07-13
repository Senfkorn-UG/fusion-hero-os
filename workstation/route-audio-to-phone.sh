#!/usr/bin/env bash
# Route PC audio to phone headset via AudioRelay (runs Windows PowerShell script).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIN_SCRIPT="$SCRIPT_DIR/route-audio-to-phone.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WIN_SCRIPT"
