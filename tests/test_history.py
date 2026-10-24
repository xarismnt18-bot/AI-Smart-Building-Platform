from datetime import datetime

from backend.history_store import HistoryStore, format_night
from conftest import reading


def store_with_night(tmp_path):
    s = HistoryStore(str(tmp_path / "h.db"))
    start = datetime(2026, 10, 20, 0, 0).timestamp()
    for i in range(0, 8 * 3600, 30):  # 00:00-08:00, one reading per 30 s
        s.record(reading(20 + i / 28800, 70 + (5 if 3 * 3600 <= i < 4 * 3600 else 0)), ts=start + i)
    return s, start


def test_offline_readings_are_not_stored(tmp_path):
    s = HistoryStore(str(tmp_path / "h.db"))
    assert not s.record(reading(online=False))
    assert not s.record(reading(temp=None))
    assert s.rows(0) == []


def test_series_buckets_and_csv(tmp_path):
    s, start = store_with_night(tmp_path)
    hourly = s.series(start, 3600, start + 8 * 3600)
    assert len(hourly) == 8 and all(b["samples"] == 120 for b in hourly)
    assert hourly[3]["humidity"] == 75.0
    text = s.csv(start, start + 60)
    assert text.splitlines()[0] == "time,room,temperature_c,humidity_pct" and len(text.splitlines()) == 4


def test_prune_keeps_recent(tmp_path):
    s, start = store_with_night(tmp_path)
    s.prune(now=start + 31 * 86400)
    assert s.rows(0, start + 40 * 86400) == []


def test_night_summary_flags_hours_over_the_limit(tmp_path, thresholds):
    s, start = store_with_night(tmp_path)
    text = format_night(s, thresholds, now=datetime(2026, 10, 20, 8, 0), hours=8)
    lines = text.splitlines()
    assert lines[0].startswith("🌙 Last 8 hours") and len(lines) == 10
    assert "03:00" in lines[4] and "⚠️" in lines[4] and "⚠️" not in lines[1]


def test_night_summary_without_data(tmp_path, thresholds):
    assert "No readings" in format_night(HistoryStore(str(tmp_path / "e.db")), thresholds)


def test_daily_presence_splits_visits_by_day(tmp_path):
    store = HistoryStore(str(tmp_path / "h.db"))
    day = datetime(2026, 10, 20, 0, 0).timestamp()
    store.visit_started(day - 1800)        # 23:30 the day before ...
    store.visit_ended(day + 3600)          # ... until 01:00
    store.visit_started(day + 10 * 3600)   # 10:00, still in at "now" 10:45
    days = store.daily_presence(2, now=day + 10 * 3600 + 2700)
    assert [d["minutes"] for d in days] == [30, 60 + 45]


def test_open_visit_is_closed_at_the_last_reading(tmp_path):
    store = HistoryStore(str(tmp_path / "h.db"))
    noon = datetime(2026, 10, 20, 12, 0).timestamp()
    store.visit_started(noon)
    store.record(reading(), ts=noon + 600)
    store.close_open_visits()
    days = store.daily_presence(1, now=noon + 3600)
    assert days[-1]["minutes"] == 10
