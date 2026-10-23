@echo off
rem Uploads the ESP8266 firmware over Wi-Fi (OTA). Optional argument: the board IP.
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\flash.py" ota %1
