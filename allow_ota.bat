@echo off
rem One-time: lets the ESP8266 fetch firmware updates from this PC over Wi-Fi (OTA).
rem Opens TCP port 48266 for the local network only. Asks for administrator rights.
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
netsh advfirewall firewall delete rule name="AIOS ESP8266 OTA" >nul 2>&1
netsh advfirewall firewall delete rule name="Thalpos ESP8266 OTA" >nul 2>&1
netsh advfirewall firewall add rule name="Thalpos ESP8266 OTA" dir=in action=allow protocol=TCP localport=48266 remoteip=LocalSubnet profile=any > "%~dp0allow_ota.log" 2>&1
echo exit code %errorlevel% >> "%~dp0allow_ota.log"
