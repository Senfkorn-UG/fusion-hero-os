#!/usr/bin/env python3
"""
Tailscale / Android Phone Notification Module

Sendet Status-Updates als **Android System-Notifications** über einen
generischen Webhook (empfohlen: ntfy.sh oder self-hosted ntfy).

Integration mit:
- hero_autoupdate (1-Min-Polling, 5-Min-Erinnerung Interaktion zum Held)
- mesh_file_share
- hero-docs-server /tailscale/status

Env:
  PHONE_NOTIFY_WEBHOOK_URL  z.B. https://ntfy.sh/<topic>
  PHONE_NOTIFY_TOKEN        optional Bearer/ basictoken für private topics
  PHONE_NOTIFY_PRIORITY     default|low|high|urgent  (ntfy)
  PHONE_NOTIFY_TAGS         z.B. heroic,bell
  PHONE_NOTIFY_CLICK        optional Click-URL

Code-Honesty: Ohne PHONE_NOTIFY_WEBHOOK_URL nur Konsolen-Log, kein Fake-Erfolg.
Layer 0 kompatibel — Fusion Hero OS v10
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional


def get_tailscale_status() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return {"online": False, "error": "Tailscale nicht erreichbar"}

        data = json.loads(result.stdout)
        return {
            "online": data.get("Self", {}).get("Online", False),
            "tailscale_ip": data.get("Self", {}).get("TailscaleIPs", [""])[0],
            "backend_state": data.get("BackendState"),
            "peers": len(data.get("Peer", {})),
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


def _is_ntfy_url(url: str) -> bool:
    u = url.lower()
    return "ntfy." in u or u.rstrip("/").endswith("/ntfy") or "/ntfy/" in u


def send_phone_notification(
    message: str,
    title: str = "Tailscale",
    *,
    priority: Optional[str] = None,
    tags: Optional[str] = None,
    click: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sendet eine Benachrichtigung ans Android-Handy (System-Notification).

    Echter, generischer Webhook-Versand (ntfy.sh, Pushover-Proxy, eigener
    Endpoint), sobald PHONE_NOTIFY_WEBHOOK_URL gesetzt ist. Ohne Konfiguration
    bleibt es beim reinen Konsolen-Log — ehrlich, kein Fake-Erfolg.

    ntfy-Apps (Android/iOS) rendern das als echte System-Notification.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📱 PHONE NOTIFICATION → {title}: {message}")

    webhook_url = os.environ.get("PHONE_NOTIFY_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {
            "ok": False,
            "delivered": False,
            "reason": "PHONE_NOTIFY_WEBHOOK_URL unset",
            "logged": True,
            "channel": "console_only",
        }

    prio = (priority or os.environ.get("PHONE_NOTIFY_PRIORITY", "default") or "default").strip()
    tag_s = (tags or os.environ.get("PHONE_NOTIFY_TAGS", "") or "").strip()
    click_url = (click or os.environ.get("PHONE_NOTIFY_CLICK", "") or "").strip()
    token = os.environ.get("PHONE_NOTIFY_TOKEN", "").strip()

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Title": title,
        "X-Title": title,
        "Priority": prio,
        "X-Priority": prio,
    }
    if tag_s:
        headers["Tags"] = tag_s
        headers["X-Tags"] = tag_s
    if click_url:
        headers["Click"] = click_url
        headers["X-Click"] = click_url
    if token:
        # ntfy access tokens: "Bearer <token>" or raw token depending on setup
        if token.lower().startswith("bearer "):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"

    body: bytes
    if _is_ntfy_url(webhook_url):
        # ntfy accepts plain body as message; JSON also works for some servers
        headers["Content-Type"] = "text/plain; charset=utf-8"
        body = message.encode("utf-8")
    else:
        payload = {
            "title": title,
            "message": message,
            "priority": prio,
            "tags": tag_s,
            "click": click_url,
            "android": True,
            "system_notification": True,
        }
        body = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            webhook_url,
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", 200) or 200
            if status >= 300:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Phone-Notify Webhook Status {status}"
                )
                return {
                    "ok": False,
                    "delivered": False,
                    "status": status,
                    "channel": "webhook",
                }
            return {
                "ok": True,
                "delivered": True,
                "status": status,
                "channel": "android_system_notification",
                "transport": "ntfy" if _is_ntfy_url(webhook_url) else "webhook",
            }
    except Exception as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Phone-Notify Webhook fehlgeschlagen: {e}"
        )
        return {
            "ok": False,
            "delivered": False,
            "error": str(e)[:200],
            "channel": "webhook",
        }


def monitor_tailscale(interval_seconds: int = 30) -> None:
    """Überwacht Tailscale und sendet Notification bei Status-Änderung."""
    last_online = None

    print("🔄 Tailscale Phone Monitor gestartet...")
    print(f"   Prüfintervall: {interval_seconds}s")
    print("   Drücke STRG+C zum Beenden.\n")

    while True:
        status = get_tailscale_status()
        current_online = status.get("online", False)

        if last_online is None:
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online",
                )
            else:
                send_phone_notification("Nicht verbunden", "Tailscale Offline")
        elif current_online != last_online:
            if current_online:
                send_phone_notification(
                    f"Verbunden • IP: {status.get('tailscale_ip', 'unbekannt')}",
                    "Tailscale Online",
                )
            else:
                send_phone_notification("Verbindung getrennt", "Tailscale Offline")

        last_online = current_online
        time.sleep(interval_seconds)


if __name__ == "__main__":
    monitor_tailscale(interval_seconds=30)
