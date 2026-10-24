"""
Everything Thalpos does with the mmWave radar's presence flag:

- a Telegram message when someone comes into the room or it becomes empty;
- the visits log (when someone was in), for "time in the room" per day;
- a reminder to air the room after a long stay while the humidity climbs;
- whether the room is empty, so comfort alerts can wait until someone is in.

The radar can flicker, so a change must hold before it counts:
ENTER_HOLD_SEC for "someone came in", LEAVE_HOLD_SEC for "room is empty"
(someone sitting very still can briefly look like an empty room).
Messages respect the Telegram /mute pause and the enter/leave quiet hours.
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

AIR_AFTER_SEC = 2 * 3600      # remind only after someone has been in this long
AIR_RISE_PCT = 3              # humidity rise over the last hour that counts as "climbing"
AIR_NEAR_LIMIT_PCT = 5        # ...or humidity within this much of the comfort limit
AIR_CHECK_SEC = 60


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


def airing_message(room: str, stayed_sec: float, hum_before: float | None, hum_now: float) -> str:
    rise = f" and the humidity went from {hum_before:.0f}% to {hum_now:.0f}% in the last hour" \
        if hum_before is not None and hum_now - hum_before >= 1 else f" and the humidity is {hum_now:.0f}%"
    return (f"🪟 Someone has been in the {room} for {duration_text(stayed_sec)}{rise}. "
            "Open the window for 5–10 minutes to let fresh air in.")


class PresenceWatcher:
    def __init__(self, telegram, sensor, notifier, on: bool = True, quiet_hours: str = "",
                 history=None, settings=None):
        self.telegram = telegram
        self._sensor = sensor
        self._notifier = notifier      # for the shared /mute pause
        self._history = history        # HistoryStore: visits log and humidity an hour ago
        self._settings = settings      # comfort limits for the airing reminder
        self.on = on                   # enter/leave messages
        self.quiet_hours = quiet_hours
        self.alerts_only_present = True   # comfort alerts wait while the room is empty
        self.airing_on = True             # airing reminder
        self._state: bool | None = None       # last confirmed presence
        self._since: float | None = None      # when the confirmed state started (monotonic), if known
        self._stay_from: float | None = None  # start of the current stay, at worst since start-up
        self._candidate: bool | None = None
        self._candidate_at = 0.0
        self._last_raw: bool | None = None    # for the log only
        self._aired_this_stay = False
        self._air_checked_at = -1e9
        self._stop = threading.Event()
        self._thread = None

    # ---------- lifecycle ----------
    def start(self) -> None:
        if self._history is not None:
            self._history.close_open_visits()
        if self.telegram.enabled:
            logger.info("Room enter/leave messages %s", "on" if self.on else "off (turned off in Settings)")
        else:
            logger.info("Room enter/leave messages off (Telegram is not set up); visits are still logged")
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="presence-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._history is not None and self._state:
            self._log("visit_ended")

    def _run(self) -> None:
        while not self._stop.wait(CHECK_SEC):
            try:
                self.check()
            except Exception:
                logger.exception("Presence check failed")

    # ---------- state ----------
    @property
    def empty(self) -> bool:
        """True only when the radar has confirmed that nobody is in."""
        return self._state is False

    @property
    def occupied(self) -> bool:
        return self._state is True

    @property
    def since(self) -> float | None:
        """Wall-clock time (epoch s) someone came in, while the room is occupied and it is known."""
        if self._state is not True or self._since is None:
            return None
        return time.time() - (time.monotonic() - self._since)

    def check(self, now: float | None = None, wall: datetime | None = None) -> str | None:
        """Returns the enter/leave message sent (or that would have been sent), for tests."""
        now = time.monotonic() if now is None else now
        wall = wall or datetime.now()
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
            self._stay_from = now if present else None
            if present:
                self._log("visit_started", wall.timestamp())
            return None
        if present == self._state:
            self._candidate = None
            self._check_airing(now, wall, latest)
            return None
        if self._candidate != present:
            self._candidate, self._candidate_at = present, now
        hold = ENTER_HOLD_SEC if present else LEAVE_HOLD_SEC
        if now - self._candidate_at < hold:
            return None

        changed_at = self._candidate_at
        changed_wall = wall.timestamp() - (now - changed_at)
        stayed = changed_at - self._since if (not present and self._since is not None) else None
        self._state, self._since, self._candidate = present, changed_at, None
        self._stay_from = changed_at if present else None
        self._aired_this_stay = False
        self._log("visit_started" if present else "visit_ended", changed_wall)

        text = message(present, latest.get("room") or "room", wall, stayed)
        self._send(text, wall, self.on)
        return text

    # ---------- airing reminder ----------
    def _check_airing(self, now: float, wall: datetime, latest: dict) -> str | None:
        if not (self.airing_on and self._state and self._stay_from is not None) or self._aired_this_stay:
            return None
        if now - self._stay_from < AIR_AFTER_SEC or now - self._air_checked_at < AIR_CHECK_SEC:
            return None
        self._air_checked_at = now
        hum = latest.get("humidity")
        if hum is None:
            return None
        before = self._humidity_an_hour_ago(wall.timestamp())
        limit = self._settings.thresholds.HUMIDITY_HIGH if self._settings is not None else 70
        climbing = before is not None and hum - before >= AIR_RISE_PCT
        if not (climbing or hum >= limit - AIR_NEAR_LIMIT_PCT):
            return None
        self._aired_this_stay = True
        text = airing_message(latest.get("room") or "room", now - self._stay_from, before, hum)
        self._send(text, wall, self.airing_on)
        return text

    def _humidity_an_hour_ago(self, now_ts: float) -> float | None:
        if self._history is None:
            return None
        try:
            rows = self._history.rows(now_ts - 3900, now_ts - 3300)   # around 60 minutes ago
        except Exception:
            logger.exception("Presence: could not read the humidity history")
            return None
        values = [r[3] for r in rows if r[3] is not None]
        return sum(values) / len(values) if values else None

    # ---------- helpers ----------
    def _send(self, text: str, wall: datetime, enabled: bool) -> None:
        if not self.should_notify(wall, enabled):
            logger.info("Not sent (off, paused or quiet hours): %s", text)
            return
        try:
            self.telegram.send(text)
            logger.info("Sent: %s", text)
        except RuntimeError as e:
            logger.warning("Telegram: %s", e)

    def _log(self, method: str, ts: float | None = None) -> None:
        log = getattr(self._history, method, None)
        if log is None:
            return
        try:
            log(ts)
        except Exception:
            logger.exception("Visits log: %s failed", method)

    def should_notify(self, wall: datetime, enabled: bool | None = None) -> bool:
        enabled = self.on if enabled is None else enabled
        return bool(enabled and self.telegram.enabled and not self._notifier.muted_until
                    and not in_quiet_hours(wall, self.quiet_hours))
