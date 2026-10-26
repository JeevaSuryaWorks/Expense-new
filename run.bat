@echo off
echo ===================================================
echo Starting Smart Expense Tracker...
echo ===================================================

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please run the first-time setup commands first:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Run Flask Application
echo Activating virtual environment and launching application...
.\venv\Scripts\python.exe app.py

pause
