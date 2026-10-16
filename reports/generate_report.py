"""
Text report over data/sensor_data.csv (SIMULATED CO2/power data).
Run: python reports/generate_report.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CO2_WARNING, CSV_FILE  # noqa: E402

HIGH_AVG_POWER_W = 1500


def generate_simple_report() -> str | None:
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print("No sensor data found.")
        return None
    if df.empty:
        print("Sensor data file is empty.")
        return None

    avg_co2 = round(df["co2"].mean(), 1)
    avg_power = round(df["power"].mean(), 1)

    report = f"""
Smart Building AI Report (simulated data, {len(df)} rows)

Average CO2 level: {avg_co2} ppm
Average power consumption: {avg_power} W
Maximum CO2 recorded: {df["co2"].max()} ppm
Maximum power recorded: {df["power"].max()} W

Summary:
"""
    report += ("Ventilation performance appears poor and should be reviewed.\n"
               if avg_co2 > CO2_WARNING else "Ventilation levels appear generally acceptable.\n")
    report += ("Energy consumption appears high and may indicate HVAC or equipment waste.\n"
               if avg_power > HIGH_AVG_POWER_W else "Energy consumption appears within a moderate range.\n")
    return report


if __name__ == "__main__":
    text = generate_simple_report()
    if text:
        print(text)
