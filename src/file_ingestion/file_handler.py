"""
Direct File Ingestion Module for Insurance AI Agent
===================================================
Author: Shrvan Hatte

This module handles direct file uploads and processing for the Insurance AI Agent system.
It provides capabilities for processing individual insurance documents that are uploaded
directly to the system (not through email attachments).

Key Features:
- Direct file upload processing (PDF, images, documents)
- File metadata extraction and validation
- Azure Blob Storage integration for file storage
- Database integration for processing record management
- Service Bus messaging for asynchronous processing
- Support for multiple file formats (PDF, DOCX, images)

File Processing Pipeline:
1. Receive uploaded file and validate format
2. Extract file metadata (size, type, creation date)
3. Upload file to Azure Blob Storage
4. Create database records for tracking
5. Send processing messages to Service Bus queues
6. Trigger downstream document classification

Supported File Types:
- PDF documents (.pdf)
- Microsoft Word documents (.docx, .doc)
- Image files (.jpg, .jpeg, .png, .tiff)
- Text files (.txt)

Author: File Processing Team
Version: 1.0
Dependencies: azure-storage-blob, azure-servicebus, sqlalchemy
"""

# Standard library imports
import logging                  # Application logging functionality
from datetime import datetime  # Date and time operations
from typing import Dict, Optional  # Type hints for better code documentation
import os                      # Operating system interface

# Local application imports
from ..shared.config import settings  # Application configuration
from ..shared.utils import upload_file_to_blob, generate_unique_id, send_to_service_bus, extract_file_metadata
from ..shared.models import get_session, ProcessingRecord  # Database models

# Initialize logger for this module
logger = logging.getLogger(__name__)


class FileIngestor:
    """
    Direct File Ingestion Engine for Insurance AI Agent
    ===================================================
    
    This class provides comprehensive file ingestion capabilities for the Insurance AI Agent,
    handling direct file uploads, metadata extraction, Azure storage integration, and
    database record management for insurance document processing workflows.
    
    Core Responsibilities:
    - Process direct file uploads (non-email sources)
    - Extract and validate file metadata
    - Upload files to Azure Blob Storage with organized structure
    - Create database records for processing tracking
    - Send processing messages to Azure Service Bus
    - Generate secure private URLs for file access
    
    Processing Architecture:
    1. File Receipt → Validate format and extract metadata
    2. Azure Storage Upload → Store files in organized structure
    3. Database Record Creation → Track processing status
    4. Service Bus Messaging → Trigger downstream processing
    5. Classification Pipeline → Document type identification
    
    Integration Points:
    - Azure Blob Storage: File storage and retrieval
    - Azure Service Bus: Asynchronous message processing
    - SQLAlchemy Database: Processing record management
    - Insurance Classification: Document type identification
    
    Supported File Operations:
    - Single file upload processing
    - Batch file processing (future enhancement)
    - File validation and metadata extraction
    - Secure storage with access control
    
    Author: File Processing Team
    Created: 2024
    Last Modified: 2024
    """
    
    def __init__(self):
        """
        Initialize the FileIngestor with database session.
        
        Sets up database connection for processing record management
        and prepares the file ingestion engine for operation.
        """
        # ========== DATABASE SESSION INITIALIZATION ==========
        # Initialize database session for processing records
        self.session = get_session()
        logger.info("FileIngestor initialized with database session")
    
    def process_file(self, file_path: str, original_filename: Optional[str] = None) -> str:
        """
        Process a direct file upload for insurance document analysis.
        
        This is the main entry point for direct file processing. It handles file
        validation, metadata extraction, Azure storage upload, database record
        creation, and triggers downstream processing workflows.
        
        Args:
            file_path (str): Local filesystem path to the uploaded file
            original_filename (Optional[str]): Original filename if different from file_path
                                              (useful for temporary files with generated names)
            
        Returns:
            str: Unique processing ID for tracking this file processing operation
            
        Raises:
            FileNotFoundError: If the file doesn't exist at specified path
            ValueError: If file format is not supported
            Exception: If file processing fails
            
        Processing Steps:
            1. Generate unique processing ID
            2. Extract and validate file metadata
            3. Upload file to Azure Blob Storage
            4. Create database records for tracking
            5. Send processing messages to Service Bus
            6. Return processing ID for client tracking
        
        Supported File Types:
            - PDF documents (.pdf)
            - Microsoft Word (.docx, .doc)
            - Image files (.jpg, .jpeg, .png, .tiff)
            - Text files (.txt)
        """
        try:
            # ========== PROCESSING ID GENERATION ==========
            # Generate unique identifier for this processing operation
            # This ID is used to track the entire file processing workflow
            processing_id = generate_unique_id()
            logger.info(f"Starting file processing with ID: {processing_id}")
            
            # ========== FILE METADATA EXTRACTION ==========
            # Extract comprehensive metadata from the uploaded file
            # Includes filename, size, MIME type, creation date, etc.
            file_metadata = extract_file_metadata(file_path)
            
            # Use original filename if provided (for temporary files)
            if original_filename:
                file_metadata['filename'] = original_filename
                logger.info(f"Using original filename: {original_filename}")
            
            logger.info(f"Extracted metadata for file: {file_metadata.get('filename', 'Unknown')}")
            
            # ========== AZURE BLOB STORAGE UPLOAD ==========
            # Upload file to Azure Blob Storage with organized structure
            # Creates folder hierarchy: files/{processing_id}/{filename}
            blob_name = f"files/{processing_id}/{file_metadata['filename']}"
            file_uri = upload_file_to_blob(file_path, blob_name)
            logger.info(f"Uploaded file to blob storage: {file_uri}")
            
            # ========== DATABASE RECORD CREATION ==========
            # Create comprehensive processing record in database
            # Stores all file metadata and processing status
            processing_record = ProcessingRecord(
                unique_processing_id=processing_id,
                source_type="file",
                filename=file_metadata['filename'],
                file_uri=file_uri,
                file_size=file_metadata['size']
            )
            
            self.session.add(processing_record)
            self.session.commit()
            
            # Send to ingestion engine
            self._send_to_ingestion_engine(processing_id, file_uri, file_metadata)
            
            logger.info(f"File processed successfully. Processing ID: {processing_id}")
            return processing_id
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            if self.session:
                self.session.rollback()
            raise
        finally:
            if self.session:
                self.session.close()
    
    def _send_to_ingestion_engine(self, processing_id: str, file_uri: str, file_metadata: Dict):
        """Send processing information to ingestion engine."""
        try:
            message = {
                "processing_id": processing_id,
                "source_type": "file",
                "file_uri": file_uri,
                "file_metadata": file_metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            send_to_service_bus(message)
            logger.info(f"Sent file processing info to ingestion engine: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error sending to ingestion engine: {str(e)}")
            raise


def process_uploaded_file(file_path: str, original_filename: Optional[str] = None) -> str:
    """
    Main function to process an uploaded file.
    
    Args:
        file_path: Path to the uploaded file
        original_filename: Original filename if different from file_path
        
    Returns:
        str: Unique processing ID
    """
    ingestor = FileIngestor()
    return ingestor.process_file(file_path, original_filename)
