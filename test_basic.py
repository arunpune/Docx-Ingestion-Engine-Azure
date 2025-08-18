"""
Basic configuration test - simplified version without complex dependencies.
"""
import os

def test_basic_config():
    """Test basic configuration loading."""
    print("=== Testing Basic Configuration ===")
    
    # Test environment loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded")
    except ImportError:
        print("✗ python-dotenv not installed")
        return False
    
    # Test basic settings
    debug = os.getenv("DEBUG", "False").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "INFO")
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    database_url = os.getenv("DATABASE_URL", "sqlite:///insurance_ai.db")
    
    print(f"Debug mode: {debug}")
    print(f"Log level: {log_level}")
    print(f"API host: {api_host}")
    print(f"API port: {api_port}")
    print(f"Database URL: {database_url}")
    
    return True

def test_basic_imports():
    """Test basic Python imports."""
    print("\n=== Testing Basic Imports ===")
    
    # Test FastAPI
    try:
        import fastapi
        print("✓ FastAPI available")
    except ImportError:
        print("✗ FastAPI not installed - run: pip install fastapi")
        return False
    
    # Test Uvicorn
    try:
        import uvicorn
        print("✓ Uvicorn available")
    except ImportError:
        print("✗ Uvicorn not installed - run: pip install uvicorn")
        return False
    
    # Test SQLAlchemy
    try:
        import sqlalchemy
        print("✓ SQLAlchemy available")
    except ImportError:
        print("✗ SQLAlchemy not installed - run: pip install sqlalchemy")
        return False
    
    # Test Requests
    try:
        import requests
        print("✓ Requests available")
    except ImportError:
        print("✗ Requests not installed - run: pip install requests")
        return False
    
    return True

def test_optional_packages():
    """Test optional packages."""
    print("\n=== Testing Optional Packages ===")
    
    # Azure packages
    try:
        import azure.storage.blob
        print("✓ Azure Storage Blob available")
    except ImportError:
        print("⚠ Azure Storage Blob not installed (optional)")
    
    try:
        import azure.servicebus
        print("✓ Azure Service Bus available")
    except ImportError:
        print("⚠ Azure Service Bus not installed (optional)")
    
    # OpenAI
    try:
        import openai
        print("✓ OpenAI available")
    except ImportError:
        print("⚠ OpenAI not installed (optional)")

if __name__ == "__main__":
    print("Insurance AI Agent - Basic Configuration Test")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_basic_config()
    success &= test_basic_imports()
    test_optional_packages()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Basic setup is working!")
        print("\nNext steps:")
        print("1. Create .env file with your configuration")
        print("2. Run: python simple_server.py")
        print("3. Open: http://localhost:8000")
    else:
        print("✗ Setup has issues - please install missing packages")
        print("\nTo install core packages:")
        print("pip install fastapi uvicorn sqlalchemy requests python-dotenv")
    
    print("=" * 50)
