import pytest

from backend import charts
from backend.notifier import TelegramClient


def test_chart_renders_png_with_gaps(thresholds):
    pytest.importorskip("matplotlib")
    pts = [{"ts": 1_760_000_000 + i * 300, "temperature": 22 + i * 0.05, "humidity": 60 + i % 5}
           for i in range(40) if not 10 <= i < 20]  # sensor off for a while
    png = charts.render(pts, 300, thresholds, "Bedroom · test")
    assert png and png.startswith(b"\x89PNG")
    times, temps, _ = charts._with_gaps(pts, 300)
    assert temps.count(None) == 1 and len(times) == len(pts) + 1


def test_chart_needs_two_points(thresholds):
    assert charts.render([], 300, thresholds, "x") is None


def test_send_photo_is_multipart(monkeypatch):
    sent = {}

    def fake_post(self, method, body, content_type, timeout):
        sent.update(method=method, body=body, content_type=content_type)
        return {"ok": True}

    monkeypatch.setattr(TelegramClient, "_post", fake_post)
    TelegramClient("t", "42").send_photo(b"\x89PNGdata", "hi")
    assert sent["method"] == "sendPhoto" and sent["content_type"].startswith("multipart/form-data; boundary=")
    assert b'name="chat_id"\r\n\r\n42' in sent["body"] and b"\x89PNGdata" in sent["body"]
