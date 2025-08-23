"""
Azure Logic App Email Listener for Insurance AI Agent
=====================================================
Author: Rachit Patekar

This module provides HTTP endpoints for receiving email processing requests from Azure Logic Apps.
It serves as the bridge between Azure's email monitoring services and the Insurance AI Agent
processing pipeline, handling email file uploads and processing orchestration.

Key Features:
- FastAPI-based REST endpoints for Logic App integration
- Email file upload handling (.eml, .msg formats)
- Temporary file management for processing
- Error handling and validation
- Processing status tracking and response
- Metadata handling for email context

Integration Architecture:
1. Azure Logic App monitors email services (Office 365, Gmail, etc.)
2. Logic App detects new emails with attachments
3. Logic App uploads email files to this listener endpoint
4. Listener validates and processes email files
5. Processing results returned to Logic App for further workflow

Supported Email Formats:
- .eml files (RFC 822 standard email format)
- .msg files (Microsoft Outlook email format)

API Endpoints:
- POST /process-email: Main email processing endpoint
- GET /health: Health check endpoint for monitoring
- GET /status/{processing_id}: Check processing status

Author: Email Integration Team
Version: 1.0
Dependencies: fastapi, pydantic, azure-servicebus
"""

# Standard library imports
import logging      # Application logging functionality
import tempfile     # Temporary file handling
import os          # Operating system interface

# Third-party imports
from fastapi import FastAPI, HTTPException, UploadFile, File, Form  # Web framework
from fastapi.responses import JSONResponse                          # HTTP responses
from pydantic import BaseModel                                     # Data validation
from typing import Optional                                        # Type hints

# Local application imports
from .email_handler import process_email_from_file  # Email processing logic

# Initialize logger for this module
logger = logging.getLogger(__name__)

# ========== FASTAPI APPLICATION INITIALIZATION ==========
# Initialize FastAPI application with metadata
app = FastAPI(
    title="Insurance AI Agent - Email Processor",
    description="Azure Logic App integration endpoint for email processing",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI documentation
    redoc_url="/redoc"     # ReDoc documentation
)


# ========== PYDANTIC DATA MODELS ==========
class EmailProcessingRequest(BaseModel):
    """
    Request model for email processing operations.
    
    This model defines the structure for email processing requests,
    supporting both direct file uploads and URL-based file references.
    
    Attributes:
        email_file_url (Optional[str]): URL to email file in Azure Blob Storage
        metadata (Optional[dict]): Additional metadata about the email processing request
    """
    email_file_url: Optional[str] = None    # Azure Blob URL for email file
    metadata: Optional[dict] = None         # Additional processing metadata


class EmailProcessingResponse(BaseModel):
    """
    Response model for email processing operations.
    
    This model defines the structure for email processing responses,
    providing status information and tracking capabilities.
    
    Attributes:
        processing_id (str): Unique identifier for tracking processing operation
        status (str): Current processing status (success, error, pending)
        message (str): Human-readable message about processing result
    """
    processing_id: str    # Unique processing identifier
    status: str          # Processing status indicator
    message: str         # Descriptive message about processing result


# ========== EMAIL PROCESSING ENDPOINT ==========
@app.post("/process-email", response_model=EmailProcessingResponse)
async def process_email_endpoint(
    email_file: UploadFile = File(...),           # Uploaded email file
    metadata: Optional[str] = Form(None)          # Optional metadata as form field
):
    """
    Process an uploaded email file from Azure Logic Apps.
    
    This endpoint serves as the primary integration point between Azure Logic Apps
    and the Insurance AI Agent email processing pipeline. It receives email files,
    validates formats, and initiates the comprehensive processing workflow.
    
    Args:
        email_file (UploadFile): Uploaded email file (.eml or .msg format)
        metadata (Optional[str]): JSON string containing additional metadata
        
    Returns:
        EmailProcessingResponse: Processing result with unique ID and status
        
    Raises:
        HTTPException: If file format is invalid or processing fails
        
    Processing Workflow:
    1. Validate email file format (.eml or .msg)
    2. Save uploaded file to temporary location
    3. Process email through EmailHandler
    4. Extract attachments and metadata
    5. Upload to Azure Blob Storage
    6. Create database records
    7. Return processing ID for tracking
    
    Error Handling:
    - File format validation with descriptive errors
    - Temporary file cleanup on success/failure
    - Comprehensive error logging for debugging
    - Structured error responses for Logic App handling
    """
    try:
        # ========== FILE FORMAT VALIDATION ==========
        # Validate that uploaded file has supported email format
        if not email_file.filename.endswith(('.eml', '.msg')):
            logger.error(f"Invalid file type uploaded: {email_file.filename}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only .eml and .msg files are supported."
            )
        
        logger.info(f"Processing email file: {email_file.filename}")
        
        # ========== TEMPORARY FILE MANAGEMENT ==========
        # Save uploaded file temporarily for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{email_file.filename}") as temp_file:
            content = await email_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the email file
            processing_id = process_email_from_file(temp_file_path)
            
            logger.info(f"Email processed successfully: {email_file.filename}, Processing ID: {processing_id}")
            
            return EmailProcessingResponse(
                processing_id=processing_id,
                status="success",
                message=f"Email processed successfully. Processing ID: {processing_id}"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@app.post("/process-email-url", response_model=EmailProcessingResponse)
async def process_email_from_url(request: EmailProcessingRequest):
    """
    Process an email file from a URL.
    
    This endpoint receives a URL to an email file and processes it.
    """
    try:
        if not request.email_file_url:
            raise HTTPException(status_code=400, detail="email_file_url is required")
        
        # Download the file from URL
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(request.email_file_url)
            response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Process the email file
            processing_id = process_email_from_file(temp_file_path)
            
            logger.info(f"Email from URL processed successfully: {request.email_file_url}, Processing ID: {processing_id}")
            
            return EmailProcessingResponse(
                processing_id=processing_id,
                status="success",
                message=f"Email processed successfully. Processing ID: {processing_id}"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error processing email from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing email from URL: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "email-processor"}


if __name__ == "__main__":
    import uvicorn
    from ..shared.config import settings
    
    uvicorn.run(
        "email_listener:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
