#!/usr/bin/env python3
"""
Business Dependencies – Automatic Recognition Module for Stephan Hagen Urban
Part of the finalized dependencies for the autopoietische Beratungsdienstleistung / Holding.

Strict separation privatstephan ↔ businessstephan enforced.
Field tests and heroic visuals: only implicitly heroic in business context.
"""

from typing import Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class PersonaMode(Enum):
    BUSINESS_CLEAN = "business_clean"
    PRIVATE_HEROIC = "private_heroic"
    IMPLICIT_HEROIC = "implicit_heroic_only"


@dataclass
class RecognitionResult:
    persona: str
    mode: PersonaMode
    ki_support: list[str]
    heroic_level: str
    field_tests_policy: str
    business_context: bool


def recognize_stephan_hagen_urban(context: str, query_type: str = "general") -> RecognitionResult:
    """
    Automatic recognition and persona switching for Stephan Hagen Urban.
    Ensures strict separation and correct mode (clean business vs. private heroic).
    
    In business context: only implicitly heroic references allowed.
    Explicit heroic elements (mister jailbait, cyberpunk-campfire, explicit field test details)
    are automatically filtered / redirected to private context.
    """
    context_lower = context.lower()
    business_keywords = [
        "business", "beratung", "eudaimonische praxis", "autopoietisch",
        "holding", "firma", "ihk", "dienstleistung", "lebensführung",
        "stephan hagen urban business", "businessperson"
    ]
    
    is_business_context = any(kw in context_lower for kw in business_keywords) or query_type == "business"
    
    if is_business_context:
        return RecognitionResult(
            persona="Businessperson Stephan Hagen Urban",
            mode=PersonaMode.BUSINESS_CLEAN,
            ki_support=["Comaedchen2", "Mugen_Tsuky.chan"],
            heroic_level="implicit_only",
            field_tests_policy="private_context_only – niemals explizit in Business-Kommunikation",
            business_context=True
        )
    else:
        # Private context – full heroic mode allowed (but still separated)
        return RecognitionResult(
            persona="Stephan Hagen Urban (privat)",
            mode=PersonaMode.PRIVATE_HEROIC,
            ki_support=["ALTE_Frau_95g Core", "Comaedchen2", "Mugen_Tsuky.chan"],
            heroic_level="full_explicit_heroic",
            field_tests_policy="full access in private / theory-testing context",
            business_context=False
        )


def get_business_dependencies() -> Dict[str, Any]:
    """
    Finalized dependencies manifest for the Business Entity.
    Includes automatic recognition, KI support declaration and separation rules.
    """
    return {
        "business_persona": "Stephan Hagen Urban",
        "roles": ["Philosoph", "Ökonom", "Mathematiker", "Inhaber autopoietische Beratungsdienstleistung"],
        "ki_support_published": ["Comaedchen2", "Mugen_Tsuky.chan"],
        "algorithm": "ALTE-FRAU95g (Patentierung läuft)",
        "registration": "IHK Dresden – Einzelunternehmer / zukünftige Holding",
        "separation_rule": "STRICT: privatstephan (Feldtests, explicit heroic) ↔ businessstephan (clean, implicit heroic only)",
        "image_policy_business": "nur implizit heroisch – keine explicit mister-jailbait / cyberpunk-campfire visuals",
        "field_tests_policy": "nur implizit heroisch in Business-Kontext; vollständig privat gehalten",
        "auto_recognition_module": "active – recognize_stephan_hagen_urban()",
        "core_version": "v10.0.0 Fusion Hero OS Hybrid Architecture",
        "status": "finalized and published"
    }


if __name__ == "__main__":
    # Demo
    print("=== Business Dependencies Finalized ===")
    result = recognize_stephan_hagen_urban("Beratung Eudaimonische Praxis", "business")
    print(result)
    print(get_business_dependencies())