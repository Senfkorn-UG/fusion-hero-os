#!/usr/bin/env bash
# tailscale_wsl_login.sh — WSL Tailscale mit gleichem Google-Account wie Windows
set -euo pipefail

echo "=== Tailscale WSL Login ==="
echo "Account: stephan95g@googlemail.com (gleich wie Windows)"
echo ""

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale fehlt — installiere..."
  curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "Starte Login (sudo erforderlich)..."
echo ""
if sudo tailscale up --accept-routes --reset 2>&1; then
  echo ""
  echo "OK — WSL verbunden:"
  tailscale status | head -10
else
  echo ""
  echo "Falls interaktiv noetig, in WSL-Terminal ausfuehren:"
  echo "  sudo tailscale up --accept-routes"
  echo ""
  echo "Login-URL (Browser):"
  tailscale status 2>&1 | grep -o 'https://login.tailscale.com[^ ]*' | head -1 || true
fi
