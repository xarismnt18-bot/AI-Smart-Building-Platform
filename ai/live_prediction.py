"""
SIMULATION DEMO - occupancy prediction on *simulated* CO2/power data.
Not used by the backend. Run: python ai/live_prediction.py
"""
import os
import random
import sys
import time
from datetime import datetime

import joblib
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import OCCUPANCY_MODEL  # noqa: E402

FEATURES = ["co2", "temperature", "humidity", "power"]


def generate_sensor_data():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "co2": random.randint(400, 1200),
        "temperature": round(random.uniform(20, 28), 1),
        "humidity": round(random.uniform(30, 70), 1),
        "power": round(random.uniform(100, 2500), 1),
    }


def main():
    model = joblib.load(OCCUPANCY_MODEL)
    print("Simulation demo: occupancy model loaded.\n")

    while True:
        sensor_data = generate_sensor_data()
        df = pd.DataFrame([{k: sensor_data[k] for k in FEATURES}])
        occupancy_status = "Occupied" if model.predict(df)[0] == 1 else "Empty"

        print("\n----------------------------------")
        print(f"Timestamp: {sensor_data['timestamp']}")
        print(f"CO2: {sensor_data['co2']} ppm | Temp: {sensor_data['temperature']} °C | "
              f"Humidity: {sensor_data['humidity']} % | Power: {sensor_data['power']} W")
        print(f"Occupancy (model): {occupancy_status}")

        time.sleep(3)


if __name__ == "__main__":
    main()
