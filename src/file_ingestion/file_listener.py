"""
File upload API for direct file ingestion.
This module provides HTTP endpoints for file uploads (Google Forms integration).
"""
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
from .file_handler import process_uploaded_file

logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance AI Agent - File Ingestion", version="1.0.0")


class FileProcessingResponse(BaseModel):
    """Response model for file processing."""
    processing_id: str
    status: str
    message: str
    filename: str


class BatchFileProcessingResponse(BaseModel):
    """Response model for batch file processing."""
    results: List[FileProcessingResponse]
    total_files: int
    successful: int
    failed: int


@app.post("/upload-file", response_model=FileProcessingResponse)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """
    Upload and process a single file.
    
    This endpoint receives file uploads (e.g., from Google Forms) and processes them.
    """
    try:
        # Validate file type (PDF files primarily)
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        content = await file.read()
        
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
        
        # Save uploaded file temporarily
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
