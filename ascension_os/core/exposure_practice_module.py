# -*- coding: utf-8 -*-
"""
AscensionOS v9.7 - ExposurePracticeModule

Simulierter Gespraechspartner fuer soziale Expositions-Uebung (z.B. gegen
Mutismus/Shutdown in Kontaktsituationen wie Dating-App-Chats). KEIN echter
Mensch ist beteiligt - der "Partner" ist ein LLM-simuliertes Gegenueber.
Es gibt keinen Auslassungs- oder Interventions-Mechanismus gegen Dritte;
geloggt wird ausschliesslich der eigene Fortschritt/die eigenen Symptome
der uebenden Person.

Nutzt den bestehenden UnifiedHeroicLLMCore.ask() (fusion_hero_os) fuer die
Partner-Antworten statt eine neue LLM-Anbindung zu bauen. Ohne echten
LLM-Provider (kein API-Key konfiguriert - erkennbar am internen Fallback-
Provider "fusion-hero", der nur generischen Boilerplate-Text liefert)
faellt dieses Modul auf einen kleinen, klar erkennbaren Antwortpool zurueck,
statt faelschlich realistische Antworten vorzutaeuschen.

Ehrlicher Status: Dies ist ein Uebungswerkzeug, kein Ersatz fuer klinische
Begleitung. Bei starkem Leidensdruck (Shutdown, Panik) ist professionelle
Unterstuetzung sinnvoll - dieses Modul ersetzt sie nicht, es unterstuetzt
nur eigenstaendiges Uebungslogging und -tracking.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DIFFICULTIES = ("leicht", "mittel", "schwer")
SCENARIOS = ("dating_app_opener", "small_talk_continuation", "handling_a_lull")

_SYSTEM_PROMPTS = {
    "leicht": (
        "Du spielst eine warme, geduldige, ermutigende Person in einer simulierten "
        "Dating-App-Konversation zu Uebungszwecken (Expositionstraining gegen soziale "
        "Angst/Mutismus). Gib der uebenden Person viele Anknuepfungspunkte, bleib "
        "freundlich, brich das Gespraech nicht ab, auch bei kurzen/holprigen Antworten."
    ),
    "mittel": (
        "Du spielst eine realistische, neutral gestimmte Person in einer simulierten "
        "Dating-App-Konversation zu Uebungszwecken (Expositionstraining gegen soziale "
        "Angst/Mutismus). Normales Interesse, gelegentlich kurze Antworten, aber nicht "
        "unfreundlich. Verhalte dich wie eine durchschnittliche echte Unterhaltung."
    ),
    "schwer": (
        "Du spielst eine eher knappe, wechselhaft interessierte Person in einer "
        "simulierten Dating-App-Konversation zu Uebungszwecken (Expositionstraining "
        "gegen soziale Angst/Mutismus). Baue gelegentlich Gespraechspausen oder kurze, "
        "wenig einladende Antworten ein, damit die uebende Person das Wiederanknuepfen "
        "ueben kann. Bleib dabei nicht feindselig, nur herausfordernder."
    ),
}

_SCENARIO_OPENERS = {
    "dating_app_opener": "Die uebende Person schreibt gerade die allererste Nachricht nach dem Match.",
    "small_talk_continuation": "Es laeuft bereits ein lockeres Gespraech, das fortgesetzt werden soll.",
    "handling_a_lull": "Das Gespraech ist gerade ins Stocken geraten und soll wiederbelebt werden.",
}

# Klar erkennbarer Offline-Fallback (kein LLM verfuegbar) - bewusst NICHT
# realistisch, nur damit das Modul ohne API-Key ueberhaupt lauffaehig bleibt.
_OFFLINE_REPLIES = {
    "leicht": [
        "[offline-uebungspartner] Klingt gut, erzaehl mir mehr davon!",
        "[offline-uebungspartner] Haha, das ist interessant - wie kam's dazu?",
        "[offline-uebungspartner] Mag ich. Was machst du sonst gern?",
    ],
    "mittel": [
        "[offline-uebungspartner] Ok, ha.",
        "[offline-uebungspartner] Interessant. Und du?",
        "[offline-uebungspartner] Kenn ich. Was noch?",
    ],
    "schwer": [
        "[offline-uebungspartner] Ok.",
        "[offline-uebungspartner] Muss gleich los, aber ja.",
        "[offline-uebungspartner] Hm.",
    ],
}

_INTERNAL_FALLBACK_MARKER = "fusion-hero"  # provider-Name von InternalFallbackProvider


@dataclass
class ConversationTurn:
    speaker: str  # "user" | "partner"
    message: str
    timestamp: str


@dataclass
class PracticeSession:
    session_id: int
    scenario: str
    difficulty: str
    started_at: str
    ended_at: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    shutdown_occurred: Optional[bool] = None
    turns_before_disengagement: Optional[int] = None
    self_rated_anxiety: Optional[float] = None  # 0-1, Selbstauskunft
    notes: str = ""


class ExposurePracticeModule:
    """Simulierter Uebungspartner + reines Selbst-Tracking (kein Dritter beteiligt)."""

    def __init__(self, llm: Any = None, persistence_path: str = "data/exposure_practice_sessions.json",
                 seed: Optional[int] = None):
        self.llm = llm
        self.persistence_path = Path(persistence_path)
        self.sessions: List[PracticeSession] = []
        self._rng = random.Random(seed)
        self._load_from_disk()

    def start_session(self, scenario: str = "dating_app_opener",
                       difficulty: str = "mittel") -> PracticeSession:
        if scenario not in SCENARIOS:
            raise ValueError(f"scenario muss einer von {SCENARIOS} sein, nicht {scenario!r}")
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"difficulty muss einer von {DIFFICULTIES} sein, nicht {difficulty!r}")

        session = PracticeSession(
            session_id=len(self.sessions) + 1,
            scenario=scenario,
            difficulty=difficulty,
            started_at=datetime.now().isoformat(),
        )
        self.sessions.append(session)
        self._save_to_disk()
        return session

    def _build_prompt(self, session: PracticeSession, user_message: str) -> str:
        history = "\n".join(f"{t.speaker}: {t.message}" for t in session.turns[-8:])
        context = _SCENARIO_OPENERS[session.scenario]
        return (
            f"{context}\n\nBisheriger Verlauf:\n{history}\n\n"
            f"user: {user_message}\npartner:"
        )

    def _offline_reply(self, difficulty: str) -> str:
        pool = _OFFLINE_REPLIES[difficulty]
        return pool[self._rng.randrange(len(pool))]

    def respond(self, session: PracticeSession, user_message: str) -> str:
        """Fuegt die Nutzer-Nachricht hinzu, generiert eine Partner-Antwort (LLM oder Offline-Pool)."""
        now = datetime.now().isoformat()
        session.turns.append(ConversationTurn("user", user_message, now))

        reply_text: Optional[str] = None
        if self.llm is not None:
            try:
                result = self.llm.ask(
                    self._build_prompt(session, user_message),
                    system_prompt=_SYSTEM_PROMPTS[session.difficulty],
                    context="exposure_practice",
                )
                provider = getattr(result, "provider", "") or ""
                if _INTERNAL_FALLBACK_MARKER not in provider:
                    reply_text = getattr(result, "response", None)
            except Exception:
                reply_text = None

        if not reply_text:
            reply_text = self._offline_reply(session.difficulty)

        session.turns.append(ConversationTurn("partner", reply_text, datetime.now().isoformat()))
        self._save_to_disk()
        return reply_text

    def end_session(self, session: PracticeSession, shutdown_occurred: bool,
                     self_rated_anxiety: Optional[float] = None, notes: str = "") -> PracticeSession:
        """Schliesst eine Session mit reiner Selbstauskunft ab (keine Drittdaten)."""
        session.ended_at = datetime.now().isoformat()
        session.shutdown_occurred = shutdown_occurred
        session.turns_before_disengagement = sum(1 for t in session.turns if t.speaker == "user")
        session.self_rated_anxiety = self_rated_anxiety
        session.notes = notes
        self._save_to_disk()
        return session

    def get_progress(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """Trend ueber abgeschlossene Sessions: mehr Turns bis Disengagement + weniger Angst = Fortschritt."""
        ended = [s for s in self.sessions if s.ended_at is not None]
        items = ended if last_n is None else ended[-last_n:]
        if not items:
            return {"sessions_completed": 0, "trend": "keine abgeschlossenen Sessions"}

        turns_vals = [s.turns_before_disengagement or 0 for s in items]
        anxiety_vals = [s.self_rated_anxiety for s in items if s.self_rated_anxiety is not None]
        shutdown_rate = sum(1 for s in items if s.shutdown_occurred) / len(items)

        result = {
            "sessions_completed": len(items),
            "avg_turns_before_disengagement": round(sum(turns_vals) / len(turns_vals), 2),
            "shutdown_rate": round(shutdown_rate, 3),
        }
        if anxiety_vals:
            result["avg_self_rated_anxiety"] = round(sum(anxiety_vals) / len(anxiety_vals), 3)
        if len(items) >= 4:
            half = len(items) // 2
            first_half_turns = sum(turns_vals[:half]) / half
            second_half_turns = sum(turns_vals[half:]) / (len(items) - half)
            result["trend"] = "verbessert" if second_half_turns > first_half_turns else (
                "stabil" if second_half_turns == first_half_turns else "ruecklaeufig"
            )
        else:
            result["trend"] = "zu wenige Sessions fuer Trend (mind. 4 noetig)"
        return result

    def get_sessions(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self.sessions if last_n is None else self.sessions[-last_n:]
        return [asdict(s) for s in items]

    def _save_to_disk(self) -> None:
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump({"sessions": [asdict(s) for s in self.sessions]}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ExposurePracticeModule] Failed to save: {e}")

    def _load_from_disk(self) -> None:
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("sessions", []):
                turns = [ConversationTurn(**t) for t in item.pop("turns", [])]
                self.sessions.append(PracticeSession(turns=turns, **item))
        except Exception as e:
            print(f"[ExposurePracticeModule] Failed to load: {e}")
