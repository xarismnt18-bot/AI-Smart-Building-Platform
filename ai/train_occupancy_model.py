import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib


DATA_FILE = "data/sensor_data.csv"
MODEL_FILE = "models/occupancy_model.pkl"


df = pd.read_csv(DATA_FILE)

# Rule-based labels for now.
# Later, these labels can come from real occupancy data.
df["occupied"] = ((df["co2"] > 700) | (df["power"] > 900)).astype(int)

features = ["co2", "temperature", "humidity", "power"]
X = df[features]
y = df["occupied"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("Model training completed.")
print(classification_report(y_test, predictions))

joblib.dump(model, MODEL_FILE)

print(f"Model saved to: {MODEL_FILE}")