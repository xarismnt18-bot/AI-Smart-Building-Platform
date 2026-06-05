import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import paho.mqtt.client as mqtt


MQTT_BROKER = "192.168.1.143"  # IP ΥΠΟΛΟΓΙΣΤΗ
MQTT_PORT = 1883
MQTT_TOPIC = "smartroom/dht11"


st.set_page_config(
    page_title="Smart Room AI MQTT",
    page_icon="🌡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #111827 100%);
}

.big-title {
    font-size: 46px;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #22c55e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #cbd5e1;
    font-size: 18px;
    margin-bottom: 25px;
}

.live-dot {
    height: 12px;
    width: 12px;
    background-color: #22c55e;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    box-shadow: 0 0 15px #22c55e;
}
</style>
""", unsafe_allow_html=True)


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
            print("MQTT message error:", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    return shared_data


mqtt_data = start_mqtt_client()


st.sidebar.title("⚙️ Controls")

refresh_rate = st.sidebar.slider(
    "Dashboard refresh rate (seconds)",
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

temp_low = st.sidebar.slider(
    "Low temperature threshold (°C)",
    min_value=5,
    max_value=22,
    value=18
)

humidity_high = st.sidebar.slider(
    "High humidity threshold (%)",
    min_value=50,
    max_value=90,
    value=70
)

humidity_low = st.sidebar.slider(
    "Low humidity threshold (%)",
    min_value=10,
    max_value=50,
    value=35
)

if st.sidebar.button("Clear history"):
    st.session_state.history = []
    st.rerun()


st_autorefresh(
    interval=refresh_rate * 1000,
    key="mqtt_dashboard_refresh"
)


st.markdown('<div class="big-title">🌡️ Smart Room AI MQTT Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle"><span class="live-dot"></span>Live MQTT monitoring from ESP8266 + DHT11</div>',
    unsafe_allow_html=True
)


temperature = mqtt_data["temperature"]
humidity = mqtt_data["humidity"]
room = mqtt_data["room"]
last_update = mqtt_data["last_update"]


if temperature is None or humidity is None:
    st.warning("Waiting for MQTT data from ESP8266...")
    st.stop()


temperature = round(temperature, 1)
humidity = round(humidity, 1)


alerts = []

if temperature > temp_high:
    alerts.append("High temperature detected.")
elif temperature < temp_low:
    alerts.append("Low temperature detected.")

if humidity > humidity_high:
    alerts.append("High humidity detected.")
elif humidity < humidity_low:
    alerts.append("Low humidity detected.")


if len(alerts) == 0:
    comfort_status = "Comfortable"
    comfort_score = 95
elif len(alerts) == 1:
    comfort_status = "Attention Needed"
    comfort_score = 70
else:
    comfort_status = "Uncomfortable"
    comfort_score = 45


row = {
    "timestamp": datetime.now().strftime("%H:%M:%S"),
    "room": room,
    "temperature": temperature,
    "humidity": humidity,
    "comfort_status": comfort_status,
    "comfort_score": comfort_score,
    "alerts": len(alerts),
    "alert_text": " | ".join(alerts) if alerts else "No alerts",
    "source": "MQTT / ESP8266",
    "last_update": last_update
}

st.session_state.history.append(row)
history_df = pd.DataFrame(st.session_state.history)


st.success(f"🟢 Connected through MQTT | Last ESP update: {last_update}")


st.subheader(f"🏠 {room} - Live Status")


def create_gauge(value, title, max_value, zones):
    fig = go.Figure(data=[go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 22}},
        gauge={
            "axis": {"range": [0, max_value]},
            "bar": {"color": "#38bdf8"},
            "bgcolor": "#0f172a",
            "borderwidth": 2,
            "bordercolor": "#334155",
            "steps": zones,
        },
        number={"font": {"size": 36, "color": "white"}}
    )])

    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "white"},
        height=320,
        margin=dict(l=20, r=20, t=70, b=20)
    )

    return fig


col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(
        create_gauge(
            temperature,
            "Temperature (°C)",
            40,
            [
                {"range": [0, temp_low], "color": "#38bdf8"},
                {"range": [temp_low, temp_high], "color": "#22c55e"},
                {"range": [temp_high, 40], "color": "#ef4444"},
            ]
        ),
        use_container_width=True,
        config={"displayModeBar": False}
    )

with col2:
    st.plotly_chart(
        create_gauge(
            humidity,
            "Humidity (%)",
            100,
            [
                {"range": [0, humidity_low], "color": "#facc15"},
                {"range": [humidity_low, humidity_high], "color": "#22c55e"},
                {"range": [humidity_high, 100], "color": "#ef4444"},
            ]
        ),
        use_container_width=True,
        config={"displayModeBar": False}
    )


k1, k2, k3, k4 = st.columns(4)

k1.metric("Temperature", f"{temperature} °C")
k2.metric("Humidity", f"{humidity} %")
k3.metric("Comfort Status", comfort_status)
k4.metric("Comfort Score", f"{comfort_score}/100")


if alerts:
    st.error("🚨 " + " | ".join(alerts))
else:
    st.success("✅ Room conditions are normal.")


st.divider()

st.subheader("💡 Smart Recommendations")

if temperature > temp_high:
    st.warning("🌡️ Temperature is high. Consider opening a window or increasing cooling.")
elif temperature < temp_low:
    st.warning("❄️ Temperature is low. Consider heating the room.")

if humidity > humidity_high:
    st.warning("💧 Humidity is high. Consider ventilation or dehumidification.")
elif humidity < humidity_low:
    st.warning("🏜️ Humidity is low. Consider humidification.")

if not alerts:
    st.success("✅ No action required. The room is within comfort range.")


st.divider()

st.subheader("📈 Historical Trends")

if len(history_df) > 1:
    c1, c2 = st.columns(2)

    with c1:
        fig_temp = px.line(
            history_df,
            x="timestamp",
            y="temperature",
            title="Temperature Trend",
            markers=True,
            line_shape="spline"
        )

        fig_temp.update_traces(line=dict(color="#f97316", width=3))
        fig_temp.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font={"color": "white"},
            xaxis=dict(gridcolor="#334155"),
            yaxis=dict(gridcolor="#334155"),
            height=340
        )

        st.plotly_chart(fig_temp, use_container_width=True, config={"displayModeBar": False})

    with c2:
        fig_hum = px.line(
            history_df,
            x="timestamp",
            y="humidity",
            title="Humidity Trend",
            markers=True,
            line_shape="spline"
        )

        fig_hum.update_traces(line=dict(color="#0ea5e9", width=3))
        fig_hum.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font={"color": "white"},
            xaxis=dict(gridcolor="#334155"),
            yaxis=dict(gridcolor="#334155"),
            height=340
        )

        st.plotly_chart(fig_hum, use_container_width=True, config={"displayModeBar": False})

    st.subheader("📋 Recent MQTT Readings")

    st.dataframe(
        history_df.tail(30)[
            [
                "timestamp",
                "room",
                "temperature",
                "humidity",
                "comfort_status",
                "comfort_score",
                "alert_text",
                "source",
                "last_update"
            ]
        ],
        use_container_width=True
    )

else:
    st.info("Collecting MQTT readings...")