"""Active alerts, shared by the /alerts endpoint and the Telegram notifier."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    key: str       # stable id, used to de-duplicate notifications
    message: str   # shown in the dashboard


def active_alerts(latest: dict, thresholds) -> list[Alert]:
    temp, hum = latest["temperature"], latest["humidity"]
    alerts = []

    if not latest["broker_connected"]:
        alerts.append(Alert("broker_offline", "MQTT broker is unreachable."))
    elif not latest["sensor_online"]:
        alerts.append(Alert("sensor_offline", "Sensor is offline: no recent packets."))

    if temp is not None and temp > thresholds.TEMP_HIGH:
        alerts.append(Alert("temp_high", "Temperature is above comfort threshold."))
    if temp is not None and temp < thresholds.TEMP_LOW:
        alerts.append(Alert("temp_low", "Temperature is below comfort threshold."))
    if hum is not None and hum > thresholds.HUMIDITY_HIGH:
        alerts.append(Alert("humidity_high", "Humidity is above comfort threshold. Mold risk may increase."))
    if hum is not None and hum < thresholds.HUMIDITY_LOW:
        alerts.append(Alert("humidity_low", "Humidity is low. Dry-air conditions detected."))

    return alerts
