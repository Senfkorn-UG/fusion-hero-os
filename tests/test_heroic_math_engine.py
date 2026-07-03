# -*- coding: utf-8 -*-
"""Regressionstests der vier bewiesenen Knoten-Saetze (K16/K17/K19/K20).

Jeder Test prueft den Satz ueber einen Zufalls-Sweep mit 0-Verletzungs-
Anspruch — schlaegt ein kuenftiger Umbau die Mathematik kaputt, faellt das
hier auf, nicht erst in einer Doku-Behauptung.
"""
import numpy as np
import pytest

from fusion_hero_os.core.heroic_math_engine import (
    BanachContractionSeed,
    HeroicMatrixEngine,
    OrthogonalProjector,
    RepairedStructureIP,
    run_sandbox_verification,
)

rng = np.random.default_rng(424242)


def test_k16_transpose_reciprocity_universal():
    """SATZ: Q1B1B2Q2 = (Q2^T B2^T B1^T Q1^T)^T fuer alle reellen Matrizen."""
    eng = HeroicMatrixEngine()
    for _ in range(500):
        n = int(rng.integers(2, 6))
        q1, b1, b2, q2 = (rng.normal(0, 2, (n, n)) for _ in range(4))
        assert eng.check_transpose_reciprocity(q1, b1, b2, q2)


def test_k16_naive_form_is_not_a_theorem():
    """Die historische naive Form ist KEIN Satz: Zufallsmatrizen verletzen sie."""
    eng = HeroicMatrixEngine()
    holds = sum(
        eng.check_reciprocity_condition(*(rng.normal(0, 2, (3, 3)) for _ in range(4)))
        for _ in range(200)
    )
    assert holds < 5  # praktisch nie erfuellt -> Negativ-Referenz bleibt ehrlich


def test_k17_projector_properties():
    """SATZ: P = UU^T ist idempotent, symmetrisch, Spektrum in {0,1}, nicht-expansiv."""
    for _ in range(300):
        n = int(rng.integers(2, 7))
        k = int(rng.integers(1, n + 1))
        proj = OrthogonalProjector(rng.normal(0, 1, (n, k)))
        v = rng.normal(0, 1, n)
        assert proj.is_idempotent()
        assert proj.is_symmetric()
        assert proj.spectrum_in_01()
        assert proj.is_nonexpansive_for(v)


def test_k19_monotone_fusion_in_proven_domain():
    """SATZ (bedingt): S(fused) >= max(S(psi), S(phi)) unter (i)+(ii), eta=0."""
    checked = 0
    for _ in range(3000):
        lm = float(rng.uniform(0, 3))
        sysm = RepairedStructureIP(lmbda=lm)
        a = float(rng.uniform(-3, 3))
        c = np.sign(a) * abs(float(rng.uniform(0, 3)))
        b = float(rng.uniform(-3, 3))
        if abs(b) < 1e-6:
            continue
        d = b * float(rng.uniform(0.5, 2.0))
        p, q = complex(a, b), complex(c, d)
        if not sysm.check_monotone_domain(p, q):
            continue
        checked += 1
        sf = sysm.compute_stability(sysm.fusion_operator(p, q))
        assert sf >= max(sysm.compute_stability(p), sysm.compute_stability(q)) - 1e-9
    assert checked > 200  # der Sweep muss den bewiesenen Bereich real abdecken


def test_k19_eta_leaves_proven_domain():
    """eta != 0 liegt ausserhalb des Satzes: check_monotone_domain lehnt ab."""
    sysm = RepairedStructureIP(lmbda=0.5, eta=1.5)
    assert not sysm.check_monotone_domain(complex(2, -1), complex(1.5, -0.5))


def test_k19_negative_lambda_rejected():
    with pytest.raises(ValueError):
        RepairedStructureIP(lmbda=-0.1)


def test_k20_banach_fixpoint_and_geometric_convergence():
    """SATZ: ||A||<1 => eindeutiger Fixpunkt + Schranke q^k*d0 haelt jeden Schritt."""
    for _ in range(150):
        n = int(rng.integers(2, 6))
        M = rng.normal(0, 1, (n, n))
        q = float(rng.uniform(0.1, 0.9))
        seed = BanachContractionSeed(M * (q / np.linalg.norm(M, 2)), rng.normal(0, 1, n))
        x0 = rng.normal(0, 5, n)
        assert seed.verify_contraction_bound(x0, n_steps=40)
        x_end, _ = seed.iterate(x0, tol=1e-8)
        assert np.linalg.norm(x_end - seed.fixpoint()) <= 1e-6


def test_k20_non_contraction_rejected():
    with pytest.raises(ValueError):
        BanachContractionSeed(np.eye(3) * 1.5, np.zeros(3))


def test_sandbox_verification_runs_clean():
    """Das CI-Gate (python -m ...heroic_math_engine) muss mit 0 Asserts durchlaufen."""
    run_sandbox_verification()
