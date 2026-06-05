# Smart Building AI - Enterprise Edition

Advanced IoT monitoring platform with predictive analytics, AI recommendations, and interactive floorplan visualization.

## 🚀 Features

### 1. **Predictive AI Analytics**
- **Next 10-Minute Forecasts** for CO2, temperature, humidity, and power consumption
- **Occupancy Trend Prediction** - predicts if rooms will become occupied/empty
- **Confidence Scores** - shows reliability of predictions
- **Trend Direction** - displays rising, stable, or falling patterns
- **Risk Assessment** - colors code predictions (green/yellow/red)

### 2. **AI Recommendation Engine**
- **Smart Suggestions** based on real-time conditions and predictions
- **Priority-Based Alerts** - critical, warning, info, and success levels
- **Actionable Insights** - specific actions to optimize building performance
- **Context-Aware** - understands occupancy, time patterns, and environmental factors
- **Examples:**
  - "Open ventilation in Main Office - CO2 rising"
  - "Reduce AC cooling in Demo Room - energy waste"
  - "Conference room likely to become empty soon - prepare power reduction"

### 3. **Live Interactive Floorplan**
- **Real-Time Room Visualization** - see all rooms on a building map
- **Color-Coded Status** - green (normal), yellow (warning), red (critical)
- **Hover Information** - view detailed metrics when hovering over rooms
- **Anomaly Indicators** - blinking alerts for critical issues
- **Building Health Score** - 0-100 metric showing overall facility status

### 4. **Enterprise Dashboard**
- **5 Specialized Views:**
  1. **Floorplan** - Visual building overview
  2. **Predictions** - Future condition forecasting
  3. **Recommendations** - AI-powered suggestions
  4. **Analytics** - Historical trend analysis
  5. **Details** - Room-level sensor data

## 📁 Project Structure

```
smart-building-ai/
├── ai/
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── prediction_engine.py      # Time-series forecasting
│   │   ├── recommendation_engine.py  # Rule-based recommendations
│   │   └── floorplan_generator.py   # Visualization engine
│   ├── advanced_dashboard.py         # NEW: Main dashboard (THIS ONE!)
│   ├── live_dashboard.py             # Old dashboard (still functional)
│   ├── train_*.py
│   └── models/
├── ui/
│   ├── __init__.py
│   └── components.py                 # Reusable UI components
├── models/                           # Trained ML models
├── data/
├── requirements.txt                  # Dependencies
└── README.md
```

## 🛠️ Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train models (if needed):**
   ```bash
   python ai/train_occupancy_model.py
   python ai/train_anomaly_model.py
   ```

3. **Run the advanced dashboard:**
   ```bash
   streamlit run ai/advanced_dashboard.py
   ```

## 📊 Usage

### Running the Dashboard

```bash
# Advanced Enterprise Dashboard (RECOMMENDED)
streamlit run ai/advanced_dashboard.py

# Original Dashboard (for comparison)
streamlit run ai/live_dashboard.py
```

The dashboard will open at `http://localhost:8501`

### Tab Guide

| Tab | Purpose | Key Features |
|-----|---------|--------------|
| 🏢 **Floorplan** | Building overview | Visual room status, health score, key metrics |
| 🔮 **Predictions** | Future forecasts | 10-minute ahead predictions, trend analysis |
| 💡 **Recommendations** | AI suggestions | Priority-ranked actions for optimization |
| 📊 **Analytics** | Historical trends | CO2, temperature, humidity, power charts |
| 📋 **Details** | Granular data | Room-by-room sensor readings |

### Sidebar Controls

- **Refresh Interval** (1-10 seconds)
- **Room Selection** - monitor specific rooms
- **Alert Thresholds:**
  - CO2 threshold (ppm)
  - Temperature threshold (°C)
  - Humidity threshold (%)
  - Power consumption threshold (W)

## 🧠 How It Works

### Prediction Engine

Uses **exponential-weighted linear regression** on historical data:

```python
# Example: Predicting CO2 in next 10 minutes
1. Extract last 20 minutes of CO2 data for room
2. Apply exponential weights (recent data = higher weight)
3. Fit linear trend
4. Extrapolate 10 minutes ahead
5. Calculate confidence from data variance
6. Assess risk level based on thresholds
```

**Supported Metrics:**
- CO2 concentration
- Room temperature
- Humidity levels
- Power consumption
- Occupancy patterns

### Recommendation Engine

Rule-based system combining:
- **Current Conditions** (sensor readings)
- **Predictions** (forecasted values)
- **Anomalies** (ML detection)
- **Thresholds** (user-configured limits)

**Example Rules:**
- If occupied AND CO2 > threshold → "Increase Ventilation"
- If empty AND power > threshold → "Reduce Energy Waste"
- If temperature rising AND occupied → "Prepare Cooling"

### Floorplan Generator

Creates interactive visualization with:
- **Room Layouts** - predefined building map
- **Color Coding** - status at a glance
- **Metrics Display** - hover for detailed info
- **Health Score** - overall building performance

## 📈 New Libraries

```
statsmodels==0.14.0  # Time-series forecasting
scikit-learn==1.8.0  # ML models
numpy==2.4.4         # Numerical computing
pandas==3.0.2        # Data manipulation
scipy==1.17.1        # Scientific computing
plotly==5.24.1       # Interactive visualizations
streamlit==1.57.0    # Dashboard framework
```

## 🎨 Design Philosophy

- **Glassmorphism** - frosted glass effect with backdrop blur
- **Dark Theme** - enterprise aesthetic (black/blue/slate)
- **Smooth Animations** - glow pulses, fade-ins, smooth transitions
- **Tesla-Inspired** - minimalist with vibrant accents
- **Responsive** - adapts to different screen sizes

## 🔧 Configuration

Edit thresholds in `advanced_dashboard.py`:

```python
# Line ~330
co2_threshold = 1000          # ppm
temp_threshold = 27           # °C
humidity_threshold = 70       # %
power_threshold = 1200        # W
```

Or use sidebar controls in the dashboard.

## 📡 Real-Time Data

- **Sensor Simulation** - generates random but realistic room data
- **ML Predictions** - occupancy detection and anomaly detection
- **Historical Tracking** - maintains session history in `st.session_state`
- **Live Updates** - refreshes based on configured interval

## 🚨 Alert Levels

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Green | Normal | Optimal conditions |
| 🟡 Yellow | Warning | Elevated but acceptable |
| 🔴 Red | Critical | Action needed immediately |
| ⚫ Gray | Empty | Room unoccupied |

## 🔐 Production Ready Features

- ✅ Modular architecture (easy to extend)
- ✅ Clean separation of concerns
- ✅ Reusable components
- ✅ Error handling
- ✅ Scalable design
- ✅ Configuration-driven
- ✅ Well-documented code
- ✅ Enterprise styling

## 🚀 Future Enhancements

Potential additions:
- Real database integration (PostgreSQL/InfluxDB)
- API endpoints (FastAPI)
- Multi-building support
- Machine learning model retraining
- Email/SMS alerts
- Historical data export
- MQTT sensor integration
- Mobile app
- WebSocket real-time sync

## 📝 Example Workflows

### Scenario 1: Energy Optimization
```
1. Dashboard shows Conference Room using 2500W while empty
2. Prediction Engine forecasts continued high usage
3. Recommendation Engine suggests: "Reduce AC - Energy Waste"
4. User takes action → saves energy
```

### Scenario 2: Comfort Management
```
1. CO2 in HR Office reaches 1100ppm (high)
2. Occupancy detected (Occupied)
3. Recommendation: "Increase Ventilation"
4. Prediction shows CO2 rising → Warn ahead of threshold
5. Building HVAC adjusts automatically
```

### Scenario 3: Anomaly Detection
```
1. ML detects unusual pattern in Main Office
2. Dashboard shows 🔴 Critical flag
3. Floorplan highlights room
4. Recommendation: "Investigate Sensor"
5. Alert sent to building manager
```

## 🤝 Support

For issues or questions:
1. Check sensor data in Details tab
2. Review predictions for trends
3. Check recommendations for actions
4. Inspect raw data in Analytics tab

## 📄 License

Enterprise AI Platform - Smart Building Monitoring System

---

**Version:** 2.0 (Enterprise Edition)  
**Last Updated:** May 2026  
**Status:** Production Ready ✅
