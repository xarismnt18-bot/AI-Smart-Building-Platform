"""
Central configuration for Smart Building AI Platform.
Defaults live here; override any of them via the .env file.

Alert thresholds below are only the *initial* values: once changed from the
dashboard Settings page they are stored in data/settings.json and served by
the backend (/config), so backend and frontend always agree.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    # MQTT username/password, generated on this PC by setup_security.bat.
    # Kept in its own git-ignored file so it never ends up in a commit.
    load_dotenv(os.path.join(BASE_DIR, "mqtt_credentials.env"))
    # Telegram bot token + chat id, written by setup_telegram.bat (git-ignored).
    load_dotenv(os.path.join(BASE_DIR, "telegram.env"))
except ImportError:
    pass


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# =========================
# MQTT
# =========================
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "smartroom/dht11")
MQTT_USERNAME = os.getenv("MQTT_USERNAME") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
MQTT_KEEPALIVE = 60
# The sensor counts as offline when no packet arrived for this many seconds,
# even if the broker connection itself is still up.
SENSOR_STALE_SEC = int(os.getenv("SENSOR_STALE_SEC", "30"))

# Broker discovery: the backend broadcasts "the broker is here" on the LAN every
# few seconds, so the ESP8266 finds this PC even when its IP address changes.
DISCOVERY_ENABLED = _env_bool("DISCOVERY_ENABLED", True)
DISCOVERY_PORT = int(os.getenv("DISCOVERY_PORT", "18831"))
DISCOVERY_INTERVAL_SEC = float(os.getenv("DISCOVERY_INTERVAL_SEC", "3"))


# =========================
# API / BACKEND
# =========================
# Localhost only by default: the dashboard runs on the same PC, and the API
# has no authentication, so it should not be reachable from the network.
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_RELOAD = _env_bool("API_RELOAD", False)
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]


# =========================
# TELEGRAM NOTIFICATIONS (optional; off until setup_telegram.bat has run)
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or None
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or None
# The same alert is not repeated more often than this, even if it flaps.
NOTIFY_COOLDOWN_MIN = int(os.getenv("NOTIFY_COOLDOWN_MIN", "30"))
NOTIFY_CHECK_SEC = int(os.getenv("NOTIFY_CHECK_SEC", "15"))
# Yesterday's summary is sent once a day, at or after this local time (HH:MM).
DAILY_SUMMARY_TIME = os.getenv("DAILY_SUMMARY_TIME", "09:00")


# =========================
# ENVIRONMENT THRESHOLDS (initial defaults)
# =========================
TEMP_HIGH = float(os.getenv("TEMP_HIGH", "27"))
TEMP_LOW = float(os.getenv("TEMP_LOW", "18"))
TEMP_CRITICAL = float(os.getenv("TEMP_CRITICAL", "32"))
HUMIDITY_HIGH = float(os.getenv("HUMIDITY_HIGH", "70"))
HUMIDITY_LOW = float(os.getenv("HUMIDITY_LOW", "35"))
HUMIDITY_CRITICAL = float(os.getenv("HUMIDITY_CRITICAL", "85"))

# Used only by the simulated CO2/power demo scripts in ai/ and sensors/
CO2_WARNING = int(os.getenv("CO2_WARNING", "1000"))
POWER_WARNING = float(os.getenv("POWER_WARNING", "1200"))


# =========================
# MOLD RISK
# =========================
MOLD_HUMIDITY_MODERATE = 60
MOLD_HUMIDITY_HIGH = 70
MOLD_TEMP_MIN = 18


# =========================
# PREDICTIONS
# =========================
PREDICTION_MINUTES_AHEAD = int(os.getenv("PREDICTION_MINUTES_AHEAD", "10"))
PREDICTION_LOOKBACK_MIN = int(os.getenv("PREDICTION_LOOKBACK_MIN", "20"))


# =========================
# DATA / STORAGE
# =========================
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "sensor_data.csv")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
STATS_FILE = os.path.join(DATA_DIR, "daily_stats.json")
MODEL_DIR = os.path.join(BASE_DIR, "models")
OCCUPANCY_MODEL = os.path.join(MODEL_DIR, "occupancy_model.pkl")
ANOMALY_MODEL = os.path.join(MODEL_DIR, "anomaly_model.pkl")
HISTORY_MAX_SIZE = int(os.getenv("HISTORY_MAX_SIZE", "500"))
