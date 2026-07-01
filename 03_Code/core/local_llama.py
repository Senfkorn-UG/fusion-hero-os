# local_llama.py — Lokales Llama nach Heroic-Training

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_LLM_ROOT = Path(__file__).parent.parent / "internal_llm"
_CONFIG = _LLM_ROOT / "output" / "heroic_llama_config.json"
_MODEL = _LLM_ROOT / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf"


class LocalLlama:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.active = False
        self._reload()

    def _reload(self) -> None:
        if _CONFIG.exists():
            try:
                self.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
                self.active = True
            except Exception:
                self.config = {}
                self.active = False
        else:
            self.active = _MODEL.exists()

    def status(self) -> Dict[str, Any]:
        self._reload()
        gen = self.config.get("generation", {})
        return {
            "active": self.active,
            "backend": os.getenv("FUSION_LLM_BACKEND", "llama-local" if self.active else "grok-intern"),
            "model_path": str(_MODEL) if _MODEL.exists() else None,
            "config_path": str(_CONFIG) if _CONFIG.exists() else None,
            "algorithm": self.config.get("algorithm"),
            "generation": gen,
            "gpu_layers": int(os.getenv("FUSION_LLAMA_GPU_LAYERS", "25")),
        }

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if str(_LLM_ROOT) not in sys.path:
            sys.path.insert(0, str(_LLM_ROOT))
        from llama_cli_backend import generate as cli_generate  # type: ignore

        cfg = self.config
        gen = cfg.get("generation", {})
        sys_prompt = system or cfg.get("system_prompt", "Du bist ALTE_Frau_95g Heroic Core.")
        full = f"<|system|>\n{sys_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
        model = cfg.get("model_path") or str(_MODEL)
        if not Path(model).exists():
            raise FileNotFoundError(f"Modell fehlt: {model}")
        text = cli_generate(
            model, full, gen,
            max_tokens=int(os.getenv("FUSION_MODEL_MAX_TOKENS", "256")),
        )
        for stop in ("<|user|>", "<|system|>"):
            if stop in text:
                text = text.split(stop, 1)[0]
        return text.strip()


_llama: LocalLlama | None = None


def get_local_llama() -> LocalLlama:
    global _llama
    if _llama is None:
        _llama = LocalLlama()
    return _llama


def default_model_pool() -> list:
    llama = get_local_llama()
    if llama.active or os.getenv("FUSION_LLM_BACKEND") == "llama-local":
        return ["llama-local", "fusion-hero", "grok-intern"]
    return ["grok-intern", "fusion-hero"]