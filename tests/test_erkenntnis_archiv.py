# -*- coding: utf-8 -*-
"""Hourly -> daily -> weekly -> monthly -> yearly Erkenntnis rollup."""

from __future__ import annotations

from fusion_hero_os.core.erkenntnis_archiv import ErkenntnisArchiv


def _archiv(tmp_path):
    return ErkenntnisArchiv(state_dir=tmp_path / "archiv")


def test_record_lands_in_current_hour_bucket(tmp_path):
    a = _archiv(tmp_path)
    a.record({"insight": "first"}, source="unit-test")
    st = a.status()
    assert st["current_hour_count"] == 1


def test_first_call_seeds_state_without_rolling(tmp_path):
    a = _archiv(tmp_path)
    result = a.force_rollover()
    assert result["rolled"] == []
    assert a._rollover_state_path().is_file()


def test_hour_boundary_reports_into_daily_archive_before_reset(tmp_path):
    a = _archiv(tmp_path)
    a.record({"insight": "during the old hour"}, source="unit-test")
    # simulate "last seen" being an hour that has definitely passed
    a._save_keys({"hour": "2020-01-01T00", "day": "2020-01-01",
                  "week": "2020-W01", "month": "2020-01", "year": "2020"})
    result = a.force_rollover()
    assert "hour" in result["rolled"]
    # hourly bucket got cleared on rollover
    assert not a._hourly_path().is_file()
    # its content was reported into the daily archive first
    day_data = a._daily_path("2020-01-01")
    assert day_data.is_file()
    import json
    day = json.loads(day_data.read_text(encoding="utf-8"))
    assert day["hours"][0]["count"] == 1
    assert day["hours"][0]["records"][0]["insight"] == "during the old hour"


def test_full_cascade_hour_to_year(tmp_path):
    a = _archiv(tmp_path)
    a.record({"insight": "x"}, source="unit-test")
    a._save_keys({"hour": "2019-01-01T00", "day": "2019-01-01",
                  "week": "2019-W01", "month": "2019-01", "year": "2019"})
    result = a.force_rollover()
    assert set(result["rolled"]) >= {"hour", "day", "week", "month"}
    assert a._daily_path("2019-01-01").is_file()
    assert a._weekly_path("2019-W01").is_file()
    assert a._monthly_path("2019-01").is_file()
    assert a._yearly_path("2019").is_file()

    import json
    year = json.loads(a._yearly_path("2019").read_text(encoding="utf-8"))
    assert year["months"][0]["month"] == "2019-01"
    assert year["months"][0]["count"] == 1


def test_no_rollover_within_same_hour(tmp_path):
    a = _archiv(tmp_path)
    a.record({"insight": "a"}, source="unit-test")
    a.record({"insight": "b"}, source="unit-test")
    st = a.status()
    assert st["current_hour_count"] == 2
    # nothing was archived yet - still inside the same hour
    assert not (a.state_dir / "daily").exists()


def test_empty_hour_does_not_create_daily_entry(tmp_path):
    a = _archiv(tmp_path)
    a._save_keys({"hour": "2020-01-01T00", "day": "2020-01-01",
                  "week": "2020-W01", "month": "2020-01", "year": "2020"})
    a.force_rollover()  # nothing was ever record()-ed for that hour
    assert not a._daily_path("2020-01-01").is_file()
