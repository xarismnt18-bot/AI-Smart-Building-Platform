@echo off
rem Launches broker, backend and dashboard from wherever this folder lives.
rem Safe to run again: it first stops a backend/dashboard left over from a previous run.
set "ROOT=%~dp0"
set "MOSQUITTO_DIR=C:\Program Files\mosquitto"

echo ========================================
echo   Thalpos - Launcher
echo ========================================

rem --- stop previous backend (port 8000) and dashboard (port 5173), if running
for %%P in (8000 5173) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
        taskkill /T /F /PID %%I >nul 2>&1
    )
)

rem --- broker: use the Windows service if it is running, otherwise start one
sc query mosquitto 2>nul | find "RUNNING" >nul
if %errorlevel%==0 (
    echo [OK] Mosquitto service is running.
) else if exist "%MOSQUITTO_DIR%\mosquitto.exe" (
    start "MQTT Broker" cmd /k "cd /d "%MOSQUITTO_DIR%" && mosquitto.exe -v -c mosquitto.conf"
) else (
    echo [WARN] mosquitto.exe not found in %MOSQUITTO_DIR% - start the broker manually.
)

rem The broker runs on this PC, so the backend talks to it over localhost.
rem This overrides MQTT_BROKER from .env (which may hold an outdated LAN IP).
rem The ESP8266 still needs this PC's LAN IP.
set "MQTT_BROKER=127.0.0.1"

rem Security: the API has no login, so keep it reachable from this PC only,
rem and accept browser calls only from the local dashboard. Overrides .env.
set "API_HOST=127.0.0.1"
set "CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173"

rem The backend retries the broker connection on its own, so no race here.
start "FastAPI Backend" cmd /k "cd /d "%ROOT%" && call venv\Scripts\activate.bat && python main.py --reload"

start "React Frontend (v6)" cmd /k "cd /d "%ROOT%frontend-react" && npm run dev"

timeout /t 5 /nobreak >nul
start http://localhost:5173
