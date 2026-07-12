# -*- coding: utf-8 -*-
"""Erkenntnis-Index-Gate: haelt docs/v8/erkenntnisse_index.yaml konsistent.

Prueft maschinell (CI-Gate neben dem Proof-Registry-Gate):

  1. Schema: jeder Eintrag hat id, path, version, status, layer_mapping.
  2. status in {aktiv, superseded, archiv}; superseded/archiv brauchen
     superseded_by ODER eine supersedes_note/summary mit Verweis.
  3. Jeder referenzierte Pfad EXISTIERT im Repo.
  4. Keine doppelten IDs.
  5. layer_mapping referenziert nur Layer, die in fusion_unified.yaml existieren.
  6. resolved_conflicts: jeder Konflikt hat state == "resolved" (offene
     Konflikte lassen das Gate scheitern) und referenziert existierende Docs.

Aufruf:
    python scripts/check_erkenntnisse_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "v8" / "erkenntnisse_index.yaml"
UNIFIED = ROOT / "fusion_unified.yaml"
VALID_STATUS = {"aktiv", "superseded", "archiv"}
REQUIRED_FIELDS = ("id", "path", "version", "status", "layer_mapping")


def fail(msg: str) -> None:
    print(f"[FEHLER] {msg}")
    sys.exit(1)


def main() -> None:
    if not INDEX.exists():
        fail(f"{INDEX.relative_to(ROOT)} fehlt.")

    data = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "docs" not in data:
        fail("erkenntnisse_index.yaml: Top-Level 'docs' fehlt.")

    unified = yaml.safe_load(UNIFIED.read_text(encoding="utf-8")) or {}
    known_layers = set((unified.get("layers") or {}).keys())
    if not known_layers:
        fail("fusion_unified.yaml: keine Layer definiert.")

    docs = data["docs"]
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, doc in enumerate(docs):
        if not isinstance(doc, dict):
            errors.append(f"docs[{i}]: kein Mapping.")
            continue
        for f in REQUIRED_FIELDS:
            if f not in doc:
                errors.append(f"docs[{i}] ({doc.get('id', '?')}): Feld '{f}' fehlt.")
        did = str(doc.get("id", f"#{i}"))
        if did in seen_ids:
            errors.append(f"Doppelte ID: {did}")
        seen_ids.add(did)

        status = str(doc.get("status", ""))
        if status not in VALID_STATUS:
            errors.append(f"{did}: ungueltiger status '{status}' (erlaubt: {sorted(VALID_STATUS)})")
        if status in ("superseded", "archiv") and not (
            doc.get("superseded_by") or doc.get("supersedes_note") or doc.get("summary")
        ):
            errors.append(f"{did}: status '{status}' ohne superseded_by/Verweis.")

        rel = str(doc.get("path", ""))
        if rel and not (ROOT / rel).exists():
            errors.append(f"{did}: Datei fehlt: {rel}")

        for layer in doc.get("layer_mapping") or []:
            if layer not in known_layers:
                errors.append(f"{did}: unbekannter Layer '{layer}' (fusion_unified.yaml kennt: {sorted(known_layers)})")

    conflicts = data.get("resolved_conflicts") or []
    for c in conflicts:
        cid = str((c or {}).get("id", "?"))
        if str((c or {}).get("state")) != "resolved":
            errors.append(f"Konflikt '{cid}' ist nicht resolved — Widerspruch offen.")
        for rel in (c or {}).get("docs") or []:
            if not (ROOT / str(rel)).exists():
                errors.append(f"Konflikt '{cid}': referenziertes Doc fehlt: {rel}")

    if errors:
        print(f"[FEHLER] Erkenntnis-Index inkonsistent ({len(errors)} Probleme):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    by_status: dict[str, int] = {}
    for doc in docs:
        s = str(doc.get("status"))
        by_status[s] = by_status.get(s, 0) + 1
    print(
        f"Erkenntnis-Index: {len(docs)} Docs — "
        + ", ".join(f"{v} {k}" for k, v in sorted(by_status.items()))
        + f"; {len(conflicts)} Konflikte aufgeloest."
    )
    print("[OK] Index konsistent: alle Pfade existieren, alle Layer bekannt, keine offenen Konflikte.")


if __name__ == "__main__":
    main()
