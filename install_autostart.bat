@echo off
rem Starts AIOS automatically (hidden) every time you sign in to Windows,
rem and adds an "AIOS Dashboard" shortcut to the desktop.
rem Undo with uninstall_autostart.bat.
set "ROOT=%~dp0"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS=%STARTUP%\AIOS v6.vbs"

(
  echo ' Starts Smart Building AI OS in the background at sign-in.
  echo Set sh = CreateObject^("WScript.Shell"^)
  echo sh.Run """%ROOT%start_aios_background.bat""", 0, False
) > "%VBS%"

(
  echo [InternetShortcut]
  echo URL=http://localhost:5173
) > "%USERPROFILE%\Desktop\AIOS Dashboard.url"

echo Autostart installed: "%VBS%"
echo Starting AIOS in the background now...
wscript "%VBS%"
timeout /t 8 /nobreak >nul
start http://localhost:5173
