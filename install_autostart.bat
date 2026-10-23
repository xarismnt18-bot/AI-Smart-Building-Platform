@echo off
rem Starts Thalpos automatically (hidden) every time you sign in to Windows,
rem and adds a "Thalpos" shortcut to the desktop.
rem Undo with uninstall_autostart.bat.
set "ROOT=%~dp0"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS=%STARTUP%\Thalpos.vbs"

rem remove the entries from before the app was renamed (AIOS)
del /q "%STARTUP%\AIOS v6.vbs" 2>nul
del /q "%USERPROFILE%\Desktop\Thalpos.url" 2>nul

(
  echo ' Starts Thalpos in the background at sign-in.
  echo Set sh = CreateObject^("WScript.Shell"^)
  echo sh.Run """%ROOT%start_thalpos_background.bat""", 0, False
) > "%VBS%"

(
  echo [InternetShortcut]
  echo URL=http://localhost:5173
) > "%USERPROFILE%\Desktop\Thalpos.url"

echo Autostart installed: "%VBS%"
echo Starting Thalpos in the background now...
wscript "%VBS%"
timeout /t 8 /nobreak >nul
start http://localhost:5173
