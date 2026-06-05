import random
import time
from datetime import datetime
import pandas as pd
import joblib


MODEL_FILE = "models/occupancy_model.pkl"

model = joblib.load(MODEL_FILE)

print("AI Occupancy Model Loaded.\n")


def generate_sensor_data():

    sensor_data = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "co2": random.randint(400, 1200),

        "temperature": round(random.uniform(20, 28), 1),

        "humidity": round(random.uniform(30, 70), 1),

        "power": round(random.uniform(100, 2500), 1)

    }

    return sensor_data


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

    print("\n----------------------------------")
    print(f"Timestamp: {sensor_data['timestamp']}")
    print(f"CO2: {sensor_data['co2']} ppm")
    print(f"Temperature: {sensor_data['temperature']} °C")
    print(f"Humidity: {sensor_data['humidity']} %")
    print(f"Power: {sensor_data['power']} W")
    print(f"AI Prediction: {occupancy_status}")

    time.sleep(3)