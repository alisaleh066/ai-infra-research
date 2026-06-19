@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
echo Using Python: !PY!
"!PY!" -m pip install -r requirements.txt
echo.
echo Done. Now run:  run.bat
pause
