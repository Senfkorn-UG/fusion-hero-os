#!/bin/bash
# run_on_heimgserver.sh
# Führt Tailscale-Kommandos remote auf dem archivierten Linux-Knoten aus (optional).
# Mainframe = Windows-Desktop (desktop-kpki9e4). Dieses Skript nur für Legacy-Linux.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="${FUSION_INTEGRATION_DIR:-$(cd "$SCRIPT_DIR/../src/normal_os/integration" 2>/dev/null && pwd)}"
SERVER="host.example.ts.net"
if [ -f "$INTEGRATION_DIR/mesh_roles.py" ]; then
    SERVER=$(python3 -c "import sys; sys.path.insert(0,'$INTEGRATION_DIR'); from mesh_roles import get_roles_registry; print(get_roles_registry()['role_assignments']['legacy']['magicdns'])" 2>/dev/null || echo "$SERVER")
fi
USER="admin"          # <-- Hier deinen SSH-User auf dem Heimserver eintragen
REMOTE_DIR="/home/workdir/artifacts/tools/tailscale"

if [ -z "$1" ]; then
    echo "Usage: $0 <command>"
    echo ""
    echo "Beispiele:"
    echo "  $0 all          → Vollständiges Mesh-Setup"
    echo "  $0 install"
    echo "  $0 start"
    echo "  $0 funnel"
    echo "  $0 status"
    echo "  $0 notify"
    exit 1
fi

COMMAND="$1"

echo "🔗 Verbinde mit $SERVER ..."

echo "→ Führe aus: ./tailscale_control.sh $COMMAND"

echo ""

ssh "$USER@$SERVER" "cd $REMOTE_DIR && chmod +x tailscale_control.sh && sudo ./tailscale_control.sh $COMMAND"

echo ""
echo "✅ Befehl '$COMMAND' auf dem Heimserver ausgeführt."