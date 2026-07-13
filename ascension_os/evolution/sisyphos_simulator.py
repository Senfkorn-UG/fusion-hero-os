# -*- coding: utf-8 -*-
"""
AscensionOS v9.5 - sisyphos_simulator

Schliesst Punkt 2 der "Naechste autonome Evolutionen"
(legacy_sources/AscensionOS/00_AscensionOS_Zusammenfuehrung_v8.md):
"sisyphos_simulator.py - Erweiterte Oszillations-Simulation +
10k-Generationen-Track mit Hyperthreading".

Ehrlicher Status zu "Hyperthreading": Dies ist eine reine Python-Simulation
(kein numpy-Hotloop wie qb_qubo.py). ThreadPoolExecutor bringt hier nur dann
echten Speedup, wenn der uebergebene load_fn selbst GIL-freigebende Arbeit
macht (I/O, numpy, C-Extensions) - reine Python-Arithmetik in load_fn bleibt
GIL-gebunden und profitiert kaum. Gleiche Einschraenkung wie bereits in
src/normal_os/ascension/fusion_hero_node.py dokumentiert ("Parallelitaet ist
nur wirksam, wenn Backend latenzgebunden ist"). Der Default-load_fn hier ist
reine Arithmetik; die Parallelisierung ist daher primaer organisatorisch
(mehrere unabhaengige Seeds/Traces gleichzeitig statt sequenziell), kein
garantierter CPU-Speedup.

Nutzt eine eigene, NICHT-persistente Sisyphos-Mechanik (identische Formel
wie SisyphosCycle.step in fusion_hero_os/core/universal_llm_router.py), um
die reale, persistierte Historie (PersistentSisyphosCycle) nicht mit
Simulationsdaten zu verunreinigen.
"""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

LoadFn = Callable[[int, float, random.Random], float]

MAX_GENERATIONS = 10_000


def default_load_fn(step: int, prev_load: float, rng: random.Random) -> float:
    """Random-Walk mit Rueckstellkraft Richtung 0.5 (einfaches, deklariertes Default-Modell)."""
    pull = (0.5 - prev_load) * 0.1
    noise = rng.uniform(-0.15, 0.15)
    return max(0.0, min(1.0, prev_load + pull + noise))


@dataclass
class SimRun:
    seed: int
    loads: List[float] = field(default_factory=list)
    satisfactions: List[float] = field(default_factory=list)

    def final_state(self) -> Dict[str, float]:
        if not self.loads:
            return {"load": 0.0, "satisfaction": 0.0}
        return {"load": self.loads[-1], "satisfaction": self.satisfactions[-1]}

    def is_sustainable(self) -> bool:
        s = self.final_state()
        return s["satisfaction"] > 0.4 and s["load"] < 0.85

    def reversal_count(self, min_delta: float = 0.02) -> int:
        reversals = 0
        direction = 0
        for prev, curr in zip(self.loads, self.loads[1:]):
            delta = curr - prev
            if abs(delta) < min_delta:
                continue
            new_direction = 1 if delta > 0 else -1
            if direction != 0 and new_direction != direction:
                reversals += 1
            direction = new_direction
        return reversals


def _run_one(seed: int, generations: int, load_fn: LoadFn, initial_load: float) -> SimRun:
    rng = random.Random(seed)
    run = SimRun(seed=seed)
    load = initial_load
    for step in range(generations):
        load = load_fn(step, load, rng)
        satisfaction = max(0.0, 1.0 - load * 0.7)  # identisch zu SisyphosCycle.step
        run.loads.append(load)
        run.satisfactions.append(satisfaction)
    return run


def simulate(generations: int = 200, n_runs: int = 8, initial_load: float = 0.5,
             load_fn: Optional[LoadFn] = None, workers: Optional[int] = None,
             base_seed: int = 0) -> Dict[str, Any]:
    """
    Fuehrt `n_runs` unabhaengige Sisyphos-Oszillations-Simulationen ueber
    `generations` Schritte aus (bis zu MAX_GENERATIONS=10_000, siehe
    Next-Evolution-Step-Vorgabe "10k-Generationen-Track").

    Siehe Modul-Docstring fuer den ehrlichen Hyperthreading-Vorbehalt.
    """
    if generations > MAX_GENERATIONS:
        raise ValueError(f"generations > {MAX_GENERATIONS} nicht unterstuetzt.")
    if n_runs < 1:
        raise ValueError("n_runs muss >= 1 sein.")

    fn = load_fn or default_load_fn
    seeds = [base_seed + k for k in range(n_runs)]

    with ThreadPoolExecutor(max_workers=workers or n_runs) as ex:
        runs = list(ex.map(lambda s: _run_one(s, generations, fn, initial_load), seeds))

    sustainable_count = sum(1 for r in runs if r.is_sustainable())
    final_satisfactions = [r.final_state()["satisfaction"] for r in runs]
    avg_reversals = sum(r.reversal_count() for r in runs) / len(runs)

    return {
        "generations": generations,
        "n_runs": n_runs,
        "sustainable_fraction": sustainable_count / n_runs,
        "avg_final_satisfaction": round(sum(final_satisfactions) / n_runs, 4),
        "avg_reversal_count": round(avg_reversals, 2),
        "runs": runs,
    }
