import random
import time
from datetime import datetime
import pandas as pd
import joblib


MODEL_FILE = "models/occupancy_model.pkl"

model = joblib.load(MODEL_FILE)

print("AI Anomaly Detection System Loaded.\n")


def generate_sensor_data():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "co2": random.randint(400, 1400),
        "temperature": round(random.uniform(18, 32), 1),
        "humidity": round(random.uniform(25, 75), 1),
        "power": round(random.uniform(50, 3000), 1)
    }


def detect_anomalies(sensor_data, occupancy_status):
    anomalies = []

    if occupancy_status == "Empty" and sensor_data["power"] > 1200:
        anomalies.append("Possible AC/equipment waste: high power while room is empty.")

    if occupancy_status == "Occupied" and sensor_data["co2"] > 1000:
        anomalies.append("Poor ventilation: high CO2 while room is occupied.")

    if occupancy_status == "Occupied" and sensor_data["temperature"] > 27:
        anomalies.append("Thermal discomfort: temperature is too high while occupied.")

    if sensor_data["humidity"] > 70:
        anomalies.append("High humidity detected.")

    return anomalies


while True:
    sensor_data = generate_sensor_data()

    df = pd.DataFrame([{
        "co2": sensor_data["co2"],
        "temperature": sensor_data["temperature"],
        "humidity": sensor_data["humidity"],
        "power": sensor_data["power"]
    }])

    prediction = model.predict(df)[0]
    occupancy_status = "Occupied" if prediction == 1 else "Empty"

    anomalies = detect_anomalies(sensor_data, occupancy_status)

    print("\n----------------------------------")
    print(f"Timestamp: {sensor_data['timestamp']}")
    print(f"CO2: {sensor_data['co2']} ppm")
    print(f"Temperature: {sensor_data['temperature']} °C")
    print(f"Humidity: {sensor_data['humidity']} %")
    print(f"Power: {sensor_data['power']} W")
    print(f"AI Occupancy Prediction: {occupancy_status}")

    if anomalies:
        print("Alerts:")
        for alert in anomalies:
            print(f"- {alert}")
    else:
        print("Alerts: No anomalies detected.")

    time.sleep(3)