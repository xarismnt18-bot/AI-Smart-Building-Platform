"""
Prediction Engine - short-term forecasts from the live telemetry history.

Method: exponentially weighted linear regression over the last
`lookback_min` minutes, fitted against real elapsed seconds (not sample
index), so the forecast horizon is correct whatever the sensor's send rate.

Confidence comes from the fit itself: the weighted residual spread is
widened for how far we extrapolate beyond the observed window, then
mapped to 0-100 relative to a metric-specific tolerance.
"""
import math

import numpy as np

from .thresholds import Thresholds

# Change per minute that counts as a real trend (DHT11 resolution is 1 degC / 1 %).
TREND_PER_MIN = {"temperature": 0.1, "humidity": 0.5}
# Prediction spread (1 sigma) at which confidence drops to ~37 %.
TOLERANCE = {"temperature": 1.0, "humidity": 5.0}
MIN_POINTS = 3
MIN_SPAN_SEC = 30


def _unknown(current=None, points=0) -> dict:
    return {
        "current": current,
        "predicted": None,
        "confidence": 0,
        "trend": "unknown",
        "risk": "unknown",
        "data_points": points,
    }


def risk_level(value: float, warn: float, crit: float) -> str:
    if value >= crit:
        return "critical"
    if value >= warn:
        return "warning"
    return "normal"


class PredictionEngine:
    def __init__(self, minutes_ahead: int = 10, lookback_min: int = 20):
        self.minutes_ahead = minutes_ahead
        self.lookback_min = lookback_min

    def predict_metric(self, history: list[dict], metric: str, thresholds: Thresholds) -> dict:
        samples = [(h["ts"], float(h[metric])) for h in history
                   if h.get("ts") is not None and h.get(metric) is not None]
        current = samples[-1][1] if samples else None
        if not samples:
            return _unknown()

        t_last = samples[-1][0]
        window = [(t, v) for t, v in samples if t_last - t <= self.lookback_min * 60]
        span = t_last - window[0][0]
        if len(window) < MIN_POINTS or span < MIN_SPAN_SEC:
            return _unknown(current, len(window))

        x = np.array([t - t_last for t, _ in window])  # seconds, <= 0
        y = np.array([v for _, v in window])
        w = np.exp(x / span)  # oldest point weight ~0.37, newest 1.0

        slope, intercept = np.polyfit(x, y, 1, w=np.sqrt(w))
        horizon = self.minutes_ahead * 60
        predicted = float(slope * horizon + intercept)

        residuals = y - (slope * x + intercept)
        resid_std = math.sqrt(float(np.sum(w * residuals ** 2) / np.sum(w)))
        spread = resid_std * math.sqrt(1 + (horizon / span) ** 2)
        confidence = round(100 * math.exp(-spread / TOLERANCE[metric]), 1)

        slope_per_min = slope * 60
        threshold = TREND_PER_MIN[metric]
        trend = "rising" if slope_per_min > threshold else "falling" if slope_per_min < -threshold else "stable"

        if metric == "temperature":
            warn, crit = thresholds.TEMP_HIGH, thresholds.TEMP_CRITICAL
        else:
            warn, crit = thresholds.HUMIDITY_HIGH, thresholds.HUMIDITY_CRITICAL
            predicted = min(max(predicted, 0.0), 100.0)

        return {
            "current": current,
            "predicted": round(predicted, 1),
            "confidence": confidence,
            "trend": trend,
            "slope_per_min": round(slope_per_min, 3) + 0.0,
            "risk": risk_level(predicted, warn, crit),
            "data_points": len(window),
        }

    def predict_all(self, history: list[dict], thresholds: Thresholds) -> dict:
        temp = self.predict_metric(history, "temperature", thresholds)
        hum = self.predict_metric(history, "humidity", thresholds)
        return {
            "temperature": temp,
            "humidity": hum,
            "minutes_ahead": self.minutes_ahead,
            "data_points": max(temp["data_points"], hum["data_points"]),
        }
