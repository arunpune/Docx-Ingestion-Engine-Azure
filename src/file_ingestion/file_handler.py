"""
File ingestion module for handling direct file uploads.
"""
import logging
from datetime import datetime
from typing import Dict, Optional
import os
from ..shared.config import settings
from ..shared.utils import upload_file_to_blob, generate_unique_id, send_to_service_bus, extract_file_metadata
from ..shared.models import get_session, ProcessingRecord

logger = logging.getLogger(__name__)


class FileIngestor:
    """Handles direct file ingestion and processing."""
    
    def __init__(self):
        self.session = get_session()
    
    def process_file(self, file_path: str, original_filename: Optional[str] = None) -> str:
        """
        Process a direct file upload.
        
        Args:
            file_path: Path to the uploaded file
            original_filename: Original filename if different from file_path
            
        Returns:
            str: Unique processing ID
        """
        try:
            # Generate unique processing ID
            processing_id = generate_unique_id()
            
            # Extract file metadata
            file_metadata = extract_file_metadata(file_path)
            if original_filename:
                file_metadata['filename'] = original_filename
            
            # Upload file to blob storage
            blob_name = f"files/{processing_id}/{file_metadata['filename']}"
            file_uri = upload_file_to_blob(file_path, blob_name)
            
            # Create processing record in database
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
