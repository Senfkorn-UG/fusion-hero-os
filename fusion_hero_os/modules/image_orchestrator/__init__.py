"""HeroicImageOrchestrator — Bild-Pipeline mit Rate-Limit-Orchestrator.

Status (Code-Honesty):
  - IMPLEMENTIERT: YAML/JSON Visual-Identity-Regeln (extern), separater Rate-Limiter,
    BaseModule-Adapter, Job-Queue ohne echten API-Aufruf.
  - KONZEPT / NICHT IMPLEMENTIERT: echte Bildgenerierung, mister-jailbait-gui-Anbindung,
    Real-Foto-Pipeline — hier Dry-Run-Pläne wie connectors.py.
"""

from fusion_hero_os.modules.image_orchestrator.orchestrator import HeroicImageOrchestrator

__all__ = ["HeroicImageOrchestrator"]