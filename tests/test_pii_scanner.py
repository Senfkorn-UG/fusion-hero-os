# -*- coding: utf-8 -*-
"""Tests for the PII/secret scanner gate (scripts/check_pii_scanner.py)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = REPO_ROOT / "scripts" / "check_pii_scanner.py"

_spec = importlib.util.spec_from_file_location("pii_scanner", SCANNER_PATH)
pii = importlib.util.module_from_spec(_spec)
sys.modules["pii_scanner"] = pii  # required so @dataclass can resolve the module
_spec.loader.exec_module(pii)


def test_detects_planted_secrets(tmp_path):
    f = tmp_path / "leak.txt"
    f.write_text(
        "email: victim@gmail.com\n"
        "host: box.tailnet.ts.net\n"
        "token: ghp_abcdefghijklmnopqrstuvwxyz0123\n"
        "supa: https://abcdefghijklmnopqrst.supabase.co\n",
        encoding="utf-8",
    )
    findings = pii.scan([f], pii.Allowlist())
    rules = {x.rule for x in findings}
    assert "private_email" in rules
    assert "magicdns_host" in rules
    assert "generic_api_token" in rules
    assert "supabase_url" in rules


def test_allowlist_literals_and_paths(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("contact user@example.com or admin@gmail.com\n", encoding="utf-8")
    allow = pii.Allowlist(literals={"admin@gmail.com"})
    findings = pii.scan([f], allow)
    assert all(x.match != "admin@gmail.com" for x in findings)


def test_private_and_cgnat_ips_are_not_flagged(tmp_path):
    f = tmp_path / "net.txt"
    f.write_text("10.0.0.5 192.168.1.1 172.16.0.1 100.64.1.2 8.8.4.4\n", encoding="utf-8")
    findings = pii.scan([f], pii.Allowlist())
    ips = {x.match for x in findings if x.rule == "ipv4_address"}
    assert "8.8.4.4" in ips  # public IP flagged
    assert "10.0.0.5" not in ips
    assert "100.64.1.2" not in ips  # CGNAT / Tailscale


def test_non_public_ip_classifier():
    assert pii._is_non_public_ip("192.168.0.1")
    assert pii._is_non_public_ip("100.100.100.100")  # CGNAT
    assert pii._is_non_public_ip("127.0.0.1")
    assert not pii._is_non_public_ip("9.9.9.9")  # public


def test_yaml_parser_preserves_hash_inside_quotes():
    """A quoted literal containing '#' must not be truncated as a comment."""
    text = (
        "allow_literals:\n"
        '  - "value#withhash"   # trailing comment stripped\n'
        "  - plain_value\n"
        "allow_paths:\n"
        "  - 'a#b/c.py'\n"
    )
    data = pii._parse_simple_yaml(text)
    assert data["allow_literals"] == ["value#withhash", "plain_value"]
    assert data["allow_paths"] == ["a#b/c.py"]


def test_strip_comment_helper():
    assert pii._strip_comment("foo # bar") == "foo "
    assert pii._strip_comment('"a#b" # c') == '"a#b" '
    assert pii._strip_comment("no comment here") == "no comment here"


def _write_denylist(tmp_path):
    dl = tmp_path / "dl.yaml"
    dl.write_text(
        "denylist_literals:\n"
        "  - synthetic-device-9000\n"
        '  - "Jane Q. Testperson"\n'
        "denylist_patterns:\n"
        '  - "acme (corp|inc)"\n',
        encoding="utf-8",
    )
    return dl


def test_denylist_catches_device_and_name_and_company(tmp_path):
    """Synthetic bare device id, legal name and company are caught as blocking."""
    dl = pii.load_denylist(_write_denylist(tmp_path))
    f = tmp_path / "cfg.txt"
    f.write_text(
        "device = synthetic-device-9000\n"
        "owner: Jane Q. Testperson\n"
        "vendor: ACME Inc\n"  # case-insensitive pattern match
        "unrelated: nothing to see\n",
        encoding="utf-8",
    )
    findings = pii.scan([f], pii.Allowlist(), dl)
    matches = {x.match.lower() for x in findings if x.rule == pii.DENYLIST_RULE}
    assert "synthetic-device-9000" in matches
    assert "jane q. testperson" in matches
    assert "acme inc" in matches
    assert pii.DENYLIST_RULE in pii.BLOCKING_RULES


def test_denylist_hits_bypass_allowlist(tmp_path):
    """A denylist hit is never exempted, even if the allowlist would allow it."""
    dl = pii.load_denylist(_write_denylist(tmp_path))
    f = tmp_path / "cfg.txt"
    f.write_text("device = synthetic-device-9000\n", encoding="utf-8")
    allow = pii.Allowlist(literals={"synthetic-device-9000"})
    findings = pii.scan([f], allow, dl)
    assert any(x.match == "synthetic-device-9000" for x in findings)


def test_denylist_source_contains_no_real_pii():
    """The committed scanner must not embed real denylist values."""
    src = pii.SCANNER_PATH.read_text(encoding="utf-8") if hasattr(pii, "SCANNER_PATH") \
        else SCANNER_PATH.read_text(encoding="utf-8")
    for token in ("der Maintainer", "phone-node", "fusionheroos"):
        assert token.lower() not in src.lower()


def test_denylist_absent_is_noop(tmp_path, monkeypatch):
    """No configured denylist -> empty, built-in rules still run."""
    monkeypatch.delenv(pii.DENYLIST_ENV, raising=False)
    assert pii.load_denylist(None).patterns == []


def test_denylist_missing_env_path_fails_closed(tmp_path, monkeypatch):
    """An explicitly configured but missing path raises (fail-closed)."""
    monkeypatch.setenv(pii.DENYLIST_ENV, str(tmp_path / "does-not-exist.yaml"))
    try:
        pii.load_denylist(None)
    except pii.DenylistError:
        return
    raise AssertionError("expected DenylistError for missing configured path")
