#!/usr/bin/env bash
# tailscale_wsl_setup.sh - Tailscale in WSL mit Windows-Tailnet verbinden
set -euo pipefail

STATUS_DIR="${HOME}/.fusion"
LOGIN_URL_FILE="${STATUS_DIR}/tailscale-wsl-login.url"
STATUS_FILE="${STATUS_DIR}/tailscale-wsl.status.json"
mkdir -p "$STATUS_DIR"

write_status() {
  local state="$1" msg="$2"
  printf '{"state":"%s","message":"%s","updated":"%s"}\n' \
    "$state" "$msg" "$(date -Iseconds)" > "$STATUS_FILE"
}

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
  echo "WSL Tailscale ausgeloggt - starte Login..."
  LOGIN_URL=$(echo "$STATUS" | grep -o 'https://login.tailscale.com[^ ]*' | head -1 || true)
  if [ -n "$LOGIN_URL" ]; then
    echo "$LOGIN_URL" > "$LOGIN_URL_FILE"
    echo "Login-URL gespeichert: $LOGIN_URL_FILE"
    echo "  $LOGIN_URL"
  fi
  if [ -n "${TS_AUTHKEY:-}" ]; then
    echo "TS_AUTHKEY gesetzt - headless login..."
    sudo tailscale up --accept-routes --auth-key "$TS_AUTHKEY" 2>&1 || true
  else
    echo ""
    echo "Interaktiv in WSL-Terminal (sudo + Browser):"
    echo "  sudo tailscale up --accept-routes"
    echo "Account: stephan95g@googlemail.com (gleich wie Windows)"
    sudo tailscale up --accept-routes 2>&1 || true
  fi
else
  echo "Tailscale WSL bereits verbunden."
  write_status "success" "connected"
fi

echo ""
tailscale status 2>&1 | head -15 || true

if tailscale status 2>&1 | grep -qi "logged out"; then
  write_status "pending" "login_required"
else
  write_status "success" "connected"
fi
