import { useMemo } from "react";
import { THRESHOLDS } from "../config";

function GaugeSVG({ value, label, color, size = 200 }) {
  const radius = 70;
  const circumference = Math.PI * radius;
  const fill = (value / 100) * circumference;

  return (
    <div className="brain-gauge">
      <svg viewBox="0 0 200 130" width={size}>
        <path d="M20 110 A70 70 0 0 1 180 110" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" strokeLinecap="round" />
        <path d="M20 110 A70 70 0 0 1 180 110" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={`${fill} ${circumference}`} style={{ transition: "stroke-dasharray 0.8s ease" }} />
        <text x="100" y="95" textAnchor="middle" fill={color} fontFamily="Oxanium" fontSize="30" fontWeight="900">{value}</text>
        <text x="100" y="118" textAnchor="middle" fill="#94a3b8" fontFamily="Manrope" fontSize="10">{label}</text>
      </svg>
    </div>
  );
}

function RadarSVG({ values, labels, size = 300 }) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.38;
  const n = labels.length;

  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  const getPoint = (i, val) => {
    const angle = startAngle + i * angleStep;
    const dist = (val / 100) * r;
    return [cx + dist * Math.cos(angle), cy + dist * Math.sin(angle)];
  };

  const gridLevels = [25, 50, 75, 100];
  const dataPoints = values.map((v, i) => getPoint(i, v).join(",")).join(" ");

  return (
    <div className="brain-radar">
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
        {gridLevels.map((level) => {
          const pts = labels.map((_, i) => getPoint(i, level).join(",")).join(" ");
          return <polygon key={level} points={pts} fill="none" stroke="rgba(0,212,255,0.1)" strokeWidth="1" />;
        })}
        {labels.map((_, i) => {
          const [x, y] = getPoint(i, 100);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(0,212,255,0.08)" strokeWidth="1" />;
        })}
        <polygon points={dataPoints} fill="rgba(0,212,255,0.12)" stroke="#22d3ee" strokeWidth="2" />
        {values.map((v, i) => {
          const [x, y] = getPoint(i, v);
          return <circle key={i} cx={x} cy={y} r="4" fill="#22d3ee" />;
        })}
        {labels.map((label, i) => {
          const [x, y] = getPoint(i, 115);
          return (
            <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
              fill="#94a3b8" fontFamily="Manrope" fontSize="10">{label}</text>
          );
        })}
      </svg>
    </div>
  );
}

function BarMetric({ name, value, color }) {
  return (
    <div className="brain-metric-row">
      <span className="metric-name">{name}</span>
      <div className="metric-bar">
        <div className="metric-bar-fill" style={{ width: `${Math.min(100, Math.max(0, value))}%`, background: color }} />
      </div>
      <span className="metric-val" style={{ color }}>{value}</span>
    </div>
  );
}

export default function AIBrain({ temp, humidity, health: healthScore, history }) {
  // health is null until the first reading; gauges use 0, labels show "--"
  const health = healthScore ?? 0;
  const healthLabel = healthScore ?? "--";
  const analysis = useMemo(() => {
    const tempF = parseFloat(temp) || 22;
    const humF = parseFloat(humidity) || 50;
    const tempDelta = Math.abs(tempF - 22);
    const humDelta = Math.abs(humF - 55);

    // Derived scores
    const tempStability = Math.max(0, Math.min(100, 100 - tempDelta * 12));
    const humidityComfort = Math.max(0, Math.min(100, 100 - Math.max(0, humF - 60) * 3 - Math.max(0, 40 - humF) * 3));
    const comfortIndex = Math.max(0, Math.min(100, 100 - tempDelta * 8 - humDelta * 2));

    // Anomaly detection
    const anomalyScore = Math.max(0, Math.min(100, tempDelta * 10 + (humF > THRESHOLDS.HUMIDITY_HIGH ? (humF - THRESHOLDS.HUMIDITY_HIGH) * 5 : 0)));
    const isAnomaly = anomalyScore > 30;

    // Trend analysis from history
    let trend = "STABLE";
    if (history.length > 5) {
      const recent = history.slice(-5).map((h) => Number(h.temperature));
      const older = history.slice(-10, -5).map((h) => Number(h.temperature));
      if (recent.length && older.length) {
        const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
        const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
        if (recentAvg - olderAvg > 0.5) trend = "RISING";
        else if (olderAvg - recentAvg > 0.5) trend = "FALLING";
      }
    }

    // Predictions
    const predictedHealth = Math.max(0, Math.min(100, health + (trend === "RISING" ? -3 : trend === "FALLING" ? 3 : 0)));
    const riskLevel = healthScore == null ? "--" : health >= 80 ? "LOW" : health >= 60 ? "MEDIUM" : "HIGH";

    return {
      tempStability: tempStability.toFixed(0),
      humidityComfort: humidityComfort.toFixed(0),
      comfortIndex: comfortIndex.toFixed(0),
      anomalyScore: anomalyScore.toFixed(0),
      isAnomaly,
      trend,
      predictedHealth: predictedHealth.toFixed(0),
      riskLevel,
      radarValues: [health, tempStability, humidityComfort, comfortIndex],
      radarLabels: ["Health", "Temp", "Humidity", "Comfort"],
    };
  }, [temp, humidity, health, healthScore, history]);

  const healthColor = health >= 80 ? "#22c55e" : health >= 60 ? "#f59e0b" : "#ef4444";
  const anomalyColor = analysis.anomalyScore > 30 ? "#ef4444" : analysis.anomalyScore > 15 ? "#f59e0b" : "#22c55e";

  return (
    <div className="module-page">
      <h1>AI BRAIN</h1>
      <p className="module-subtitle">RULE-BASED COMFORT ANALYSIS · HEALTH SCORE · DEVIATION CHECK</p>

      {/* KPI Row */}
      <div className="brain-kpi-row">
        {[
          { label: "HEALTH SCORE", value: `${healthLabel}/100`, color: healthColor },
          { label: "DEVIATION", value: analysis.isAnomaly ? "DETECTED" : "NONE", color: analysis.isAnomaly ? "#ef4444" : "#22c55e" },
          { label: "TREND", value: analysis.trend, color: analysis.trend === "STABLE" ? "#22d3ee" : analysis.trend === "RISING" ? "#ef4444" : "#22c55e" },
          { label: "RISK", value: analysis.riskLevel, color: analysis.riskLevel === "LOW" ? "#22c55e" : analysis.riskLevel === "MEDIUM" ? "#f59e0b" : "#ef4444" },
        ].map((k) => (
          <div key={k.label} className="module-card">
            <span className="kpi-label">{k.label}</span>
            <h2 className="kpi-value" style={{ color: k.color, fontSize: 20 }}>{k.value}</h2>
          </div>
        ))}
      </div>

      {/* Gauge + Metrics */}
      <div className="brain-grid">
        <div className="module-card">
          <h3>HEALTH INDEX</h3>
          <GaugeSVG value={health} label="HEALTH SCORE" color={healthColor} />
        </div>

        <div className="module-card">
          <h3>COMFORT METRICS</h3>
          <div className="brain-metrics">
            <BarMetric name="Health Score" value={health} color={healthColor} />
            <BarMetric name="Temp Stability" value={analysis.tempStability} color="#f59e0b" />
            <BarMetric name="Humidity Comfort" value={analysis.humidityComfort} color="#22d3ee" />
            <BarMetric name="Comfort Index" value={analysis.comfortIndex} color="#22c55e" />
            <BarMetric name="Deviation Score" value={analysis.anomalyScore} color={anomalyColor} />
          </div>
        </div>
      </div>

      {/* Radar + Analysis */}
      <div className="brain-grid">
        <div className="module-card">
          <h3>COMFORT RADAR</h3>
          <RadarSVG values={analysis.radarValues} labels={analysis.radarLabels} />
        </div>

        <div className="module-card">
          <h3>ANALYSIS LOG</h3>
          <div className="brain-log">
            <div className="log-line log-info">▶ RULE ENGINE</div>
            <div className="log-line">─────────────────────────</div>
            <div className="log-line log-ok">[HEALTH]   Score: {healthLabel}/100</div>
            <div className="log-line log-ok">[STATUS]   {healthScore == null ? "WAITING FOR DATA" : health >= 80 ? "OPTIMAL — All systems normal" : health >= 60 ? "ATTENTION — Minor adjustments needed" : "CRITICAL — Action required"}</div>
            <div className="log-line">─────────────────────────</div>
            <div className="log-line log-info">▶ ENVIRONMENT ANALYSIS</div>
            <div className="log-line">[TEMP]     {temp}°C — Stability: {analysis.tempStability}%</div>
            <div className="log-line">[HUMIDITY] {humidity}% — Comfort: {analysis.humidityComfort}%</div>
            <div className="log-line">[COMFORT]  Index: {analysis.comfortIndex}%</div>
            <div className="log-line">─────────────────────────</div>
            <div className="log-line log-info">▶ DEVIATION CHECK (vs 22°C / 55%)</div>
            <div className={`log-line ${analysis.isAnomaly ? "log-err" : "log-ok"}`}>
              [SCORE]    {analysis.anomalyScore}/100 {analysis.isAnomaly ? "— DEVIATION DETECTED" : "— Within normal range"}
            </div>
            <div className="log-line">─────────────────────────</div>
            <div className="log-line log-info">▶ PREDICTION</div>
            <div className="log-line">[TREND]    {analysis.trend}</div>
            <div className="log-line">[PREDICT]  Next health: {analysis.predictedHealth}/100</div>
            <div className="log-line">[RISK]     {analysis.riskLevel}</div>
            <div className="log-line">─────────────────────────</div>
            <div className="log-line log-ok">▶ ENGINE ACTIVE — Monitoring</div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="module-card">
        <h3>AI CAPABILITIES</h3>
        <div className="brain-features">
          {[
            { icon: "🧠", label: "HEALTH SCORING", status: "Active — real-time" },
            { icon: "📈", label: "TREND DETECTION", status: "Active — analyzing history" },
            { icon: "⚠️", label: "DEVIATION CHECK", status: "Active — rule-based" },
            { icon: "🔮", label: "PREDICTION", status: "See Predictions page" },
            { icon: "🌡️", label: "COMFORT INDEX", status: "Active — temp + humidity" },
            { icon: "💧", label: "HUMIDITY COMFORT", status: "Active — humidity band" },
          ].map((f) => (
            <div key={f.label} className="brain-feature">
              <div className="feature-icon">{f.icon}</div>
              <div className="feature-label">{f.label}</div>
              <div className="feature-status">{f.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
