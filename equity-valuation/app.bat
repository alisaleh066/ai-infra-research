@echo off
REM Launch the Streamlit web app.
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PY=%USERPROFILE%\anaconda3\python.exe"
if not exist "!PY!" set "PY=python"
"!PY!" -m streamlit run app.py
