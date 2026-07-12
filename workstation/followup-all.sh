#!/usr/bin/env bash
# followup-all.sh — Alle Session-Follow-ups in einem Durchlauf
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "╔══════════════════════════════════════════╗"
echo "║  Fusion Hero OS — Follow-up All-in-One   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "[1/6] README/Mesh — bereits in mesh_roles.yaml verankert"
python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'src/normal_os/integration'); from mesh_roles import get_mainframe_hostname; print('  Mainframe:', get_mainframe_hostname())" 2>/dev/null || true

echo ""
echo "[2/6] Verification LLM-Recovery Status"
PYTHONPATH=src/normal_os/core python3 -c "from verification_orchestrator import status; import json; print(json.dumps({k:status()[k] for k in ('llm_recovery_enabled','recovery_enabled')}, indent=2))" 2>/dev/null || true

echo ""
echo "[3/6] Tailscale WSL"
bash "$ROOT/workstation/tailscale_wsl_setup.sh" 2>&1 | sed 's/^/  /'

echo ""
echo "[4/6] AudioRelay (Windows)"
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/check-audio-relay.ps1" 2>&1 | sed 's/^/  /'
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/route-audio-to-phone.ps1" 2>&1 | sed 's/^/  /' || true
else
  echo "  powershell.exe nicht verfuegbar"
fi

echo ""
echo "[5/6] Gmail Triage Bridge"
python3 "$ROOT/scripts/gmail_triage_bridge.py" 2 2>&1 | sed 's/^/  /'

echo ""
echo "[6/6] Archiv-Anker (uncommitted)"
python3 "$ROOT/scripts/archiv_anchor_uncommitted.py" --include-ignored 2>&1 | sed 's/^/  /' || true

echo ""
echo "=== Follow-up abgeschlossen ==="
