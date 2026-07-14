#!/bin/bash
# Tailscale IP forwarding + UDP GRO tuning for GCE subnet router / exit node
set -euo pipefail

echo "=== 1) IP forwarding (persistent) ==="
sudo tee /etc/sysctl.d/99-tailscale.conf >/dev/null <<'EOF'
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

echo "=== 2) UDP GRO (immediate) ==="
NETDEV="$(ip -o route get 8.8.8.8 | cut -f 5 -d ' ')"
echo "netdev=${NETDEV}"
sudo ethtool -K "${NETDEV}" rx-udp-gro-forwarding on rx-gro-list off

echo "=== 2b) UDP GRO (persistent via networkd-dispatcher) ==="
sudo mkdir -p /etc/networkd-dispatcher/routable.d
printf '#!/bin/sh\n\nethtool -K %s rx-udp-gro-forwarding on rx-gro-list off\n' "${NETDEV}" \
  | sudo tee /etc/networkd-dispatcher/routable.d/50-tailscale >/dev/null
sudo chmod 755 /etc/networkd-dispatcher/routable.d/50-tailscale
sudo /etc/networkd-dispatcher/routable.d/50-tailscale
test $? -eq 0 && echo "dispatcher ok" || echo "dispatcher error"

echo "=== 3) Tailscale subnet router + exit node ==="
sudo tailscale up \
  --hostname=fusion-mesh-exit \
  --accept-routes \
  --advertise-exit-node \
  --advertise-routes=10.156.0.0/20 \
  --ssh 2>&1 | head -10 || true

echo "=== status ==="
sudo tailscale status 2>&1 | head -10
sudo tailscale ip -4 2>&1 || true