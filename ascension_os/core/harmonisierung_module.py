# -*- coding: utf-8 -*-
"""
AscensionOS v9.6 - HarmonisierungsCoreModule

Setzt den in Core_Update_ALTE_Frau_95g_V4_Integration_2026-06-22.md (Drive,
01_Heroismus_Projekt-Archiv) explizit vorgeschlagenen Self-Mod-Punkt um:
"Implement HarmonisierungsCoreModule ... in executable code (Python) and
test with sample states".

Aus der Quelle (Kompendium der Heroik, Teil III):
- Harmonisierungs-Operation H = {b.q} . {q.b}
- Pruefkriterium: Narzissmus-Filter (messbare Abweichung vom Ausgangszustand
  bei mindestens einem Teilnehmer)
- Mass: Zufriedenheitsquant (binaer, pro abgeschlossener Operation geloggt)
- Vierschritt: Erkennen, Hinterfragen, Verinnerlichen, Kooperation
- Evolution Rule: Selbstmodifikations-Vorschlag nur wenn Banach-Kontraktion haelt

Ehrlicher Status: Die Quelle definiert q ("analoges/fliessendes Denken") und
b ("binaeres/schneidendes Denken") NUR konzeptuell, nicht als konkrete
Formel. Dieses Modul formalisiert q und b EXPLIZIT als affine Kontraktionen
ueber die bereits vorhandene, beweisgefuehrte BanachContractionSeed aus
heroic_math_engine.py (Knoten 20) - eine von mehreren moeglichen
Formalisierungen, keine autoritative. Nicht-Kommutativitaet (b(q(x)) !=
q(b(x))) ergibt sich hier aus den unterschiedlichen Zielpunkten von q und b,
nicht aus nicht-kommutierenden Matrizen (beide linear = Skalar*Identitaet) -
siehe _vierschritt_hinterfragen().
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    _ROOT = str(Path(__file__).resolve().parents[2])
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from fusion_hero_os.core.heroic_math_engine import BanachContractionSeed
except Exception:
    BanachContractionSeed = None

try:
    from .coevolutionary_closure import get_coevolutionary_closure
except Exception:
    get_coevolutionary_closure = None


@dataclass
class HarmonizationResult:
    timestamp: str
    initial_gap: float
    final_gap: float
    noncommutativity_gap: float
    is_contraction: bool
    contraction_factor: Optional[float]
    steps: int
    zufriedenheitsquant: bool
    narzissmus_filter_passed: Dict[str, bool]
    fixpoint: Optional[List[float]] = None


def _make_affine_seed(alpha: float, target: np.ndarray) -> "BanachContractionSeed":
    """Affine Kontraktion T(x) = alpha*x + (1-alpha)*target, alpha in (0,1)."""
    n = target.shape[0]
    A = alpha * np.eye(n)
    c = (1.0 - alpha) * target
    return BanachContractionSeed(A, c)


class HarmonisierungsCoreModule:
    """
    Iterative Annaeherung zweier Zustaende an einen gemeinsamen Fixpunkt
    ueber H = {b.q}.{q.b}.

    q = "fliessende" Annaeherung an den Partnerzustand (grosses alpha_q,
        sanfte Blend-Rate)
    b = "schneidende" Annaeherung an einen fixen Entscheidungsanker
        (kleines alpha_b, entschiedenere Rate)
    """

    def __init__(self, alpha_q: float = 0.8, alpha_b: float = 0.4,
                 narzissmus_epsilon: float = 1e-3,
                 persistence_path: str = "data/harmonisierung_history.json"):
        if BanachContractionSeed is None:
            raise ImportError(
                "BanachContractionSeed (fusion_hero_os.core.heroic_math_engine) nicht importierbar."
            )
        if not (0.0 < alpha_q < 1.0) or not (0.0 < alpha_b < 1.0):
            raise ValueError("alpha_q und alpha_b muessen in (0, 1) liegen (Kontraktionsbedingung).")

        self.alpha_q = alpha_q
        self.alpha_b = alpha_b
        self.narzissmus_epsilon = narzissmus_epsilon
        self.persistence_path = Path(persistence_path)
        self.history: List[HarmonizationResult] = []
        self.cec = get_coevolutionary_closure() if get_coevolutionary_closure else None
        self._load_from_disk()

    def _build_h_seed(self, state_a: np.ndarray, state_b: np.ndarray):
        """
        H = 0.5*(b(q(x)) + q(b(x))) als eigene affine Kontraktion.
        Ziel von q: state_b (Partnerzustand - fliessende Annaeherung).
        Ziel von b: Mittelpunkt (state_a+state_b)/2 (fixer Entscheidungsanker).
        """
        anchor = (state_a + state_b) / 2.0
        q_seed = _make_affine_seed(self.alpha_q, state_b)
        b_seed = _make_affine_seed(self.alpha_b, anchor)

        # b(q(x)) = A_b(A_q x + c_q) + c_b = (A_b A_q) x + (A_b c_q + c_b)
        A_bq = b_seed.A @ q_seed.A
        c_bq = b_seed.A @ q_seed.c + b_seed.c
        # q(b(x)) analog, andere Reihenfolge
        A_qb = q_seed.A @ b_seed.A
        c_qb = q_seed.A @ b_seed.c + q_seed.c

        A_h = 0.5 * (A_bq + A_qb)
        c_h = 0.5 * (c_bq + c_qb)
        h_seed = BanachContractionSeed(A_h, c_h)
        return h_seed, (A_bq, c_bq), (A_qb, c_qb)

    @staticmethod
    def _vierschritt_hinterfragen(bq: Tuple[np.ndarray, np.ndarray],
                                   qb: Tuple[np.ndarray, np.ndarray]) -> float:
        """Nicht-Kommutativitaet: Abstand der Bilder von b(q(.)) und q(b(.)) am Ursprung."""
        _, c_bq = bq
        _, c_qb = qb
        return float(np.linalg.norm(c_bq - c_qb))

    def harmonize(self, state_a: Any, state_b: Any,
                  participant_labels: Tuple[str, str] = ("A", "B")) -> HarmonizationResult:
        """Vollzieht den Vierschritt: Erkennen, Hinterfragen, Verinnerlichen, Kooperation."""
        x_a = np.asarray(state_a, dtype=np.float64)
        x_b = np.asarray(state_b, dtype=np.float64)

        # 1. Erkennen
        initial_gap = float(np.linalg.norm(x_a - x_b))

        # 2. Hinterfragen
        h_seed, bq, qb = self._build_h_seed(x_a, x_b)
        noncommutativity_gap = self._vierschritt_hinterfragen(bq, qb)

        # 3. Verinnerlichen (Fixpunkt-Iteration ueber die bewiesene Banach-Maschinerie;
        #    beide Zustaende laufen auf denselben H-Fixpunkt zu)
        new_a, steps_a = h_seed.iterate(x_a)
        new_b, steps_b = h_seed.iterate(x_b)
        final_gap = float(np.linalg.norm(new_a - new_b))

        # 4. Kooperation: Narzissmus-Filter + Zufriedenheitsquant
        dev_a = float(np.linalg.norm(new_a - x_a))
        dev_b = float(np.linalg.norm(new_b - x_b))
        narzissmus_filter_passed = {
            participant_labels[0]: dev_a > self.narzissmus_epsilon,
            participant_labels[1]: dev_b > self.narzissmus_epsilon,
        }
        zufriedenheitsquant = final_gap < initial_gap and all(narzissmus_filter_passed.values())

        result = HarmonizationResult(
            timestamp=datetime.now().isoformat(),
            initial_gap=round(initial_gap, 6),
            final_gap=round(final_gap, 6),
            noncommutativity_gap=round(noncommutativity_gap, 6),
            is_contraction=h_seed.q < 1.0,  # per Konstruktion von BanachContractionSeed garantiert
            contraction_factor=round(h_seed.q, 6),
            steps=max(steps_a, steps_b),
            zufriedenheitsquant=zufriedenheitsquant,
            narzissmus_filter_passed=narzissmus_filter_passed,
            fixpoint=h_seed.fixpoint().tolist(),
        )
        self.history.append(result)
        self._save_to_disk()

        if self.cec:
            self.cec.notify_change(
                source="HarmonisierungsCoreModule",
                change_type="harmonize",
                payload={"zufriedenheitsquant": zufriedenheitsquant, "final_gap": result.final_gap},
            )

        return result

    def propose_self_modification(self, result: HarmonizationResult) -> Dict[str, Any]:
        """
        Evolution Rule aus der Quelle: Selbstmodifikations-Vorschlag an
        PeerReviewCoreModule NUR wenn die Banach-Kontraktionsbedingung haelt.
        Schlaegt nur vor (Dict), fuehrt nichts eigenmaechtig aus.
        """
        if not result.is_contraction:
            return {"proposed": False, "reason": "Keine Kontraktion (q >= 1) - keine Konvergenzgarantie."}
        return {
            "proposed": True,
            "target": "PeerReviewCoreModule",
            "contraction_factor": result.contraction_factor,
            "fixpoint": result.fixpoint,
            "rationale": (
                f"H ist eine {result.contraction_factor:.4f}-Kontraktion, "
                f"Zufriedenheitsquant={result.zufriedenheitsquant}. "
                f"Vorschlag zur Aufnahme in PeerReview-Historie."
            ),
        }

    def get_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self.history if last_n is None else self.history[-last_n:]
        return [asdict(r) for r in items]

    def _save_to_disk(self) -> None:
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump({"history": [asdict(r) for r in self.history]}, f, indent=2)
        except Exception as e:
            print(f"[HarmonisierungsCoreModule] Failed to save: {e}")

    def _load_from_disk(self) -> None:
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("history", []):
                self.history.append(HarmonizationResult(**item))
        except Exception as e:
            print(f"[HarmonisierungsCoreModule] Failed to load: {e}")
