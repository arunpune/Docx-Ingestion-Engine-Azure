#!/usr/bin/env pwsh

Write-Host "🚀 Starting Insurance AI Agent - Simplified Setup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Blue
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& .\venv\Scripts\Activate.ps1

# Install basic requirements
Write-Host "📥 Installing basic requirements..." -ForegroundColor Blue
pip install --quiet fastapi uvicorn jinja2 python-dotenv

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "⚠️  Please edit the .env file with your Azure credentials before continuing." -ForegroundColor Yellow
    Read-Host "Press Enter when ready"
}

# Start the simplified UI
Write-Host "🌐 Starting web interface..." -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Open your browser and go to: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python simple_ui.py

Read-Host "Press Enter to exit"
