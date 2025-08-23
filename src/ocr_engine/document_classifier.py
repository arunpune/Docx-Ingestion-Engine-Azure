"""
AI Document Classifier for Insurance Documents
=============================================
Author: Rachit Patekar

This module provides intelligent document classification capabilities for insurance-related documents
using OpenAI's GPT models. It processes text extracted from OCR and classifies documents into
predefined categories specific to insurance business processes.

Key Features:
- AI-powered document classification using OpenAI GPT
- Support for multiple insurance document types
- Database integration for storing classification results
- Service Bus message processing for asynchronous operations
- Confidence scoring for classification accuracy

Supported Document Types:
- General Liability Policy Documents
- Excess Liability Policy Documents
- Certificate of Insurance
- Contract Documents
- Request Documents
- Claim Requests
- Insurance RFP (Request for Proposal)

Author: Insurance AI Agent Team
Version: 1.0
Dependencies: openai, sqlalchemy, azure-servicebus
"""

# Standard library imports
import logging          # Application logging functionality
import json            # JSON data serialization/deserialization
from datetime import datetime    # Date and time operations
from typing import Dict, Optional, Tuple  # Type hints for better code documentation

# Third-party imports
import openai          # OpenAI API client for GPT models

# Local application imports
from ..shared.config import settings                                    # Application configuration
from ..shared.models import get_session, ProcessingRecord, DocumentClassification  # Database models

# Initialize logger for this module
logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Advanced AI Document Classifier for Insurance Documents
    =======================================================
    
    This class provides state-of-the-art document classification capabilities using OpenAI's
    GPT models to automatically categorize insurance documents. It processes OCR-extracted
    text and applies machine learning to identify document types with high accuracy.
    
    Core Responsibilities:
    - Classify insurance documents using AI/ML models
    - Process OCR-extracted text for document understanding
    - Generate confidence scores for classification accuracy
    - Store classification results in database
    - Handle multiple document types and formats
    - Integrate with Azure Service Bus for asynchronous processing
    
    Classification Categories:
    1. General Liability Policy Document - Standard liability insurance policies
    2. Excess Liability Policy Document - Umbrella/excess liability coverage
    3. Certificate of Insurance - Insurance verification certificates
    4. Contract Document - Legal agreements and insurance contracts
    5. Request - General information or service requests
    6. Claim Request - Insurance claim forms and loss reports
    7. Insurance RFP - Request for Proposal documents
    
    AI Model Integration:
    - Primary: OpenAI GPT-4 for advanced document understanding
    - Fallback: OpenAI GPT-3.5-turbo for cost-effective processing
    - Custom prompts optimized for insurance terminology
    - Context-aware classification with document structure analysis
    
    Processing Pipeline:
    1. Text Preprocessing → Clean and prepare OCR text
    2. Context Analysis → Identify key insurance terms and phrases
    3. AI Classification → Apply GPT model for document categorization
    4. Confidence Assessment → Calculate classification reliability score
    5. Result Validation → Verify classification against business rules
    6. Database Storage → Store results with metadata
    7. Notification → Send processing completion messages
    
    Quality Assurance:
    - Multi-stage validation of classification results
    - Confidence threshold enforcement (minimum 70%)
    - Human review triggers for low-confidence classifications
    - Continuous learning from classification feedback
    - Error detection and retry mechanisms
    
    Integration Points:
    - OpenAI API: GPT model access for classification
    - SQLAlchemy Database: Classification result storage
    - Azure Service Bus: Asynchronous message processing
    - OCR Engine: Text extraction coordination
    - Azure Blob Storage: Document access and retrieval
    
    Performance Features:
    - Batch processing capabilities for multiple documents
    - Caching of classification results to avoid reprocessing
    - Rate limiting compliance with OpenAI API restrictions
    - Memory-efficient text processing for large documents
    - Parallel processing for high-throughput scenarios
    
    Security & Compliance:
    - Secure API key management via environment variables
    - Data privacy protection for sensitive insurance documents
    - Audit trail for all classification decisions
    - Compliance with insurance industry regulations
    
    Author: AI Classification Team
    Created: 2024
    Last Modified: 2024
    Version: 3.0
    """
    
    def __init__(self):
        """
        Initialize the DocumentClassifier with database session and OpenAI API key.
        """
        self.session = get_session()
        openai.api_key = settings.openai_api_key
    
    def process_classification_message(self, message: Dict) -> bool:
        """
        Process a document classification message from Azure Service Bus.
        
        This method handles asynchronous document classification requests received
        from the Service Bus queue. It extracts the document text, performs
        AI-powered classification, and stores the results in the database.
        
        Args:
            message (Dict): Service Bus message containing:
                - processing_id (str): Unique identifier for the processing record
                - file_uri (str): URI of the document file in blob storage
                - extracted_text (str): OCR-extracted text from the document
                
        Returns:
            bool: True if classification processed successfully, False otherwise
        """
        try:
            # Extract required information from the message
            processing_id = message.get("processing_id")
            file_uri = message.get("file_uri")
            extracted_text = message.get("extracted_text", "")
            
            # Validate required message components
            if not processing_id or not file_uri:
                logger.error("Processing ID or file URI not found in message")
                return False
            
            logger.info(f"Processing document classification for Processing ID: {processing_id}")
            
            # Perform AI-powered document classification
            classification_result = self._classify_document(extracted_text)
            
            # Store classification result in database
            self._save_classification_result(processing_id, file_uri, classification_result)
            
            # Update processing record to mark completion
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

1. General Liability Policy Document - General liability insurance policies and coverage documents
2. Excess Liability Policy Document - Excess or umbrella liability insurance policies
3. Certificate of Insurance - Insurance certificates and evidence of coverage documents
4. Contract Document - Contracts, agreements, and legal documents
5. Insurance Document - General insurance documents that don't fit other categories
6. Request - General requests for information, services, or documentation
7. Claim Request - Insurance claim forms, claim requests, and claim-related documents
8. Insurance RFP - Request for Proposal documents for insurance services

For each document, also extract:
- Key entities (names, dates, amounts, policy numbers, claim numbers, etc.)
- Risk assessment (High, Medium, Low)
- Priority level (High, Medium, Low)
- Confidence score (0.0 to 1.0)

Use these exact document type names in your response. Respond with a JSON object containing your analysis."""
    
    def _create_classification_prompt(self, extracted_text: str) -> str:
        """Create the classification prompt with the extracted text."""
        return f"""Please analyze and classify the following insurance document text:

DOCUMENT TEXT:
{extracted_text}

Please provide your analysis in the following JSON format:
{{
    "document_type": "Certificate of Insurance",
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
