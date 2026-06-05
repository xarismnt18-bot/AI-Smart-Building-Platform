@echo off
cd /d C:\Users\HARIS\Desktop\smart-building-ai

start "MQTT Broker" cmd /k "cd /d C:\Program Files\mosquitto && .\mosquitto.exe -v"

timeout /t 2 /nobreak

start "FastAPI Backend" cmd /k "cd /d C:\Users\HARIS\Desktop\smart-building-ai && call .\venv\Scripts\activate.bat && uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak

start "React Frontend" cmd /k "cd /d C:\Users\HARIS\Desktop\smart-building-ai\frontend-react && npm run dev"

timeout /t 5 /nobreak

start http://localhost:5173

pause