@echo off
rem Resets the ESP8266 over USB and saves what it prints to serial_log.txt.
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\serial_log.py" 40
