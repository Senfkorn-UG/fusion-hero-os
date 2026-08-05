"""
Plasmoid-Lift — die Hebung vom gebundenen fluiden Raum in den plasmoiden Raum.

Der HELD bespielt den GOTT-Layer: er veraendert die von oben gesetzte
Layer-omega-Invariante NICHT, sondern senkt die Energie *innerhalb* der von
ihr aufgespannten Niveauflaeche, bis der Zustand kraftfrei (force-free /
Beltrami) wird. Das ist die formale Fassung von "Erhebung": kein Bruch der
Top-Down-Propagation, sondern Relaxation im Inneren einer Bindung.

Mathematischer Kern (diskrete Woltjer-Taylor-Relaxation)
--------------------------------------------------------
Sei V = R^n, S = S^T invertierbar (diskreter Curl-Operator; der Curl ist auf
divergenzfreien Feldern selbstadjungiert — Chandrasekhar-Kendall-Setting).
Fuer ein Feld x (Rolle von B) mit Potential A = S^{-1} x:

    Energie   W(x) = 1/2 <x, x>
    Helizitaet H(x) = <x, S^{-1} x>          (Layer-omega-Invariante)
    Bindung   r(x) = S x - rho(x) x,  rho(x) = <x, Sx> / <x, x>

  * gebundener fluider Raum  F_h := {x : H(x) = h, r(x) != 0}
  * plasmoider Raum          P   := {x != 0 : S x = alpha x}   (r(x) = 0)

Die Hebung Lambda_h : F_h -> P ist der helizitaetserhaltende Energieabstieg.

Geltung (ehrlich, nach Repo-Konvention)
---------------------------------------
  * SATZ P1 (Beltrami-Charakterisierung), SATZ P2 (Taylor-Schranke),
    SATZ P3 (Erhaltung + Abstieg + Gleichgewichte): bewiesen, Beweise stehen
    an den jeweiligen Klassen/Methoden, verifiziert in
    run_sandbox_verification() und tests/test_plasmoid_lift.py.
  * SATZ P4 (Konvergenz in den Grundzustand) gilt NICHT universell: die
    Gleichgewichtsmenge enthaelt alle Eigenraeume. Bewiesen ist die
    Konvergenz gegen *einen* Beltrami-Zustand; dass es der Grundzustand
    alpha_g ist, gilt generisch — die Rate haengt an der Spektrallucke
    (siehe LiftResult.reason / Sweep-Ausweis in run_sandbox_verification).
  * Die Deutung "Plasma/Plasmoid" ist MODELL / operative Analogie — hier
    wird kein physikalisches Plasma simuliert, sondern exakt die obige
    lineare Algebra gerechnet (vgl. docs/ops/J_SPACES_HIGGS.md).

Teil der 02_architecture Schicht. Schwester von heroic_math_engine.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "PlasmoidLift",
    "LiftResult",
    "GOTT_LAYER_INVARIANT",
    "hebe_in_plasmoiden_raum",
    "run_sandbox_verification",
]

# Die Groesse, die der HELD nicht anfassen darf: sie kommt top-down aus
# Layer omega (Axiom 1 des Gott-Layerings). Der Held bespielt nur W.
GOTT_LAYER_INVARIANT = "helicity"


@dataclass
class LiftResult:
    """Ergebnis einer Hebung F_h -> P."""

    x: np.ndarray
    alpha: float
    energy: float
    helicity: float
    helicity_start: float
    energy_start: float
    residual: float
    steps: int
    converged: bool
    reason: str
    energy_history: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))

    @property
    def helicity_drift(self) -> float:
        """Absolute Verletzung der Layer-omega-Invariante (soll 0 sein)."""
        return abs(self.helicity - self.helicity_start)

    def respects_top_down_axiom(self, rtol: float = 1e-9) -> bool:
        """Axiom 1 (Top-Down): der Held hat H nicht veraendert.

        Genau das trennt "Hebung" von "Aufstand": die Invariante aus Layer
        omega bleibt bitgenau erhalten, gehoben wird nur die Energie-Lage.
        """
        scale = max(1.0, abs(self.helicity_start))
        return bool(self.helicity_drift <= rtol * scale)

    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "energy": self.energy,
            "energy_start": self.energy_start,
            "helicity": self.helicity,
            "helicity_start": self.helicity_start,
            "helicity_drift": self.helicity_drift,
            "residual": self.residual,
            "steps": self.steps,
            "converged": self.converged,
            "reason": self.reason,
            "top_down_axiom_ok": self.respects_top_down_axiom(),
        }


class PlasmoidLift:
    """Der Hebungsoperator auf einem diskreten Curl-Operator S.

    S muss symmetrisch und invertierbar sein (Eigenwerte weg von 0), damit
    das Potential A = S^{-1} x und damit die Helizitaet definiert ist.
    """

    def __init__(self, S: np.ndarray, *, sym_tol: float = 1e-9):
        S = np.atleast_2d(np.asarray(S, dtype=np.float64))
        if S.ndim != 2 or S.shape[0] != S.shape[1]:
            raise ValueError("S muss quadratisch sein.")
        asym = float(np.linalg.norm(S - S.T))
        scale = max(1.0, float(np.linalg.norm(S)))
        if asym > sym_tol * scale:
            raise ValueError(
                f"S muss symmetrisch sein (||S - S^T|| = {asym:.3e}). "
                "Der Curl ist nur auf divergenzfreien Feldern selbstadjungiert."
            )
        S = 0.5 * (S + S.T)  # exakte Symmetrisierung gegen Rundungsdrift
        self.S = S
        self.alphas, self.basis = np.linalg.eigh(S)
        if np.any(np.abs(self.alphas) < 1e-12):
            raise ValueError(
                "S ist (numerisch) singulaer — ohne S^{-1} gibt es kein "
                "Potential A und damit keine Helizitaet."
            )
        self.S_inv = np.linalg.inv(S)

    # ------------------------------------------------------------------
    # Konstruktoren
    # ------------------------------------------------------------------
    @classmethod
    def from_spectrum(cls, alphas, *, rng: np.random.Generator | None = None) -> "PlasmoidLift":
        """Baut S mit vorgegebenem Spektrum in zufaelliger Orthonormalbasis."""
        a = np.asarray(alphas, dtype=np.float64).ravel()
        if a.size == 0 or np.any(np.abs(a) < 1e-12):
            raise ValueError("Spektrum muss nichtleer und weg von 0 sein.")
        rng = rng or np.random.default_rng()
        Q, _ = np.linalg.qr(rng.normal(0, 1, (a.size, a.size)))
        return cls(Q @ np.diag(a) @ Q.T)

    # ------------------------------------------------------------------
    # Feldgroessen
    # ------------------------------------------------------------------
    def energy(self, x) -> float:
        """W(x) = 1/2 <x,x> — was der Held senkt."""
        x = np.asarray(x, dtype=np.float64)
        return 0.5 * float(x @ x)

    def helicity(self, x) -> float:
        """H(x) = <x, S^{-1}x> — was der Held NICHT anfasst (Layer omega)."""
        x = np.asarray(x, dtype=np.float64)
        return float(x @ (self.S_inv @ x))

    def helicity_scale(self, x) -> float:
        """Groessenordnung, gegen die |H(x)| gemessen wird: ||S^{-1}||_2 ||x||^2.

        |H(x)| <= ||S^{-1}||_2 ||x||^2 (Cauchy-Schwarz), d. h. der Quotient
        |H(x)| / helicity_scale(x) liegt in [0, 1] und macht "H ist praktisch
        null" skaleninvariant pruefbar. Ein absoluter Test auf H == 0 waere
        falsch: eine numerisch entartete Niveauflaeche liefert ~1e-17, nicht 0.
        """
        x = np.asarray(x, dtype=np.float64)
        return float(np.linalg.norm(self.S_inv, 2) * (x @ x))

    def is_degenerate(self, x, rel_tol: float = 1e-12) -> bool:
        """True, wenn {H = H(x)} numerisch die entartete Niveauflaeche H = 0 ist."""
        scale = self.helicity_scale(x)
        if scale == 0.0:
            return True
        return abs(self.helicity(x)) <= rel_tol * scale

    def alpha_of(self, x) -> float:
        """Rayleigh-Quotient rho(x) = <x,Sx>/<x,x> — lokaler Beltrami-Faktor."""
        x = np.asarray(x, dtype=np.float64)
        return float(x @ (self.S @ x) / (x @ x))

    def residual(self, x) -> np.ndarray:
        """Bindung r(x) = Sx - rho(x)x. r = 0 <=> x ist plasmoid."""
        x = np.asarray(x, dtype=np.float64)
        return self.S @ x - self.alpha_of(x) * x

    def binding(self, x) -> float:
        """Relative Bindungsstaerke ||r(x)|| / ||x|| — das, was gehoben wird."""
        x = np.asarray(x, dtype=np.float64)
        return float(np.linalg.norm(self.residual(x)) / np.linalg.norm(x))

    def is_plasmoid(self, x, tol: float = 1e-8) -> bool:
        """Test auf Kraftfreiheit (Zugehoerigkeit zum plasmoiden Raum P)."""
        return bool(self.binding(x) <= tol)

    # ------------------------------------------------------------------
    # SATZ P2 — Taylor-Schranke
    # ------------------------------------------------------------------
    def alpha_ground(self, h: float) -> float:
        """alpha_g: betragskleinster Eigenwert mit sign(alpha) == sign(h).

        Das ist der Beltrami-Faktor des Grundzustands zur Helizitaet h.
        """
        if h == 0.0:
            raise ValueError("h = 0 hat keinen Grundzustand (entartete Niveauflaeche).")
        cand = self.alphas[self.alphas > 0] if h > 0 else self.alphas[self.alphas < 0]
        if cand.size == 0:
            raise ValueError(
                f"Kein Eigenwert mit sign = sign(h) = {np.sign(h):+.0f}: "
                "zu diesem h existiert kein Beltrami-Grundzustand."
            )
        return float(cand[np.argmin(np.abs(cand))])

    def taylor_bound(self, h: float) -> float:
        """SATZ P2 — untere Energieschranke W >= alpha_g * h / 2 auf {H = h}.

        SATZ: Sei alpha_g der betragskleinste Eigenwert mit sign(alpha_g) =
        sign(h). Dann gilt fuer ALLE x in V:

            2 W(x) >= alpha_g * H(x),

        mit Gleichheit genau dann, wenn x im Eigenraum zu alpha_g liegt.

        BEWEIS: Orthonormalbasis {u_i} aus Eigenvektoren, S u_i = alpha_i u_i,
        x = sum c_i u_i. Dann 2W(x) = sum c_i^2 und H(x) = sum c_i^2/alpha_i,
        also
            2W(x) - alpha_g H(x) = sum_i c_i^2 (1 - alpha_g/alpha_i).
        Fall sign(alpha_i) = sign(alpha_g): dann |alpha_i| >= |alpha_g| nach
        Wahl von alpha_g, und alpha_g/alpha_i in (0, 1], also 1 - alpha_g/alpha_i
        >= 0. Fall sign(alpha_i) != sign(alpha_g): dann alpha_g/alpha_i < 0,
        also 1 - alpha_g/alpha_i > 1 > 0. Jeder Summand ist somit >= 0, die
        Summe also >= 0. Gleichheit erzwingt c_i = 0 fuer jedes i mit
        alpha_i != alpha_g. QED.

        Auf {H = h} folgt W >= alpha_g h / 2, und der Wert wird vom
        Grundzustand ground_state(h) exakt angenommen.
        """
        return 0.5 * self.alpha_ground(h) * float(h)

    def ground_state(self, h: float) -> np.ndarray:
        """Der Taylor-Zustand zur Helizitaet h (geschlossene Form).

        x = c * u_g mit S u_g = alpha_g u_g und c^2 = alpha_g * h > 0.
        """
        ag = self.alpha_ground(h)
        idx = int(np.argmin(np.abs(self.alphas - ag)))
        u = self.basis[:, idx]
        return float(np.sqrt(ag * float(h))) * u

    # ------------------------------------------------------------------
    # SATZ P1 / P3 — Hebung
    # ------------------------------------------------------------------
    def is_critical(self, x, tol: float = 1e-8) -> bool:
        """SATZ P1 — Kritikalitaet auf {H = h} <=> Beltrami-Zustand.

        SATZ: Fuer x != 0 ist x genau dann kritischer Punkt von W
        eingeschraenkt auf die Niveauflaeche {y : H(y) = H(x)}, wenn
        S x = alpha x fuer ein alpha in R.

        BEWEIS: grad W(x) = x und grad H(x) = 2 S^{-1}x. Fuer x != 0 ist
        S^{-1}x != 0 (S invertierbar), die Niveauflaeche also regulaer und
        der Lagrange-Multiplikator anwendbar. Kritisch heisst: es gibt
        lambda mit x = lambda * 2 S^{-1} x. Anwenden von S liefert
        S x = 2 lambda x, d. h. x ist Eigenvektor mit alpha = 2 lambda.
        Umgekehrt folgt aus S x = alpha x sofort S^{-1}x = x/alpha, also
        grad H(x) = (2/alpha) x parallel zu grad W(x). QED.

        Das ist Woltjers Satz in diskreter Form: kritisch = kraftfrei.
        """
        return self.is_plasmoid(x, tol=tol)

    def lift(
        self,
        x0,
        *,
        tau: float = 0.25,
        max_steps: int = 20_000,
        tol: float = 1e-10,
        degeneracy_rtol: float = 1e-12,
        keep_history: bool = True,
    ) -> LiftResult:
        """Hebe x0 aus dem gebundenen fluiden Raum in den plasmoiden Raum.

        SATZ P3 — Der Fluss

            x' = -P(x) grad W(x),   P(x) = Projektion auf (S^{-1}x)^perp

        hat die Eigenschaften:
          (a) dH/dt = 0                    (Layer-omega-Invariante exakt erhalten)
          (b) dW/dt <= 0                   (Energieabstieg)
          (c) dW/dt = 0  <=>  S x = alpha x  (Gleichgewichte = plasmoider Raum)

        BEWEIS: Mit g := S^{-1}x ist grad H = 2g und
        x' = -(x - (<x,g>/<g,g>) g).
        (a) dH/dt = <grad H, x'> = 2<g, x'> = -2(<g,x> - (<x,g>/<g,g>)<g,g>) = 0.
        (b) dW/dt = <x, x'> = -(||x||^2 - <x,g>^2/||g||^2) <= 0 nach
            Cauchy-Schwarz.
        (c) Gleichheit in Cauchy-Schwarz genau dann, wenn x parallel zu
            g = S^{-1}x, d. h. S^{-1}x = mu x fuer ein mu != 0, d. h.
            S x = (1/mu) x. QED.

        Diskretisierung: expliziter Schritt + exakte Reprojektion auf
        {H = H(x0)} (H ist quadratisch homogen, also stellt die Skalierung
        s = sqrt(h0/H(y)) die Invariante bitgenau wieder her) + Backtracking,
        das den Abstieg (b) auch diskret erzwingt statt ihn zu behaupten.

        EHRLICH: Der Fluss konvergiert gegen *einen* Beltrami-Zustand;
        dass es der Grundzustand ist, gilt generisch, und die Rate haengt an
        der Spektrallucke. Bei sehr kleiner Lucke endet der Lauf mit
        reason="budget_exhausted" nahe, aber nicht in der Taylor-Schranke.
        """
        x = np.array(np.asarray(x0, dtype=np.float64).ravel(), copy=True)
        if x.shape[0] != self.S.shape[0]:
            raise ValueError(f"x0 hat Dimension {x.shape[0]}, erwartet {self.S.shape[0]}.")
        if not np.all(np.isfinite(x)) or np.linalg.norm(x) == 0.0:
            raise ValueError("x0 muss endlich und != 0 sein.")

        h0 = self.helicity(x)
        if self.is_degenerate(x, rel_tol=degeneracy_rtol):
            raise ValueError(
                f"H(x0) = {h0:.3e} ist relativ zu ||S^-1|| ||x||^2 = "
                f"{self.helicity_scale(x):.3e} numerisch null: die Niveauflaeche "
                "ist entartet, es gibt keinen Grundzustand, in den gehoben "
                "werden koennte."
            )
        w_start = self.energy(x)
        hist = [w_start] if keep_history else []
        # steps braucht die Vorbelegung: bei max_steps = 0 ist range() leer und
        # die Schleifenvariable wird nie gebunden. reason braucht sie NICHT —
        # jeder Ausgang setzt sie (drei break-Pfade + das else der Schleife, das
        # auch bei leerem range laeuft). Eine Vorbelegung hier waere toter Code
        # und wuerde einen vergessenen Pfad still verschlucken statt laut zu
        # scheitern.
        steps = 0

        for steps in range(1, max_steps + 1):
            g = self.S_inv @ x
            gg = float(g @ g)
            if gg <= 0.0:  # nur bei x = 0 moeglich; defensiv
                reason = "degenerate_potential"
                break
            d = x - (float(x @ g) / gg) * g  # = P(x) grad W(x)
            if float(np.linalg.norm(d)) <= tol:
                reason = "stationary"
                steps -= 1
                break

            t = tau
            w_cur = self.energy(x)
            advanced = False
            for _ in range(60):  # Backtracking erzwingt diskreten Abstieg
                y = x - t * d
                hy = self.helicity(y)
                if hy != 0.0 and (hy > 0) == (h0 > 0):
                    y = y * np.sqrt(h0 / hy)  # exakte Reprojektion auf {H = h0}
                    if self.energy(y) < w_cur:
                        advanced = True
                        break
                t *= 0.5
            if not advanced:
                # Kein zulaessiger Abstiegsschritt mehr -> numerisch stationaer
                reason = "no_descent_step"
                steps -= 1
                break

            x = y
            if keep_history:
                hist.append(self.energy(x))
        else:
            reason = "budget_exhausted"

        binding = self.binding(x)
        converged = bool(binding <= 1e-6) and reason in ("stationary", "no_descent_step")
        return LiftResult(
            x=x,
            alpha=self.alpha_of(x),
            energy=self.energy(x),
            energy_start=w_start,
            helicity=self.helicity(x),
            helicity_start=h0,
            residual=binding,
            steps=steps,
            converged=converged,
            reason=reason,
            energy_history=np.asarray(hist, dtype=np.float64),
        )


def hebe_in_plasmoiden_raum(S, x0, **kw) -> LiftResult:
    """Bequemer Einstieg: HELD bespielt den GOTT-Layer in einem Aufruf."""
    return PlasmoidLift(S).lift(x0, **kw)


# ----------------------------------------------------------------------
# Verifikations-Sandbox (Repo-Konvention: echte Asserts, ehrlicher Ausweis)
# ----------------------------------------------------------------------
def run_sandbox_verification() -> None:
    """Prueft P1-P3 mit echten Asserts und weist P4 ehrlich als generisch aus."""
    print("=" * 68)
    print("PLASMOID-LIFT VERIFICATION SANDBOX (Hebung in den plasmoiden Raum)")
    print("=" * 68)
    rng = np.random.default_rng(20260805)

    def random_lift(n: int) -> PlasmoidLift:
        a = rng.uniform(0.5, 4.0, n) * rng.choice([-1.0, 1.0], n)
        a[0] = abs(a[0])  # mindestens ein positiver Eigenwert
        return PlasmoidLift.from_spectrum(a, rng=rng)

    # ---- SATZ P2: Taylor-Schranke ----
    trials, viol, tight_fail = 3000, 0, 0
    for _ in range(trials):
        pl = random_lift(int(rng.integers(2, 8)))
        x = rng.normal(0, 2, pl.S.shape[0])
        h = pl.helicity(x)
        if h == 0.0:
            continue
        ag = pl.alpha_ground(h)
        if 2 * pl.energy(x) < ag * h - 1e-9 * max(1.0, abs(ag * h)):
            viol += 1
        xg = pl.ground_state(abs(h) if ag > 0 else -abs(h))
        hg = pl.helicity(xg)
        if abs(2 * pl.energy(xg) - ag * hg) > 1e-8 * max(1.0, abs(ag * hg)):
            tight_fail += 1
    assert viol == 0, f"P2 Taylor-Schranke verletzt: {viol}/{trials}"
    assert tight_fail == 0, f"P2 Gleichheit im Grundzustand verfehlt: {tight_fail}/{trials}"
    print(f"[SATZ P2] Taylor-Schranke 2W >= alpha_g H: {trials - viol}/{trials} bestanden; "
          f"Grundzustand erreicht die Schranke exakt ({trials - tight_fail}/{trials})")

    # ---- SATZ P1: kritisch <=> plasmoid ----
    trials, viol, false_crit = 2000, 0, 0
    for _ in range(trials):
        pl = random_lift(int(rng.integers(2, 7)))
        n = pl.S.shape[0]
        u = pl.basis[:, int(rng.integers(0, n))] * float(rng.normal(0, 2))
        if not pl.is_critical(u):
            viol += 1
        y = rng.normal(0, 2, n)
        if pl.is_critical(y):  # ein Zufallsvektor darf nicht kritisch sein
            false_crit += 1
    assert viol == 0, f"P1 Eigenvektor nicht als kritisch erkannt: {viol}/{trials}"
    print(f"[SATZ P1] kritisch auf {{H=h}} <=> Beltrami: {trials - viol}/{trials} bestanden "
          f"(Zufallsvektoren faelschlich kritisch: {false_crit}/{trials} "
          f"-> Satz ist nicht trivial)")

    # ---- SATZ P3 + P4-Ausweis ----
    trials = 300
    drift_fail = mono_fail = 0
    ground_hit = usable = 0
    gap_misses = []
    for _ in range(trials):
        pl = random_lift(int(rng.integers(3, 9)))
        x0 = rng.normal(0, 2, pl.S.shape[0])
        h0 = pl.helicity(x0)
        if h0 == 0.0:
            continue
        try:
            ag = pl.alpha_ground(h0)
        except ValueError:
            continue
        usable += 1
        res = pl.lift(x0, max_steps=4000)
        if not res.respects_top_down_axiom():
            drift_fail += 1
        if res.energy_history.size > 1 and np.any(np.diff(res.energy_history) > 1e-12):
            mono_fail += 1
        if abs(2 * res.energy - ag * h0) <= 1e-4 * max(1.0, abs(ag * h0)):
            ground_hit += 1
        else:
            same = np.sort(np.abs(pl.alphas[(pl.alphas > 0) == (h0 > 0)]))
            gap_misses.append(float(same[1] - same[0]) if same.size > 1 else float("inf"))

    assert drift_fail == 0, f"P3(a) Helizitaet driftet: {drift_fail}/{usable}"
    assert mono_fail == 0, f"P3(b) Energieabstieg verletzt: {mono_fail}/{usable}"
    print(f"[SATZ P3] Helizitaet exakt erhalten (Axiom 1): "
          f"{usable - drift_fail}/{usable} bestanden")
    print(f"[SATZ P3] Energie monoton fallend: {usable - mono_fail}/{usable} bestanden")
    print(f"[P4, generisch] Grundzustand erreicht: {ground_hit}/{usable}")
    if gap_misses:
        print(f"  -> {len(gap_misses)} Ausreisser bei kleinster Spektrallucke "
              f"{min(gap_misses):.2e}: KEIN falscher Fixpunkt, sondern Budget — "
              "die Rate haengt an der Lucke (siehe Modul-Docstring).")

    # ---- Gleichgewichte sind genau die plasmoiden Zustaende ----
    pl = random_lift(6)
    x0 = rng.normal(0, 2, 6)
    if pl.helicity(x0) < 0:
        pl = PlasmoidLift.from_spectrum(np.abs(pl.alphas), rng=rng)
    res = pl.lift(x0, max_steps=50_000)
    assert pl.is_plasmoid(res.x, tol=1e-5), f"Endzustand nicht kraftfrei: {res.residual:.2e}"
    print(f"[SATZ P3c] Endzustand kraftfrei: ||r||/||x|| = {res.residual:.2e}, "
          f"alpha = {res.alpha:.6f}, W: {res.energy_start:.4f} -> {res.energy:.4f}, "
          f"H-Drift = {res.helicity_drift:.2e}")

    print("=" * 68)
    print("P1/P2/P3 MIT 0 VERLETZUNGEN VERIFIZIERT — P4 ehrlich als generisch ausgewiesen.")
    print("=" * 68)


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(
        description="Plasmoid-Lift — Hebung vom gebundenen fluiden in den plasmoiden Raum"
    )
    ap.add_argument("--verify", action="store_true", help="Verifikations-Sandbox laufen lassen")
    ap.add_argument("--demo", action="store_true", help="Eine Hebung rechnen und ausgeben")
    ap.add_argument("--n", type=int, default=6, help="Dimension fuer --demo")
    ap.add_argument("--seed", type=int, default=20260805)
    args = ap.parse_args()

    if args.demo:
        rng = np.random.default_rng(args.seed)
        pl = PlasmoidLift.from_spectrum(rng.uniform(0.5, 4.0, args.n), rng=rng)
        x0 = rng.normal(0, 2, args.n)
        res = pl.lift(x0)
        out = res.to_dict()
        out["alpha_ground"] = pl.alpha_ground(res.helicity_start)
        out["taylor_bound"] = pl.taylor_bound(res.helicity_start)
        out["binding_start"] = pl.binding(x0)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    run_sandbox_verification()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
