@echo off
REM Start the VedaVerse AI backend with the project virtual environment.
cd /d "%~dp0"
"venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
