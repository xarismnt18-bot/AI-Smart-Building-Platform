import { useEffect, useState } from "react";
import {
  CLIENT, SERVER, THRESHOLDS,
  getClientSettings, saveClientSettings, resetClientSettings,
  loadServerConfig, saveThresholds, resetThresholds,
} from "../config";
import TelegramCard from "./TelegramCard";

const THRESHOLD_FIELDS = [
  { key: "TEMP_LOW", label: "Temperature Low (°C)", color: "#f59e0b", min: -10, max: 50, step: 0.5 },
  { key: "TEMP_HIGH", label: "Temperature High (°C)", color: "#ef4444", min: -10, max: 50, step: 0.5 },
  { key: "TEMP_CRITICAL", label: "Temperature Critical (°C)", color: "#ef4444", min: -10, max: 60, step: 0.5 },
  { key: "HUMIDITY_LOW", label: "Humidity Low (%)", color: "#f59e0b", min: 0, max: 100, step: 1 },
  { key: "HUMIDITY_HIGH", label: "Humidity High (%)", color: "#ef4444", min: 0, max: 100, step: 1 },
  { key: "HUMIDITY_CRITICAL", label: "Humidity Critical (%)", color: "#ef4444", min: 0, max: 100, step: 1 },
];

const pickThresholds = () => Object.fromEntries(THRESHOLD_FIELDS.map(({ key }) => [key, THRESHOLDS[key]]));

function StatusCard({ label, ok, okText = "ONLINE", badText = "OFFLINE" }) {
  return (
    <div className="module-card">
      <span className="kpi-label">{label}</span>
      <h2 className="kpi-value" style={{ color: ok ? "#22c55e" : "#ef4444", fontSize: 18 }}>{ok ? okText : badText}</h2>
    </div>
  );
}

export default function Settings({ temp, humidity, health, lastUpdate, status, onConfigChange }) {
  const [client, setClient] = useState(getClientSettings);
  const [thresholds, setThresholds] = useState(pickThresholds);
  const [message, setMessage] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadServerConfig()
      .then(() => { setThresholds(pickThresholds()); onConfigChange(); })
      .catch(() => setMessage({ ok: false, text: "Backend unreachable: thresholds shown are defaults." }));
  }, [onConfigChange]);

  const updateClient = (key, value) => setClient((prev) => ({ ...prev, [key]: value }));
  const updateThreshold = (key, value) => setThresholds((prev) => ({ ...prev, [key]: value }));

  const saveAll = async () => {
    setSaving(true);
    setMessage(null);
    const needsReload = client.API_URL !== CLIENT.API_URL || Number(client.REFRESH_INTERVAL) !== Number(CLIENT.REFRESH_INTERVAL);
    try {
      await saveThresholds(thresholds);
      saveClientSettings(client);
      onConfigChange();
      if (needsReload) {
        window.location.reload();
        return;
      }
      setMessage({ ok: true, text: "Saved. Backend alerts and predictions now use these thresholds." });
    } catch (e) {
      setMessage({ ok: false, text: `Not saved: ${e.message}` });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Reset all settings to defaults?")) return;
    resetClientSettings();
    setClient(getClientSettings());
    try {
      await resetThresholds();
      setThresholds(pickThresholds());
      setMessage({ ok: true, text: "Settings reset to defaults." });
    } catch (e) {
      setMessage({ ok: false, text: `Thresholds not reset: ${e.message}` });
    }
    onConfigChange();
  };

  const over = (val, limit) => Number(val) > Number(limit);

  return (
    <div className="module-page">
      <h1>SETTINGS</h1>
      <p className="module-subtitle">SYSTEM CONFIGURATION · EDIT & SAVE</p>

      <div className="settings-status-row">
        <StatusCard label="FASTAPI" ok={status.api} />
        <StatusCard label="MQTT BROKER" ok={status.broker} />
        <StatusCard label="SENSOR" ok={status.sensor} />
      </div>

      <div className="settings-grid">
        <div className="module-card">
          <h3>DASHBOARD (THIS BROWSER)</h3>
          <div className="setting-field">
            <label htmlFor="room-name">Room Name</label>
            <input id="room-name" type="text" value={client.ROOM_NAME} onChange={(e) => updateClient("ROOM_NAME", e.target.value)} />
          </div>
          <div className="setting-field">
            <label htmlFor="refresh">Refresh Interval (ms)</label>
            <input id="refresh" type="number" min={500} max={30000} step={500} value={client.REFRESH_INTERVAL} onChange={(e) => updateClient("REFRESH_INTERVAL", Number(e.target.value))} />
          </div>
          <div className="setting-field">
            <label htmlFor="api-url">API URL</label>
            <input id="api-url" type="text" value={client.API_URL} onChange={(e) => updateClient("API_URL", e.target.value)} />
          </div>
          <div className="setting-field">
            <label htmlFor="mqtt-topic">MQTT Topic (set in backend .env)</label>
            <input id="mqtt-topic" type="text" value={SERVER.mqttTopic} readOnly />
          </div>
        </div>

        <div className="module-card">
          <h3>ALERT THRESHOLDS (BACKEND)</h3>
          {THRESHOLD_FIELDS.map((f) => (
            <div key={f.key} className="setting-field">
              <label htmlFor={f.key} style={{ color: f.color }}>{f.label}</label>
              <input
                id={f.key} type="number" min={f.min} max={f.max} step={f.step}
                value={thresholds[f.key]}
                onChange={(e) => updateThreshold(f.key, Number(e.target.value))}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="settings-actions">
        <button className="export-btn" onClick={saveAll} disabled={saving || !status.api}>
          {saving ? "SAVING..." : "SAVE ALL SETTINGS"}
        </button>
        <button className="export-btn secondary" onClick={handleReset}>RESET TO DEFAULTS</button>
      </div>
      {message && (
        <p className="settings-message" style={{ color: message.ok ? "#22c55e" : "#ef4444" }}>{message.text}</p>
      )}

      <TelegramCard apiOnline={status.api} />

      <div className="module-card" style={{ marginTop: 18 }}>
        <h3>SENSOR LIVE STATUS</h3>
        <div className="mqtt-terminal">
          <div><span>[ROOM]</span> {client.ROOM_NAME}</div>
          <div><span>[TEMP]</span> {temp} °C</div>
          <div><span>[HUMIDITY]</span> {humidity} %</div>
          <div><span>[STATUS]</span> {status.sensor ? "ONLINE" : "OFFLINE"}</div>
          <div><span>[AI_HEALTH]</span> {health}/100</div>
          <div><span>[LAST_PKT]</span> {lastUpdate}</div>
          <br />
          <div><span>── THRESHOLD CHECK (unsaved values) ──</span></div>
          <div style={{ color: over(temp, thresholds.TEMP_HIGH) ? "#ef4444" : "#22c55e" }}>
            <span>[TEMP]</span> {temp} {over(temp, thresholds.TEMP_HIGH) ? `> HIGH! (>${thresholds.TEMP_HIGH})` : "< OK"}
          </div>
          <div style={{ color: over(humidity, thresholds.HUMIDITY_HIGH) ? "#ef4444" : "#22c55e" }}>
            <span>[HUMIDITY]</span> {humidity} {over(humidity, thresholds.HUMIDITY_HIGH) ? `> HIGH! (>${thresholds.HUMIDITY_HIGH})` : "< OK"}
          </div>
        </div>
      </div>

      <div className="module-card" style={{ marginTop: 18 }}>
        <h3>WHERE SETTINGS LIVE</h3>
        <div className="settings-files-row">
          {[
            { name: ".env / config.py", desc: "Broker, topic, ports, initial thresholds", color: "#22c55e" },
            { name: "data/settings.json", desc: "Thresholds saved from this page (backend)", color: "#22d3ee" },
            { name: "localStorage", desc: "API URL, refresh, room name (this browser)", color: "#a855f7" },
          ].map((f) => (
            <div key={f.name} className="file-card">
              <span style={{ color: f.color, fontFamily: "Oxanium", fontSize: 11, fontWeight: 700 }}>{f.name}</span>
              <small>{f.desc}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
