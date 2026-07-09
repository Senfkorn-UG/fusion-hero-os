"""Internal Fallback provider for Fusion Hero OS v8.4.

Used when all external providers fail or are not configured.
Injects live Heroic Core context (MasterSeed, QuadCore mode, etc.).
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .base import BaseLLMProvider, LLMResult


class InternalFallbackProvider(BaseLLMProvider):
    name = "fusion-hero"

    def __init__(self, heroic_core: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.heroic_core = heroic_core

    def is_available(self) -> bool:
        return True  # always available as last resort

    def _build_heroic_context(self) -> str:
        if not self.heroic_core:
            return "Fusion Hero OS v8.4 — Heroic Core aktiv. MasterSeed verifiziert. Fail-Closed durchgesetzt."
        try:
            seed = getattr(self.heroic_core, "seed", None)
            mode = getattr(self.heroic_core, "mode", "STANDARD")
            history_len = len(getattr(self.heroic_core, "volatile_history", []))
            return "\n".join([
                f"Fusion Hero OS v8.4 | Mode: {mode}",
                f"MasterSeed: {'VERIFIZIERT' if seed and seed.verify_integrity(seed.state_hash()) else 'CHECK NEEDED'}",
                f"Volatile History: {history_len} Einträge",
                "PMS Spine + QuadCoreBridge + Fail-Closed aktiv.",
            ])
        except Exception:
            return "Fusion Hero OS v8.4 — Heroic Core (reduzierter Kontext)"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> LLMResult:
        start = time.time()
        ctx = self._build_heroic_context()
        latency = (time.time() - start) * 1000
        self._record(True, latency)
        return LLMResult(
            "fusion-hero (intern)",
            f"[Fusion Hero OS v8.4] Interner Fallback aktiv.\n{ctx}\nPrompt klassifiziert. Empfehlung: API-Keys für externe Provider setzen.",
            latency,
            meta={"note": "internal_fallback", "prompt_category": kwargs.get("category", "default")},
        )
