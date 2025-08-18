"""
OCR Engine - Handles text extraction from documents using Azure Form Recognizer and Tesseract.
"""
import logging
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import requests
from ..shared.config import settings
from ..shared.models import get_session, ProcessingRecord, OCRResult
from ..shared.utils import send_to_service_bus

logger = logging.getLogger(__name__)


class OCREngine:
    """Handles OCR and text extraction from documents."""
    
    def __init__(self):
        self.session = get_session()
    
    def process_ocr_message(self, message: Dict) -> bool:
        """
        Process an OCR message from Service Bus.
        
        Args:
            message: Message dictionary containing file information
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            processing_id = message.get("processing_id")
            file_uri = message.get("file_uri")
            filename = message.get("filename", "unknown")
            
            if not processing_id or not file_uri:
                logger.error("Processing ID or file URI not found in message")
                return False
            
            logger.info(f"Processing OCR for file: {filename}, Processing ID: {processing_id}")
            
            # Download file from blob storage
            temp_file_path = self._download_file_from_uri(file_uri, filename)
            
            try:
                # Extract text using OCR
                extracted_text, confidence_score, page_count, processing_time = self._extract_text_from_file(
                    temp_file_path, filename
                )
                
                # Save OCR result to database
                self._save_ocr_result(
                    processing_id, file_uri, extracted_text, confidence_score, 
                    page_count, processing_time
                )
                
                # Send to AI document classifier
                self._send_to_document_classifier(processing_id, file_uri, extracted_text)
                
                logger.info(f"OCR completed for file: {filename}, Processing ID: {processing_id}")
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error processing OCR message: {str(e)}")
            return False
        finally:
            if self.session:
                self.session.close()
    
    def _download_file_from_uri(self, file_uri: str, filename: str) -> str:
        """Download file from blob storage URI to temporary file."""
        try:
            # Download the file
            response = requests.get(file_uri, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            file_extension = os.path.splitext(filename)[1] or '.pdf'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            logger.info(f"Downloaded file to temporary location: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error downloading file from URI {file_uri}: {str(e)}")
            raise
    
    def _extract_text_from_file(self, file_path: str, filename: str) -> Tuple[str, str, int, int]:
        """
        Extract text from file using multiple OCR methods.
        
        Returns:
            Tuple of (extracted_text, confidence_score, page_count, processing_time_seconds)
        """
        start_time = datetime.utcnow()
        
        try:
            file_extension = os.path.splitext(filename)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                return self._extract_text_from_image(file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._extract_text_from_word(file_path)
            elif file_extension == '.txt':
                return self._extract_text_from_txt(file_path)
            else:
                # Try Azure Form Recognizer as fallback
                return self._extract_text_with_azure_form_recognizer(file_path)
                
        except Exception as e:
            logger.error(f"Error extracting text from file {filename}: {str(e)}")
            # Return empty result with error indication
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _extract_text_from_pdf(self, file_path: str) -> Tuple[str, str, int, int]:
        """Extract text from PDF file."""
        start_time = datetime.utcnow()
        
        try:
            # First try PyPDF2 for text-based PDFs
            import PyPDF2
            
            extracted_text = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        extracted_text += text + "\n"
            
            # If no text extracted, try OCR with pdf2image and tesseract
            if not extracted_text.strip():
                extracted_text = self._ocr_pdf_with_tesseract(file_path)
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            confidence_score = "0.9" if extracted_text.strip() else "0.0"
            
            return extracted_text, confidence_score, page_count, processing_time
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _ocr_pdf_with_tesseract(self, file_path: str) -> str:
        """OCR PDF using pdf2image and tesseract."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF to images
            images = convert_from_path(file_path)
            
            extracted_text = ""
            for image in images:
                # OCR each page
                text = pytesseract.image_to_string(image)
                extracted_text += text + "\n"
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error in PDF OCR with Tesseract: {str(e)}")
            return ""
    
    def _extract_text_from_image(self, file_path: str) -> Tuple[str, str, int, int]:
        """Extract text from image file using Tesseract."""
        start_time = datetime.utcnow()
        
        try:
            import pytesseract
            from PIL import Image
            
            # Open and OCR the image
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            confidence_score = "0.8" if extracted_text.strip() else "0.0"
            
            return extracted_text, confidence_score, 1, processing_time
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _extract_text_from_word(self, file_path: str) -> Tuple[str, str, int, int]:
        """Extract text from Word document."""
        start_time = datetime.utcnow()
        
        try:
            # For .docx files
            if file_path.endswith('.docx'):
                import docx
                doc = docx.Document(file_path)
                extracted_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                page_count = 1  # Approximate
            else:
                # For .doc files, would need additional library like python-docx2txt
                # For now, return empty
                extracted_text = ""
                page_count = 0
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            confidence_score = "1.0" if extracted_text.strip() else "0.0"
            
            return extracted_text, confidence_score, page_count, processing_time
            
        except Exception as e:
            logger.error(f"Error extracting text from Word document: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _extract_text_from_txt(self, file_path: str) -> Tuple[str, str, int, int]:
        """Extract text from plain text file."""
        start_time = datetime.utcnow()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                extracted_text = file.read()
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return extracted_text, "1.0", 1, processing_time
            
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _extract_text_with_azure_form_recognizer(self, file_path: str) -> Tuple[str, str, int, int]:
        """Extract text using Azure Form Recognizer."""
        start_time = datetime.utcnow()
        
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            
            # Initialize Form Recognizer client
            client = DocumentAnalysisClient(
                endpoint=settings.azure_form_recognizer_endpoint,
                credential=AzureKeyCredential(settings.azure_form_recognizer_key)
            )
            
            # Analyze document
            with open(file_path, "rb") as file:
                poller = client.begin_analyze_document("prebuilt-read", file)
                result = poller.result()
            
            # Extract text
            extracted_text = ""
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            confidence_score = "0.95"  # Azure Form Recognizer typically has high confidence
            page_count = len(result.pages)
            
            return extracted_text, confidence_score, page_count, processing_time
            
        except Exception as e:
            logger.error(f"Error with Azure Form Recognizer: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds())
            return "", "0.0", 0, processing_time
    
    def _save_ocr_result(self, processing_id: str, file_uri: str, extracted_text: str, 
                        confidence_score: str, page_count: int, processing_time: int):
        """Save OCR result to database."""
        try:
            # Get processing record ID
            processing_record = self.session.query(ProcessingRecord).filter_by(
                unique_processing_id=processing_id
            ).first()
            
            if not processing_record:
                logger.error(f"Processing record not found for ID: {processing_id}")
                return
            
            # Create OCR result record
            ocr_result = OCRResult(
                processing_record_id=processing_record.id,
                file_uri=file_uri,
                extracted_text=extracted_text,
                confidence_score=confidence_score,
                page_count=page_count,
                processing_time_seconds=processing_time,
                status="completed" if extracted_text.strip() else "failed"
            )
            
            self.session.add(ocr_result)
            self.session.commit()
            
            logger.info(f"OCR result saved for processing ID: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error saving OCR result: {str(e)}")
            if self.session:
                self.session.rollback()
    
    def _send_to_document_classifier(self, processing_id: str, file_uri: str, extracted_text: str):
        """Send extracted text to AI document classifier."""
        try:
            if not extracted_text.strip():
                logger.warning(f"No text extracted for processing ID: {processing_id}, skipping classification")
                return
            
            classifier_message = {
                "processing_id": processing_id,
                "file_uri": file_uri,
                "extracted_text": extracted_text[:10000],  # Limit text size for message
                "timestamp": datetime.utcnow().isoformat(),
                "action": "classify_document"
            }
            
            # Send to classifier queue
            send_to_service_bus(classifier_message, "document-classification-queue")
            
            logger.info(f"Sent text to document classifier for processing ID: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error sending to document classifier: {str(e)}")


class OCRWorker:
    """Worker class for processing OCR Service Bus messages."""
    
    def __init__(self):
        self.engine = OCREngine()
    
    def start_listening(self):
        """Start listening for OCR messages from Service Bus."""
        from azure.servicebus import ServiceBusClient
        
        try:
            with ServiceBusClient.from_connection_string(settings.service_bus_connection_string) as client:
                with client.get_queue_receiver(queue_name="ocr-processing-queue") as receiver:
                    logger.info("OCR worker started, listening for messages...")
                    
                    for message in receiver:
                        try:
                            # Parse message body
                            message_body = json.loads(str(message))
                            logger.info(f"Received OCR message: {message_body.get('processing_id')}")
                            
                            # Process the message
                            success = self.engine.process_ocr_message(message_body)
                            
                            if success:
                                receiver.complete_message(message)
                                logger.info("OCR message processed successfully")
                            else:
                                receiver.abandon_message(message)
                                logger.error("OCR message processing failed, message abandoned")
                                
                        except Exception as e:
                            logger.error(f"Error processing OCR Service Bus message: {str(e)}")
                            receiver.dead_letter_message(message)
                            
        except Exception as e:
            logger.error(f"Error in OCR worker: {str(e)}")
            raise


def start_ocr_worker():
    """Start the OCR worker."""
    worker = OCRWorker()
    worker.start_listening()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the worker
    start_ocr_worker()
