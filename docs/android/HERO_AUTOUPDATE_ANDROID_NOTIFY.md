# Hero Autoupdate — Android System-Notifications

**Stand:** v10.0.0  
**Defaults:** Poll **60 s** (1 Min) · Erinnerung nach **300 s** (5 Min) ohne Interaktion zum Held  
**Kanal:** Android **System-Benachrichtigung** via [ntfy](https://ntfy.sh) (oder kompatibler Webhook)

## Verhalten

| Ereignis | Intervall / Bedingung | Android-Notify |
|----------|----------------------|----------------|
| Logisches Polling | alle **1 Min** | still (nur bei Änderung) |
| Health-Wechsel | bei Poll | ja (wenn `notify_on_health_change`) |
| Git-HEAD-Wechsel | bei Poll | ja (wenn `notify_on_update`) |
| Idle-Erinnerung | **5 Min** ohne Interaktion zum Held | ja (Titel: „Held — Interaktion fällig“) |
| Startup | einmal beim Daemon-Start | ja (optional) |

**Interaktion zum Held** setzt den Idle-Timer zurück bei:

- `POST /api/hero-autoupdate/touch`
- `POST /api/input`
- `POST /api/grok/chat`

## Android einrichten (System-Notifications)

1. **ntfy** aus dem Play Store installieren (offizielle App).
2. In der App ein **privates Topic** abonnieren, z. B. `fusion-held-<langes-geheimnis>`.
3. Auf dem Mainframe (`.env`, nicht committen):

```env
FUSION_HERO_AUTOUPDATE=1
FUSION_HERO_POLL_INTERVAL_SEC=60
FUSION_HERO_REMINDER_AFTER_SEC=300
PHONE_NOTIFY_WEBHOOK_URL=https://ntfy.sh/fusion-held-DEIN_GEHEIMNIS
PHONE_NOTIFY_PRIORITY=high
PHONE_NOTIFY_TAGS=heroic,bell
```

4. Dashboard neu starten (`start_all.ps1` oder Backend-Restart).
5. Test:

```powershell
# Status
Invoke-RestMethod http://127.0.0.1:8000/api/hero-autoupdate/status

# Manuelle Erinnerung
Invoke-RestMethod -Method POST http://127.0.0.1:8000/api/hero-autoupdate/tick `
  -ContentType application/json -Body '{"force_reminder":true}'

# Interaktion markieren
Invoke-RestMethod -Method POST http://127.0.0.1:8000/api/hero-autoupdate/touch `
  -ContentType application/json -Body '{"source":"manual"}'
```

Ohne `PHONE_NOTIFY_WEBHOOK_URL` läuft das Polling weiter, aber es gibt **nur Konsolen-Log** (Code-Honesty, kein Fake-Erfolg).

## API

| Methode | Pfad | Zweck |
|---------|------|--------|
| GET | `/api/hero-autoupdate/status` | Idle, Zähler, Config |
| GET | `/api/hero-autoupdate/config` | Defaults 60/300 + Android-Kanal |
| POST | `/api/hero-autoupdate/touch` | Interaktion zum Held |
| POST | `/api/hero-autoupdate/tick` | Poll jetzt (`force_reminder`, `do_fetch`) |

## Dateien

- `hero_autoupdate.yaml` — Defaults
- `fusion_hero_os/core/hero_autoupdate.py` — Service
- `fusion_hero_os/modules/hero_autoupdate.py` — Dispatcher-Modul
- `tailscale_phone_notify.py` — Android-Webhook (ntfy)
- `03_Code/Dashboard/mainframe_background.py` — 1-Min-Loop im Dashboard-Prozess

## Alternativen

- **Self-hosted ntfy** hinter Tailscale (gleiche Headers: Title, Priority, Tags, Click).
- **Tasker/MacroDroid** auf HTTP-Trigger vom Mainframe (nicht im Default-Pfad).
- Microsoft Phone Link ist im Repo **read-only** für SMS — kein Outbound-System-Notify; ntfy ist der ehrliche Android-Kanal.
