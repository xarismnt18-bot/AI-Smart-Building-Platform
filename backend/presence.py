"""
Telegram message when someone comes into the room or the room becomes empty,
from the mmWave radar's presence flag in each sensor reading.

The radar can flicker, so a change must hold before it is reported:
ENTER_HOLD_SEC for "someone came in", LEAVE_HOLD_SEC for "room is empty"
(someone sitting very still can briefly look like an empty room).
Respects the Telegram /mute pause and its own quiet hours.
"""
import logging
import threading
import time
from datetime import datetime

from backend.voice import in_quiet_hours

logger = logging.getLogger(__name__)

ENTER_HOLD_SEC = 5
LEAVE_HOLD_SEC = 60
CHECK_SEC = 2


def duration_text(seconds: float) -> str:
    minutes = int(seconds // 60)
    if minutes < 1:
        return "less than a minute"
    if minutes < 60:
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min" if minutes else f"{hours} h"


def message(present: bool, room: str, at: datetime, stayed_sec: float | None) -> str:
    clock = at.strftime("%H:%M")
    if present:
        return f"🚶 Someone came into the {room} ({clock})."
    text = f"🚪 The {room} is empty now ({clock})."
    if stayed_sec is not None:
        text += f" Someone was there for {duration_text(stayed_sec)}."
    return text


class PresenceWatcher:
    def __init__(self, telegram, sensor, notifier, on: bool = True, quiet_hours: str = ""):
        self.telegram = telegram
        self._sensor = sensor
        self._notifier = notifier      # for the shared /mute pause
        self.on = on
        self.quiet_hours = quiet_hours
        self._state: bool | None = None       # last confirmed presence
        self._since: float | None = None      # when the confirmed state started (monotonic)
        self._candidate: bool | None = None
        self._candidate_at = 0.0
        self._last_raw: bool | None = None  # for the log only
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        if not self.telegram.enabled:
            logger.info("Room enter/leave messages off (Telegram is not set up)")
            return
        logger.info("Room enter/leave messages %s", "on" if self.on else "off (turned off in Settings)")
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="presence-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(CHECK_SEC):
            try:
                self.check()
            except Exception:
                logger.exception("Presence check failed")

    def check(self, now: float | None = None, wall: datetime | None = None) -> str | None:
        """Returns the message sent (or that would have been sent), for tests."""
        now = time.monotonic() if now is None else now
        latest = self._sensor.latest
        present = latest.get("presence")
        if not isinstance(present, bool):   # no radar, or sensor offline: keep what we knew
            self._candidate = None
            return None
        if present != self._last_raw:
            logger.info("Radar: %s", "someone there" if present else "nobody")
            self._last_raw = present
        if self._state is None:             # first reading after start-up: no message,
            self._state, self._since = present, None   # and we don't know since when
            return None
        if present == self._state:
            self._candidate = None
            return None
        if self._candidate != present:
            self._candidate, self._candidate_at = present, now
        hold = ENTER_HOLD_SEC if present else LEAVE_HOLD_SEC
        if now - self._candidate_at < hold:
            return None

        changed_at = self._candidate_at
        stayed = changed_at - self._since if (not present and self._since is not None) else None
        self._state, self._since, self._candidate = present, changed_at, None
        wall = wall or datetime.now()
        text = message(present, latest.get("room") or "room", wall, stayed)
        if self.should_notify(wall):
            try:
                self.telegram.send(text)
                logger.info("Sent: %s", text)
            except RuntimeError as e:
                logger.warning("Telegram: %s", e)
        else:
            logger.info("Not sent (off, paused or quiet hours): %s", text)
        return text

    @property
    def since(self) -> float | None:
        """Wall-clock time (epoch s) someone came in, while the room is occupied and it is known."""
        if self._state is not True or self._since is None:
            return None
        return time.time() - (time.monotonic() - self._since)

    def should_notify(self, wall: datetime) -> bool:
        return bool(self.on and self.telegram.enabled and not self._notifier.muted_until
                    and not in_quiet_hours(wall, self.quiet_hours))
