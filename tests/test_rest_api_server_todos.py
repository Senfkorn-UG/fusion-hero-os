"""Tests fuer die behobenen TODOs in 03_Code/reference/rest_api_server.py:

- GPU-Detection (_detect_gpu_count) statt hartcodierter 0
- /mod/apply echte heroic_orchestration-Integration (Layer 1 Geltung + Layer 3
  Hygiene aus 01_Framework/heroic-core-foundation) statt hartcodiertem
  "approved".
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "03_Code", "reference"))

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import rest_api_server as ras  # noqa: E402


def test_detect_gpu_count_returns_int_never_raises():
    count = ras._detect_gpu_count()
    assert isinstance(count, int)
    assert count >= 0


def test_input_factors_uses_real_detection(monkeypatch):
    monkeypatch.setattr(ras, "_detect_gpu_count", lambda: 2)
    client = TestClient(ras.app)
    resp = client.get("/api/input-factors")
    assert resp.status_code == 200
    assert resp.json()["gpu_count"] == 2


def test_mod_apply_flags_hygiene_issue_code():
    """Text mit 'wie ... beweist' triggert die metaphor_proof-Hygiene-Regel."""
    client = TestClient(ras.app)
    code = "# wie ein Beispiel beweist dies eindeutig die Annahme\nx = 1"
    resp = client.post("/mod/apply", json={"code": code})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "flagged"
    assert len(body["hygiene_issues"]) >= 1
    assert body["geltung"] == "flagged_for_review"


def test_mod_apply_approves_clean_code():
    client = TestClient(ras.app)
    resp = client.post("/mod/apply", json={"code": "x = 1 + 1\nprint(x)\n"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["geltung"] == "proven"
    assert body["hygiene_issues"] == []
