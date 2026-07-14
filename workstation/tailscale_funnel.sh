#!/bin/bash
# Tailscale Funnel Automation für Fusion Hero OS
# Ermöglicht sicheren öffentlichen Zugriff auf den Hero Docs Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="${FUSION_INTEGRATION_DIR:-$(cd "$SCRIPT_DIR/../src/normal_os/integration" 2>/dev/null && pwd)}"
<<<<<<< HEAD
MF_DNS="desktop-kpki9e4.tail391adb.ts.net"
=======
MF_DNS="host.example.ts.net"
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
if [ -f "$INTEGRATION_DIR/mesh_roles.py" ]; then
    MF_DNS=$(python3 -c "import sys; sys.path.insert(0,'$INTEGRATION_DIR'); from mesh_roles import get_mainframe_magicdns; print(get_mainframe_magicdns())" 2>/dev/null || echo "$MF_DNS")
fi

echo "🚀 [Fusion Hero OS] Tailscale Funnel wird konfiguriert..."

# Prüfen ob Tailscale läuft
if ! tailscale status >/dev/null 2>&1; then
    echo "❌ Tailscale läuft nicht. Bitte zuerst mit tailscale_start.sh starten."
    exit 1
fi

# Funnel für Port 8088 (Hero Docs Server) aktivieren
echo "📡 Aktiviere Funnel auf Port 8088..."

sudo tailscale funnel --bg --port 8088 on

echo ""
echo "✅ Tailscale Funnel ist jetzt aktiv!"
echo ""
echo "Dein Hero Docs Server ist jetzt öffentlich erreichbar unter:"
echo "   https://$MF_DNS"
echo ""
echo "Weitere nützliche URLs:"
echo "   MasterSeed Status:  https://$MF_DNS/status"
echo "   Tailscale Status:   https://$MF_DNS/tailscale/status"
echo ""
echo "Um Funnel zu deaktivieren:"
echo "   sudo tailscale funnel --port 8088 off"
echo ""
echo "Status prüfen mit: tailscale funnel status"