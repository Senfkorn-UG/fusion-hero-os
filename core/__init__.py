# Fusion-Hero-OS Core - v8

"""
ALTE_Frau_95g Heroic Core

Enthält die zentralen Core-Module:
- CoEvolutionaryClosure (CEC)
- RustHybridEmbodiment (RHE)
- PsycholysisTrigger
- HeroicMathEngine (mathematische Kernkomponenten)

Teil der 02_architecture Schicht.
"""

__version__ = "v8"

from .cec import global_cec
try:
    from .rhe import global_rhe
except ImportError:
    global_rhe = None
try:
    from .psycholysis_trigger import PsycholysisTrigger
except ImportError:
    PsycholysisTrigger = None

# Neue mathematische Kernkomponente (v8)
try:
    from .heroic_math_engine import (
        HeroicMatrixEngine,
        StableCoreLattice,
        RepairedStructureIP,
        global_heroic_math
    )
except ImportError:
    HeroicMatrixEngine = None
    StableCoreLattice = None
    RepairedStructureIP = None
    global_heroic_math = None