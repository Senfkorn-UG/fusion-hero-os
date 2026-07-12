"""Tests fuer den echten (fail-closed) Piper-Backend-Pfad in tts/tts_router.py.

Ersetzt den vorherigen TODO-Stub, der stillschweigend b"PIPER_FAKE_AUDIO_DATA"
zurueckgab. Der neue Pfad ruft ein echtes 'piper'-Binary auf, wenn konfiguriert,
und schlaegt sonst explizit (fail-closed) fehl - konsistent mit der
Code-Honesty-Konvention des Repos (docs/01_vision/V8_STATUS_REPORT.md).

Kein pytest-asyncio im Repo vorhanden -> Tests treiben die Coroutinen selbst
per asyncio.run(), wie an anderer Stelle im Projekt ueblich.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tts"))

from tts_router import TTSBackendUnavailableError, TTSRequest, TTSRouter, VoiceProfile  # noqa: E402


def test_piper_backend_fails_closed_without_binary_or_model(monkeypatch):
    monkeypatch.delenv("PIPER_MODEL_PATH", raising=False)
    monkeypatch.delenv("PIPER_MODEL_MASTER_ARCHETYPAL", raising=False)
    monkeypatch.setenv("PIPER_BINARY", "definitely-not-a-real-piper-binary")

    router = TTSRouter()
    request = TTSRequest(text="Hallo Welt", agent_id="test-agent")

    with pytest.raises(TTSBackendUnavailableError):
        asyncio.run(router._piper_local_backend(request))


def test_piper_backend_never_returns_fake_audio_marker(monkeypatch):
    """Regression guard: no code path may silently return the old fake bytes."""
    monkeypatch.delenv("PIPER_MODEL_PATH", raising=False)
    monkeypatch.setenv("PIPER_BINARY", "definitely-not-a-real-piper-binary")

    router = TTSRouter()
    request = TTSRequest(text="Test", agent_id="test-agent", voice_profile=VoiceProfile.HEROIC_NARRATOR)

    try:
        result = asyncio.run(router._piper_local_backend(request))
    except TTSBackendUnavailableError:
        result = None

    assert result != b"PIPER_FAKE_AUDIO_DATA"


def test_voice_profile_env_var_naming_convention():
    """PIPER_MODEL_<PROFILE> must match the uppercased enum value used by the backend."""
    assert VoiceProfile.HEROIC_NARRATOR.value.upper() == "HEROIC_NARRATOR"
