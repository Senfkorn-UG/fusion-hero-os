#!/bin/bash
# Tailscale Installation + Mesh Setup for Fusion Hero OS (Linux/WSL)
# Usage: export TS_AUTHKEY=tskey-auth-... && sudo ./tailscale_install.sh

set -euo pipefail

echo "[Fusion Hero OS] Tailscale Installation & Mesh Config starting..."

if [[ -z "${TS_AUTHKEY:-}" ]]; then
    echo "Set TS_AUTHKEY first (reusable key from login.tailscale.com/admin/settings/keys)"
    exit 1
fi

echo "-> Downloading and installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "Tailscale binary installed."

if command -v systemctl &> /dev/null; then
    echo "-> Enabling tailscaled service..."
    systemctl enable --now tailscaled || true
fi

echo ""
echo "-> Running tailscale up..."
tailscale up \
    --reset \
    --auth-key="${TS_AUTHKEY}" \
    --hostname=desktop-kpki9e4 \
    --accept-routes \
    --ssh

echo ""
tailscale status || true
echo ""
echo "Install complete. Optional tags after ACL tagOwners:"
echo "  tailscale up --advertise-tags=tag:fusion-node-desktop --advertise-exit-node"
