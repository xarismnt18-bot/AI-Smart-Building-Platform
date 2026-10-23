@echo off
rem Restarts Thalpos in the background (no windows). Same as signing out and in.
set "VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Thalpos.vbs"
if exist "%VBS%" (
  wscript "%VBS%"
  echo Thalpos is restarting in the background.
) else (
  echo Autostart is not installed. Run install_autostart.bat first.
  pause
)
