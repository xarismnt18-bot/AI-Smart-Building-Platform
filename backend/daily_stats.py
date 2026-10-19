"""
Per-day statistics for the Telegram /today command and the morning summary.

The backend keeps only a short in-memory history, so instead of storing every
reading this samples the live value every few seconds and keeps running totals
per calendar day (min / max / mean, time spent above or below each limit).
The last DAYS_KEPT days are saved to a small JSON file, so a restart doesn't
lose the day.
"""
import json
import os
import threading
import time
from datetime import date, datetime, timedelta

DAYS_KEPT = 7
SAVE_EVERY_SEC = 300
MAX_GAP_SEC = 60  # a longer pause between samples counts as offline time


def _empty_day() -> dict:
    return {
        "samples": 0, "online_sec": 0.0,
        "t_sum": 0.0, "t_min": None, "t_max": None,
        "h_sum": 0.0, "h_min": None, "h_max": None,
        "sec_temp_high": 0.0, "sec_temp_low": 0.0,
        "sec_hum_high": 0.0, "sec_hum_low": 0.0,
    }


class DailyStats:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._days: dict[str, dict] = {}
        self._meta: dict = {}
        self._last_sample: float | None = None
        self._last_save = time.monotonic()
        self._load()

    # ---------- persistence ----------
    def _load(self) -> None:
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            self._days = data.get("days", {})
            self._meta = data.get("meta", {})
        except (OSError, ValueError):
            self._days, self._meta = {}, {}

    def save(self) -> None:
        with self._lock:
            keep = sorted(self._days)[-DAYS_KEPT:]
            self._days = {d: self._days[d] for d in keep}
            data = {"days": self._days, "meta": self._meta}
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp, self._path)
        self._last_save = time.monotonic()

    # ---------- recording ----------
    def sample(self, latest: dict, thresholds, now: datetime | None = None) -> None:
        """Adds the current reading, weighted by the time since the previous sample."""
        mono = time.monotonic()
        gap = None if self._last_sample is None else mono - self._last_sample
        self._last_sample = mono

        temp, hum = latest.get("temperature"), latest.get("humidity")
        if not latest.get("sensor_online") or temp is None or hum is None:
            return
        weight = 0.0 if gap is None or gap > MAX_GAP_SEC else gap

        key = (now or datetime.now()).date().isoformat()
        with self._lock:
            d = self._days.setdefault(key, _empty_day())
            d["samples"] += 1
            d["t_sum"] += temp
            d["h_sum"] += hum
            d["t_min"] = temp if d["t_min"] is None else min(d["t_min"], temp)
            d["t_max"] = temp if d["t_max"] is None else max(d["t_max"], temp)
            d["h_min"] = hum if d["h_min"] is None else min(d["h_min"], hum)
            d["h_max"] = hum if d["h_max"] is None else max(d["h_max"], hum)
            d["online_sec"] += weight
            if temp > thresholds.TEMP_HIGH:
                d["sec_temp_high"] += weight
            if temp < thresholds.TEMP_LOW:
                d["sec_temp_low"] += weight
            if hum > thresholds.HUMIDITY_HIGH:
                d["sec_hum_high"] += weight
            if hum < thresholds.HUMIDITY_LOW:
                d["sec_hum_low"] += weight

        if time.monotonic() - self._last_save > SAVE_EVERY_SEC:
            self.save()

    def day(self, day: date) -> dict | None:
        with self._lock:
            d = self._days.get(day.isoformat())
            return dict(d) if d and d["samples"] else None

    # ---------- "sent once per day" bookkeeping for the morning summary ----------
    def summary_sent_for(self) -> str | None:
        return self._meta.get("summary_sent_for")

    def mark_summary_sent(self, day: date) -> None:
        with self._lock:
            self._meta["summary_sent_for"] = day.isoformat()
        self.save()


def _hours(sec: float) -> str:
    if sec < 60:
        return "0 min"
    if sec < 3600:
        return f"{sec / 60:.0f} min"
    return f"{sec / 3600:.1f} h"


def format_day(title: str, d: dict | None, thresholds) -> str:
    if not d:
        return f"{title}\nNo readings yet."
    t_avg, h_avg = d["t_sum"] / d["samples"], d["h_sum"] / d["samples"]
    lines = [
        title,
        f"🌡️ {d['t_min']:.1f}–{d['t_max']:.1f}°C (avg {t_avg:.1f})",
        f"💧 {d['h_min']:.0f}–{d['h_max']:.0f}% (avg {h_avg:.0f})",
    ]
    out_of_range = [
        (d["sec_hum_high"], f"humidity above {thresholds.HUMIDITY_HIGH:g}%"),
        (d["sec_hum_low"], f"humidity below {thresholds.HUMIDITY_LOW:g}%"),
        (d["sec_temp_high"], f"temperature above {thresholds.TEMP_HIGH:g}°C"),
        (d["sec_temp_low"], f"temperature below {thresholds.TEMP_LOW:g}°C"),
    ]
    flagged = [f"• {_hours(sec)} {label}" for sec, label in out_of_range if sec >= 60]
    lines += flagged or ["✅ Stayed inside the comfort range."]
    lines.append(f"📡 Sensor online {_hours(d['online_sec'])}")
    return "\n".join(lines)


def yesterday(today: date | None = None) -> date:
    return (today or date.today()) - timedelta(days=1)
