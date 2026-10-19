"""
Two-way Telegram: commands from your phone, plus the morning summary.

Commands (only the chat saved by setup_telegram.bat gets answers):
    /status          current readings, trend and active alerts
    /today           today's min / max / average and time out of range
    /mute [30m|2h]   pause alert messages (default 1 hour)
    /unmute          resume alert messages
    /voice on|off|test|status   Alexa: spoken alerts, test, read the status aloud
    /help            this list
"""
import logging
import re
import threading
import time
from datetime import datetime

from ai.engines import dew_point, health_score, mold_risk
from backend.alerts import active_alerts
from backend.daily_stats import DailyStats, format_day, yesterday
from backend.voice import status_sentence

logger = logging.getLogger(__name__)

SAMPLE_SEC = 10
HELP = (
    "AIOS commands:\n"
    "/status – current readings and alerts\n"
    "/today – today's range and time out of comfort\n"
    "/mute 2h – pause alerts (30m, 2h, 1d; default 1h)\n"
    "/unmute – resume alerts\n"
    "/voice on | off | test – spoken alerts on Alexa\n"
    "/voice status – Alexa reads the room status aloud"
)


def parse_duration(text: str, default_sec: int = 3600) -> int | None:
    """'30m' -> 1800, '2h' -> 7200, '1d' -> 86400, '' -> default. None if invalid."""
    text = text.strip().lower()
    if not text:
        return default_sec
    match = re.fullmatch(r"(\d+)\s*(m|min|h|d)?", text)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2) or "m"
    seconds = value * {"m": 60, "min": 60, "h": 3600, "d": 86400}[unit]
    return seconds if 0 < seconds <= 7 * 86400 else None


class TelegramBot:
    def __init__(self, telegram, notifier, sensor, settings, predictor, stats: DailyStats, summary_time: str):
        self.telegram = telegram
        self._notifier = notifier
        self._sensor = sensor
        self._settings = settings
        self._predictor = predictor
        self._stats = stats
        self._summary_hhmm = summary_time
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        # Daily stats are useful for /today even before Telegram is set up.
        self._spawn(self._record_loop, "daily-stats")
        if self.telegram.enabled:
            self._spawn(self._command_loop, "telegram-commands")
            self._spawn(self._summary_loop, "daily-summary")

    def stop(self) -> None:
        self._stop.set()
        self._stats.save()

    def _spawn(self, target, name: str) -> None:
        thread = threading.Thread(target=target, name=name, daemon=True)
        thread.start()
        self._threads.append(thread)

    # ---------- daily stats + morning summary ----------
    def _record_loop(self) -> None:
        while not self._stop.wait(SAMPLE_SEC):
            try:
                self._stats.sample(self._sensor.latest, self._settings.thresholds)
            except Exception:
                logger.exception("Daily stats sample failed")

    def _summary_loop(self) -> None:
        while not self._stop.wait(30):
            try:
                self.maybe_send_summary(datetime.now())
            except Exception:
                logger.exception("Daily summary failed")

    def maybe_send_summary(self, now: datetime) -> bool:
        if now.strftime("%H:%M") < self._summary_hhmm:
            return False
        day = yesterday(now.date())
        if self._stats.summary_sent_for() == day.isoformat():
            return False
        data = self._stats.day(day)
        room = self._sensor.latest.get("room") or "Room"
        if data:  # nothing to report for a day with no readings
            text = format_day(f"☀️ Good morning. {room} yesterday ({day:%a %d %b}):", data, self._settings.thresholds)
            try:
                self.telegram.send(text)
            except RuntimeError as e:
                logger.warning("Daily summary not sent: %s", e)
                return False
        self._stats.mark_summary_sent(day)
        return bool(data)

    # ---------- commands ----------
    def _command_loop(self) -> None:
        offset = self._skip_backlog()
        while not self._stop.is_set():
            try:
                updates = self.telegram.get_updates(offset)
            except RuntimeError as e:
                logger.warning("Telegram polling: %s", e)
                self._stop.wait(15)
                continue
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message") or {}
                if str(message.get("chat", {}).get("id")) != str(self.telegram.chat_id):
                    continue  # someone else found the bot: ignore
                reply = self.handle(message.get("text", ""))
                if reply:
                    try:
                        self.telegram.send(reply)
                    except RuntimeError as e:
                        logger.warning("Telegram reply not sent: %s", e)

    def _skip_backlog(self) -> int | None:
        """Commands sent while AIOS was off are stale; start after the newest one."""
        try:
            pending = self.telegram.get_updates(-1, timeout=0)
        except RuntimeError:
            return None
        return pending[-1]["update_id"] + 1 if pending else None

    def handle(self, text: str) -> str | None:
        command, _, arg = text.strip().partition(" ")
        command = command.split("@")[0].lower()
        if command in ("/start", "/help"):
            return HELP
        if command == "/status":
            return self.status_text()
        if command == "/today":
            return format_day("📊 Today so far:", self._stats.day(datetime.now().date()), self._settings.thresholds)
        if command == "/mute":
            seconds = parse_duration(arg)
            if seconds is None:
                return "Use it like /mute 30m, /mute 2h or /mute 1d."
            until = self._notifier.mute(seconds)
            return f"🔕 Alerts paused until {datetime.fromtimestamp(until):%H:%M %a}. /unmute to resume."
        if command == "/unmute":
            self._notifier.unmute()
            return "🔔 Alerts are back on."
        if command == "/voice":
            return self.voice_command(arg.strip().lower())
        if command.startswith("/"):
            return "I don't know that one.\n\n" + HELP
        return None

    def voice_command(self, arg: str) -> str:
        voice = self._notifier.voice
        if not voice or not voice.enabled:
            return "🔇 Voice alerts aren't set up. Run setup_voice.bat on the PC."
        if arg == "off":
            voice.on = False
            return "🔇 Alexa will stay quiet. /voice on to bring it back."
        if arg == "on":
            voice.on = True
            return f"🔊 Alexa will announce new alerts (quiet hours {voice.quiet_hours})."
        if arg == "test":
            try:
                voice.announce("This is a test from your smart home. Voice alerts are working.")
            except RuntimeError as e:
                return f"Alexa test failed: {e}"
            return "🔊 Sent. Your Echo should speak now."
        if arg == "status":
            try:
                voice.announce(status_sentence(self._sensor.latest, self._settings.thresholds))
            except RuntimeError as e:
                return f"Alexa status failed: {e}"
            return "🔊 Your Echo is reading the room status."
        state = "on" if voice.on else "off"
        return f"Voice alerts are {state} (quiet hours {voice.quiet_hours}). Use /voice on, /voice off, /voice test or /voice status."

    def status_text(self) -> str:
        latest = self._sensor.latest
        t = self._settings.thresholds
        room = latest.get("room") or "Room"
        temp, hum = latest.get("temperature"), latest.get("humidity")

        if not latest.get("broker_connected"):
            return f"🛑 {room}: MQTT broker unreachable, no live data."
        if not latest.get("sensor_online") or temp is None:
            age = latest.get("seconds_since_update")
            when = f"{age / 60:.0f} min ago" if age else "never"
            return f"📡 {room}: sensor offline (last packet {when})."

        lines = [
            f"🏠 {room}: {temp:.1f}°C, {hum:.0f}%",
            f"Health {health_score(temp, hum, t)}/100 · dew point {dew_point(temp, hum):.1f}° · mold risk {mold_risk(temp, hum)}",
        ]
        forecast = self._predictor.predict_all(self._sensor.history(), t)
        trend = forecast["temperature"].get("trend")
        predicted = forecast["temperature"].get("predicted")
        if trend and trend != "unknown" and predicted is not None:
            lines.append(f"Next {forecast['minutes_ahead']} min: {trend}, ~{predicted:.1f}°C")
        alerts = [a.message for a in active_alerts(latest, t)]
        lines.append("⚠️ " + "\n⚠️ ".join(alerts) if alerts else "✅ No alerts.")
        muted = self._notifier.muted_until
        if muted:
            lines.append(f"🔕 Alerts paused until {datetime.fromtimestamp(muted):%H:%M}.")
        return "\n".join(lines)
