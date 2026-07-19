# -*- coding: utf-8 -*-
"""Tests für den Persona-Signatur-Trigger (membran-konform)."""
from __future__ import annotations

import json
from pathlib import Path

from fusion_hero_os.core.persona_signature import (
    FIXPOINT_FORMULA,
    SIGNATURE_TRIGGER,
    expand_signature_triggers,
    signature_block,
    signature_status,
)


def _unbind(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FUSION_OPERATOR_IDENTITY", str(tmp_path / "missing.json"))
    monkeypatch.delenv("FUSION_AUTHOR_BIND", raising=False)


def _bind(monkeypatch, tmp_path: Path, publication_name: str) -> None:
    vault = tmp_path / "identity.local.json"
    vault.write_text(
        json.dumps(
            {
                "role": "operator",
                "author": {
                    "publication_name": publication_name,
                    "bind_to_publication": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("FUSION_OPERATOR_IDENTITY", str(vault))
    monkeypatch.setenv("FUSION_AUTHOR_BIND", "1")


def test_unbound_signature_uses_abstract_role(monkeypatch, tmp_path: Path):
    _unbind(monkeypatch, tmp_path)
    block = signature_block()
    assert block.startswith("Vorgelegt von Operator.")
    assert FIXPOINT_FORMULA in block
    st = signature_status()
    assert st["author_bind_active"] is False
    assert st["display"] == "Operator"


def test_bound_signature_uses_vault_publication_name(monkeypatch, tmp_path: Path):
    _bind(monkeypatch, tmp_path, "Test Persona")
    block = signature_block()
    assert block.startswith("Vorgelegt von Test Persona.")
    assert signature_status()["author_bind_active"] is True


def test_trigger_expansion_replaces_all_and_is_idempotent(monkeypatch, tmp_path: Path):
    _unbind(monkeypatch, tmp_path)
    text = f"Intro\n{SIGNATURE_TRIGGER}\nMitte {SIGNATURE_TRIGGER} Ende"
    out = expand_signature_triggers(text)
    assert SIGNATURE_TRIGGER not in out
    assert out.count("Vorgelegt von") == 2
    assert expand_signature_triggers(out) == out  # idempotent
    assert "Intro" in out and "Ende" in out


def test_markdown_variant_quotes_every_line(monkeypatch, tmp_path: Path):
    _unbind(monkeypatch, tmp_path)
    md = signature_block(markdown=True)
    assert all(line.startswith("> ") for line in md.splitlines())


def test_module_contains_no_hardcoded_person_name():
    source = Path("fusion_hero_os/core/persona_signature.py").read_text(encoding="utf-8")
    # Membran-Regel: Klarname nur im Kanon-Doc-Layer, nie im Paket.
    assert "Stephan Hagen Urban" not in source
