from ai.engines.prediction_engine import MAX_DATA_AGE_SEC, PredictionEngine
from ai.engines.thresholds import Thresholds


def history(t_end, n=20, step=30, temp=22.0):
    return [{"ts": t_end - (n - 1 - i) * step, "temperature": temp + i * 0.01, "humidity": 50.0}
            for i in range(n)]


def test_fresh_data_gives_a_forecast():
    now = 1_800_000_000
    p = PredictionEngine().predict_all(history(now - 5), Thresholds(), now=now)
    assert p["stale"] is False and p["temperature"]["predicted"] is not None
    assert p["data_age_sec"] == 5 and p["generated_at"] == now


def test_old_data_gives_no_forecast():
    now = 1_800_000_000
    p = PredictionEngine().predict_all(history(now - MAX_DATA_AGE_SEC - 60), Thresholds(), now=now)
    assert p["stale"] is True
    for metric in ("temperature", "humidity"):
        assert p[metric]["predicted"] is None and p[metric]["confidence"] == 0 and p[metric]["stale"]


def test_no_data_is_stale():
    p = PredictionEngine().predict_all([], Thresholds(), now=1_800_000_000)
    assert p["stale"] is True and p["data_age_sec"] is None
