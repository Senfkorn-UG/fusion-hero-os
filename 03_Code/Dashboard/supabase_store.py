# -*- coding: utf-8 -*-
"""Persistenz-Layer: Fusion Hero OS → Supabase (swmmoxhdzarmoupyssqe)."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from supabase_client import get_client, is_configured

# --- Tables-Ready-Gate -------------------------------------------------------
# Ohne angewendetes Schema (supabase/schema.sql) existieren die Ziel-Tabellen
# nicht -> jeder Insert wäre ein fehlschlagender Netzwerk-Aufruf. Da emit() bei
# jedem Event einen save_event() feuert, würde das Supabase dauerhaft mit
# aussichtslosen Requests fluten. Deshalb wird die Existenz EINMAL geprüft und
# gecacht; solange die Tabellen fehlen, werden Inserts lokal übersprungen.
# check_tables() aktualisiert den Cache — nach dem Anwenden des Schemas genügt
# ein Aufruf (z.B. GET /api/supabase/tables), um die Persistenz scharf zu schalten.
_TABLES_READY: Optional[bool] = None  # None = noch nicht geprüft


def _ensure_ready() -> bool:
    """Einmalige, gecachte Prüfung, ob die Ziel-Tabellen existieren."""
    global _TABLES_READY
    if _TABLES_READY is None:
        if not is_configured() or get_client() is None:
            _TABLES_READY = False
        else:
            _TABLES_READY = bool(check_tables().get("ok"))  # setzt Cache selbst
    return bool(_TABLES_READY)


def refresh_ready() -> bool:
    """Cache invalidieren und neu prüfen (z.B. nachdem das Schema angewendet wurde)."""
    global _TABLES_READY
    _TABLES_READY = None
    return _ensure_ready()


def _insert(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return {"ok": False, "error": "supabase client unavailable"}
    if not _ensure_ready():
        # Schema nicht angewendet -> nicht sinnlos gegen fehlende Tabellen schreiben
        return {"ok": False, "skipped": True, "table": table,
                "reason": "tables not ready (schema not applied)"}
    try:
        resp = client.table(table).insert(row).execute()
        return {"ok": True, "table": table, "count": len(resp.data or [])}
    except Exception as exc:
        return {"ok": False, "table": table, "error": str(exc)}


def save_event(event: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "event_id": event.get("id"),
        "event_type": event.get("type", "info"),
        "message": event.get("msg", ""),
        "severity": event.get("severity"),
        "layer": event.get("layer"),
        "ts": event.get("ts", time.time()),
        "payload": {k: v for k, v in event.items() if k not in ("id", "type", "msg", "severity", "layer", "ts")},
    }
    return _insert("fusion_events", row)


def save_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "cpu_pct": metrics.get("cpu"),
        "ram_pct": metrics.get("ram"),
        "events_count": metrics.get("events"),
        "subs_count": metrics.get("subs"),
        "ops_per_sec": metrics.get("ops_per_sec"),
        "ts": metrics.get("ts", time.time()),
        "payload": metrics,
    }
    return _insert("fusion_metrics", row)


def save_job(job: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "job_id": job.get("id"),
        "query": job.get("query", ""),
        "category": job.get("category"),
        "dom": job.get("dom"),
        "status": job.get("status", "received"),
        "ts": time.time(),
        "payload": job,
    }
    return _insert("fusion_jobs", row)


def save_llama_config(config: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "algorithm": config.get("algorithm", "heroic_qubo_annealing_v1"),
        "model_path": config.get("model_path"),
        "generation": config.get("generation", {}),
        "metrics": config.get("metrics", {}),
        "ts": time.time(),
    }
    return _insert("heroic_llama_configs", row)


def list_recent_events(limit: int = 20) -> List[Dict[str, Any]]:
    client = get_client()
    if not client:
        return []
    try:
        resp = (
            client.table("fusion_events")
            .select("*")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


TARGET_TABLES = [
    "fusion_events",
    "fusion_metrics",
    "fusion_jobs",
    "heroic_llama_configs",
]


def store_status() -> Dict[str, Any]:
    """Konfigurations-Status (KEIN Netzwerk). tables = Ziel-Tabellen, NICHT als
    'existiert' zu verstehen — dafür check_tables() aufrufen."""
    return {
        "configured": is_configured(),
        "target_tables": TARGET_TABLES,
        "schema_sql": "supabase/schema.sql",
        "note": "Ziel-Tabellen; Existenz per check_tables() prüfen",
    }


def check_tables() -> Dict[str, Any]:
    """Read-only-Prüfung, welche Ziel-Tabellen im Projekt existieren.

    select().limit(1) pro Tabelle. PostgREST-Fehler PGRST205 => Tabelle fehlt
    (Schema noch nicht via supabase/schema.sql angewendet). Ein leeres Ergebnis
    (RLS ohne SELECT-Policy) zählt trotzdem als 'exists', da die Anfrage 200 liefert.
    """
    client = get_client()
    if not client:
        return {
            "ok": False,
            "error": "supabase client unavailable",
            "tables": {t: None for t in TARGET_TABLES},
        }
    tables: Dict[str, str] = {}
    for t in TARGET_TABLES:
        try:
            client.table(t).select("*").limit(1).execute()
            tables[t] = "exists"
        except Exception as exc:
            tables[t] = "missing" if "PGRST205" in str(exc) else f"error: {str(exc)[:120]}"
    all_exist = all(v == "exists" for v in tables.values())
    # Gate-Cache aktualisieren: nach Anwenden des Schemas schaltet dieser Aufruf
    # (z.B. via GET /api/supabase/tables) die Persistenz ohne Neustart scharf.
    global _TABLES_READY
    _TABLES_READY = all_exist
    return {
        "ok": all_exist,
        "tables": tables,
        "schema_sql": None if all_exist else "supabase/schema.sql",
        "hint": None if all_exist else "Schema anwenden: SQL Editor -> supabase/schema.sql ausführen",
    }


def roundtrip_test() -> Dict[str, Any]:
    """Schreib-Lese-Test: fügt ein markiertes Test-Event ein und liest es zurück.

    ACHTUNG: schreibt eine Zeile nach fusion_events — nur bewusst aufrufen.
    """
    marker = f"roundtrip-{int(time.time())}"
    ins = save_event({"id": marker, "type": "selftest", "msg": marker, "severity": "low"})
    if not ins.get("ok"):
        return {"ok": False, "stage": "insert", "marker": marker, **ins}
    rows = list_recent_events(10)
    found = any(r.get("event_id") == marker for r in rows)
    return {"ok": found, "stage": "read", "marker": marker, "recent_count": len(rows)}


if __name__ == "__main__":
    import json
    import sys

    print("[supabase_store] configured:", is_configured())
    tbl = check_tables()
    print("[supabase_store] check_tables:")
    print(json.dumps(tbl, indent=2, ensure_ascii=False))

    if "--write" in sys.argv:
        if tbl.get("ok"):
            print("[supabase_store] roundtrip_test (schreibt ein Test-Event):")
            print(json.dumps(roundtrip_test(), indent=2, ensure_ascii=False))
        else:
            print("[supabase_store] roundtrip übersprungen — Tabellen fehlen (Schema anwenden).")