import json
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


def test_restart_does_not_repeat_alerts(thresholds, tmp_path):
    state = str(tmp_path / "alert_state.json")
    sensor, telegram = FakeSensor(reading(hum=80)), FakeTelegram()

    def notifier():
        n = N.AlertNotifier(telegram, sensor, FakeSettings(thresholds), 15, 30, state_path=state)
        n._started_at = time.monotonic() - N.STARTUP_GRACE_SEC - 1
        return n

    first = notifier()
    first.check(); first.check()
    assert len(telegram.sent) == 1
    second = notifier()  # Thalpos restarted, alert still active
    for _ in range(4):
        second.check()
    assert len(telegram.sent) == 1
    sensor.latest = reading(hum=60)
    second.check(); second.check()
    assert "back to normal" in telegram.sent[-1]


def test_stuck_sensor_alert_is_text_only(thresholds, tmp_path):
    from backend.history_store import HistoryStore

    store = HistoryStore(str(tmp_path / "h.db"))
    now = time.time()
    for i in range(int(3.2 * 3600 / 30)):
        store.record(reading(25 + i * 0.001, 95), ts=now - i * 30)
    sensor, telegram = FakeSensor(reading(25, 95)), FakeTelegram()
    n = N.AlertNotifier(telegram, sensor, FakeSettings(thresholds), 15, 30, history=store)
    n._started_at = time.monotonic() - N.STARTUP_GRACE_SEC - 1
    n.check(); n.check()
    assert any("may be stuck" in m and "95%" in m for m in telegram.sent)


def test_alert_log_records_start_delivery_and_end(thresholds, tmp_path):
    from backend.history_store import HistoryStore

    store = HistoryStore(str(tmp_path / "h.db"))
    sensor, telegram = FakeSensor(reading(hum=80)), FakeTelegram()
    n = N.AlertNotifier(telegram, sensor, FakeSettings(thresholds), 15, 30, history=store)
    n._started_at = time.monotonic() - N.STARTUP_GRACE_SEC - 1
    n.check(); n.check()
    [event] = store.alert_events(time.time() - 60)
    assert event["key"] == "humidity_high" and event["ended"] is None and event["notified"]
    assert "humidity is high" in event["message"]

    sensor.latest = reading(hum=60)
    n.check(); n.check()
    [event] = store.alert_events(time.time() - 60)
    assert event["ended"] is not None and event["duration_sec"] >= 0


def test_restart_closes_alerts_that_are_no_longer_active(tmp_path):
    from backend.history_store import HistoryStore

    store = HistoryStore(str(tmp_path / "h.db"))
    store.alert_started("temp_high", "warm")
    store.alert_started("temp_high", "warm again")  # already open: no duplicate
    store.alert_started("humidity_high", "damp")
    store.close_open_alerts(keep={"humidity_high"})
    events = {e["key"]: e for e in store.alert_events(time.time() - 60)}
    assert len(store.alert_events(time.time() - 60)) == 2
    assert events["temp_high"]["ended"] is not None and events["humidity_high"]["ended"] is None


def test_alert_active_across_restart_appears_in_log(thresholds, tmp_path):
    from backend.history_store import HistoryStore

    state = tmp_path / "state.json"
    state.write_text(json.dumps({"notified": ["humidity_high"], "last_sent": {"humidity_high": time.time() - 600}}))
    store = HistoryStore(str(tmp_path / "h.db"))
    N.AlertNotifier(FakeTelegram(), FakeSensor(reading(hum=80)), FakeSettings(thresholds), 15, 30,
                    history=store, state_path=str(state))
    [event] = store.alert_events(time.time() - 3600)
    assert event["key"] == "humidity_high" and event["ended"] is None and event["notified"]


class FakePresence:
    def __init__(self, empty):
        self.alerts_only_present = True
        self.empty = empty


def test_comfort_alert_waits_while_room_is_empty(setup):
    n, sensor, telegram = setup
    n.presence = FakePresence(empty=True)
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    assert telegram.sent == []
    n.presence.empty = False          # someone comes in: now it is reported
    n.check(); n.check()
    assert len(telegram.sent) == 1 and "humidity is high" in telegram.sent[0]


def test_empty_room_does_not_clear_an_alert(setup):
    n, sensor, telegram = setup
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    n.presence = FakePresence(empty=True)
    sensor.latest = reading(hum=60)
    n.check(); n.check()
    assert len(telegram.sent) == 1     # no "back to normal" while nobody is in
    n.presence.empty = False
    n.check(); n.check()
    assert "back to normal" in telegram.sent[-1]


def test_critical_humidity_gets_through_an_empty_room(setup, thresholds):
    n, sensor, telegram = setup
    n.presence = FakePresence(empty=True)
    sensor.latest = reading(hum=thresholds.HUMIDITY_CRITICAL + 1)
    n.check(); n.check()
    assert len(telegram.sent) == 1


def test_setting_off_alerts_as_before(setup):
    n, sensor, telegram = setup
    n.presence = FakePresence(empty=True)
    n.presence.alerts_only_present = False
    sensor.latest = reading(hum=80)
    n.check(); n.check()
    assert len(telegram.sent) == 1
