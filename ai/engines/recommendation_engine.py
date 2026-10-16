"""
Recommendation Engine - rule-based action suggestions from the current
reading, the short-term forecast and the mold-risk estimate.
"""
from .comfort import mold_risk
from .thresholds import Thresholds

PRIORITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "success": 3}
MAX_RECOMMENDATIONS = 5


def _rec(priority: str, title: str, message: str, action: str) -> dict:
    return {"priority": priority, "title": title, "message": message, "action": action}


class RecommendationEngine:
    def generate(self, latest: dict, predictions: dict, t: Thresholds) -> list[dict]:
        recs: list[dict] = []
        temp = latest.get("temperature")
        hum = latest.get("humidity")

        if not latest.get("broker_connected"):
            recs.append(_rec("critical", "Broker Offline",
                             "The backend cannot reach the MQTT broker.",
                             "Check that Mosquitto is running"))
        elif not latest.get("sensor_online"):
            recs.append(_rec("critical", "Sensor Offline",
                             "No packet from the sensor recently.",
                             "Check the ESP8266 power and Wi-Fi"))

        if temp is not None:
            if temp > t.TEMP_HIGH:
                recs.append(_rec("warning", "Temperature High",
                                 f"Current {temp}°C exceeds {t.TEMP_HIGH}°C.",
                                 "Increase cooling or open ventilation"))
            elif temp < t.TEMP_LOW:
                recs.append(_rec("warning", "Temperature Low",
                                 f"Current {temp}°C is below {t.TEMP_LOW}°C.",
                                 "Increase heating"))
            elif predictions.get("temperature", {}).get("risk") in ("warning", "critical"):
                p = predictions["temperature"]
                recs.append(_rec("info", "Temperature Rising",
                                 f"Forecast {p['predicted']}°C in {predictions['minutes_ahead']} min.",
                                 "Prepare cooling"))

        if hum is not None:
            if hum > t.HUMIDITY_HIGH:
                recs.append(_rec("warning", "High Humidity",
                                 f"Humidity {hum}% exceeds {t.HUMIDITY_HIGH}%.",
                                 "Run a dehumidifier or ventilate"))
            elif hum < t.HUMIDITY_LOW:
                recs.append(_rec("info", "Low Humidity",
                                 f"Humidity {hum}% is below {t.HUMIDITY_LOW}%. Dry air.",
                                 "Consider a humidifier"))
            elif predictions.get("humidity", {}).get("risk") in ("warning", "critical"):
                p = predictions["humidity"]
                recs.append(_rec("info", "Humidity Rising",
                                 f"Forecast {p['predicted']}% in {predictions['minutes_ahead']} min.",
                                 "Ventilate before it builds up"))

        if temp is not None and hum is not None:
            risk = mold_risk(temp, hum)
            if risk == "high":
                recs.append(_rec("warning", "Mold Risk High",
                                 "Warm and humid conditions favour mold growth.",
                                 "Ventilate and keep humidity below 60%"))
            elif risk == "moderate":
                recs.append(_rec("info", "Mold Risk Moderate",
                                 "Humidity is in the range where mold can start.",
                                 "Air the room regularly"))

            in_band = t.TEMP_LOW <= temp <= t.TEMP_HIGH and t.HUMIDITY_LOW <= hum <= t.HUMIDITY_HIGH
            if in_band and not recs:
                recs.append(_rec("success", "Optimal Conditions",
                                 "Temperature and humidity are inside the comfort band.",
                                 "Maintain current settings"))

        if not recs:
            recs.append(_rec("info", "Waiting for Data",
                             "No sensor reading received yet.",
                             "Check the sensor and broker"))

        recs.sort(key=lambda r: PRIORITY_ORDER.get(r["priority"], 4))
        return recs[:MAX_RECOMMENDATIONS]
