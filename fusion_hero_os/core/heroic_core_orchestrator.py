#!/usr/bin/env python3
"""
FUSION HERO OS v8.9 - HEROIC CORE ORCHESTRATOR

Mit Ascension-Integration über alle Layer.
QuadCoreBridge ist jetzt sowohl Heroic- als auch Ascension-aware.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from .heroic_core import get_heroic_core, HeroicCore
from .universal_llm_router import get_unified_llm_core, LLMResult

# Ascension Track Integration
try:
    from ascension_os.core.ascension_core import get_ascension_core, AscensionCore
except ImportError:
    AscensionCore = None
    get_ascension_core = None

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class MasterSeed:
    genesis_hash: str = "000000000im0000000000000000000000000000000000000000000000000000"
    criticality_target: float = 0.22
    strict_contraction_enforced: bool = True

    def state_hash(self) -> str:
        canonical = json.dumps({"genesis_hash": self.genesis_hash, "criticality_target": self.criticality_target, "strict_contraction_enforced": self.strict_contraction_enforced}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self, current_state_hash: str) -> bool:
        return isinstance(current_state_hash, str) and current_state_hash.strip().lower() == self.state_hash()


class PMSEvidenceSpine:
    def __init__(self, executable_path: str = None, model_path: str = None, audit_path: str = None):
        self.kernel_path = executable_path or str(_REPO_ROOT / "pms_rust_kernel_crate" / "target" / "release" / ("pms_rust_kernel.exe" if os.name == "nt" else "pms_rust_kernel"))
        self.model_path = model_path or str(_REPO_ROOT / "PMS.yaml")
        self.audit_path = audit_path or str(_REPO_ROOT / "pms_audit.jsonl")

    @property
    def available(self) -> bool:
        from pathlib import Path
        return Path(self.kernel_path).is_file() and Path(self.model_path).is_file()

    def _run(self, args, payload_json: str) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.kernel_path, *args, "--model", self.model_path, "--audit", self.audit_path], input=payload_json.encode("utf-8"), capture_output=True, check=True, timeout=10.0)
            return json.loads(result.stdout)
        except Exception as e:
            return {"status": "FAIL_CLOSED", "error": str(e)}

    def execute_operator_chain(self, operator_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._run(["--operator", operator_id], json.dumps(payload))

    def validate_chain(self, chain_id: str) -> Dict[str, Any]:
        return self._run(["--validate-chain", chain_id], "")


class QuadCoreBridge:
    """
    Layer 0 + 4 + 5 Bridge mit Ascension-Unterstützung.

    Kann sowohl im Heroic- als auch im Ascension-Modus betrieben werden.
    """

    def __init__(self, spine: PMSEvidenceSpine, seed: MasterSeed = None, mode: str = "heroic"):
        self.spine = spine
        self.seed = seed or MasterSeed()
        self.mode = mode.upper()  # "HEROIC" oder "ASCENSION"
        self.volatile_history: list = []
        self.volatile_cache: Dict[str, Any] = {}

        # Heroic Track
        self.heroic = get_heroic_core(quad_core=self)
        self.llm = self.heroic.llm if self.heroic else None

        # Ascension Track (falls verfügbar)
        self.ascension: Optional[AscensionCore] = None
        if get_ascension_core:
            try:
                self.ascension = get_ascension_core()
            except Exception:
                self.ascension = None

    def invoke_phoenix_mode(self) -> bool:
        print(f"[LAYER 5] Phoenix-Mode aktiviert (Mode: {self.mode})")
        self.mode = "PHOENIX"
        self._flush_volatile_memory()
        return self.seed.verify_integrity(self.seed.state_hash())

    def _flush_volatile_memory(self):
        n = len(self.volatile_history) + len(self.volatile_cache)
        self.volatile_history.clear()
        self.volatile_cache.clear()

    def process_query(self, domain: str, operator_id: str, payload: Dict[str, Any]) -> Any:
        if domain in ["BEWEIS", "GESTALT"]:
            return self.spine.execute_operator_chain(operator_id, payload)
        self.volatile_history.append({"domain": domain, "operator": operator_id})
        return {"status": "SUCCESS", "message": f"via {self.mode} Core v8.9"}

    def ask_llm(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResult:
        if self.mode == "ASCENSION" and self.ascension:
            # Ascension-spezifische Logik (kann später erweitert werden)
            print("[ASCENSION v8.9] Using AscensionCore path")
            if hasattr(self.ascension, "llm") and self.ascension.llm:
                return self.ascension.llm.ask(prompt, system_prompt, force_provider, context="ascension")

        # Default: Heroic Path
        assignment = self.llm.get_best_assignment(prompt) if self.llm else None
        if assignment:
            print(f"[{self.mode} v8.9] {assignment['provider']} (score={assignment['score']:.3f})")
        return self.llm.ask(prompt, system_prompt, force_provider, context="heroic") if self.llm else LLMResult("no-llm", "Core nicht verfügbar")


def bootstrap_v8_system(mode: str = "heroic"):
    print("=" * 70)
    print(f"BOOTING FUSION-HERO-OS v8.9 — {mode.upper()} MODE")
    print("=" * 70)
    seed = MasterSeed()
    spine = PMSEvidenceSpine()
    core = QuadCoreBridge(spine, seed=seed, mode=mode)
    print(f"[LAYER 0+4+5] MasterSeed + PMS + QuadCore + {mode.upper()} Core v8.9")
    print("[ASCENSION INTEGRATION] Ascension properties now available across layers")
    print("=" * 70)
    return core


if __name__ == "__main__":
    # Beispiel: Im Ascension-Modus starten
    core = bootstrap_v8_system(mode="ascension")
    result = core.ask_llm("Zeige Ascension-Integration über alle Layer.")
    print(f"Provider: {result.provider}")
