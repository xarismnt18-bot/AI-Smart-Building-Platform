import { useEffect, useState } from "react";
import { apiGet } from "../config";

function TrendArrow({ trend }) {
  if (trend === "rising") return <span style={{ color: "#ef4444" }}>↗ RISING</span>;
  if (trend === "falling") return <span style={{ color: "#22c55e" }}>↘ FALLING</span>;
  return <span style={{ color: "#22d3ee" }}>→ STABLE</span>;
}

function RiskBadge({ risk }) {
  const styles = {
    critical: { bg: "rgba(239,68,68,0.15)", border: "#ef4444", color: "#ef4444" },
    warning: { bg: "rgba(245,158,11,0.15)", border: "#f59e0b", color: "#f59e0b" },
    normal: { bg: "rgba(34,197,94,0.15)", border: "#22c55e", color: "#22c55e" },
    unknown: { bg: "rgba(148,163,184,0.15)", border: "#94a3b8", color: "#94a3b8" },
  };
  const s = styles[risk] || styles.unknown;
  return (
    <span style={{
      display: "inline-block", padding: "4px 12px", borderRadius: 20,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
      fontFamily: "Oxanium", fontSize: 10, fontWeight: 700, letterSpacing: 1,
    }}>
      {(risk || "unknown").toUpperCase()}
    </span>
  );
}

function PredictionCard({ label, current, predicted, confidence, trend, risk, unit, icon, minutes }) {
  const riskColor = risk === "critical" ? "#ef4444" : risk === "warning" ? "#f59e0b" : "#22c55e";
  const trendColor = trend === "rising" ? "#ef4444" : trend === "falling" ? "#22c55e" : "#22d3ee";

  return (
    <div className="module-card pred-card">
      <div className="pred-header">
        <span className="pred-icon">{icon}</span>
        <span className="kpi-label">{label}</span>
        <RiskBadge risk={risk} />
      </div>

      <div className="pred-values">
        <div className="pred-current">
          <span className="pred-label">NOW</span>
          <span className="pred-num" style={{ color: "#22d3ee" }}>{current != null ? `${current}${unit}` : "--"}</span>
        </div>
        <div className="pred-arrow">→</div>
        <div className="pred-future">
          <span className="pred-label">IN {minutes} MIN</span>
          <span className="pred-num" style={{ color: riskColor }}>{predicted != null ? `${predicted}${unit}` : "--"}</span>
        </div>
      </div>

      <div className="pred-details">
        <div className="pred-detail">
          <span>TREND</span>
          <TrendArrow trend={trend} />
        </div>
        <div className="pred-detail">
          <span>CONFIDENCE</span>
          <span style={{ color: confidence > 70 ? "#22c55e" : confidence > 40 ? "#f59e0b" : "#ef4444" }}>
            {confidence}%
          </span>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="pred-conf-bar">
        <div className="pred-conf-fill" style={{ width: `${confidence}%`, background: trendColor }} />
      </div>
    </div>
  );
}

export default function Predictions() {
  const [preds, setPreds] = useState(null);
  const [recs, setRecs] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const [p, r] = await Promise.all([apiGet("/predictions"), apiGet("/recommendations")]);
        setPreds(p);
        setRecs(r.recommendations || []);
      } catch (e) {
        console.log("Prediction API offline:", e);
      }
    }
    load();
    const iv = setInterval(load, 5000);
    return () => clearInterval(iv);
  }, []);

  const tp = preds?.temperature || {};
  const hp = preds?.humidity || {};

  return (
    <div className="module-page">
      <h1>PREDICTIONS</h1>
      <p className="module-subtitle">10-MINUTE FORECASTS · TREND ANALYSIS · SMART RECOMMENDATIONS</p>

      {/* Prediction Cards */}
      <div className="pred-grid">
        <PredictionCard
          label="TEMPERATURE" icon="🌡️" unit="°C"
          current={tp.current} predicted={tp.predicted}
          confidence={tp.confidence || 0} trend={tp.trend} risk={tp.risk}
          minutes={preds?.minutes_ahead || 10}
        />
        <PredictionCard
          label="HUMIDITY" icon="💧" unit="%"
          current={hp.current} predicted={hp.predicted}
          confidence={hp.confidence || 0} trend={hp.trend} risk={hp.risk}
          minutes={preds?.minutes_ahead || 10}
        />
      </div>

      {/* Summary */}
      <div className="module-card" style={{ marginTop: 18, padding: "14px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <span className="kpi-label">FORECAST WINDOW</span>
            <span style={{ fontFamily: "Oxanium", fontSize: 16, color: "#22d3ee" }}>{preds?.minutes_ahead || 10} minutes</span>
          </div>
          <div>
            <span className="kpi-label">DATA POINTS</span>
            <span style={{ fontFamily: "Oxanium", fontSize: 16, color: "#a855f7" }}>{preds?.data_points || 0}</span>
          </div>
          <div>
            <span className="kpi-label">MODEL</span>
            <span style={{ fontFamily: "Oxanium", fontSize: 16, color: "#22c55e" }}>Weighted Linear Regression</span>
          </div>
          <div>
            <span className="kpi-label">STATUS</span>
            <span style={{ fontFamily: "Oxanium", fontSize: 16, color: preds ? "#22c55e" : "#ef4444" }}>{preds ? "ACTIVE" : "API OFFLINE"}</span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="module-card" style={{ marginTop: 18 }}>
        <h3>SMART RECOMMENDATIONS</h3>
        {recs.length === 0 ? (
          <p style={{ color: "#94a3b8" }}>Waiting for data...</p>
        ) : (
          <div className="rec-list">
            {recs.map((r, i) => {
              const colors = { critical: "#ef4444", warning: "#f59e0b", info: "#22d3ee", success: "#22c55e" };
              const c = colors[r.priority] || "#94a3b8";
              return (
                <div key={i} className="rec-row" style={{ borderLeftColor: c }}>
                  <div className="rec-top">
                    <span className="rec-title" style={{ color: c }}>{r.title}</span>
                    <RiskBadge risk={r.priority === "success" ? "normal" : r.priority} />
                  </div>
                  <p className="rec-msg">{r.message}</p>
                  <span className="rec-action">→ {r.action}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="module-card" style={{ marginTop: 18 }}>
        <h3>HOW PREDICTIONS WORK</h3>
        <div className="pred-how-grid">
          {[
            { step: "1", title: "COLLECT", desc: "ESP8266 sends temperature & humidity via MQTT every few seconds" },
            { step: "2", title: "ANALYZE", desc: "Weighted linear regression over the last 20 minutes, fitted on real timestamps, recent data weighted higher" },
            { step: "3", title: "PREDICT", desc: "Extrapolate ahead; confidence shrinks with fit error and with how far beyond the data we project" },
            { step: "4", title: "RECOMMEND", desc: "Rule engine compares predictions against thresholds to generate smart actions" },
          ].map((s) => (
            <div key={s.step} className="pred-how-step">
              <div className="pred-how-num">{s.step}</div>
              <div className="pred-how-title">{s.title}</div>
              <div className="pred-how-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
