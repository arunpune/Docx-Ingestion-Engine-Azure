"""
Azure Logic App listener for processing emails.
This module provides the HTTP endpoint that Logic Apps can call.
"""
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
from .email_handler import process_email_from_file

logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance AI Agent - Email Processor", version="1.0.0")


class EmailProcessingRequest(BaseModel):
    """Request model for email processing."""
    email_file_url: Optional[str] = None
    metadata: Optional[dict] = None


class EmailProcessingResponse(BaseModel):
    """Response model for email processing."""
    processing_id: str
    status: str
    message: str


@app.post("/process-email", response_model=EmailProcessingResponse)
async def process_email_endpoint(
    email_file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Process an uploaded email file.
    
    This endpoint receives email files from Azure Logic Apps and processes them.
    """
    try:
        # Validate file type
        if not email_file.filename.endswith(('.eml', '.msg')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .eml and .msg files are supported.")
        
        # Save uploaded file temporarily
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
