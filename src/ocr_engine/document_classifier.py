"""
AI Document Classifier - Classifies documents using OpenAI GPT for insurance document types.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import openai
from ..shared.config import settings
from ..shared.models import get_session, ProcessingRecord, DocumentClassification

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Handles AI-powered document classification for insurance documents."""
    
    def __init__(self):
        self.session = get_session()
        openai.api_key = settings.openai_api_key
    
    def process_classification_message(self, message: Dict) -> bool:
        """
        Process a document classification message from Service Bus.
        
        Args:
            message: Message dictionary containing extracted text
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            processing_id = message.get("processing_id")
            file_uri = message.get("file_uri")
            extracted_text = message.get("extracted_text", "")
            
            if not processing_id or not file_uri:
                logger.error("Processing ID or file URI not found in message")
                return False
            
            logger.info(f"Processing document classification for Processing ID: {processing_id}")
            
            # Classify the document
            classification_result = self._classify_document(extracted_text)
            
            # Save classification result to database
            self._save_classification_result(processing_id, file_uri, classification_result)
            
            # Update processing record status
            self._update_processing_status(processing_id, "completed")
            
            logger.info(f"Document classification completed for Processing ID: {processing_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error processing classification message: {str(e)}")
            return False
        finally:
            if self.session:
                self.session.close()
    
    def _classify_document(self, extracted_text: str) -> Dict:
        """
        Classify document using OpenAI GPT.
        
        Args:
            extracted_text: Extracted text from OCR
            
        Returns:
            Dict: Classification results
        """
        try:
            # Truncate text if too long (GPT has token limits)
            max_text_length = 8000  # Approximately 2000 tokens
            if len(extracted_text) > max_text_length:
                extracted_text = extracted_text[:max_text_length] + "..."
            
            # Create classification prompt
            prompt = self._create_classification_prompt(extracted_text)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1,  # Low temperature for more consistent results
                response_format={"type": "json_object"}
            )
            
            # Parse response
            classification_text = response.choices[0].message.content
            classification_result = json.loads(classification_text)
            
            logger.info(f"Document classified as: {classification_result.get('document_type', 'Unknown')}")
            return classification_result
            
        except Exception as e:
            logger.error(f"Error in document classification: {str(e)}")
            return {
                "document_type": "Unknown",
                "confidence": 0.0,
                "entities": [],
                "risk_assessment": "Unknown",
                "priority": "Low",
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for document classification."""
        return """You are an expert insurance document classifier. Analyze the provided document text and classify it into one of the following insurance document types:

1. CLAIM_FORM - Insurance claim forms and applications
2. POLICY_DOCUMENT - Insurance policy documents and contracts
3. MEDICAL_REPORT - Medical reports, doctor's notes, hospital records
4. ACCIDENT_REPORT - Accident reports, police reports, incident documentation
5. INVOICE_RECEIPT - Bills, invoices, receipts for services or repairs
6. CORRESPONDENCE - Letters, emails, or other correspondence
7. LEGAL_DOCUMENT - Legal documents, court papers, legal notices
8. FINANCIAL_STATEMENT - Financial statements, bank statements, financial records
9. IDENTIFICATION - ID documents, driver's licenses, passports
10. PHOTO_EVIDENCE - Photos of damages, accidents, or evidence
11. OTHER - Any other type of document

For each document, also extract:
- Key entities (names, dates, amounts, policy numbers, etc.)
- Risk assessment (High, Medium, Low)
- Priority level (High, Medium, Low)
- Confidence score (0.0 to 1.0)

Respond with a JSON object containing your analysis."""
    
    def _create_classification_prompt(self, extracted_text: str) -> str:
        """Create the classification prompt with the extracted text."""
        return f"""Please analyze and classify the following insurance document text:

DOCUMENT TEXT:
{extracted_text}

Please provide your analysis in the following JSON format:
{{
    "document_type": "DOCUMENT_TYPE_FROM_LIST",
    "confidence": 0.95,
    "entities": [
        {{"type": "policy_number", "value": "POL123456", "confidence": 0.9}},
        {{"type": "claim_amount", "value": "$5000", "confidence": 0.85}},
        {{"type": "date", "value": "2024-01-15", "confidence": 0.9}},
        {{"type": "name", "value": "John Doe", "confidence": 0.95}}
    ],
    "risk_assessment": "Medium",
    "priority": "High",
    "summary": "Brief summary of the document content",
    "key_findings": ["List of key findings or concerns"]
}}"""
    
    def _save_classification_result(self, processing_id: str, file_uri: str, classification_result: Dict):
        """Save classification result to database."""
        try:
            # Get processing record ID
            processing_record = self.session.query(ProcessingRecord).filter_by(
                unique_processing_id=processing_id
            ).first()
            
            if not processing_record:
                logger.error(f"Processing record not found for ID: {processing_id}")
                return
            
            # Create classification record
            classification = DocumentClassification(
                processing_record_id=processing_record.id,
                file_uri=file_uri,
                document_type=classification_result.get("document_type", "Unknown"),
                classification_confidence=str(classification_result.get("confidence", 0.0)),
                extracted_entities=json.dumps(classification_result.get("entities", [])),
                risk_assessment=classification_result.get("risk_assessment", "Unknown"),
                priority_level=classification_result.get("priority", "Low")
            )
            
            self.session.add(classification)
            self.session.commit()
            
            logger.info(f"Classification result saved for processing ID: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error saving classification result: {str(e)}")
            if self.session:
                self.session.rollback()
    
    def _update_processing_status(self, processing_id: str, status: str):
        """Update the processing record status."""
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


class ClassificationWorker:
    """Worker class for processing document classification Service Bus messages."""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
    
    def start_listening(self):
        """Start listening for classification messages from Service Bus."""
        from azure.servicebus import ServiceBusClient
        
        try:
            with ServiceBusClient.from_connection_string(settings.service_bus_connection_string) as client:
                with client.get_queue_receiver(queue_name="document-classification-queue") as receiver:
                    logger.info("Document classification worker started, listening for messages...")
                    
                    for message in receiver:
                        try:
                            # Parse message body
                            message_body = json.loads(str(message))
                            logger.info(f"Received classification message: {message_body.get('processing_id')}")
                            
                            # Process the message
                            success = self.classifier.process_classification_message(message_body)
                            
                            if success:
                                receiver.complete_message(message)
                                logger.info("Classification message processed successfully")
                            else:
                                receiver.abandon_message(message)
                                logger.error("Classification message processing failed, message abandoned")
                                
                        except Exception as e:
                            logger.error(f"Error processing classification Service Bus message: {str(e)}")
                            receiver.dead_letter_message(message)
                            
        except Exception as e:
            logger.error(f"Error in classification worker: {str(e)}")
            raise


def start_classification_worker():
    """Start the document classification worker."""
    worker = ClassificationWorker()
    worker.start_listening()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the worker
    start_classification_worker()
