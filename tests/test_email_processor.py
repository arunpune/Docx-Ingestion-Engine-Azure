"""
Unit tests for email processing functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.email_processor.email_handler import EmailProcessor


class TestEmailProcessor:
    """Test cases for EmailProcessor class."""
    
    def test_process_email_file_success(self, temp_file, mock_blob_client, mock_service_bus, test_database):
        """Test successful email file processing."""
        with patch('src.email_processor.email_handler.get_session') as mock_session:
            mock_session.return_value = Mock()
            
            processor = EmailProcessor()
            
            # Mock email parsing
            with patch('email.message_from_bytes') as mock_email:
                mock_message = Mock()
                mock_message.get.side_effect = lambda key, default="": {
                    "From": "test@example.com",
                    "To": "recipient@example.com",
                    "Subject": "Test Email"
                }.get(key, default)
                mock_message.is_multipart.return_value = False
                mock_message.get_payload.return_value = "Test email body"
                mock_email.return_value = mock_message
                
                processing_id = processor.process_email_file(temp_file)
                
                assert processing_id.startswith("PROC_")
                assert len(processing_id) > 10
    
    def test_extract_email_metadata(self, mock_email_message):
        """Test email metadata extraction."""
        processor = EmailProcessor()
        metadata = processor._extract_email_metadata(mock_email_message)
        
        assert metadata["from"] == "test@example.com"
        assert metadata["to"] == "recipient@example.com"
        assert metadata["subject"] == "Test Email"
    
    def test_extract_attachments_no_attachments(self, mock_email_message):
        """Test attachment extraction when no attachments exist."""
        processor = EmailProcessor()
        mock_email_message.is_multipart.return_value = False
        
        attachments = processor._extract_attachments(mock_email_message, "test_id")
        
        assert len(attachments) == 0
    
    def test_extract_attachments_with_attachments(self):
        """Test attachment extraction with attachments."""
        processor = EmailProcessor()
        
        # Mock email message with attachment
        mock_message = Mock()
        mock_message.is_multipart.return_value = True
        
        # Mock attachment part
        mock_attachment = Mock()
        mock_attachment.get.return_value = "attachment; filename=test.pdf"
        mock_attachment.get_filename.return_value = "test.pdf"
        mock_attachment.get_payload.return_value = b"PDF content"
        mock_attachment.get_content_type.return_value = "application/pdf"
        
        mock_message.walk.return_value = [mock_attachment]
        
        with patch('src.email_processor.email_handler.upload_file_to_blob') as mock_upload:
            mock_upload.return_value = "https://storage.com/test.pdf"
            
            with patch('tempfile.NamedTemporaryFile'):
                attachments = processor._extract_attachments(mock_message, "test_id")
                
                assert len(attachments) == 1
                assert attachments[0]["filename"] == "test.pdf"
                assert attachments[0]["uri"] == "https://storage.com/test.pdf"


@pytest.mark.asyncio
async def test_email_listener_endpoint():
    """Test email listener API endpoint."""
    from src.email_processor.email_listener import app
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test health endpoint
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
