"""
Simple startup script to test the basic functionality.
"""
from src.shared.config import settings

def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    print(f"Debug mode: {settings.debug}")
    print(f"Log level: {settings.log_level}")
    print(f"API host: {settings.api_host}")
    print(f"API port: {settings.api_port}")
    print("Configuration test completed!")

def test_imports():
    """Test basic imports."""
    print("Testing imports...")
    
    try:
        from src.shared import utils
        print("✓ Shared utilities imported")
    except ImportError as e:
        print(f"✗ Failed to import shared utilities: {e}")
    
    try:
        from src.shared import models
        print("✓ Database models imported")
    except ImportError as e:
        print(f"✗ Failed to import database models: {e}")
    
    try:
        from src.email_processor import email_handler
        print("✓ Email processor imported")
    except ImportError as e:
        print(f"✗ Failed to import email processor: {e}")
    
    try:
        from src.file_ingestion import file_handler
        print("✓ File ingestion imported")
    except ImportError as e:
        print(f"✗ Failed to import file ingestion: {e}")
    
    print("Import tests completed!")

if __name__ == "__main__":
    print("=== Insurance AI Agent - Basic Test ===")
    print()
    
    test_config()
    print()
    
    test_imports()
    print()
    
    print("=== Test completed ===")
    print()
    print("To run the full system:")
    print("1. Configure .env file with your Azure credentials")
    print("2. Install additional dependencies: pip install -r requirements.txt")
    print("3. Run: python main.py")
