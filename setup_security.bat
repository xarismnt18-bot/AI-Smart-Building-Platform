@echo off
rem Runs setup_security.ps1 as Administrator (Windows will ask for permission).
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_security.ps1"
timeout /t 8
