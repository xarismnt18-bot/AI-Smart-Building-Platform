from datetime import datetime
from unittest import mock

from backend.ikea import MIN_ON_SEC, AlertLamp
from conftest import FakeOutlet

DAY, NIGHT = datetime(2026, 10, 20, 15, 0), datetime(2026, 10, 20, 23, 30)


def lamp(**kw):
    outlet = FakeOutlet(**kw)
    return AlertLamp(outlet, "23:00-08:00"), outlet


def test_on_with_alert_off_after_minimum_time():
    l, o = lamp()
    l.sync({"humidity_high"}, DAY)
    l.sync(set(), DAY)
    assert o.calls == [True]  # held for MIN_ON_SEC
    with mock.patch("time.monotonic", return_value=1e9 + MIN_ON_SEC):
        l.sync(set(), DAY)
    assert o.calls == [True, False] and not l.lit_by_alert


def test_quiet_hours_and_connectivity_alerts_stay_dark():
    l, o = lamp()
    l.sync({"temp_high"}, NIGHT)
    l.sync({"sensor_offline", "broker_offline"}, DAY)
    assert o.calls == []


def test_switches_off_when_quiet_hours_start():
    l, o = lamp()
    l.sync({"humidity_high"}, DAY)
    l.sync({"humidity_high"}, NIGHT)
    assert o.calls == [True, False]


def test_manual_off_snoozes_until_alert_clears():
    l, o = lamp()
    l.sync({"humidity_high"}, DAY)
    l.manual(False, alert_active=True)
    l.sync({"humidity_high"}, DAY)
    assert o.calls == [True, False]
    l.sync(set(), DAY)
    l.sync({"humidity_high"}, DAY)
    assert o.calls[-1] is True


def test_auto_off_and_hub_errors():
    l, o = lamp()
    l.auto = False
    l.sync({"humidity_high"}, DAY)
    assert o.calls == []
    broken, _ = lamp(fail=True)
    broken.sync({"humidity_high"}, DAY)  # logged, not raised
    assert not broken.lit_by_alert
