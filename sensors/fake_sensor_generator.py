"""
Simulated sensor that appends fake CO2/temperature/humidity/power rows to
data/sensor_data.csv every 2 s - training data for the demo models.
Run: python sensors/fake_sensor_generator.py   (Ctrl+C to stop)
"""
import os
import random
import sys
import time
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CSV_FILE, DATA_DIR  # noqa: E402


def generate_sensor_data():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "room": "Main Office",
        "co2": random.randint(400, 1200),
        "temperature": round(random.uniform(20, 28), 1),
        "humidity": round(random.uniform(30, 70), 1),
        "power": round(random.uniform(100, 2500), 1),
    }


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    while True:
        data = generate_sensor_data()
        print(data)
        pd.DataFrame([data]).to_csv(
            CSV_FILE, mode="a", header=not os.path.isfile(CSV_FILE), index=False,
        )
        time.sleep(2)


if __name__ == "__main__":
    main()
