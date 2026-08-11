# -*- coding: utf-8 -*-
"""Gate fuer das God-Layer-Siegel.

Das Siegel sperrt Force-Pushes auf God-/Highest-/Self-Mod-Scopes, bis der
Operator es mit der Bestaetigungsphrase oeffnet. Bis hierher war es durch
keinen einzigen Test gedeckt — und genau darin lag der Fehler, den diese
Datei festnagelt: ``push_layer_guard`` fing den gesamten Siegel-Block mit
einem ``except Exception: pass`` ab und liess Force-Pushes durch, sobald bei
der Auswertung irgendetwas schiefging. Ein Siegel, das bei Stoerung aufgeht,
ist keins.

Geprueft wird deshalb dreierlei:
  1. Fehlerverhalten ist FAIL CLOSED (nicht fail open) — und zwar nur fuer force.
  2. ``public_status`` haelt seinen Docstring ein: kein roher Token.
  3. Die Plattform-Version ist nicht mehr hartkodiert.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD_SRC = REPO_ROOT / "fusion_hero_os" / "core" / "push_layer_guard.py"
SEAL_SRC = REPO_ROOT / "fusion_hero_os" / "core" / "god_layer_seal.py"


# --- 1. Fail closed statt fail open -----------------------------------------


def test_seal_block_is_scoped_to_force_pushes():
    """Der Siegel-Block darf nur fuer force=True laufen.

    So bleibt die urspruengliche Sorge gewahrt (nicht jeden Push wegen eines
    fremden Fehlers blockieren), ohne das Siegel selbst zu entwerten.
    """
    src = GUARD_SRC.read_text(encoding="utf-8")
    block = src[src.index("# God-layer seal:") :]
    assert re.search(r"\n    if force:\n", block[:2000]), (
        "Der God-layer-Seal-Block ist nicht mehr auf force-Pushes eingegrenzt. "
        "Ohne diese Eingrenzung trifft ein Fail-Closed auch normale Pushes."
    )


def test_seal_evaluation_errors_do_not_fail_open():
    """Ein Fehler beim Auswerten des Siegels darf den Push NICHT durchlassen."""
    src = GUARD_SRC.read_text(encoding="utf-8")
    block = src[src.index("# God-layer seal:") : src.index("branch_rules =")]

    # Der alte Regressionspfad: alles abfangen und weiterlaufen.
    assert "except Exception:\n            pass" not in block, (
        "Regression: der Siegel-Block faengt Fehler wieder ab und laeuft weiter "
        "(fail open). Bei unlesbarem Siegelzustand muss force-push gesperrt "
        "werden, nicht erlaubt."
    )
    # Der neue Pfad: Fehler setzen die Sperre.
    assert "seal_blocked = True" in block, (
        "Kein Fail-Closed-Pfad gefunden: ein Auswertungsfehler muss "
        "seal_blocked setzen."
    )


def test_missing_module_may_still_fail_open():
    """Fehlt das Modul ganz, gibt es kein Siegel — Durchfall ist dann korrekt.

    Diese Unterscheidung ist der Grund, warum nicht pauschal alles gesperrt
    wird: ImportError heisst 'Integration nicht vorhanden', jeder andere
    Fehler heisst 'Zustand unklar'.
    """
    src = GUARD_SRC.read_text(encoding="utf-8")
    block = src[src.index("# God-layer seal:") : src.index("branch_rules =")]
    assert "except ImportError:" in block, (
        "ImportError muss vom uebrigen Fehlerfall getrennt behandelt werden."
    )


def _evaluate(**kw):
    """evaluate_push ohne Git-Zugriff: Dateien/Subjects/URL werden gesetzt.

    Der Guard importiert ``is_sealed``/``require_write`` erst zur Laufzeit aus
    dem Seal-Modul — monkeypatch auf die Modulattribute greift daher.
    """
    from fusion_hero_os.core import push_layer_guard as guard

    kw.setdefault("remote", "origin")
    kw.setdefault("branch", "main")
    kw.setdefault("remote_url", "https://github.com/95guknow/fusion-hero-os.git")
    kw.setdefault("files", ["README.md"])
    kw.setdefault("subjects", ["docs: harmlose Aenderung"])
    return guard.evaluate_push(**kw)


def test_seal_blocks_force_push_when_sealed(monkeypatch):
    """Verhaltenstest: gesiegelt + force + kein Unlock => allow=False."""
    from fusion_hero_os.core import god_layer_seal as seal

    monkeypatch.setattr(seal, "is_sealed", lambda: True)
    monkeypatch.setattr(
        seal, "require_write", lambda scope=None: (False, "sealed: %s" % scope)
    )

    decision = _evaluate(force=True)
    assert decision.allow is False
    assert "seal" in (decision.reason or "").lower()


def test_seal_evaluation_error_blocks_force_push(monkeypatch):
    """Verhaltenstest: wirft die Siegelpruefung, wird force-push gesperrt."""
    from fusion_hero_os.core import god_layer_seal as seal

    def _boom() -> bool:
        raise RuntimeError("god_layer_seal.json beschaedigt")

    monkeypatch.setattr(seal, "is_sealed", _boom)

    decision = _evaluate(force=True)
    assert decision.allow is False, (
        "Bei unlesbarem Siegelzustand wurde der force-push erlaubt — das ist "
        "genau die Fail-Open-Regression."
    )
    assert "nicht auswertbar" in (decision.reason or "")


def test_seal_evaluation_error_does_not_block_normal_push(monkeypatch):
    """Gegenprobe: ohne --force bleibt ein Siegelfehler folgenlos.

    Das ist die Zusicherung, die das Fail-Closed vertretbar macht — die
    urspruengliche Sorge im alten Kommentar war, dass ein fremder Fehler
    jeden Push blockiert. Genau das passiert nicht.
    """
    from fusion_hero_os.core import god_layer_seal as seal

    def _boom() -> bool:
        raise RuntimeError("god_layer_seal.json beschaedigt")

    monkeypatch.setattr(seal, "is_sealed", _boom)

    decision = _evaluate(force=False)
    assert "nicht auswertbar" not in (decision.reason or ""), (
        "Ein Siegelfehler darf normale Pushes nicht beruehren."
    )


# --- 2. public_status haelt seinen Docstring ein -----------------------------


def test_public_status_leaks_no_raw_unlock_token():
    from fusion_hero_os.core.god_layer_seal import DEFAULT_UNLOCK_TOKEN, public_status

    flat = repr(public_status())
    assert DEFAULT_UNLOCK_TOKEN not in flat, (
        "public_status() verspricht 'no raw tokens', gibt aber den "
        "Entsiegelungs-Token aus."
    )
    assert "unlock_hint" not in public_status()


def test_operator_status_still_carries_the_hint():
    """Die Trennung muss echt sein: status() bleibt fuer den Operator vollstaendig."""
    from fusion_hero_os.core.god_layer_seal import status

    assert status().get("unlock_hint")


# --- 3. Plattform-Version nicht mehr hartkodiert -----------------------------


def test_platform_version_follows_the_canon():
    from fusion_hero_os.core.god_layer_seal import PLATFORM

    canon = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert PLATFORM == canon, (
        f"god_layer_seal meldet Plattform {PLATFORM!r}, Kanon ist {canon!r}. "
        "Die Konstante darf nicht wieder fest im Modul stehen."
    )


def test_platform_constant_is_not_a_literal():
    src = SEAL_SRC.read_text(encoding="utf-8")
    assert not re.search(r'^PLATFORM\s*=\s*["\']\d', src, re.MULTILINE), (
        "PLATFORM ist wieder ein Literal. bump_version.py --check deckt nur "
        "Manifeste ab, nicht Konstanten im Code — die Drift faellt dann nicht auf."
    )
