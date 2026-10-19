import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (  # noqa: E402
    CORS_ORIGINS, HISTORY_MAX_SIZE, SETTINGS_FILE,
    PREDICTION_MINUTES_AHEAD, PREDICTION_LOOKBACK_MIN, SENSOR_STALE_SEC,
    MQTT_PORT, DISCOVERY_ENABLED, DISCOVERY_PORT, DISCOVERY_INTERVAL_SEC,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTIFY_CHECK_SEC, NOTIFY_COOLDOWN_MIN,
    DAILY_SUMMARY_TIME, STATS_FILE,
    VOICEMONKEY_TOKEN, VOICEMONKEY_DEVICE, VOICE_QUIET_HOURS, VOICE_STATUS_VAR, VOICE_STATUS_SEC,
)
from ai.mqtt_client import SharedMQTTClient  # noqa: E402
from ai.engines import (  # noqa: E402
    PredictionEngine, RecommendationEngine,
    dew_point, health_score, health_status, mold_risk,
)
from backend.settings_store import SettingsStore  # noqa: E402
from backend.alerts import active_alerts  # noqa: E402
from backend.discovery import BrokerBeacon  # noqa: E402
from backend.notifier import AlertNotifier, TelegramClient  # noqa: E402
from backend.daily_stats import DailyStats  # noqa: E402
from backend.telegram_bot import TelegramBot  # noqa: E402
from backend.voice import VoiceAnnouncer, VoiceStatusPublisher  # noqa: E402

logger = logging.getLogger(__name__)

sensor = SharedMQTTClient(max_history=HISTORY_MAX_SIZE)
settings = SettingsStore(SETTINGS_FILE)
predictor = PredictionEngine(PREDICTION_MINUTES_AHEAD, PREDICTION_LOOKBACK_MIN)
recommender = RecommendationEngine()
beacon = BrokerBeacon(MQTT_PORT, DISCOVERY_PORT, DISCOVERY_INTERVAL_SEC)
telegram = TelegramClient(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
voice = VoiceAnnouncer(VOICEMONKEY_TOKEN, VOICEMONKEY_DEVICE, VOICE_QUIET_HOURS)
notifier = AlertNotifier(telegram, sensor, settings, NOTIFY_CHECK_SEC, NOTIFY_COOLDOWN_MIN, voice=voice)
voice_status = VoiceStatusPublisher(voice, sensor, settings, VOICE_STATUS_VAR, VOICE_STATUS_SEC)
bot = TelegramBot(telegram, notifier, sensor, settings, predictor, DailyStats(STATS_FILE), DAILY_SUMMARY_TIME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sensor.start()
    if DISCOVERY_ENABLED:
        beacon.start()
    notifier.start()
    bot.start()
    voice_status.start()
    yield
    voice_status.stop()
    bot.stop()
    notifier.stop()
    beacon.stop()
    sensor.stop()


app = FastAPI(title="Smart Building AI OS API", version="6.7.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # no cookies/auth; required to be False with "*"
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# =========================
# STATUS / DATA
# =========================
@app.get("/")
def root():
    latest = sensor.latest
    return {
        "message": "Smart Building AI OS API is running",
        "version": app.version,
        "mqtt_topic": sensor.topic,
        "broker": sensor.broker,
        "broker_connected": latest["broker_connected"],
        "sensor_online": latest["sensor_online"],
        "sensor_stale_after_sec": SENSOR_STALE_SEC,
    }


@app.get("/latest")
def get_latest():
    return sensor.latest


@app.get("/history")
def get_history(limit: int | None = Query(None, ge=1, le=HISTORY_MAX_SIZE)):
    return sensor.history(limit)


@app.get("/health")
def get_health():
    latest = sensor.latest
    temp, hum = latest["temperature"], latest["humidity"]

    if temp is None or hum is None:
        return {
            "status": "WAITING_FOR_DATA",
            "health_score": None,
            "message": "No MQTT data received yet",
        }

    score = health_score(temp, hum, settings.thresholds)
    return {
        "status": health_status(score),
        "health_score": score,
        "temperature": temp,
        "humidity": hum,
        "dew_point": dew_point(temp, hum),
        "mold_risk": mold_risk(temp, hum),
        "sensor_online": latest["sensor_online"],
    }


@app.get("/alerts")
def get_alerts():
    alerts = [a.message for a in active_alerts(sensor.latest, settings.thresholds)]
    return {"alerts": alerts or ["No active alerts."]}


# =========================
# AI
# =========================
@app.get("/predictions")
def get_predictions():
    return predictor.predict_all(sensor.history(), settings.thresholds)


@app.get("/recommendations")
def get_recommendations():
    t = settings.thresholds
    predictions = predictor.predict_all(sensor.history(), t)
    return {"recommendations": recommender.generate(sensor.latest, predictions, t)}


# =========================
# CONFIG (single source of truth for thresholds)
# =========================
@app.get("/config")
def get_config():
    return {"thresholds": settings.thresholds.as_dict(), "mqtt_topic": sensor.topic}


@app.put("/config")
def put_config(changes: dict[str, float]):
    try:
        updated = settings.update(changes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"thresholds": updated.as_dict(), "mqtt_topic": sensor.topic}


@app.delete("/config")
def reset_config():
    return {"thresholds": settings.reset().as_dict(), "mqtt_topic": sensor.topic}


# =========================
# NOTIFICATIONS
# =========================
@app.get("/notifications")
def get_notifications():
    muted = notifier.muted_until
    return {
        "telegram_enabled": telegram.enabled,
        "voice_enabled": voice.enabled,
        "voice_on": voice.on,
        "voice_quiet_hours": voice.quiet_hours,
        "muted_until": muted,
    }


@app.post("/notifications/test")
def send_test_notification():
    room = sensor.latest.get("room") or "AIOS"
    try:
        notifier.telegram.send(f"👋 Test from AIOS: Telegram alerts for {room} are working.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"sent": True}


@app.post("/voice/test")
def send_test_announcement():
    try:
        voice.announce("This is a test from your smart home. Voice alerts are working.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"sent": True}


@app.get("/voice/status")
def get_voice_status():
    """The sentence Alexa reads for "Alexa, bedroom status", and whether it reached Voice Monkey."""
    return {
        "enabled": voice.enabled,
        "variable": voice_status.variable,
        "text": voice_status.text,
        "last_error": voice_status.last_error,
    }
