import * as THREE from "three";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Text, Line } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import { Component, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  Brain,
  LayoutDashboard,
  Box,
  Building2,
  LineChart,
  Zap,
  Cloud,
  AlertTriangle,
  FileText,
  Settings as SettingsIcon,
  Layers,
  Thermometer,
  Droplets,
  Wind,
  Sparkles,
} from "lucide-react";
import "./App.css";
import { CLIENT, SERVER, THRESHOLDS, apiGet, formatTime, loadServerConfig } from "./config";
import Energy from "./components/Energy";
import Reports from "./components/Reports";
import Settings from "./components/Settings";
import AIBrain from "./components/AIBrain";
import Predictions from "./components/Predictions";

const HISTORY_REFRESH_FACTOR = 5; // history changes slowly; poll it 5x less often
const NO_ALERTS = "No active alerts.";

// drei <Text> fetches glyph data from a CDN. Without internet that fetch fails
// and used to blank the whole 3D canvas; now only the label is skipped.
class OptionalBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error) {
    console.warn("3D label unavailable:", error.message);
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

function Room({ position, size, color, label, temp, humidity, active, viewMode, layers }) {
  const [w, h, d] = size;
  // One geometry per room size, disposed on unmount (was re-created every poll).
  const edges = useMemo(() => {
    const box = new THREE.BoxGeometry(w, h, d);
    const geometry = new THREE.EdgesGeometry(box);
    box.dispose();
    return geometry;
  }, [w, h, d]);
  useEffect(() => () => edges.dispose(), [edges]);

  const heatColor =
    Number(humidity) > THRESHOLDS.HUMIDITY_HIGH ? "#ef4444" :
    Number(humidity) > THRESHOLDS.HUMIDITY_WARM ? "#facc15" :
    color;

  const finalColor = viewMode === "HEATMAP" && active ? heatColor : color;

  const readout = [
    layers.temperature ? `${temp}°C` : null,
    layers.humidity ? `${humidity}%` : null,
  ].filter(Boolean).join(" | ");

  return (
    <group position={position}>
      {layers.structure && (
        <>
          {active && (
            <mesh position={[0, h / 2, 0]}>
              <boxGeometry args={size} />
              <meshStandardMaterial
                color={finalColor}
                transparent
                opacity={0.3}
                emissive={finalColor}
                emissiveIntensity={0.9}
                depthWrite={false}
              />
            </mesh>
          )}

          <lineSegments position={[0, h / 2, 0]} geometry={edges}>
            <lineBasicMaterial color={finalColor} transparent opacity={active ? 1 : 0.28} />
          </lineSegments>
        </>
      )}

      {active && (
        <>
          <pointLight position={[0, 1.8, 0]} color={finalColor} intensity={4} distance={5} />

          {readout && (
            <OptionalBoundary>
            <Suspense fallback={null}>
            <Text
              position={[0, h + 0.6, 0]}
              fontSize={0.24}
              color="#22d3ee"
              anchorX="center"
              anchorY="middle"
              maxWidth={4}
              textAlign="center"
            >
              {`${label}\n${readout}`}
            </Text>
            </Suspense>
            </OptionalBoundary>
          )}
        </>
      )}
    </group>
  );
}

function FlowLine({ points, color = "#00d4ff" }) {
  return <Line points={points} color={color} lineWidth={3} transparent opacity={0.75} />;
}

const PARTICLE_COUNT = 80;
const PARTICLE_COLORS = ["#00d4ff", "#22c55e", "#facc15"].map((c) => new THREE.Color(c));

// Generated once at module load (keeps render pure); one draw call for all particles.
const PARTICLE_POSITIONS = new Float32Array(PARTICLE_COUNT * 3);
const PARTICLE_VERTEX_COLORS = new Float32Array(PARTICLE_COUNT * 3);
for (let i = 0; i < PARTICLE_COUNT; i++) {
  PARTICLE_POSITIONS.set([(Math.random() - 0.5) * 10, Math.random() * 3.2, (Math.random() - 0.5) * 7], i * 3);
  const c = PARTICLE_COLORS[i % PARTICLE_COLORS.length];
  PARTICLE_VERTEX_COLORS.set([c.r, c.g, c.b], i * 3);
}

function Particles() {
  const positions = PARTICLE_POSITIONS;
  const colors = PARTICLE_VERTEX_COLORS;

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.06} vertexColors toneMapped={false} sizeAttenuation />
    </points>
  );
}

const DEFAULT_LAYERS = { structure: true, temperature: true, humidity: true, airflow: true };

function BuildingScene({ room, temp, humidity, viewMode = "3D", layers = DEFAULT_LAYERS }) {
  const camera =
    viewMode === "2D"
      ? { position: [0, 8, 0.01], fov: 45 }
      : { position: [5.7, 5.0, 6.5], fov: 43 };

  return (
    <Canvas key={viewMode} camera={camera}>
      <color attach="background" args={["#020617"]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[5, 8, 4]} intensity={1.5} color="#8edcff" />
      <pointLight position={[0, 4, 0]} intensity={2.8} color="#00d4ff" />

      <group rotation={[0, viewMode === "2D" ? 0 : -0.22, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
          <planeGeometry args={[10, 7, 25, 25]} />
          <meshStandardMaterial color="#03111f" transparent opacity={0.95} />
        </mesh>

        <gridHelper args={[10, 25, "#00d4ff", "#083553"]} position={[0, 0.01, 0]} />

        <Room
          position={[-2.5, 0, -0.8]}
          size={[2.5, 1.1, 2.2]}
          color="#00ff88"
          label={room.toUpperCase()}
          temp={temp}
          humidity={humidity}
          active
          viewMode={viewMode}
          layers={layers}
        />

        <Room position={[0.1, 0, -1.4]} size={[2.5, 1.2, 2.0]} color="#00b7ff" active={false} viewMode={viewMode} layers={layers} />
        <Room position={[2.45, 0, -0.7]} size={[2.3, 1.2, 2.1]} color="#facc15" active={false} viewMode={viewMode} layers={layers} />
        <Room position={[-0.7, 0, 1.55]} size={[2.2, 1.0, 1.6]} color="#22c55e" active={false} viewMode={viewMode} layers={layers} />
        <Room position={[2.0, 0, 1.45]} size={[2.4, 1.25, 1.8]} color="#3b82f6" active={false} viewMode={viewMode} layers={layers} />

        {layers.airflow && (
          <>
            <FlowLine points={[[-3.6, 0.08, 0.8], [-2, 0.08, 1.3], [0, 0.08, 0.7], [1.8, 0.08, 1.3]]} />
            <FlowLine points={[[-2.7, 0.12, -1.8], [-0.6, 0.12, -1.2], [1.6, 0.12, -1.6], [3.3, 0.12, -0.6]]} color="#22c55e" />
            <FlowLine points={[[-0.8, 0.1, 2.4], [0.5, 0.1, 1.5], [2.5, 0.1, 1.8]]} color="#a855f7" />
          </>
        )}

        <Particles />
      </group>

      <OrbitControls enableZoom={false} enablePan={false} autoRotate={viewMode === "3D"} autoRotateSpeed={0.45} />

      <EffectComposer>
        <Bloom intensity={1.7} luminanceThreshold={0.08} luminanceSmoothing={0.2} />
      </EffectComposer>
    </Canvas>
  );
}

const NAV_ITEMS = [
  ["DASHBOARD", LayoutDashboard],
  ["3D TWIN", Box],
  ["FLOORPLAN", Building2],
  ["ANALYTICS", LineChart],
  ["AI BRAIN", Brain],
  ["PREDICTIONS", Sparkles],
  ["ENERGY", Zap],
  ["MQTT STREAM", Cloud],
  ["ALERTS", AlertTriangle],
  ["REPORTS", FileText],
  ["SETTINGS", SettingsIcon],
];

function statusLabel(status) {
  if (!status.api) return { text: "API OFFLINE", ok: false };
  if (!status.broker) return { text: "BROKER OFFLINE", ok: false };
  if (!status.sensor) return { text: "SENSOR OFFLINE", ok: false };
  return { text: "NETWORK ACTIVE", ok: true };
}

function Sidebar({ active, setActive, room, status }) {
  const net = statusLabel(status);

  return (
    <aside className="sidebar">
      <div className="brand">
        <Brain size={48} />
        <div>
          <h1>AI OS v6</h1>
          <p>{room.toUpperCase()} MONITORING<br />NEURAL CONTROL CENTER</p>
        </div>
      </div>

      <nav>
        {NAV_ITEMS.map(([name, Icon]) => (
          <button key={name} className={active === name ? "active" : ""} onClick={() => setActive(name)}>
            <Icon />
            {name}
          </button>
        ))}
      </nav>

      <div className="system">
        <span>SYSTEM INFO</span>
        <p>Version <b>v6.1</b></p>
        <p>Backend <b>FastAPI</b></p>
        <p>Sensor <b>DHT11</b></p>
        <p>Topic <b>{SERVER.mqttTopic}</b></p>
        <div className="mini-brain">🧠</div>
        <strong className={net.ok ? "" : "status-off"}>{net.text}</strong>
      </div>
    </aside>
  );
}

function Metric({ label, value, sub, bad }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <h2 className={bad ? "status-off" : ""}>{value}</h2>
      <small>{sub}</small>
    </div>
  );
}

function LiveEnvironment({ room, temp, humidity, health, lastUpdate }) {
  return (
    <section className="env-panel">
      <h3>LIVE ENVIRONMENT</h3>

      <div>
        <span>ROOM</span>
        <b>{room}</b>
        <small>Active sensor zone</small>
      </div>

      <div>
        <span>TEMPERATURE</span>
        <b>{temp} °C</b>
        <small>Live DHT11 value</small>
      </div>

      <div>
        <span>HUMIDITY</span>
        <b>{humidity} %</b>
        <small>Live DHT11 value</small>
      </div>

      <div>
        <span>AI HEALTH</span>
        <b>{health}/100</b>
        <small>Calculated from temp/humidity</small>
      </div>

      <div>
        <span>LAST PACKET</span>
        <b>{lastUpdate}</b>
        <small>MQTT update time</small>
      </div>
    </section>
  );
}

function MqttPanel({ room, latest, health, lastUpdate, connected }) {
  const payload = { room: latest.room, temperature: latest.temperature, humidity: latest.humidity };

  return (
    <div className="mqtt panel">
      <h3>MQTT PACKET STREAM <b className={connected ? "" : "status-off"}>● {connected ? "LIVE" : "OFFLINE"}</b></h3>

      <div className="mqtt-terminal">
        <div><span>[API]</span> {CLIENT.API_URL}</div>
        <div><span>[TOPIC]</span> {SERVER.mqttTopic}</div>
        <div><span>[ROOM]</span> {room}</div>
        <div><span>[TEMP]</span> {latest.temperature ?? "--"} °C</div>
        <div><span>[HUMIDITY]</span> {latest.humidity ?? "--"} %</div>
        <div><span>[AI_HEALTH]</span> {health}/100</div>
        <div><span>[LAST_PACKET]</span> {lastUpdate}</div>
        <div><span>[BAD_PACKETS]</span> {latest.invalid_packets ?? 0}</div>

        <br />

        <div><span>last payload</span></div>
        <div>{JSON.stringify(payload)}</div>
      </div>
    </div>
  );
}

function MiniChart({ data, field, color }) {
  const values = data.map((d) => Number(d[field])).filter((v) => !Number.isNaN(v));

  const safeValues = values.length > 1 ? values.slice(-40) : [0, 0];
  const min = Math.min(...safeValues);
  const max = Math.max(...safeValues);
  const range = max - min || 1;

  const points = safeValues
    .map((v, i) => `${(i / (safeValues.length - 1)) * 600},${170 - ((v - min) / range) * 130}`)
    .join(" ");

  const lastY = 170 - ((safeValues[safeValues.length - 1] - min) / range) * 130;

  return (
    <svg className="real-chart" viewBox="0 0 600 190">
      <polyline points={points} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="600" cy={lastY} r="6" fill={color} />
    </svg>
  );
}

function AlertCards({ alerts, apiOnline }) {
  if (!apiOnline) {
    return <div className="alert red">NO DATA<br /><small>Backend unreachable: alerts unknown.</small></div>;
  }
  const active = alerts.filter((a) => a !== NO_ALERTS);
  if (active.length === 0) {
    return <div className="alert green">ALL CLEAR<br /><small>No active alerts.</small></div>;
  }
  return active.map((a) => (
    <div key={a} className="alert red">ALERT<br /><small>{a}</small></div>
  ));
}

function Dashboard({ room, latest, temp, humidity, health, lastUpdate, alerts, status }) {
  const [viewMode, setViewMode] = useState("3D");
  const [layers, setLayers] = useState(DEFAULT_LAYERS);
  const toggle = (key) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  const upper = room.toUpperCase();

  return (
    <>
      <div className="top-row">
        <div className="logo-panel">
          <Brain />
          <div>
            <h1>AI OS v6</h1>
            <p>{upper} MONITORING<br />NEURAL CONTROL CENTER</p>
          </div>
        </div>

        <Metric
          label="AI CORE"
          value={status.api ? "ONLINE" : "OFFLINE"}
          sub={status.api ? "Backend/API active" : "Backend unreachable"}
          bad={!status.api}
        />
        <Metric label={`${upper} TEMP`} value={`${temp}°C`} sub="Live DHT11 value" />
        <Metric label={`${upper} HUMIDITY`} value={`${humidity}%`} sub="Live DHT11 value" />
        <Metric label="AI HEALTH" value={`${health}/100`} sub="Calculated score" />
        <Metric
          label="LAST PACKET"
          value={lastUpdate}
          sub={status.sensor ? "MQTT update time" : "Sensor offline"}
          bad={!status.sensor}
        />
      </div>

      <div className="dashboard-grid">
        <LiveEnvironment room={room} temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate} />

        <section className="twin-panel">
          <div className="panel-header">
            <h3>3D {upper} DIGITAL TWIN</h3>
            <p><span>REAL-TIME</span><span>DIGITAL SHADOW</span></p>
          </div>

          <BuildingScene room={room} temp={temp} humidity={humidity} viewMode={viewMode} layers={layers} />

          <div className="controls">
            <div>
              ROOM
              <button className="active">{upper}</button>
              <button disabled>ROOM 2</button>
              <button disabled>ROOM 3</button>
            </div>

            <div>
              VIEW
              {["3D", "2D", "HEATMAP"].map((mode) => (
                <button key={mode} className={viewMode === mode ? "active" : ""} onClick={() => setViewMode(mode)}>{mode}</button>
              ))}
            </div>

            <div>
              LAYERS
              <button className={layers.structure ? "active" : ""} onClick={() => toggle("structure")} title="Structure"><Layers /></button>
              <button className={layers.temperature ? "active" : ""} onClick={() => toggle("temperature")} title="Temperature"><Thermometer /></button>
              <button className={layers.humidity ? "active" : ""} onClick={() => toggle("humidity")} title="Humidity"><Droplets /></button>
              <button className={layers.airflow ? "active" : ""} onClick={() => toggle("airflow")} title="Airflow"><Wind /></button>
            </div>
          </div>
        </section>

        <aside className="right-stack">
          <div className="alerts panel">
            <h3>AI ALERTS</h3>
            <AlertCards alerts={alerts} apiOnline={status.api} />
            <div className="alert blue">
              AI HEALTH
              <br />
              <small>Current calculated health score: {health}/100</small>
            </div>
          </div>

          <MqttPanel room={room} latest={latest} health={health} lastUpdate={lastUpdate} connected={status.sensor} />
        </aside>
      </div>
    </>
  );
}

function Floorplan({ room, temp, humidity, health }) {
  return (
    <div className="module-page">
      <h1>FLOORPLAN</h1>
      <p className="module-subtitle">{room} active zone + empty future rooms</p>

      <div className="floorplan-grid">
        <div className="zone zone-green">
          <h3>{room.toUpperCase()}</h3>
          <p>{temp}°C | {humidity}%</p>
          <span>AI Health: {health}/100</span>
        </div>

        <div className="zone zone-empty"><h3>ROOM 2</h3><p>--</p><span>Future sensor zone</span></div>
        <div className="zone zone-empty"><h3>ROOM 3</h3><p>--</p><span>Future sensor zone</span></div>
        <div className="zone zone-empty"><h3>ROOM 4</h3><p>--</p><span>Future sensor zone</span></div>
      </div>
    </div>
  );
}

function Analytics({ room, temp, humidity, health, history }) {
  return (
    <div className="module-page">
      <h1>ANALYTICS</h1>
      <p className="module-subtitle">Only live {room} telemetry is shown</p>

      <div className="analytics-grid">
        <div className="module-card">
          <h3>{room} Temperature</h3>
          <MiniChart data={history} field="temperature" color="#f97316" />
          <p>Current: <b>{temp}°C</b></p>
        </div>

        <div className="module-card">
          <h3>{room} Humidity</h3>
          <MiniChart data={history} field="humidity" color="#22d3ee" />
          <p>Current: <b>{humidity}%</b></p>
        </div>

        <div className="module-card">
          <h3>AI Health Score</h3>
          <div className="big-score">{health}/100</div>
          <p>Calculated from live temperature/humidity</p>
        </div>
      </div>
    </div>
  );
}

function Alerts({ room, health, alerts, healthInfo, apiOnline }) {
  const active = apiOnline ? alerts.filter((a) => a !== NO_ALERTS) : ["Backend unreachable: alerts unknown."];

  return (
    <div className="module-page">
      <h1>ALERTS</h1>
      <p className="module-subtitle">{room} environmental alert center · thresholds from backend</p>

      <div className="alerts-list">
        {active.length === 0 ? (
          <div className="alert-module good">
            <h3>✅ All Clear</h3>
            <p>No active alerts for {room}.</p>
          </div>
        ) : (
          active.map((a) => (
            <div key={a} className="alert-module bad">
              <h3>⚠ Alert</h3>
              <p>{a}</p>
            </div>
          ))
        )}

        <div className="alert-module blue">
          <h3>🧠 AI Diagnosis</h3>
          <p>
            {room} health score is {health}/100.
            {healthInfo.dew_point != null && ` Dew point ${healthInfo.dew_point}°C, mold risk ${healthInfo.mold_risk}.`}
          </p>
        </div>
      </div>
    </div>
  );
}

const EMPTY_LATEST = { temperature: null, humidity: null, last_update: null, room: null };

export default function App() {
  const [active, setActive] = useState("DASHBOARD");
  const [latest, setLatest] = useState(EMPTY_LATEST);
  const [healthInfo, setHealthInfo] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [apiOnline, setApiOnline] = useState(false);
  const [, setConfigVersion] = useState(0);
  const refreshConfig = useCallback(() => setConfigVersion((v) => v + 1), []);

  const loadLive = useCallback(async () => {
    try {
      const [latestJson, healthJson, alertsJson] = await Promise.all([
        apiGet("/latest"),
        apiGet("/health"),
        apiGet("/alerts"),
      ]);
      setLatest(latestJson);
      setHealthInfo(healthJson);
      setAlerts(alertsJson.alerts || []);
      setApiOnline(true);
    } catch (error) {
      console.warn("API offline:", error);
      setApiOnline(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const json = await apiGet("/history");
      setHistory(Array.isArray(json) ? json : []);
    } catch {
      // live loader already reports the outage
    }
  }, []);

  useEffect(() => {
    loadServerConfig().then(refreshConfig).catch(() => {});
    const first = setTimeout(() => {
      loadLive();
      loadHistory();
    }, 0);

    const interval = Number(CLIENT.REFRESH_INTERVAL) || 2000;
    const live = setInterval(loadLive, interval);
    const hist = setInterval(loadHistory, interval * HISTORY_REFRESH_FACTOR);
    return () => {
      clearTimeout(first);
      clearInterval(live);
      clearInterval(hist);
    };
  }, [loadLive, loadHistory, refreshConfig]);

  const temp = latest.temperature != null ? Number(latest.temperature).toFixed(1) : "--";
  const humidity = latest.humidity != null ? Number(latest.humidity).toFixed(1) : "--";
  const healthScore = healthInfo.health_score ?? null;
  const health = healthScore ?? "--";
  const lastUpdate = formatTime(latest.last_update);
  const room = CLIENT.ROOM_NAME || latest.room || "Room";

  const status = {
    api: apiOnline,
    broker: apiOnline && Boolean(latest.broker_connected),
    sensor: apiOnline && Boolean(latest.connected),
  };

  return (
    <div className="app">
      <Sidebar active={active} setActive={setActive} room={room} status={status} />

      <main className="main">
        {active === "DASHBOARD" && (
          <Dashboard
            room={room} latest={latest} temp={temp} humidity={humidity} health={health}
            lastUpdate={lastUpdate} alerts={alerts} status={status}
          />
        )}

        {active === "3D TWIN" && (
          <section className="twin-panel full-page-panel">
            <div className="panel-header">
              <h3>3D {room.toUpperCase()} DIGITAL TWIN</h3>
              <p><span>REAL-TIME</span><span>DIGITAL SHADOW</span></p>
            </div>
            <BuildingScene room={room} temp={temp} humidity={humidity} />
          </section>
        )}

        {active === "FLOORPLAN" && <Floorplan room={room} temp={temp} humidity={humidity} health={health} />}

        {active === "ANALYTICS" && (
          <Analytics room={room} temp={temp} humidity={humidity} health={health} history={history} />
        )}

        {active === "MQTT STREAM" && (
          <MqttPanel room={room} latest={latest} health={health} lastUpdate={lastUpdate} connected={status.sensor} />
        )}

        {active === "ALERTS" && <Alerts room={room} health={health} alerts={alerts} healthInfo={healthInfo} apiOnline={status.api} />}

        {active === "AI BRAIN" && <AIBrain temp={temp} humidity={humidity} health={healthScore} history={history} />}
        {active === "PREDICTIONS" && <Predictions />}
        {active === "ENERGY" && <Energy temp={temp} humidity={humidity} history={history} />}
        {active === "REPORTS" && <Reports room={room} history={history} />}
        {active === "SETTINGS" && (
          <Settings
            temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate}
            status={status} onConfigChange={refreshConfig}
          />
        )}
      </main>
    </div>
  );
}
