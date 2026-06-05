import pandas as pd


DATA_FILE = "data/sensor_data.csv"


def generate_simple_report():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print("No sensor data found.")
        return

    avg_co2 = round(df["co2"].mean(), 1)
    avg_power = round(df["power"].mean(), 1)
    max_co2 = df["co2"].max()
    max_power = df["power"].max()

    report = f"""
Smart Building AI Report

Average CO2 level: {avg_co2} ppm
Average power consumption: {avg_power} W
Maximum CO2 recorded: {max_co2} ppm
Maximum power recorded: {max_power} W

Summary:
The monitored space showed an average CO2 level of {avg_co2} ppm and an average power consumption of {avg_power} W.
"""

    if avg_co2 > 1000:
        report += "Ventilation performance appears poor and should be reviewed.\n"
    else:
        report += "Ventilation levels appear generally acceptable.\n"

    if avg_power > 1500:
        report += "Energy consumption appears high and may indicate HVAC or equipment waste.\n"
    else:
        report += "Energy consumption appears within a moderate range.\n"

    print(report)


generate_simple_report()