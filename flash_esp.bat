@echo off
rem Compiles and uploads the ESP8266 firmware with the arduino-cli bundled in Arduino IDE.
set "ROOT=%~dp0"
set "LOG=%ROOT%flash_esp.log"
set "CLI=C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
set "PORT=COM9"
echo ==== %date% %time% ==== > "%LOG%"
if not exist "%CLI%" (
  echo arduino-cli not found at "%CLI%" >> "%LOG%"
  exit /b 1
)
"%CLI%" compile --fqbn esp8266:esp8266:nodemcuv2 "%ROOT%firmware\esp8266_dht11" >> "%LOG%" 2>&1
echo compile exit code: %errorlevel% >> "%LOG%"
if errorlevel 1 goto end
"%CLI%" upload -p %PORT% --fqbn esp8266:esp8266:nodemcuv2 "%ROOT%firmware\esp8266_dht11" >> "%LOG%" 2>&1
echo upload exit code: %errorlevel% >> "%LOG%"
:end
echo ==== done ==== >> "%LOG%"
