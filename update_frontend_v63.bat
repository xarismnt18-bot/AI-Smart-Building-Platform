@echo off
cd /d "%~dp0frontend-react"
echo Removing the old 3D twin files...
if exist "src\components\twin" rmdir /s /q "src\components\twin"
if exist "src\lib\twin.js" del /q "src\lib\twin.js"
echo Installing new fonts (Oxanium, Manrope)...
call npm install --no-audit --no-fund
echo.
echo Done. Start AIOS with Run_AIOS_v6.bat
pause
