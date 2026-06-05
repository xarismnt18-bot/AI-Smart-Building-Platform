# How to Run AIOS v6

## Prerequisites

Install:

* Python 3.11+
* Node.js
* Mosquitto MQTT Broker

---

## Option 1 – One Click Launch (Recommended)

Run:

```text
start_ai_os.bat
```

The script automatically:

1. Starts the MQTT Broker
2. Starts the FastAPI Backend
3. Starts the React Frontend
4. Opens the application in your browser

The dashboard will be available at:

```text
http://localhost:5173
```

---

## Option 2 – Manual Startup

### Start MQTT Broker

```bash
mosquitto -v
```

### Start FastAPI Backend

```bash
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### Start React Frontend

```bash
cd frontend-react
npm run dev
```

### Open Browser

```text
http://localhost:5173
```

---

## Notes

The application currently runs locally and communicates with an MQTT broker for real-time telemetry.

If no sensor data is available, the dashboard will wait for incoming MQTT packets before displaying live information.
