#!/usr/bin/env bash
# followup-all.sh — Alle Session-Follow-ups in einem Durchlauf
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "╔══════════════════════════════════════════╗"
echo "║  Fusion Hero OS — Follow-up All-in-One   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "[1/8] README/Mesh — bereits in mesh_roles.yaml verankert"
python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'src/normal_os/integration'); from mesh_roles import get_mainframe_hostname; print('  Mainframe:', get_mainframe_hostname())" 2>/dev/null || true

echo ""
echo "[2/8] Verification LLM-Recovery Status"
PYTHONPATH=src/normal_os/core python3 -c "from verification_orchestrator import status; import json; print(json.dumps({k:status()[k] for k in ('llm_recovery_enabled','recovery_enabled')}, indent=2))" 2>/dev/null || true

echo ""
echo "[3/8] Tailscale WSL"
bash "$ROOT/workstation/tailscale_wsl_setup.sh" 2>&1 | sed 's/^/  /'

echo ""
echo "[4/8] AudioRelay (Windows)"
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/check-audio-relay.ps1" 2>&1 | sed 's/^/  /'
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/route-audio-to-phone.ps1" 2>&1 | sed 's/^/  /' || true
else
  echo "  powershell.exe nicht verfuegbar"
fi

echo ""
echo "[5/8] Gmail Triage Bridge"
python3 "$ROOT/scripts/gmail_triage_bridge.py" 2 2>&1 | sed 's/^/  /'

echo ""
echo "[6/8] Archiv-Anker (uncommitted)"
python3 "$ROOT/scripts/archiv_anchor_uncommitted.py" --include-ignored 2>&1 | sed 's/^/  /' || true

echo ""
echo "[7/8] Planova Inneneinrichter (Windows)"
if command -v powershell.exe >/dev/null 2>&1; then
  PLAN_EXE="/mnt/c/Users/Admin/Programs/planova/planova.exe"
  if [ -f "$PLAN_EXE" ]; then
    echo "  Bereits installiert: $PLAN_EXE"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/install-planova.ps1" -SkipBuild 2>&1 | sed 's/^/  /' || true
  else
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/install-planova.ps1" -Auto 2>&1 | sed 's/^/  /' || true
  fi
else
  echo "  powershell.exe nicht verfuegbar"
fi

echo ""
echo "[8/8] GDrive Storage Policy (nicht-operative Daten)"
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT/workstation/apply-storage-policy.ps1" 2>&1 | sed 's/^/  /' || true
else
  echo "  powershell.exe nicht verfuegbar"
fi

echo ""
echo "=== Follow-up abgeschlossen ==="
