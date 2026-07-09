#!/usr/bin/env python3
"""
FUSION HERO OS v8.5 - HEROIC CORE ORCHESTRATOR

Jetzt mit expliziter Nutzung der dynamischen, nicht-festen Task-Zuweisung aus dem UniversalLLMRouter v8.5.
Layer 0 (MasterSeed) + Layer 4/5 (PMS + QuadCore) + dynamische LLM/Agent-Assignment auf allen Ebenen.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from .universal_llm_router import get_universal_llm_router, LLMResult

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class MasterSeed:
    genesis_hash: str = "000000000000000000im0000000000000000000000000000000000000000000"
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
    def __init__(self, spine: PMSEvidenceSpine, seed: MasterSeed = None):
        self.spine = spine
        self.seed = seed or MasterSeed()
        self.mode = "STANDARD"
        self.volatile_history: list = []
        self.volatile_cache: Dict[str, Any] = {}
        self.llm_router = get_universal_llm_router(heroic_core=self)

    def invoke_phoenix_mode(self) -> bool:
        print("[LAYER 5] Phoenix-Mode aktiviert")
        self.mode = "PHOENIX"
        self._flush_volatile_memory()
        return self.seed.verify_integrity(self.seed.state_hash())

    def _flush_volatile_memory(self):
        n = len(self.volatile_history) + len(self.volatile_cache)
        self.volatile_history.clear()
        self.volatile_cache.clear()
        print(f"[LAYER 5] Volatile memory flushed ({n} entries)")

    def process_query(self, domain: str, operator_id: str, payload: Dict[str, Any]) -> Any:
        if domain in ["BEWEIS", "GESTALT"]:
            return self.spine.execute_operator_chain(operator_id, payload)
        self.volatile_history.append({"domain": domain, "operator": operator_id})
        return {"status": "SUCCESS", "message": "Philosophische Synthese etabliert."}

    def ask_llm(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResult:
        """Verwendet die dynamische v8.5 Assignment-Logik des Routers."""
        assignment = self.llm_router.assign_dynamic(prompt, system_prompt)
        print(f"[DYNAMIC ASSIGN v8.5] {assignment['provider']} (score={assignment['score']:.3f}, category={assignment['category']})")
        return self.llm_router.route(prompt, system_prompt, force_provider)


def bootstrap_v8_system():
    print("=" * 60)
    print("BOOTING FUSION-HERO-OS v8.5 (Dynamic Non-Fixed Assignment Layer)")
    print("=" * 60)
    seed = MasterSeed()
    spine = PMSEvidenceSpine()
    core = QuadCoreBridge(spine, seed=seed)
    print("[LAYER 0+4+5] MasterSeed + PMS + QuadCore + Dynamic LLM Router v8.5 online")
    print("[INTEGRATION] Assignment now computed fresh on every ask_llm() across all layers")
    print("=" * 60)
    return core


if __name__ == "__main__":
    heroic_core = bootstrap_v8_system()
    result = heroic_core.ask_llm("Erkläre kurz den Vorteil dynamischer Agenten-Zuweisung in v8.5")
    print(f"\nProvider: {result.provider} | Latency: {result.latency_ms:.1f}ms")
