from backend.alerts import active_alerts
from conftest import reading


def keys(latest, t):
    return {a.key for a in active_alerts(latest, t)}


def test_comfortable_room_has_no_alerts(thresholds):
    assert keys(reading(22, 50), thresholds) == set()


def test_value_alerts(thresholds):
    assert keys(reading(28, 75), thresholds) == {"temp_high", "humidity_high"}
    assert keys(reading(17, 30), thresholds) == {"temp_low", "humidity_low"}


def test_limits_are_exclusive(thresholds):
    assert keys(reading(27, 70), thresholds) == set()


def test_broker_offline_wins_over_sensor_offline(thresholds):
    assert keys(reading(online=False, broker=False), thresholds) == {"broker_offline"}
    assert keys(reading(online=False), thresholds) == {"sensor_offline"}


def test_missing_values_raise_no_value_alerts(thresholds):
    assert keys(reading(None, None, online=False), thresholds) == {"sensor_offline"}
