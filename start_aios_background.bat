@echo off
rem Starts broker, backend and dashboard with no windows; output goes to logs\.
rem Used by the Windows autostart (install_autostart.bat). For a visible start
rem with console windows, use Run_AIOS_v6.bat instead.
set "ROOT=%~dp0"
cd /d "%ROOT%"
if not exist "%ROOT%logs" mkdir "%ROOT%logs"

rem --- stop a previous backend (8000) / dashboard (5173), if any
for %%P in (8000 5173) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
        taskkill /T /F /PID %%I >nul 2>&1
    )
)

rem --- broker: normally the Windows service; otherwise run it in the background
sc query mosquitto 2>nul | find "RUNNING" >nul
if errorlevel 1 if exist "C:\Program Files\mosquitto\mosquitto.exe" (
    start "" /b cmd /c ""C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Program Files\mosquitto\mosquitto.conf" > "%ROOT%logs\mosquitto.log" 2>&1"
)

set "MQTT_BROKER=127.0.0.1"
set "API_HOST=127.0.0.1"
set "CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173"

start "" /b cmd /c ""%ROOT%venv\Scripts\python.exe" "%ROOT%main.py" > "%ROOT%logs\backend.log" 2>&1"
cd /d "%ROOT%frontend-react"
start "" /b cmd /c "npm run dev > "%ROOT%logs\frontend.log" 2>&1"
