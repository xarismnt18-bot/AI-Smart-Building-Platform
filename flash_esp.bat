@echo off
rem Compiles the ESP8266 firmware and uploads it over USB (finds the COM port by itself).
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\flash.py" usb
