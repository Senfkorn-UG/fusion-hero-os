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
