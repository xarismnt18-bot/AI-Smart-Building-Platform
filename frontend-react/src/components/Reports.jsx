import { useMemo } from "react";
import { THRESHOLDS, formatTime } from "../config";
import StoredExport from "./StoredExport";

function Histogram({ data, field, color, thresholdHigh, thresholdLow, label, unit }) {
  const values = data.map((d) => Number(d[field])).filter((v) => !Number.isNaN(v));
  if (values.length === 0) return <p style={{ color: "#94a3b8" }}>No data</p>;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const bins = 15;
  const binWidth = (max - min) / bins || 1;

  const counts = Array(bins).fill(0);
  values.forEach((v) => {
    const idx = Math.min(Math.floor((v - min) / binWidth), bins - 1);
    counts[idx]++;
  });
  const maxCount = Math.max(...counts);

  const highIdx = thresholdHigh != null ? Math.floor((thresholdHigh - min) / binWidth) : -1;
  const lowIdx = thresholdLow != null ? Math.floor((thresholdLow - min) / binWidth) : -1;

  return (
    <div>
      <h3>{label}</h3>
      <svg viewBox="0 0 600 200" className="real-chart">
        {counts.map((c, i) => {
          const x = (i / bins) * 580 + 10;
          const w = 580 / bins - 2;
          const h = maxCount > 0 ? (c / maxCount) * 150 : 0;
          let fill = color;
          if (i === highIdx || i === lowIdx) fill = "#ef4444";
          return <rect key={i} x={x} y={180 - h} width={w} height={h} rx="3" fill={fill} opacity="0.8" />;
        })}
        {thresholdHigh != null && highIdx >= 0 && highIdx < bins && (
          <line x1={(highIdx / bins) * 580 + 10 + (580 / bins) / 2} y1="10" x2={(highIdx / bins) * 580 + 10 + (580 / bins) / 2} y2="180" stroke="#ef4444" strokeDasharray="6 4" strokeWidth="2" />
        )}
        {thresholdLow != null && lowIdx >= 0 && lowIdx < bins && (
          <line x1={(lowIdx / bins) * 580 + 10 + (580 / bins) / 2} y1="10" x2={(lowIdx / bins) * 580 + 10 + (580 / bins) / 2} y2="180" stroke="#22c55e" strokeDasharray="6 4" strokeWidth="2" />
        )}
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "Manrope", fontSize: 11, color: "#94a3b8", padding: "0 10px" }}>
        <span>{min.toFixed(1)}{unit}</span>
        <span>Avg: {(values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)}{unit}</span>
        <span>{max.toFixed(1)}{unit}</span>
      </div>
    </div>
  );
}

export default function Reports({ room, history }) {
  const stats = useMemo(() => {
    if (history.length === 0) return null;
    const temps = history.map((h) => Number(h.temperature)).filter((v) => !Number.isNaN(v));
    const hums = history.map((h) => Number(h.humidity)).filter((v) => !Number.isNaN(v));

    const avg = (arr) => arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1) : "--";
    const minVal = (arr) => arr.length ? Math.min(...arr).toFixed(1) : "--";
    const maxVal = (arr) => arr.length ? Math.max(...arr).toFixed(1) : "--";

    return {
      count: history.length,
      tempAvg: avg(temps),
      tempMin: minVal(temps),
      tempMax: maxVal(temps),
      humAvg: avg(hums),
      humMin: minVal(hums),
      humMax: maxVal(hums),
      timeSpan: `${formatTime(history[0]?.timestamp)} → ${formatTime(history[history.length - 1]?.timestamp)}`,
      tempHighCount: temps.filter((t) => t > THRESHOLDS.TEMP_HIGH).length,
      tempLowCount: temps.filter((t) => t < THRESHOLDS.TEMP_LOW).length,
      humHighCount: hums.filter((h) => h > THRESHOLDS.HUMIDITY_HIGH).length,
      humLowCount: hums.filter((h) => h < THRESHOLDS.HUMIDITY_LOW).length,
    };
  }, [history]);

  const downloadCSV = () => {
    if (history.length === 0) return;
    const headers = Object.keys(history[0]).join(",");
    const cell = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v);
    const rows = history.map((r) => Object.values(r).map(cell).join(",")).join("\n");
    const blob = new Blob([headers + "\n" + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "telemetry_report.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadSummary = () => {
    if (!stats) return;
    const totalAlerts = stats.tempHighCount + stats.tempLowCount + stats.humHighCount + stats.humLowCount;
    const text = `Thalpos - Telemetry Report (${room})
Generated: ${new Date().toLocaleString()}

=== SUMMARY ===
Total Records: ${stats.count}
Temperature - Avg: ${stats.tempAvg}°C | Min: ${stats.tempMin}°C | Max: ${stats.tempMax}°C
Humidity    - Avg: ${stats.humAvg}%  | Min: ${stats.humMin}%  | Max: ${stats.humMax}%

=== ALERTS ===
High temperature events (>${THRESHOLDS.TEMP_HIGH}°C): ${stats.tempHighCount}
Low temperature events (<${THRESHOLDS.TEMP_LOW}°C): ${stats.tempLowCount}
High humidity events (>${THRESHOLDS.HUMIDITY_HIGH}%): ${stats.humHighCount}
Low humidity events (<${THRESHOLDS.HUMIDITY_LOW}%): ${stats.humLowCount}
Total alerts: ${totalAlerts}
`;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "telemetry_summary.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (history.length === 0) {
    return (
      <div className="module-page">
        <h1>REPORTS</h1>
        <p className="module-subtitle">TELEMETRY SUMMARY · DISTRIBUTION · EXPORT</p>
        <div className="module-card" style={{ padding: 40, textAlign: "center" }}>
          <p style={{ color: "#94a3b8", fontSize: 18 }}>Waiting for telemetry data...</p>
        </div>
        <StoredExport />
      </div>
    );
  }

  return (
    <div className="module-page">
      <h1>REPORTS</h1>
      <p className="module-subtitle">TELEMETRY SUMMARY · DISTRIBUTION · EXPORT</p>

      {/* Stats Row */}
      <div className="reports-stats-row">
        {[
          { label: "RECORDS", value: stats.count, color: "#22d3ee" },
          { label: "AVG TEMP", value: `${stats.tempAvg}°C`, color: "#f59e0b" },
          { label: "MAX TEMP", value: `${stats.tempMax}°C`, color: "#ef4444" },
          { label: "AVG HUM", value: `${stats.humAvg}%`, color: "#22d3ee" },
          { label: "MAX HUM", value: `${stats.humMax}%`, color: "#ef4444" },
          { label: "TIME SPAN", value: stats.timeSpan, color: "#a855f7" },
        ].map((s) => (
          <div key={s.label} className="module-card small-card">
            <span className="kpi-label">{s.label}</span>
            <h2 className="kpi-value" style={{ color: s.color, fontSize: 18 }}>{s.value}</h2>
          </div>
        ))}
      </div>

      {/* Distribution */}
      <div className="reports-charts-row">
        <div className="module-card">
          <Histogram data={history} field="temperature" color="#f97316"
            thresholdHigh={THRESHOLDS.TEMP_HIGH} thresholdLow={THRESHOLDS.TEMP_LOW}
            label="TEMPERATURE DISTRIBUTION" unit="°C" />
        </div>
        <div className="module-card">
          <Histogram data={history} field="humidity" color="#22d3ee"
            thresholdHigh={THRESHOLDS.HUMIDITY_HIGH} thresholdLow={THRESHOLDS.HUMIDITY_LOW}
            label="HUMIDITY DISTRIBUTION" unit="%" />
        </div>
      </div>

      {/* Alert counts */}
      <div className="module-card" style={{ marginTop: 18 }}>
        <h3>ALERTS IN THIS DATASET</h3>
        <div className="reports-alerts-row">
          {[
            { label: "TOTAL", value: stats.tempHighCount + stats.tempLowCount + stats.humHighCount + stats.humLowCount, color: "#ef4444" },
            { label: "HIGH TEMP", value: stats.tempHighCount, color: "#ef4444" },
            { label: "LOW TEMP", value: stats.tempLowCount, color: "#f59e0b" },
            { label: "HIGH HUM", value: stats.humHighCount, color: "#ef4444" },
            { label: "LOW HUM", value: stats.humLowCount, color: "#f59e0b" },
          ].map((a) => (
            <div key={a.label} className="alert-stat">
              <span className="kpi-label">{a.label}</span>
              <h2 style={{ color: a.color, fontSize: 22 }}>{a.value}×</h2>
            </div>
          ))}
        </div>
      </div>

      {/* Data table */}
      <div className="module-card" style={{ marginTop: 18, overflow: "auto", maxHeight: 400 }}>
        <h3>FULL TELEMETRY — {history.length} RECORDS</h3>
        <table className="data-table">
          <thead>
            <tr>
              {history.length > 0 && Object.keys(history[0]).map((k) => <th key={k}>{k}</th>)}
            </tr>
          </thead>
          <tbody>
            {history.slice(-50).map((row, i) => (
              <tr key={i}>
                {Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Export buttons */}
      <div className="reports-export-row">
        <button className="export-btn" onClick={downloadCSV}>Download recent packets (CSV)</button>
        <button className="export-btn secondary" onClick={downloadSummary}>Download Summary (.txt)</button>
      </div>

      <StoredExport />
    </div>
  );
}
