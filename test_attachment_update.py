#!/usr/bin/env python3
"""
Test script to verify attachment number updates work correctly.
"""
import json
import uuid
from datetime import datetime
from src.ingestion_engine.ingestion_processor import IngestionEngine

def test_attachment_processing():
    """Test attachment processing and updates."""
    print("🧪 Testing attachment processing...")
    
    try:
        # Initialize ingestion engine
        engine = IngestionEngine()
        print("✅ Ingestion engine initialized")
        
        # Create test email with multiple attachments
        processing_id = str(uuid.uuid4())
        email_id = "test-email-123"
        
        test_message = {
            "processing_id": processing_id,
            "source_type": "email",
            "email": {
                "id": email_id,
                "from": "test@example.com",
                "to": ["recipient@example.com"],
                "cc": [],
                "subject": "Test Email with Attachments",
                "body": "This is a test email with multiple attachments.",
                "date": "2025-08-19",
                "time": "14:30:00",
                "email_uri": "https://test.blob.core.windows.net/test/email.eml"
            },
            "attachments": [
                {
                    "uri": "https://test.blob.core.windows.net/test/doc1.pdf",
                    "filename": "document1.pdf"
                },
                {
                    "uri": "https://test.blob.core.windows.net/test/doc2.pdf", 
                    "filename": "document2.pdf"
                },
                {
                    "uri": "https://test.blob.core.windows.net/test/doc3.pdf",
                    "filename": "document3.pdf"
                }
            ]
        }
        
        # Process the message
        print(f"📧 Processing test email with {len(test_message['attachments'])} attachments...")
        success = engine.process_ingestion_message(test_message)
        
        if success:
            print("✅ Email processed successfully")
            
            # Check attachments in database
            print("🔍 Checking attachments in database...")
            attachments = engine.db.list_attachments(email_id)
            
            print(f"📎 Found {len(attachments)} attachments:")
            for att in attachments:
                print(f"  - ID: {att['id']}")
                print(f"    Number: {att['attachmentNumber']}")
                print(f"    Filename: {att['fileName']}")
                print(f"    Status: {att.get('status', 'unknown')}")
                print(f"    Created: {att.get('createdAt', 'unknown')}")
                print()
            
            # Test updating attachment status
            print("🔄 Testing attachment status updates...")
            for i, att in enumerate(attachments):
                test_ocr_text = f"This is extracted text from {att['fileName']}"
                
                engine.db.update_attachment_status(
                    attachment_id=att['id'],
                    email_id=email_id,
                    status="completed",
                    ocr_text=test_ocr_text
                )
                print(f"✅ Updated attachment {att['id']} to completed status")
            
            # Verify updates
            print("🔍 Verifying updates...")
            updated_attachments = engine.db.list_attachments(email_id)
            
            for att in updated_attachments:
                print(f"  - {att['fileName']}: {att.get('status')} - OCR text length: {att.get('ocrTextLength', 0)}")
            
            print("✅ All tests completed successfully!")
            
        else:
            print("❌ Failed to process email")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_attachment_processing()
