import time

import pytest

from backend import notifier as N
from backend.ikea import AlertLamp
from conftest import FakeOutlet, FakeSensor, FakeSettings, FakeTelegram, reading


@pytest.fixture
def setup(thresholds, monkeypatch):
    sensor, telegram = FakeSensor(reading()), FakeTelegram()
    n = N.AlertNotifier(telegram, sensor, FakeSettings(thresholds), check_sec=15, cooldown_min=30)
    n._started_at = time.monotonic() - N.STARTUP_GRACE_SEC - 1  # past the start-up grace
    return n, sensor, telegram


def test_alert_needs_two_checks(setup):
    n, sensor, telegram = setup
    sensor.latest = reading(hum=80)
    n.check()
    assert telegram.sent == []
    n.check()
    assert len(telegram.sent) == 1 and "humidity is high" in telegram.sent[0]


def test_one_message_per_episode_then_resolved(setup):
    n, sensor, telegram = setup
    sensor.latest = reading(hum=80)
    for _ in range(5):
        n.check()
    assert len(telegram.sent) == 1
    sensor.latest = reading(hum=60)
    n.check(); n.check()
    assert len(telegram.sent) == 2 and "back to normal" in telegram.sent[1]


def test_cooldown_blocks_a_quick_repeat(setup):
    n, sensor, telegram = setup
    for hum in (80, 80, 60, 60, 80, 80):
        sensor.latest = reading(hum=hum)
        n.check()
    assert len(telegram.sent) == 2  # alert + resolved; the comeback is inside the cooldown


def test_sensor_offline_freezes_value_alerts(setup):
    n, sensor, telegram = setup
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    sensor.latest = reading(hum=None, temp=None, online=False)
    n.check(); n.check()
    assert not any("back to normal" in m for m in telegram.sent)
    assert any("stopped sending" in m for m in telegram.sent)


def test_startup_grace_hides_connectivity(setup):
    n, sensor, telegram = setup
    n._started_at = time.monotonic()
    sensor.latest = reading(online=False, temp=None, hum=None)
    n.check(); n.check()
    assert telegram.sent == []


def test_muted_alert_is_reported_after_unmute(setup):
    n, sensor, telegram = setup
    n.mute(3600)
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    assert telegram.sent == []
    n.unmute()
    n.check(); n.check(); n.check()
    assert len(telegram.sent) == 1


def test_lamp_follows_reported_alerts(setup):
    n, sensor, _ = setup
    outlet = FakeOutlet()
    n.lamp = AlertLamp(outlet, quiet_hours="")
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    assert outlet.calls == [True]
