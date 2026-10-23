@echo off
rem Removes the Thalpos autostart entry and desktop shortcut. A running backend/dashboard
rem keeps running until you sign out or close it.
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Thalpos.vbs" 2>nul
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AIOS v6.vbs" 2>nul
del /q "%USERPROFILE%\Desktop\Thalpos.url" 2>nul
echo Thalpos autostart removed.
pause
