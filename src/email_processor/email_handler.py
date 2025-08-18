"""
Email processor module for handling incoming emails and extracting attachments.
"""
import email
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import tempfile
from ..shared.config import settings
from ..shared.utils import upload_file_to_blob, generate_private_blob_url, generate_unique_id, send_to_service_bus
from ..shared.models import get_session, ProcessingRecord, AttachmentRecord

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Handles email processing and attachment extraction."""
    
    def __init__(self):
        self.session = get_session()
    
    def process_email_file(self, email_file_path: str) -> str:
        """
        Process an email file (.eml) and extract metadata and attachments.
        
        Args:
            email_file_path: Path to the email file
            
        Returns:
            str: Unique processing ID
        """
        try:
            # Generate unique processing ID
            processing_id = generate_unique_id()
            
            # Parse email file
            with open(email_file_path, 'rb') as f:
                email_message = email.message_from_bytes(f.read())
            
            # Extract email metadata
            email_metadata = self._extract_email_metadata(email_message)
            
            # Upload email file to blob storage
            email_blob_name = f"emails/{processing_id}/{os.path.basename(email_file_path)}"
            email_uri = upload_file_to_blob(email_file_path, email_blob_name)
            
            # Extract and process attachments
            attachments = self._extract_attachments(email_message, processing_id)
            
            # Create processing record in database
            processing_record = ProcessingRecord(
                unique_processing_id=processing_id,
                source_type="email",
                email_file_uri=email_uri,
                email_from=email_metadata.get("from"),
                email_to=email_metadata.get("to"),
                email_cc=email_metadata.get("cc"),
                email_subject=email_metadata.get("subject"),
                email_body=email_metadata.get("body"),
                email_date=email_metadata.get("date"),
                num_attachments=len(attachments)
            )
            
            self.session.add(processing_record)
            self.session.commit()
            
            # Save attachment records
            for attachment_info in attachments:
                attachment_record = AttachmentRecord(
                    processing_record_id=processing_record.id,
                    attachment_filename=attachment_info["filename"],
                    attachment_uri=attachment_info["uri"],
                    attachment_size=attachment_info["size"],
                    mime_type=attachment_info["mime_type"]
                )
                self.session.add(attachment_record)
            
            self.session.commit()
            
            # Send to ingestion engine
            self._send_to_ingestion_engine(processing_id, attachments)
            
            logger.info(f"Email processed successfully. Processing ID: {processing_id}")
            return processing_id
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            if self.session:
                self.session.rollback()
            raise
        finally:
            if self.session:
                self.session.close()
    
    def _extract_email_metadata(self, email_message) -> Dict:
        """Extract metadata from email message."""
        try:
            # Extract basic headers
            from_addr = email_message.get("From", "")
            to_addr = email_message.get("To", "")
            cc_addr = email_message.get("Cc", "")
            subject = email_message.get("Subject", "")
            date_str = email_message.get("Date", "")
            
            # Parse date
            email_date = None
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    email_date = parsedate_to_datetime(date_str)
                except:
                    pass
            
            # Extract body
            body = self._extract_email_body(email_message)
            
            return {
                "from": from_addr,
                "to": to_addr,
                "cc": cc_addr,
                "subject": subject,
                "date": email_date,
                "body": body
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
