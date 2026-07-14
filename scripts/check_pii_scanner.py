#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PII / secret scanning gate for Fusion Hero OS.

Scans tracked text files for likely personal identifiers and secrets:
private emails, IP addresses, MagicDNS/Tailscale hostnames, Supabase project
URLs, cloud tokens/keys and known personal-persona identifiers.

An explicit allowlist (``scripts/pii_allowlist.yaml``) exempts documentation
examples and neutral placeholders. Any *new* finding outside the allowlist
fails the gate (exit code 1), so the CI blocks accidental PII/secret commits.

Usage::

    python scripts/check_pii_scanner.py            # scan repo, fail on findings
    python scripts/check_pii_scanner.py --json      # machine-readable report
    python scripts/check_pii_scanner.py PATH ...     # scan explicit paths
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = REPO_ROOT / "scripts" / "pii_allowlist.yaml"

# --- detection rules ------------------------------------------------------
# Each rule: name -> compiled regex. Kept conservative to limit false positives.
RULES: Dict[str, re.Pattern] = {
    "private_email": re.compile(
        r"\b[a-zA-Z0-9._%+-]+@(?:gmail|googlemail|icloud|hotmail|outlook|yahoo|gmx|web)\.[a-z]{2,}\b"
    ),
    "ipv4_address": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
    ),
    "magicdns_host": re.compile(r"\b[\w-]+\.[\w-]+\.ts\.net\b"),
    "tailscale_authkey": re.compile(r"\btskey-[A-Za-z0-9-]{10,}\b"),
    "supabase_url": re.compile(r"\bhttps?://[a-z0-9]{20}\.supabase\.co\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_api_token": re.compile(r"\b(?:sk|xoxb|ghp|gho|ghs)_[A-Za-z0-9]{20,}\b"),
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "persona_identifier": re.compile(r"\balte[_\- ]?frau[_\- ]?95g\b", re.IGNORECASE),
}

# Blocking rules fail the gate (secrets / real PII). Non-blocking rules are
# reported as warnings only — used for professionalism concerns (e.g. persona
# identifiers) whose full remediation is a separate, import-affecting refactor.
BLOCKING_RULES = {
    "private_email", "ipv4_address", "magicdns_host", "tailscale_authkey",
    "supabase_url", "aws_access_key", "generic_api_token", "private_key_block",
}

# Files/dirs never scanned (binaries, vendored, VCS, generated).
SKIP_DIR_PARTS = {
    ".git", "node_modules", "__pycache__", "target", "dist", "build",
    ".svelte-kit", ".venv", "venv", ".mypy_cache", ".pytest_cache",
}
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".whl", ".so", ".dll", ".dylib", ".bin", ".lock", ".woff", ".woff2",
    ".ttf", ".mp4", ".mp3", ".wasm",
}
# Loopback / documentation-reserved IPs are always allowed (RFC 5737 etc.).
ALWAYS_ALLOWED_IPS = {
    "127.0.0.1", "0.0.0.0", "255.255.255.255", "8.8.8.8", "1.1.1.1",
    "192.0.2.1", "198.51.100.1", "203.0.113.1",
}


def _is_non_public_ip(ip: str) -> bool:
    """True for RFC1918 private, RFC6598/Tailscale CGNAT, loopback and link-local.

    These are not personal data on their own (they identify no external host),
    so they do not block the gate. Any public/routable IP still fails.
    """
    try:
        octets = [int(o) for o in ip.split(".")]
    except ValueError:
        return False
    if len(octets) != 4 or any(o < 0 or o > 255 for o in octets):
        return False
    a, b = octets[0], octets[1]
    if a == 10:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 192 and b == 168:
        return True
    if a == 100 and 64 <= b <= 127:  # RFC6598 CGNAT (Tailscale range)
        return True
    if a == 127 or (a == 169 and b == 254) or a == 0:
        return True
    return False


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    match: str

    def key(self) -> str:
        return f"{self.rule}:{self.match}"

    def to_dict(self) -> Dict[str, object]:
        return {"path": self.path, "line": self.line, "rule": self.rule,
                "match": self.match}


@dataclass
class Allowlist:
    literals: set = field(default_factory=set)  # exact "rule:match" or bare match
    path_globs: List[str] = field(default_factory=list)

    def allows(self, finding: Finding) -> bool:
        if finding.rule == "ipv4_address" and (
            finding.match in ALWAYS_ALLOWED_IPS or _is_non_public_ip(finding.match)
        ):
            return True
        if finding.match in self.literals or finding.key() in self.literals:
            return True
        norm = finding.path.replace(os.sep, "/")
        for glob in self.path_globs:
            # Treat a trailing "/**" as a recursive prefix match (fnmatch does
            # not handle "**" recursively).
            if glob.endswith("/**") and norm.startswith(glob[:-3] + "/"):
                return True
            if fnmatch.fnmatch(norm, glob):
                return True
        return False


def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment, ignoring ``#`` inside single/double quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _parse_simple_yaml(text: str) -> Dict[str, List[str]]:
    """Minimal YAML reader for the allowlist (top-level keys -> list of strings).

    Avoids a PyYAML dependency for the gate. Supports::

        key:
          - value
          - "value"
    """
    result: Dict[str, List[str]] = {}
    current = None
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t", "-")) and line.endswith(":"):
            current = line[:-1].strip()
            result[current] = []
        elif line.lstrip().startswith("-") and current is not None:
            item = line.lstrip()[1:].strip().strip('"').strip("'")
            if item:
                result[current].append(item)
    return result


def load_allowlist(path: Path = ALLOWLIST_PATH) -> Allowlist:
    if not path.exists():
        return Allowlist()
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    return Allowlist(
        literals=set(data.get("allow_literals", [])),
        path_globs=list(data.get("allow_paths", [])),
    )


def _tracked_files() -> List[Path]:
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        )
        files = [REPO_ROOT / line for line in out.splitlines() if line.strip()]
        if files:
            return files
    except Exception:
        pass
    # Fallback: walk the tree.
    files = []
    for root, dirs, names in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_PARTS]
        for name in names:
            files.append(Path(root) / name)
    return files


def _should_skip(path: Path) -> bool:
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def scan_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        rel = str(path.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(path)
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return findings  # binary or unreadable -> skip
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in RULES.items():
            for m in pattern.finditer(line):
                findings.append(Finding(rel, lineno, rule, m.group(0)))
    return findings


def scan(paths: List[Path], allowlist: Allowlist) -> List[Finding]:
    results: List[Finding] = []
    for path in paths:
        if not path.is_file() or _should_skip(path):
            continue
        for finding in scan_file(path):
            if not allowlist.allows(finding):
                results.append(finding)
    return results


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PII/secret scanning gate.")
    parser.add_argument("paths", nargs="*", help="Explicit paths to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)

    allowlist = load_allowlist()
    targets = [Path(p).resolve() for p in args.paths] if args.paths else _tracked_files()
    findings = scan(targets, allowlist)
    blocking = [f for f in findings if f.rule in BLOCKING_RULES]
    warnings = [f for f in findings if f.rule not in BLOCKING_RULES]

    if args.json:
        print(json.dumps({
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
            "blocking": [f.to_dict() for f in blocking],
            "warnings": [f.to_dict() for f in warnings],
        }, indent=2))
    else:
        if blocking:
            print(f"PII/secret scan: {len(blocking)} BLOCKING finding(s):\n")
            for f in blocking:
                print(f"  {f.path}:{f.line}  [{f.rule}]  {f.match}")
            print("\nIf a finding is a documentation example or neutral placeholder,")
            print(f"add it to {ALLOWLIST_PATH.relative_to(REPO_ROOT)} (allow_literals/allow_paths).")
        else:
            print("PII/secret scan: clean (no blocking findings).")
        if warnings:
            print(f"\n{len(warnings)} non-blocking warning(s) (e.g. persona identifiers) "
                  "— tracked for a follow-up refactor PR.")

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
