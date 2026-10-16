"""
Alert thresholds shared by every engine (and served to the dashboard).
"""
import os
import sys
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config  # noqa: E402


@dataclass(frozen=True)
class Thresholds:
    TEMP_LOW: float = config.TEMP_LOW
    TEMP_HIGH: float = config.TEMP_HIGH
    TEMP_CRITICAL: float = config.TEMP_CRITICAL
    HUMIDITY_LOW: float = config.HUMIDITY_LOW
    HUMIDITY_HIGH: float = config.HUMIDITY_HIGH
    HUMIDITY_CRITICAL: float = config.HUMIDITY_CRITICAL

    def validate(self) -> None:
        if not self.TEMP_LOW < self.TEMP_HIGH <= self.TEMP_CRITICAL:
            raise ValueError("Temperature thresholds must satisfy LOW < HIGH <= CRITICAL")
        if not 0 <= self.HUMIDITY_LOW < self.HUMIDITY_HIGH <= self.HUMIDITY_CRITICAL <= 100:
            raise ValueError("Humidity thresholds must satisfy 0 <= LOW < HIGH <= CRITICAL <= 100")

    def as_dict(self) -> dict:
        return asdict(self)
