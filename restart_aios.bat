@echo off
rem Restarts AIOS in the background (no windows). Same as signing out and in.
set "VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AIOS v6.vbs"
if exist "%VBS%" (
  wscript "%VBS%"
  echo AIOS is restarting in the background.
) else (
  echo Autostart is not installed. Run install_autostart.bat first.
  pause
)
