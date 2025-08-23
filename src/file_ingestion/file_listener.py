"""
Direct File Upload API for Insurance AI Agent
=============================================
Author: Shrvan Hatte

This module provides comprehensive HTTP endpoints for direct file uploads to the Insurance AI Agent system.
It serves as the integration point for external systems (like Google Forms, web portals, or third-party
applications) to submit insurance documents for processing and analysis.

Key Features:
- FastAPI-based REST endpoints for file upload handling
- Multiple file format support (PDF, Word, images, text)
- Batch file processing capabilities
- File validation and size limits
- Temporary file management with automatic cleanup
- Error handling and detailed response messages
- Health check endpoints for monitoring

Integration Use Cases:
1. Google Forms integration for document submission
2. Web portal file uploads from insurance clients
3. Third-party system integration via REST API
4. Batch document processing from external sources
5. Mobile app file upload support

Supported File Formats:
- PDF documents (.pdf) - Primary insurance document format
- Microsoft Word (.doc, .docx) - Policy documents and contracts
- Image files (.jpg, .jpeg, .png, .tiff) - Scanned documents and photos
- Text files (.txt) - Plain text insurance documents

File Processing Pipeline:
1. File Upload → Receive and validate uploaded files
2. Format Validation → Check file type and size limits
3. Temporary Storage → Save files securely for processing
4. Processing Trigger → Initiate document analysis workflow
5. Cleanup → Remove temporary files after processing
6. Response → Return processing ID and status

Security Features:
- File type validation to prevent malicious uploads
- File size limits to prevent system overload
- Temporary file cleanup to prevent storage bloat
- Error handling to prevent information disclosure

API Endpoints:
- POST /upload-file: Single file upload processing
- POST /upload-files: Batch file upload processing
- GET /health: Service health check
- GET /supported-formats: List of supported file types

Author: File Integration Team
Version: 1.0
Dependencies: fastapi, pydantic, tempfile, os
"""

# Standard library imports
import logging      # Application logging functionality
import tempfile     # Temporary file handling for upload processing
import os          # Operating system interface for file operations

# Third-party imports
from fastapi import FastAPI, HTTPException, UploadFile, File, Form  # Web framework components
from fastapi.responses import JSONResponse                          # HTTP JSON responses
from pydantic import BaseModel                                     # Data validation models
from typing import Optional, List                                  # Type hints for better code documentation

# Local application imports
from .file_handler import process_uploaded_file  # Core file processing logic

# Initialize logger for this module with proper naming
logger = logging.getLogger(__name__)

# ========== FASTAPI APPLICATION INITIALIZATION ==========
# Initialize FastAPI application with comprehensive metadata
app = FastAPI(
    title="Insurance AI Agent - File Ingestion",              # Application title for documentation
    description="Direct file upload API for insurance document processing",  # Detailed description
    version="1.0.0",                                          # Version for API versioning
    docs_url="/docs",                                         # Swagger UI documentation endpoint
    redoc_url="/redoc"                                        # ReDoc documentation endpoint
)


# ========== PYDANTIC DATA MODELS ==========
class FileProcessingResponse(BaseModel):
    """
    Response model for individual file processing operations.
    
    This model defines the structure for single file processing responses,
    providing comprehensive status information and tracking capabilities.
    
    Attributes:
        processing_id (str): Unique identifier for tracking the file processing operation
        status (str): Processing status indicator (success, failed, pending)
        message (str): Human-readable message describing the processing result
        filename (str): Original filename of the processed file
        
    Example Response:
        {
            "processing_id": "proc_12345678",
            "status": "success",
            "message": "File processed successfully. Processing ID: proc_12345678",
            "filename": "insurance_policy.pdf"
        }
    """
    processing_id: str    # Unique processing identifier for tracking
    status: str          # Processing status (success/failed/pending)
    message: str         # Descriptive message about processing result
    filename: str        # Original filename for reference


class BatchFileProcessingResponse(BaseModel):
    """
    Response model for batch file processing operations.
    
    This model defines the structure for multiple file processing responses,
    providing summary statistics and individual file results for bulk uploads.
    
    Attributes:
        results (List[FileProcessingResponse]): List of individual file processing results
        total_files (int): Total number of files in the batch
        successful (int): Number of files processed successfully
        failed (int): Number of files that failed processing
        
    Example Response:
        {
            "results": [...],
            "total_files": 5,
            "successful": 4,
            "failed": 1
        }
    """
    results: List[FileProcessingResponse]    # Individual file processing results
    total_files: int                        # Total count of files processed
    successful: int                         # Count of successful processings
    failed: int                            # Count of failed processings


# ========== SINGLE FILE UPLOAD ENDPOINT ==========
@app.post("/upload-file", response_model=FileProcessingResponse)
async def upload_file_endpoint(
    file: UploadFile = File(...),           # Uploaded file from multipart form
    description: Optional[str] = Form(None) # Optional description metadata
):
    """
    Upload and process a single insurance document file.
    
    This endpoint serves as the primary integration point for external systems
    to submit individual insurance documents for processing and analysis.
    It handles file validation, temporary storage, and processing initiation.
    
    Args:
        file (UploadFile): Uploaded file object from multipart form data
        description (Optional[str]): Optional description or metadata about the file
        
    Returns:
        FileProcessingResponse: Processing result with unique ID and status
        
    Raises:
        HTTPException: 
            - 400: Invalid file type or size exceeds limit
            - 500: Internal processing error
            
    Processing Workflow:
    1. Validate file format against allowed extensions
    2. Check file size against maximum limit (50MB)
    3. Save file to temporary location for processing
    4. Process file through FileHandler
    5. Clean up temporary files
    6. Return processing ID and status
    
    Supported File Types:
    - PDF documents (.pdf) - Insurance policies, certificates
    - Word documents (.doc, .docx) - Contracts and agreements
    - Images (.jpg, .jpeg, .png, .tiff) - Scanned documents
    - Text files (.txt) - Plain text insurance documents
    
    Integration Examples:
    - Google Forms file upload processing
    - Web portal document submission
    - Mobile app file uploads
    - Third-party system integration
    """
    try:
        # ========== FILE FORMAT VALIDATION ==========
        # Define allowed file extensions for insurance document processing
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        
        # Extract file extension and normalize to lowercase
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Validate file type against allowed extensions
        if file_extension not in allowed_extensions:
            logger.error(f"Invalid file type uploaded: {file.filename} (extension: {file_extension})")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # ========== FILE SIZE VALIDATION ==========
        # Define maximum file size limit (50MB for reasonable upload times)
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        
        # Read file content to check size
        content = await file.read()
        
        # Validate file size against maximum limit
        if len(content) > max_size:
            logger.error(f"File size exceeds limit: {file.filename} ({len(content)} bytes > {max_size} bytes)")
            raise HTTPException(
                status_code=400, 
                detail="File size exceeds 50MB limit"
            )
        
        logger.info(f"Processing file upload: {file.filename} ({len(content)} bytes, type: {file_extension})")
        
        # ========== TEMPORARY FILE MANAGEMENT ==========
        # Save uploaded file to temporary location for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the file
            processing_id = process_uploaded_file(temp_file_path, file.filename)
            
            logger.info(f"File processed successfully: {file.filename}, Processing ID: {processing_id}")
            
            return FileProcessingResponse(
                processing_id=processing_id,
                status="success",
                message=f"File processed successfully. Processing ID: {processing_id}",
                filename=file.filename
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/upload-files", response_model=BatchFileProcessingResponse)
async def upload_multiple_files_endpoint(
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None)
):
    """
    Upload and process multiple files.
    
    This endpoint receives multiple file uploads and processes them in batch.
    """
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            # Validate file type
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                results.append(FileProcessingResponse(
                    processing_id="",
                    status="failed",
                    message=f"Unsupported file type: {file_extension}",
                    filename=file.filename
                ))
                failed += 1
                continue
            
            # Check file size
            max_size = 50 * 1024 * 1024  # 50MB
            content = await file.read()
            
            if len(content) > max_size:
                results.append(FileProcessingResponse(
                    processing_id="",
                    status="failed",
                    message="File size exceeds 50MB limit",
                    filename=file.filename
                ))
                failed += 1
                continue
            
            # Save and process file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                processing_id = process_uploaded_file(temp_file_path, file.filename)
                
                results.append(FileProcessingResponse(
                    processing_id=processing_id,
                    status="success",
                    message=f"File processed successfully. Processing ID: {processing_id}",
                    filename=file.filename
                ))
                successful += 1
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            results.append(FileProcessingResponse(
                processing_id="",
                status="failed",
                message=f"Error processing file: {str(e)}",
                filename=file.filename
            ))
            failed += 1
    
    return BatchFileProcessingResponse(
        results=results,
        total_files=len(files),
        successful=successful,
        failed=failed
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "file-ingestion"}


@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    return {
        "supported_formats": [
            {"extension": ".pdf", "description": "PDF documents"},
            {"extension": ".doc", "description": "Microsoft Word documents (legacy)"},
            {"extension": ".docx", "description": "Microsoft Word documents"},
            {"extension": ".txt", "description": "Plain text files"},
            {"extension": ".jpg", "description": "JPEG images"},
            {"extension": ".jpeg", "description": "JPEG images"},
            {"extension": ".png", "description": "PNG images"},
            {"extension": ".tiff", "description": "TIFF images"},
            {"extension": ".tif", "description": "TIFF images"}
        ],
        "max_file_size": "50MB"
    }


if __name__ == "__main__":
    import uvicorn
    from ..shared.config import settings
    
    uvicorn.run(
        "file_listener:app",
        host=settings.api_host,
        port=settings.api_port + 1,  # Run on different port from email processor
        reload=settings.debug
    )
