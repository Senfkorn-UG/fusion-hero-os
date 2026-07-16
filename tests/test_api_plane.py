# -*- coding: utf-8 -*-
"""API plane membrane — hyperraum vs business."""
from __future__ import annotations

from fusion_hero_os.core.api_plane import (
    PLANE_BUSINESS,
    PLANE_HYPERRAUM,
    assert_plane_safe_payload,
    classify_path,
    planes_status,
)


def test_business_paths():
    for p in (
        "/api/v1/business",
        "/api/v1/business/pricing",
        "/api/businessplan",
        "/api/health",
        "/api/metrics",
        "/api/gui/status",
    ):
        c = classify_path(p)
        assert c["plane"] == PLANE_BUSINESS, p


def test_hyperraum_paths():
    for p in (
        "/api/hyperraum",
        "/api/hyperraum/status",
        "/api/grok/interconnect",
        "/api/mainframe/site/status",
        "/api/autoload/status",
        "/mainframe/grok",
        "/api/agents",
    ):
        c = classify_path(p)
        assert c["plane"] == PLANE_HYPERRAUM, p


def test_longest_prefix_business_v1():
    c = classify_path("/api/v1/business/pricing?tier=x")
    assert c["plane"] == PLANE_BUSINESS
    assert "v1/business" in c["match_prefix"] or c["match_prefix"].startswith("/api/v1/business")


def test_planes_status_shape():
    st = planes_status()
    assert st["ok"] is True
    assert "hyperraum" in st["planes"]
    assert "business" in st["planes"]
    assert st["planes"]["hyperraum"]["privacy"] == "half_private"
    assert st["planes"]["business"]["privacy"] == "product"


def test_business_payload_guard():
    ok, issues = assert_plane_safe_payload(
        PLANE_BUSINESS, {"quote": 1.0, "tier": "inference_standard"}
    )
    assert ok is True
    assert issues == []
    ok2, issues2 = assert_plane_safe_payload(
        PLANE_BUSINESS, {"author": {"legal_name": "should-not-leak"}}
    )
    assert ok2 is False
    assert any("legal_name" in i for i in issues2)


def test_hyperraum_allows_richer_keys():
    ok, issues = assert_plane_safe_payload(
        PLANE_HYPERRAUM, {"organs": {"operator_identity": {"public": {}}}}
    )
    assert ok is True
