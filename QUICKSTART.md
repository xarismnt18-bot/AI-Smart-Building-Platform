# 🚀 Quick Start Guide - Smart Building AI Enterprise

## Installation (5 minutes)

```bash
# 1. Navigate to project directory
cd c:\Users\HARIS\Desktop\smart-building-ai

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Run the advanced dashboard
streamlit run ai/advanced_dashboard.py
```

Dashboard opens at: `http://localhost:8501`

---

## What You Get

### 🏢 **Tab 1: Floorplan**
- Interactive building map with color-coded rooms
- Real-time status visualization
- Building health score (0-100)
- Key metrics at a glance

### 🔮 **Tab 2: Predictions**
- AI forecasts for next 10 minutes
- CO2, temperature, humidity, power predictions
- Confidence scores for each prediction
- Trend direction (↑↓→)
- Risk levels (🟢🟡🔴)

### 💡 **Tab 3: Recommendations**
- Smart suggestions to optimize buildings
- Priority-ranked by severity
- Actionable recommendations
- Color-coded by urgency

### 📊 **Tab 4: Analytics**
- Historical trend charts
- CO2, temperature, humidity, power consumption
- Interactive Plotly visualizations
- Select different rooms

### 📋 **Tab 5: Details**
- Real-time sensor data for each room
- Alert status
- ML anomaly detection
- Expandable room details

---

## Key Features Explained

### **Prediction Engine** 🔮
```
Takes last 20 minutes of data → Fits trend → Predicts 10 minutes ahead
Example: "CO2 in Main Office will reach 1050 ppm (Warning level)"
```

### **Recommendation Engine** 💡
```
Combines: Current conditions + Predictions + Anomalies + Thresholds
→ Smart suggestions
Example: "Room empty but using 2500W - likely energy waste"
```

### **Floorplan** 🏢
```
Visual building map with color-coded status:
🟢 Normal   🟡 Warning   🔴 Critical   ⚫ Empty
```

---

## Sidebar Controls

| Control | Range | What It Does |
|---------|-------|--------------|
| Refresh | 1-10s | How often dashboard updates |
| Rooms | Multi-select | Which rooms to monitor |
| CO2 | 600-1500ppm | Alert threshold |
| Temp | 20-35°C | Alert threshold |
| Humidity | 50-90% | Alert threshold |
| Power | 500-3000W | Alert threshold |

---

## Project Structure

```
smart-building-ai/
├── ai/
│   ├── engines/                    # NEW: AI engines
│   │   ├── prediction_engine.py    # Forecasting
│   │   ├── recommendation_engine.py # Suggestions
│   │   └── floorplan_generator.py  # Visualization
│   ├── advanced_dashboard.py       # NEW: Main dashboard
│   ├── live_dashboard.py           # Old dashboard
│   └── train_*.py                  # Model training
├── ui/                             # NEW: UI components
│   └── components.py               # Reusable styling
├── models/                         # ML models
├── requirements.txt                # Dependencies
├── ENTERPRISE_README.md            # Full docs
└── QUICKSTART.md                   # This file
```

---

## Common Tasks

### **Change Alert Thresholds**

Use sidebar sliders OR edit `advanced_dashboard.py`:

```python
# Line ~330
co2_threshold = 1000          # Change this
temp_threshold = 27           # Or this
humidity_threshold = 70
power_threshold = 1200
```

### **Monitor Different Rooms**

Sidebar: "Monitor rooms" → Select/deselect rooms

### **View Predictions**

Tab: "🔮 Predictions" → Select room → See 10-min forecast

### **Get Smart Recommendations**

Tab: "💡 Recommendations" → Select room → View AI suggestions

### **Analyze Historical Trends**

Tab: "📊 Analytics" → Select room → View charts

---

## Example Scenarios

### Scenario 1: High CO2 in Occupied Room
```
1. Floorplan shows 🟡 Yellow in Conference Room
2. Predictions show CO2 will reach 1100 ppm
3. Recommendation: "Increase ventilation"
→ Action: Open windows / Adjust HVAC
```

### Scenario 2: Energy Waste
```
1. Dashboard shows 2800W usage in empty room
2. Anomaly detection flags suspicious pattern
3. Recommendation: "Reduce power consumption"
→ Action: Turn off HVAC / Lights / Equipment
```

### Scenario 3: Optimal Conditions
```
1. Room is occupied with ideal CO2, temp, humidity
2. No alerts or anomalies
3. Recommendation: "✨ Optimal conditions - maintain"
→ Action: No action needed
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard won't start | `pip install -r requirements.txt` then restart |
| Predictions don't appear | Wait 1-2 minutes for data collection |
| Floorplan not showing | Ensure at least one room is selected |
| High CPU usage | Increase refresh rate in sidebar |
| No anomalies detected | Models may need retraining (run `train_anomaly_model.py`) |

---

## Next Steps

1. **Explore Each Tab** - Get familiar with all visualizations
2. **Test Predictions** - Watch how room conditions evolve
3. **Review Recommendations** - See AI suggestions in action
4. **Adjust Thresholds** - Set limits that match your building
5. **Monitor Trends** - Use Analytics tab for long-term insights

---

## Key Innovations 🎯

✅ **Predictive Analytics** - Forecast future conditions  
✅ **Smart Recommendations** - AI-powered suggestions  
✅ **Interactive Floorplan** - Visual building status  
✅ **Enterprise Design** - Modern glassmorphism aesthetic  
✅ **Production Ready** - Modular, scalable architecture  

---

## Support Resources

- **ENTERPRISE_README.md** - Full documentation
- **advanced_dashboard.py** - Source code
- **ai/engines/** - AI engine implementations
- **ui/components.py** - UI styling

---

**Status:** ✅ Ready to Use  
**Version:** 2.0 Enterprise Edition  
**Last Updated:** May 2026

Enjoy your AI-powered smart building! 🏢✨
