import random
import time
from datetime import datetime
import pandas as pd
import os


CSV_FILE = "data/sensor_data.csv"


def generate_sensor_data():

    sensor_data = {

        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "room": "Main Office",

        "co2": random.randint(400, 1200),

        "temperature": round(random.uniform(20, 28), 1),

        "humidity": round(random.uniform(30, 70), 1),

        "power": round(random.uniform(100, 2500), 1)

    }

    return sensor_data


while True:

    data = generate_sensor_data()

    print(data)

    df = pd.DataFrame([data])

    file_exists = os.path.isfile(CSV_FILE)

    df.to_csv(
        CSV_FILE,
        mode='a',
        header=not file_exists,
        index=False
    )

    time.sleep(2)