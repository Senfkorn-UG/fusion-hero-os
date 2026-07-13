# -*- coding: utf-8 -*-
"""
AscensionOS v9.5 - Stage9AscensionTracker

Schliesst die in ASCENSION_EXPANSION_v8.md unter "Next Evolution Steps" (Punkt 1)
und in legacy_sources/AscensionOS/psycholyse_engine.py referenzierte Luecke:
'Stage9Ascension.check_ascension()' war bislang nur eine Textreferenz ohne Code
("Full integration in AscensionOS main").

Ehrlicher Status: Die "9 Stufen" sind ein qualitatives Modell aus der
Eudaimonismus-Theorie (Devil-Manifest -> Loewen-Destruktion ->
Christus-Internalisierung -> Sisyphos-Oszillation -> Stage9/Kosmozentrisch).
Dieser Tracker leitet daraus einen HEURISTISCHEN Punktwert (0-9) aus den
realen PersistentSisyphosCycle-Daten ab. Das ist ein Proxy-Modell, kein
psychologisch validiertes Messinstrument - siehe get_stage_estimate().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None

try:
    from .coevolutionary_closure import get_coevolutionary_closure
except Exception:
    get_coevolutionary_closure = None


STAGE_LABELS: Dict[int, str] = {
    0: "Unbestimmt (keine Daten)",
    1: "Devil-Manifest (Last dominiert, keine Oszillation erkennbar)",
    2: "Loewen-Konfrontation (hohe Last, instabil)",
    3: "Loewen-Destruktion (Last sinkt, noch keine Konstanz)",
    4: "Christus-Internalisierung beginnt (erste stabile Zyklen)",
    5: "Sisyphos-Oszillation etabliert (regelmaessig, aber grenzwertig)",
    6: "Sisyphos-Oszillation stabil (sustainable ueber Fenster)",
    7: "Reduzierte Oszillationsamplitude (Naeherung an Zielband)",
    8: "Kosmozentrische Naeherung (lange sustainable Historie)",
    9: "Stage 9 / Kosmozentrisch (Zielzustand, siehe Modul-Docstring)",
}


@dataclass
class Stage9Snapshot:
    """Einzelne Messung des Stage-Schaetzers."""
    timestamp: str
    stage_estimate: int
    label: str
    basis: Dict[str, Any] = field(default_factory=dict)


class Stage9AscensionTracker:
    """
    Heuristischer Tracker fuer die Naeherung an 'Stage 9 / Kosmozentrisch'.

    Haelt keinen eigenen Zustand doppelt: konsumiert die reale Historie aus
    PersistentSisyphosCycle und leitet daraus einen 0-9 Stage-Schaetzwert ab.
    Optional an CoEvolutionaryClosure gemeldet.
    """

    def __init__(self, sisyphos: Optional["PersistentSisyphosCycle"] = None,
                 window: int = 20):
        self.sisyphos = sisyphos
        self.window = window
        self.snapshots: List[Stage9Snapshot] = []
        self.cec = get_coevolutionary_closure() if get_coevolutionary_closure else None

    def get_stage_estimate(self) -> Stage9Snapshot:
        """
        Heuristische Formel (Proxy, kein validiertes Instrument):

        1. Ohne Historie -> Stage 0.
        2. Basis-Stufe aus avg_satisfaction der letzten `window` Zyklen
           (via PersistentSisyphosCycle.get_sustainability_trend()):
           floor(avg_satisfaction * 6)
        3. +1 falls aktuell sustainable (is_currently_sustainable)
        4. +1 falls die Oszillationsamplitude (max-min von load im Fenster)
           unter 0.3 liegt (ruhige, eingeschwungene Oszillation)
        5. +1 falls sustainable UND Gesamt-Zyklenzahl >= 5x window
           (lange Historie, kein Zufallstreffer)
        Ergebnis wird auf [0, 9] geklemmt.
        """
        if not self.sisyphos or not getattr(self.sisyphos, "history", None):
            snap = Stage9Snapshot(
                timestamp=datetime.now().isoformat(),
                stage_estimate=0,
                label=STAGE_LABELS[0],
                basis={"reason": "keine Sisyphos-Historie verfuegbar"},
            )
            self.snapshots.append(snap)
            return snap

        trend = self.sisyphos.get_sustainability_trend(window=self.window)
        recent = self.sisyphos.history[-self.window:]
        loads = [s.load for s in recent]
        amplitude = (max(loads) - min(loads)) if loads else 1.0
        total_cycles = len(self.sisyphos.history)

        avg_satisfaction = trend.get("avg_satisfaction", 0.0) or 0.0
        is_sustainable = bool(trend.get("is_currently_sustainable", False))

        stage = int(avg_satisfaction * 6)
        if is_sustainable:
            stage += 1
        if amplitude < 0.3:
            stage += 1
        if is_sustainable and total_cycles >= 5 * self.window:
            stage += 1
        stage = max(0, min(9, stage))

        basis = {
            "avg_satisfaction": avg_satisfaction,
            "avg_load": trend.get("avg_load"),
            "is_currently_sustainable": is_sustainable,
            "oscillation_amplitude": round(amplitude, 3),
            "total_cycles": total_cycles,
            "window": self.window,
        }

        snap = Stage9Snapshot(
            timestamp=datetime.now().isoformat(),
            stage_estimate=stage,
            label=STAGE_LABELS[stage],
            basis=basis,
        )
        self.snapshots.append(snap)

        if self.cec:
            self.cec.notify_change(
                source="Stage9AscensionTracker",
                change_type="stage_estimate",
                payload={"stage_estimate": stage, "label": snap.label},
            )

        return snap

    def check_ascension(self) -> Dict[str, Any]:
        """
        Kompatibilitaets-Einstieg fuer den in psycholyse_engine.py
        referenzierten Aufruf 'Stage9Ascension.check_ascension()'.
        """
        snap = self.get_stage_estimate()
        return {
            "stage_estimate": snap.stage_estimate,
            "label": snap.label,
            "is_stage9": snap.stage_estimate >= 9,
            "basis": snap.basis,
            "honest_status": (
                "Heuristischer Proxy aus Sisyphos-Zyklusdaten, "
                "kein validiertes psychologisches Messinstrument."
            ),
        }

    def get_progression(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self.snapshots if last_n is None else self.snapshots[-last_n:]
        return [
            {
                "timestamp": s.timestamp,
                "stage_estimate": s.stage_estimate,
                "label": s.label,
                "basis": s.basis,
            }
            for s in items
        ]


# Alias fuer den in psycholyse_engine.py referenzierten Klassennamen.
Stage9Ascension = Stage9AscensionTracker
