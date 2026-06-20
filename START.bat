@echo off
REM ============================================================
REM  projectsf - one launcher for all three projects.
REM  Double-click this file. Pick a number. That's it.
REM ============================================================
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"

:menu
cls
echo ==================================================
echo    projectsf  -  Investment Analysis Toolkit
echo ==================================================
echo.
echo   EQUITY VALUATION
echo      1) Value a stock        (DCF, scenarios, comps)
echo      2) Research analysis    (scores + BUY/HOLD/SELL)
echo      3) Web app
echo      8) Screen a watchlist   (league table)
echo.
echo   AI BOTTLENECK MAP
echo      4) Run                  (tightness ranking)
echo      5) Web app
echo.
echo   REAL-ESTATE ROI
echo      6) Run                  (LP/GP waterfall)
echo      7) Web app
echo.
echo      0) Exit
echo.
set /p "c=Choose a number: "

if "%c%"=="1" goto val
if "%c%"=="2" goto ana
if "%c%"=="3" goto valapp
if "%c%"=="4" goto bott
if "%c%"=="5" goto bottapp
if "%c%"=="6" goto re
if "%c%"=="7" goto reapp
if "%c%"=="8" goto screen
if "%c%"=="0" exit /b
goto menu

:screen
cd /d "%ROOT%equity-valuation"
"!PY!" screen.py
echo.
pause
goto menu

:val
set /p "t=Ticker (e.g. MU, AAPL): "
if "!t!"=="" set "t=MU"
cd /d "%ROOT%equity-valuation"
"!PY!" value.py !t!
echo.
pause
goto menu

:ana
set /p "t=Ticker (e.g. MU, AAPL): "
if "!t!"=="" set "t=MU"
cd /d "%ROOT%equity-valuation"
"!PY!" analyze.py !t!
echo.
pause
goto menu

:valapp
echo Launching web app... close the browser tab and press Ctrl+C here to return.
cd /d "%ROOT%equity-valuation"
"!PY!" -m streamlit run app.py
goto menu

:bott
cd /d "%ROOT%ai-bottleneck-map"
"!PY!" build.py
echo.
pause
goto menu

:bottapp
echo Launching web app... close the browser tab and press Ctrl+C here to return.
cd /d "%ROOT%ai-bottleneck-map"
"!PY!" -m streamlit run app.py
goto menu

:re
cd /d "%ROOT%real-estate-roi"
"!PY!" roi.py
echo.
pause
goto menu

:reapp
echo Launching web app... close the browser tab and press Ctrl+C here to return.
cd /d "%ROOT%real-estate-roi"
"!PY!" -m streamlit run app.py
goto menu
