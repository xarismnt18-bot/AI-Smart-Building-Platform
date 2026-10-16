import * as THREE from "three";
import { THRESHOLDS } from "../config";

// Status colours shared by the 3D twin and the UI (good / warning / critical).
export const STATUS_COLORS = {
  cold: "#3b82f6",
  cool: "#22d3ee",
  good: "#22c55e",
  warning: "#facc15",
  critical: "#ef4444",
  dry: "#f59e0b",
  idle: "#00ff88",
};

function gradient(value, stops) {
  if (value == null || Number.isNaN(value)) return null;
  if (value <= stops[0][0]) return new THREE.Color(stops[0][1]);
  for (let i = 1; i < stops.length; i++) {
    const [v1, c1] = stops[i];
    const [v0, c0] = stops[i - 1];
    if (value <= v1) {
      const t = (value - v0) / (v1 - v0 || 1);
      return new THREE.Color(c0).lerp(new THREE.Color(c1), t);
    }
  }
  return new THREE.Color(stops[stops.length - 1][1]);
}

/** Blue (cold) -> green (comfortable) -> yellow (warm) -> red (critical). */
export function temperatureColor(temp) {
  const { TEMP_LOW, TEMP_HIGH, TEMP_CRITICAL } = THRESHOLDS;
  return gradient(temp, [
    [TEMP_LOW - 4, STATUS_COLORS.cold],
    [TEMP_LOW, STATUS_COLORS.cool],
    [(TEMP_LOW + TEMP_HIGH) / 2, STATUS_COLORS.good],
    [TEMP_HIGH, STATUS_COLORS.warning],
    [TEMP_CRITICAL, STATUS_COLORS.critical],
  ]);
}

/** Amber (dry) -> green (comfortable) -> yellow (humid) -> red (critical). */
export function humidityColor(hum) {
  const { HUMIDITY_LOW, HUMIDITY_HIGH, HUMIDITY_CRITICAL } = THRESHOLDS;
  return gradient(hum, [
    [HUMIDITY_LOW - 10, STATUS_COLORS.dry],
    [HUMIDITY_LOW, STATUS_COLORS.cool],
    [(HUMIDITY_LOW + HUMIDITY_HIGH) / 2, STATUS_COLORS.good],
    [HUMIDITY_HIGH, STATUS_COLORS.warning],
    [HUMIDITY_CRITICAL, STATUS_COLORS.critical],
  ]);
}

/** CSS linear-gradient matching temperatureColor, for the on-screen legend. */
export function temperatureLegendGradient() {
  return `linear-gradient(90deg, ${STATUS_COLORS.cold}, ${STATUS_COLORS.cool}, ${STATUS_COLORS.good}, ${STATUS_COLORS.warning}, ${STATUS_COLORS.critical})`;
}

export function humidityLegendGradient() {
  return `linear-gradient(90deg, ${STATUS_COLORS.dry}, ${STATUS_COLORS.cool}, ${STATUS_COLORS.good}, ${STATUS_COLORS.warning}, ${STATUS_COLORS.critical})`;
}
