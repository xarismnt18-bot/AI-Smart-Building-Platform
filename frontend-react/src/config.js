// Two kinds of settings:
//  * client settings (API URL, refresh rate, display name, heatmap colours)
//    live in this browser's localStorage;
//  * alert thresholds live in the backend (GET/PUT /config) so the dashboard
//    and the backend's /alerts, /health and /recommendations always agree.

const STORAGE_KEY = "smartbuilding_settings";

const clientDefaults = {
  API_URL: "http://127.0.0.1:8000",
  REFRESH_INTERVAL: 2000,
  ROOM_NAME: "Bedroom",
  TEMP_WARM: 25,
  HUMIDITY_WARM: 65,
};

const thresholdDefaults = {
  TEMP_LOW: 18,
  TEMP_HIGH: 27,
  TEMP_CRITICAL: 32,
  HUMIDITY_LOW: 35,
  HUMIDITY_HIGH: 70,
  HUMIDITY_CRITICAL: 85,
};

function loadClientOverrides() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    // keep only keys that still exist (older versions stored thresholds here)
    return Object.fromEntries(Object.entries(parsed).filter(([k]) => k in clientDefaults));
  } catch {
    return {};
  }
}

export function getClientSettings() {
  return { ...clientDefaults, ...loadClientOverrides() };
}

export function saveClientSettings(values) {
  const clean = Object.fromEntries(Object.entries(values).filter(([k]) => k in clientDefaults));
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clean));
  } catch {
    // storage unavailable (private mode) - settings apply until reload only
  }
  Object.assign(CLIENT, clean);
}

export function resetClientSettings() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
  Object.assign(CLIENT, clientDefaults);
}

// Live objects: components read these at render time, so updating them in
// place (Object.assign) is picked up on the next render without a reload.
export const CLIENT = getClientSettings();
export const THRESHOLDS = {
  ...thresholdDefaults,
  get TEMP_WARM() { return CLIENT.TEMP_WARM; },
  get HUMIDITY_WARM() { return CLIENT.HUMIDITY_WARM; },
};
export const SERVER = { mqttTopic: "--" };

function applyServerConfig(json) {
  Object.assign(THRESHOLDS, json.thresholds || {});
  if (json.mqtt_topic) SERVER.mqttTopic = json.mqtt_topic;
  return json;
}

async function request(path, options) {
  const res = await fetch(`${CLIENT.API_URL}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function apiGet(path) {
  return request(path);
}

export async function loadServerConfig() {
  return applyServerConfig(await request("/config"));
}

export async function saveThresholds(changes) {
  return applyServerConfig(await request("/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  }));
}

export async function resetThresholds() {
  return applyServerConfig(await request("/config", { method: "DELETE" }));
}

export function formatTime(iso) {
  if (!iso) return "--";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleTimeString();
}
