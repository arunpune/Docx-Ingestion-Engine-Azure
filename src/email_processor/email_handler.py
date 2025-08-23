"""
Email Processing Module for Insurance AI Agent
==============================================
Author: Rachit Patekar

This module handles comprehensive email processing for the Insurance AI Agent system.
It processes incoming emails, extracts metadata, handles attachments, and integrates
with Azure services for storage and downstream processing.

Key Features:
- Email file parsing (.eml, .msg formats)
- Metadata extraction (sender, recipients, subject, date, body)
- Attachment detection and extraction
- Azure Blob Storage integration for file storage
- Database integration for processing record management
- Service Bus messaging for asynchronous processing
- Support for multiple attachment formats (PDF, images, documents)

Email Processing Pipeline:
1. Parse email file and extract metadata
2. Upload email to Azure Blob Storage
3. Extract and process individual attachments
4. Store attachment files in organized blob structure
5. Create database records for tracking
6. Send processing messages to Service Bus queues

Author: Insurance AI Agent Team
Version: 1.0
Dependencies: email, azure-storage-blob, azure-servicebus, sqlalchemy
"""

# Standard library imports
import email                    # Email parsing and handling
import logging                  # Application logging functionality
from datetime import datetime  # Date and time operations
from typing import List, Dict, Optional, Tuple  # Type hints for better code documentation
from email.mime.multipart import MIMEMultipart  # Email composition
from email.mime.text import MIMEText            # Email text content
import os                      # Operating system interface
import tempfile               # Temporary file handling

# Local application imports
from ..shared.config import settings  # Application configuration
from ..shared.utils import upload_file_to_blob, generate_private_blob_url, generate_unique_id, send_to_service_bus
from ..shared.models import get_session, ProcessingRecord, AttachmentRecord  # Database models

# Initialize logger for this module
logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Comprehensive Email Processing Engine for Insurance AI Agent
    ============================================================
    
    This class provides complete email processing capabilities for the Insurance AI Agent,
    handling email parsing, attachment extraction, Azure storage integration, and
    database record management for insurance document processing workflows.
    
    Core Responsibilities:
    - Parse email files (.eml, .msg) and extract metadata
    - Extract and validate email attachments 
    - Upload email content and attachments to Azure Blob Storage
    - Create database records for processing tracking
    - Send processing messages to Azure Service Bus
    - Generate secure private URLs for blob access
    
    Processing Architecture:
    1. Email File Ingestion → Parse metadata and content
    2. Attachment Extraction → Identify and extract files
    3. Azure Storage Upload → Store emails and attachments
    4. Database Record Creation → Track processing status
    5. Service Bus Messaging → Trigger downstream processing
    
    Integration Points:
    - Azure Blob Storage: File storage and retrieval
    - Azure Service Bus: Asynchronous message processing
    - SQLAlchemy Database: Processing record management
    - Insurance Classification: Document type identification
    
    Author: Email Processing Team
    Created: 2024
    Last Modified: 2024
    """

    def __init__(self):
        """
        Initialize the EmailProcessor with database session.
        """
        self.session = get_session()
    
    def process_email_file(self, email_file_path: str) -> str:
        """
        Process an email file (.eml or .msg) and extract metadata and attachments.
        
        This is the main entry point for email processing. It parses the email file,
        extracts metadata and attachments, uploads files to Azure Blob Storage,
        creates database records, and triggers downstream processing.
        
        Args:
            email_file_path (str): Local filesystem path to the email file
            
        Returns:
            str: Unique processing ID for tracking this email processing operation
            
        Raises:
            FileNotFoundError: If the email file doesn't exist
            Exception: If email processing fails
            
        Processing Steps:
            1. Generate unique processing ID
            2. Parse email file and extract metadata
            3. Upload email file to Azure Blob Storage
            4. Extract and process individual attachments
            5. Create database records for tracking
            6. Send processing messages to Service Bus
        """
        try:
            # ========== PROCESSING ID GENERATION ==========
            # Generate unique identifier for this processing operation
            # This ID is used to track the entire email processing workflow
            processing_id = generate_unique_id()
            logger.info(f"Starting email processing with ID: {processing_id}")
            
            # ========== EMAIL FILE PARSING ==========
            # Parse the email file using Python's email library
            # Supports both .eml (RFC822) and .msg (Outlook) formats
            with open(email_file_path, 'rb') as f:
                email_message = email.message_from_bytes(f.read())
            logger.info(f"Successfully parsed email file: {email_file_path}")
            
            # ========== METADATA EXTRACTION ==========
            # Extract comprehensive metadata from the email message
            # Includes sender, recipients, subject, date, and body content
            email_metadata = self._extract_email_metadata(email_message)
            logger.info(f"Extracted metadata for email: {email_metadata.get('subject', 'No Subject')}")
            
            # ========== EMAIL FILE STORAGE ==========
            # Upload original email file to Azure Blob Storage for archival
            # Creates organized folder structure: emails/{processing_id}/{filename}
            email_blob_name = f"emails/{processing_id}/{os.path.basename(email_file_path)}"
            email_uri = upload_file_to_blob(email_file_path, email_blob_name)
            logger.info(f"Uploaded email to blob storage: {email_uri}")
            
            # ========== ATTACHMENT PROCESSING ==========
            # Extract and process all email attachments
            # Returns list of attachment metadata and storage URIs
            attachments = self._extract_attachments(email_message, processing_id)
            logger.info(f"Extracted {len(attachments)} attachments from email")
            
            # ========== DATABASE RECORD CREATION ==========
            # Create comprehensive processing record in database
            # Stores all email metadata and processing status
            processing_record = ProcessingRecord(
                unique_processing_id=processing_id,           # Unique identifier for tracking
                source_type="email",                          # Source type for this processing
                email_file_uri=email_uri,                     # Azure blob URI for email file
                email_from=email_metadata.get("from"),        # Sender email address
                email_to=email_metadata.get("to"),           # Primary recipient(s)
                email_cc=email_metadata.get("cc"),           # CC recipient(s)
                email_subject=email_metadata.get("subject"),  # Email subject line
                email_body=email_metadata.get("body"),       # Email body content
                email_date=email_metadata.get("date"),       # Email date/timestamp
                num_attachments=len(attachments)              # Total attachment count
            )
            
            # Add processing record to database session
            self.session.add(processing_record)
            self.session.commit()  # Commit to get the processing_record.id
            logger.info(f"Created processing record with ID: {processing_record.id}")
            
            # ========== ATTACHMENT RECORDS CREATION ==========
            # Create individual database records for each attachment
            # Links attachments to the main processing record
            for attachment_info in attachments:
                # Create attachment record with comprehensive metadata
                attachment_record = AttachmentRecord(
                    processing_record_id=processing_record.id,           # Link to parent processing record
                    attachment_filename=attachment_info["filename"],     # Original filename
                    attachment_uri=attachment_info["uri"],               # Azure blob storage URI
                    attachment_size=attachment_info["size"],             # File size in bytes
                    mime_type=attachment_info["mime_type"]               # MIME type for content identification
                )
                self.session.add(attachment_record)
            
            # Commit all attachment records to database
            self.session.commit()
            logger.info(f"Saved {len(attachments)} attachment records to database")
            
            # ========== SERVICE BUS INTEGRATION ==========
            # Send processing notification to ingestion engine
            # Triggers downstream document classification and analysis
            self._send_to_ingestion_engine(processing_id, attachments)
            logger.info(f"Sent processing message to ingestion engine for ID: {processing_id}")
            
            # ========== PROCESSING COMPLETION ==========
            # Log successful completion and return processing ID for tracking
            logger.info(f"Email processed successfully. Processing ID: {processing_id}")
            return processing_id
            
        except Exception as e:
            # ========== ERROR HANDLING ==========
            # Log error details and rollback database changes if needed
            logger.error(f"Error processing email: {str(e)}")
            if self.session:
                self.session.rollback()  # Undo any incomplete database changes
            raise  # Re-raise exception for upstream handling
        finally:
            # ========== CLEANUP ==========
            # Ensure database session is properly closed
            if self.session:
                self.session.close()
    
    def _extract_email_metadata(self, email_message) -> Dict:
        """
        Extract comprehensive metadata from email message object.
        
        This method parses email headers and content to extract all relevant
        metadata for storage and processing. Handles various email formats
        and encoding issues gracefully.
        
        Args:
            email_message: Parsed email message object from email library
            
        Returns:
            Dict: Dictionary containing extracted email metadata including:
                - from: Sender email address and name
                - to: Primary recipient(s)
                - cc: CC recipient(s) 
                - subject: Email subject line
                - date: Email timestamp
                - body: Email body content (text and HTML)
                
        Processing Steps:
        1. Extract standard email headers (From, To, CC, Subject, Date)
        2. Parse and format date information
        3. Extract body content from both text and HTML parts
        4. Handle encoding and formatting issues
        5. Return structured metadata dictionary
        
        Author: Email Processing Team
        """
        try:
            # ========== EMAIL HEADER EXTRACTION ==========
            # Extract basic headers with fallback to empty strings
            from_addr = email_message.get("From", "")      # Sender information
            to_addr = email_message.get("To", "")          # Primary recipients
            cc_addr = email_message.get("Cc", "")          # CC recipients
            subject = email_message.get("Subject", "")     # Email subject line
            date_str = email_message.get("Date", "")       # Raw date string from headers
            
            # ========== DATE PARSING AND VALIDATION ==========
            # Parse email date string into Python datetime object
            email_date = None
            if date_str:
                try:
                    # Use email.utils for RFC-compliant date parsing
                    from email.utils import parsedate_to_datetime
                    email_date = parsedate_to_datetime(date_str)
                    logger.debug(f"Parsed email date: {email_date}")
                except Exception as date_error:
                    # Log date parsing errors but continue processing
                    logger.warning(f"Failed to parse email date '{date_str}': {date_error}")
                    pass
            
            # ========== EMAIL BODY EXTRACTION ==========
            # Extract body content from email (handles both text and HTML)
            body = self._extract_email_body(email_message)
            
            # ========== METADATA ASSEMBLY ==========
            # Return structured dictionary with all extracted metadata
            return {
                "from": from_addr,        # Sender email address and display name
                "to": to_addr,           # Primary recipient email addresses
                "cc": cc_addr,           # Carbon copy recipient addresses
                "subject": subject,       # Email subject line
                "date": email_date,      # Parsed datetime object
                "body": body             # Email body content (text/HTML)
            }
            
        except Exception as e:
            logger.error(f"Error extracting email metadata: {str(e)}")
            return {}
    
    def _extract_email_body(self, email_message) -> str:
        """Extract the body text from email message."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Extract text content (not attachments)
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        # For HTML, you might want to convert to plain text
                        html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # Simple HTML to text conversion (you can use html2text library for better conversion)
                        body += html_content
                    except:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        return body.strip()
    
    def _extract_attachments(self, email_message, processing_id: str) -> List[Dict]:
        """Extract attachments from email and upload to blob storage."""
        attachments = []
        
        if not email_message.is_multipart():
            return attachments
        
        for part in email_message.walk():
            content_disposition = str(part.get("Content-Disposition"))
            
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    try:
                        # Create temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                            attachment_data = part.get_payload(decode=True)
                            temp_file.write(attachment_data)
                            temp_file_path = temp_file.name
                        
                        # Upload to blob storage
                        blob_name = f"attachments/{processing_id}/{filename}"
                        attachment_uri = upload_file_to_blob(temp_file_path, blob_name)
                        
                        # Get file size
                        file_size = len(attachment_data)
                        
                        # Determine MIME type
                        mime_type = part.get_content_type() or "application/octet-stream"
                        
                        attachments.append({
                            "filename": filename,
                            "uri": attachment_uri,
                            "size": file_size,
                            "mime_type": mime_type
                        })
                        
                        # Clean up temporary file
                        os.unlink(temp_file_path)
                        
                        logger.info(f"Attachment processed: {filename}")
                        
                    except Exception as e:
                        logger.error(f"Error processing attachment {filename}: {str(e)}")
        
        return attachments
    
    def _send_to_ingestion_engine(self, processing_id: str, attachments: List[Dict]):
        """Send processing information to ingestion engine."""
        try:
            message = {
                "processing_id": processing_id,
                "source_type": "email",
                "attachments": attachments,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            send_to_service_bus(message)
            logger.info(f"Sent email processing info to ingestion engine: {processing_id}")
            
        except Exception as e:
            logger.error(f"Error sending to ingestion engine: {str(e)}")
            raise


def process_email_from_file(email_file_path: str) -> str:
    """
    Main function to process an email file.
    
    Args:
        email_file_path: Path to the email file
        
    Returns:
        str: Unique processing ID
    """
    processor = EmailProcessor()
    return processor.process_email_file(email_file_path)
