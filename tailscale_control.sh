#!/bin/bash
# Tailscale Control Center – Fusion Hero OS Mesh Integration
# Zentrale Steuerung aller Tailscale-Komponenten

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "Tailscale Control Center – Fusion Hero OS"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  install     - Tailscale installieren + authentifizieren"
    echo "  start       - Tailscale starten + Service einrichten"
    echo "  status      - Aktuellen Status anzeigen"
    echo "  funnel      - Funnel für Hero Docs Server aktivieren"
    echo "  notify      - Phone Notification Monitor starten"
    echo "  all         - Alles nacheinander ausführen (install → start → funnel)"
    echo "  help        - Diese Hilfe anzeigen"
    echo ""
}

case "$1" in
    install)
        echo "→ Führe Installation aus..."
        sudo "$SCRIPT_DIR/tailscale_install.sh"
        ;;
    start)
        echo "→ Starte Tailscale..."
        sudo "$SCRIPT_DIR/tailscale_start.sh"
        ;;
    status)
        echo "→ Tailscale Status:"
        python3 "$SCRIPT_DIR/tailscale_status.py"
        ;;
    funnel)
        echo "→ Aktiviere Funnel..."
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        ;;
    notify)
        echo "→ Starte Phone Notification Monitor..."
        python3 "$SCRIPT_DIR/tailscale_phone_notify.py"
        ;;
    all)
        echo "🚀 Vollständige Tailscale Mesh Initialisierung..."
        sudo "$SCRIPT_DIR/tailscale_install.sh"
        sudo "$SCRIPT_DIR/tailscale_start.sh"
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        echo "✅ Mesh Integration abgeschlossen."
        ;;
    *)
        show_help
        ;;
esac