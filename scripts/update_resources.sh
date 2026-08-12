#!/usr/bin/env bash
set -e

RESOURCE_FILE="resources.md"
VERSION_FILE="VERSION"

# Das Doc-Versions-Gate (scripts/check_doc_versions.py) verlangt einen
# sichtbaren Stand-Marker in den ersten 12 Zeilen jedes Top-Level-Dokuments.
# Der Generator schreibt ihn deshalb SELBST — frueher stand er nicht im
# Heredoc, wurde von Hand nachgetragen (a672564) und vom naechsten
# Auto-Update-Lauf (e91b9ad) wieder ueberschrieben. Ein Generator, der die
# Datei vollstaendig neu schreibt, muss alles mitschreiben, was das Gate
# verlangt; sonst ist jeder manuelle Fix nur bis zum naechsten Lauf gueltig.
PLATFORM_VERSION="$(tr -d ' \t\r\n' < "$VERSION_FILE")"

# Das Stand-Datum stammt aus dem letzten VERSION-Commit, NICHT aus `date`:
# update-resources.yml faehrt diesen Generator taeglich um 03:00 UTC mit
# Auto-Commit auf main. Mit `date` aendert sich die Kopfzeile jede Nacht,
# der Auto-Commit landet auf main und triggert die komplette CI — jede
# Nacht ein Commit und ein Lauf, ohne dass sich inhaltlich etwas geaendert
# hat. Gebunden an VERSION bewegt sich die Zeile nur bei echten Releases,
# und der Generator wird idempotent. `date` bleibt Fallback ohne Git-Kontext.
TODAY="$(git log -1 --format=%cs -- "$VERSION_FILE" 2>/dev/null || true)"
[ -n "$TODAY" ] || TODAY="$(date -u +%Y-%m-%d)"

# Kopf mit Expansion, Rumpf ohne — so kann kein '$' im Fliesstext
# versehentlich expandiert werden.
{
  echo "# AscensionOS / Fusion Hero OS Ressourcen"
  echo
  echo "> **Stand:** v${PLATFORM_VERSION} · ${TODAY}"
  echo
} > "$RESOURCE_FILE"

cat >> "$RESOURCE_FILE" << 'EOR'
Diese Seite wird automatisch aus festen Quellen und Repo-Metadaten generiert.

## Eigene Repositories und Organisationen

- Fusion Hero OS Repo: https://github.com/95guknow/fusion-hero-os
- Senfkorn-Organisation: https://github.com/Senfkorn-UG

## Mesh, Monitoring und Archiv-Tools (Externe)

- Mesh-Monitoring / Dashboards: Grafana, Prometheus, Meshtastic-Integrationen.
- Web-Archivierung: ArchiveBox.
- Architektur-Dokumentation: Beispiele und Awesome-Architecture-Listen.

## XR / WebXR / VR/AR Frameworks

- WebXR Mesh Detection / Scene Understanding.
- Frameworks: A-Frame, Three.js, Babylon.js, 8th Wall.

## Dokumentation / Templates

- Good Docs / Architektur-Templates.
- Richtlinien für technische und semantische Kanon-Dokumente.

EOR
