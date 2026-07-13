#!/usr/bin/env python3
"""Kompatibilitaets-Shim (v8.3-Konsolidierung).

Die kanonische Implementierung lebt in
fusion_hero_os/core/heroic_core_orchestrator.py - diese Datei re-exportiert
sie nur, damit aeltere Aufrufe (python core/heroic_core_orchestrator.py)
weiter funktionieren und keine zweite, driftende Kopie existiert.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fusion_hero_os.core.heroic_core_orchestrator import (  # noqa: E402,F401
    VALID_DOMAINS,
    MasterSeed,
    PMSEvidenceSpine,
    QuadCoreBridge,
    bootstrap_v8_system,
)

if __name__ == "__main__":
    core = bootstrap_v8_system()
    response = core.process_query(
        domain="GESTALT",
        operator_id="OP_Q_B_CIRC",
        payload={"action": "verify_reciprocity"},
    )
    print(f"Spine Response: {response}")
