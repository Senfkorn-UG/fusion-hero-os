# -*- coding: utf-8 -*-
"""
CONTROLLER AGGREGATE — Owner-Ebene + Layer-basiertes implizites Laden (v1.0)
=============================================================================
Die Schnittstelle zwischen Endnutzer und System: definiert, welche Funktionen/
Agenten auf welcher Layer implizit (automatisch, ohne explizite Anforderung)
geladen werden. Je hoeher die Layer, desto impliziter das Laden.

Zwei Zonen:
  - OEFFENTLICH (jeder Nutzer): Layer-Uebersicht lesen, registrierte
    Capabilities auflisten, sehen was beim aktuellen Schwellwert implizit aktiv ist.
  - OWNER-ONLY (nur mit gueltigem Auth-Token): Capabilities registrieren/entfernen,
    den Implizitheits-Schwellwert (active_threshold) veraendern.

Owner-Auth (echtes Login/Token, kein Deko):
  - Beim allerersten Start MUSS der Owner per initialize_owner(password) ein
    Passwort setzen (fail-closed: vor Initialisierung sind alle Owner-Aktionen
    gesperrt). Danach ist initialize_owner() gesperrt — keine Uebernahme durch
    Dritte moeglich, ausser die Credential-Datei wird manuell geloescht.
  - Passwort wird NIE im Klartext gespeichert: PBKDF2-HMAC-SHA256 + zufaelliger
    Salt (stdlib hashlib, keine Fremdabhaengigkeit).
  - authenticate(password) liefert bei Erfolg einen zufaelligen Session-Token
    (secrets.token_urlsafe), der serverseitig mit Ablaufzeit gehalten wird.
  - verify(token) prueft Gueltigkeit + Ablauf; revoke(token) macht ihn sofort ungueltig.
  - Credentials liegen standardmaessig AUSSERHALB des Repos (~/.fusion_hero_os/),
    damit nie versehentlich ein Passwort-Hash eingecheckt werden kann.

HARTE INVARIANTEN (vgl. orchestration/agents.py):
  1. Import-sicher: KEINE Seiteneffekte auf Modulebene.
  2. Reines Python (nur Standardbibliothek: hashlib, hmac, json, secrets, time).
  3. Kein Passwort/Token wird geloggt oder im Klartext persistiert.
  4. Fail-closed: ohne gueltiges Token keine Owner-Aktion — auch nicht "im Zweifel erlauben".
  5. House style: deutsche Docstrings/Kommentare.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

DEFAULT_CREDENTIALS_PATH = Path.home() / ".fusion_hero_os" / "controller_owner_credentials.json"
_PBKDF2_ITERATIONS = 600_000
_TOKEN_TTL_SECONDS = 4 * 60 * 60  # 4 Stunden Session-Gueltigkeit


class OwnerAuthError(Exception):
    """Owner-Aktion ohne gueltiges Token versucht, oder Owner-Setup-Konflikt."""


@dataclass
class OwnerAuth:
    """Owner-Login per Passwort, Session-Tokens mit Ablaufzeit.

    Ein-Personen-System: genau ein Owner-Credential-Satz pro Installation.
    """

    credentials_path: Path = field(default_factory=lambda: DEFAULT_CREDENTIALS_PATH)
    _tokens: Dict[str, float] = field(default_factory=dict, repr=False)  # token -> expiry ts

    @property
    def is_initialized(self) -> bool:
        return self.credentials_path.exists()

    def initialize_owner(self, password: str) -> None:
        """Setzt das Owner-Passwort EINMALIG.

        Schlaegt fehl, wenn bereits initialisiert — verhindert Uebernahme durch Dritte,
        solange die Credential-Datei besteht. Zum bewussten Zuruecksetzen muss die Datei
        unter ``credentials_path`` manuell geloescht werden.
        """
        if self.is_initialized:
            raise OwnerAuthError(
                "Owner bereits initialisiert. Zum Zuruecksetzen die Datei "
                f"{self.credentials_path} manuell loeschen (nur lokal, mit Bedacht)."
            )
        if not password or len(password) < 8:
            raise ValueError("Passwort muss mindestens 8 Zeichen haben.")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        self.credentials_path.write_text(
            json.dumps({"salt": salt.hex(), "hash": digest.hex(), "iterations": _PBKDF2_ITERATIONS}),
            encoding="utf-8",
        )
        try:
            os.chmod(self.credentials_path, 0o600)
        except OSError:
            pass  # z. B. unter Windows nicht immer verfuegbar — kein Hard-Fail

    def authenticate(self, password: str) -> Optional[str]:
        """Prueft das Passwort; liefert bei Erfolg einen neuen Session-Token, sonst None."""
        if not self.is_initialized:
            return None
        try:
            data = json.loads(self.credentials_path.read_text(encoding="utf-8"))
            salt = bytes.fromhex(data["salt"])
            expected = bytes.fromhex(data["hash"])
            iterations = int(data.get("iterations", _PBKDF2_ITERATIONS))
        except (OSError, ValueError, KeyError):
            return None
        candidate = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
        if not hmac.compare_digest(candidate, expected):
            return None
        token = secrets.token_urlsafe(32)
        self._tokens[token] = time.time() + _TOKEN_TTL_SECONDS
        return token

    def verify(self, token: Optional[str]) -> bool:
        """Prueft, ob ein Token aktuell gueltig ist (existiert + nicht abgelaufen)."""
        if not token:
            return False
        expiry = self._tokens.get(token)
        if expiry is None:
            return False
        if time.time() > expiry:
            del self._tokens[token]
            return False
        return True

    def revoke(self, token: Optional[str]) -> None:
        """Macht ein Token sofort ungueltig (z. B. beim Logout)."""
        self._tokens.pop(token, None)

    def require(self, token: Optional[str]) -> None:
        """Wirft OwnerAuthError, wenn das Token ungueltig ist. Fuer Owner-only-Methoden."""
        if not self.verify(token):
            raise OwnerAuthError("Owner-Aktion verweigert: ungueltiges oder fehlendes Token.")


# =============================================================================
# Layer-Modell: je hoeher die Layer, desto impliziter das Laden
# =============================================================================

@dataclass
class Layer:
    """Eine Ladestufe. Layer 0 = rein explizit (nur auf direkten Aufruf).
    Aufsteigende Layer = zunehmend implizites/automatisches Laden."""

    level: int
    name: str
    description: str


DEFAULT_LAYERS: List[Layer] = [
    Layer(0, "Kernel",      "Immutable Basis. Nie implizit veraendert, nur explizit gelesen."),
    Layer(1, "Werkzeug",    "Auf direkten Aufruf (\"nutze X\"). Keine Automatik."),
    Layer(2, "Vorschlag",   "Wird vorgeschlagen, aber nicht automatisch ausgefuehrt."),
    Layer(3, "Kontext",     "Laedt automatisch, wenn der Kontext eindeutig passt."),
    Layer(4, "Hintergrund", "Laeuft automatisch im Hintergrund, ohne Nachfrage."),
    Layer(5, "Ambient",     "Vollstaendig implizit: Teil der Umgebung, nie explizit angefordert."),
]


@dataclass
class Capability:
    """Eine registrierte Funktion/Agent-Faehigkeit, gebunden an eine Layer.

    ``loader`` wird NICHT automatisch im Hintergrund aufgerufen — das Aggregat haelt nur
    fest, WAS beim aktuellen Schwellwert implizit waere (fuer GUI-Status/Audit). Das
    tatsaechliche Ausfuehren bleibt eine bewusste, seiteneffektbehaftete Operation
    (siehe ``ControllerAggregate.load_active``), damit implizites Laden nie im Dunkeln
    passiert.
    """

    name: str
    layer: int
    description: str
    loader: Callable[[], object]


class ControllerAggregate:
    """Die Schnittstelle Endnutzer <-> System.

    Oeffentliche Methoden (kein Token noetig): Layer-Uebersicht, aktive Capabilities.
    Owner-only Methoden (gueltiges Token noetig): registrieren, Schwellwert setzen.
    """

    def __init__(self, auth: Optional[OwnerAuth] = None, layers: Optional[List[Layer]] = None):
        self.auth = auth if auth is not None else OwnerAuth()
        self.layers: Dict[int, Layer] = {l.level: l for l in (layers or DEFAULT_LAYERS)}
        self._registry: Dict[str, Capability] = {}
        self._threshold: int = 0  # Start: nur Layer 0 (Kernel) gilt als "aktiv"

    # ---- oeffentlich --------------------------------------------------

    def describe_layers(self) -> List[Dict[str, object]]:
        """Layer-Tabelle fuer die GUI (immer lesbar, kein Token noetig)."""
        return [
            {"level": l.level, "name": l.name, "description": l.description,
             "active": l.level <= self._threshold}
            for l in sorted(self.layers.values(), key=lambda x: x.level)
        ]

    def active_threshold(self) -> int:
        return self._threshold

    def resolve_active(self) -> List[Capability]:
        """Alle Capabilities, die beim aktuellen Schwellwert implizit geladen waeren."""
        return [c for c in self._registry.values() if c.layer <= self._threshold]

    def list_all(self) -> List[Capability]:
        return list(self._registry.values())

    # ---- owner-only -----------------------------------------------------

    def register(self, capability: Capability, token: Optional[str]) -> None:
        """Registriert eine neue Capability zur Laufzeit. Owner-only."""
        self.auth.require(token)
        if capability.layer not in self.layers:
            raise ValueError(f"Unbekannte Layer {capability.layer}. Bekannt: {sorted(self.layers)}")
        self._registry[capability.name] = capability

    def unregister(self, name: str, token: Optional[str]) -> bool:
        """Entfernt eine Capability zur Laufzeit. Owner-only."""
        self.auth.require(token)
        return self._registry.pop(name, None) is not None

    def set_threshold(self, level: int, token: Optional[str]) -> None:
        """Setzt den Implizitheits-Schwellwert. Owner-only."""
        self.auth.require(token)
        if level not in self.layers:
            raise ValueError(f"Unbekannte Layer {level}. Bekannt: {sorted(self.layers)}")
        self._threshold = level

    # ---- bootstrap (nur fuer Anwendungs-Startcode, kein UI/API-Pfad) ----

    def bootstrap_register(self, capability: Capability) -> None:
        """Registriert eine Capability OHNE Token-Pruefung.

        Ausschliesslich fuer den Start der Anwendung gedacht (z. B. app.py registriert
        seine eingebauten Capabilities beim Hochfahren) — das ist Code, das der Owner
        selbst geschrieben und deployed hat, keine Laufzeit-Aktion durch einen Nutzer.
        Diese Methode darf NIE hinter einem GUI-Button oder einer API-Route haengen.
        """
        if capability.layer not in self.layers:
            raise ValueError(f"Unbekannte Layer {capability.layer}. Bekannt: {sorted(self.layers)}")
        self._registry[capability.name] = capability

    def load_active(self) -> Dict[str, object]:
        """Fuehrt die Loader ALLER aktuell impliziten Capabilities aus.

        Oeffentlich (kein Token) — das Aggregat entscheidet ueber die Sichtbarkeit
        implizit geladener Funktionen, nicht ueber ihre generelle Nutzbarkeit."""
        out: Dict[str, object] = {}
        for cap in self.resolve_active():
            try:
                out[cap.name] = cap.loader()
            except Exception as exc:  # noqa: BLE001 — ein defekter Loader darf die anderen nicht stoppen
                out[cap.name] = {"error": repr(exc)}
        return out


# =============================================================================
# DEMO (nur unter __main__ — import-sicher)
# =============================================================================

def _demo() -> None:
    """Kleine, schnelle Demonstration des vollen Owner-Auth- und Layer-Flows.

    Nutzt eine temporaere Credentials-Datei, damit der Demo-Lauf keine echten
    Owner-Daten unter ~/.fusion_hero_os/ beruehrt."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        auth = OwnerAuth(credentials_path=Path(tmp) / "demo_credentials.json")
        agg = ControllerAggregate(auth=auth)

        print("=== Controller Aggregate Demo ===")
        print(f"Owner initialisiert? {auth.is_initialized}")

        # Registrierung OHNE Token schlaegt fehl (fail-closed).
        try:
            agg.register(Capability("x", 1, "test", lambda: 1), token=None)
        except OwnerAuthError as exc:
            print(f"Erwarteter Fehler (kein Owner): {exc}")

        auth.initialize_owner("sehr-sicheres-passwort")
        print(f"Owner initialisiert? {auth.is_initialized}")

        token = auth.authenticate("falsches-passwort")
        print(f"Falsches Passwort -> Token: {token}")

        token = auth.authenticate("sehr-sicheres-passwort")
        print(f"Richtiges Passwort -> Token erhalten: {bool(token)}")

        agg.register(Capability("qubo", 1, "QUBO-Solver", lambda: "geladen"), token=token)
        agg.register(Capability("ambient_status", 5, "Ambient Status-Feed", lambda: "geladen"), token=token)
        print(f"Registriert: {[c.name for c in agg.list_all()]}")

        print(f"Aktiv bei Schwellwert {agg.active_threshold()}: {[c.name for c in agg.resolve_active()]}")
        agg.set_threshold(5, token=token)
        print(f"Aktiv bei Schwellwert {agg.active_threshold()}: {[c.name for c in agg.resolve_active()]}")
        print(f"load_active(): {agg.load_active()}")

        auth.revoke(token)
        print(f"Token nach Logout noch gueltig? {auth.verify(token)}")


if __name__ == "__main__":
    _demo()
