# -*- coding: utf-8 -*-
"""Archive-anchor passphrase derivation gate (v10 Stage-A).

The pre-v10 salt embedded a device/tailnet identifier. v10 replaces it with a
neutral default and moves legacy verification behind an explicit private env
var (fail-closed). These tests pin that contract:

  * new archives derive from a neutral, identifier-free salt,
  * an explicit passphrase env is used verbatim,
  * legacy verification uses sha256 of the private FUSION_ARCHIVE_LEGACY_SALT,
  * legacy verification fails closed when that var is absent,
  * no personal/device/tailnet literal is reintroduced into the module.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "scripts" / "archiv_anchor_uncommitted.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("archiv_anchor_uncommitted", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def test_default_salt_is_neutral():
    salt = mod.DEFAULT_PASSPHRASE_SALT
    assert not re.search(r"desktop-|kpki9e4|\.ts\.net|tail[0-9a-f]{6,}", salt), (
        f"default salt reintroduces a personal/device identifier: {salt!r}"
    )
    assert salt == "fusion-hero-os|archiv|v10"


def test_new_archive_derivation(monkeypatch):
    monkeypatch.delenv(mod.GPG_PASSPHRASE_ENV, raising=False)
    monkeypatch.delenv(mod.LEGACY_SALT_ENV, raising=False)
    assert mod._default_passphrase() == _sha(mod.DEFAULT_PASSPHRASE_SALT)


def test_explicit_passphrase_used_verbatim(monkeypatch):
    monkeypatch.setenv(mod.GPG_PASSPHRASE_ENV, "explicit-secret")
    assert mod._default_passphrase() == "explicit-secret"
    # even in legacy mode an explicit passphrase takes precedence
    assert mod._default_passphrase(legacy=True) == "explicit-secret"


def test_legacy_override_with_synthetic_salt(monkeypatch):
    monkeypatch.delenv(mod.GPG_PASSPHRASE_ENV, raising=False)
    synthetic = "synthetic-legacy-salt|test-only"
    monkeypatch.setenv(mod.LEGACY_SALT_ENV, synthetic)
    assert mod._default_passphrase(legacy=True) == _sha(synthetic)


def test_legacy_fails_closed_without_salt(monkeypatch):
    monkeypatch.delenv(mod.GPG_PASSPHRASE_ENV, raising=False)
    monkeypatch.delenv(mod.LEGACY_SALT_ENV, raising=False)
    with pytest.raises(SystemExit):
        mod._default_passphrase(legacy=True)


def test_module_has_no_personal_salt_literal():
    text = _MODULE_PATH.read_text(encoding="utf-8")
    assert "kpki9e4" not in text
    assert "tail391adb" not in text
    assert "desktop-kpki9e4|" not in text
