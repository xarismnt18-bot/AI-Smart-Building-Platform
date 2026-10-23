@echo off
rem Teaches the ESP8266 the Wi-Fi this laptop is on, then uploads over USB.
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\add_wifi.py"
