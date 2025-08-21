"""
Automated Setup and Launch Script for Insurance AI Agent
This script handles dependency installation and starts the application automatically.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required Python packages."""
    logger.info("Installing dependencies...")
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required Azure configs."""
    env_path = Path(".env")
    if not env_path.exists():
        logger.error("❌ .env file not found. Please ensure it exists with Azure credentials.")
        return False
    
    # Read .env file to check for required keys
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_keys = [
        "AZURE_COSMOS_ENDPOINT",
        "AZURE_COSMOS_KEY", 
        "SERVICE_BUS_CONNECTION_STRING"
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in content or f"{key}=" in content and not content.split(f"{key}=")[1].split('\n')[0].strip():
            missing_keys.append(key)
    
    if missing_keys:
        logger.error(f"❌ Missing or empty Azure credentials in .env: {missing_keys}")
        return False
    
    logger.info("✅ Azure credentials found in .env file")
    return True

def start_application():
    """Start the web application."""
    logger.info("Starting Insurance AI Agent Web UI...")
    try:
        # Import and run the application
        from ui_app import app
        import uvicorn
        
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        return False

def main():
    """Main setup and launch function."""
    print("🚀 Insurance AI Agent - Automated Setup")
    print("=" * 50)
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check environment file
    if not check_env_file():
        sys.exit(1)
    
    # Step 3: Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Step 4: Start application
    logger.info("🎉 Setup complete! Starting application...")
    start_application()

if __name__ == "__main__":
    main()
