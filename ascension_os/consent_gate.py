# -*- coding: utf-8 -*-
"""Consent gate for the AscensionOS track.

The Strong Track (Option B) modules touch personal, behavioural and
self-reported clinical-adjacent data (Sisyphos load history, Psycholyse
session logs, social-exposure practice transcripts). Prior to v10 these
operations ran with no consent, vault or audit discipline — unlike the
``fusion_hero_os.meta`` slice.

This module bridges AscensionOS to the existing, tested meta-neural consent
machinery (:mod:`fusion_hero_os.meta.consent`) so that every privileged,
personal-data operation on :class:`~ascension_os.core.ascension_core.AscensionCore`
requires a live, purpose-scoped :class:`ConsentGrant` and emits a
tamper-evident audit event. There is deliberately no bypass path: an
:class:`AscensionCore` constructed without a configured gate **denies**
personal-data operations (fail closed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from fusion_hero_os.meta.consent import (
        ConsentError,
        ConsentStore,
        Purpose,
    )

    _META_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when meta slice absent
    _META_AVAILABLE = False

    class ConsentError(RuntimeError):  # type: ignore[no-redef]
        """Fallback consent error when the meta slice is unavailable."""

if TYPE_CHECKING:  # pragma: no cover
    from fusion_hero_os.meta.consent import ConsentGrant


class AscensionConsentGate:
    """Binds a single subject to the meta :class:`ConsentStore`.

    Personal-data operations map onto the meta slice's closed, benign
    :class:`Purpose` set — no surveillance/profiling purpose exists or is
    added here.
    """

    def __init__(self, store: "ConsentStore", subject_id: str) -> None:
        if not _META_AVAILABLE:
            raise ConsentError(
                "meta consent slice unavailable; cannot construct a consent gate"
            )
        if not subject_id:
            raise ConsentError("subject_id is required (fail closed)")
        self._store = store
        self._subject_id = subject_id

    @property
    def subject_id(self) -> str:
        return self._subject_id

    def require(self, purpose: "Purpose", *, action: str) -> "ConsentGrant":
        """Authorise ``action`` for ``purpose`` or raise :class:`ConsentError`.

        Delegates to :meth:`ConsentStore.authorize`, which appends exactly one
        (granted|denied) audit event and fails closed when no active grant
        exists.
        """
        return self._store.authorize(self._subject_id, purpose, action=action)
