# -*- coding: utf-8 -*-
"""
AscensionOS v9.5 - QUBOAscensionOptimizer (QUBO_ascension_optimizer)

Schliesst Punkt 1 der "Naechste autonome Evolutionen"
(legacy_sources/AscensionOS/00_AscensionOS_Zusammenfuehrung_v8.md):
"QUBO-Problem fuer Devil-vs-Christus-Balance auf Stage-9-Trajectory".

Nutzt den bestehenden, echten QUBO-Solver (qb_qubo.py, inkl. Hyperthreading
via parallel_anneal) - keine neue Optimierungs-Engine, nur eine
domaenenspezifische Q-Matrix-Konstruktion + Ergebnis-Interpretation.

Ehrlicher Status: Die Abbildung "Devil-Praesenz vs. Christus-Internalisierung
pro Checkpoint als 2 Binaervariablen mit zeitabhaengigem Bias" ist EINE
plausible Formalisierung des in ASCENSION_EXPANSION_v8.md beschriebenen
Konzepts, keine autoritative oder validierte. Andere Formalisierungen sind
moeglich; das Modell macht keine Aussage ueber reale psychologische
Dynamiken - es macht lediglich eine QUBO-Trajektorie plausibel gemaess der
selbstgesetzten, unten dokumentierten Modellannahmen.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    _ROOT = str(Path(__file__).resolve().parents[2])
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    import qb_qubo
except Exception:
    qb_qubo = None


@dataclass
class CheckpointVerdict:
    index: int
    devil_active: bool
    christus_active: bool
    phase_label: str


@dataclass
class TrajectoryResult:
    checkpoints: List[CheckpointVerdict]
    energy: float
    n_restarts: int
    workers: int
    runtime_seconds: float


def build_devil_christus_qubo(n_checkpoints: int, base_bias: float = 1.0,
                               incoherence_penalty: float = 2.0,
                               lock_in_penalty: float = 0.5,
                               oscillation_tail_fraction: float = 0.3) -> np.ndarray:
    """
    Baut die QUBO-Matrix Q (Groesse 2*n_checkpoints) fuer die
    Devil-vs-Christus-Trajektorie.

    Variablen: x = [d_0..d_{N-1}, c_0..c_{N-1}]
      d_i=1  -> "Devil-Manifest" an Checkpoint i dominant
      c_i=1  -> "Christus-Internalisierung" an Checkpoint i dominant

    Modellannahmen (siehe Modul-Docstring fuer den Ehrlicher-Status-Hinweis):
      1. Linearer Bias: d wird mit steigendem i zunehmend unattraktiv (hoehere
         Energie bei d_i=1), c zunehmend attraktiv - bildet die in der Theorie
         beschriebene Trajektorie Devil -> Christus ueber die Zeit ab.
      2. Inkohaerenz-Strafe: d_i UND c_i gleichzeitig aktiv wird bestraft
         (kein Checkpoint ist beides zugleich).
      3. Lock-in-Strafe im "Sisyphos-Oszillations"-Schwanzbereich (letzte
         `oscillation_tail_fraction` der Checkpoints): zwei aufeinander-
         folgende Checkpoints mit demselben aktiven Pol werden leicht
         bestraft, um erstarrte Ein-Pol-Dominanz gegenueber Oszillation zu
         benachteiligen (Sisyphos-Zyklus = andauernde Oszillation, kein
         finaler Fixpunkt).
    """
    n = n_checkpoints
    size = 2 * n
    Q = np.zeros((size, size), dtype=np.float64)

    def d(i: int) -> int:
        return i

    def c(i: int) -> int:
        return n + i

    for i in range(n):
        t = i / max(1, n - 1)
        Q[d(i), d(i)] += base_bias * t
        Q[c(i), c(i)] += -base_bias * t
        Q[d(i), c(i)] += incoherence_penalty / 2.0
        Q[c(i), d(i)] += incoherence_penalty / 2.0

    tail_start = int(n * (1.0 - oscillation_tail_fraction))
    for i in range(max(tail_start, 0), n - 1):
        for var in (d, c):
            a, b = var(i), var(i + 1)
            Q[a, b] += lock_in_penalty / 2.0
            Q[b, a] += lock_in_penalty / 2.0

    return Q


class QUBOAscensionOptimizer:
    """Loest die Devil-vs-Christus-QUBO ueber den bestehenden Hyperthreading-SA-Solver."""

    def __init__(self, n_checkpoints: int = 12):
        if qb_qubo is None:
            raise ImportError(
                "qb_qubo.py nicht importierbar (numpy/numba fehlen?) - "
                "QUBOAscensionOptimizer benoetigt den bestehenden QUBO-Solver."
            )
        self.n_checkpoints = n_checkpoints

    def solve(self, steps: int = 4000, n_restarts: Optional[int] = None,
              **qubo_kwargs: Any) -> TrajectoryResult:
        Q = build_devil_christus_qubo(self.n_checkpoints, **qubo_kwargs)
        raw = qb_qubo.parallel_anneal(Q, steps=steps, n_restarts=n_restarts)
        return self._interpret(raw)

    def _interpret(self, raw: Dict[str, Any]) -> TrajectoryResult:
        solution = raw["solution"]
        n = self.n_checkpoints
        checkpoints: List[CheckpointVerdict] = []
        for i in range(n):
            devil = bool(solution[i])
            christus = bool(solution[n + i])
            if devil and christus:
                label = "inkohaerent (beide aktiv)"
            elif devil:
                label = "devil-dominant"
            elif christus:
                label = "christus-dominant"
            else:
                label = "passiv (keins aktiv)"
            checkpoints.append(CheckpointVerdict(i, devil, christus, label))

        return TrajectoryResult(
            checkpoints=checkpoints,
            energy=raw["energy"],
            n_restarts=raw["n_restarts"],
            workers=raw["workers"],
            runtime_seconds=raw["runtime_seconds"],
        )
