"""
Main Application Entry Point for Insurance AI Agent System
=========================================================
Author: Rachit Patekar

This is the primary entry point for the Insurance AI Agent system. It orchestrates
all system components including email processing, file ingestion, OCR processing,
and AI document classification into a unified application.

System Architecture:
- FastAPI main application with sub-application mounting
- Asynchronous worker processes for different processing stages
- Multi-threaded execution for parallel processing capabilities
- Comprehensive logging and monitoring
- CORS-enabled API for frontend integration

Key Components Orchestrated:
1. Email Processor: Monitors and processes incoming emails
2. File Ingestion: Handles direct file uploads and processing
3. OCR Engine: Extracts text from documents using multiple methods
4. Document Classifier: AI-powered document categorization
5. Ingestion Engine: Coordinates data flow and storage

Processing Pipeline:
Email/File → Ingestion → OCR → Classification → Storage → Reporting

Usage:
    python main.py
    
    Access main API at: http://localhost:8080
    Email processing at: http://localhost:8080/email
    File processing at: http://localhost:8080/files

Author: Insurance AI Agent Team
Version: 1.0.0
Dependencies: fastapi, uvicorn, asyncio, threading, concurrent.futures
"""

# Standard library imports
import asyncio              # Asynchronous programming support
import logging             # Application logging and monitoring
import threading           # Multi-threading for parallel processing
from concurrent.futures import ThreadPoolExecutor  # Thread pool management

# FastAPI framework imports
from fastapi import FastAPI                         # Main web framework
from fastapi.middleware.cors import CORSMiddleware  # Cross-origin resource sharing
import uvicorn             # ASGI server for FastAPI applications

# Local application imports
from src.shared.config import settings                    # Application configuration
from src.shared.models import create_tables               # Database setup
from src.email_processor.email_listener import app as email_app      # Email processing module
from src.file_ingestion.file_listener import app as file_app         # File ingestion module
from src.ingestion_engine.ingestion_processor import start_ingestion_worker    # Ingestion coordination
from src.ocr_engine.ocr_processor import start_ocr_worker            # OCR processing
from src.ocr_engine.document_classifier import start_classification_worker    # AI classification

# ========== LOGGING CONFIGURATION ==========
# Configure comprehensive logging for the entire system
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper() if hasattr(settings, 'log_level') else 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('insurance_ai_agent.log'),  # File logging for persistence
        logging.StreamHandler()                         # Console logging for development
    ]
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

# ========== MAIN FASTAPI APPLICATION ==========
# Create the main FastAPI application that orchestrates all system components
main_app = FastAPI(
    title="Insurance AI Agent",
    description="Comprehensive insurance document processing system with AI classification and automated workflows",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI documentation
    redoc_url="/redoc"     # Alternative API documentation
)

# ========== CORS MIDDLEWARE CONFIGURATION ==========
# Enable Cross-Origin Resource Sharing for frontend applications
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (configure for production security)
    allow_credentials=True,     # Allow authentication cookies
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

# ========== SUB-APPLICATION MOUNTING ==========
# Mount specialized sub-applications for different processing workflows
main_app.mount("/email", email_app)   # Email processing and monitoring endpoints
main_app.mount("/files", file_app)    # File upload and processing endpoints

@main_app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "Insurance AI Agent System",
        "version": "1.0.0",
        "services": {
            "email_processor": "/email",
            "file_ingestion": "/files",
            "health_check": "/health"
        },
        "status": "running"
    }

@main_app.get("/health")
async def health_check():
    """Health check endpoint for the entire system."""
    return {
        "status": "healthy",
        "services": {
            "email_processor": "running",
            "file_ingestion": "running",
            "ingestion_engine": "running",
            "ocr_engine": "running",
            "document_classifier": "running"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }

@main_app.get("/status")
async def get_system_status():
    """Get detailed system status and metrics."""
    try:
        from src.shared.models import get_session, ProcessingRecord
        
        session = get_session()
        try:
            # Get processing statistics
            total_records = session.query(ProcessingRecord).count()
            pending_records = session.query(ProcessingRecord).filter_by(status="pending").count()
            processing_records = session.query(ProcessingRecord).filter_by(status="processing").count()
            completed_records = session.query(ProcessingRecord).filter_by(status="completed").count()
            failed_records = session.query(ProcessingRecord).filter_by(status="failed").count()
            
            return {
                "system_status": "operational",
                "statistics": {
                    "total_documents": total_records,
                    "pending": pending_records,
                    "processing": processing_records,
                    "completed": completed_records,
                    "failed": failed_records
                },
                "services": {
                    "database": "connected",
                    "blob_storage": "connected",
                    "service_bus": "connected"
                }
            }
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "system_status": "error",
            "error": str(e),
            "services": {
                "database": "error",
                "blob_storage": "unknown",
                "service_bus": "unknown"
            }
        }

def start_background_workers():
    """Start background worker processes."""
    logger.info("Starting background workers...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Start workers in separate threads
        executor.submit(start_ingestion_worker)
        executor.submit(start_ocr_worker)
        executor.submit(start_classification_worker)

def initialize_database():
    """Initialize database tables."""
    try:
        logger.info("Initializing database...")
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

async def startup_event():
    """Startup event handler."""
    logger.info("Starting Insurance AI Agent system...")
    
    # Initialize database
    initialize_database()
    
    # Start background workers in a separate thread
    worker_thread = threading.Thread(target=start_background_workers, daemon=True)
    worker_thread.start()
    
    logger.info("Insurance AI Agent system started successfully")

async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Insurance AI Agent system...")

# Add event handlers
main_app.add_event_handler("startup", startup_event)
main_app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    # Run the main application
    uvicorn.run(
        "main:main_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
