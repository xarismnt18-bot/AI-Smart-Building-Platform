@echo off
rem Puts a Thalpos icon on the desktop: double-click it to start everything.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\create_shortcut.ps1"
