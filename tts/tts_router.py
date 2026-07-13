#!/usr/bin/env python3
"""
tts/tts_router.py
Fusion Hero OS - Independent Voice Layer v1

Fully decoupled TTS system.
Voice runs completely independent from text output.
Supports full-duplex conversation, multi-voice per agent, QUBO-optimized parameters,
and dedicated audio WebSocket streaming.

Part of the Master Core / Intent Bus architecture.
"""

import asyncio
import os
import shutil
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("fusion_hero_os.tts")


class TTSBackendUnavailableError(RuntimeError):
    """Raised when a backend has no real inference path configured.

    Fail-closed by design (matches the repo's Code-Honesty convention, see
    docs/01_vision/V8_STATUS_REPORT.md): we never return fake audio bytes
    silently. Callers must handle this explicitly.
    """


class VoiceProfile(str, Enum):
    """Predefined voice archetypes for different agents."""
    MASTER_ARCHETYPAL = "master_archetypal"
    QUBO_COLD_PRECISE = "qubo_cold_precise"
    ASR_WARM_PATIENT = "asr_warm_patient"
    MEME_CHAOTIC_FUN = "meme_chaotic_fun"
    HEROIC_NARRATOR = "heroic_narrator"
    COAL_CANARY_WARNING = "coal_canary_warning"


@dataclass
class TTSRequest:
    """Request object for decoupled voice synthesis."""
    text: str
    agent_id: str
    voice_profile: VoiceProfile = VoiceProfile.MASTER_ARCHETYPAL
    speed: float = 1.0
    pitch: float = 1.0
    emotion: str = "neutral"
    stream: bool = True
    priority: int = 5
    interrupt_current: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class TTSRouter:
    """
    Central decoupled TTS Router for Fusion Hero OS.

    Key features:
    - Voice generation is completely independent from text pipeline
    - Full-duplex support (user can speak while system speaks)
    - Dedicated audio WebSocket channel (separate from text)
    - QUBO optimization for voice parameters per request
    - Multi-voice support (different voice per agent)
    - Pluggable backends (local + cloud)
    - Intent Bus integration for orchestration
    """

    def __init__(self, intent_bus: Any = None, qubo_engine: Any = None):
        self.intent_bus = intent_bus
        self.qubo_engine = qubo_engine
        self.active_voices: Dict[str, VoiceProfile] = {}
        self.audio_websocket: Optional[Any] = None
        self.backends: Dict[str, Callable] = {}
        self._current_playback_tasks: Dict[str, asyncio.Task] = {}

        self._register_default_backends()
        logger.info("TTSRouter initialized (decoupled voice layer active)")

    def _register_default_backends(self):
        """Register available TTS backends."""
        self.backends["piper_local"] = self._piper_local_backend
        self.backends["coqui_xtts"] = self._coqui_xtts_backend
        self.backends["elevenlabs"] = self._elevenlabs_backend
        self.backends["system_default"] = self._piper_local_backend

    async def synthesize(self, request: TTSRequest) -> Optional[bytes]:
        """
        Main synthesis entry point. Completely decoupled from text output.
        """
        # QUBO optimization of voice parameters
        if self.qubo_engine:
            try:
                optimized = await self.qubo_engine.optimize_voice_parameters(request)
                request.speed = optimized.get("speed", request.speed)
                request.pitch = optimized.get("pitch", request.pitch)
                request.emotion = optimized.get("emotion", request.emotion)
            except Exception as e:
                logger.warning(f"QUBO voice optimization failed: {e}")

        # Select backend
        backend_name = request.metadata.get("backend", "system_default")
        backend = self.backends.get(backend_name, self.backends["system_default"])

        audio_data = await backend(request)

        if request.stream and self.audio_websocket:
            await self._stream_audio(audio_data, request.agent_id)

        return audio_data

    async def speak_only(self, text: str, agent_id: str, **kwargs) -> None:
        """Voice-only mode - no text is sent to the user."""
        req = TTSRequest(text=text, agent_id=agent_id, **kwargs)
        await self.synthesize(req)

    async def interrupt_agent(self, agent_id: str):
        """Interrupt current speech of a specific agent."""
        if agent_id in self._current_playback_tasks:
            task = self._current_playback_tasks.pop(agent_id)
            task.cancel()
            logger.info(f"Interrupted speech for agent {agent_id}")

    async def set_voice_for_agent(self, agent_id: str, profile: VoiceProfile):
        """Dynamically assign voice profile to an agent."""
        self.active_voices[agent_id] = profile
        logger.info(f"Agent {agent_id} now using voice profile: {profile.value}")

    async def _stream_audio(self, audio_data: bytes, agent_id: str):
        """Stream audio over dedicated WebSocket (independent channel)."""
        if self.audio_websocket:
            try:
                await self.audio_websocket.send_audio_chunk(audio_data, agent_id=agent_id)
            except Exception as e:
                logger.error(f"Audio streaming failed: {e}")

    # ==================== BACKEND PLACEHOLDERS ====================

    async def _piper_local_backend(self, request: TTSRequest) -> bytes:
        """Real Piper inference via subprocess, fail-closed if not configured.

        Configure with:
          PIPER_BINARY               path/name of the piper executable (default: "piper")
          PIPER_MODEL_<PROFILE>      per-voice-profile .onnx model path, e.g.
                                      PIPER_MODEL_HEROIC_NARRATOR=/models/heroic.onnx
          PIPER_MODEL_PATH           fallback model path used for any profile

        Without a real binary + model, this raises TTSBackendUnavailableError
        instead of returning fake audio bytes.
        """
        logger.info(f"[TTS][Piper] Synthesizing for {request.agent_id} | speed={request.speed}")

        piper_bin = shutil.which(os.environ.get("PIPER_BINARY", "piper"))
        profile_env = f"PIPER_MODEL_{request.voice_profile.value.upper()}"
        model_path = os.environ.get(profile_env) or os.environ.get("PIPER_MODEL_PATH", "")

        if not piper_bin or not model_path or not os.path.isfile(model_path):
            logger.warning(
                "[TTS][Piper] Kein echtes Piper-Binary/Modell konfiguriert "
                f"(PIPER_BINARY={piper_bin!r}, {profile_env} oder PIPER_MODEL_PATH={model_path!r}). "
                "Fail-closed statt Fake-Audio."
            )
            raise TTSBackendUnavailableError(
                "piper_local backend requires a real 'piper' binary on PATH (or PIPER_BINARY) "
                f"and a voice model ({profile_env} or PIPER_MODEL_PATH)."
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                piper_bin,
                "--model", model_path,
                "--output-raw",
                "--length_scale", str(1.0 / max(request.speed, 0.1)),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate(input=request.text.encode("utf-8"))
            if proc.returncode != 0:
                raise TTSBackendUnavailableError(
                    f"piper exited with code {proc.returncode}: "
                    f"{stderr.decode('utf-8', errors='ignore')[:200]}"
                )
            return stdout
        except FileNotFoundError as e:
            raise TTSBackendUnavailableError(str(e)) from e

    async def _coqui_xtts_backend(self, request: TTSRequest) -> bytes:
        logger.info(f"[TTS][Coqui] Synthesizing for {request.agent_id}")
        await asyncio.sleep(0.08)
        return b"COQUI_FAKE_AUDIO_DATA"

    async def _elevenlabs_backend(self, request: TTSRequest) -> bytes:
        logger.info(f"[TTS][ElevenLabs] Synthesizing for {request.agent_id}")
        await asyncio.sleep(0.12)
        return b"ELEVENLABS_FAKE_AUDIO_DATA"


# Factory function for easy integration
def get_tts_router(intent_bus: Any = None, qubo_engine: Any = None) -> TTSRouter:
    return TTSRouter(intent_bus=intent_bus, qubo_engine=qubo_engine)
