"""
Spoken alerts on an Amazon Echo, through the Voice Monkey announcement API.

Only new alerts are spoken (not "back to normal"), never during quiet hours,
and never while alerts are muted. Off until setup_voice.bat has stored a
Voice Monkey token and speaker device in voice.env.
"""
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

API = "https://api-v3.voicemonkey.io"


def in_quiet_hours(now: datetime, quiet: str) -> bool:
    """quiet = 'HH:MM-HH:MM' (may wrap past midnight); empty = never quiet."""
    if not quiet or "-" not in quiet:
        return False
    start, end = (part.strip() for part in quiet.split("-", 1))
    hhmm = now.strftime("%H:%M")
    if start <= end:
        return start <= hhmm < end
    return hhmm >= start or hhmm < end


def spoken(key: str, latest: dict, thresholds) -> str:
    """Plain sentences for text-to-speech: no emoji, numbers rounded."""
    room = latest.get("room") or "the room"
    temp, hum = latest.get("temperature"), latest.get("humidity")
    t = f"{temp:.0f} degrees" if temp is not None else "unknown"
    h = f"{hum:.0f} percent" if hum is not None else "unknown"
    return {
        "broker_offline": "Smart home alert. The sensor broker is offline.",
        "sensor_offline": f"Smart home alert. The {room} sensor stopped sending data.",
        "temp_high": f"{room} is warm, {t}. Consider opening a window or switching on the air conditioning.",
        "temp_low": f"{room} is cold, {t}.",
        "humidity_high": f"{room} humidity is {h}, above {thresholds.HUMIDITY_HIGH:g}. "
                         "Consider running the dehumidifier.",
        "humidity_low": f"The air in the {room} is dry, {h} humidity.",
    }.get(key, f"Smart home alert for the {room}.")


class VoiceAnnouncer:
    def __init__(self, token: str | None, device: str | None, quiet_hours: str):
        self._token = token
        self._device = device
        self.quiet_hours = quiet_hours
        self.on = True  # switched by the Telegram /voice command

    @property
    def enabled(self) -> bool:
        return bool(self._token and self._device)

    def should_speak(self, now: datetime | None = None) -> bool:
        return self.enabled and self.on and not in_quiet_hours(now or datetime.now(), self.quiet_hours)

    def announce(self, text: str) -> None:
        """Raises RuntimeError with a readable reason if Voice Monkey refuses."""
        if not self.enabled:
            raise RuntimeError("Voice alerts are not set up. Run setup_voice.bat.")
        body = json.dumps({"token": self._token, "device": self._device, "speech": text}).encode("utf-8")
        request = urllib.request.Request(f"{API}/announce", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.load(response)
        except urllib.error.HTTPError as e:
            try:
                detail = json.load(e).get("error") or str(e)
            except (ValueError, AttributeError):
                detail = str(e)
            raise RuntimeError(f"Voice Monkey refused the announcement: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(f"Could not reach Voice Monkey: {e}") from None
        if not result.get("success"):
            raise RuntimeError(f"Voice Monkey refused the announcement: {result}")
