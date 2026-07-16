"""Ehrliche Regressionstests für core/heroic_math_engine.py.

Diese Tests behaupten NICHT, dass Knoten 16 (Reziprozität) oder Knoten 19
(Monotonie) universell bewiesene mathematische Gesetze sind - beide sind
laut Modul-Docstring als FRAGMENT bzw. MODELL eingestuft. Stattdessen wird
genau das verankert, was tatsächlich verifiziert wurde, damit ein künftiger
Edit nicht stillschweigend wieder in eine Überclaim-Behauptung zurückfällt.
"""
import numpy as np
import pytest

from fusion_hero_os.core.heroic_math_engine import (
    HeroicMatrixEngine,
    RepairedStructureIP,
    OrthogonalProjector,
    BanachContractionSeed,
)


def test_commutator_is_antisymmetric():
    """Knoten 1: [Q,B] = -[B,Q] ist reine lineare Algebra, keine Sonderbehauptung."""
    engine = HeroicMatrixEngine()
    comm_qb = engine.compute_commutator(engine.q_default, engine.b_default)
    comm_bq = engine.compute_commutator(engine.b_default, engine.q_default)
    assert np.allclose(comm_qb, -comm_bq)


def test_reciprocity_holds_only_in_trivial_case():
    """Knoten 16 (FRAGMENT): reziprok NUR wenn Q1==Q2 - keine universelle Reziprozität."""
    engine = HeroicMatrixEngine()
    m1 = np.array([[0.5, 0.2], [0.1, 0.9]])
    m2 = np.array([[0.8, -0.3], [0.4, 0.2]])

    assert engine.check_reciprocity_condition(m1, engine.b_default, m1, engine.b_default) is True

    # Auch mit zwei echten Rotationsmatrizen (nicht nur generischen) gilt es NICHT
    # für Q1 != Q2 - das ist der dokumentierte, verifizierte Fragment-Status.
    def rot(phi):
        return np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])

    assert engine.check_reciprocity_condition(m1, engine.b_default, m2, engine.b_default) is False
    assert engine.check_reciprocity_condition(rot(0.3), engine.b_default, rot(0.9), engine.b_default) is False


def test_monotonicity_documented_example_holds():
    """Knoten 19 (MODELL): das im Modul dokumentierte Beispiel muss weiterhin halten."""
    ip = RepairedStructureIP(lmbda=0.5, eta=1.5)
    psi, phi = complex(2.0, -1.0), complex(1.5, -0.5)
    s_psi, s_phi = ip.compute_stability(psi), ip.compute_stability(phi)
    s_fused = ip.compute_stability(ip.fusion_operator(psi, phi))
    assert s_fused >= max(s_psi, s_phi)


def test_monotonicity_is_not_a_universal_law():
    """Knoten 19 (MODELL): Verletzungsrate bleibt in einer erwartbaren Größenordnung.

    Kein Beweis für 0% - im Gegenteil, dieser Test verankert, dass es KEIN
    universelles Gesetz ist (per Sweep beobachtete Rate ~10-40%). Schlägt nur
    fehl, wenn sich das grundlegende Verhalten der Formel unerwartet ändert.
    """
    ip = RepairedStructureIP(lmbda=0.5, eta=1.5)
    rng = np.random.default_rng(42)
    tested = violations = 0
    for _ in range(500):
        p = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        q = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        if not ip.check_compatibility(p, q):
            continue
        tested += 1
        sp, sq = ip.compute_stability(p), ip.compute_stability(q)
        sf = ip.compute_stability(ip.fusion_operator(p, q))
        if sf < max(sp, sq) - 1e-9:
            violations += 1
    assert tested > 100, "Sweep sollte genug kompatible Paare finden, um aussagekräftig zu sein"
    rate = violations / tested
    assert 0.05 < rate < 0.60, (
        f"Verletzungsrate {rate:.1%} liegt außerhalb der erwarteten Fragment-Bandbreite - "
        "entweder wurde die Formel echt repariert (Docstring aktualisieren!) oder "
        "etwas anderes hat sich unerwartet geändert."
    )


def test_k17_orthogonal_projector_properties():
    """Knoten 17 — SATZ: Orthogonalprojektor idempotent/symmetrisch/Spektrum/nicht-expansiv."""
    rng = np.random.default_rng(17)
    for _ in range(80):
        n = int(rng.integers(2, 7))
        k = int(rng.integers(1, n + 1))
        proj = OrthogonalProjector(rng.normal(0, 1, (n, k)))
        v = rng.normal(0, 1, n)
        assert proj.is_idempotent()
        assert proj.is_symmetric()
        assert proj.spectrum_in_01()
        assert proj.is_nonexpansive_for(v)


def test_k20_banach_contraction_fixed_point():
    """Knoten 20 — SATZ: Banach-Kontraktion hat Fixpunkt und geometrische Konvergenz."""
    rng = np.random.default_rng(20)
    for _ in range(40):
        n = int(rng.integers(2, 6))
        M = rng.normal(0, 1, (n, n))
        q = float(rng.uniform(0.1, 0.9))
        # scale to spectral radius < q < 1
        svals = np.linalg.svd(M, compute_uv=False)
        scale = (q * 0.99) / (svals[0] + 1e-12)
        A = M * scale
        c = rng.normal(0, 1, n)
        banach = BanachContractionSeed(A, c)
        x0 = rng.normal(0, 1, n)
        assert banach.verify_contraction_bound(x0, n_steps=30)
        x_star = banach.fixpoint()
        x, _ = banach.iterate(x0, max_steps=200)
        assert np.linalg.norm(x - x_star) < 1e-6


def test_module_docstring_does_not_use_blanket_repair_claim():
    """Wächter: keine pauschale 'Repariert alle Knoten'-Phrase ohne Geltung."""
    import fusion_hero_os.core.heroic_math_engine as mod

    doc = (mod.__doc__ or "").lower()
    assert "repariert zentrale mathematische schwächen (knoten 16, 17, 19, 20)" not in doc
    # K17/K20 are implemented as SATZ — must not claim "nicht implementiert" anymore
    assert "knoten 17" in doc and "satz" in doc
    assert "knoten 20" in doc
