@echo off
REM Screen a watchlist into a league table.  Usage: screen.bat   or   screen.bat NVDA MU AVGO
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
"!PY!" screen.py %*
echo.
pause
