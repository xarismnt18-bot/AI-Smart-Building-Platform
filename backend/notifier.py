"""
Telegram notifications for alerts.

A background thread checks the alerts every NOTIFY_CHECK_SEC seconds and sends
a message when an alert starts, and another one when it clears. To avoid spam:
  * a change must hold for two checks in a row before it is reported;
  * the same alert is not re-sent within NOTIFY_COOLDOWN_MIN minutes;
  * "sensor / broker offline" is ignored for the first minute after start-up.

Disabled (and silent) until TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set,
which setup_telegram.bat does.
"""
import json
import logging
import threading
import time
import urllib.error
import urllib.request

from backend.alerts import active_alerts
from backend.voice import spoken

logger = logging.getLogger(__name__)

STARTUP_GRACE_SEC = 60
CONNECTIVITY_KEYS = {"broker_offline", "sensor_offline"}


class TelegramClient:
    def __init__(self, token: str | None, chat_id: str | None):
        self._token = token
        self._chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self._token and self._chat_id)

    @property
    def chat_id(self) -> str | None:
        return self._chat_id

    def send(self, text: str) -> None:
        """Raises RuntimeError with a readable reason if Telegram refuses."""
        self._call("sendMessage", {"chat_id": self._chat_id, "text": text}, timeout=10)

    def get_updates(self, offset: int | None, timeout: int = 25) -> list[dict]:
        """Long-polls for new messages to the bot."""
        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return self._call("getUpdates", params, timeout=timeout + 10).get("result", [])

    def _call(self, method: str, params: dict, timeout: int) -> dict:
        if not self.enabled:
            raise RuntimeError("Telegram is not set up. Run setup_telegram.bat.")
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        body = json.dumps(params).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.load(response)
        except urllib.error.HTTPError as e:
            try:
                detail = json.load(e).get("description", str(e))
            except (ValueError, AttributeError):
                detail = str(e)
            raise RuntimeError(f"Telegram refused the message: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(f"Could not reach Telegram: {e}") from None
        if not result.get("ok"):
            raise RuntimeError(f"Telegram refused the message: {result.get('description')}")
        return result


def describe(key: str, latest: dict, thresholds, resolved: bool) -> str:
    room = latest.get("room") or "Room"
    temp, hum = latest.get("temperature"), latest.get("humidity")
    t, h = (f"{temp:.1f}°C" if temp is not None else "--"), (f"{hum:.0f}%" if hum is not None else "--")

    if resolved:
        return {
            "broker_offline": "✅ MQTT broker is reachable again.",
            "sensor_offline": f"✅ {room} sensor is reporting again ({t}, {h}).",
            "temp_high": f"✅ {room}: temperature back to normal ({t}).",
            "temp_low": f"✅ {room}: temperature back to normal ({t}).",
            "humidity_high": f"✅ {room}: humidity back to normal ({h}).",
            "humidity_low": f"✅ {room}: humidity back to normal ({h}).",
        }.get(key, f"✅ {room}: alert cleared.")

    age = latest.get("seconds_since_update")
    return {
        "broker_offline": "🛑 MQTT broker is unreachable. Check that the Mosquitto service is running.",
        "sensor_offline": f"📡 {room} sensor stopped sending"
                          + (f" (last packet {age:.0f} s ago)." if age is not None else "."),
        "temp_high": f"🌡️ {room} is warm: {t} (comfort limit {thresholds.TEMP_HIGH:g}°C).",
        "temp_low": f"🥶 {room} is cold: {t} (comfort limit {thresholds.TEMP_LOW:g}°C).",
        "humidity_high": f"💧 {room} humidity is high: {h} (limit {thresholds.HUMIDITY_HIGH:g}%). "
                         "Mold risk rises; open a window or run the dehumidifier.",
        "humidity_low": f"🏜️ {room} air is dry: {h} (limit {thresholds.HUMIDITY_LOW:g}%).",
    }.get(key, f"⚠️ {room}: {key}")


class AlertNotifier:
    def __init__(self, telegram: TelegramClient, sensor, settings, check_sec: int, cooldown_min: int, voice=None, lamp=None):
        self.telegram = telegram
        self.voice = voice
        self.lamp = lamp
        self._sensor = sensor
        self._settings = settings
        self._check_sec = check_sec
        self._cooldown_sec = cooldown_min * 60
        self._started_at = time.monotonic()
        self._reported: set[str] = set()      # alerts currently considered active
        self._notified: set[str] = set()      # active alerts whose message was sent
        self._pending: dict[str, int] = {}    # key -> consecutive checks the change held
        self._last_sent: dict[str, float] = {}
        self._muted_until = 0.0  # wall-clock time; alerts are not sent before it
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        voice_on = bool(self.voice and self.voice.enabled)
        lamp_on = bool(self.lamp and self.lamp.enabled)
        logger.info("Voice alerts %s", "on" if voice_on else "off (run setup_voice.bat to turn them on)")
        logger.info("Alert lamp %s", "on" if lamp_on else "off (run setup_ikea.bat to turn it on)")
        if not self.telegram.enabled:
            logger.info("Telegram notifications off (run setup_telegram.bat to turn them on)")
        if not (self.telegram.enabled or voice_on or lamp_on):
            return
        self._started_at = time.monotonic()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="alert-notifier", daemon=True)
        self._thread.start()
        if self.telegram.enabled:
            logger.info("Telegram notifications on")

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(self._check_sec):
            try:
                self.check()
            except Exception:  # never let one bad check kill the thread
                logger.exception("Notification check failed")

    def check(self) -> None:
        if not self.muted_until and self._reported - self._notified:
            # alerts that started while muted: forget them so they are reported now
            self._reported &= self._notified
        latest = self._sensor.latest
        thresholds = self._settings.thresholds
        current = {a.key for a in active_alerts(latest, thresholds)}
        if not latest.get("sensor_online"):
            # values are stale while the sensor is offline: keep value alerts as
            # they were and only track connectivity
            current = (current & CONNECTIVITY_KEYS) | (self._reported - CONNECTIVITY_KEYS)
        if time.monotonic() - self._started_at < STARTUP_GRACE_SEC:
            current -= CONNECTIVITY_KEYS

        changed = (current - self._reported) | (self._reported - current)
        for key in list(self._pending):
            if key not in changed:
                del self._pending[key]
        for key in changed:
            self._pending[key] = self._pending.get(key, 0) + 1
            if self._pending[key] < 2:
                continue  # wait one more check before believing it
            del self._pending[key]
            if key in current:
                self._raise(key, latest, thresholds)
            else:
                self._clear(key, latest, thresholds)
        if self.lamp:
            self.lamp.sync(self._reported)

    def _raise(self, key: str, latest: dict, thresholds) -> None:
        self._reported.add(key)
        now = time.monotonic()
        if now - self._last_sent.get(key, -self._cooldown_sec) < self._cooldown_sec:
            return
        if self._send(describe(key, latest, thresholds, resolved=False)):
            self._last_sent[key] = now
            self._notified.add(key)
            self._speak(spoken(key, latest, thresholds))

    def _clear(self, key: str, latest: dict, thresholds) -> None:
        self._reported.discard(key)
        if key in self._notified:  # only confirm alerts the user actually received
            self._notified.discard(key)
            self._send(describe(key, latest, thresholds, resolved=True))

    # ---------- mute (from the Telegram /mute command) ----------
    def mute(self, seconds: float) -> float:
        self._muted_until = time.time() + seconds
        return self._muted_until

    def unmute(self) -> None:
        self._muted_until = 0.0

    @property
    def muted_until(self) -> float | None:
        return self._muted_until if self._muted_until > time.time() else None

    def _send(self, text: str) -> bool:
        """True when the alert counts as delivered (Telegram, or voice-only setups)."""
        if self.muted_until:
            return False  # treated like "not sent": no "resolved" follow-up either
        if not self.telegram.enabled:
            return bool(self.voice and self.voice.enabled)
        try:
            self.telegram.send(text)
            return True
        except RuntimeError as e:
            logger.warning("Telegram: %s", e)
            return False

    @property
    def active_keys(self) -> set[str]:
        return set(self._reported)

    def _speak(self, text: str) -> None:
        if not (self.voice and self.voice.should_speak()):
            return
        try:
            self.voice.announce(text)
        except RuntimeError as e:
            logger.warning("Voice: %s", e)
