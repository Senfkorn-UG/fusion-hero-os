#!/bin/bash
# Tailscale Installation + Mesh Setup for Fusion Hero OS
# Generated for desktop node integration (hostname + tag + exit node)
# Usage: sudo ./tailscale_install.sh   (or from control script)
# Date: 2026-07-14

set -e

echo "🚀 [Fusion Hero OS] Tailscale Installation & Mesh Config starting..."

# 1. Install Tailscale (official)
echo "→ Downloading and installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "✅ Tailscale binary installed."

# 2. Enable service (Linux)
if command -v systemctl &> /dev/null; then
    echo "→ Enabling tailscaled service..."
    sudo systemctl enable --now tailscaled || true
    echo "✅ tailscaled service enabled."
else
    echo "⚠️  systemctl not found – assuming manual service management."
fi

# 3. Authenticate and configure with pre-auth key + Fusion Mesh settings
# Node: desktop (Windows main workstation, aliased in mesh)
# Tag: fusion-node-desktop (for ACLs and mesh segmentation)
# Advertise as exit node for other mesh participants (phone, agents)
# Accept routes from other nodes
echo ""
echo "🔐 Running tailscale up (unattended with auth key)..."
echo "   Hostname: desktop-kpki9e4"
echo "   Tag:      tag:fusion-node-desktop"
echo "   Features: --advertise-exit-node --accept-routes --ssh"

sudo tailscale up \
    --auth-key=tskey-auth-kfffkrbmhF11CNTRL-srWw54orSqToi6yGMjfSqTFyk1PE6hsmT \
    --hostname=desktop-kpki9e4 \
    --advertise-tags=tag:fusion-node-desktop \
    --advertise-exit-node \
    --accept-routes \
    --ssh

echo ""
echo "✅ Tailscale configured and authenticated."
echo ""

# 4. Show status
echo "📡 Current status:"
tailscale status || echo "(status output may be limited until fully connected)"

echo ""
echo "✅ Install complete."
echo ""
echo "Next steps (recommended):"
echo "  ./tailscale_control.sh start"
echo "  ./tailscale_control.sh mesh"
echo "  ./tailscale_control.sh all"
echo ""
echo "Verify tag & exit node:"
echo "  tailscale status"
echo "  tailscale up --advertise-exit-node   (if needed to re-advertise)"
echo ""
echo "For other nodes to use this as exit node:"
echo "  tailscale up --exit-node=100.64.104.58 --exit-node-allow-lan-access"
echo ""
echo "⚠️  Security note: The auth key used here is single-use or time-limited."
echo "    Regenerate new keys in the Tailscale admin console if needed."