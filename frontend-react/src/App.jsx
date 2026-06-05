import * as THREE from "three";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Text, Line } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import { useEffect, useMemo, useState } from "react";
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
  Settings,
  Layers,
  Thermometer,
  Droplets,
  Wind,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function Room({ position, size, color, label, temp, humidity, active, viewMode, layers }) {
  const heatColor =
    Number(humidity) > 75 ? "#ef4444" :
    Number(humidity) > 65 ? "#facc15" :
    color;

  const finalColor = viewMode === "HEATMAP" && active ? heatColor : color;

  return (
    <group position={position}>
      {layers.structure && (
        <>
          {active && (
            <mesh position={[0, size[1] / 2, 0]}>
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

          <lineSegments position={[0, size[1] / 2, 0]}>
            <edgesGeometry args={[new THREE.BoxGeometry(...size)]} />
            <lineBasicMaterial
              color={finalColor}
              transparent
              opacity={active ? 1 : 0.28}
            />
          </lineSegments>
        </>
      )}

      {active && (
        <>
          <pointLight position={[0, 1.8, 0]} color={finalColor} intensity={4} distance={5} />

          {(layers.temperature || layers.humidity) && (
            <Text
              position={[0, size[1] + 0.6, 0]}
              fontSize={0.24}
              color="#22d3ee"
              anchorX="center"
              anchorY="middle"
              maxWidth={4}
            >
              {`${label}
${layers.temperature ? `${temp}°C` : ""}
${layers.temperature && layers.humidity ? " | " : ""}
${layers.humidity ? `${humidity}%` : ""}`}
            </Text>
          )}
        </>
      )}
    </group>
  );
}

function FlowLine({ points, color = "#00d4ff" }) {
  return (
    <Line
      points={points}
      color={color}
      lineWidth={3}
      transparent
      opacity={0.75}
    />
  );
}

function Particles() {
  const points = useMemo(() => {
    return Array.from({ length: 80 }, () => [
      (Math.random() - 0.5) * 10,
      Math.random() * 3.2,
      (Math.random() - 0.5) * 7,
    ]);
  }, []);

  return (
    <>
      {points.map((p, i) => {
        const color = i % 3 === 0 ? "#00d4ff" : i % 3 === 1 ? "#22c55e" : "#facc15";

        return (
          <mesh key={i} position={p}>
            <sphereGeometry args={[0.025, 8, 8]} />
            <meshStandardMaterial
              color={color}
              emissive={color}
              emissiveIntensity={2}
            />
          </mesh>
        );
      })}
    </>
  );
}

function BuildingScene({ temp, humidity, viewMode = "3D", layers = {} }) {
  const safeLayers = {
    structure: true,
    temperature: true,
    humidity: true,
    airflow: true,
    ...layers,
  };

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
          label="BEDROOM"
          temp={temp}
          humidity={humidity}
          active={true}
          viewMode={viewMode}
          layers={safeLayers}
        />

        <Room position={[0.1, 0, -1.4]} size={[2.5, 1.2, 2.0]} color="#00b7ff" active={false} viewMode={viewMode} layers={safeLayers} />
        <Room position={[2.45, 0, -0.7]} size={[2.3, 1.2, 2.1]} color="#facc15" active={false} viewMode={viewMode} layers={safeLayers} />
        <Room position={[-0.7, 0, 1.55]} size={[2.2, 1.0, 1.6]} color="#22c55e" active={false} viewMode={viewMode} layers={safeLayers} />
        <Room position={[2.0, 0, 1.45]} size={[2.4, 1.25, 1.8]} color="#3b82f6" active={false} viewMode={viewMode} layers={safeLayers} />

        {safeLayers.airflow && (
          <>
            <FlowLine points={[[-3.6, 0.08, 0.8], [-2, 0.08, 1.3], [0, 0.08, 0.7], [1.8, 0.08, 1.3]]} />
            <FlowLine points={[[-2.7, 0.12, -1.8], [-0.6, 0.12, -1.2], [1.6, 0.12, -1.6], [3.3, 0.12, -0.6]]} color="#22c55e" />
            <FlowLine points={[[-0.8, 0.1, 2.4], [0.5, 0.1, 1.5], [2.5, 0.1, 1.8]]} color="#a855f7" />
          </>
        )}

        <Particles />
      </group>

      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate={viewMode === "3D"}
        autoRotateSpeed={0.45}
      />

      <EffectComposer>
        <Bloom intensity={1.7} luminanceThreshold={0.08} luminanceSmoothing={0.2} />
      </EffectComposer>
    </Canvas>
  );
}

function Sidebar({ active, setActive }) {
  const items = [
    ["DASHBOARD", <LayoutDashboard />],
    ["3D TWIN", <Box />],
    ["FLOORPLAN", <Building2 />],
    ["ANALYTICS", <LineChart />],
    ["AI BRAIN", <Brain />],
    ["ENERGY", <Zap />],
    ["MQTT STREAM", <Cloud />],
    ["ALERTS", <AlertTriangle />],
    ["REPORTS", <FileText />],
    ["SETTINGS", <Settings />],
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <Brain size={48} />
        <div>
          <h1>AI OS v6</h1>
          <p>BEDROOM MONITORING<br />NEURAL CONTROL CENTER</p>
        </div>
      </div>

      <nav>
        {items.map(([name, icon]) => (
          <button
            key={name}
            className={active === name ? "active" : ""}
            onClick={() => setActive(name)}
          >
            {icon}
            {name}
          </button>
        ))}
      </nav>

      <div className="system">
        <span>SYSTEM INFO</span>
        <p>Version <b>v6.0</b></p>
        <p>Backend <b>FastAPI</b></p>
        <p>Sensor <b>DHT11</b></p>
        <p>Topic <b>smartroom/dht11</b></p>
        <div className="mini-brain">🧠</div>
        <strong>NETWORK ACTIVE</strong>
      </div>
    </aside>
  );
}

function Metric({ label, value, sub }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <h2>{value}</h2>
      <small>{sub}</small>
    </div>
  );
}

function LiveEnvironment({ temp, humidity, health, lastUpdate }) {
  return (
    <section className="env-panel">
      <h3>LIVE ENVIRONMENT</h3>

      <div>
        <span>ROOM</span>
        <b>Bedroom</b>
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

function MqttPanel({ temp, humidity, health, lastUpdate }) {
  return (
    <div className="mqtt panel">
      <h3>MQTT PACKET STREAM <b>● LIVE</b></h3>

      <div className="mqtt-terminal">
        <div><span>[API]</span> http://127.0.0.1:8000</div>
        <div><span>[TOPIC]</span> smartroom/dht11</div>
        <div><span>[ROOM]</span> Bedroom</div>
        <div><span>[TEMP]</span> {temp} °C</div>
        <div><span>[HUMIDITY]</span> {humidity} %</div>
        <div><span>[AI_HEALTH]</span> {health}/100</div>
        <div><span>[LAST_PACKET]</span> {lastUpdate}</div>

        <br />

        <div><span>payload</span></div>
        <div>
          {`{ "room": "Bedroom", "temperature": ${temp}, "humidity": ${humidity}, "health_score": ${health} }`}
        </div>
      </div>
    </div>
  );
}

function MiniChart({ data, field, color }) {
  const values = data
    .map((d) => Number(d[field]))
    .filter((v) => !Number.isNaN(v));

  const safeValues = values.length > 1 ? values.slice(-40) : [0, 0];
  const min = Math.min(...safeValues);
  const max = Math.max(...safeValues);
  const range = max - min || 1;

  const points = safeValues
    .map((v, i) => {
      const x = (i / (safeValues.length - 1)) * 600;
      const y = 170 - ((v - min) / range) * 130;
      return `${x},${y}`;
    })
    .join(" ");

  const last = safeValues[safeValues.length - 1];
  const lastY = 170 - ((last - min) / range) * 130;

  return (
    <svg className="real-chart" viewBox="0 0 600 190">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="600" cy={lastY} r="6" fill={color} />
    </svg>
  );
}

function Dashboard({ temp, humidity, health, lastUpdate }) {
  const [viewMode, setViewMode] = useState("3D");
  const [layers, setLayers] = useState({
    structure: true,
    temperature: true,
    humidity: true,
    airflow: true,
  });

  return (
    <>
      <div className="top-row">
        <div className="logo-panel">
          <Brain />
          <div>
            <h1>AI OS v6</h1>
            <p>BEDROOM MONITORING<br />NEURAL CONTROL CENTER</p>
          </div>
        </div>

        <Metric label="AI CORE" value="ONLINE" sub="Backend/API active" />
        <Metric label="BEDROOM TEMP" value={`${temp}°C`} sub="Live DHT11 value" />
        <Metric label="BEDROOM HUMIDITY" value={`${humidity}%`} sub="Live DHT11 value" />
        <Metric label="AI HEALTH" value={`${health}/100`} sub="Calculated score" />
        <Metric label="LAST PACKET" value={lastUpdate} sub="MQTT update time" />
      </div>

      <div className="dashboard-grid">
        <LiveEnvironment temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate} />

        <section className="twin-panel">
          <div className="panel-header">
            <h3>3D BEDROOM DIGITAL TWIN</h3>
            <p><span>REAL-TIME</span><span>DIGITAL SHADOW</span></p>
          </div>

          <BuildingScene
            temp={temp}
            humidity={humidity}
            viewMode={viewMode}
            layers={layers}
          />

          <div className="controls">
            <div>
              ROOM
              <button className="active">BEDROOM</button>
              <button disabled>ROOM 2</button>
              <button disabled>ROOM 3</button>
            </div>

            <div>
              VIEW
              <button className={viewMode === "3D" ? "active" : ""} onClick={() => setViewMode("3D")}>3D</button>
              <button className={viewMode === "2D" ? "active" : ""} onClick={() => setViewMode("2D")}>2D</button>
              <button className={viewMode === "HEATMAP" ? "active" : ""} onClick={() => setViewMode("HEATMAP")}>HEATMAP</button>
            </div>

            <div>
              LAYERS
              <button className={layers.structure ? "active" : ""} onClick={() => setLayers({ ...layers, structure: !layers.structure })}><Layers /></button>
              <button className={layers.temperature ? "active" : ""} onClick={() => setLayers({ ...layers, temperature: !layers.temperature })}><Thermometer /></button>
              <button className={layers.humidity ? "active" : ""} onClick={() => setLayers({ ...layers, humidity: !layers.humidity })}><Droplets /></button>
              <button className={layers.airflow ? "active" : ""} onClick={() => setLayers({ ...layers, airflow: !layers.airflow })}><Wind /></button>
            </div>
          </div>
        </section>

        <aside className="right-stack">
          <div className="alerts panel">
            <h3>AI ALERTS</h3>

            <div className={Number(humidity) > 70 ? "alert red" : "alert green"}>
              {Number(humidity) > 70 ? "HIGH HUMIDITY" : "HUMIDITY NORMAL"}
              <br />
              <small>{Number(humidity) > 70 ? `Bedroom humidity is ${humidity}%. Ventilation recommended.` : "Humidity is acceptable."}</small>
            </div>

            <div className={Number(temp) > 27 ? "alert red" : "alert green"}>
              {Number(temp) > 27 ? "HIGH TEMPERATURE" : "TEMPERATURE NORMAL"}
              <br />
              <small>{Number(temp) > 27 ? `Bedroom temperature is ${temp}°C.` : "Temperature is acceptable."}</small>
            </div>

            <div className="alert blue">
              AI HEALTH
              <br />
              <small>Current calculated health score: {health}/100</small>
            </div>
          </div>

          <MqttPanel temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate} />
        </aside>
      </div>
    </>
  );
}

function Floorplan({ temp, humidity, health }) {
  return (
    <div className="module-page">
      <h1>FLOORPLAN</h1>
      <p className="module-subtitle">Bedroom active zone + empty future rooms</p>

      <div className="floorplan-grid">
        <div className="zone zone-green">
          <h3>BEDROOM</h3>
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

function Analytics({ temp, humidity, health, history }) {
  return (
    <div className="module-page">
      <h1>ANALYTICS</h1>
      <p className="module-subtitle">Only live Bedroom telemetry is shown</p>

      <div className="analytics-grid">
        <div className="module-card">
          <h3>Bedroom Temperature</h3>
          <MiniChart data={history} field="temperature" color="#f97316" />
          <p>Current: <b>{temp}°C</b></p>
        </div>

        <div className="module-card">
          <h3>Bedroom Humidity</h3>
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

function Alerts({ temp, humidity, health }) {
  return (
    <div className="module-page">
      <h1>ALERTS</h1>
      <p className="module-subtitle">Bedroom environmental alert center</p>

      <div className="alerts-list">
        <div className={Number(humidity) > 70 ? "alert-module bad" : "alert-module good"}>
          <h3>{Number(humidity) > 70 ? "⚠ High Humidity" : "✅ Humidity Normal"}</h3>
          <p>{Number(humidity) > 70 ? `Bedroom humidity is ${humidity}%. Ventilation recommended.` : "Bedroom humidity is acceptable."}</p>
        </div>

        <div className={Number(temp) > 27 ? "alert-module bad" : "alert-module good"}>
          <h3>{Number(temp) > 27 ? "⚠ High Temperature" : "✅ Temperature Normal"}</h3>
          <p>{Number(temp) > 27 ? `Bedroom temperature is ${temp}°C.` : "Bedroom temperature is acceptable."}</p>
        </div>

        <div className="alert-module blue">
          <h3>🧠 AI Diagnosis</h3>
          <p>Bedroom health score is {health}/100.</p>
        </div>
      </div>
    </div>
  );
}

function Placeholder({ title }) {
  return (
    <div className="module-page">
      <h1>{title}</h1>
      <p className="module-subtitle">This module is ready for future data integration.</p>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState("DASHBOARD");

  const [latest, setLatest] = useState({
    temperature: null,
    humidity: null,
    last_update: "--",
  });

  const [health, setHealth] = useState(0);
  const [history, setHistory] = useState([]);

  async function loadData() {
    try {
      const latestResponse = await fetch(`${API_URL}/latest`);
      const latestJson = await latestResponse.json();

      const healthResponse = await fetch(`${API_URL}/health`);
      const healthJson = await healthResponse.json();

      const historyResponse = await fetch(`${API_URL}/history`);
      const historyJson = await historyResponse.json();

      setLatest(latestJson);
      setHealth(healthJson.health_score ?? 0);
      setHistory(Array.isArray(historyJson) ? historyJson : []);
    } catch (error) {
      console.log("API offline:", error);
    }
  }

  useEffect(() => {
    loadData();

    const interval = setInterval(loadData, 2000);

    return () => clearInterval(interval);
  }, []);

  const temp =
    latest.temperature !== null && latest.temperature !== undefined
      ? Number(latest.temperature).toFixed(1)
      : "--";

  const humidity =
    latest.humidity !== null && latest.humidity !== undefined
      ? Number(latest.humidity).toFixed(1)
      : "--";

  const lastUpdate = latest.last_update ?? "--";

  return (
    <div className="app">
      <Sidebar active={active} setActive={setActive} />

      <main className="main">
        {active === "DASHBOARD" && (
          <Dashboard temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate} />
        )}

        {active === "3D TWIN" && (
          <section className="twin-panel full-page-panel">
            <div className="panel-header">
              <h3>3D BEDROOM DIGITAL TWIN</h3>
              <p><span>REAL-TIME</span><span>DIGITAL SHADOW</span></p>
            </div>
            <BuildingScene temp={temp} humidity={humidity} />
          </section>
        )}

        {active === "FLOORPLAN" && (
          <Floorplan temp={temp} humidity={humidity} health={health} />
        )}

        {active === "ANALYTICS" && (
          <Analytics temp={temp} humidity={humidity} health={health} history={history} />
        )}

        {active === "MQTT STREAM" && (
          <MqttPanel temp={temp} humidity={humidity} health={health} lastUpdate={lastUpdate} />
        )}

        {active === "ALERTS" && (
          <Alerts temp={temp} humidity={humidity} health={health} />
        )}

        {active === "AI BRAIN" && <Placeholder title="AI BRAIN" />}
        {active === "ENERGY" && <Placeholder title="ENERGY" />}
        {active === "REPORTS" && <Placeholder title="REPORTS" />}
        {active === "SETTINGS" && <Placeholder title="SETTINGS" />}
      </main>
    </div>
  );
}