Write-Host "Starting Insurance AI Agent - Simplified UI..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Install/update dependencies automatically
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Start the FastAPI application
Write-Host ""
Write-Host "Starting web interface..." -ForegroundColor Green
Write-Host "Open your browser to: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn ui_app:app --host 0.0.0.0 --port 8000 --reload

Read-Host "Press Enter to exit"
