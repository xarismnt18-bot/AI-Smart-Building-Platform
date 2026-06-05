import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
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
    page_title="Smart Building AI OS",
    page_icon="🧠",
    layout="wide"
)


# =========================
# FUTURISTIC CSS
# =========================
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 15% 20%, rgba(56,189,248,0.20), transparent 30%),
        radial-gradient(circle at 85% 10%, rgba(34,197,94,0.14), transparent 25%),
        radial-gradient(circle at 50% 90%, rgba(168,85,247,0.12), transparent 30%),
        linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%);
    color: white;
}

.block-container {
    padding-top: 2rem;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.6); }
    70% { box-shadow: 0 0 0 14px rgba(34,197,94,0); }
    100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

@keyframes glow {
    0%, 100% { filter: drop-shadow(0 0 8px rgba(56,189,248,0.6)); }
    50% { filter: drop-shadow(0 0 22px rgba(56,189,248,1)); }
}

.os-title {
    font-size: 54px;
    font-weight: 900;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #38bdf8, #22c55e, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 3s infinite ease-in-out;
}

.os-subtitle {
    color: #cbd5e1;
    font-size: 18px;
    margin-bottom: 25px;
}

.glass-card {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(56,189,248,0.22);
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    backdrop-filter: blur(12px);
    margin-bottom: 20px;
}

.ai-core {
    border: 1px solid rgba(34,197,94,0.4);
    background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(6,78,59,0.22));
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

.neon-label {
    color: #94a3b8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
}

.neon-value {
    font-size: 36px;
    font-weight: 800;
    color: #f8fafc;
}

.room-hologram {
    height: 320px;
    border: 2px solid rgba(56,189,248,0.35);
    border-radius: 24px;
    background:
        linear-gradient(rgba(56,189,248,0.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(56,189,248,0.07) 1px, transparent 1px),
        rgba(15,23,42,0.75);
    background-size: 34px 34px;
    position: relative;
    overflow: hidden;
}

.sensor-node {
    position: absolute;
    top: 42%;
    left: 46%;
    width: 54px;
    height: 54px;
    background: radial-gradient(circle, #22c55e, #0f766e);
    border-radius: 50%;
    box-shadow: 0 0 35px rgba(34,197,94,0.9);
    animation: pulse 2s infinite;
}

.sensor-label {
    position: absolute;
    top: 60%;
    left: 38%;
    color: #e0f2fe;
    font-weight: 700;
    text-align: center;
}

.airflow {
    position: absolute;
    width: 160px;
    height: 4px;
    background: linear-gradient(90deg, transparent, #38bdf8, transparent);
    opacity: 0.7;
    animation: glow 2s infinite;
}

.airflow.a1 { top: 25%; left: 12%; }
.airflow.a2 { top: 45%; right: 12%; }
.airflow.a3 { bottom: 22%; left: 30%; }

.terminal-box {
    background: #020617;
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 18px;
    padding: 18px;
    color: #22c55e;
    font-family: Consolas, monospace;
    font-size: 14px;
}

.alert-good {
    background: rgba(34,197,94,0.15);
    border-left: 5px solid #22c55e;
    padding: 14px;
    border-radius: 12px;
}

.alert-warning {
    background: rgba(250,204,21,0.15);
    border-left: 5px solid #facc15;
    padding: 14px;
    border-radius: 12px;
}

.alert-danger {
    background: rgba(239,68,68,0.15);
    border-left: 5px solid #ef4444;
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# SESSION STATE
# =========================
if "latest_data" not in st.session_state:
    st.session_state.latest_data = {
        "room": "My Room",
        "temperature": None,
        "humidity": None,
        "connected": False,
        "last_update": None
    }

if "history" not in st.session_state:
    st.session_state.history = []


# =========================
# MQTT CLIENT
# =========================
@st.cache_resource
def start_mqtt_client():
    shared_data = {
        "room": "My Room",
        "temperature": None,
        "humidity": None,
        "connected": False,
        "last_update": None
    }

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            shared_data["connected"] = True
            client.subscribe(MQTT_TOPIC)
        else:
            shared_data["connected"] = False

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())

            shared_data["room"] = payload.get("room", "My Room")
            shared_data["temperature"] = float(payload["temperature"])
            shared_data["humidity"] = float(payload["humidity"])
            shared_data["connected"] = True
            shared_data["last_update"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print("MQTT error:", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    return shared_data


mqtt_data = start_mqtt_client()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ AI OS Controls")

refresh_rate = st.sidebar.slider(
    "Refresh rate (seconds)",
    min_value=2,
    max_value=15,
    value=3
)

temp_high = st.sidebar.slider(
    "High temperature threshold (°C)",
    min_value=20,
    max_value=35,
    value=27
)

humidity_high = st.sidebar.slider(
    "High humidity threshold (%)",
    min_value=50,
    max_value=90,
    value=70
)

if st.sidebar.button("Clear history"):
    st.session_state.history = []
    st.rerun()


st_autorefresh(
    interval=refresh_rate * 1000,
    key="futuristic_ai_os_refresh"
)


# =========================
# HELPERS
# =========================
def comfort_score(temp, humidity):
    score = 100

    if temp > temp_high:
        score -= min((temp - temp_high) * 8, 35)

    if humidity > humidity_high:
        score -= min((humidity - humidity_high) * 4, 35)

    return max(int(score), 20)


def status_level(temp, humidity):
    if temp > temp_high or humidity > humidity_high:
        return "ATTENTION REQUIRED"
    return "OPTIMAL"


def create_radial(value, title, max_value, color):
    fig = go.Figure(data=[go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 22}},
        gauge={
            "axis": {"range": [0, max_value]},
            "bar": {"color": color},
            "bgcolor": "#0f172a",
            "bordercolor": "#334155",
            "borderwidth": 2,
        },
        number={"font": {"size": 34, "color": "white"}}
    )])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=310,
        margin=dict(l=20, r=20, t=70, b=20)
    )

    return fig


def create_trend(df, column, title, color):
    fig = px.line(
        df,
        x="timestamp",
        y=column,
        title=title,
        markers=True,
        line_shape="spline"
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


# =========================
# DATA
# =========================
temperature = mqtt_data["temperature"]
humidity = mqtt_data["humidity"]
last_update = mqtt_data["last_update"]
room = mqtt_data["room"]

if temperature is None or humidity is None:
    st.markdown('<div class="os-title">🧠 Smart Building AI OS</div>', unsafe_allow_html=True)
    st.warning("Waiting for MQTT data from ESP8266...")
    st.stop()

temperature = round(float(temperature), 1)
humidity = round(float(humidity), 1)
score = comfort_score(temperature, humidity)
level = status_level(temperature, humidity)

alerts = []

if temperature > temp_high:
    alerts.append("Temperature above comfort threshold.")

if humidity > humidity_high:
    alerts.append("Humidity above comfort threshold.")

if not alerts:
    alerts.append("Environment stable. No action required.")

row = {
    "timestamp": datetime.now().strftime("%H:%M:%S"),
    "room": room,
    "temperature": temperature,
    "humidity": humidity,
    "comfort_score": score,
    "status": level,
    "last_update": last_update
}

st.session_state.history.append(row)
history_df = pd.DataFrame(st.session_state.history)


# =========================
# HEADER
# =========================
left, right = st.columns([4, 1])

with left:
    st.markdown('<div class="os-title">🧠 Smart Building AI OS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="os-subtitle"><span class="live-dot"></span>ESP8266 + MQTT + AI environmental intelligence layer</div>',
        unsafe_allow_html=True
    )

with right:
    st.markdown(
        f"""
        <div class="glass-card ai-core">
            <div class="neon-label">AI Core</div>
            <div class="neon-value">ONLINE</div>
            <div style="color:#94a3b8;">Last packet: {last_update}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# TOP KPI CARDS
# =========================
k1, k2, k3, k4 = st.columns(4)

k1.markdown(f"""
<div class="glass-card">
    <div class="neon-label">Temperature</div>
    <div class="neon-value">{temperature}°C</div>
</div>
""", unsafe_allow_html=True)

k2.markdown(f"""
<div class="glass-card">
    <div class="neon-label">Humidity</div>
    <div class="neon-value">{humidity}%</div>
</div>
""", unsafe_allow_html=True)

k3.markdown(f"""
<div class="glass-card">
    <div class="neon-label">Comfort Score</div>
    <div class="neon-value">{score}/100</div>
</div>
""", unsafe_allow_html=True)

k4.markdown(f"""
<div class="glass-card">
    <div class="neon-label">Room Status</div>
    <div class="neon-value" style="font-size:25px;">{level}</div>
</div>
""", unsafe_allow_html=True)


# =========================
# MAIN OS VIEW
# =========================
left, right = st.columns([1.2, 1])

with left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🏠 Live Room Hologram")

    st.markdown(f"""
    <div class="room-hologram">
        <div class="airflow a1"></div>
        <div class="airflow a2"></div>
        <div class="airflow a3"></div>
        <div class="sensor-node"></div>
        <div class="sensor-label">
            MQTT SENSOR NODE<br>
            {temperature}°C | {humidity}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📡 Live MQTT Stream")

    st.markdown(f"""
    <div class="terminal-box">
    [MQTT] broker: {MQTT_BROKER}:1883<br>
    [TOPIC] {MQTT_TOPIC}<br>
    [PACKET] received at {last_update}<br>
    [TEMP] {temperature} °C<br>
    [HUMIDITY] {humidity} %<br>
    [STATUS] {level}<br>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# GAUGES
# =========================
g1, g2 = st.columns(2)

with g1:
    st.plotly_chart(
        create_radial(temperature, "Temperature Reactor", 40, "#38bdf8"),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with g2:
    st.plotly_chart(
        create_radial(humidity, "Humidity Matrix", 100, "#22c55e"),
        use_container_width=True,
        config={"displayModeBar": False}
    )


# =========================
# AI ANALYSIS
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("💡 AI Recommendation Engine")

if level == "OPTIMAL":
    st.markdown(
        '<div class="alert-good">✅ Environment stable. Comfort conditions are currently optimal.</div>',
        unsafe_allow_html=True
    )
else:
    for alert in alerts:
        st.markdown(
            f'<div class="alert-warning">⚠️ {alert} Suggested action: improve ventilation or adjust room conditions.</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# HISTORICAL TRENDS
# =========================
if len(history_df) > 1:
    st.subheader("📈 Neural Trend Analytics")

    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(
            create_trend(history_df, "temperature", "Temperature Signal", "#f97316"),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    with c2:
        st.plotly_chart(
            create_trend(history_df, "humidity", "Humidity Signal", "#0ea5e9"),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    st.subheader("📋 Telemetry Memory")

    st.dataframe(
        history_df.tail(30),
        use_container_width=True
    )
else:
    st.info("Collecting neural telemetry...")