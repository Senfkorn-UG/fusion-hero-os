"""Ehrliche Regressionstests für core/plasmoid_lift.py.

Verankert wird genau das, was bewiesen UND verifiziert ist:

  * SATZ P1  kritisch auf {H = h}  <=>  Beltrami (kraftfrei)
  * SATZ P2  2W(x) >= alpha_g H(x), Gleichheit nur im Grundzustand
  * SATZ P3  Hebung erhält H exakt, senkt W monoton, Gleichgewichte = P

Ausdrücklich NICHT behauptet wird die universelle Konvergenz in den
Grundzustand (P4): die Gleichgewichtsmenge enthält alle Eigenräume, und die
Konvergenzrate hängt an der Spektrallücke. test_ground_state_is_generic_not_
universal verankert genau diese Einschränkung, damit ein späterer Edit sie
nicht stillschweigend zur Überclaim-Behauptung aufwertet.
"""
import numpy as np
import pytest

from fusion_hero_os.core.plasmoid_lift import (
    GOTT_LAYER_INVARIANT,
    PlasmoidLift,
    hebe_in_plasmoiden_raum,
    run_sandbox_verification,
)


@pytest.fixture
def rng():
    return np.random.default_rng(20260805)


def _lift_with_positive_spectrum(rng, n=6):
    """S mit rein positivem Spektrum -> H(x) > 0 für alle x != 0."""
    return PlasmoidLift.from_spectrum(rng.uniform(0.5, 4.0, n), rng=rng)


# ----------------------------------------------------------------------
# Konstruktion / Vorbedingungen
# ----------------------------------------------------------------------
def test_rejects_asymmetric_operator(rng):
    """Der Curl ist nur auf divergenzfreien Feldern selbstadjungiert —
    ein unsymmetrisches S ist außerhalb des Geltungsbereichs und muss knallen."""
    S = rng.normal(0, 1, (4, 4))
    with pytest.raises(ValueError, match="symmetrisch"):
        PlasmoidLift(S)


def test_rejects_singular_operator():
    """Ohne S^{-1} gibt es kein Potential A und damit keine Helizität."""
    S = np.diag([1.0, 2.0, 0.0])
    with pytest.raises(ValueError, match="singulaer"):
        PlasmoidLift(S)


def test_zero_helicity_has_no_ground_state(rng):
    """H = 0 ist die entartete Niveaufläche — kein Grundzustand, kein Lift."""
    pl = PlasmoidLift.from_spectrum([2.0, -2.0], rng=rng)
    x0 = pl.basis[:, 0] + pl.basis[:, 1]  # H = 1/2 - 1/2 = 0
    assert abs(pl.helicity(x0)) < 1e-12
    with pytest.raises(ValueError, match="entartet"):
        pl.lift(x0)


def test_degeneracy_check_is_scale_invariant(rng):
    """Der Entartungstest muss relativ sein, nicht absolut.

    Regression: ein Test auf `H == 0.0` greift nicht, weil die entartete
    Fläche numerisch ~1e-17 statt exakt 0 liefert — und ein fester absoluter
    Schwellwert würde umgekehrt bei kleiner Skalierung gesunde Zustände
    fälschlich als entartet verwerfen. Beide Richtungen werden hier verankert.
    """
    pl = PlasmoidLift.from_spectrum([2.0, -2.0], rng=rng)
    degenerate = pl.basis[:, 0] + pl.basis[:, 1]

    # entartet bleibt entartet, egal wie skaliert
    for s in (1e-6, 1.0, 1e6):
        assert pl.is_degenerate(degenerate * s), f"Skalierung {s} bricht den Test"
        assert abs(pl.helicity(degenerate * s)) < 1e-9 * max(1.0, s * s)

    # gesunder Zustand bleibt gesund, auch winzig skaliert
    healthy = pl.basis[:, 0]
    for s in (1e-8, 1.0, 1e8):
        assert not pl.is_degenerate(healthy * s), f"Skalierung {s} verwirft fälschlich"
        pl.lift(healthy * s, max_steps=10)  # darf nicht werfen


# ----------------------------------------------------------------------
# SATZ P1
# ----------------------------------------------------------------------
def test_p1_eigenvectors_are_exactly_the_critical_points(rng):
    """SATZ P1: Eigenvektoren sind kritisch, generische Vektoren nicht."""
    for _ in range(200):
        n = int(rng.integers(2, 7))
        pl = PlasmoidLift.from_spectrum(
            rng.uniform(0.5, 4.0, n) * rng.choice([-1.0, 1.0], n), rng=rng
        )
        u = pl.basis[:, int(rng.integers(0, n))] * float(rng.normal(0, 2))
        assert pl.is_critical(u), "Eigenvektor muss kritisch sein"
        assert pl.is_plasmoid(u), "Eigenvektor muss kraftfrei sein"

    # Nicht-trivial: ein generischer Vektor ist NICHT kritisch.
    pl = _lift_with_positive_spectrum(rng, n=5)
    y = rng.normal(0, 2, 5)
    assert not pl.is_critical(y)
    assert pl.binding(y) > 1e-6


# ----------------------------------------------------------------------
# SATZ P2
# ----------------------------------------------------------------------
def test_p2_taylor_bound_holds_universally(rng):
    """SATZ P2: 2W(x) >= alpha_g H(x) für ALLE x — 0 Verletzungen erwartet."""
    viol = 0
    trials = 1500
    for _ in range(trials):
        n = int(rng.integers(2, 8))
        a = rng.uniform(0.5, 4.0, n) * rng.choice([-1.0, 1.0], n)
        a[0] = abs(a[0])
        pl = PlasmoidLift.from_spectrum(a, rng=rng)
        x = rng.normal(0, 2, n)
        h = pl.helicity(x)
        if h == 0.0:
            continue
        ag = pl.alpha_ground(h)
        if 2 * pl.energy(x) < ag * h - 1e-9 * max(1.0, abs(ag * h)):
            viol += 1
    assert viol == 0, f"P2 verletzt in {viol}/{trials} Fällen"


def test_p2_ground_state_attains_the_bound_exactly(rng):
    """SATZ P2 (Gleichheitsfall): der Taylor-Zustand sitzt exakt auf der Schranke."""
    for _ in range(200):
        n = int(rng.integers(2, 7))
        pl = _lift_with_positive_spectrum(rng, n=n)
        h = float(abs(rng.normal(0, 3))) + 0.1
        xg = pl.ground_state(h)
        assert pl.helicity(xg) == pytest.approx(h, rel=1e-9)
        assert pl.energy(xg) == pytest.approx(pl.taylor_bound(h), rel=1e-9)
        assert pl.is_plasmoid(xg), "Grundzustand muss kraftfrei sein"
        assert pl.alpha_of(xg) == pytest.approx(pl.alpha_ground(h), rel=1e-9)


def test_p2_bound_also_holds_for_negative_helicity(rng):
    """Die Schranke ist vorzeichensymmetrisch (Spiegelfall h < 0)."""
    pl = PlasmoidLift.from_spectrum([-3.0, -0.7, 1.2, 2.5], rng=rng)
    for _ in range(300):
        x = rng.normal(0, 2, 4)
        h = pl.helicity(x)
        if h >= 0:
            continue
        ag = pl.alpha_ground(h)
        assert ag < 0, "zu h < 0 gehört ein negativer Grundzustands-alpha"
        assert 2 * pl.energy(x) >= ag * h - 1e-9 * max(1.0, abs(ag * h))


def test_p2_no_ground_state_when_sign_missing(rng):
    """Ohne Eigenwert passenden Vorzeichens existiert kein Grundzustand —
    das muss ein ehrlicher Fehler sein, keine stillschweigende Ersatzantwort."""
    pl = PlasmoidLift.from_spectrum([1.0, 2.0, 3.0], rng=rng)  # rein positiv
    with pytest.raises(ValueError, match="Kein Eigenwert"):
        pl.alpha_ground(-1.0)


# ----------------------------------------------------------------------
# SATZ P3 — die eigentliche Hebung
# ----------------------------------------------------------------------
def test_p3_lift_conserves_helicity_exactly(rng):
    """SATZ P3(a) + Axiom 1: der HELD verändert die Layer-omega-Invariante nicht.

    Das ist die formale Trennlinie zwischen Hebung und Axiombruch.
    """
    for _ in range(60):
        n = int(rng.integers(3, 8))
        pl = _lift_with_positive_spectrum(rng, n=n)
        x0 = rng.normal(0, 2, n)
        res = pl.lift(x0, max_steps=2000)
        assert res.respects_top_down_axiom(), (
            f"Helizitätsdrift {res.helicity_drift:.3e} verletzt Axiom 1"
        )
        assert res.helicity == pytest.approx(res.helicity_start, rel=1e-9)


def test_p3_energy_decreases_monotonically(rng):
    """SATZ P3(b): W fällt monoton — kein Aufschwingen, kein Zurückfallen."""
    for _ in range(40):
        n = int(rng.integers(3, 8))
        pl = _lift_with_positive_spectrum(rng, n=n)
        res = pl.lift(rng.normal(0, 2, n), max_steps=2000)
        diffs = np.diff(res.energy_history)
        assert np.all(diffs <= 1e-12), f"Energie stieg um {diffs.max():.3e}"
        assert res.energy <= res.energy_start + 1e-12


def test_p3_equilibria_are_force_free(rng):
    """SATZ P3(c): der Endzustand der Hebung liegt im plasmoiden Raum."""
    pl = _lift_with_positive_spectrum(rng, n=6)
    res = pl.lift(rng.normal(0, 2, 6), max_steps=50_000)
    assert res.converged, f"nicht konvergiert: reason={res.reason}"
    assert pl.is_plasmoid(res.x, tol=1e-5), f"Bindung ||r||/||x|| = {res.residual:.3e}"
    assert res.residual < pl.binding(np.ones(6)) or res.residual < 1e-5


def test_p3_binding_strictly_decreases_from_fluid_to_plasmoid(rng):
    """Der gebundene fluide Raum wird verlassen: Bindung r(x) geht gegen 0."""
    pl = _lift_with_positive_spectrum(rng, n=5)
    x0 = rng.normal(0, 2, 5)
    binding_start = pl.binding(x0)
    assert binding_start > 1e-6, "Startpunkt muss echt gebunden (nicht plasmoid) sein"
    res = pl.lift(x0, max_steps=50_000)
    assert res.residual < binding_start
    assert res.residual < 1e-5


def test_lift_sets_reason_on_every_exit_path(rng):
    """`reason` wird auf jedem Ausgang gesetzt — auch bei leerem Schleifenrange.

    Regression zu einer CodeQL-Meldung: die Vorbelegung `reason = "stationary"`
    war toter Code, weil alle drei break-Pfade UND das else der Schleife sie
    ohnehin setzen. Sie wurde entfernt; dieser Test verankert, dass dadurch
    kein Pfad ohne `reason` zurückkehrt (sonst: UnboundLocalError).
    """
    pl = _lift_with_positive_spectrum(rng, n=4)
    x0 = rng.normal(0, 2, 4)
    valid = {"stationary", "no_descent_step", "budget_exhausted", "degenerate_potential"}

    # leerer Range: Schleifenkörper läuft nie, das else trägt die Begründung
    res0 = pl.lift(x0, max_steps=0)
    assert res0.reason == "budget_exhausted"
    assert res0.steps == 0
    assert res0.energy == pytest.approx(res0.energy_start, rel=1e-12)

    # Budget erschöpft, stationär erreicht, und ein bereits kraftfreier Start
    for ms in (1, 2, 25, 50_000):
        assert pl.lift(x0, max_steps=ms).reason in valid
    assert pl.lift(pl.ground_state(2.0), max_steps=10).reason in valid


def test_p3_lift_starting_in_plasmoid_space_is_a_no_op(rng):
    """Wer schon kraftfrei ist, wird nicht weiter gehoben (Fixpunkt-Eigenschaft)."""
    pl = _lift_with_positive_spectrum(rng, n=5)
    xg = pl.ground_state(2.0)
    res = pl.lift(xg, max_steps=1000)
    assert res.steps == 0
    assert res.reason in ("stationary", "no_descent_step")
    assert res.energy == pytest.approx(pl.energy(xg), rel=1e-12)


# ----------------------------------------------------------------------
# P4 — ehrliche Einschränkung
# ----------------------------------------------------------------------
def test_p4_reaches_taylor_bound_for_well_separated_spectrum(rng):
    """Bei klarer Spektrallücke landet die Hebung im Grundzustand (generisch)."""
    pl = PlasmoidLift.from_spectrum([1.0, 2.5, 4.0, 6.0], rng=rng)
    for _ in range(25):
        x0 = rng.normal(0, 2, 4)
        h0 = pl.helicity(x0)
        res = pl.lift(x0, max_steps=50_000)
        assert res.energy == pytest.approx(pl.taylor_bound(h0), rel=1e-5)
        assert res.alpha == pytest.approx(pl.alpha_ground(h0), rel=1e-5)


def test_p4_is_not_a_universal_law_all_eigenspaces_are_equilibria(rng):
    """P4 ist KEIN Satz: jeder Eigenraum ist Gleichgewicht, nicht nur der Grundzustand.

    Startet man exakt in einem höheren Eigenraum, bleibt die Hebung dort
    stehen — der Energiewert liegt dann strikt ÜBER der Taylor-Schranke.
    Dieser Test verankert die Einschränkung bewusst als Negativ-Referenz.
    """
    pl = PlasmoidLift.from_spectrum([1.0, 2.5, 4.0, 6.0], rng=rng)
    idx_high = int(np.argmax(pl.alphas))
    x0 = pl.basis[:, idx_high] * 1.7
    h0 = pl.helicity(x0)

    res = pl.lift(x0, max_steps=10_000)
    assert res.steps == 0, "ein Eigenraum ist bereits Gleichgewicht"
    assert res.energy > pl.taylor_bound(h0) * (1 + 1e-6), (
        "höherer Eigenraum liegt strikt über der Taylor-Schranke — "
        "die Hebung findet von dort aus den Grundzustand NICHT"
    )
    # Die Schranke selbst bleibt natürlich gültig:
    assert 2 * res.energy >= pl.alpha_ground(h0) * h0 - 1e-9


# ----------------------------------------------------------------------
# Kontrakt / Integration
# ----------------------------------------------------------------------
def test_gott_layer_invariant_is_helicity():
    """Der Vertrag mit dem Gott-Layering: die top-down gesetzte Größe ist H."""
    assert GOTT_LAYER_INVARIANT == "helicity"


def test_convenience_wrapper_matches_class_api(rng):
    pl = _lift_with_positive_spectrum(rng, n=4)
    x0 = rng.normal(0, 2, 4)
    a = pl.lift(x0, max_steps=500)
    b = hebe_in_plasmoiden_raum(pl.S, x0, max_steps=500)
    assert b.energy == pytest.approx(a.energy, rel=1e-12)
    assert b.helicity == pytest.approx(a.helicity, rel=1e-12)


def test_result_to_dict_is_json_serialisable(rng):
    import json

    pl = _lift_with_positive_spectrum(rng, n=4)
    res = pl.lift(rng.normal(0, 2, 4), max_steps=500)
    payload = json.loads(json.dumps(res.to_dict()))
    assert payload["top_down_axiom_ok"] is True
    assert set(payload) >= {"alpha", "energy", "helicity", "residual", "reason"}


def test_module_docstring_flags_plasma_reading_as_model():
    """Code-Honesty: die Plasma-Deutung darf nicht als Physik-Claim auftreten."""
    from fusion_hero_os.core import plasmoid_lift

    doc = plasmoid_lift.__doc__ or ""
    assert "MODELL" in doc and "Analogie" in doc
    assert "SATZ P4" in doc, "die Einschränkung zu P4 muss im Docstring stehen"


def test_sandbox_verification_runs_green(capsys):
    """Die Sandbox ist ein CI-Gate: sie muss mit 0 Verletzungen durchlaufen."""
    run_sandbox_verification()
    out = capsys.readouterr().out
    assert "MIT 0 VERLETZUNGEN VERIFIZIERT" in out
