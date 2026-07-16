# -*- coding: utf-8 -*-
"""Consent gating for the AscensionOS Strong Track (v10 Stage-A).

Verifies that personal-data operations on AscensionCore fail closed without a
consent gate, are authorised with a live grant, and that every decision is
recorded on the tamper-evident meta audit log.
"""

import pytest

from fusion_hero_os.meta.consent import ConsentError, ConsentStore, Purpose
from ascension_os.consent_gate import AscensionConsentGate
from ascension_os.core.ascension_core import AscensionCore

SUBJECT = "subject-opaque-1"


def test_personal_data_op_denied_without_gate():
    core = AscensionCore()  # no gate -> fail closed
    with pytest.raises(ConsentError):
        core.step_sisyphos(0.5, notes="should be denied")
    with pytest.raises(ConsentError):
        core.log_psycholyse_session("reflection", "self_reported")
    with pytest.raises(ConsentError):
        core.ask("hello")


def test_personal_data_op_allowed_with_active_grant():
    store = ConsentStore()
    store.grant(SUBJECT, Purpose.PERSISTENCE)
    gate = AscensionConsentGate(store, SUBJECT)
    core = AscensionCore(consent_gate=gate)
    # With a live grant the consent check passes; the underlying component may
    # be unavailable in the test environment, in which case the method returns
    # gracefully (None / status) rather than raising ConsentError.
    result = core.step_sisyphos(0.5, notes="granted")
    assert result is None or isinstance(result, dict)
    # A denied event is produced for a purpose that was never granted.
    with pytest.raises(ConsentError):
        core.ask("needs association purpose, not granted")


def test_denial_is_audited():
    store = ConsentStore()
    gate = AscensionConsentGate(store, SUBJECT)
    core = AscensionCore(consent_gate=gate)
    before = len(store.audit)
    with pytest.raises(ConsentError):
        core.step_sisyphos(0.5)
    events = store.audit.events_for(SUBJECT)
    assert any(e.decision == "denied" and e.action == "ascension.step_sisyphos"
               for e in events)
    assert len(store.audit) == before + 1
    assert store.audit.verify() is True


def test_gate_requires_subject_and_meta():
    store = ConsentStore()
    with pytest.raises(ConsentError):
        AscensionConsentGate(store, "")
