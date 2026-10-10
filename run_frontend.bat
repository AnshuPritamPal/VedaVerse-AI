@echo off
REM Start the VedaVerse AI frontend with the project virtual environment.
cd /d "%~dp0"
"venv\Scripts\python.exe" -m streamlit run frontend\app.py
