"""HeroicLLM-EA Orchestrator — LLM-Vorschläge + evolutionäre Auswahl.

Status (Code-Honesty):
  - IMPLEMENTIERT: austauschbares LLM-Interface, Fitness (Konsistenz + Performance
    + PeerReview-Score), hierarchisches Mutations-Gedächtnis, BaseModule-Adapter.
  - KONZEPT / NICHT IMPLEMENTIERT: echter LLM-Provider-Aufruf, Campfire-Pilot-Daten,
    tokio/async-Inferenz — hier nur deterministische Stub-Proposals für Tests.
"""

from fusion_hero_os.modules.heroic_llm_ea.orchestrator import HeroicLLMEAOrchestrator

__all__ = ["HeroicLLMEAOrchestrator"]