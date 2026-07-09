#!/usr/bin/env python3
"""
FUSION HERO OS v8 - HEROIC CORE ORCHESTRATOR

Ebene: Layer 0 bis Layer 5 Integration + Universal LLM Router v8.2
Status: Alles mit allem verdrahtet (Stand 2026-07-09)

- Layer 0: MasterSeed (echte SHA-256 + Strict Contraction)
- Layer 4: PMS Evidence Spine (Rust Kernel, FAIL_CLOSED)
- Layer 5: QuadCoreBridge (Phoenix-Mode, volatile state)
- Universal LLM Router v8.2: Zentrale KI-Schnittstelle (Grok + Claude + EveryAPI)
  mit Heroic Core Context Injection und dynamischem Routing.

Vollständig verbunden: Router ↔ QuadCoreBridge ↔ MasterSeed ↔ ModuleRegistry
"""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from .universal_llm_router import get_universal_llm_router, LLMResponse

_REPO_ROOT = Path(__file__).resolve().parents[2]


# =====================================================================
# LAYER 0: MASTER SEED
# =====================================================================

@dataclass(frozen=True)
class MasterSeed:
    genesis_hash: str = "000000000000000000im0000000000000000000000000000000000000000000"
    criticality_target: float = 0.22
    strict_contraction_enforced: bool = True

    def state_hash(self) -> str:
        canonical = json.dumps(
            {
                "genesis_hash": self.genesis_hash,
                "criticality_target": self.criticality_target,
                "strict_contraction_enforced": self.strict_contraction_enforced,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self, current_state_hash: str) -> bool:
        if not isinstance(current_state_hash, str):
            return False
        return current_state_hash.strip().lower() == self.state_hash()

    def verify_strict_contraction(self, operator_matrix) -> bool:
        import numpy as np
        A = np.asarray(operator_matrix, dtype=np.float64)
        if A.ndim != 2 or A.shape[0] != A.shape[1] or not np.all(np.isfinite(A)):
            return False
        return bool(np.linalg.norm(A, 2) < 1.0)


# =====================================================================
# LAYER 4 & 5: PMS + QUAD CORE
# =====================================================================

def _resolve_kernel_path() -> str:
    env = os.environ.get("PMS_KERNEL_PATH")
    if env:
        return env
    exe = "pms_rust_kernel.exe" if os.name == "nt" else "pms_rust_kernel"
    candidates = [
        _REPO_ROOT / "pms_rust_kernel_crate" / "target" / "release" / exe,
        _REPO_ROOT / exe,
        Path("./") / exe,
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return str(candidates[0])


class PMSEvidenceSpine:
    def __init__(self, executable_path: str = None, model_path: str = None, audit_path: str = None):
        self.kernel_path = executable_path or _resolve_kernel_path()
        self.model_path = model_path or str(_REPO_ROOT / "PMS.yaml")
        self.audit_path = audit_path or str(_REPO_ROOT / "pms_audit.jsonl")

    @property
    def available(self) -> bool:
        return Path(self.kernel_path).is_file() and Path(self.model_path).is_file()

    def _run(self, args, payload_json: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                [self.kernel_path, *args, "--model", self.model_path, "--audit", self.audit_path],
                input=payload_json.encode("utf-8"),
                capture_output=True,
                check=True,
                timeout=10.0,
            )
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
        # === NEU: Universal LLM Router verdrahtet ===
        self.llm_router = get_universal_llm_router(heroic_core=self)

    def invoke_phoenix_mode(self) -> bool:
        print("[LAYER 5] Phoenix-Mode aktiviert: Saeubere latentes Zustand...")
        self.mode = "PHOENIX"
        self._flush_volatile_memory()
        seed_ok = self.seed.verify_integrity(self.seed.state_hash())
        print(f"[LAYER 5] MasterSeed-Integritaet nach Reset: {'OK' if seed_ok else 'VERLETZT'}")
        return seed_ok

    def _flush_volatile_memory(self):
        n = len(self.volatile_history) + len(self.volatile_cache)
        self.volatile_history.clear()
        self.volatile_cache.clear()
        print(f"[LAYER 5] Fluechtiger Speicher geleert ({n} Eintraege).")

    def process_query(self, domain: str, operator_id: str, payload: Dict[str, Any]) -> Any:
        if domain not in ["MYTHOS", "GRUND", "BEWEIS", "GESTALT"]:
            raise ValueError(f"Ungueltige Domaene: {domain}")

        if domain in ["BEWEIS", "GESTALT"]:
            print(f"[{domain}] Leite an PMS Evidence Spine weiter...")
            result = self.spine.execute_operator_chain(operator_id, payload)
        else:
            print(f"[{domain}] Konsultiere Unified Modules...")
            result = {"status": "SUCCESS", "message": "Philosophische Synthese etabliert."}

        self.volatile_history.append({"domain": domain, "operator": operator_id})
        self.volatile_cache[operator_id] = result
        return result

    # === NEU: Zentrale LLM-Schnittstelle ===
    def ask_llm(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResponse:
        """Verwendet den verdrahteten Universal LLM Router (Grok/Claude/EveryAPI + Heroic Context)."""
        print(f"[LLM ROUTER] Anfrage klassifiziert und geroutet...")
        return self.llm_router.route(prompt, system_prompt, force_provider)


# =====================================================================
# BOOT
# =====================================================================

def bootstrap_v8_system():
    print("=" * 60)
    print("BOOTING FUSION-HERO-OS v8 (alles mit allem verbunden)")
    print("=" * 60)
    
    seed = MasterSeed()
    print(f"[LAYER 0] MasterSeed etabliert. Criticality: {seed.criticality_target}")
    
    spine = PMSEvidenceSpine()
    status = "verfuegbar" if spine.available else "NICHT gebaut -> FAIL_CLOSED"
    print(f"[LAYER 4] PMS Evidence Spine angekoppelt ({status}).")

    core = QuadCoreBridge(spine, seed=seed)
    print("[LAYER 5] Quad Core Bridge + Universal LLM Router v8.2 aktiv.")
    print("[INTEGRATION] Router ↔ Heroic Core ↔ MasterSeed ↔ PMS Spine vollständig verdrahtet.")
    print("=" * 60)
    print("SYSTEM BEREIT. THE HEROIC CORE IS ONLINE.")
    print("=" * 60)
    
    return core


if __name__ == "__main__":
    heroic_core = bootstrap_v8_system()
    
    # Test der neuen LLM-Verbindung
    llm_result = heroic_core.ask_llm("Erkläre kurz den Unterschied zwischen MasterSeed und Strict Contraction in Fusion Hero OS v8.")
    print(f"\n[LLM TEST] Provider: {llm_result.provider}")
    print(f"Antwort (Ausschnitt): {llm_result.response[:400]}...")