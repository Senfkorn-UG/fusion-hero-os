# Tailscale Integration – Fusion Hero OS v8

**Status:** Neu implementiert (09.07.2026)  
**Zweck:** Zero-Config VPN für sicheren Zugriff auf den Heimserver von überall (inkl. Phone-Bridge-Steuerung)

## Was ist das?

Tailscale ist ein modernes WireGuard-basiertes Mesh-VPN. Es erlaubt dir:
- Deinen Heimserver sicher von unterwegs zu erreichen (ohne Port-Forwarding)
- Einfache Authentifizierung über GitHub / Google / Microsoft
- Nahtlose Integration mit `pc-handy-bridge` + `phonelink-control`

## Schnellstart (auf dem Heimserver)

```bash
# 1. Installation + Setup
cd tools/tailscale
chmod +x tailscale_install.sh
./tailscale_install.sh

# 2. Tailscale starten + als Service einrichten
./tailscale_start.sh
```

Danach kannst du im Tailscale Admin Console (https://login.tailscale.com) deinen Server sehen und freigeben.

## Phone-Bridge Integration (empfohlen)

Die Integration ist so designed, dass du Tailscale-Status und Start/Stop **vom Handy aus** über die Bridge steuern kannst.

Zukünftige Erweiterung (bereits vorbereitet):
- `tailscale_phone_notify.py` → sendet Status-Updates via `phonelink-control` an dein Handy
- Status-Abfrage über `hero-docs-server` Endpoint möglich

## Dateien

| Datei                        | Zweck                                      |
|-----------------------------|--------------------------------------------|
| `tailscale_install.sh`      | Ein-Klick Installation + Auth              |
| `tailscale_start.sh`        | Startet Tailscale + richtet Service ein    |
| `tailscale_status.py`       | Status-Abfrage (Python, bridge-fähig)      |
| `README.md`                 | Diese Anleitung                            |

## Nächste Schritte (geplant)

- [ ] Phone-Notification beim Connect/Disconnect
- [ ] Automatischer Start beim Mainframe-Boot
- [ ] `/tailscale/status` Endpoint im `hero-docs-server`
- [ ] One-Command "Tailscale aktivieren vom Handy aus"

---

**Layer 0 verankert** – passt zum Fusion Hero OS v8 Standard.  
Möchtest du die Phone-Notification + Status-Endpoint jetzt auch noch direkt implementieren?