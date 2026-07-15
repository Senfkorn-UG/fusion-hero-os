# -*- coding: utf-8 -*-
"""Archive-anchor key-derivation gate (v10 Stage-A, archiv_version 2.0).

v10 replaces the pre-v10 device/tailnet salt AND the weak, unversioned
``sha256(secret)`` passphrase derivation with a versioned, memory-hard
``hashlib.scrypt`` KDF using a random per-archive salt stored (non-secret) in
the manifest. These tests pin that contract:

  * the default secret material is neutral / identifier-free,
  * ``_secret_material`` prefers an explicit env secret and labels its source,
  * ``_derive_passphrase`` is a deterministic, salted, versioned scrypt KDF,
  * a different per-archive salt yields a different passphrase,
  * ``_content_digest`` is a plain SHA256 over NON-SECRET bytes (integrity
    only) and is kept distinct from credential derivation,
  * written manifests are v2, carry a non-secret ``kdf`` block, and no longer
    embed a passphrase hash,
  * the removed pre-v10 legacy sha256 write-path is gone,
  * no personal/device/tailnet literal is reintroduced into the module.

The tests deliberately never compute ``sha256`` over secret/salt material —
KDF assertions use ``hashlib.scrypt`` reference vectors so the test suite does
not itself trip the weak-sensitive-data-hashing rule.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "scripts" / "archiv_anchor_uncommitted.py"
_RECOVER_PATH = ROOT / "archiv" / "obfuscated" / "recover_obfuscated.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("archiv_anchor_uncommitted", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


def test_default_salt_is_neutral():
    salt = mod.DEFAULT_PASSPHRASE_SALT
    assert not re.search(r"desktop-|kpki9e4|\.ts\.net|tail[0-9a-f]{6,}", salt), (
        f"default secret reintroduces a personal/device identifier: {salt!r}"
    )
    assert salt == "fusion-hero-os|archiv|v10"


def test_secret_material_default(monkeypatch):
    monkeypatch.delenv(mod.GPG_PASSPHRASE_ENV, raising=False)
    secret, source = mod._secret_material()
    assert secret == mod.DEFAULT_PASSPHRASE_SALT.encode("utf-8")
    assert source == "default-salt"


def test_secret_material_explicit_env(monkeypatch):
    monkeypatch.setenv(mod.GPG_PASSPHRASE_ENV, "explicit-secret")
    secret, source = mod._secret_material()
    assert secret == b"explicit-secret"
    assert source == "env:FUSION_ARCHIV_GPG_PASSPHRASE"


def test_kdf_is_versioned_scrypt():
    assert mod.KDF_NAME == "scrypt"
    assert mod.KDF_VERSION == 2
    # Memory-hard cost parameters must stay within the declared maxmem budget.
    assert 128 * mod.KDF_N * mod.KDF_R * mod.KDF_P <= mod.KDF_MAXMEM


def test_derive_passphrase_matches_scrypt_reference():
    secret = b"unit-test-secret"
    kdf_salt = b"0123456789abcdef"
    expected = base64.b64encode(
        hashlib.scrypt(
            secret,
            salt=kdf_salt,
            n=mod.KDF_N,
            r=mod.KDF_R,
            p=mod.KDF_P,
            dklen=mod.KDF_DKLEN,
            maxmem=mod.KDF_MAXMEM,
        )
    ).decode("ascii")
    assert mod._derive_passphrase(secret, kdf_salt) == expected


def test_derive_passphrase_salt_dependent():
    secret = b"unit-test-secret"
    a = mod._derive_passphrase(secret, b"salt-aaaaaaaaaaa")
    b = mod._derive_passphrase(secret, b"salt-bbbbbbbbbbb")
    assert a != b


def test_content_digest_is_plain_sha256_of_nonsecret():
    # NON-SECRET literal: this asserts the integrity helper is ordinary SHA256,
    # separate from the KDF. No secret/salt is hashed here.
    payload = b"the quick brown fox"
    assert mod._content_digest(payload) == hashlib.sha256(payload).hexdigest()


def test_legacy_sha256_write_path_removed():
    text = _MODULE_PATH.read_text(encoding="utf-8")
    assert "_default_passphrase" not in text
    assert "FUSION_ARCHIVE_LEGACY_SALT" not in text
    assert "--legacy-salt" not in text
    assert "passphrase_sha256" not in text
    assert not hasattr(mod, "_default_passphrase")


@pytest.mark.skipif(shutil.which("gpg") is None, reason="gpg not available")
def test_manifest_v2_and_roundtrip(monkeypatch):
    monkeypatch.delenv(mod.GPG_PASSPHRASE_ENV, raising=False)
    work = ROOT / "_archive_v2_roundtrip_tmp"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    try:
        # RECOVER.sh resolves recover_obfuscated.py one dir above the archive.
        shutil.copy(_RECOVER_PATH, work / "recover_obfuscated.py")
        src = work / "payload.txt"
        src.write_bytes(b"deterministic integrity payload\n")

        secret, source = mod._secret_material()
        out_dir = work / "arch"
        manifest = mod.anchor_files([src], out_dir, secret, source)

        assert manifest["archiv_version"] == "2.0"
        assert manifest["algorithm"].startswith("scrypt-kdf")
        assert "passphrase_sha256" not in manifest
        assert "passphrase_hint" not in manifest

        kdf = manifest["kdf"]
        assert kdf["name"] == "scrypt" and kdf["version"] == 2
        assert kdf["secret_source"] == source
        assert len(base64.b64decode(kdf["salt_b64"])) == 16

        # Integrity digest is a plain content SHA256 over the source bytes.
        assert manifest["entries"][0]["sha256"] == hashlib.sha256(src.read_bytes()).hexdigest()

        # Manifest self-digest is over the entries only.
        assert manifest["manifest_sha256"] == hashlib.sha256(
            json.dumps(manifest["entries"], sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        result = subprocess.run(
            ["bash", str(out_dir / "RECOVER.sh")],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr[-500:]
        restored = out_dir / "restored" / str(src.resolve().relative_to(ROOT))
        assert restored.read_bytes() == src.read_bytes()
    finally:
        shutil.rmtree(work)


def test_module_has_no_personal_salt_literal():
    text = _MODULE_PATH.read_text(encoding="utf-8")
    assert "kpki9e4" not in text
    assert "tail391adb" not in text
    assert "mainframe|" not in text
