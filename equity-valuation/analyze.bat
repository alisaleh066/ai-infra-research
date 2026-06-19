@echo off
REM Full research workup (ratios, F-Score, Altman Z, Beneish M, reverse DCF...).
REM Usage:  analyze.bat MU    (defaults to MU if no ticker given)
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
set "TICKER=%~1"
if "%TICKER%"=="" set "TICKER=MU"
"!PY!" analyze.py %TICKER%
echo.
echo Report written to: output\%TICKER%_research.md  and  output\%TICKER%_analysis.xlsx
pause
