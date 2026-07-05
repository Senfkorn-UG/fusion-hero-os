# -*- coding: utf-8 -*-
"""Watch Together — Supabase als autoritativer Sync-Server.

Alle Geräte (PC, Redmi, zweiter PC) lesen/schreiben den Raumzustand über
Supabase. Lokaler Speicher ist nur Cache; Konflikte gewinnt der Server-Stand.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from watch_party import WatchPartyManager, WatchRoom


def server_sync_enabled() -> bool:
    if os.getenv("FUSION_WATCH_SERVER_SYNC", "1") != "1":
        return False
    try:
        import supabase_store as store

        return store.cloud_sync_enabled()
    except Exception:
        return False


def server_poll_interval_sec() -> float:
    try:
        return float(os.getenv("FUSION_WATCH_SERVER_POLL_SEC", "2"))
    except ValueError:
        return 2.0


def merge_row_into_room(room: "WatchRoom", row: Dict[str, Any]) -> bool:
    """Überschreibt lokalen Cache wenn Supabase neuer ist."""
    server_ts = float(row.get("updated_at") or 0)
    if server_ts <= room.updated_at + 0.001:
        return False
    room.video_id = row.get("video_id") or ""
    room.position = float(row.get("position") or 0)
    room.playing = bool(row.get("playing"))
    room.updated_at = server_ts
    room.title = row.get("title") or ""
    if row.get("created_at"):
        room.created_at = float(row.get("created_at"))
    return True


def refresh_room_from_server(mgr: "WatchPartyManager", room_id: str) -> Optional["WatchRoom"]:
    if not server_sync_enabled():
        return mgr.get_room(room_id)
    try:
        import supabase_store as store

        row = store.load_watch_room(room_id)
    except Exception:
        return mgr.get_room(room_id)
    if not row:
        return mgr.get_room(room_id)
    room = mgr.ensure_room(room_id)
    merge_row_into_room(room, row)
    return room


def push_room_to_server(room: "WatchRoom") -> Dict[str, Any]:
    try:
        import supabase_store as store

        return store.save_watch_room(
            {
                "room_id": room.room_id,
                "video_id": room.video_id,
                "position": room.position,
                "playing": room.playing,
                "title": room.title,
                "updated_at": room.updated_at,
                "created_at": room.created_at,
                "payload": {"sync_authority": "server", "pushed_at": time.time()},
            }
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def finalize_command(mgr: "WatchPartyManager", room: "WatchRoom") -> "WatchRoom":
    """Nach lokaler Berechnung: Supabase schreiben und Server-Stand zurücklesen."""
    if server_sync_enabled():
        push_room_to_server(room)
        refreshed = refresh_room_from_server(mgr, room.room_id)
        return refreshed or room
    mgr._persist_room(room)
    return room


def get_authoritative_state(room_id: str, mgr: "WatchPartyManager") -> Dict[str, Any]:
    if server_sync_enabled():
        refresh_room_from_server(mgr, room_id)
    room = mgr.get_room(room_id)
    if not room:
        return {"ok": False, "error": "room_not_found"}
    state = room.to_state()
    state["updated_at"] = room.updated_at
    state["sync_authority"] = "server" if server_sync_enabled() else "local"
    return {
        "ok": True,
        "state": state,
        "sync_source": "supabase" if server_sync_enabled() else "memory",
        "server_sync": server_sync_enabled(),
    }


def active_room_ids(mgr: "WatchPartyManager") -> list[str]:
    ids = set(mgr._rooms.keys())
    for rid, subs in mgr._subscribers.items():
        if subs:
            ids.add(rid)
    return list(ids)