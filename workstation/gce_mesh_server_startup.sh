#!/bin/bash
# GCE startup — Fusion Hero OS mesh exit + fractal replica host
set -euo pipefail

LOG=/var/log/fusion-mesh-startup.log
exec > >(tee -a "$LOG") 2>&1
echo "=== Fusion Mesh GCE startup $(date -Iseconds) ==="

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl git python3 python3-pip ca-certificates

# Tailscale
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
  systemctl enable --now tailscaled
fi

TS_KEY="$(curl -fsS -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/ts-authkey 2>/dev/null || true)"
HOSTNAME_TAG="$(curl -fsS -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/fusion-hostname 2>/dev/null || true)"
HOSTNAME_TAG="${HOSTNAME_TAG:-fusion-mesh-exit}"

if [[ -n "$TS_KEY" && "$TS_KEY" != "unset" ]]; then
  tailscale up --reset \
    --auth-key="$TS_KEY" \
    --hostname="$HOSTNAME_TAG" \
    --accept-routes \
    --advertise-exit-node \
    --ssh || true
  echo "Tailscale joined as $HOSTNAME_TAG"
else
  echo "No ts-authkey metadata — run tailscale up manually after SSH"
fi

# Fractal replica dir (hero-docs optional)
mkdir -p /home/admin_fuhos/.fusion/mesh/fractal/replicas
chmod -R 777 /home/admin_fuhos/.fusion 2>/dev/null || mkdir -p /root/.fusion/mesh/fractal/replicas

echo "Startup complete"