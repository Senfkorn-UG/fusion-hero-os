#!/bin/bash
# Tailscale Funnel Automation für Fusion Hero OS
# Ermöglicht sicheren öffentlichen Zugriff auf den Hero Docs Server

set -e

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
<<<<<<< HEAD
echo "   https://mainframe.tail391adb.ts.net"
echo ""
echo "Weitere nützliche URLs:"
echo "   MasterSeed Status:  https://mainframe.tail391adb.ts.net/status"
echo "   Tailscale Status:   https://mainframe.tail391adb.ts.net/tailscale/status"
=======
echo "   https://host.example.ts.net"
echo ""
echo "Weitere nützliche URLs:"
echo "   MasterSeed Status:  https://host.example.ts.net/status"
echo "   Tailscale Status:   https://host.example.ts.net/tailscale/status"
>>>>>>> 404701973eb09fd68448759c001b712e6fb2ef09
echo ""
echo "Um Funnel zu deaktivieren:"
echo "   sudo tailscale funnel --port 8088 off"
echo ""
echo "Status prüfen mit: tailscale funnel status"