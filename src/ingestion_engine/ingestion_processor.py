"""
Ingestion Engine - Processes messages from email and file processors.
Creates transactional records and coordinates OCR processing.
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from ..shared.config import settings
from ..shared.models import get_session, ProcessingRecord, AttachmentRecord
from ..shared.utils import send_to_service_bus

logger = logging.getLogger(__name__)


class IngestionEngine:
    """Handles ingestion of processed emails and files, coordinates OCR processing."""
    
    def __init__(self):
        self.session = get_session()
    
    def process_ingestion_message(self, message: Dict) -> bool:
        """
        Process an ingestion message from Service Bus.
        
        Args:
            message: Message dictionary containing processing information
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            processing_id = message.get("processing_id")
            source_type = message.get("source_type")
            
            if not processing_id:
                logger.error("Processing ID not found in message")
                return False
            
            logger.info(f"Processing ingestion message for ID: {processing_id}, Type: {source_type}")
            
            # Get processing record from database
            processing_record = self.session.query(ProcessingRecord).filter_by(
                unique_processing_id=processing_id
            ).first()
            
            if not processing_record:
                logger.error(f"Processing record not found for ID: {processing_id}")
                return False
            
            # Update status to processing
            processing_record.status = "processing"
            processing_record.updated_at = datetime.utcnow()
            self.session.commit()
            
            if source_type == "email":
                return self._process_email_ingestion(processing_record, message)
            elif source_type == "file":
                return self._process_file_ingestion(processing_record, message)
            else:
                logger.error(f"Unknown source type: {source_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing ingestion message: {str(e)}")
            if self.session:
                self.session.rollback()
            return False
        finally:
            if self.session:
                self.session.close()
    
    def _process_email_ingestion(self, processing_record: ProcessingRecord, message: Dict) -> bool:
        """Process email ingestion and send attachments to OCR."""
        try:
            attachments = message.get("attachments", [])
            
            if not attachments:
                logger.info(f"No attachments found for email processing ID: {processing_record.unique_processing_id}")
                processing_record.status = "completed"
                self.session.commit()
                return True
            
            # Send each attachment to OCR engine
            for attachment in attachments:
                self._send_to_ocr_engine(
                    processing_record.unique_processing_id,
                    attachment["uri"],
                    attachment["filename"]
                )
            
            processing_record.status = "ocr_pending"
            self.session.commit()
            
            logger.info(f"Email ingestion completed for ID: {processing_record.unique_processing_id}, "
                       f"Sent {len(attachments)} attachments to OCR")
            return True
            
        except Exception as e:
            logger.error(f"Error processing email ingestion: {str(e)}")
            processing_record.status = "failed"
            self.session.commit()
            return False
    
    def _process_file_ingestion(self, processing_record: ProcessingRecord, message: Dict) -> bool:
        """Process file ingestion and send file to OCR."""
        try:
            file_uri = message.get("file_uri")
            file_metadata = message.get("file_metadata", {})
            
            if not file_uri:
                logger.error(f"File URI not found for processing ID: {processing_record.unique_processing_id}")
                processing_record.status = "failed"
                self.session.commit()
                return False
            
            # Send file to OCR engine
            self._send_to_ocr_engine(
                processing_record.unique_processing_id,
                file_uri,
                file_metadata.get("filename", "unknown")
            )
            
            processing_record.status = "ocr_pending"
            self.session.commit()
            
            logger.info(f"File ingestion completed for ID: {processing_record.unique_processing_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file ingestion: {str(e)}")
            processing_record.status = "failed"
            self.session.commit()
            return False
    
    def _send_to_ocr_engine(self, processing_id: str, file_uri: str, filename: str):
        """Send file to OCR engine for text extraction."""
        try:
            ocr_message = {
                "processing_id": processing_id,
                "file_uri": file_uri,
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
                "action": "extract_text"
            }
            
            # Send to OCR queue (using a different queue name)
            send_to_service_bus(ocr_message, "ocr-processing-queue")
            
            logger.info(f"Sent file to OCR engine: {filename}, Processing ID: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error sending to OCR engine: {str(e)}")
            raise
    
    def update_processing_status(self, processing_id: str, status: str, error_message: Optional[str] = None):
        """Update the status of a processing record."""
        try:
            processing_record = self.session.query(ProcessingRecord).filter_by(
                unique_processing_id=processing_id
            ).first()
            
            if processing_record:
                processing_record.status = status
                processing_record.updated_at = datetime.utcnow()
                self.session.commit()
                
                logger.info(f"Updated processing status for ID {processing_id}: {status}")
            else:
                logger.error(f"Processing record not found for ID: {processing_id}")
                
        except Exception as e:
            logger.error(f"Error updating processing status: {str(e)}")
            if self.session:
                self.session.rollback()
        finally:
            if self.session:
                self.session.close()


class IngestionWorker:
    """Worker class for processing Service Bus messages."""
    
    def __init__(self):
        self.engine = IngestionEngine()
    
    def start_listening(self):
        """Start listening for messages from Service Bus."""
        from azure.servicebus import ServiceBusClient
        
        try:
            with ServiceBusClient.from_connection_string(settings.service_bus_connection_string) as client:
                with client.get_queue_receiver(queue_name=settings.service_bus_queue_name) as receiver:
                    logger.info("Ingestion worker started, listening for messages...")
                    
                    for message in receiver:
                        try:
                            # Parse message body
                            message_body = json.loads(str(message))
                            logger.info(f"Received message: {message_body.get('processing_id')}")
                            
                            # Process the message
                            success = self.engine.process_ingestion_message(message_body)
                            
                            if success:
                                # Complete the message (remove from queue)
                                receiver.complete_message(message)
                                logger.info("Message processed successfully")
                            else:
                                # Abandon the message (it will be retried)
                                receiver.abandon_message(message)
                                logger.error("Message processing failed, message abandoned")
                                
                        except Exception as e:
                            logger.error(f"Error processing Service Bus message: {str(e)}")
                            # Dead letter the message if processing fails repeatedly
                            receiver.dead_letter_message(message)
                            
        except Exception as e:
            logger.error(f"Error in ingestion worker: {str(e)}")
            raise


def start_ingestion_worker():
    """Start the ingestion worker."""
    worker = IngestionWorker()
    worker.start_listening()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the worker
    start_ingestion_worker()
