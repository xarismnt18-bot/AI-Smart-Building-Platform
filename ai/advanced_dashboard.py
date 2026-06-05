"""
Smart Building AI Dashboard - Enterprise Edition
Advanced IoT monitoring with predictive analytics, recommendations, and floorplan visualization
"""
import random
import pandas as pd
import streamlit as st
from datetime import datetime
import joblib
import time
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.engines import PredictionEngine, RecommendationEngine, FloorplanGenerator
from ui.components import (
    render_metric_card, render_recommendation, render_health_score,
    render_prediction_card
)

# ==================== CONFIG ====================
OCCUPANCY_MODEL = "models/occupancy_model.pkl"
ANOMALY_MODEL = "models/anomaly_model.pkl"

occupancy_model = joblib.load(OCCUPANCY_MODEL)
anomaly_model = joblib.load(ANOMALY_MODEL)

# Initialize engines
prediction_engine = PredictionEngine(lookback_minutes=20)
recommendation_engine = RecommendationEngine()
floorplan_generator = FloorplanGenerator()

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Smart Building AI", layout="wide", initial_sidebar_state="expanded")

# ==================== ENTERPRISE STYLING ====================
st.markdown("""
<style>
/* Animations */
@keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.4), inset 0 0 20px rgba(59, 130, 246, 0.05); }
    50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.8), inset 0 0 30px rgba(59, 130, 246, 0.1); }
}

@keyframes float-animation {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

@keyframes blink {
    0%, 49%, 100% { opacity: 1; }
    50%, 99% { opacity: 0.3; }
}

@keyframes slide-in {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* Main styling */
.main {
    background: linear-gradient(135deg, #0f172a 0%, #1a1f2e 100%);
    background-attachment: fixed;
    position: relative;
}

/* Animated background particles */
.particle {
    position: fixed;
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
    filter: drop-shadow(0 0 20px currentColor);
}

.particle-1 {
    width: 8px;
    height: 8px;
    background: rgba(59, 130, 246, 0.6);
    top: 10%;
    left: 5%;
    animation: float-animation 8s ease-in-out infinite;
}

.particle-2 {
    width: 6px;
    height: 6px;
    background: rgba(34, 197, 94, 0.5);
    top: 20%;
    right: 10%;
    animation: float-animation 10s ease-in-out infinite;
}

.particle-3 {
    width: 5px;
    height: 5px;
    background: rgba(250, 204, 21, 0.5);
    bottom: 30%;
    left: 15%;
    animation: float-animation 12s ease-in-out infinite;
}

/* Title styling */
.big-title {
    font-size: 48px;
    font-weight: 900;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #3b82f6, #22c55e, #facc15, #f97316);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: glow-pulse 3s ease-in-out infinite;
    position: relative;
    z-index: 1;
}

.subtitle {
    color: #cbd5e1;
    font-size: 16px;
    margin-bottom: 30px;
    position: relative;
    z-index: 1;
    letter-spacing: 0.5px;
}

/* Status pill */
.status-pill {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(59, 130, 246, 0.3);
    animation: slide-in 0.5s ease-out;
}

.status-green { color: #22c55e; background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.3); }
.status-yellow { color: #facc15; background: rgba(250, 204, 21, 0.1); border-color: rgba(250, 204, 21, 0.3); }
.status-red { color: #ef4444; background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); }

/* Glassmorphism container */
.glass-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6));
    backdrop-filter: blur(20px);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-container:hover {
    border-color: rgba(59, 130, 246, 0.4);
    box-shadow: 0 8px 40px rgba(59, 130, 246, 0.15);
}

/* Subheader styling */
h2, h3 {
    color: #f1f5f9;
    font-weight: 700;
}

/* Alert animations */
.anomaly-blink {
    animation: blink 0.6s ease-in-out infinite;
}
</style>
""", unsafe_allow_html=True)

# Add background particles
st.markdown("""
<div class="particle particle-1"></div>
<div class="particle particle-2"></div>
<div class="particle particle-3"></div>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="big-title">🏢 Smart Building AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Enterprise IoT Monitoring & Predictive Analytics Platform</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="status-pill status-green">🟢 LIVE</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #64748b; font-size: 12px; margin-top: 10px;">Last update: {datetime.now().strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

st.divider()

# ==================== SIDEBAR ====================
st.sidebar.markdown("### ⚙️ Dashboard Controls")

refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 1, 10, 3)
selected_rooms = st.sidebar.multiselect("Monitor rooms", ["Main Office", "HR Office", "Conference Room", "Demo Room"], default=["Main Office", "HR Office", "Conference Room", "Demo Room"])

st.sidebar.markdown("### 📊 Thresholds")
co2_threshold = st.sidebar.slider("CO2 alert (ppm)", 600, 1500, 1000, 50)
temp_threshold = st.sidebar.slider("Temp alert (°C)", 20, 35, 27, 1)
humidity_threshold = st.sidebar.slider("Humidity alert (%)", 50, 90, 70, 5)
power_threshold = st.sidebar.slider("Power alert (W)", 500, 3000, 1200, 100)

# ==================== STATE INITIALIZATION ====================
if "history" not in st.session_state:
    st.session_state.history = []

# ==================== HELPER FUNCTIONS ====================
def generate_room_data(room):
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "room": room,
        "co2": random.randint(400, 1400),
        "temperature": round(random.uniform(18, 32), 1),
        "humidity": round(random.uniform(25, 75), 1),
        "power": round(random.uniform(50, 3000), 1)
    }

def detect_alerts(sensor_data, occupancy_status):
    alerts = []
    if occupancy_status == "Empty" and sensor_data["power"] > power_threshold:
        alerts.append("Energy waste detected")
    if occupancy_status == "Occupied" and sensor_data["co2"] > co2_threshold:
        alerts.append("Poor ventilation")
    if occupancy_status == "Occupied" and sensor_data["temperature"] > temp_threshold:
        alerts.append("High temperature")
    if sensor_data["humidity"] > humidity_threshold:
        alerts.append("High humidity")
    return alerts

# ==================== DATA COLLECTION ====================
current_rows = []

for room in selected_rooms:
    sensor_data = generate_room_data(room)
    model_input = pd.DataFrame([{"co2": sensor_data["co2"], "temperature": sensor_data["temperature"], "humidity": sensor_data["humidity"], "power": sensor_data["power"]}])
    
    prediction = occupancy_model.predict(model_input)[0]
    anomaly_prediction = anomaly_model.predict(model_input)[0]
    
    ml_anomaly_status = "Anomaly" if anomaly_prediction == -1 else "Normal"
    occupancy_status = "Occupied" if prediction == 1 else "Empty"
    alerts = detect_alerts(sensor_data, occupancy_status)
    
    sensor_data["occupancy"] = occupancy_status
    sensor_data["alerts"] = len(alerts)
    sensor_data["ml_status"] = ml_anomaly_status
    sensor_data["alert_text"] = " | ".join(alerts) if alerts else "No issues"
    
    current_rows.append(sensor_data)
    st.session_state.history.append(sensor_data)

current_df = pd.DataFrame(current_rows)
history_df = pd.DataFrame(st.session_state.history)

# ==================== TAB INTERFACE ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏢 Floorplan", 
    "🔮 Predictions", 
    "💡 Recommendations",
    "📊 Analytics",
    "📋 Details"
])

# ==================== TAB 1: FLOORPLAN ====================
with tab1:
    st.markdown("### Live Building Status")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        floorplan_fig = floorplan_generator.create_floorplan(current_df)
        if floorplan_fig:
            st.plotly_chart(floorplan_fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        building_overview = floorplan_generator.create_building_overview(current_df, history_df)
        render_health_score(building_overview['health_score'])
        st.markdown("---")
        st.markdown(f"**Total Rooms:** {building_overview['total_rooms']}")
        st.markdown(f"**Occupied:** {building_overview['occupancy_rate']}")
        st.markdown(f"**Alerts:** {building_overview['critical_alerts']}")
        st.markdown(f"**Anomalies:** {building_overview['anomalies']}")
    
    st.markdown("---")
    
    # Building metrics
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Avg CO2", f"{building_overview['avg_co2']} ppm", 'info')
    with metric_cols[1]:
        render_metric_card("Total Power", f"{building_overview['total_power']} W", 'warning')
    with metric_cols[2]:
        render_metric_card("Occupancy", building_overview['occupancy_rate'], 'success')
    with metric_cols[3]:
        render_metric_card("Health", f"{building_overview['health_score']}/100", 'success')

# ==================== TAB 2: PREDICTIONS ====================
with tab2:
    st.markdown("### 🔮 AI Predictions (Next 10 Minutes)")
    
    prediction_room = st.selectbox("Select room for predictions", selected_rooms, key="pred_room")
    
    room_data = current_df[current_df['room'] == prediction_room]
    if not room_data.empty:
        room_info = room_data.iloc[0]
        predictions = prediction_engine.get_all_predictions(st.session_state.history, prediction_room, minutes_ahead=10)
        
        # Metric predictions
        pred_cols = st.columns(4)
        with pred_cols[0]:
            render_prediction_card('co2', predictions['co2'])
        with pred_cols[1]:
            render_prediction_card('temperature', predictions['temperature'])
        with pred_cols[2]:
            render_prediction_card('humidity', predictions['humidity'])
        with pred_cols[3]:
            render_prediction_card('power', predictions['power'])
        
        st.markdown("---")
        
        # Occupancy prediction
        st.markdown("### Occupancy Forecast")
        occ_pred = predictions['occupancy']
        st.info(f"{occ_pred['trend']} (Confidence: {occ_pred['confidence']}%)")
        
        # Prediction insights
        st.markdown("### 📈 Trend Analysis")
        insights = []
        if predictions['co2'].get('slope', 0) > 5:
            insights.append("⚠️ CO2 is rising rapidly - Consider ventilation improvements")
        if predictions['temperature'].get('trend') == '📈 Rising':
            insights.append("🌡️ Temperature expected to increase - Prepare cooling systems")
        if predictions['power'].get('trend') == '📈 Rising' and room_info['occupancy'] == 'Empty':
            insights.append("⚡ Power usage increasing while empty - Investigate for anomalies")
        
        for insight in insights:
            st.warning(insight)

# ==================== TAB 3: RECOMMENDATIONS ====================
with tab3:
    st.markdown("### 💡 Smart Recommendations")
    
    rec_room = st.selectbox("Select room for recommendations", selected_rooms, key="rec_room")
    
    room_data = current_df[current_df['room'] == rec_room]
    if not room_data.empty:
        room_info = room_data.iloc[0]
        predictions = prediction_engine.get_all_predictions(st.session_state.history, rec_room, minutes_ahead=10)
        
        recommendations = recommendation_engine.generate_recommendations(
            room_info.to_dict(),
            predictions,
            room_info['ml_status']
        )
        
        if recommendations:
            for rec in recommendations:
                render_recommendation(
                    rec['priority'],
                    rec['title'],
                    rec['message'],
                    rec['action'],
                    rec['icon'],
                    rec['color']
                )
        else:
            st.success("✨ No recommendations - Room operating optimally!")

# ==================== TAB 4: ANALYTICS ====================
with tab4:
    st.markdown("### 📊 Room Analytics")
    
    analytics_room = st.selectbox("Select room to analyze", selected_rooms, key="analytics_room")
    
    room_history = history_df[history_df["room"] == analytics_room]
    
    if not room_history.empty:
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            st.markdown("**CO2 Trend**")
            fig = px.line(room_history, x='timestamp', y='co2', markers=True, line_shape='spline')
            fig.update_layout(paper_bgcolor='#0f172a', plot_bgcolor='#0f172a', font={'color': '#fff'}, height=300)
            fig.update_traces(line=dict(color='#ef4444', width=2), marker=dict(size=4))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with chart_cols[1]:
            st.markdown("**Temperature Trend**")
            fig = px.line(room_history, x='timestamp', y='temperature', markers=True, line_shape='spline')
            fig.update_layout(paper_bgcolor='#0f172a', plot_bgcolor='#0f172a', font={'color': '#fff'}, height=300)
            fig.update_traces(line=dict(color='#facc15', width=2), marker=dict(size=4))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        chart_cols2 = st.columns(2)
        
        with chart_cols2[0]:
            st.markdown("**Humidity Trend**")
            fig = px.line(room_history, x='timestamp', y='humidity', markers=True, line_shape='spline')
            fig.update_layout(paper_bgcolor='#0f172a', plot_bgcolor='#0f172a', font={'color': '#fff'}, height=300)
            fig.update_traces(line=dict(color='#0ea5e9', width=2), marker=dict(size=4))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with chart_cols2[1]:
            st.markdown("**Power Consumption**")
            fig = px.line(room_history, x='timestamp', y='power', markers=True, line_shape='spline')
            fig.update_layout(paper_bgcolor='#0f172a', plot_bgcolor='#0f172a', font={'color': '#fff'}, height=300)
            fig.update_traces(line=dict(color='#f97316', width=2), marker=dict(size=4))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==================== TAB 5: DETAILS ====================
with tab5:
    st.markdown("### 📋 Real-Time Room Details")
    
    for _, row in current_df.iterrows():
        with st.expander(f"🏢 {row['room']} - {row['occupancy']}", expanded=False):
            detail_cols = st.columns(4)
            
            with detail_cols[0]:
                st.metric("CO2", f"{row['co2']} ppm", delta=None)
            with detail_cols[1]:
                st.metric("Temp", f"{row['temperature']}°C", delta=None)
            with detail_cols[2]:
                st.metric("Humidity", f"{row['humidity']}%", delta=None)
            with detail_cols[3]:
                st.metric("Power", f"{row['power']} W", delta=None)
            
            st.markdown("---")
            
            alert_status = "✅ Normal" if row['alerts'] == 0 else f"⚠️ {row['alerts']} Alert(s)"
            ml_status = "🟢 Normal" if row['ml_status'] == "Normal" else "🔴 Anomaly"
            
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Occupancy:** {row['occupancy']}")
            col2.write(f"**Status:** {alert_status}")
            col3.write(f"**ML:** {ml_status}")
            
            if row['alerts'] > 0:
                st.warning(f"Alerts: {row['alert_text']}")

# ==================== AUTO REFRESH ====================
time.sleep(refresh_rate)
st.rerun()
