import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest


DATA_FILE = "data/sensor_data.csv"
MODEL_FILE = "models/anomaly_model.pkl"


df = pd.read_csv(DATA_FILE)

features = ["co2", "temperature", "humidity", "power"]
X = df[features]

model = IsolationForest(
    n_estimators=100,
    contamination=0.10,
    random_state=42
)

model.fit(X)

df["anomaly_prediction"] = model.predict(X)
df["anomaly_status"] = df["anomaly_prediction"].map({
    1: "Normal",
    -1: "Anomaly"
})

print("Anomaly model trained successfully.")
print(df["anomaly_status"].value_counts())

joblib.dump(model, MODEL_FILE)

print(f"Model saved to: {MODEL_FILE}")