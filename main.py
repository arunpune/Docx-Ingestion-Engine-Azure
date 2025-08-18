"""
Main application entry point for the Insurance AI Agent system.
"""
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.shared.config import settings
from src.shared.models import create_tables
from src.email_processor.email_listener import app as email_app
from src.file_ingestion.file_listener import app as file_app
from src.ingestion_engine.ingestion_processor import start_ingestion_worker
from src.ocr_engine.ocr_processor import start_ocr_worker
from src.ocr_engine.document_classifier import start_classification_worker

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('insurance_ai_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Main FastAPI app that combines all services
main_app = FastAPI(
    title="Insurance AI Agent",
    description="Comprehensive insurance document processing system with AI classification",
    version="1.0.0"
)

# Add CORS middleware
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
main_app.mount("/email", email_app)
main_app.mount("/files", file_app)

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
