#!/usr/bin/env python3
"""
Tailscale Phone Notification Module
Sendet Status-Updates via phonelink-control an dein Handy

Integration mit:
- pc-handy-bridge v8.1
- phonelink-control v8.2
- hero-docs-server /tailscale/status

Layer 0 kompatibel — Fusion Hero OS v8
"""

import subprocess
import json
import time
import os
import urllib.request
from datetime import datetime

def get_tailscale_status():
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8
        )
        if result.returncode != 0:
            return {"online": False, "error": "Tailscale nicht erreichbar"}

        data = json.loads(result.stdout)
        return {
            "online": data.get("Self", {}).get("Online", False),
            "tailscale_ip": data.get("Self", {}).get("TailscaleIPs", [""])[0],
            "backend_state": data.get("BackendState"),
            "peers": len(data.get("Peer", {}))
        }
    except Exception as e:
        return {"online": False, "error": str(e)}

def send_phone_notification(message: str, title: str = "Tailscale"):
    """
    Sendet eine Benachrichtigung ans Handy.

    Echter, generischer Webhook-Versand (z. B. ntfy.sh, Pushover-Proxy, eigener
    Endpoint), sobald PHONE_NOTIFY_WEBHOOK_URL gesetzt ist. Ohne Konfiguration
    bleibt es beim reinen Konsolen-Log - ehrlich, kein Fake-Erfolg (siehe
    docs/01_vision/V8_STATUS_REPORT.md, Code-Honesty-Konvention). Ein
    proprietäres 'phonelink-control' Paket existiert nicht; dieser generische
    Webhook-Pfad ist der reale Ersatz dafür.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📱 PHONE NOTIFICATION → {title}: {message}")

    webhook_url = os.environ.get("PHONE_NOTIFY_WEBHOOK_URL", "")
    if not webhook_url:
        return  # Kein echter Endpunkt konfiguriert - kein Fake-Versand.

    try:
        payload = json.dumps({"title": title, "message": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "Title": title},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status >= 300:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Phone-Notify Webhook antwortete mit Status {resp.status}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Phone-Notify Webhook fehlgeschlagen: {e}")

def monitor_tailscale(interval_seconds: int = 30):
    """Überwacht Tailscale und sendet Notification bei Status-Änderung"""
    last_online = None

    print("🔄 Tailscale Phone Monitor gestartet...")
    print(f"   Prüfintervall: {interval_seconds}s")
    print("   Drücke STRG+C zum Beenden.\n")

    while True:
        status = get_tailscale_status()
        current_online = status.get("online", False)

        if last_online is None:
            # Erster Durchlauf
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online"
                )
            else:
                send_phone_notification("Nicht verbunden", "Tailscale Offline")
        elif current_online != last_online:
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online"
                )
            else:
                send_phone_notification("Verbindung getrennt", "Tailscale Offline")

        last_online = current_online
        time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_tailscale(interval_seconds=30)