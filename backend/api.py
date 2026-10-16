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
)
from ai.mqtt_client import SharedMQTTClient  # noqa: E402
from ai.engines import (  # noqa: E402
    PredictionEngine, RecommendationEngine,
    dew_point, health_score, health_status, mold_risk,
)
from backend.settings_store import SettingsStore  # noqa: E402

logger = logging.getLogger(__name__)

sensor = SharedMQTTClient(max_history=HISTORY_MAX_SIZE)
settings = SettingsStore(SETTINGS_FILE)
predictor = PredictionEngine(PREDICTION_MINUTES_AHEAD, PREDICTION_LOOKBACK_MIN)
recommender = RecommendationEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sensor.start()
    yield
    sensor.stop()


app = FastAPI(title="Smart Building AI OS API", version="6.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # no cookies/auth; required to be False with "*"
    allow_methods=["GET", "PUT", "DELETE"],
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
    latest = sensor.latest
    t = settings.thresholds
    temp, hum = latest["temperature"], latest["humidity"]
    alerts = []

    if not latest["broker_connected"]:
        alerts.append("MQTT broker is unreachable.")
    elif not latest["sensor_online"]:
        alerts.append("Sensor is offline: no recent packets.")

    if temp is not None and temp > t.TEMP_HIGH:
        alerts.append("Temperature is above comfort threshold.")
    if temp is not None and temp < t.TEMP_LOW:
        alerts.append("Temperature is below comfort threshold.")
    if hum is not None and hum > t.HUMIDITY_HIGH:
        alerts.append("Humidity is above comfort threshold. Mold risk may increase.")
    if hum is not None and hum < t.HUMIDITY_LOW:
        alerts.append("Humidity is low. Dry-air conditions detected.")

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
