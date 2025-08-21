@echo off
echo Starting Insurance AI Agent - Simplified UI...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies automatically
echo Installing/updating dependencies...
pip install -r requirements.txt --quiet

REM Start the FastAPI application
echo.
echo Starting web interface...
echo Open your browser to: http://localhost:8000
echo.
python -m uvicorn ui_app:app --host 0.0.0.0 --port 8000 --reload

pause
