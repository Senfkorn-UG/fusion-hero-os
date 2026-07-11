#!/usr/bin/env bash
# AudioRelay Virtual-Mic fuer Linux-Nodes (PulseAudio) — v1.0 · 2026-07-11
#
# Setzt die offizielle AudioRelay-Anleitung um:
# https://audiorelay.net/docs/linux/use-your-phone-as-a-mic-for-a-linux-pc
#
# Erzeugt zwei virtuelle PulseAudio-Geraete:
#   Virtual-Mic-Sink : Ziel, auf das die AudioRelay-Desktop-App den
#                      Handy-Mikrofon-Stream abspielt (Player-Tab)
#   Virtual-Mic      : Quelle, die Kommunikations-Apps (Discord, Zoom, ...)
#                      als Mikrofon auswaehlen
#
# Nutzung auf dem Linux-Node (z.B. mainframe-Heimserver im Tailnet):
#   ./audiorelay_virtual_mic_linux.sh            # temporaer (bis Reboot/pulseaudio -k)
#   ./audiorelay_virtual_mic_linux.sh --undo     # temporaere Module entladen
#   ./audiorelay_virtual_mic_linux.sh --permanent# in /etc/pulse/default.pa eintragen (sudo)
#   ./audiorelay_virtual_mic_linux.sh --status   # Geraete anzeigen
#
# Danach in der AudioRelay-Desktop-App: Player-Tab -> Audiogeraet
# 'Virtual-Mic-Sink' -> Handy verbinden (im Tailnet: 'Connect manually'
# mit der Tailscale-IP des Handys, kein LAN-Broadcast noetig).
# Handy-App: Server-Tab -> Mikrofon-Quelle aktivieren.

set -euo pipefail

SINK_LINE="load-module module-null-sink sink_name=Virtual-Mic-Sink sink_properties=device.description=Virtual-Mic-Sink"
SOURCE_LINE="load-module module-remap-source master=Virtual-Mic-Sink.monitor source_name=Virtual-Mic source_properties=device.description=Virtual-Mic"
PULSE_CONF="/etc/pulse/default.pa"

require_pactl() {
  if ! command -v pactl >/dev/null 2>&1; then
    echo "[FEHLER] pactl nicht gefunden — PulseAudio(-Kompatibilitaet) noetig." >&2
    echo "         PipeWire-Systeme: 'pipewire-pulse' installieren (stellt pactl bereit)." >&2
    exit 1
  fi
}

case "${1:-}" in
  --permanent)
    require_pactl
    if [ ! -w "$PULSE_CONF" ]; then
      echo "[FEHLER] $PULSE_CONF nicht schreibbar — mit sudo ausfuehren." >&2
      exit 1
    fi
    if grep -q "Virtual-Mic-Sink" "$PULSE_CONF"; then
      echo "[OK] Eintraege existieren bereits in $PULSE_CONF"
    else
      printf '\n# AudioRelay Virtual-Mic (tools/audiorelay_virtual_mic_linux.sh)\n%s\n%s\n' \
        "$SINK_LINE" "$SOURCE_LINE" >> "$PULSE_CONF"
      echo "[OK] Eintraege ergaenzt. Neu laden mit: pulseaudio -k"
    fi
    ;;
  --undo)
    require_pactl
    for mod in $(pactl list short modules | awk '/Virtual-Mic/ {print $1}'); do
      pactl unload-module "$mod" && echo "[OK] Modul $mod entladen"
    done
    ;;
  --status)
    require_pactl
    echo "--- Sinks ---";   pactl list short sinks   | grep -i "virtual-mic" || echo "kein Virtual-Mic-Sink"
    echo "--- Sources ---"; pactl list short sources | grep -i "virtual-mic" || echo "keine Virtual-Mic-Quelle"
    ;;
  "")
    require_pactl
    pactl load-module ${SINK_LINE#load-module } >/dev/null && echo "[OK] Virtual-Mic-Sink geladen"
    pactl load-module ${SOURCE_LINE#load-module } >/dev/null && echo "[OK] Virtual-Mic geladen"
    echo "[Hinweis] Temporaer bis Reboot; dauerhaft: $0 --permanent (sudo)"
    ;;
  *)
    echo "Nutzung: $0 [--permanent|--undo|--status]" >&2
    exit 2
    ;;
esac
