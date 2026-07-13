# -*- coding: utf-8 -*-
"""
AscensionOS v9.5 - PsycholyseProtocolLogger

Schliesst Punkt 1 der "Next Evolution Steps" (ASCENSION_EXPANSION_v8.md):
allgemeiner Session-Logger mit "honest status tags" - im Unterschied zu
legacy_sources/AscensionOS/psycholyse_engine.py, das genau EIN historisches
Beispiel (Easter 2026) fest codiert. Dieses Modul loggt beliebige Sessions
und verbindet sie optional mit PersistentSisyphosCycle - der von
psycholyse_engine.integrate_with_eudaimonismus() vorausgesagte, bislang
fehlende Integrationspunkt ("feeds directly into SisyphosCycle").

Ehrlicher Status: Reine Protokollierung + Statusverwaltung. Keine
klinische/therapeutische Bewertung, keine Wirksamkeitsaussage - der
Pflicht-`status`-Tag markiert ausdruecklich, dass Eintraege per Default
Selbstauskunft sind, sofern nicht anders vermerkt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None


VALID_STATUS_TAGS = ("self_reported", "observed", "unverified")


@dataclass
class PsycholyseLogEntry:
    session_id: int
    timestamp: str
    protocol_type: str
    status: str  # siehe VALID_STATUS_TAGS - Pflichtfeld, kein Default auf "verifiziert"
    pre_state: Dict[str, Any] = field(default_factory=dict)
    post_state: Dict[str, Any] = field(default_factory=dict)
    breakthrough_effects: List[str] = field(default_factory=list)
    notes: str = ""
    linked_sisyphos_cycle: Optional[int] = None


class PsycholyseProtocolLogger:
    """Allgemeiner, persistenter Logger fuer Psycholyse-Protokoll-Sessions."""

    def __init__(self, persistence_path: str = "data/psycholyse_sessions.json",
                 sisyphos: Optional["PersistentSisyphosCycle"] = None):
        self.persistence_path = Path(persistence_path)
        self.sisyphos = sisyphos
        self.entries: List[PsycholyseLogEntry] = []
        self._load_from_disk()

    def log_session(self, protocol_type: str, status: str,
                     pre_state: Optional[Dict[str, Any]] = None,
                     post_state: Optional[Dict[str, Any]] = None,
                     breakthrough_effects: Optional[List[str]] = None,
                     notes: str = "") -> PsycholyseLogEntry:
        if status not in VALID_STATUS_TAGS:
            raise ValueError(f"status muss einer von {VALID_STATUS_TAGS} sein, nicht {status!r}")

        entry = PsycholyseLogEntry(
            session_id=len(self.entries) + 1,
            timestamp=datetime.now().isoformat(),
            protocol_type=protocol_type,
            status=status,
            pre_state=pre_state or {},
            post_state=post_state or {},
            breakthrough_effects=breakthrough_effects or [],
            notes=notes,
        )
        self.entries.append(entry)
        self._save_to_disk()
        return entry

    def apply_to_sisyphos(self, entry: PsycholyseLogEntry, load_after: float) -> Optional[Dict[str, Any]]:
        """
        Der von psycholyse_engine.py vorausgesagte Integrationspunkt:
        traegt das Post-Session-Load als echten Sisyphos-Zyklus-Schritt ein,
        mit Rueckverweis auf die Session-ID.
        """
        if not self.sisyphos:
            return None
        result = self.sisyphos.step(
            load_after,
            notes=f"psycholyse_session={entry.session_id} ({entry.protocol_type})",
        )
        entry.linked_sisyphos_cycle = self.sisyphos.cycle_count
        self._save_to_disk()
        return result

    def monitor_coal_canary(self) -> str:
        """Verallgemeinerte Fassung von psycholyse_engine.PsycholyseEngine.monitor_coal_canary."""
        if not self.entries:
            return "Coal Canary: keine Sessions geloggt."
        last = self.entries[-1]
        load = last.post_state.get("load")
        if load is None:
            return "Coal Canary: letzte Session hat kein post_state['load']."
        if load > 0.5:
            return (
                "COAL CANARY ACTIVE: Hohe Last nach letzter Session "
                f"(load={load}). Booster oder Sisyphos-Oszillation pruefen."
            )
        return f"Coal Canary ruhig. Letzte Session load={load}."

    def get_entries(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self.entries if last_n is None else self.entries[-last_n:]
        return [asdict(e) for e in items]

    def _save_to_disk(self) -> None:
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"entries": [asdict(e) for e in self.entries]}
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[PsycholyseProtocolLogger] Failed to save: {e}")

    def _load_from_disk(self) -> None:
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("entries", []):
                self.entries.append(PsycholyseLogEntry(**item))
        except Exception as e:
            print(f"[PsycholyseProtocolLogger] Failed to load: {e}")
