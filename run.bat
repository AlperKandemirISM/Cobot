@echo off
echo ================================
echo    ST3215 Servo Control
echo ================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
python UI.py

REM Pause to see any errors
echo.
echo ================================
echo Application closed.
echo ================================
pause
