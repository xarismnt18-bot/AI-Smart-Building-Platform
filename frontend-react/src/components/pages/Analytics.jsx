import { useMemo, useState } from "react";
import { THRESHOLDS } from "../../config";
import { lastSeconds, toSeries } from "../../lib/series";
import TimeSeriesChart from "../charts/TimeSeriesChart";
import AnimatedNumber from "../ui/AnimatedNumber";

const RANGES = [
  ["15 min", 15 * 60],
  ["1 hour", 60 * 60],
  ["6 hours", 6 * 60 * 60],
  ["All", null],
];
const TEMP_COLOR = "#f97316";
const HUM_COLOR = "#22d3ee";

export default function Analytics({ telemetry, room }) {
  const { history, healthInfo } = telemetry;
  const [range, setRange] = useState(RANGES[1][1]);
  const [hoverTs, setHoverTs] = useState(null);

  const temps = useMemo(() => lastSeconds(toSeries(history, "temperature"), range), [history, range]);
  const hums = useMemo(() => lastSeconds(toSeries(history, "humidity"), range), [history, range]);

  return (
    <div className="module-page">
      <h1>Analytics</h1>
      <p className="module-subtitle">{room} telemetry. Hover or use the arrow keys on a chart to inspect a moment.</p>

      <div className="range-filter" role="group" aria-label="Time range">
        {RANGES.map(([label, seconds]) => (
          <button
            key={label}
            type="button"
            className={range === seconds ? "active" : ""}
            aria-pressed={range === seconds}
            onClick={() => setRange(seconds)}
          >
            {label}
          </button>
        ))}
        <span className="range-filter__note">{temps.length} readings kept in memory (restart clears them)</span>
      </div>

      <div className="analytics-grid">
        <div className="module-card">
          <TimeSeriesChart
            title="Temperature"
            unit="°C"
            color={TEMP_COLOR}
            points={temps}
            band={{ low: THRESHOLDS.TEMP_LOW, high: THRESHOLDS.TEMP_HIGH }}
            hoverTs={hoverTs}
            onHover={setHoverTs}
          />
        </div>
        <div className="module-card">
          <TimeSeriesChart
            title="Humidity"
            unit="%"
            color={HUM_COLOR}
            points={hums}
            band={{ low: THRESHOLDS.HUMIDITY_LOW, high: THRESHOLDS.HUMIDITY_HIGH }}
            hoverTs={hoverTs}
            onHover={setHoverTs}
          />
        </div>
        <div className="module-card analytics-health">
          <h3>Health score</h3>
          <div className="big-score">
            <AnimatedNumber value={healthInfo.health_score ?? null} decimals={0} suffix="/100" />
          </div>
          <dl className="analytics-health__facts">
            <div><dt>Status</dt><dd>{healthInfo.status?.replaceAll("_", " ").toLowerCase() ?? "--"}</dd></div>
            <div><dt>Dew point</dt><dd>{healthInfo.dew_point != null ? `${healthInfo.dew_point} °C` : "--"}</dd></div>
            <div><dt>Mold risk</dt><dd>{healthInfo.mold_risk ?? "--"}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  );
}
