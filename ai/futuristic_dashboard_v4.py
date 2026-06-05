import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from sklearn.ensemble import IsolationForest
from streamlit_autorefresh import st_autorefresh
import paho.mqtt.client as mqtt


# =========================
# MQTT SETTINGS
# =========================
MQTT_BROKER = "192.168.1.143"
MQTT_PORT = 1883
MQTT_TOPIC = "smartroom/dht11"


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Smart Building AI OS v5",
    page_icon="🧠",
    layout="wide"
)


# =========================
# CSS
# =========================
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(56,189,248,0.22), transparent 28%),
        radial-gradient(circle at 85% 10%, rgba(34,197,94,0.16), transparent 25%),
        radial-gradient(circle at 50% 90%, rgba(168,85,247,0.16), transparent 30%),
        linear-gradient(135deg, #020617 0%, #0f172a 55%, #020617 100%);
    color: white;
}

.block-container {
    padding-top: 2rem;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }
    70% { box-shadow: 0 0 0 16px rgba(34,197,94,0); }
    100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

@keyframes scan {
    0% { left: -20%; }
    100% { left: 120%; }
}

@keyframes flow {
    0% { transform: translateX(-120px); opacity: 0; }
    50% { opacity: 1; }
    100% { transform: translateX(620px); opacity: 0; }
}

.os-title {
    font-size: 54px;
    font-weight: 900;
    background: linear-gradient(90deg, #38bdf8, #22c55e, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #cbd5e1;
    font-size: 18px;
    margin-bottom: 20px;
}

.live-dot {
    width: 12px;
    height: 12px;
    background: #22c55e;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.holo-card {
    background: rgba(15,23,42,0.78);
    border: 1px solid rgba(56,189,248,0.30);
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 0 35px rgba(56,189,248,0.10);
    backdrop-filter: blur(14px);
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.holo-card:hover {
    border-color: rgba(56,189,248,0.60);
    box-shadow: 0 0 50px rgba(56,189,248,0.25);
    transform: translateY(-2px);
}

.holo-label {
    color: #94a3b8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.holo-value {
    font-size: 36px;
    font-weight: 900;
}

.room3d {
    height: 360px;
    border: 2px solid rgba(56,189,248,0.38);
    border-radius: 24px;
    background:
        linear-gradient(rgba(56,189,248,0.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(56,189,248,0.07) 1px, transparent 1px),
        rgba(2,6,23,0.75);
    background-size: 34px 34px;
    position: relative;
    overflow: hidden;
    transform: perspective(900px) rotateX(8deg);
}

.scanline {
    position: absolute;
    top: 0;
    width: 160px;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(56,189,248,0.25), transparent);
    animation: scan 4s infinite linear;
}

.sensor-node {
    position: absolute;
    top: 42%;
    left: 46%;
    width: 62px;
    height: 62px;
    border-radius: 50%;
    background: radial-gradient(circle, #22c55e, #0f766e);
    box-shadow: 0 0 45px rgba(34,197,94,1);
    animation: pulse 2s infinite;
}

.room-label {
    position: absolute;
    top: 61%;
    left: 37%;
    text-align: center;
    font-weight: 800;
    color: #e0f2fe;
}

.energy-line {
    position: absolute;
    width: 130px;
    height: 4px;
    background: linear-gradient(90deg, transparent, #38bdf8, transparent);
    animation: flow 3s infinite linear;
}

.e1 { top: 25%; left: 10%; }
.e2 { top: 50%; left: 20%; animation-delay: 1s; }
.e3 { top: 75%; left: 5%; animation-delay: 2s; }

.terminal {
    background: #020617;
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 18px;
    padding: 18px;
    color: #22c55e;
    font-family: Consolas, monospace;
    font-size: 14px;
}

.ai-good {
    border-left: 5px solid #22c55e;
    background: rgba(34,197,94,0.16);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
}

.ai-warn {
    border-left: 5px solid #facc15;
    background: rgba(250,204,21,0.16);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
}

.ai-bad {
    border-left: 5px solid #ef4444;
    background: rgba(239,68,68,0.16);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
}

.heat-cell {
    height: 85px;
    border-radius: 16px;
    padding: 18px;
    font-weight: 800;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.12);
}
</style>
""", unsafe_allow_html=True)


# =========================
# SESSION STATE
# =========================
if "history" not in st.session_state:
    st.session_state.history = []


# =========================
# MQTT CLIENT
# =========================
@st.cache_resource
def start_mqtt_client():
    shared = {
        "room": "My Room",
        "temperature": None,
        "humidity": None,
        "connected": False,
        "last_update": None,
    }

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            shared["connected"] = True
            client.subscribe(MQTT_TOPIC)
        else:
            shared["connected"] = False

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            shared["room"] = payload.get("room", "My Room")
            shared["temperature"] = float(payload["temperature"])
            shared["humidity"] = float(payload["humidity"])
            shared["connected"] = True
            shared["last_update"] = datetime.now().strftime("%H:%M:%S")
        except Exception:
            shared["connected"] = False

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    return shared


mqtt_data = start_mqtt_client()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ AI OS Controls")

refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 2, 15, 3)
temp_high = st.sidebar.slider("High temperature threshold (°C)", 20, 35, 27)
humidity_high = st.sidebar.slider("High humidity threshold (%)", 50, 90, 70)

if st.sidebar.button("Clear memory"):
    st.session_state.history = []
    st.rerun()

st_autorefresh(interval=refresh_rate * 1000, key="ai_os_v5_refresh")


# =========================
# AI FUNCTIONS
# =========================
def comfort_score(temp, hum):
    score = 100

    if temp > temp_high:
        score -= min((temp - temp_high) * 8, 35)

    if hum > humidity_high:
        score -= min((hum - humidity_high) * 4, 35)

    if hum < 40:
        score -= min((40 - hum) * 2, 20)

    return max(int(score), 20)


def mold_risk_score(temp, hum):
    if hum < 60:
        return "LOW", 15
    if 60 <= hum < 70:
        return "MODERATE", 45
    if hum >= 70 and temp >= 18:
        return "HIGH", 80
    return "MODERATE", 50


def comfort_optimization(temp, hum):
    suggestions = []

    if hum > humidity_high:
        suggestions.append("Reduce humidity through ventilation or dehumidification.")

    if temp > temp_high:
        suggestions.append("Lower temperature or improve airflow.")

    if hum < 40:
        suggestions.append("Humidity is low. Consider humidification.")

    if 20 <= temp <= 25 and 40 <= hum <= 60:
        suggestions.append("Room conditions are optimal.")

    if not suggestions:
        suggestions.append("Conditions are acceptable, but continue monitoring trends.")

    return suggestions


def estimate_occupancy(history_df):
    if len(history_df) < 8:
        return "Unknown"

    recent_hum = history_df["humidity"].tail(8).values
    recent_temp = history_df["temperature"].tail(8).values

    hum_change = recent_hum[-1] - recent_hum[0]
    temp_change = recent_temp[-1] - recent_temp[0]

    if hum_change > 2 or temp_change > 0.4:
        return "Possible Occupancy"

    return "Likely Empty / Stable"


def predict_next(history_df, column):
    if len(history_df) < 6:
        return None, "Collecting data", 50

    y = history_df[column].tail(8).values
    x = np.arange(len(y))

    slope, intercept = np.polyfit(x, y, 1)
    next_value = slope * (len(y) + 3) + intercept

    if slope > 0.15:
        direction = "Rising"
    elif slope < -0.15:
        direction = "Falling"
    else:
        direction = "Stable"

    confidence = min(95, max(55, int(70 + abs(slope) * 20)))
    return round(float(next_value), 1), direction, confidence


def detect_ml_anomaly(history_df):
    if len(history_df) < 20:
        return False, "Collecting baseline"

    model_data = history_df[["temperature", "humidity"]].tail(60)

    model = IsolationForest(
        n_estimators=120,
        contamination=0.12,
        random_state=42
    )

    prediction = model.fit_predict(model_data)
    latest_prediction = prediction[-1]

    if latest_prediction == -1:
        return True, "ML anomaly detected"

    return False, "Normal pattern"


def device_online_status(last_update):
    if last_update is None:
        return "OFFLINE", "No MQTT packet received yet"
    return "ONLINE", f"Last packet at {last_update}"


def anomaly_severity(history_df, temp, hum):
    if len(history_df) < 20:
        return "LEARNING", 0, "Collecting normal baseline"

    temp_mean = history_df["temperature"].tail(40).mean()
    hum_mean = history_df["humidity"].tail(40).mean()

    temp_diff = abs(temp - temp_mean)
    hum_diff = abs(hum - hum_mean)

    severity_score = min(100, int((temp_diff * 18) + (hum_diff * 4)))

    if severity_score < 30:
        return "NORMAL", severity_score, "Environmental behavior is within expected range"
    elif severity_score < 60:
        return "WARNING", severity_score, "Noticeable deviation from recent room baseline"
    else:
        return "CRITICAL", severity_score, "Strong deviation detected from normal pattern"


def building_health_score(comfort, mold_score, anomaly_score):
    health = comfort
    health -= int(mold_score * 0.25)
    health -= int(anomaly_score * 0.30)
    return max(0, min(100, health))


def predictive_alert(pred_temp, pred_hum, temp_high, humidity_high):
    alerts = []

    if pred_temp is not None and pred_temp > temp_high:
        alerts.append("Temperature is expected to exceed the selected threshold soon.")

    if pred_hum is not None and pred_hum > humidity_high:
        alerts.append("Humidity is expected to exceed the selected threshold soon.")

    if not alerts:
        alerts.append("No immediate environmental risk predicted.")

    return alerts


# =========================
# GRAPH FUNCTIONS
# =========================
def create_signal_chart(df, column, title, color):
    fig = px.line(
        df,
        x="timestamp",
        y=column,
        markers=True,
        line_shape="spline",
        title=title
    )

    fig.update_traces(
        line=dict(color=color, width=4),
        marker=dict(size=7, color=color)
    )

    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "white"},
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        height=340
    )

    return fig


def create_gauge(value, title, suffix="", max_value=100):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title, "font": {"color": "white", "size": 18}},
            number={"suffix": suffix, "font": {"color": "white"}},
            gauge={
                "axis": {"range": [0, max_value], "tickcolor": "white"},
                "bar": {"color": "#38bdf8"},
                "bgcolor": "#0f172a",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, max_value * 0.6], "color": "rgba(239,68,68,0.35)"},
                    {"range": [max_value * 0.6, max_value * 0.8], "color": "rgba(250,204,21,0.35)"},
                    {"range": [max_value * 0.8, max_value], "color": "rgba(34,197,94,0.35)"},
                ],
            },
        )
    )

    fig.update_layout(
        height=260,
        paper_bgcolor="#0f172a",
        font={"color": "white"},
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return fig


def create_radar_chart(score, health_score, mold_score, severity_score):
    categories = ["Comfort", "AI Health", "Mold Safety", "Normality"]
    values = [
        score,
        health_score,
        100 - mold_score,
        100 - severity_score
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name="Room Health"
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#334155",
                tickfont=dict(color="white")
            ),
            angularaxis=dict(
                gridcolor="#334155",
                tickfont=dict(color="white")
            )
        ),
        showlegend=False,
        paper_bgcolor="#0f172a",
        font={"color": "white"},
        height=360,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig


def create_prediction_bar(pred_temp, pred_hum, temp_high, humidity_high):
    data = pd.DataFrame({
        "Metric": ["Predicted Temp", "Temp Threshold", "Predicted Humidity", "Humidity Threshold"],
        "Value": [
            pred_temp if pred_temp is not None else 0,
            temp_high,
            pred_hum if pred_hum is not None else 0,
            humidity_high
        ]
    })

    fig = px.bar(
        data,
        x="Metric",
        y="Value",
        title="Prediction vs Threshold"
    )

    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "white"},
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        height=330
    )

    return fig


def render_topology(temperature, humidity, health_score, device_status, temp_direction):
    topology_html = f"""
    <style>
    body {{
        margin: 0;
        background: transparent;
        font-family: Arial, sans-serif;
        color: white;
    }}

    .topology-card {{
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(56,189,248,0.35);
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 0 35px rgba(56,189,248,0.14);
    }}

    .network-topology {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 28px;
        flex-wrap: wrap;
    }}

    .topology-node {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }}

    .node-circle {{
        width: 74px;
        height: 74px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(2,6,23,0.9);
        border: 3px solid #38bdf8;
        box-shadow: 0 0 24px rgba(56,189,248,0.8);
        font-size: 28px;
        animation: pulseNode 2s infinite;
    }}

    @keyframes pulseNode {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.06); }}
        100% {{ transform: scale(1); }}
    }}

    .node-label {{
        font-size: 14px;
        font-weight: 800;
        color: #e0f2fe;
    }}

    .node-status {{
        font-size: 12px;
        color: #94a3b8;
    }}

    .connection-arrow {{
        font-size: 30px;
        color: #38bdf8;
    }}
    </style>

    <div class="topology-card">
        <div class="network-topology">

            <div class="topology-node">
                <div class="node-circle">📡</div>
                <div class="node-label">ESP8266</div>
                <div class="node-status">{device_status}</div>
            </div>

            <div class="connection-arrow">➜</div>

            <div class="topology-node">
                <div class="node-circle" style="border-color:#22c55e; box-shadow:0 0 24px rgba(34,197,94,0.8);">🌐</div>
                <div class="node-label">MQTT Broker</div>
                <div class="node-status">{temperature}°C | {humidity}%</div>
            </div>

            <div class="connection-arrow">➜</div>

            <div class="topology-node">
                <div class="node-circle" style="border-color:#facc15; box-shadow:0 0 24px rgba(250,204,21,0.8);">🔮</div>
                <div class="node-label">Prediction</div>
                <div class="node-status">{temp_direction}</div>
            </div>

            <div class="connection-arrow">➜</div>

            <div class="topology-node">
                <div class="node-circle" style="border-color:#a78bfa; box-shadow:0 0 24px rgba(167,139,250,0.8);">🧠</div>
                <div class="node-label">AI Core</div>
                <div class="node-status">{health_score}/100</div>
            </div>

        </div>
    </div>
    """

    components.html(topology_html, height=230)


# =========================
# DATA
# =========================
temperature = mqtt_data["temperature"]
humidity = mqtt_data["humidity"]
room = mqtt_data["room"]
last_update = mqtt_data["last_update"]

if temperature is None or humidity is None:
    st.markdown('<div class="os-title">🧠 Smart Building AI OS v5</div>', unsafe_allow_html=True)
    st.warning("Waiting for MQTT data from ESP8266...")
    st.stop()

temperature = round(float(temperature), 1)
humidity = round(float(humidity), 1)

score = comfort_score(temperature, humidity)

status = "OPTIMAL"
if score < 80:
    status = "ATTENTION REQUIRED"
if score < 60:
    status = "CRITICAL"

row = {
    "timestamp": datetime.now().strftime("%H:%M:%S"),
    "room": room,
    "temperature": temperature,
    "humidity": humidity,
    "comfort_score": score,
    "status": status,
    "last_update": last_update,
}

st.session_state.history.append(row)
history_df = pd.DataFrame(st.session_state.history)

pred_temp, temp_direction, temp_conf = predict_next(history_df, "temperature")
pred_hum, hum_direction, hum_conf = predict_next(history_df, "humidity")
ml_anomaly, ml_status = detect_ml_anomaly(history_df)
mold_level, mold_score = mold_risk_score(temperature, humidity)
comfort_suggestions = comfort_optimization(temperature, humidity)
estimated_occupancy = estimate_occupancy(history_df)

device_status, device_message = device_online_status(last_update)
severity_level, severity_score, severity_text = anomaly_severity(history_df, temperature, humidity)
health_score = building_health_score(score, mold_score, severity_score)
future_alerts = predictive_alert(pred_temp, pred_hum, temp_high, humidity_high)


# =========================
# HEADER
# =========================
left, right = st.columns([4, 1])

with left:
    st.markdown('<div class="os-title">🧠 Smart Building AI OS v5</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle"><span class="live-dot"></span>ESP8266 + MQTT + AI prediction + ML anomaly detection + live smart-building graphics</div>',
        unsafe_allow_html=True
    )

with right:
    st.markdown(
        f"""
        <div class="holo-card">
            <div class="holo-label">AI Core</div>
            <div class="holo-value" style="font-size:28px;">ONLINE</div>
            <div style="color:#94a3b8;">Last packet: {last_update}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# KPI CARDS
# =========================
k1, k2, k3, k4, k5 = st.columns(5)

k1.markdown(
    f'<div class="holo-card"><div class="holo-label">Temperature</div><div class="holo-value">{temperature}°C</div></div>',
    unsafe_allow_html=True
)

k2.markdown(
    f'<div class="holo-card"><div class="holo-label">Humidity</div><div class="holo-value">{humidity}%</div></div>',
    unsafe_allow_html=True
)

k3.markdown(
    f'<div class="holo-card"><div class="holo-label">Comfort Score</div><div class="holo-value">{score}/100</div></div>',
    unsafe_allow_html=True
)

k4.markdown(
    f'<div class="holo-card"><div class="holo-label">AI Health</div><div class="holo-value">{health_score}/100</div></div>',
    unsafe_allow_html=True
)

k5.markdown(
    f'<div class="holo-card"><div class="holo-label">Device</div><div class="holo-value" style="font-size:24px;">{device_status}</div></div>',
    unsafe_allow_html=True
)


# =========================
# LIVE GRAPHICS
# =========================
st.subheader("🎛️ Live Building Gauges")

g1, g2, g3 = st.columns(3)

with g1:
    st.plotly_chart(
        create_gauge(score, "Comfort Score", "/100", 100),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with g2:
    st.plotly_chart(
        create_gauge(health_score, "AI Health", "/100", 100),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with g3:
    st.plotly_chart(
        create_gauge(severity_score, "Anomaly Severity", "/100", 100),
        use_container_width=True,
        config={"displayModeBar": False}
    )


# =========================
# ENVIRONMENTAL INTELLIGENCE
# =========================
st.subheader("🧬 Environmental Intelligence Layer")

e1, e2, e3 = st.columns(3)

e1.markdown(
    f"""
    <div class="holo-card">
        <div class="holo-label">Mold Risk Prediction</div>
        <div class="holo-value">{mold_level}</div>
        <p>Risk Score: {mold_score}/100</p>
    </div>
    """,
    unsafe_allow_html=True
)

e2.markdown(
    f"""
    <div class="holo-card">
        <div class="holo-label">Estimated Occupancy</div>
        <div class="holo-value" style="font-size:24px;">{estimated_occupancy}</div>
        <p>Based on temperature/humidity movement</p>
    </div>
    """,
    unsafe_allow_html=True
)

e3.markdown(
    f"""
    <div class="holo-card">
        <div class="holo-label">Anomaly Severity</div>
        <div class="holo-value">{severity_level}</div>
        <p>Severity Score: {severity_score}/100</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# DIGITAL TWIN + MQTT STREAM
# =========================
left, right = st.columns([1.2, 1])

with left:
    st.subheader("🏠 3D Smart Room Digital Twin")
    st.markdown(
        f"""
        <div class="room3d">
            <div class="scanline"></div>
            <div class="energy-line e1"></div>
            <div class="energy-line e2"></div>
            <div class="energy-line e3"></div>
            <div class="sensor-node"></div>
            <div class="room-label">
                MQTT SENSOR NODE<br>
                {temperature}°C | {humidity}%<br>
                Status: {status}<br>
                Health: {health_score}/100
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with right:
    st.subheader("📡 Live MQTT Stream")
    st.markdown(
        f"""
        <div class="terminal">
        [MQTT] broker: {MQTT_BROKER}:1883<br>
        [TOPIC] {MQTT_TOPIC}<br>
        [PACKET] received at {last_update}<br>
        [DEVICE_STATUS] {device_status}<br>
        [TEMP] {temperature} °C<br>
        [HUMIDITY] {humidity} %<br>
        [AI_STATUS] {status}<br>
        [AI_HEALTH_SCORE] {health_score}/100<br>
        [ML_ANOMALY] {ml_status}<br>
        [ANOMALY_SEVERITY] {severity_level} - {severity_score}/100<br>
        [MOLD_RISK] {mold_level}<br>
        [OCCUPANCY_PROXY] {estimated_occupancy}<br>
        [PREDICTIVE_ALERTS] {len(future_alerts)} active<br>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# NEURAL TOPOLOGY
# =========================
st.subheader("🧬 Neural Network Topology")
render_topology(
    temperature=temperature,
    humidity=humidity,
    health_score=health_score,
    device_status=device_status,
    temp_direction=temp_direction
)


# =========================
# AI PREDICTION ENGINE
# =========================
st.subheader("🧠 AI Prediction Engine")

p1, p2 = st.columns(2)

p1.markdown(
    f"""
    <div class="holo-card">
        <div class="holo-label">Temperature Forecast</div>
        <div class="holo-value">{pred_temp if pred_temp else "--"}°C</div>
        <p>Direction: {temp_direction}</p>
        <p>Confidence: {temp_conf}%</p>
    </div>
    """,
    unsafe_allow_html=True
)

p2.markdown(
    f"""
    <div class="holo-card">
        <div class="holo-label">Humidity Forecast</div>
        <div class="holo-value">{pred_hum if pred_hum else "--"}%</div>
        <p>Direction: {hum_direction}</p>
        <p>Confidence: {hum_conf}%</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# EXTRA LIVE AI GRAPHICS
# =========================
st.subheader("📊 Live AI Graphics")

lg1, lg2 = st.columns(2)

with lg1:
    st.plotly_chart(
        create_radar_chart(score, health_score, mold_score, severity_score),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with lg2:
    st.plotly_chart(
        create_prediction_bar(pred_temp, pred_hum, temp_high, humidity_high),
        use_container_width=True,
        config={"displayModeBar": False}
    )


# =========================
# AI REASONING
# =========================
st.subheader("💡 AI Reasoning Engine")

if ml_anomaly:
    st.markdown(
        '<div class="ai-bad">🚨 ML anomaly detected. The latest environmental pattern differs from the recent baseline.</div>',
        unsafe_allow_html=True
    )

if mold_level == "HIGH":
    st.markdown(
        '<div class="ai-bad">🦠 High mold-risk conditions detected due to elevated humidity. Ventilation is recommended.</div>',
        unsafe_allow_html=True
    )
elif mold_level == "MODERATE":
    st.markdown(
        '<div class="ai-warn">⚠️ Moderate mold-risk trend. Keep monitoring humidity stability.</div>',
        unsafe_allow_html=True
    )

for suggestion in comfort_suggestions:
    if "optimal" in suggestion.lower():
        st.markdown(f'<div class="ai-good">✅ {suggestion}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-warn">🧠 {suggestion}</div>', unsafe_allow_html=True)


# =========================
# AI BUILDING DIAGNOSIS
# =========================
st.subheader("🧠 AI Building Diagnosis")

if severity_level == "CRITICAL":
    st.markdown(
        f'<div class="ai-bad">🚨 Critical anomaly severity: {severity_score}/100. {severity_text}</div>',
        unsafe_allow_html=True
    )
elif severity_level == "WARNING":
    st.markdown(
        f'<div class="ai-warn">⚠️ Anomaly warning: {severity_score}/100. {severity_text}</div>',
        unsafe_allow_html=True
    )
elif severity_level == "NORMAL":
    st.markdown(
        f'<div class="ai-good">✅ Normal behavior: {severity_score}/100. {severity_text}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="ai-warn">🧠 {severity_text}</div>',
        unsafe_allow_html=True
    )

for alert in future_alerts:
    if "No immediate" in alert:
        st.markdown(f'<div class="ai-good">✅ {alert}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-warn">📡 Predictive alert: {alert}</div>', unsafe_allow_html=True)


# =========================
# ROOM HEATMAP
# =========================
st.subheader("🔥 Room Heatmap")

h1, h2, h3, h4 = st.columns(4)

temp_color = "#22c55e" if temperature <= temp_high else "#ef4444"
hum_color = "#22c55e" if humidity <= humidity_high else "#ef4444"
mold_color = "#22c55e" if mold_level == "LOW" else "#facc15" if mold_level == "MODERATE" else "#ef4444"
health_color = "#22c55e" if health_score >= 80 else "#facc15" if health_score >= 60 else "#ef4444"

h1.markdown(
    f'<div class="heat-cell" style="background:{temp_color};">Temperature<br>{temperature}°C</div>',
    unsafe_allow_html=True
)

h2.markdown(
    f'<div class="heat-cell" style="background:{hum_color};">Humidity<br>{humidity}%</div>',
    unsafe_allow_html=True
)

h3.markdown(
    f'<div class="heat-cell" style="background:{mold_color};">Mold Risk<br>{mold_level}</div>',
    unsafe_allow_html=True
)

h4.markdown(
    f'<div class="heat-cell" style="background:{health_color};">AI Health<br>{health_score}/100</div>',
    unsafe_allow_html=True
)


# =========================
# TRENDS
# =========================
if len(history_df) > 1:
    st.subheader("📈 Neural Trend Analytics")

    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(
            create_signal_chart(history_df, "temperature", "Temperature Signal", "#f97316"),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    with c2:
        st.plotly_chart(
            create_signal_chart(history_df, "humidity", "Humidity Signal", "#0ea5e9"),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    st.subheader("📋 Telemetry Memory")
    st.dataframe(history_df.tail(30), use_container_width=True)
else:
    st.info("Collecting neural telemetry...")