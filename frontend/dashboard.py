import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# =========================
# CONFIG
# =========================
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Smart Building AI OS v6",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SESSION STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "DASHBOARD"

# =========================
# CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

/* ── HIDE DEFAULT STREAMLIT CHROME (black top bar) ── */
#MainMenu                              { visibility: hidden !important; }
header[data-testid="stHeader"]        { display: none !important; height: 0 !important; }
footer                                 { visibility: hidden !important; }
.stDeployButton                        { display: none !important; }
div[data-testid="stToolbar"]           { display: none !important; }
div[data-testid="stDecoration"]        { display: none !important; }
div[data-testid="stStatusWidget"]      { display: none !important; }

/* Remove top-padding leftover from hidden header */
.appview-container .main .block-container { padding-top: 0.8rem !important; }
.block-container { padding-top: 0.8rem !important; padding-bottom: 1rem !important; }

/* ── ROOT BACKGROUND ── */
.stApp {
    background:
        radial-gradient(ellipse at top left,  rgba(0,212,255,0.12) 0%, transparent 45%),
        radial-gradient(ellipse at top right, rgba(120,40,200,0.14) 0%, transparent 45%),
        radial-gradient(ellipse at bottom,    rgba(0,80,160,0.10)  0%, transparent 55%),
        linear-gradient(160deg, #010b1a 0%, #040d20 50%, #010b1a 100%);
    color: #e2f4ff;
    font-family: 'Rajdhani', sans-serif;
    overflow-x: hidden;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020e22 0%, #030f25 100%) !important;
    border-right: 1px solid rgba(0,212,255,0.2) !important;
}
[data-testid="stSidebarContent"] { padding-top: 0 !important; }
[data-testid="stSidebar"] * { font-family: 'Rajdhani', sans-serif !important; }

/* Nav buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    padding: 9px 14px !important;
    text-align: left !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    color: #7a9ab5 !important;
    transition: all 0.2s !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(0,212,255,0.07) !important;
    color: #00d4ff !important;
    border-color: rgba(0,212,255,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(0,212,255,0.12) !important;
    border: 1px solid rgba(0,212,255,0.35) !important;
    color: #00d4ff !important;
}

/* ── PARTICLES ── */
@keyframes floatA { 0%,100%{transform:translateY(0);}  50%{transform:translateY(-18px);} }
@keyframes floatB { 0%,100%{transform:translateY(0);}  50%{transform:translateY(-12px);} }
.particle { position:fixed; border-radius:50%; opacity:0.4; z-index:0; pointer-events:none; }
.p1{width:8px;height:8px;background:#00d4ff;top:8%;left:12%;animation:floatA 6s infinite ease-in-out;}
.p2{width:5px;height:5px;background:#22c55e;top:18%;left:88%;animation:floatB 4s infinite ease-in-out 1s;}
.p3{width:10px;height:10px;background:#a855f7;top:72%;left:22%;animation:floatA 7s infinite ease-in-out 2s;}
.p4{width:7px;height:7px;background:#f59e0b;top:82%;left:78%;animation:floatB 5s infinite ease-in-out 0.5s;}
.p5{width:6px;height:6px;background:#00d4ff;top:45%;left:5%;animation:floatA 8s infinite ease-in-out 3s;}
.p6{width:4px;height:4px;background:#f472b6;top:55%;left:95%;animation:floatB 6s infinite ease-in-out 1.5s;}

/* ── TYPOGRAPHY ── */
.os-brand { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; letter-spacing:4px; color:#00d4ff; margin-bottom:2px; }
.os-title {
    font-family:'Orbitron',monospace; font-size:34px; font-weight:900;
    background:linear-gradient(90deg,#00d4ff 0%,#22c55e 40%,#a855f7 80%,#00d4ff 100%);
    background-size:200% auto; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    animation:shimmer 4s linear infinite; line-height:1.1;
}
@keyframes shimmer { 0%{background-position:0% center;} 100%{background-position:200% center;} }
.os-subtitle { font-family:'Share Tech Mono',monospace; font-size:12px; color:#22c55e; letter-spacing:2px; margin-top:4px; }
.page-hero   { font-family:'Orbitron',monospace; font-size:26px; font-weight:900; color:#00d4ff; letter-spacing:4px; margin-bottom:6px; }
.page-desc   { font-family:'Share Tech Mono',monospace; font-size:12px; color:#4a7a94; letter-spacing:2px; }
.section-header { font-family:'Orbitron',monospace; font-size:13px; font-weight:700; letter-spacing:3px; color:#00d4ff; text-transform:uppercase; border-bottom:1px solid rgba(0,212,255,0.2); padding-bottom:8px; margin-bottom:16px; margin-top:8px; }

/* ── HOLO CARDS ── */
.holo-card {
    background:rgba(1,16,40,0.75); border:1px solid rgba(0,212,255,0.3); border-radius:16px;
    padding:18px 22px; backdrop-filter:blur(18px);
    box-shadow:0 0 30px rgba(0,212,255,0.10), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom:16px; transition:transform 0.25s, box-shadow 0.25s; position:relative; overflow:hidden;
}
.holo-card::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(0,212,255,0.6),transparent); }
.holo-card:hover { transform:translateY(-3px); box-shadow:0 0 50px rgba(0,212,255,0.22); }

/* ── KPI ── */
.kpi-label { font-family:'Share Tech Mono',monospace; font-size:10px; letter-spacing:3px; color:#64a0b8; text-transform:uppercase; margin-bottom:6px; }
.kpi-value { font-family:'Orbitron',monospace; font-size:30px; font-weight:900; color:#00d4ff; line-height:1; }
.kpi-value-green{color:#22c55e;} .kpi-value-amber{color:#f59e0b;} .kpi-value-red{color:#ef4444;} .kpi-value-purple{color:#a855f7;}
.kpi-sub { font-size:11px; color:#4a7a94; margin-top:4px; font-family:'Share Tech Mono',monospace; }
.spark { height:26px; background:linear-gradient(90deg,#00d4ff22,#00d4ff); border-radius:4px; margin-top:6px; position:relative; overflow:hidden; }
.spark::after { content:''; position:absolute; inset:0; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent); animation:sparkle 2s infinite; }
@keyframes sparkle { 0%{left:-100%;} 100%{left:100%;} }

/* ── BADGES ── */
.badge-online  { display:inline-block; background:rgba(34,197,94,0.15);  border:1px solid #22c55e; color:#22c55e; font-family:'Orbitron',monospace; font-size:10px; font-weight:700; letter-spacing:2px; padding:3px 10px; border-radius:20px; }
.badge-offline { display:inline-block; background:rgba(239,68,68,0.15);  border:1px solid #ef4444; color:#ef4444; font-family:'Orbitron',monospace; font-size:10px; font-weight:700; letter-spacing:2px; padding:3px 10px; border-radius:20px; }
.live-dot { display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%; box-shadow:0 0 10px #22c55e; animation:blink 1.2s infinite; margin-right:6px; }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }

/* ── DIGITAL TWIN ── */
.twin-floor {
    height:280px; border-radius:18px; position:relative; overflow:hidden;
    background: linear-gradient(rgba(0,212,255,0.06) 1px,transparent 1px), linear-gradient(90deg,rgba(0,212,255,0.06) 1px,transparent 1px), rgba(1,10,25,0.85);
    background-size:28px 28px; border:1px solid rgba(0,212,255,0.3);
}
.twin-scan { position:absolute; width:200px; height:100%; background:linear-gradient(90deg,transparent,rgba(0,212,255,0.18),transparent); animation:scanX 3.5s linear infinite; z-index:2; }
@keyframes scanX { 0%{left:-20%;} 100%{left:120%;} }
.twin-sensor-main { position:absolute; top:38%; left:44%; width:64px; height:64px; border-radius:50%; background:radial-gradient(circle,#00d4ff,#0369a1); box-shadow:0 0 50px rgba(0,212,255,0.9),0 0 100px rgba(0,212,255,0.4); animation:pulseB 2.2s infinite ease-in-out; z-index:3; }
.twin-sensor-alt  { position:absolute; width:36px; height:36px; border-radius:50%; background:radial-gradient(circle,#22c55e,#14532d); box-shadow:0 0 25px rgba(34,197,94,0.8); animation:pulseG 3s infinite ease-in-out; z-index:3; }
@keyframes pulseB { 0%,100%{transform:scale(1);} 50%{transform:scale(1.12);} }
@keyframes pulseG { 0%,100%{transform:scale(1);} 50%{transform:scale(1.08);} }
.twin-ring { position:absolute; border-radius:50%; border:1px solid rgba(0,212,255,0.25); animation:ringP 3s infinite ease-out; }
@keyframes ringP { 0%{transform:scale(0.8);opacity:0.8;} 100%{transform:scale(2.2);opacity:0;} }
.room-label { position:absolute; background:rgba(0,20,50,0.85); border:1px solid rgba(0,212,255,0.4); border-radius:8px; padding:5px 10px; font-family:'Share Tech Mono',monospace; font-size:10px; color:#00d4ff; z-index:4; }

/* ── TERMINAL ── */
.terminal { background:rgba(0,5,15,0.92); border:1px solid #22c55e; border-radius:14px; padding:16px 20px; font-family:'Share Tech Mono',monospace; color:#22c55e; font-size:12px; line-height:1.9; box-shadow:0 0 20px rgba(34,197,94,0.12); }
.terminal .t-key{color:#64a0b8;} .terminal .t-val{color:#00d4ff;} .terminal .t-ok{color:#22c55e;} .terminal .t-warn{color:#f59e0b;} .terminal .t-err{color:#ef4444;} .terminal .t-label{color:#a855f7;}

/* ── ALERTS ── */
.alert-good { background:rgba(34,197,94,0.10); border:1px solid rgba(34,197,94,0.3); border-left:4px solid #22c55e; padding:13px 18px; border-radius:12px; margin-bottom:10px; }
.alert-warn { background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.3); border-left:4px solid #f59e0b; padding:13px 18px; border-radius:12px; margin-bottom:10px; }
.alert-bad  { background:rgba(239,68,68,0.10);  border:1px solid rgba(239,68,68,0.3);  border-left:4px solid #ef4444; padding:13px 18px; border-radius:12px; margin-bottom:10px; }
.alert-title { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:3px; }

/* ── SIDEBAR INFO ── */
.sys-info-row { display:flex; justify-content:space-between; font-family:'Share Tech Mono',monospace; font-size:10px; padding:4px 14px; border-bottom:1px solid rgba(0,212,255,0.07); }
.sys-info-key{color:#4a7a94;} .sys-info-val{color:#00d4ff;} .sys-info-val-green{color:#22c55e;}
</style>

<div class="particle p1"></div><div class="particle p2"></div>
<div class="particle p3"></div><div class="particle p4"></div>
<div class="particle p5"></div><div class="particle p6"></div>
""", unsafe_allow_html=True)


# =========================
# SAFE API
# =========================
def get_api(endpoint, fallback):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=2)
        r.raise_for_status()
        return r.json()
    except:
        return fallback


# =========================
# LOAD DATA
# =========================
latest      = get_api("/latest",  {"room":"My Room","temperature":None,"humidity":None,"connected":False,"last_update":None})
health      = get_api("/health",  {"status":"WAITING_FOR_DATA","health_score":0})
alerts_data = get_api("/alerts",  {"alerts":["API is not responding."]})
history     = get_api("/history", [])

alerts       = alerts_data.get("alerts", [])
df           = pd.DataFrame(history)
temperature  = latest.get("temperature")
humidity     = latest.get("humidity")
last_update  = latest.get("last_update", "--:--:--")
connected    = latest.get("connected", False)
health_score = health.get("health_score", 0) or 0
status       = health.get("status", "WAITING_FOR_DATA")
room_name    = latest.get("room", "My Room")


# =========================
# SIDEBAR NAV
# =========================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 18px 0;border-bottom:1px solid rgba(0,212,255,0.15);margin-bottom:10px;">
        <div style="font-family:'Orbitron',monospace;font-size:22px;font-weight:900;
                    background:linear-gradient(90deg,#00d4ff,#22c55e);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">AI OS v6</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#4a7a94;letter-spacing:3px;margin-top:4px;">SMART BUILDING</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#4a7a94;letter-spacing:2px;">NEURAL CONTROL CENTER</div>
    </div>""", unsafe_allow_html=True)

    nav_items = [
        ("📊","DASHBOARD"), ("🏗️","3D TWIN"), ("🗺️","FLOORPLAN"),
        ("📈","ANALYTICS"), ("🧠","AI BRAIN"), ("📷","CAMERAS"),
        ("⚡","ENERGY"), ("📡","MQTT STREAM"), ("🚨","ALERTS"),
        ("📋","REPORTS"), ("⚙️","SETTINGS"),
    ]

    for icon, label in nav_items:
        is_active = st.session_state.page == label
        if st.button(f"{icon}  {label}", key=f"nav_{label}",
                     type="primary" if is_active else "secondary",
                     use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Share Tech Mono\',monospace;font-size:9px;color:#4a7a94;letter-spacing:2px;padding:0 14px;margin-bottom:6px;">SYSTEM INFO</div>', unsafe_allow_html=True)

    for key, val, sty in [
        ("Uptime",  datetime.now().strftime("%H:%M:%S"), "val"),
        ("Version", "v6.0.0 Enterprise",                 "val"),
        ("GPU",     "RTX 3060  42°C",                    "val-green"),
        ("CPU",     "23%",                               "val-green"),
        ("RAM",     "38%",                               "val"),
    ]:
        st.markdown(f'<div class="sys-info-row"><span class="sys-info-key">{key}</span><span class="sys-info-{sty}">{val}</span></div>', unsafe_allow_html=True)

    nn_color = "#22c55e" if connected else "#ef4444"
    nn_label = "ACTIVE" if connected else "INACTIVE"
    st.markdown(f"""
    <div style="margin:14px 14px 0;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);border-radius:10px;padding:10px;">
        <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#4a7a94;letter-spacing:2px;">NEURAL NETWORK</div>
        <div style="font-family:'Orbitron',monospace;font-size:12px;font-weight:700;color:{nn_color};margin-top:4px;">⬡ NETWORK {nn_label}</div>
    </div>""", unsafe_allow_html=True)


# =========================
# WAIT SCREEN
# =========================
if temperature is None or humidity is None:
    st.markdown('<div class="os-title">🧠 Smart Building AI OS v6</div>', unsafe_allow_html=True)
    st.warning("⏳ Waiting for live MQTT data...")
    st.info(f"Backend: {API_URL}/latest")
    st_autorefresh(interval=5000, key="waiting_refresh")
    st.stop()


# =========================
# COMMON HELPERS
# =========================
page         = st.session_state.page
temp_color   = "#22c55e" if float(temperature) <= 25 else ("#f59e0b" if float(temperature) <= 27 else "#ef4444")
hum_color    = "#22c55e" if float(humidity) <= 70 else "#ef4444"
health_color = "green"   if health_score >= 80 else ("amber" if health_score >= 60 else "red")
conn_cls     = "t-ok"    if connected else "t-err"
conn_str     = "CONNECTED" if connected else "DISCONNECTED"
stat_cls     = "t-ok"    if status == "OPTIMAL" else ("t-warn" if status == "ATTENTION_REQUIRED" else "t-err")

chart_layout = dict(
    paper_bgcolor="rgba(1,10,25,0.0)", plot_bgcolor="rgba(1,10,25,0.6)",
    font={"color":"#a8d8f0","family":"Share Tech Mono"}, height=300,
    margin=dict(l=40,r=20,t=40,b=40),
    xaxis=dict(gridcolor="rgba(0,212,255,0.08)", linecolor="rgba(0,212,255,0.2)"),
    yaxis=dict(gridcolor="rgba(0,212,255,0.08)", linecolor="rgba(0,212,255,0.2)")
)
gl = dict(paper_bgcolor="rgba(1,10,25,0.0)", font={"color":"#a8d8f0","family":"Share Tech Mono"},
          height=320, margin=dict(l=20,r=20,t=55,b=20))


# ══════════════════════════════
# DASHBOARD
# ══════════════════════════════
if page == "DASHBOARD":
    # Header
    h_left, h_right = st.columns([3,1])
    with h_left:
        badge = '<span class="badge-online">● ONLINE</span>' if connected else '<span class="badge-offline">● OFFLINE</span>'
        st.markdown(f"""
        <div class="os-brand">SMART BUILDING</div>
        <div class="os-title">AI OS v6</div>
        <div class="os-subtitle"><span class="live-dot"></span> LIVE AI BUILDING MONITORING SYSTEM &nbsp;|&nbsp; AI CORE: {badge}</div>
        """, unsafe_allow_html=True)
    with h_right:
        st.markdown(f"""
        <div class="holo-card" style="text-align:right;">
            <div style="font-family:'Orbitron',monospace;font-size:28px;font-weight:900;color:#00d4ff;">{datetime.now().strftime("%H:%M:%S")}</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a7a94;">{datetime.now().strftime("%Y-%m-%d")}</div>
            <div style="margin-top:8px;"><span class="live-dot"></span><span style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#22c55e;">LIVE</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # KPIs
    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_data = [
        (k1,"AI CORE",        "ONLINE" if connected else "OFFLINE","green" if connected else "red","Neural Engine Status",False),
        (k2,"BUILDING HEALTH",f"{health_score}/100",health_color,status,True),
        (k3,"TEMPERATURE",    f"{temperature}°C","amber",f"Room: {room_name}",True),
        (k4,"HUMIDITY",       f"{humidity}%","green" if float(humidity)<=70 else "red","Relative Humidity",True),
        (k5,"LAST PACKET",    str(last_update) if last_update else "--","purple","MQTT Stream",False),
    ]
    for col,label,value,color,sub,spark in kpi_data:
        sp = '<div class="spark"></div>' if spark else ""
        col.markdown(f"""
        <div class="holo-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value kpi-value-{color}">{value}</div>
            <div class="kpi-sub">{sub}</div>{sp}
        </div>""", unsafe_allow_html=True)

    # Twin + Terminal
    st.markdown('<div class="section-header">🏗️ 3D BUILDING TWIN &nbsp;<span style="font-size:10px;color:#22c55e;">● REAL-TIME</span></div>', unsafe_allow_html=True)
    tc, rc = st.columns([1.4,1])
    with tc:
        st.markdown(f"""
        <div class="twin-floor">
            <div class="twin-scan"></div>
            <div class="twin-sensor-main"></div>
            <div class="twin-ring" style="width:80px;height:80px;top:33%;left:41%;"></div>
            <div class="twin-ring" style="width:80px;height:80px;top:33%;left:41%;animation-delay:1s;"></div>
            <div class="twin-sensor-alt" style="top:20%;left:15%;"></div>
            <div class="twin-sensor-alt" style="top:60%;left:72%;background:radial-gradient(circle,#f59e0b,#78350f);box-shadow:0 0 25px rgba(245,158,11,0.8);"></div>
            <div class="room-label" style="top:12%;left:8%;">OFFICE AREA<br><span style="color:#22c55e;">{temperature}°C | {humidity}%</span></div>
            <div class="room-label" style="top:12%;left:62%;">LAB 1<br><span style="color:#f59e0b;">{temperature}°C | {humidity}%</span></div>
            <div class="room-label" style="top:58%;left:65%;">SERVER ROOM<br><span style="color:#22c55e;">21°C | 35%</span></div>
            <div style="position:absolute;bottom:12px;left:50%;transform:translateX(-50%);font-family:'Share Tech Mono',monospace;font-size:11px;color:#00d4ff;text-align:center;z-index:5;">
                MQTT NODE &nbsp;|&nbsp;<span style="color:{temp_color};">{temperature}°C</span>&nbsp;|&nbsp;<span style="color:{hum_color};">{humidity}%</span>&nbsp;|&nbsp;HEALTH:<span style="color:#22c55e;"> {health_score}/100</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with rc:
        st.markdown(f"""
        <div class="terminal">
            <span class="t-label">▶ LIVE MQTT STREAM</span><br>
            ────────────────────────────<br>
            <span class="t-key">[API]      </span><span class="t-val">{API_URL}</span><br>
            <span class="t-key">[MQTT]     </span><span class="{conn_cls}">{conn_str}</span><br>
            <span class="t-key">[TOPIC]    </span><span class="t-val">smartroom/dht11</span><br>
            <span class="t-key">[TEMP]     </span><span class="t-val">{temperature} °C</span><br>
            <span class="t-key">[HUMIDITY] </span><span class="t-val">{humidity} %</span><br>
            <span class="t-key">[HEALTH]   </span><span class="t-ok">{health_score}/100</span><br>
            <span class="t-key">[STATUS]   </span><span class="{stat_cls}">{status}</span><br>
            <span class="t-key">[LAST_PKT] </span><span class="t-val">{last_update}</span><br>
            ────────────────────────────<br>
            <span class="t-label">▶ PACKET LOG</span><br>
            <span class="t-key">smartbuilding/dht11</span><br>
            <span class="t-val">  payload: {{t:{temperature}, h:{humidity}}}</span><br>
            <span class="t-key">smartbuilding/health</span><br>
            <span class="t-val">  score:{health_score} status:{status}</span>
        </div>""", unsafe_allow_html=True)

    # Charts
    st.markdown('<div class="section-header" style="margin-top:20px;">📈 NEURAL ANALYTICS</div>', unsafe_allow_html=True)
    if len(df) > 1 and "timestamp" in df.columns:
        c1,c2 = st.columns(2)
        if "temperature" in df.columns:
            fig1 = px.line(df.tail(80), x="timestamp", y="temperature", line_shape="spline", title="Temperature Signal")
            fig1.update_traces(line=dict(color="#f97316",width=3))
            fig1.update_layout(**chart_layout, title=dict(font=dict(family="Orbitron",size=12,color="#00d4ff")))
            c1.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})
        if "humidity" in df.columns:
            fig2 = px.line(df.tail(80), x="timestamp", y="humidity", line_shape="spline", title="Humidity Signal")
            fig2.update_traces(line=dict(color="#00d4ff",width=3))
            fig2.update_layout(**chart_layout, title=dict(font=dict(family="Orbitron",size=12,color="#00d4ff")))
            c2.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("⏳ Collecting live telemetry history...")

    # AI Brain gauges
    st.markdown('<div class="section-header" style="margin-top:8px;">🧠 AI BRAIN MONITORING</div>', unsafe_allow_html=True)
    g1,g2,g3 = st.columns(3)

    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number", value=health_score,
        title={"text":"AI HEALTH SCORE","font":{"family":"Orbitron","size":12,"color":"#00d4ff"}},
        number={"font":{"family":"Orbitron","size":36,"color":"#00d4ff"}},
        gauge={"axis":{"range":[0,100]},"bar":{"color":"#00d4ff"},"bgcolor":"rgba(0,0,0,0)",
               "steps":[{"range":[0,50],"color":"rgba(239,68,68,0.25)"},
                        {"range":[50,80],"color":"rgba(245,158,11,0.25)"},
                        {"range":[80,100],"color":"rgba(34,197,94,0.25)"}]}
    ))
    gauge_fig.update_layout(**gl)
    g1.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar":False})

    rv = [health_score, min(100,max(0,100-abs(float(temperature)-22)*8)), max(0,100-float(humidity)), 92]
    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(r=rv+[rv[0]], theta=["Health","Temp Stability","Air Quality","AI Confidence","Health"],
        fill="toself", fillcolor="rgba(0,212,255,0.12)", line=dict(color="#00d4ff",width=2)))
    radar_fig.update_layout(polar=dict(bgcolor="rgba(1,10,25,0.6)",
        radialaxis=dict(visible=True,range=[0,100],gridcolor="rgba(0,212,255,0.15)"),
        angularaxis=dict(gridcolor="rgba(0,212,255,0.1)")),
        title=dict(text="AI BRAIN ACTIVITY",font=dict(family="Orbitron",size=12,color="#00d4ff")), **gl)
    g2.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar":False})

    energy_fig = go.Figure(go.Pie(labels=["HVAC","Lighting","Equipment"], values=[22.1,8.7,14.8], hole=0.62,
        marker=dict(colors=["#00d4ff","#22c55e","#a855f7"]), textfont=dict(family="Share Tech Mono",color="white",size=10)))
    energy_fig.add_annotation(text="45.6kW", font=dict(family="Orbitron",size=15,color="#00d4ff"), showarrow=False)
    energy_fig.update_layout(title=dict(text="ENERGY DISTRIBUTION",font=dict(family="Orbitron",size=12,color="#00d4ff")),
        legend=dict(font=dict(family="Share Tech Mono",color="#a8d8f0",size=10)), **gl)
    g3.plotly_chart(energy_fig, use_container_width=True, config={"displayModeBar":False})

    # Alerts
    st.markdown('<div class="section-header" style="margin-top:8px;">🚨 AI ALERTS</div>', unsafe_allow_html=True)
    for alert in alerts:
        if "No active" in alert:
            st.markdown(f'<div class="alert-good"><div class="alert-title">✅ SYSTEM OPTIMAL</div>{alert}</div>', unsafe_allow_html=True)
        elif "Humidity" in alert or "Temperature" in alert:
            st.markdown(f'<div class="alert-warn"><div class="alert-title">⚠️ PREDICTIVE WARNING</div>{alert}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-bad"><div class="alert-title">🚨 CRITICAL ALERT</div>{alert}</div>', unsafe_allow_html=True)

    # Telemetry
    st.markdown('<div class="section-header" style="margin-top:8px;">📋 TELEMETRY MEMORY</div>', unsafe_allow_html=True)
    if len(df) > 0:
        st.dataframe(df.tail(25), use_container_width=True, hide_index=True)
    else:
        st.info("⏳ No telemetry history yet.")

    # Log bar
    now_s = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="holo-card" style="margin-top:10px;padding:10px 18px;">
        <div style="display:flex;gap:28px;flex-wrap:wrap;font-family:'Share Tech Mono',monospace;font-size:10px;">
            <span><span style="color:#00d4ff;">{now_s}</span> <span style="color:#22c55e;">[AI]</span> <span style="color:#a8d8f0;">Monitoring active</span></span>
            <span><span style="color:#00d4ff;">{last_update}</span> <span style="color:#a855f7;">[MQTT]</span> <span style="color:#a8d8f0;">Packet received from smartroom/dht11</span></span>
            <span><span style="color:#00d4ff;">{now_s}</span> <span style="color:#f59e0b;">[SYSTEM]</span> <span style="color:#a8d8f0;">Health: {health_score}/100</span></span>
            <span style="margin-left:auto;"><span class="live-dot"></span><span style="color:#22c55e;">CONNECTED TO MQTT BROKER</span></span>
        </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# 3D TWIN
# ══════════════════════════════
elif page == "3D TWIN":
    st.markdown('<div class="page-hero">🏗️ 3D BUILDING TWIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">REAL-TIME DIGITAL SHADOW · MULTI-FLOOR VIEW</div><br>', unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    floors = [
        (f1,"FLOOR 1 – OFFICE",temperature,humidity,"#22c55e"),
        (f2,"FLOOR 2 – LAB",temperature,humidity,"#f59e0b"),
        (f3,"FLOOR 3 – SERVER","21.0","35.0","#00d4ff"),
    ]
    for col,floor,t,h,color in floors:
        col.markdown(f"""
        <div class="twin-floor" style="height:220px;">
            <div class="twin-scan"></div>
            <div class="twin-sensor-main" style="width:44px;height:44px;top:40%;left:46%;"></div>
            <div class="twin-ring" style="width:55px;height:55px;top:34%;left:41%;"></div>
            <div style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
                        font-family:'Share Tech Mono',monospace;font-size:11px;color:{color};text-align:center;z-index:5;">
                {floor}<br>{t}°C | {h}%
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# ANALYTICS
# ══════════════════════════════
elif page == "ANALYTICS":
    st.markdown('<div class="page-hero">📈 NEURAL ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">HISTORICAL TELEMETRY · TREND ANALYSIS</div><br>', unsafe_allow_html=True)
    if len(df) > 1 and "timestamp" in df.columns:
        for col_name, color, title in [("temperature","#f97316","Full Temperature History"),("humidity","#00d4ff","Full Humidity History")]:
            if col_name in df.columns:
                fig = px.line(df, x="timestamp", y=col_name, line_shape="spline", title=title)
                fig.update_traces(line=dict(color=color,width=2))
                fig.update_layout(**{**chart_layout, "height": 340},title=dict(font=dict(family="Orbitron", size=13, color="#00d4ff"))
)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("⏳ Collecting telemetry history...")


# ══════════════════════════════
# AI BRAIN
# ══════════════════════════════
elif page == "AI BRAIN":
    st.markdown('<div class="page-hero">🧠 AI BRAIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">NEURAL NETWORK INFERENCE · LIVE MODEL STATUS</div><br>', unsafe_allow_html=True)
    b1,b2 = st.columns(2)
    gl2 = {**gl, "height":380}
    rv = [health_score, min(100,max(0,100-abs(float(temperature)-22)*8)), max(0,100-float(humidity)), 92]
    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(r=rv+[rv[0]], theta=["Health","Temp Stability","Air Quality","AI Confidence","Health"],
        fill="toself", fillcolor="rgba(0,212,255,0.12)", line=dict(color="#00d4ff",width=2)))
    radar_fig.update_layout(polar=dict(bgcolor="rgba(1,10,25,0.6)",
        radialaxis=dict(visible=True,range=[0,100],gridcolor="rgba(0,212,255,0.15)"),
        angularaxis=dict(gridcolor="rgba(0,212,255,0.1)")),
        title=dict(text="AI CONFIDENCE RADAR",font=dict(family="Orbitron",size=13,color="#00d4ff")), **gl2)
    b1.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar":False})

    gauge_fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=health_score,
        delta={"reference":80,"font":{"family":"Orbitron"}},
        title={"text":"NEURAL HEALTH INDEX","font":{"family":"Orbitron","size":12,"color":"#00d4ff"}},
        number={"font":{"family":"Orbitron","size":42,"color":"#00d4ff"}},
        gauge={"axis":{"range":[0,100]},"bar":{"color":"#00d4ff"},
               "steps":[{"range":[0,50],"color":"rgba(239,68,68,0.25)"},
                        {"range":[50,80],"color":"rgba(245,158,11,0.25)"},
                        {"range":[80,100],"color":"rgba(34,197,94,0.25)"}]}))
    gauge_fig.update_layout(**gl2)
    b2.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar":False})


# ══════════════════════════════
# ENERGY
# ══════════════════════════════
elif page == "ENERGY":
    st.markdown('<div class="page-hero">⚡ ENERGY FLOW</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">LIVE POWER DISTRIBUTION · EFFICIENCY METRICS</div><br>', unsafe_allow_html=True)
    e1,e2 = st.columns(2)
    gl2 = {**gl,"height":400}
    ef = go.Figure(go.Pie(labels=["HVAC","Lighting","Equipment"], values=[22.1,8.7,14.8], hole=0.65,
        marker=dict(colors=["#00d4ff","#22c55e","#a855f7"]), textfont=dict(family="Share Tech Mono",color="white",size=11)))
    ef.add_annotation(text="45.6 kW<br>Total", font=dict(family="Orbitron",size=14,color="#00d4ff"), showarrow=False)
    ef.update_layout(title=dict(text="ENERGY DISTRIBUTION",font=dict(family="Orbitron",size=13,color="#00d4ff")),
        legend=dict(font=dict(family="Share Tech Mono",color="#a8d8f0",size=11)), **gl2)
    e1.plotly_chart(ef, use_container_width=True, config={"displayModeBar":False})

    bf = go.Figure(go.Bar(x=["HVAC","Lighting","Equipment"], y=[22.1,8.7,14.8],
        marker=dict(color=["#00d4ff","#22c55e","#a855f7"]),
        text=["22.1 kW","8.7 kW","14.8 kW"], textposition="outside",
        textfont=dict(family="Share Tech Mono",color="white")))
    bf.update_layout(title=dict(text="POWER BY SYSTEM (kW)",font=dict(family="Orbitron",size=13,color="#00d4ff")),
        yaxis=dict(gridcolor="rgba(0,212,255,0.1)"), **gl2)
    e2.plotly_chart(bf, use_container_width=True, config={"displayModeBar":False})


# ══════════════════════════════
# MQTT STREAM
# ══════════════════════════════
elif page == "MQTT STREAM":
    st.markdown('<div class="page-hero">📡 MQTT STREAM</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">LIVE PACKET MONITOR · BROKER CONNECTION</div><br>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="terminal" style="font-size:13px;line-height:2.1;">
        <span class="t-label">▶ BROKER CONNECTION</span><br>
        ──────────────────────────────────────────<br>
        <span class="t-key">[BROKER]   </span><span class="t-val">192.168.1.143 : 1883</span><br>
        <span class="t-key">[API]      </span><span class="t-val">{API_URL}</span><br>
        <span class="t-key">[STATUS]   </span><span class="{conn_cls}">{conn_str}</span><br>
        <span class="t-key">[TOPIC]    </span><span class="t-val">smartroom/dht11</span><br>
        ──────────────────────────────────────────<br>
        <span class="t-label">▶ LATEST PACKET</span><br>
        <span class="t-key">[TEMP]     </span><span class="t-val">{temperature} °C</span><br>
        <span class="t-key">[HUMIDITY] </span><span class="t-val">{humidity} %</span><br>
        <span class="t-key">[HEALTH]   </span><span class="t-ok">{health_score}/100</span><br>
        <span class="t-key">[STATUS]   </span><span class="{stat_cls}">{status}</span><br>
        <span class="t-key">[TIMESTAMP]</span><span class="t-val">{last_update}</span><br>
        ──────────────────────────────────────────<br>
        <span class="t-label">▶ HISTORY — {len(df)} records stored</span>
    </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if len(df) > 0:
        st.dataframe(df.tail(50), use_container_width=True, hide_index=True)
    else:
        st.info("⏳ No packets yet.")


# ══════════════════════════════
# ALERTS
# ══════════════════════════════
elif page == "ALERTS":
    st.markdown('<div class="page-hero">🚨 AI ALERTS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">REAL-TIME ANOMALY DETECTION · PREDICTIVE WARNINGS</div><br>', unsafe_allow_html=True)
    for alert in alerts:
        if "No active" in alert:
            st.markdown(f'<div class="alert-good"><div class="alert-title">✅ SYSTEM OPTIMAL</div>{alert}</div>', unsafe_allow_html=True)
        elif "Humidity" in alert or "Temperature" in alert:
            st.markdown(f'<div class="alert-warn"><div class="alert-title">⚠️ PREDICTIVE WARNING</div>{alert}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-bad"><div class="alert-title">🚨 CRITICAL ALERT</div>{alert}</div>', unsafe_allow_html=True)


# ══════════════════════════════
# REPORTS
# ══════════════════════════════
elif page == "REPORTS":
    st.markdown('<div class="page-hero">📋 REPORTS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">TELEMETRY LOG · EXPORT READY</div><br>', unsafe_allow_html=True)
    if len(df) > 0:
        st.markdown(f'<div class="section-header">📊 FULL TELEMETRY LOG — {len(df)} records</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), "telemetry.csv", "text/csv", use_container_width=True)
    else:
        st.info("⏳ No data to report yet.")


# ══════════════════════════════
# SETTINGS
# ══════════════════════════════
elif page == "SETTINGS":
    st.markdown('<div class="page-hero">⚙️ SETTINGS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">SYSTEM CONFIGURATION · API & MQTT</div><br>', unsafe_allow_html=True)
    for label, val, color in [
        ("API ENDPOINT",    API_URL,             "#00d4ff"),
        ("MQTT BROKER",     "192.168.1.143:1883","#22c55e"),
        ("MQTT TOPIC",      "smartroom/dht11",   "#a855f7"),
        ("REFRESH INTERVAL","5000 ms",           "#f59e0b"),
    ]:
        st.markdown(f"""
        <div class="holo-card">
            <div class="kpi-label">{label}</div>
            <div style="font-family:'Share Tech Mono',monospace;color:{color};font-size:16px;">{val}</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# FALLBACK
# ══════════════════════════════
else:
    st.markdown(f'<div class="page-hero">{page}</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">UNDER DEVELOPMENT</div><br>', unsafe_allow_html=True)
    st.info(f"🚧 The **{page}** page is coming soon.")


# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=5000, key="main_refresh")