#!/bin/bash
# Tailscale Installation + Mesh Setup for Fusion Hero OS (Linux/WSL)
# Usage:
#   export TS_AUTHKEY=tskey-auth-...
#   sudo -E ./tailscale_install.sh

set -euo pipefail

echo "[Fusion Hero OS] Tailscale Installation & Mesh Config starting..."

if [[ -z "${TS_AUTHKEY:-}" ]]; then
    echo "Set TS_AUTHKEY first (reusable key from login.tailscale.com/admin/settings/keys)"
    echo "  export TS_AUTHKEY=tskey-auth-..."
    echo "  sudo -E ./tailscale_install.sh"
    exit 1
fi

TS_CMD=(tailscale)
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    TS_CMD=(sudo tailscale)
fi

if command -v tailscale >/dev/null 2>&1; then
    echo "-> Tailscale already installed: $(command -v tailscale)"
else
    echo "-> Downloading and installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
fi

if command -v systemctl >/dev/null 2>&1 && [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    echo "-> Enabling tailscaled service..."
    systemctl enable --now tailscaled || true
fi

if [[ -z "${TS_HOSTNAME:-}" ]]; then
    if grep -qi microsoft /proc/version 2>/dev/null; then
        TS_HOSTNAME="mainframe-wsl"
    else
        TS_HOSTNAME="mainframe"
    fi
fi

echo ""
echo "-> Running tailscale up (hostname=${TS_HOSTNAME})..."
"${TS_CMD[@]}" up \
    --reset \
    --auth-key="${TS_AUTHKEY}" \
    --hostname="${TS_HOSTNAME}" \
    --accept-routes \
    --ssh

echo ""
"${TS_CMD[@]}" status || true
echo ""
echo "Install complete. Optional tags after ACL tagOwners:"
echo "  tailscale up --advertise-tags=tag:fusion-node-desktop --advertise-exit-node"
