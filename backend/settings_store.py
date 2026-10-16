"""
Persistent alert thresholds: defaults from config.py/.env, overrides saved
to data/settings.json by the dashboard (PUT /config).
"""
import json
import logging
import os
import threading
from dataclasses import fields, replace

from ai.engines import Thresholds

logger = logging.getLogger(__name__)
FIELD_NAMES = {f.name for f in fields(Thresholds)}


class SettingsStore:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._thresholds = self._load()

    @property
    def thresholds(self) -> Thresholds:
        with self._lock:
            return self._thresholds

    def update(self, changes: dict) -> Thresholds:
        """Apply a partial update, validate it, persist it. Raises ValueError."""
        unknown = set(changes) - FIELD_NAMES
        if unknown:
            raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
        with self._lock:
            candidate = replace(self._thresholds, **{k: float(v) for k, v in changes.items()})
            candidate.validate()
            self._save(candidate)
            self._thresholds = candidate
            return candidate

    def reset(self) -> Thresholds:
        with self._lock:
            self._thresholds = Thresholds()
            if os.path.exists(self._path):
                os.remove(self._path)
            return self._thresholds

    def _load(self) -> Thresholds:
        defaults = Thresholds()
        if not os.path.exists(self._path):
            return defaults
        try:
            with open(self._path, encoding="utf-8") as f:
                saved = {k: float(v) for k, v in json.load(f).items() if k in FIELD_NAMES}
            loaded = replace(defaults, **saved)
            loaded.validate()
            return loaded
        except (OSError, ValueError, TypeError) as e:
            logger.error("Ignoring invalid %s (%s); using defaults", self._path, e)
            return defaults

    def _save(self, thresholds: Thresholds) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(thresholds.as_dict(), f, indent=2)
        os.replace(tmp, self._path)
