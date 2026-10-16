"""
Train an IsolationForest on data/sensor_data.csv (SIMULATED CO2/power data
from sensors/fake_sensor_generator.py). Output: models/anomaly_model.pkl
"""
import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ANOMALY_MODEL, CSV_FILE, MODEL_DIR  # noqa: E402

FEATURES = ["co2", "temperature", "humidity", "power"]
MIN_ROWS = 50


def main():
    df = pd.read_csv(CSV_FILE)
    if len(df) < MIN_ROWS:
        sys.exit(f"Need at least {MIN_ROWS} rows in {CSV_FILE}, found {len(df)}.")

    model = IsolationForest(n_estimators=100, contamination=0.10, random_state=42)
    model.fit(df[FEATURES])

    status = pd.Series(model.predict(df[FEATURES])).map({1: "Normal", -1: "Anomaly"})
    print("Anomaly model trained.")
    print(status.value_counts())

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, ANOMALY_MODEL)
    print(f"Model saved to: {ANOMALY_MODEL}")


if __name__ == "__main__":
    main()
