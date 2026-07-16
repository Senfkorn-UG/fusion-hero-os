# -*- coding: utf-8 -*-
"""Tests fuer Google OAuth connector layer (ohne echte Credentials)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

CONNECTORS = Path(__file__).resolve().parents[1] / "src" / "normal_os" / "connectors"
NORMAL_OS = CONNECTORS.parent
if str(NORMAL_OS) not in sys.path:
    sys.path.insert(0, str(NORMAL_OS))

from connectors.google_oauth import (  # noqa: E402
    CONNECTOR_SCOPES,
    all_connectors_status,
    oauth_status,
)
from connectors.registry import ConnectorRegistry  # noqa: E402


def test_connector_scopes_defined():
    assert "gmail" in CONNECTOR_SCOPES
    assert "google_drive" in CONNECTOR_SCOPES
    assert "google_calendar" in CONNECTOR_SCOPES


def test_oauth_status_not_ready_without_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("FUSION_GOOGLE_OAUTH_DIR", str(tmp_path))
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    st = oauth_status("gmail")
    assert st["ready"] is False
    assert st["include_granted_scopes"] is True
    assert st["reason"]


def test_all_connectors_status_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("FUSION_GOOGLE_OAUTH_DIR", str(tmp_path))
    summary = all_connectors_status()
    assert summary["connector_count"] == 3
    assert "connectors" in summary
    assert "gmail" in summary["connectors"]


def test_registry_includes_google_connectors():
    reg = ConnectorRegistry()
    names = reg.list_connectors()
    assert "gmail" in names
    assert "google_drive" in names
    assert "google_calendar" in names


def test_registry_status_report(monkeypatch, tmp_path):
    monkeypatch.setenv("FUSION_GOOGLE_OAUTH_DIR", str(tmp_path))
    reg = ConnectorRegistry()
    report = reg.status_report()
    assert "google_oauth" in report
    assert "connectors" in report
    assert report["connectors"]["gmail"]["oauth"]["connector_id"] == "gmail"
