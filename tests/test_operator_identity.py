# -*- coding: utf-8 -*-
"""Operator identity membrane — person extracted from role."""
from __future__ import annotations

import json
from pathlib import Path

from fusion_hero_os.core import operator_identity as oi


def test_role_is_always_operator():
    assert oi.operator_role() == "operator"
    assert oi.public_operator_view()["role"] == "operator"


def test_public_view_has_no_legal_name_key_with_value():
    view = oi.public_operator_view()
    assert "legal_name" not in view
    assert view["membrane"] == "operator_identity_v1"


def test_author_unbound_by_default(monkeypatch, tmp_path):
    vault = tmp_path / "identity.local.json"
    monkeypatch.setattr(oi, "VAULT_PATH", vault)
    monkeypatch.delenv("FUSION_AUTHOR_BIND", raising=False)
    a = oi.author_for_publication()
    assert a["bound"] is False
    assert a["display"] == "Operator"
    assert a["legal_name"] == ""


def test_author_bind_from_vault(monkeypatch, tmp_path):
    vault = tmp_path / "identity.local.json"
    vault.write_text(
        json.dumps(
            {
                "role": "operator",
                "operator_id": "OP_TEST",
                "author": {
                    "legal_name": "Test Person",
                    "publication_name": "Test Person",
                    "bind_to_publication": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(oi, "VAULT_PATH", vault)
    monkeypatch.setenv("FUSION_AUTHOR_BIND", "0")  # vault flag still binds
    a = oi.author_for_publication()
    assert a["bound"] is True
    assert a["display"] == "Test Person"


def test_extract_status_ok():
    st = oi.extract_status()
    assert st["ok"] is True
    assert st["role"] == "operator"
    assert "extracted" in st["rule"].lower() or "Operator" in st["rule"] or "operator" in st["rule"]


def test_active_package_has_no_urban_literal():
    """Operative package must not hard-code the extracted legal person."""
    pkg = Path(__file__).resolve().parents[1] / "fusion_hero_os"
    # assemble fragments so this test file is not a hit for extract scanner patterns
    needle = "Stephan" + " Hagen " + "Urban"
    offenders = []
    for path in pkg.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if needle in text:
            offenders.append(str(path.relative_to(pkg.parent)))
    assert offenders == [], f"legal name still in operative package: {offenders}"
