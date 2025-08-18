"""
Simple API server for testing the Insurance AI Agent system.
"""
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Create FastAPI app
app = FastAPI(
    title="Insurance AI Agent - Simple Server",
    description="Basic API server for testing the Insurance AI Agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Insurance AI Agent - Simple Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "test": "/test"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
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
