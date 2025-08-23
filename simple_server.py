"""
Simple API Server for Insurance AI Agent Testing
================================================
Author: Shrvan Hatte

This module provides a lightweight FastAPI server for testing and development
of the Insurance AI Agent system. It offers basic endpoints for system health
checks, configuration validation, and integration testing.

Purpose:
- Development and testing environment setup
- System health monitoring and diagnostics
- Configuration validation and troubleshooting
- Basic API functionality testing
- CORS-enabled for frontend development

Key Features:
- FastAPI framework with automatic API documentation
- CORS middleware for cross-origin requests
- Environment variable configuration
- Health check endpoints for monitoring
- Integration testing capabilities
- Lightweight and fast startup for development

Usage:
    python simple_server.py
    
    Access API documentation at: http://localhost:8000/docs
    Health check at: http://localhost:8000/health

Author: Insurance AI Agent Team
Version: 1.0.0
Dependencies: fastapi, uvicorn, python-dotenv
"""

# Standard library imports
import os  # Operating system interface for environment variables

# FastAPI framework imports
from fastapi import FastAPI                    # Main FastAPI application
from fastapi.responses import JSONResponse     # JSON response handling
from fastapi.middleware.cors import CORSMiddleware  # Cross-origin resource sharing

# Environment configuration with error handling
try:
    from dotenv import load_dotenv  # Environment variable loading
    load_dotenv()  # Load variables from .env file
except ImportError:
    # Gracefully handle missing python-dotenv package
    pass

# ========== FASTAPI APPLICATION SETUP ==========
# Create FastAPI application instance with comprehensive metadata
app = FastAPI(
    title="Insurance AI Agent - Simple Server",
    description="Basic API server for testing and development of the Insurance AI Agent system",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI documentation endpoint
    redoc_url="/redoc"     # ReDoc alternative documentation endpoint
)

# ========== CORS MIDDLEWARE CONFIGURATION ==========
# Enable Cross-Origin Resource Sharing for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (restrict in production)
    allow_credentials=True,     # Allow cookies and authentication
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

# ========== API ENDPOINTS ==========

@app.get("/")
async def root():
    """
    Root endpoint providing system information and available endpoints.
    
    Returns basic information about the Insurance AI Agent system including
    version, status, and available API endpoints for navigation.
    
    Returns:
        dict: System information and endpoint directory
    """
    return {
        "message": "Insurance AI Agent - Simple Server",
        "version": "1.0.0",
        "status": "running",
        "description": "Development and testing server for Insurance AI Agent",
        "endpoints": {
            "health": "/health",           # System health check
            "docs": "/docs",               # Swagger API documentation
            "redoc": "/redoc",             # Alternative API documentation
            "test": "/test",               # Basic functionality test
            "config": "/config"            # Configuration information
        }
    }

@app.get("/health")
async def health_check():
    """
    System health check endpoint for monitoring and diagnostics.
    
    Provides comprehensive system health information including server status,
    environment configuration, and basic system diagnostics.
    
    Returns:
        dict: Health status and system diagnostics information
    """
    return {
        "status": "healthy",
        "service": "insurance-ai-agent-simple",
        "version": "1.0.0"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the API is working."""
    config = {
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///insurance_ai.db"),
        "api_port": int(os.getenv("API_PORT", "8000"))
    }
    
    return {
        "message": "Test endpoint working",
        "configuration": config,
        "environment_loaded": True
    }

@app.post("/upload-test")
async def upload_test():
    """Test upload endpoint."""
    return {
        "message": "Upload endpoint working",
        "note": "This is a test endpoint - full upload functionality requires additional setup"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Insurance AI Agent Simple Server...")
    print(f"Server will be available at: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Debug mode: {debug}")
    
    uvicorn.run(
        "simple_server:app",
        host=host,
        port=port,
        reload=debug
    )
