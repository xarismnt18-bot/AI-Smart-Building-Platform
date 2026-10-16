"""
Comfort analytics derived from temperature + relative humidity:
health score, dew point and mold risk.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import MOLD_HUMIDITY_HIGH, MOLD_HUMIDITY_MODERATE, MOLD_TEMP_MIN  # noqa: E402

from .thresholds import Thresholds


def health_score(temp: float, hum: float, t: Thresholds) -> int:
    """0-100 score; 100 = inside every comfort band."""
    score = 100.0
    if temp > t.TEMP_HIGH:
        score -= min((temp - t.TEMP_HIGH) * 8, 35)
    if temp < t.TEMP_LOW:
        score -= min((t.TEMP_LOW - temp) * 6, 30)
    if hum > t.HUMIDITY_HIGH:
        score -= min((hum - t.HUMIDITY_HIGH) * 4, 35)
    if hum < t.HUMIDITY_LOW:
        score -= min((t.HUMIDITY_LOW - hum) * 2, 20)
    return max(int(score), 20)


def health_status(score: int) -> str:
    if score >= 80:
        return "OPTIMAL"
    if score >= 60:
        return "ATTENTION_REQUIRED"
    return "CRITICAL"


def dew_point(temp: float, hum: float) -> float:
    """Magnus formula, accurate to ~0.4 degC for normal indoor ranges."""
    a, b = 17.62, 243.12
    gamma = math.log(max(hum, 1.0) / 100.0) + a * temp / (b + temp)
    return round(b * gamma / (a - gamma), 1)


def mold_risk(temp: float, hum: float) -> str:
    """'low' | 'moderate' | 'high' - mold needs both moisture and warmth."""
    if temp < MOLD_TEMP_MIN:
        return "low" if hum < MOLD_HUMIDITY_HIGH else "moderate"
    if hum >= MOLD_HUMIDITY_HIGH:
        return "high"
    if hum >= MOLD_HUMIDITY_MODERATE:
        return "moderate"
    return "low"
