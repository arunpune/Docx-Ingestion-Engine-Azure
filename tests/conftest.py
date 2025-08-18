"""
Test configurations and fixtures for the Insurance AI Agent system.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.shared.models import Base, get_engine
from src.shared.config import settings


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(b"Test file content")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def mock_email_message():
    """Mock email message for testing."""
    mock_msg = Mock()
    mock_msg.get.side_effect = lambda key, default="": {
        "From": "test@example.com",
        "To": "recipient@example.com",
        "Subject": "Test Email",
        "Date": "Mon, 1 Jan 2024 12:00:00 +0000"
    }.get(key, default)
    
    mock_msg.is_multipart.return_value = True
    mock_msg.walk.return_value = []
    
    return mock_msg


@pytest.fixture
def test_database():
    """Create a test database."""
    # Use in-memory SQLite for testing
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_blob_client():
    """Mock Azure Blob Storage client."""
    with patch('src.shared.utils.get_blob_service_client') as mock_client:
        mock_blob_client = Mock()
        mock_blob_client.upload_blob.return_value = None
        mock_client.return_value.get_blob_client.return_value = mock_blob_client
        yield mock_client


@pytest.fixture
def mock_service_bus():
    """Mock Azure Service Bus client."""
    with patch('src.shared.utils.ServiceBusClient') as mock_client:
        yield mock_client


@pytest.fixture
def sample_processing_record():
    """Sample processing record data."""
    return {
        "unique_processing_id": "TEST_20240101_12345678",
        "source_type": "email",
        "email_from": "test@example.com",
        "email_to": "recipient@example.com",
        "email_subject": "Test Email",
        "num_attachments": 1,
        "status": "pending"
    }
