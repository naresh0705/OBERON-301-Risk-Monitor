@echo off
echo ==========================================
echo  OBERON-301 Risk-Based Data Quality Monitor
echo  Setup and Launch Script
echo ==========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo [Step 1/3] Creating virtual environment...
    python -m venv venv
    echo Done.
) else (
    echo [Step 1/3] Virtual environment already exists. Skipping.
)

echo [Step 2/3] Installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo Done.

echo [Step 3/3] Starting the app...
echo.
echo ==========================================
echo  App is running!
echo  Open your browser and go to:
echo  http://localhost:8001
echo.
echo  Press Ctrl+C to stop the app.
echo ==========================================
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8001
