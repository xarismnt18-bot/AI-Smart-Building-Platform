from datetime import datetime

from backend.presence import ENTER_HOLD_SEC, LEAVE_HOLD_SEC, PresenceWatcher, duration_text


class FakeTelegram:
    enabled = True

    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)


class FakeSensor:
    def __init__(self):
        self.latest = {"room": "Bedroom", "presence": None}


class FakeNotifier:
    muted_until = None


NOON = datetime(2026, 10, 23, 12, 0)


def make(**kw):
    tg, sensor, notifier = FakeTelegram(), FakeSensor(), FakeNotifier()
    return PresenceWatcher(tg, sensor, notifier, **kw), tg, sensor, notifier


def step(w, sensor, present, t, wall=NOON):
    sensor.latest["presence"] = present
    return w.check(now=t, wall=wall)


def test_first_reading_is_silent():
    w, tg, sensor, _ = make()
    step(w, sensor, True, 0)
    assert tg.sent == []


def test_enter_after_hold():
    w, tg, sensor, _ = make()
    step(w, sensor, False, 0)
    step(w, sensor, True, 10)
    assert tg.sent == []
    step(w, sensor, True, 10 + ENTER_HOLD_SEC)
    assert len(tg.sent) == 1 and "came into the Bedroom" in tg.sent[0]


def test_flicker_is_ignored():
    w, tg, sensor, _ = make()
    step(w, sensor, True, 0)
    step(w, sensor, False, 10)
    step(w, sensor, True, 20)          # back before LEAVE_HOLD_SEC
    step(w, sensor, True, 10 + LEAVE_HOLD_SEC + 5)
    assert tg.sent == []


def test_leave_reports_how_long():
    w, tg, sensor, _ = make()
    step(w, sensor, False, 0)
    step(w, sensor, True, 100)
    step(w, sensor, True, 100 + ENTER_HOLD_SEC)
    step(w, sensor, False, 100 + 3600)
    step(w, sensor, False, 100 + 3600 + LEAVE_HOLD_SEC)
    assert "empty now" in tg.sent[-1] and "1 h" in tg.sent[-1]


def test_offline_keeps_state():
    w, tg, sensor, _ = make()
    step(w, sensor, False, 0)
    step(w, sensor, None, 10)
    step(w, sensor, False, 20)
    assert tg.sent == []


def test_muted_off_and_quiet_hours_are_silent():
    for kw, muted, wall in (({"on": False}, None, NOON), ({}, 9e12, NOON),
                            ({"quiet_hours": "23:00-08:00"}, None, datetime(2026, 10, 23, 2, 0))):
        w, tg, sensor, notifier = make(**kw)
        notifier.muted_until = muted
        step(w, sensor, False, 0, wall)
        step(w, sensor, True, 1, wall)
        assert step(w, sensor, True, 1 + ENTER_HOLD_SEC, wall) is not None
        assert tg.sent == []


def test_duration_text():
    assert duration_text(30) == "less than a minute"
    assert duration_text(125) == "2 min"
    assert duration_text(3 * 3600) == "3 h"


def test_since_only_while_someone_is_in():
    w, tg, sensor, _ = make()
    step(w, sensor, False, 0)
    assert w.since is None
    step(w, sensor, True, 10)
    step(w, sensor, True, 10 + ENTER_HOLD_SEC)
    assert w.since is not None


class FakeHistory:
    def __init__(self, hum_an_hour_ago=None):
        self.events = []
        self.hum = hum_an_hour_ago

    def visit_started(self, ts):
        self.events.append("in")

    def visit_ended(self, ts):
        self.events.append("out")

    def rows(self, since, until):
        return [(since, "Bedroom", 24.0, self.hum)] if self.hum is not None else []


def make_with(history, **kw):
    tg, sensor, notifier = FakeTelegram(), FakeSensor(), FakeNotifier()
    return PresenceWatcher(tg, sensor, notifier, history=history, **kw), tg, sensor


def test_visits_are_logged():
    h = FakeHistory()
    w, tg, sensor = make_with(h)
    step(w, sensor, True, 0)                       # in at start-up
    step(w, sensor, False, 10)
    step(w, sensor, False, 10 + LEAVE_HOLD_SEC)
    step(w, sensor, True, 200)
    step(w, sensor, True, 200 + ENTER_HOLD_SEC)
    assert h.events == ["in", "out", "in"]
    assert w.occupied and not w.empty


def test_airing_reminder_after_a_long_stay_with_rising_humidity():
    from backend.presence import AIR_AFTER_SEC
    w, tg, sensor = make_with(FakeHistory(hum_an_hour_ago=52))
    sensor.latest["humidity"] = 58
    step(w, sensor, False, 0)
    step(w, sensor, True, 10)
    step(w, sensor, True, 10 + ENTER_HOLD_SEC)
    step(w, sensor, True, 10 + AIR_AFTER_SEC - 60)    # too early
    assert not any("Open the window" in m for m in tg.sent)
    step(w, sensor, True, 10 + AIR_AFTER_SEC + 1)
    assert "from 52% to 58%" in tg.sent[-1]
    step(w, sensor, True, 10 + AIR_AFTER_SEC + 600)   # once per stay
    assert sum("Open the window" in m for m in tg.sent) == 1


def test_no_airing_reminder_when_humidity_is_steady():
    from backend.presence import AIR_AFTER_SEC
    w, tg, sensor = make_with(FakeHistory(hum_an_hour_ago=50))
    sensor.latest["humidity"] = 51
    step(w, sensor, True, 0)
    step(w, sensor, True, AIR_AFTER_SEC + 100)
    assert not any("Open the window" in m for m in tg.sent)
