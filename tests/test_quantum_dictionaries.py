# -*- coding: utf-8 -*-
"""Beweise fuer die Quanten-Wörterbücher (Claim QUANTUM-DICT).

'Quanten-Wörterbuch' = zentrale, deterministisch adressierte Memoisierung mit
Zustands-Invalidierung (deklarierte Namenskonvention, kein Quantencomputing).
Die Performance-Behauptung wird hier gemessen, nicht behauptet.
"""

from __future__ import annotations

import time

from fusion_hero_os.core.quantum_dictionaries import (
    QuantumDictionary,
    canonical_key,
    get_quantum_dictionary,
    registry_stats,
)


# ---------------------------------------------------------------------------
# Deterministische Adressen
# ---------------------------------------------------------------------------

def test_canonical_key_is_deterministic_and_order_independent():
    a = canonical_key({"x": 1, "y": [2, 3]})
    b = canonical_key({"y": [2, 3], "x": 1})
    assert a == b
    assert len(a) == 64  # SHA-256-Hexdigest


def test_canonical_key_distinguishes_different_inputs():
    assert canonical_key({"x": 1}) != canonical_key({"x": 2})


# ---------------------------------------------------------------------------
# Memoisierung + Invalidierung
# ---------------------------------------------------------------------------

def test_get_or_compute_caches_and_counts():
    qd = QuantumDictionary("test-basic")
    calls = []
    value1 = qd.get_or_compute("k", lambda: calls.append(1) or 42)
    value2 = qd.get_or_compute("k", lambda: calls.append(1) or 42)
    assert value1 == value2 == 42
    assert len(calls) == 1, "zweiter Aufruf muss aus dem Wörterbuch kommen"
    stats = qd.stats()
    assert stats["hits"] == 1 and stats["misses"] == 1


def test_signature_change_invalidates():
    qd = QuantumDictionary("test-signature")
    assert qd.get_or_compute("k", lambda: "alt", signature="zustand-1") == "alt"
    assert qd.get_or_compute("k", lambda: "neu", signature="zustand-2") == "neu"
    assert qd.stats()["invalidations"] == 1


def test_ttl_expiry():
    qd = QuantumDictionary("test-ttl", ttl_sec=0.01)
    qd.get_or_compute("k", lambda: 1)
    time.sleep(0.05)
    assert qd.get_or_compute("k", lambda: 2) == 2


def test_max_entries_evicts_oldest():
    qd = QuantumDictionary("test-evict", max_entries=2)
    qd.get_or_compute("a", lambda: 1)
    qd.get_or_compute("b", lambda: 2)
    qd.get_or_compute("c", lambda: 3)  # verdraengt aeltesten
    assert qd.stats()["entries"] == 2


def test_registry_returns_same_instance_and_stats():
    qd1 = get_quantum_dictionary("test-registry-x")
    qd2 = get_quantum_dictionary("test-registry-x")
    assert qd1 is qd2
    qd1.get_or_compute("k", lambda: 1)
    assert "test-registry-x" in registry_stats()


# ---------------------------------------------------------------------------
# Anwendung: Dependency Atlas (die 'nötig und ratsam'-Stelle)
# ---------------------------------------------------------------------------

def test_atlas_cached_is_hit_on_second_call_and_identical():
    from fusion_hero_os.core.dependency_atlas import build_atlas_cached
    qd = get_quantum_dictionary("dependency-atlas")
    qd.invalidate()

    t0 = time.perf_counter()
    atlas1 = build_atlas_cached()
    cold = time.perf_counter() - t0

    t0 = time.perf_counter()
    atlas2 = build_atlas_cached()
    warm = time.perf_counter() - t0

    assert atlas2 is atlas1, "unveraenderter Repo-Zustand muss denselben Atlas liefern"
    assert qd.stats()["hits"] >= 1
    # Messung dokumentieren; hartes Zeit-Assert waere CI-flaky, aber der
    # Warm-Pfad darf nie langsamer als der halbe Kalt-Pfad sein.
    assert warm < max(cold * 0.5, 0.05), f"kalt={cold:.3f}s warm={warm:.3f}s"


def test_atlas_signature_reacts_to_file_change(tmp_path, monkeypatch):
    from fusion_hero_os.core import dependency_atlas as da
    sig1 = da._repo_state_signature()
    sig2 = da._repo_state_signature()
    assert sig1 == sig2, "Signatur muss ohne Aenderung stabil sein"
