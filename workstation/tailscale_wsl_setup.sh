#!/usr/bin/env bash
# tailscale_wsl_setup.sh — Tailscale in WSL mit Windows-Tailnet verbinden
set -euo pipefail

echo "=== Tailscale WSL Setup ==="

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale nicht installiert. Installiere..."
  if [ -f "$(dirname "$0")/tailscale_install.sh" ]; then
    sudo "$(dirname "$0")/tailscale_install.sh"
  else
    curl -fsSL https://tailscale.com/install.sh | sh
  fi
fi

STATUS=$(tailscale status 2>&1 || true)
if echo "$STATUS" | grep -qi "logged out"; then
  echo "WSL Tailscale ausgeloggt — starte Login..."
  sudo tailscale up --accept-routes 2>&1 || true
  echo ""
  echo "Falls Browser-Login nötig: sudo tailscale up"
  echo "Gleicher Account wie Windows: user@example.com"
else
  echo "Tailscale WSL bereits verbunden."
fi

echo ""
tailscale status 2>&1 | head -15 || true
