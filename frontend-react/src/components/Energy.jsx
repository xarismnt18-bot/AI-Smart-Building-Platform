import { useMemo } from "react";
import { THRESHOLDS } from "../config";

function MiniChart({ data, field, color }) {
  const values = data.map((d) => Number(d[field])).filter((v) => !Number.isNaN(v));
  const safe = values.length > 1 ? values.slice(-50) : [0, 0];
  const min = Math.min(...safe);
  const max = Math.max(...safe);
  const range = max - min || 1;
  const points = safe.map((v, i) => `${(i / (safe.length - 1)) * 600},${170 - ((v - min) / range) * 130}`).join(" ");
  const lastY = 170 - ((safe[safe.length - 1] - min) / range) * 130;

  return (
    <svg className="real-chart" viewBox="0 0 600 190">
      <polyline points={points} fill="none" stroke={color} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="600" cy={lastY} r="6" fill={color} />
    </svg>
  );
}

// Typical single-room loads (kW). There is no power meter yet, so every
// number on this page is a model estimate, not a measurement.
const TEMP_OPTIMAL = 22.0;
const EQUIPMENT_KW = 0.12;
const LIGHTING_KW = { day: 0.06, evening: 0.04, night: 0.01 };
const HVAC_BASE_KW = 0.15;
const HVAC_MAX_KW = 1.8;
const BAR_SCALE_KW = 2;

function estimateHvacKw(temp, hum) {
  let kw = HVAC_BASE_KW + Math.abs(temp - TEMP_OPTIMAL) * 0.12;
  if (hum > THRESHOLDS.HUMIDITY_HIGH) kw += (hum - THRESHOLDS.HUMIDITY_HIGH) * 0.02;
  return Math.max(0.1, Math.min(kw, HVAC_MAX_KW));
}

function lightingKwAt(hour) {
  if (hour >= 8 && hour <= 18) return LIGHTING_KW.day;
  if ((hour >= 6 && hour < 8) || (hour > 18 && hour <= 22)) return LIGHTING_KW.evening;
  return LIGHTING_KW.night;
}

export default function Energy({ temp, humidity, history }) {
  const tempF = parseFloat(temp) || 22;
  const humF = parseFloat(humidity) || 50;
  const hour = new Date().getHours();

  const calc = useMemo(() => {
    const hvacKw = estimateHvacKw(tempF, humF);
    const lightingKw = lightingKwAt(hour);
    const equipmentKw = EQUIPMENT_KW;
    const totalKw = hvacKw + lightingKw + equipmentKw;
    const optimalTotal = HVAC_BASE_KW + lightingKw + EQUIPMENT_KW;
    const efficiency = Math.max(0, Math.min(100, (optimalTotal / Math.max(totalKw, 1)) * 100));
    const dailyKwh = totalKw * 18;

    return {
      hvacKw: hvacKw.toFixed(2),
      lightingKw: lightingKw.toFixed(2),
      equipmentKw: equipmentKw.toFixed(2),
      totalKw: totalKw.toFixed(2),
      efficiency: efficiency.toFixed(1),
      dailyKwh: dailyKwh.toFixed(1),
      hvacPct: ((hvacKw / totalKw) * 100).toFixed(0),
      lightingPct: ((lightingKw / totalKw) * 100).toFixed(0),
      equipmentPct: ((equipmentKw / totalKw) * 100).toFixed(0),
    };
  }, [tempF, humF, hour]);

  const recs = useMemo(() => {
    const r = [];
    const tempDelta = Math.abs(tempF - 22);
    if (tempDelta > 3) r.push(`Temperature is ${tempDelta.toFixed(1)}°C from optimal. HVAC is working hard — check insulation or adjust thermostat.`);
    if (humF > THRESHOLDS.HUMIDITY_HIGH) r.push(`Humidity at ${humF}% exceeds ${THRESHOLDS.HUMIDITY_HIGH}%. Dehumidifier load increasing energy draw.`);
    if (humF < THRESHOLDS.HUMIDITY_LOW) r.push(`Low humidity (${humF}%). Consider humidifier to reduce dry-air energy waste.`);
    if (hour >= 22 || hour < 6) r.push("Off-peak hours: consider reducing HVAC and lighting to save energy.");
    else if (hour >= 8 && hour <= 18) r.push("Peak occupancy hours. HVAC and lighting at working-level consumption.");
    if (r.length === 0) r.push("System operating near optimal efficiency. No action needed.");
    return r;
  }, [tempF, humF, hour]);

  const effColor = calc.efficiency >= 80 ? "#22c55e" : calc.efficiency >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="module-page">
      <h1>ENERGY</h1>
      <p className="module-subtitle">ESTIMATED POWER · EFFICIENCY · OPTIMIZATION TIPS</p>

      <div className="sim-banner">
        SIMULATED ESTIMATE: no power meter is connected. Values are modelled from temperature,
        humidity and time of day using typical single-room loads, not measured.
      </div>

      {/* KPI Row */}
      <div className="energy-kpi-row">
        <div className="module-card">
          <span className="kpi-label">TOTAL DRAW</span>
          <h2 className="kpi-value cyan">{calc.totalKw} kW</h2>
          <small>Model estimate</small>
        </div>
        <div className="module-card">
          <span className="kpi-label">HVAC LOAD</span>
          <h2 className="kpi-value cyan">{calc.hvacKw} kW</h2>
          <small>{calc.hvacPct}% of total</small>
        </div>
        <div className="module-card">
          <span className="kpi-label">EFFICIENCY</span>
          <h2 className="kpi-value" style={{ color: effColor }}>{calc.efficiency}%</h2>
          <small>vs optimal baseline</small>
        </div>
        <div className="module-card">
          <span className="kpi-label">DAILY EST.</span>
          <h2 className="kpi-value purple">{calc.dailyKwh} kWh</h2>
          <small>18h active assumption</small>
        </div>
      </div>

      {/* Charts Row */}
      <div className="energy-charts-row">
        <div className="module-card">
          <h3>POWER DISTRIBUTION</h3>
          <div className="energy-donut">
            <div className="donut-bar" style={{ background: `conic-gradient(#00d4ff 0% ${calc.hvacPct}%, #22c55e ${calc.hvacPct}% ${Number(calc.hvacPct) + Number(calc.lightingPct)}%, #a855f7 ${Number(calc.hvacPct) + Number(calc.lightingPct)}% 100%)` }}>
              <div className="donut-hole">
                <span className="donut-total">{calc.totalKw}</span>
                <span className="donut-unit">kW</span>
              </div>
            </div>
            <div className="donut-legend">
              <div><span style={{ background: "#00d4ff" }} />HVAC {calc.hvacKw} kW ({calc.hvacPct}%)</div>
              <div><span style={{ background: "#22c55e" }} />Lighting {calc.lightingKw} kW ({calc.lightingPct}%)</div>
              <div><span style={{ background: "#a855f7" }} />Equipment {calc.equipmentKw} kW ({calc.equipmentPct}%)</div>
            </div>
          </div>
        </div>

        <div className="module-card">
          <h3>POWER BY SYSTEM</h3>
          <div className="energy-bars">
            {[
              { label: "HVAC", value: parseFloat(calc.hvacKw), color: "#00d4ff" },
              { label: "Lighting", value: parseFloat(calc.lightingKw), color: "#22c55e" },
              { label: "Equipment", value: parseFloat(calc.equipmentKw), color: "#a855f7" },
            ].map((bar) => (
              <div key={bar.label} className="bar-row">
                <span className="bar-label">{bar.label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${Math.min(100, (bar.value / BAR_SCALE_KW) * 100)}%`, background: bar.color }} />
                </div>
                <span className="bar-val" style={{ color: bar.color }}>{bar.value} kW</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Efficiency gauge + recommendations */}
      <div className="energy-bottom-row">
        <div className="module-card">
          <h3>ENERGY EFFICIENCY</h3>
          <div className="gauge-container">
            <svg viewBox="0 0 200 120" className="gauge-svg">
              <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="16" strokeLinecap="round" />
              <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke={effColor} strokeWidth="16" strokeLinecap="round"
                strokeDasharray={`${(calc.efficiency / 100) * 251} 251`} />
              <text x="100" y="85" textAnchor="middle" fill={effColor} fontFamily="Oxanium" fontSize="28" fontWeight="900">{calc.efficiency}%</text>
              <text x="100" y="108" textAnchor="middle" fill="#94a3b8" fontFamily="Manrope" fontSize="10">EFFICIENCY</text>
            </svg>
          </div>
        </div>

        <div className="module-card recommendations">
          <h3>ENERGY TIPS</h3>
          {recs.map((r, i) => (
            <div key={i} className="rec-item">{r}</div>
          ))}
        </div>
      </div>

      {/* Consumption trend */}
      {history.length > 2 && (
        <div className="module-card" style={{ marginTop: 18 }}>
          <h3>ESTIMATED CONSUMPTION TREND</h3>
          <MiniChart
            data={history.map((h) => ({
              ...h,
              total_kw: estimateHvacKw(Number(h.temperature), Number(h.humidity)) + parseFloat(calc.lightingKw) + EQUIPMENT_KW,
            }))}
            field="total_kw"
            color="#00d4ff"
          />
        </div>
      )}
    </div>
  );
}
