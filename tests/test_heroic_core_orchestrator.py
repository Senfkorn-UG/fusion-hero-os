# -*- coding: utf-8 -*-
"""Tests des Heroic-Core-Orchestrators — seit 2026-07-04 ECHTE Semantik.

Die frueheren Stub-Tests (verify_integrity immer True, Phoenix ohne Reset)
sind ersetzt: diese Tests beweisen die implementierten Eigenschaften und
schlagen fehl, wenn jemand die Implementierung wieder zum Stub degradiert.
"""
import json

import pytest

from fusion_hero_os.core.heroic_core_orchestrator import (
    MasterSeed,
    PMSEvidenceSpine,
    QuadCoreBridge,
)


# ---------------- Layer 0: MasterSeed (echte Integritaetspruefung) ----------

def test_master_seed_verify_integrity_accepts_only_canonical_hash():
    seed = MasterSeed()
    assert seed.verify_integrity(seed.state_hash()) is True
    assert seed.verify_integrity("beliebiger_hash") is False
    assert seed.verify_integrity("") is False
    assert seed.verify_integrity(None) is False  # type: ignore[arg-type]


def test_master_seed_state_hash_is_deterministic_and_tamper_evident():
    a, b = MasterSeed(), MasterSeed()
    assert a.state_hash() == b.state_hash()
    tampered = MasterSeed(criticality_target=0.99)
    assert tampered.state_hash() != a.state_hash()
    # der Original-Hash darf den manipulierten Seed NICHT verifizieren
    assert tampered.verify_integrity(a.state_hash()) is False


def test_master_seed_strict_contraction_check_is_real():
    seed = MasterSeed()
    assert seed.verify_strict_contraction([[0.5, 0.0], [0.0, 0.4]]) is True
    assert seed.verify_strict_contraction([[2.0, 0.0], [0.0, 2.0]]) is False
    assert seed.verify_strict_contraction([[1.0, 0.0]]) is False  # nicht quadratisch


# ---------------- Layer 4: Fail-Closed ohne Kernel ---------------------------

def test_pms_spine_fails_closed_when_kernel_missing():
    spine = PMSEvidenceSpine(executable_path="./definitiv_nicht_vorhanden.exe")
    out = spine.execute_operator_chain("OP_Q_B_CIRC", {"action": "verify_reciprocity"})
    assert out["status"] == "FAIL_CLOSED"


# ---------------- Layer 5: Bridge + echter Phoenix-Reset ---------------------

def test_quad_core_bridge_rejects_invalid_domain():
    bridge = QuadCoreBridge(PMSEvidenceSpine(executable_path="./fehlt.exe"))
    with pytest.raises(ValueError):
        bridge.process_query("CHAOS", "OP_X", {})


def test_phoenix_mode_really_resets_volatile_state():
    bridge = QuadCoreBridge(PMSEvidenceSpine(executable_path="./fehlt.exe"))
    bridge.process_query("MYTHOS", "OP_A", {})
    bridge.process_query("GRUND", "OP_B", {})
    assert len(bridge.volatile_history) == 2 and len(bridge.volatile_cache) == 2
    seed_ok = bridge.invoke_phoenix_mode()
    assert bridge.volatile_history == [] and bridge.volatile_cache == {}
    assert bridge.mode == "PHOENIX"
    assert seed_ok is True  # unversehrter Seed verifiziert sich selbst


# ---------------- Kernel-Integration (nur wenn Binary gebaut) ---------------

_spine = PMSEvidenceSpine()
needs_kernel = pytest.mark.skipif(
    not _spine.available,
    reason="pms_rust_kernel nicht gebaut (cd pms_rust_kernel_crate && cargo build --release)",
)


@needs_kernel
def test_kernel_executes_proven_operator_deterministically(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    payload = {"q1": [[1, 2], [3, 4]], "b1": [[1, 0], [0, 0]],
               "q2": [[0.5, 0.2], [0.1, 0.9]], "b2": [[0, 1], [1, 0]]}
    r1 = spine.execute_operator_chain("OP_TRANSPOSE_RECIPROCITY", payload)
    r2 = spine.execute_operator_chain("OP_TRANSPOSE_RECIPROCITY", payload)
    assert r1["status"] == "SUCCESS" and r1["result"]["holds"] is True
    assert r1 == r2  # Determinismus: identischer Input -> identisches Ergebnis


@needs_kernel
def test_kernel_fail_closed_on_unknown_operator(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    out = spine.execute_operator_chain("OP_EVIL", {})
    assert out["status"] == "FAIL_CLOSED"


@needs_kernel
def test_kernel_fail_closed_on_non_contraction(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    out = spine.execute_operator_chain("OP_BANACH_FIXPOINT",
                                       {"a": [[2, 0], [0, 2]], "c": [1, 1]})
    assert out["status"] == "FAIL_CLOSED"
    assert "Kontraktion" in out["error"]


@needs_kernel
def test_kernel_banach_fixpoint_verified(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    out = spine.execute_operator_chain("OP_BANACH_FIXPOINT",
                                       {"a": [[0.5, 0.1], [0.0, 0.4]], "c": [1, 2]})
    assert out["status"] == "SUCCESS"
    assert out["result"]["verified"] is True
    assert out["result"]["contraction_q"] < 1.0


@needs_kernel
def test_kernel_validates_delta_psi_chain(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    out = spine.validate_chain("CHAIN_DELTA_PSI_PROOF")
    assert out["status"] == "VALID"
    assert "OP_BANACH_FIXPOINT" in out["operators"]
    bad = spine.validate_chain("CHAIN_GIBTS_NICHT")
    assert bad["status"] == "FAIL_CLOSED"


@needs_kernel
def test_kernel_writes_jsonl_audit_trail(tmp_path):
    audit = tmp_path / "audit.jsonl"
    spine = PMSEvidenceSpine(audit_path=str(audit))
    spine.execute_operator_chain("OP_Q_B_CIRC", {"action": "verify_reciprocity"})
    spine.execute_operator_chain("OP_EVIL", {})
    lines = audit.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec_ok, rec_fail = (json.loads(x) for x in lines)
    assert rec_ok["status"] == "SUCCESS" and len(rec_ok["input_sha256"]) == 64
    assert rec_fail["status"].startswith("FAIL_CLOSED")


@needs_kernel
def test_bridge_end_to_end_gestalt_executes_via_kernel(tmp_path):
    spine = PMSEvidenceSpine(audit_path=str(tmp_path / "audit.jsonl"))
    bridge = QuadCoreBridge(spine)
    out = bridge.process_query("GESTALT", "OP_Q_B_CIRC", {"action": "verify_reciprocity"})
    assert out["status"] == "SUCCESS"
    assert out["result"]["holds"] is True
