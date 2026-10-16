"""
Train an occupancy classifier on data/sensor_data.csv (SIMULATED data).

Note: there is no ground-truth occupancy yet, so labels come from a rule
(CO2 > 700 or power > 900). The model can therefore only re-learn that rule;
its accuracy says nothing about real occupancy. Replace `make_labels` with
real labels (e.g. a PIR sensor or a manual log) before trusting it.
"""
import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CSV_FILE, MODEL_DIR, OCCUPANCY_MODEL  # noqa: E402

FEATURES = ["co2", "temperature", "humidity", "power"]
MIN_ROWS = 50


def make_labels(df: pd.DataFrame) -> pd.Series:
    """Placeholder labels - swap for real occupancy data."""
    return ((df["co2"] > 700) | (df["power"] > 900)).astype(int)


def main():
    df = pd.read_csv(CSV_FILE)
    if len(df) < MIN_ROWS:
        sys.exit(f"Need at least {MIN_ROWS} rows in {CSV_FILE}, found {len(df)}.")

    X, y = df[FEATURES], make_labels(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("Model training completed (rule-derived labels, see module docstring).")
    print(classification_report(y_test, model.predict(X_test)))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, OCCUPANCY_MODEL)
    print(f"Model saved to: {OCCUPANCY_MODEL}")


if __name__ == "__main__":
    main()
