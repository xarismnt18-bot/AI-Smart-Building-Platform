# AIOS v6 – AI-Powered Smart Building Digital Twin Platform

## Overview

AIOS v6 is a full-stack Smart Building Monitoring Platform that combines IoT, MQTT communication, machine learning, real-time analytics, and a 3D Digital Twin environment.

The platform enables real-time environmental monitoring, intelligent alerting, health scoring, anomaly detection, and interactive visualization of building conditions through a modern enterprise dashboard.

This project was developed as a personal portfolio project demonstrating the integration of IoT systems, backend development, frontend development, data analytics, and AI-driven monitoring technologies.

---

## Key Features

### Real-Time IoT Monitoring

* MQTT sensor communication
* Live temperature monitoring
* Live humidity monitoring
* Sensor status tracking
* Real-time packet streaming

### Digital Twin Visualization

* Interactive 3D room representation
* Digital shadow concept
* Live environmental data overlay
* Room-level monitoring

### AI Health Monitoring

* Building health scoring system
* Environmental condition assessment
* Comfort-level evaluation
* Automated status classification

### Alert Engine

* Temperature alerts
* Humidity alerts
* Connectivity alerts
* System health notifications

### Analytics Dashboard

* Historical data visualization
* Environmental trends
* Sensor performance tracking
* Interactive charts and metrics

### Full-Stack Architecture

* FastAPI backend
* MQTT integration
* React frontend
* Streamlit dashboard
* Modular AI architecture

---

## Current Functional Modules

| Module          | Status       |
| --------------- | ------------ |
| Dashboard       | ✅ Functional |
| 3D Digital Twin | ✅ Functional |
| Floorplan View  | ✅ Functional |
| Analytics       | ✅ Functional |
| MQTT Stream     | ✅ Functional |
| Alerts System   | ✅ Functional |
| AI Health Score | ✅ Functional |
| FastAPI Backend | ✅ Functional |

---

## Modules Under Development

| Module              | Status            |
| ------------------- | ----------------- |
| AI Brain            | 🚧 In Development |
| Energy Optimization | 🚧 In Development |
| Automated Reports   | 🚧 In Development |

The architecture has been designed to support future expansion with advanced AI reasoning, energy optimization algorithms, predictive maintenance, and automated reporting capabilities.

---

## System Architecture

```text
IoT Sensors
     │
     ▼
 MQTT Broker
     │
     ▼
 FastAPI Backend
     │
     ├── Health Scoring Engine
     ├── Alert Engine
     ├── Analytics Engine
     └── Data Processing Layer
     │
     ▼
 Streamlit Dashboard
     │
     ▼
 Digital Twin Interface
```

---

## Technology Stack

### Backend

* Python
* FastAPI
* MQTT (Paho MQTT)

### Frontend

* React
* Vite
* Streamlit

### Data & Analytics

* Pandas
* NumPy
* Plotly

### AI & Machine Learning

* Scikit-Learn
* Anomaly Detection Models
* Occupancy Prediction Models

### IoT

* MQTT Communication
* Environmental Sensors
* Real-Time Data Streaming

---

## Dashboard Views

### Dashboard

Real-time overview of environmental conditions and building status.

### 3D Twin

Interactive digital twin visualization of monitored spaces.

### Floorplan

Building layout representation with room-level monitoring.

### Analytics

Historical trends and environmental performance metrics.

### MQTT Stream

Live sensor communication monitoring.

### Alerts

System-generated environmental and connectivity alerts.

---

## Project Structure

```text
smart-building-ai/
│
├── ai/
├── backend/
├── dashboard/
├── frontend/
├── frontend-react/
├── models/
├── sensors/
├── ui/
│
├── main.py
├── requirements.txt
└── README.md
```

---

## Future Roadmap

* AI Brain implementation
* Energy optimization engine
* Automated reporting system
* Predictive maintenance
* Multi-room occupancy forecasting
* Cloud deployment
* Mobile dashboard
* Edge AI integration
* Home Assistant integration

---

## Project Goals

This project aims to demonstrate practical implementation of:

* IoT Systems Engineering
* Smart Building Technologies
* Real-Time Data Processing
* Machine Learning Integration
* Digital Twin Concepts
* Full-Stack Development
* AI-Driven Monitoring Platforms

---

## Author

Mentsios Nikolaou Charalampos
Electrical & Electronics Engineer (MEng)
---

### Status

Version: AIOS v6

Current State: Functional MVP with modular architecture for future AI and energy management capabilities.
