import io
import json
from datetime import datetime
from unittest import mock

from backend import voice as V
from conftest import FakeSensor, FakeSettings, reading


def test_quiet_hours_wrap_midnight():
    q = "23:00-08:00"
    assert V.in_quiet_hours(datetime(2026, 1, 1, 23, 30), q)
    assert V.in_quiet_hours(datetime(2026, 1, 1, 7, 59), q)
    assert not V.in_quiet_hours(datetime(2026, 1, 1, 8, 0), q)
    assert not V.in_quiet_hours(datetime(2026, 1, 1, 12, 0), "")


def test_spoken_text_has_no_emoji(thresholds):
    text = V.spoken("humidity_high", reading(hum=82.4), thresholds)
    assert "82 percent" in text and text.isascii()


def test_status_sentence(thresholds):
    assert V.status_sentence(reading(21.44, 55), thresholds) == (
        "The bedroom is 21.4 degrees, with 55 percent humidity. Everything is in the comfort range.")
    assert "dehumidifier" in V.status_sentence(reading(hum=80), thresholds)
    assert "no live readings" in V.status_sentence(reading(online=False, age=400), thresholds)


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_publisher_pushes_only_changes(thresholds):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append(json.loads(req.data))
        assert "AIOS" in req.headers["User-agent"]  # Cloudflare blocks Python's default UA
        return _Resp(b'{"success": true}')

    sensor = FakeSensor(reading(22, 50))
    p = V.VoiceStatusPublisher(V.VoiceAnnouncer("tok", "dev", ""), sensor, FakeSettings(thresholds), "AIOS_STATUS", 60)
    with mock.patch("urllib.request.urlopen", fake_urlopen):
        assert p.publish() and not p.publish()
        sensor.latest = reading(23, 50)
        assert p.publish()
        p.stop()  # never started: must not spend a request
    assert len(calls) == 2 and calls[0]["variable"] == "AIOS_STATUS"


def test_voice_budget():
    v = V.VoiceAnnouncer("tok", "dev", "")
    t0 = datetime(2026, 10, 20, 10, 0)
    assert v.should_speak("humidity_high", t0)
    v.spoke("humidity_high", t0)
    assert not v.should_speak("humidity_high", t0.replace(hour=15))  # same alert within 6 h
    assert v.should_speak("humidity_high", t0.replace(hour=16, minute=1))
    for i in range(4):
        v.spoke(f"k{i}", t0)
    assert not v.should_speak("temp_high", t0.replace(hour=17))  # 5 a day
    assert v.should_speak("temp_high", datetime(2026, 10, 21, 10, 0))  # new day
