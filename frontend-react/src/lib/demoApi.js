// In-browser stand-in for the FastAPI backend, used by the public demo build
// (VITE_DEMO=1). It mirrors the backend's responses and maths closely enough
// for every page to work, with a simulated DHT11 sending a packet every 3 s.
// Humidity drifts slowly, so visitors see the room in alert and then recover.

const PACKET_MS = 3000;
const HISTORY_MAX = 500;
const DEFAULT_THRESHOLDS = {
  TEMP_LOW: 18, TEMP_HIGH: 27, TEMP_CRITICAL: 32,
  HUMIDITY_LOW: 35, HUMIDITY_HIGH: 70, HUMIDITY_CRITICAL: 85,
};

let thresholds = { ...DEFAULT_THRESHOLDS };
const history = [];
const startedAt = Date.now();

function reading(atMs) {
  const t = (atMs - startedAt) / 1000;
  const noise = () => (Math.random() - 0.5);
  return {
    // visit starts with humidity just over the limit (red room), easing back
    // below it after ~7 minutes; slow waves so the 20-minute forecast makes sense
    temperature: +(24.2 + 1.4 * Math.sin(t / 900 + 0.4) + 0.15 * noise()).toFixed(1),
    humidity: +(66 + 7 * Math.sin(t / 300 + 1.2) + 0.5 * noise()).toFixed(1),
  };
}

function push(atMs) {
  const r = reading(atMs);
  history.push({ room: "Bedroom", ...r, timestamp: new Date(atMs).toISOString(), ts: atMs / 1000 });
  if (history.length > HISTORY_MAX) history.shift();
}

// back-fill 25 minutes so charts and forecasts have data straight away
for (let i = HISTORY_MAX - 1; i >= 0; i--) push(startedAt - i * PACKET_MS);
setInterval(() => push(Date.now()), PACKET_MS);

const last = () => history[history.length - 1];

// ---- same formulas as ai/engines/comfort.py ----
function healthScore(temp, hum, t) {
  let score = 100;
  if (temp > t.TEMP_HIGH) score -= Math.min((temp - t.TEMP_HIGH) * 8, 35);
  if (temp < t.TEMP_LOW) score -= Math.min((t.TEMP_LOW - temp) * 6, 30);
  if (hum > t.HUMIDITY_HIGH) score -= Math.min((hum - t.HUMIDITY_HIGH) * 4, 35);
  if (hum < t.HUMIDITY_LOW) score -= Math.min((t.HUMIDITY_LOW - hum) * 2, 20);
  return Math.max(Math.trunc(score), 20);
}
const healthStatus = (s) => (s >= 80 ? "OPTIMAL" : s >= 60 ? "ATTENTION_REQUIRED" : "CRITICAL");
function dewPoint(temp, hum) {
  const a = 17.62, b = 243.12;
  const g = Math.log(Math.max(hum, 1) / 100) + (a * temp) / (b + temp);
  return Math.round(((b * g) / (a - g)) * 10) / 10;
}
function moldRisk(temp, hum) {
  if (temp < 18) return hum < 70 ? "low" : "moderate";
  if (hum >= 70) return "high";
  if (hum >= 60) return "moderate";
  return "low";
}

function alerts(r) {
  const t = thresholds;
  const out = [];
  if (r.temperature > t.TEMP_HIGH) out.push("Temperature is above comfort threshold.");
  if (r.temperature < t.TEMP_LOW) out.push("Temperature is below comfort threshold.");
  if (r.humidity > t.HUMIDITY_HIGH) out.push("Humidity is above comfort threshold. Mold risk may increase.");
  if (r.humidity < t.HUMIDITY_LOW) out.push("Humidity is low. Dry-air conditions detected.");
  return out;
}

// ---- forecast: weighted linear regression over the last 20 minutes ----
function forecast(field, warn, crit) {
  const now = last().ts;
  const pts = history.filter((p) => p.ts >= now - 20 * 60);
  const n = pts.length;
  const current = last()[field];
  if (n < 5) return { current, predicted: null, confidence: 0, trend: "unknown", risk: "unknown", data_points: n };
  const xs = pts.map((p) => p.ts - now);
  const ys = pts.map((p) => p[field]);
  const ws = xs.map((_, i) => 0.5 + i / n);
  const sw = ws.reduce((a, b) => a + b, 0);
  const mx = xs.reduce((a, x, i) => a + x * ws[i], 0) / sw;
  const my = ys.reduce((a, y, i) => a + y * ws[i], 0) / sw;
  const sxx = xs.reduce((a, x, i) => a + ws[i] * (x - mx) ** 2, 0);
  const sxy = xs.reduce((a, x, i) => a + ws[i] * (x - mx) * (ys[i] - my), 0);
  const slope = sxy / (sxx || 1);
  const predicted = my + slope * (600 - mx);
  const resid = Math.sqrt(ys.reduce((a, y, i) => a + ws[i] * (y - (my + slope * (xs[i] - mx))) ** 2, 0) / sw);
  const perMin = slope * 60;
  const limit = field === "temperature" ? 0.02 : 0.05;
  const risk = predicted >= crit ? "critical" : predicted >= warn ? "warning" : "normal";
  return {
    current,
    predicted: Math.round(predicted * 10) / 10,
    confidence: Math.max(10, Math.min(95, Math.round(95 - resid * 40))),
    trend: perMin > limit ? "rising" : perMin < -limit ? "falling" : "stable",
    risk,
    slope_per_min: Math.round(perMin * 1000) / 1000,
    data_points: n,
  };
}

function predictions() {
  const t = thresholds;
  const temperature = forecast("temperature", t.TEMP_HIGH, t.TEMP_CRITICAL);
  const humidity = forecast("humidity", t.HUMIDITY_HIGH, t.HUMIDITY_CRITICAL);
  return { temperature, humidity, minutes_ahead: 10, data_points: Math.max(temperature.data_points, humidity.data_points) };
}

function recommendations() {
  const r = last();
  const t = thresholds;
  const p = predictions();
  const recs = [];
  const rec = (priority, title, message, action) => recs.push({ priority, title, message, action });
  if (r.temperature > t.TEMP_HIGH) rec("warning", "Temperature High", `Current ${r.temperature}°C exceeds ${t.TEMP_HIGH}°C.`, "Open a window or switch on the AC.");
  else if (p.temperature.risk !== "normal" && p.temperature.risk !== "unknown") rec("info", "Temperature Rising", `Forecast ${p.temperature.predicted}°C in 10 min.`, "Plan to cool the room.");
  if (r.humidity > t.HUMIDITY_HIGH) rec("warning", "High Humidity", `Humidity ${r.humidity}% exceeds ${t.HUMIDITY_HIGH}%.`, "Ventilate or run a dehumidifier.");
  else if (p.humidity.risk !== "normal" && p.humidity.risk !== "unknown") rec("info", "Humidity Rising", `Forecast ${p.humidity.predicted}% in 10 min.`, "Ventilate before it crosses the limit.");
  const mold = moldRisk(r.temperature, r.humidity);
  if (mold === "high") rec("warning", "Mold Risk High", "Warm and humid: conditions favour mold.", "Keep humidity under 60%.");
  else if (mold === "moderate") rec("info", "Mold Risk Moderate", "Humidity is getting close to mold-friendly levels.", "Air the room for a few minutes.");
  if (recs.length === 0) rec("success", "Optimal Conditions", "Everything is inside the comfort range.", "No action needed.");
  return recs.slice(0, 5);
}

function latest() {
  const r = last();
  return {
    room: "Bedroom",
    temperature: r.temperature,
    humidity: r.humidity,
    last_update: r.timestamp,
    seconds_since_update: Math.round((Date.now() - r.ts * 1000) / 100) / 10,
    broker_connected: true,
    sensor_online: true,
    connected: true,
    invalid_packets: 0,
  };
}

const config = () => ({ thresholds: { ...thresholds }, mqtt_topic: "smartroom/dht11" });

/** Same contract as config.js request(): resolves to JSON or throws Error(detail). */
export async function demoRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const route = path.split("?")[0];
  const r = last();

  if (route === "/latest") return latest();
  if (route === "/history") return history.slice();
  if (route === "/health") {
    const score = healthScore(r.temperature, r.humidity, thresholds);
    return {
      status: healthStatus(score), health_score: score,
      temperature: r.temperature, humidity: r.humidity,
      dew_point: dewPoint(r.temperature, r.humidity), mold_risk: moldRisk(r.temperature, r.humidity),
      sensor_online: true,
    };
  }
  if (route === "/alerts") {
    const list = alerts(r);
    return { alerts: list.length ? list : ["No active alerts."] };
  }
  if (route === "/predictions") return predictions();
  if (route === "/recommendations") return { recommendations: recommendations() };
  if (route === "/config") {
    if (method === "PUT") thresholds = { ...thresholds, ...JSON.parse(options.body || "{}") };
    if (method === "DELETE") thresholds = { ...DEFAULT_THRESHOLDS };
    return config();
  }
  if (route === "/notifications") return { telegram_enabled: false, muted_until: null };
  if (route === "/notifications/test") throw new Error("Telegram isn't available in the online demo.");
  throw new Error(`Not available in the demo: ${route}`);
}
