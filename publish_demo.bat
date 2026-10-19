@echo off
rem Builds the dashboard in demo mode (simulated sensor, no backend) and pushes
rem it to the gh-pages branch, which GitHub Pages serves as the live demo.
rem Run it again whenever you want the online demo to show the latest frontend.
setlocal
set "ROOT=%~dp0"
set "LOG=%ROOT%publish_demo.log"
echo ==== %date% %time% ==== > "%LOG%"
for /f "delims=" %%U in ('git -C "%ROOT%." remote get-url origin') do set "ORIGIN=%%U"
for /f "delims=" %%E in ('git -C "%ROOT%." config user.email') do set "EMAIL=%%E"
for /f "delims=" %%N in ('git -C "%ROOT%." config user.name') do set "NAME=%%N"

cd /d "%ROOT%frontend-react"
set "VITE_DEMO=1"
set "VITE_BASE=/AI-Smart-Building-Platform/"
call npm run build >> "%LOG%" 2>&1
if errorlevel 1 ( echo build failed >> "%LOG%" & exit /b 1 )

cd /d "%ROOT%frontend-react\dist"
type nul > .nojekyll
copy /y index.html 404.html >nul
if exist .git rmdir /s /q .git
git init -q -b gh-pages
git config user.email "%EMAIL%"
git config user.name "%NAME%"
git add -A
git commit -q -m "Live demo build" >> "%LOG%" 2>&1
git push -f "%ORIGIN%" gh-pages >> "%LOG%" 2>&1
echo push exit code: %errorlevel% >> "%LOG%"
rmdir /s /q .git
echo ==== done ==== >> "%LOG%"
