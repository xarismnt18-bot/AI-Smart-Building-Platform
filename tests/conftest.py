import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ai.engines import Thresholds  # noqa: E402


@pytest.fixture
def thresholds():
    return Thresholds(TEMP_LOW=18, TEMP_HIGH=27, TEMP_CRITICAL=32,
                      HUMIDITY_LOW=35, HUMIDITY_HIGH=70, HUMIDITY_CRITICAL=85)


def reading(temp=22.0, hum=50.0, online=True, broker=True, room="Bedroom", age=2.0):
    return {"room": room, "temperature": temp, "humidity": hum, "sensor_online": online,
            "broker_connected": broker, "seconds_since_update": age}


class FakeSensor:
    def __init__(self, latest):
        self.latest = latest

    def history(self, limit=None):
        return []


class FakeSettings:
    def __init__(self, thresholds):
        self.thresholds = thresholds


class FakeTelegram:
    enabled = True
    chat_id = "1"

    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)

    def send_photo(self, png, caption=""):
        self.sent.append(("photo", png))


class FakeOutlet:
    enabled = True

    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def set_on(self, on):
        if self.fail:
            raise RuntimeError("Could not reach the IKEA hub: timed out")
        self.calls.append(on)
