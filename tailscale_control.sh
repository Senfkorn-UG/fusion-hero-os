#!/bin/bash
# Tailscale Control Center – Fusion Hero OS Mesh Integration
# Zentrale Steuerung aller Tailscale-Komponenten
# Prinzip: Jeder Konnektor = eigenes Mesh-Segment (siehe mesh_connectors.yaml)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "Tailscale Control Center – Fusion Hero OS"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  install          - Tailscale installieren + authentifizieren"
    echo "  start            - Tailscale starten + Service einrichten"
    echo "  status           - Aktuellen Status anzeigen"
    echo "  mesh             - Gesamtes Mesh (alle Konnektor-Segmente) anzeigen"
    echo "  mesh-connector   - Einzelnes Konnektor-Segment prüfen (z.B. github)"
    echo "  fusion           - Verknüpfter Gesamtstatus (Mesh + LLM + Tailscale)"
    echo "  fusion-graph     - Integrationsgraph anzeigen"
    echo "  llm              - Alle LLM-Frameworks anzeigen"
    echo "  ssh              - Tailscale SSH auf diesem Node aktivieren (tailscale set --ssh)"
    echo "  hyper4d          - Hyper4D-Node registrieren + bifurkal syncen (Layer-ω)"
    echo "  hyper4d-status   - Hyper4D-Status (/mesh/hyper4d/status Payload)"
    echo "  funnel           - Funnel für Hero Docs Server aktivieren"
    echo "  notify           - Phone Notification Monitor starten"
    echo "  fractal-save     - Mainframe fractal auf Mesh speichern"
    echo "  fractal-status   - Fractal-Manifest + Exit-Node-Status"
    echo "  exit-apply       - Virtuelles Exit-Profil anwenden (z.B. cloud-eu)"
    echo "  mainframe-mesh   - Vollständiges Mainframe-Mesh-Setup (save + optional exit)"
    echo "  cloud-sync       - Fractal → Supabase + Google Drive + Google GCE"
    echo "  files-sync       - Mesh-Dateimanifest für Handy aktualisieren"
    echo "  all              - Alles nacheinander ausführen (install → start → funnel)"
    echo "  help             - Diese Hilfe anzeigen"
    echo ""
    echo "Mesh-Prinzip: Jeder Konnektor ist ein eigenständiges Teil des Mesh."
    echo "Registry: mesh_connectors.yaml"
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
    mesh)
        echo "→ Mesh Status (alle Konnektor-Segmente):"
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py"
        ;;
    mesh-connector)
        if [ -z "$2" ]; then
            echo "Usage: $0 mesh-connector <connector_id>"
            echo "Beispiel: $0 mesh-connector github"
            exit 1
        fi
        echo "→ Mesh-Segment: $2"
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py" "$2"
        ;;
    fusion)
        echo "→ Unified Integration Status (alles verknüpft):"
        python3 "$SCRIPT_DIR/fusion_integration_hub.py" status
        ;;
    fusion-graph)
        echo "→ Integrationsgraph:"
        python3 "$SCRIPT_DIR/fusion_integration_hub.py" graph
        ;;
    llm)
        echo "→ LLM Framework Status:"
        python3 "$SCRIPT_DIR/03_Code/llm_status.py"
        ;;
    ssh)
        echo "→ Aktiviere Tailscale SSH auf diesem Node..."
        sudo tailscale set --ssh
        echo "✅ Tailscale SSH aktiv (Zugriff gemäß Tailnet-ACLs)."
        ;;
    hyper4d)
        echo "→ Hyper4D-Node registrieren + bifurkale Synchronisation..."
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py" hyper4d-register
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py" hyper4d-sync
        ;;
    hyper4d-status)
        python3 "$SCRIPT_DIR/tailscale_mesh_registry.py" hyper4d-status
        ;;
    funnel)
        echo "→ Aktiviere Funnel..."
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        ;;
    notify)
        echo "→ Starte Phone Notification Monitor..."
        python3 "$SCRIPT_DIR/tailscale_phone_notify.py"
        ;;
    fractal-save)
        echo "→ Speichere Mainframe fractal auf Mesh..."
        python3 "$SCRIPT_DIR/fractal_mainframe_mesh.py" save "$@"
        ;;
    fractal-status)
        echo "→ Fractal + Virtual Exit Status:"
        python3 "$SCRIPT_DIR/fractal_mainframe_mesh.py" status
        ;;
    exit-apply)
        PROFILE="${2:-direct}"
        echo "→ Wende virtuelles Exit-Profil an: $PROFILE"
        python3 "$SCRIPT_DIR/fractal_mainframe_mesh.py" apply-exit "$PROFILE" "${@:3}"
        ;;
    mainframe-mesh)
        EXIT_PROFILE="${2:-direct}"
        echo "→ Mainframe Mesh Setup (fractal save, exit=$EXIT_PROFILE)..."
        python3 "$SCRIPT_DIR/fractal_mainframe_mesh.py" setup --exit "$EXIT_PROFILE" "${@:3}"
        ;;
    cloud-sync)
        echo "→ Cloud sync (Supabase + Google Drive + Google server)..."
        python3 "$SCRIPT_DIR/mesh_cloud_backends.py" sync
        ;;
    files-sync)
        echo "→ Mesh file mirror sync (phone portal)..."
        python3 "$SCRIPT_DIR/mesh_file_share.py" sync
        ;;
    all)
        echo "🚀 Vollständige Tailscale Mesh Initialisierung..."
        sudo "$SCRIPT_DIR/tailscale_install.sh"
        sudo "$SCRIPT_DIR/tailscale_start.sh"
        sudo "$SCRIPT_DIR/tailscale_funnel.sh"
        echo "✅ Mesh Integration abgeschlossen."
        echo "→ Konnektor-Segmente prüfen: $0 mesh"
        ;;
    *)
        show_help
        ;;
esac
