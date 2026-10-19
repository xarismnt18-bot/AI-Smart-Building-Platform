@echo off
rem Removes the AIOS autostart entry. Running backend/dashboard keep running
rem until you sign out or close them.
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AIOS v6.vbs" 2>nul
echo AIOS autostart removed.
pause
