@echo off
rem Connects the IKEA smart plug (via the DIRIGERA hub) as the Thalpos alert lamp.
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" "%~dp0tools\setup_ikea.py"
if errorlevel 1 exit /b 1
call "%~dp0restart_thalpos.bat"
