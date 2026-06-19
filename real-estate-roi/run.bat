@echo off
REM Run the deal. Usage:  run.bat            (uses deal.sample.json)
REM                       run.bat mydeal.json
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
"!PY!" roi.py %1
echo.
pause
