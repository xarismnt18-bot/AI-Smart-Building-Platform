"""
Notification preferences changed from the dashboard (Settings page): Alexa
on/off, Alexa quiet hours, alert-lamp automation and lamp quiet hours, and
room enter/leave messages with their quiet hours. Saved
to data/preferences.json and applied again at start-up, so they survive a
restart. Defaults come from config.py / .env.
"""
import json
import logging
import os
import re
import threading

logger = logging.getLogger(__name__)

QUIET_HOURS = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")


def valid_quiet_hours(value: str) -> str:
    """'HH:MM-HH:MM' (may wrap past midnight) or '' for never. Raises ValueError."""
    value = (value or "").replace(" ", "")
    if value and not QUIET_HOURS.match(value):
        raise ValueError("Quiet hours must look like 23:00-08:00 (or be empty for never).")
    return value


class Preferences:
    FIELDS = {"voice_on": bool, "voice_quiet_hours": str, "lamp_auto": bool, "lamp_quiet_hours": str,
              "presence_on": bool, "presence_quiet_hours": str}

    def __init__(self, path: str, voice, lamp, presence=None):
        self._path = path
        self._voice = voice
        self._lamp = lamp
        self._presence = presence
        self._lock = threading.Lock()
        self._apply(self._load())

    def as_dict(self) -> dict:
        out = {
            "voice_on": self._voice.on,
            "voice_quiet_hours": self._voice.quiet_hours,
            "lamp_auto": self._lamp.auto,
            "lamp_quiet_hours": self._lamp.quiet_hours,
        }
        if self._presence is not None:
            out["presence_on"] = self._presence.on
            out["presence_quiet_hours"] = self._presence.quiet_hours
        return out

    def update(self, changes: dict) -> dict:
        """Partial update; validates everything before applying anything. Raises ValueError."""
        unknown = set(changes) - set(self.FIELDS)
        if unknown:
            raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
        clean = {}
        for key, value in changes.items():
            if self.FIELDS[key] is bool:
                if not isinstance(value, bool):
                    raise ValueError(f"{key} must be true or false.")
                clean[key] = value
            else:
                clean[key] = valid_quiet_hours(str(value))
        with self._lock:
            self._apply(clean)
            self._save()
            return self.as_dict()

    def _apply(self, values: dict) -> None:
        if "voice_on" in values:
            self._voice.on = values["voice_on"]
        if "voice_quiet_hours" in values:
            self._voice.quiet_hours = values["voice_quiet_hours"]
        if "lamp_auto" in values:
            self._lamp.auto = values["lamp_auto"]
        if "lamp_quiet_hours" in values:
            self._lamp.quiet_hours = values["lamp_quiet_hours"]
        if self._presence is not None:
            if "presence_on" in values:
                self._presence.on = values["presence_on"]
            if "presence_quiet_hours" in values:
                self._presence.quiet_hours = values["presence_quiet_hours"]

    def _load(self) -> dict:
        try:
            with open(self._path, encoding="utf-8") as f:
                saved = json.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as e:
            logger.error("Ignoring invalid %s (%s); using defaults", self._path, e)
            return {}
        out = {}
        for key, kind in self.FIELDS.items():
            if key not in saved:
                continue
            value = saved[key]
            try:
                if kind is bool:
                    if not isinstance(value, bool):
                        raise ValueError
                    out[key] = value
                else:
                    out[key] = valid_quiet_hours(str(value))
            except ValueError:
                logger.error("Ignoring invalid %s in %s", key, self._path)
        return out

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.as_dict(), f, indent=2)
        os.replace(tmp, self._path)
