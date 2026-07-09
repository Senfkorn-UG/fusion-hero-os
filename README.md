# Tailscale Mesh Integration – Fusion Hero OS v8

**Status:** Vollständig integriert (09.07.2026)  
**Zweck:** Zero-Config Mesh-VPN + Phone-Bridge + Funnel für den gesamten Heimserver

## Was ist das?

Vollständige Tailscale-Integration als **Mesh** innerhalb von Fusion Hero OS:

- Sicherer Zugriff von überall (MagicDNS + Funnel)
- Phone-Benachrichtigungen via `pc-handy-bridge` + `phonelink-control`
- Zentrale Steuerung über ein Control Center
- Live-Status direkt im `hero-docs-server`

## Ein-Klick Mesh Setup

### Von Windows (Git Bash) aus (empfohlen)

```bash
cd tools/tailscale

# Einmalig ausführbar machen
chmod +x run_on_heimgserver.sh

# Vollständiges Mesh-Setup auf dem Heimserver triggern
./run_on_heimgserver.sh all
```

Einzelne Kommandos:
```bash
./run_on_heimgserver.sh install
./run_on_heimgserver.sh start
./run_on_heimgserver.sh funnel
./run_on_heimgserver.sh status
```

> **Hinweis:** Trage oben in `run_on_heimgserver.sh` deinen SSH-Usernamen ein (`USER="admin"` → dein tatsächlicher User).

### Direkt auf dem Linux-Heimserver

```bash
cd tools/tailscale
chmod +x tailscale_control.sh
sudo ./tailscale_control.sh all
```

## Verfügbare Kommandos

| Command     | Beschreibung                              |
|-------------|-------------------------------------------|
| `install`   | Installation + Authentifizierung          |
| `start`     | Start + Service einrichten                |
| `status`    | Aktuellen Status anzeigen                 |
| `funnel`    | Funnel für Hero Docs Server aktivieren    |
| `notify`    | Phone Notification Monitor starten        |
| `all`       | Komplettes Mesh-Setup                     |

## Erreichbare URLs (nach Funnel + MagicDNS)

- **Hero Docs Server**: `https://mainframe.tail391adb.ts.net`
- **MasterSeed Status**: `https://mainframe.tail391adb.ts.net/status`
- **Tailscale Status**: `https://mainframe.tail391adb.ts.net/tailscale/status`

## Phone-Bridge Integration

- `tailscale_phone_notify.py` sendet Connect/Disconnect Events ans Handy
- Status-Abfrage möglich über `hero-docs-server`
- Zukünftig: Direkte Steuerung vom Handy aus

## Dateien

| Datei                        | Zweck                                           |
|-----------------------------|-------------------------------------------------|
| `tailscale_control.sh`      | Zentrales Control Center (Mesh Orchestrator)    |
| `tailscale_install.sh`      | Installation + Login                            |
| `tailscale_start.sh`        | Start + Service                                 |
| `tailscale_status.py`       | Status als JSON (Bridge-fähig)                  |
| `tailscale_funnel.sh`       | Funnel-Aktivierung für öffentlichen Zugriff     |
| `tailscale_phone_notify.py` | Phone Notifications bei Status-Änderung         |
| `run_on_heimgserver.sh`     | Remote-Ausführung von Windows aus per SSH         |
| `README.md`                 | Diese Anleitung                                 |

---

**Layer 0 verankert** – Vollständig integriert in ALTE_Frau_95g Heroic Core v8 + HorkruxSelfUpdateProtocol.