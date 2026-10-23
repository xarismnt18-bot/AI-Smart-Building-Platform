import json

import pytest

from backend.preferences import Preferences, valid_quiet_hours


class Voice:
    on, quiet_hours = True, "23:00-08:00"


class Lamp:
    auto, quiet_hours = True, "23:00-08:00"


def test_quiet_hours_format():
    assert valid_quiet_hours(" 22:30-07:00 ") == "22:30-07:00"
    assert valid_quiet_hours("") == ""
    for bad in ("25:00-08:00", "23-08", "23:00", "x"):
        with pytest.raises(ValueError):
            valid_quiet_hours(bad)


def test_update_applies_saves_and_reloads(tmp_path):
    path = tmp_path / "prefs.json"
    voice, lamp = Voice(), Lamp()
    prefs = Preferences(str(path), voice, lamp)
    out = prefs.update({"voice_on": False, "voice_quiet_hours": "22:00-09:00", "lamp_auto": False})
    assert voice.on is False and voice.quiet_hours == "22:00-09:00" and lamp.auto is False
    assert out["lamp_quiet_hours"] == "23:00-08:00"
    assert json.loads(path.read_text())["voice_on"] is False

    voice2, lamp2 = Voice(), Lamp()
    Preferences(str(path), voice2, lamp2)  # a restart
    assert voice2.on is False and voice2.quiet_hours == "22:00-09:00" and lamp2.auto is False


def test_invalid_update_changes_nothing(tmp_path):
    voice, lamp = Voice(), Lamp()
    prefs = Preferences(str(tmp_path / "p.json"), voice, lamp)
    for bad in ({"voice_on": "yes"}, {"voice_quiet_hours": "late"}, {"volume": 3},
                {"voice_on": False, "lamp_quiet_hours": "nope"}):
        with pytest.raises(ValueError):
            prefs.update(bad)
    assert voice.on is True and lamp.quiet_hours == "23:00-08:00"
    assert not (tmp_path / "p.json").exists()


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "p.json"
    path.write_text('{"voice_on": "maybe", "voice_quiet_hours": "21:00-07:00", "lamp_auto": false')
    voice = Voice()
    Preferences(str(path), voice, Lamp())
    assert voice.on is True and voice.quiet_hours == "23:00-08:00"
    path.write_text('{"voice_on": "maybe", "voice_quiet_hours": "21:00-07:00"}')
    Preferences(str(path), voice, Lamp())
    assert voice.on is True and voice.quiet_hours == "21:00-07:00"
