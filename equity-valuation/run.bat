@echo off
REM Value a stock.  Usage:  run.bat MU   (defaults to MU if no ticker given)
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
set "TICKER=%~1"
if "%TICKER%"=="" set "TICKER=MU"
"!PY!" value.py %TICKER%
echo.
pause
