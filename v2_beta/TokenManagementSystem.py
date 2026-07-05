"""
v2_beta Timespace TMS — verweist auf kanonische Implementierungen.

- Basis: 03_Code/TokenManagementSystem.py (TMS v1.0, implementiert)
- Geometrie: 03_Code/timespace_token_management.py (Scaffold, 2026-07-05)

Der frühere Ein-Zeilen-Platzhalter wurde durch echten Code ersetzt.
"""

from pathlib import Path
import sys

_CODE = Path(__file__).resolve().parents[1] / "03_Code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from TokenManagementSystem import (  # noqa: E402
    ResourceState,
    TokenManagementSystem,
    TransformationType,
)
from timespace_token_management import (  # noqa: E402
    TimespaceCoordinate,
    TimespaceTokenManager,
    TimespaceTrack,
)

__all__ = [
    "ResourceState",
    "TokenManagementSystem",
    "TransformationType",
    "TimespaceCoordinate",
    "TimespaceTokenManager",
    "TimespaceTrack",
]