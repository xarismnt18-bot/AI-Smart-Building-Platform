import json
from datetime import datetime
from threading import Lock

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# =========================
# MQTT SETTINGS
# =========================
MQTT_BROKER = "192.168.1.143"
MQTT_PORT = 1883
MQTT_TOPIC = "smartroom/dht11"


# =========================
# GLOBAL MEMORY
# =========================
data_lock = Lock()

latest_data = {
    "room": "My Room",
    "temperature": None,
    "humidity": None,
    "connected": False,
    "last_update": None,
}

history = []


# =========================
# FASTAPI APP
# =========================
app = FastAPI(
    title="Smart Building AI OS API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# MQTT CALLBACKS
# =========================
def on_connect(client, userdata, flags, rc):
    with data_lock:
        latest_data["connected"] = rc == 0

    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        print(f"Connected to MQTT broker and subscribed to {MQTT_TOPIC}")
    else:
        print(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    global latest_data, history

    try:
        payload = json.loads(msg.payload.decode())

        temperature = float(payload["temperature"])
        humidity = float(payload["humidity"])
        room = payload.get("room", "My Room")

        packet = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "room": room,
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "connected": True,
            "last_update": datetime.now().strftime("%H:%M:%S"),
        }

        with data_lock:
            latest_data.update(packet)
            history.append(packet)

            if len(history) > 500:
                history = history[-500:]

        print("MQTT packet received:", packet)

    except Exception as e:
        print("MQTT payload error:", e)
        with data_lock:
            latest_data["connected"] = False


# =========================
# MQTT STARTUP
# =========================
@app.on_event("startup")
def start_mqtt():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        app.state.mqtt_client = client
        print("MQTT client started")

    except Exception as e:
        print(f"MQTT connection failed: {e}")
        print("API will continue running without MQTT data")

        with data_lock:
            latest_data["connected"] = False


# =========================
# API ROUTES
# =========================
@app.get("/")
def root():
    return {
        "message": "Smart Building AI OS API is running",
        "mqtt_topic": MQTT_TOPIC,
        "broker": MQTT_BROKER,
    }


@app.get("/latest")
def get_latest():
    with data_lock:
        return latest_data


@app.get("/history")
def get_history():
    with data_lock:
        return history


@app.get("/health")
def get_health():
    with data_lock:
        temp = latest_data["temperature"]
        hum = latest_data["humidity"]

    if temp is None or hum is None:
        return {
            "status": "WAITING_FOR_DATA",
            "health_score": None,
            "message": "No MQTT data received yet"
        }

    score = 100

    if temp > 27:
        score -= min((temp - 27) * 8, 35)

    if hum > 70:
        score -= min((hum - 70) * 4, 35)

    if hum < 40:
        score -= min((40 - hum) * 2, 20)

    score = max(int(score), 20)

    if score >= 80:
        status = "OPTIMAL"
    elif score >= 60:
        status = "ATTENTION_REQUIRED"
    else:
        status = "CRITICAL"

    return {
        "status": status,
        "health_score": score,
        "temperature": temp,
        "humidity": hum,
    }


@app.get("/alerts")
def get_alerts():
    alerts = []

    with data_lock:
        temp = latest_data["temperature"]
        hum = latest_data["humidity"]
        connected = latest_data["connected"]

    if not connected:
        alerts.append("Device is offline or MQTT connection is unstable.")

    if temp is not None and temp > 27:
        alerts.append("Temperature is above comfort threshold.")

    if hum is not None and hum > 70:
        alerts.append("Humidity is above comfort threshold. Mold risk may increase.")

    if hum is not None and hum < 40:
        alerts.append("Humidity is low. Dry-air conditions detected.")

    if not alerts:
        alerts.append("No active alerts.")

    return {
        "alerts": alerts
    }