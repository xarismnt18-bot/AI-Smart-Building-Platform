"""
SIMULATION DEMO - anomaly + occupancy detection on *simulated* CO2/power data.

The real sensor (DHT11) only reports temperature and humidity, so this script
generates fake CO2/power readings. It is not used by the backend.

Run:  python ai/anomaly_detection.py   (after training both models)
"""
import os
import random
import sys
import time
from datetime import datetime

import joblib
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ANOMALY_MODEL, CO2_WARNING, HUMIDITY_HIGH, OCCUPANCY_MODEL, POWER_WARNING, TEMP_HIGH  # noqa: E402

FEATURES = ["co2", "temperature", "humidity", "power"]


def generate_sensor_data():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "co2": random.randint(400, 1400),
        "temperature": round(random.uniform(18, 32), 1),
        "humidity": round(random.uniform(25, 75), 1),
        "power": round(random.uniform(50, 3000), 1),
    }


def rule_based_alerts(sensor_data, occupancy_status):
    alerts = []
    if occupancy_status == "Empty" and sensor_data["power"] > POWER_WARNING:
        alerts.append("Possible AC/equipment waste: high power while room is empty.")
    if occupancy_status == "Occupied" and sensor_data["co2"] > CO2_WARNING:
        alerts.append("Poor ventilation: high CO2 while room is occupied.")
    if occupancy_status == "Occupied" and sensor_data["temperature"] > TEMP_HIGH:
        alerts.append("Thermal discomfort: temperature is too high while occupied.")
    if sensor_data["humidity"] > HUMIDITY_HIGH:
        alerts.append("High humidity detected.")
    return alerts


def main():
    occupancy_model = joblib.load(OCCUPANCY_MODEL)
    anomaly_model = joblib.load(ANOMALY_MODEL)
    print("Simulation demo: models loaded.\n")

    while True:
        sensor_data = generate_sensor_data()
        df = pd.DataFrame([{k: sensor_data[k] for k in FEATURES}])

        occupancy_status = "Occupied" if occupancy_model.predict(df)[0] == 1 else "Empty"
        is_anomaly = anomaly_model.predict(df)[0] == -1
        alerts = rule_based_alerts(sensor_data, occupancy_status)

        print("\n----------------------------------")
        print(f"Timestamp: {sensor_data['timestamp']}")
        print(f"CO2: {sensor_data['co2']} ppm | Temp: {sensor_data['temperature']} °C | "
              f"Humidity: {sensor_data['humidity']} % | Power: {sensor_data['power']} W")
        print(f"Occupancy (model): {occupancy_status}")
        print(f"IsolationForest: {'ANOMALY' if is_anomaly else 'normal'}")
        print("Alerts:" if alerts else "Alerts: none")
        for alert in alerts:
            print(f"- {alert}")

        time.sleep(3)


if __name__ == "__main__":
    main()
