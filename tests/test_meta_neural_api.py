# -*- coding: utf-8 -*-
"""API-level tests for the meta-neural slice (happy path + unsafe-path denial)."""

from __future__ import annotations

import importlib

import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")
pytest.importorskip("httpx")

from fusion_hero_os.meta import api as meta_api  # noqa: E402


@pytest.fixture()
def client():
    # Fresh service per test so consent/audit state does not leak between tests.
    importlib.reload(meta_api)
    from fastapi.testclient import TestClient

    return TestClient(meta_api.create_app())


def test_api_happy_path(client):
    subj = "subj_api"
    purposes = ["ingest", "working_memory", "association", "optimization", "audit_read"]
    grants = {}
    for p in purposes:
        r = client.post("/meta/consent", json={"subject_id": subj, "purpose": p})
        assert r.status_code == 200, r.text
        grants[p] = r.json()["grant_id"]

    r = client.post("/meta/ingest", json={
        "subject_id": subj, "grant_id": grants["ingest"],
        "nodes": [
            {"node_id": "a", "type": "concept", "dimensions": {"salience": 0.9}},
            {"node_id": "b", "type": "concept", "dimensions": {"salience": 0.5}},
        ],
        "edges": [{"edge_id": "e1", "type": "relates_to", "source": "a", "target": "b"}],
    })
    assert r.status_code == 200, r.text
    assert r.json()["node_count"] == 2

    r = client.post("/meta/activate", json={
        "subject_id": subj, "grant_id": grants["working_memory"],
        "activations": {"a": 0.9, "b": 0.6}, "steps": 1,
    })
    assert r.status_code == 200
    assert r.json()["step_index"] == 1

    r = client.post("/meta/associate", json={
        "subject_id": subj, "grant_id": grants["association"]})
    assert r.status_code == 200
    assert "is_contraction" in r.json()

    r = client.post("/meta/optimize", json={
        "subject_id": subj, "grant_id": grants["optimization"],
        "cardinality": 1, "backend": "numpy", "seed": 7, "steps": 800,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Not quantum" in body["note"]
    assert set(body["assignment"]) == {"a", "b"}

    r = client.get(f"/meta/audit/{subj}", params={"grant_id": grants["audit_read"]})
    assert r.status_code == 200
    assert r.json()["chain_valid"] is True


def test_api_denies_ingest_without_consent(client):
    r = client.post("/meta/ingest", json={
        "subject_id": "nobody", "grant_id": "no-grant",
        "nodes": [], "edges": [],
    })
    assert r.status_code == 403


def test_api_denies_optimize_without_consent(client):
    r = client.post("/meta/optimize", json={
        "subject_id": "nobody", "grant_id": "no-grant"})
    assert r.status_code == 403
