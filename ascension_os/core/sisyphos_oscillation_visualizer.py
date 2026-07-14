# -*- coding: utf-8 -*-
"""
AscensionOS v9.5 - SisyphosOscillationVisualizer

Schliesst Punkt 1 der "Next Evolution Steps" (ASCENSION_EXPANSION_v8.md):
Visualisierung der Sisyphos-Oszillation aus PersistentSisyphosCycle.

Ehrlicher Status: BRANCH_STRATEGY.md nennt eine Zielschwelle "Oszillation <7
fuer nachhaltige Eudaimonia ohne Kollaps", ohne die Einheit zu definieren.
Dieses Modul interpretiert das EXPLIZIT als "Anzahl Richtungswechsel
(Reversals) von `load` im Beobachtungsfenster" - eine plausible, aber nicht
die einzig moegliche Lesart (siehe REVERSAL_THRESHOLD_SOURCE).

Abhaengigkeitsfrei (kein matplotlib): ASCII-Sparkline + minimaler
Hand-SVG-Renderer, reicht fuer Logs/Dashboards ohne neue Dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None


REVERSAL_THRESHOLD_SOURCE = (
    "BRANCH_STRATEGY.md: 'Sisyphos-Zyklus as sustainability engine "
    "(oscillation <7 for long-term Eudaimonia without collapse)'. Einheit "
    "im Original nicht spezifiziert; hier interpretiert als "
    "Richtungswechsel-Anzahl von `load` im Fenster."
)

SPARK_CHARS = " ▁▂▃▄▅▆▇█"


@dataclass
class OscillationReport:
    n_points: int
    amplitude: float
    reversal_count: int
    within_threshold: Optional[bool]
    sparkline: str
    series: List[Dict[str, float]]


class SisyphosOscillationVisualizer:
    """Liest PersistentSisyphosCycle-Historie und erzeugt Kennzahlen + Charts."""

    def __init__(self, sisyphos: Optional["PersistentSisyphosCycle"] = None):
        self.sisyphos = sisyphos

    def _get_series(self, last_n: Optional[int], field_name: str) -> List[float]:
        if not self.sisyphos or not getattr(self.sisyphos, "history", None):
            return []
        history = self.sisyphos.history if last_n is None else self.sisyphos.history[-last_n:]
        return [getattr(s, field_name) for s in history]

    @staticmethod
    def _sparkline(values: List[float]) -> str:
        if not values:
            return ""
        lo, hi = min(values), max(values)
        span = (hi - lo) or 1.0
        n_chars = len(SPARK_CHARS) - 1
        return "".join(
            SPARK_CHARS[min(n_chars, int((v - lo) / span * n_chars))] for v in values
        )

    @staticmethod
    def _count_reversals(values: List[float], min_delta: float = 0.02) -> int:
        """Zaehlt Richtungswechsel (Peak/Trough) oberhalb einer Rauschschwelle."""
        if len(values) < 3:
            return 0
        reversals = 0
        direction = 0
        for prev, curr in zip(values, values[1:]):
            delta = curr - prev
            if abs(delta) < min_delta:
                continue
            new_direction = 1 if delta > 0 else -1
            if direction != 0 and new_direction != direction:
                reversals += 1
            direction = new_direction
        return reversals

    def build_report(self, last_n: int = 40, reversal_threshold: int = 7) -> OscillationReport:
        loads = self._get_series(last_n, "load")
        satisfactions = self._get_series(last_n, "satisfaction")

        amplitude = (max(loads) - min(loads)) if loads else 0.0
        reversals = self._count_reversals(loads)
        within = (reversals < reversal_threshold) if loads else None

        series = [{"load": l, "satisfaction": s} for l, s in zip(loads, satisfactions)]

        return OscillationReport(
            n_points=len(loads),
            amplitude=round(amplitude, 3),
            reversal_count=reversals,
            within_threshold=within,
            sparkline=self._sparkline(loads),
            series=series,
        )

    def render_svg(self, last_n: int = 40, width: int = 480, height: int = 120) -> str:
        """Minimaler, abhaengigkeitsfreier SVG-Linienchart (kein matplotlib noetig)."""
        loads = self._get_series(last_n, "load")
        if not loads:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                f'<text x="10" y="{height // 2}" font-size="12">Keine Sisyphos-Historie</text></svg>'
            )

        lo, hi = min(loads), max(loads)
        span = (hi - lo) or 1.0
        pad = 10
        n = len(loads)
        step = (width - 2 * pad) / max(1, n - 1)

        points = []
        for i, v in enumerate(loads):
            x = pad + i * step
            y = height - pad - ((v - lo) / span) * (height - 2 * pad)
            points.append(f"{x:.1f},{y:.1f}")
        polyline = " ".join(points)

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<polyline points="{polyline}" fill="none" stroke="#c0392b" stroke-width="2"/>'
            f'<text x="{pad}" y="{pad}" font-size="10">load (n={n}, '
            f'amp={round(hi - lo, 3)})</text>'
            f"</svg>"
        )
