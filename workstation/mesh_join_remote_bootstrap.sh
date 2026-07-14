#!/bin/bash
# Remote Linux leaf — Tailscale + optional Fusion hero-docs (mesh replica)
# Invoked by mesh_join_remote.ps1 via SSH. Do not run standalone without env.
set -euo pipefail

ROLE="${FUSION_MESH_ROLE:-leaf}"
HOSTNAME="${FUSION_TS_HOSTNAME:-fusion-mesh-leaf}"
REPO_URL="${FUSION_REPO_URL:-https://github.com/95guknow/fusion-hero-os.git}"
INSTALL_DIR="${FUSION_INSTALL_DIR:-$HOME/fusion-hero-core}"
WITH_HERO_DOCS="${FUSION_MESH_HERO_DOCS:-1}"
TS_KEY="${TS_AUTHKEY:-}"

echo "=== Fusion Mesh Remote Join $(date -Iseconds) ==="
echo "hostname=$HOSTNAME role=$ROLE install=$INSTALL_DIR"

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y curl git python3 python3-pip ca-certificates
fi

if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
sudo systemctl enable --now tailscaled 2>/dev/null || true

TS_ARGS=(up --reset --hostname="$HOSTNAME" --accept-routes --ssh)
if [[ -n "$TS_KEY" ]]; then
  TS_ARGS+=(--auth-key="$TS_KEY")
fi
case "$ROLE" in
  exit)
    TS_ARGS+=(--advertise-exit-node)
    ;;
  subnet)
    ROUTES="${FUSION_ADVERTISE_ROUTES:-10.0.0.0/8}"
    TS_ARGS+=(--advertise-routes="$ROUTES")
    ;;
esac

echo "-> tailscale ${TS_ARGS[*]}"
sudo tailscale "${TS_ARGS[@]}" 2>&1 || sudo tailscale up --hostname="$HOSTNAME" --accept-routes --ssh 2>&1 || true
sudo tailscale status || true
echo "-> tailscale ip: $(sudo tailscale ip -4 2>/dev/null || echo pending)"

if [[ "$WITH_HERO_DOCS" == "1" ]]; then
  if [[ ! -d "$INSTALL_DIR/.git" ]]; then
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" || git clone "$REPO_URL" "$INSTALL_DIR"
  else
    cd "$INSTALL_DIR" && git pull --ff-only origin main 2>/dev/null || true
  fi
  python3 -m pip install --user pyyaml numpy 2>/dev/null || sudo pip3 install pyyaml numpy 2>/dev/null || true
  mkdir -p "$HOME/.fusion/mesh/fractal/replicas"
  sudo mkdir -p /etc/systemd/system/fusion-hero-docs.service.d 2>/dev/null || true
  printf '%s\n' '[Service]' \
    "Environment=PYTHONPATH=$INSTALL_DIR/03_Code:$INSTALL_DIR" \
    "Environment=FUSION_BUSINESSPLAN_PATH=$INSTALL_DIR/docs/business/senfkorn_businessplan.yaml" \
    | sudo tee /etc/systemd/system/fusion-hero-docs.service.d/override.conf >/dev/null 2>&1 || true
  if [[ ! -f /etc/systemd/system/fusion-hero-docs.service ]]; then
    sudo tee /etc/systemd/system/fusion-hero-docs.service >/dev/null <<EOF
[Unit]
Description=Fusion Hero Docs (mesh leaf)
After=network.target tailscaled.service
[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/hero-docs-server.py
Restart=on-failure
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$INSTALL_DIR/03_Code:$INSTALL_DIR
[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable fusion-hero-docs
  fi
  sudo fuser -k 8088/tcp 2>/dev/null || true
  sudo systemctl restart fusion-hero-docs 2>/dev/null || true
  sleep 2
  curl -fsS http://127.0.0.1:8088/status >/dev/null && echo "-> hero-docs OK" || echo "-> hero-docs pending"
fi

echo "=== Mesh join complete ==="
echo "MAGICDNS=${HOSTNAME}.tail391adb.ts.net"
echo "VERIFY=http://${HOSTNAME}.tail391adb.ts.net:8088/mesh/fractal/status"