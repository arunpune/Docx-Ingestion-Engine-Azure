@echo off
echo 🚀 Starting Insurance AI Agent - Simplified Setup
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
echo.

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

:: Install basic requirements
echo 📥 Installing basic requirements...
pip install --quiet fastapi uvicorn jinja2 python-dotenv

:: Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo ⚠️  Please edit the .env file with your Azure credentials before continuing.
    echo Press any key when ready...
    pause
)

:: Start the simplified UI
echo 🌐 Starting web interface...
echo.
echo 🎉 Open your browser and go to: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python simple_ui.py

pause
