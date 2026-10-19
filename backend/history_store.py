"""
Long-term reading history in SQLite (data/history.db).

The MQTT client keeps only the last few hundred packets in memory, so a
background thread stores the live reading every SAMPLE_SEC seconds and keeps
KEEP_DAYS days. Readings are only stored while the sensor is online, so a gap
in the data means the sensor (or the PC) was off.
"""
import csv
import io
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

SAMPLE_SEC = 30
KEEP_DAYS = 30


class HistoryStore:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS readings (ts REAL PRIMARY KEY, room TEXT, temperature REAL, humidity REAL)"
            )
        self._stop = threading.Event()

    # ---------- writing ----------
    def record(self, latest: dict, ts: float | None = None) -> bool:
        temp, hum = latest.get("temperature"), latest.get("humidity")
        if not latest.get("sensor_online") or temp is None or hum is None:
            return False
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO readings VALUES (?, ?, ?, ?)",
                             (ts or time.time(), latest.get("room"), temp, hum))
        return True

    def prune(self, now: float | None = None) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM readings WHERE ts < ?", ((now or time.time()) - KEEP_DAYS * 86400,))

    def start(self, sensor) -> None:
        def loop():
            self.prune()
            while not self._stop.wait(SAMPLE_SEC):
                try:
                    self.record(sensor.latest)
                except Exception:
                    logger.exception("History: could not store a reading")
        threading.Thread(target=loop, name="history-store", daemon=True).start()
        logger.info("History: storing a reading every %d s in SQLite (%d days kept)", SAMPLE_SEC, KEEP_DAYS)

    def stop(self) -> None:
        self._stop.set()

    # ---------- reading ----------
    def rows(self, since: float, until: float | None = None) -> list[tuple]:
        with self._lock:
            return self._db.execute(
                "SELECT ts, room, temperature, humidity FROM readings WHERE ts >= ? AND ts <= ? ORDER BY ts",
                (since, until or time.time()),
            ).fetchall()

    def series(self, since: float, step_sec: int, until: float | None = None) -> list[dict]:
        """Averages per step_sec bucket, for charts."""
        with self._lock:
            rows = self._db.execute(
                "SELECT CAST(ts / ? AS INTEGER) * ? AS bucket, AVG(temperature), AVG(humidity), "
                "MIN(temperature), MAX(temperature), MIN(humidity), MAX(humidity), COUNT(*) "
                "FROM readings WHERE ts >= ? AND ts <= ? GROUP BY bucket ORDER BY bucket",
                (step_sec, step_sec, since, until or time.time()),
            ).fetchall()
        return [{
            "ts": b, "time": datetime.fromtimestamp(b).isoformat(timespec="minutes"),
            "temperature": round(t, 2), "humidity": round(h, 1),
            "t_min": tmin, "t_max": tmax, "h_min": hmin, "h_max": hmax, "samples": n,
        } for b, t, h, tmin, tmax, hmin, hmax, n in rows]

    def csv(self, since: float, until: float | None = None) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["time", "room", "temperature_c", "humidity_pct"])
        for ts, room, temp, hum in self.rows(since, until):
            writer.writerow([datetime.fromtimestamp(ts).isoformat(timespec="seconds"), room, temp, hum])
        return out.getvalue()


def format_night(store: HistoryStore, thresholds, now: datetime | None = None, hours: int = 10) -> str:
    """Hour-by-hour summary for Telegram /night (default: the last 10 hours)."""
    now = now or datetime.now()
    since = now.timestamp() - hours * 3600
    buckets = store.series(since, 3600, now.timestamp())
    if not buckets:
        return f"🌙 No readings stored in the last {hours} hours."
    lines = [f"🌙 Last {hours} hours, hourly average (min–max):"]
    for b in buckets:
        flag = " ⚠️" if (b["h_max"] > thresholds.HUMIDITY_HIGH or b["t_max"] > thresholds.TEMP_HIGH
                         or b["t_min"] < thresholds.TEMP_LOW or b["h_min"] < thresholds.HUMIDITY_LOW) else ""
        lines.append(f"{datetime.fromtimestamp(b['ts']):%H:%M}  {b['temperature']:.1f}°C  "
                     f"{b['humidity']:.0f}% ({b['h_min']:.0f}–{b['h_max']:.0f}){flag}")
    temps = [r[2] for r in store.rows(since, now.timestamp())]
    hums = [r[3] for r in store.rows(since, now.timestamp())]
    lines.append(f"Range: {min(temps):.1f}–{max(temps):.1f}°C, {min(hums):.0f}–{max(hums):.0f}%")
    return "\n".join(lines)
