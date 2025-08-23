"""
Shared Utilities for Insurance AI Agent System
==============================================
Author: Shrvan Hatte

This module provides common utility functions used throughout the Insurance AI Agent system.
It includes functions for Azure Blob Storage operations, unique ID generation, file handling,
and Service Bus messaging operations.

Key Utilities:
- Unique ID generation for processing records
- Azure Blob Storage file upload/download operations
- Service Bus message sending and receiving
- File validation and type checking
- Error handling and logging helpers
- Date/time formatting utilities

Azure Integration:
- Blob Storage client management with authentication
- SAS token generation for secure file access
- Container management and file organization
- Automatic retry logic for cloud operations

Author: Insurance AI Agent Team
Version: 1.0
Dependencies: azure-storage-blob, azure-identity, azure-servicebus, uuid, logging
"""

# Standard library imports
import uuid                # UUID generation for unique identifiers
import logging            # Application logging functionality
import os                 # Operating system interface
from datetime import datetime     # Date and time operations
from typing import Optional      # Type hints for optional parameters

# Azure SDK imports for cloud services
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential  # Azure authentication

# Local configuration import
from .config import settings  # Application configuration

# Configure logging for this module
logging.basicConfig(level=getattr(logging, settings.log_level.upper() if hasattr(settings, 'log_level') else 'INFO'))
logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """
    Generate a unique processing ID for tracking operations.
    
    Creates a unique identifier combining timestamp and UUID for tracking
    processing records throughout the system. Format: PROC_YYYYMMDD_HHMMSS_UUID8
    
    Returns:
        str: Unique processing ID in format "PROC_20241223_143052_a1b2c3d4"
        
    Example:
        >>> processing_id = generate_unique_id()
        >>> print(processing_id)
        "PROC_20241223_143052_a1b2c3d4"
    """
    # Generate timestamp component for chronological ordering
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Generate unique component using UUID
    unique_id = str(uuid.uuid4())[:8]
    return f"PROC_{timestamp}_{unique_id}"


def get_blob_service_client() -> BlobServiceClient:
    """
    Get authenticated Azure Blob Storage service client.
    
    Creates and returns a BlobServiceClient instance configured with the
    application's Azure Storage credentials from settings.
    
    Returns:
        BlobServiceClient: Authenticated client for Azure Blob Storage operations
        
    Raises:
        Exception: If Azure Storage credentials are invalid or missing
    """
    return BlobServiceClient(
        account_url=f"https://{settings.azure_storage_account_name}.blob.core.windows.net",
        credential=settings.azure_storage_account_key
    )


def upload_file_to_blob(file_path: str, blob_name: str, container_name: Optional[str] = None) -> str:
    """
    Upload a file to Azure Blob Storage and return the blob URI.
    
    Uploads a local file to Azure Blob Storage with proper error handling
    and logging. Supports custom container names and generates accessible URIs.
    
    Args:
        file_path (str): Local filesystem path to the file to upload
        blob_name (str): Desired name for the blob in Azure Storage
        container_name (Optional[str]): Target container name (uses default if None)
    
    Returns:
        str: Complete URI of the uploaded blob for external access
        
    Raises:
        FileNotFoundError: If the specified local file doesn't exist
        Exception: If Azure Storage upload fails
        
    Example:
        >>> uri = upload_file_to_blob("/tmp/document.pdf", "docs/doc1.pdf")
        >>> print(uri)
        "https://storage.blob.core.windows.net/container/docs/doc1.pdf"
    """
    # Use default container if none specified
    if container_name is None:
        container_name = settings.azure_blob_container_name
    
    try:
        # Get authenticated blob service client
        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_name
        )
        
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        blob_uri = f"https://{settings.azure_storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        logger.info(f"File uploaded successfully to {blob_uri}")
        return blob_uri
        
    except Exception as e:
        logger.error(f"Error uploading file to blob storage: {str(e)}")
        raise


def generate_private_blob_url(blob_name: str, container_name: Optional[str] = None, expiry_hours: int = 24) -> str:
    """
    Generate a private (SAS) URL for a blob with limited access time.
    
    Args:
        blob_name: Name of the blob
        container_name: Container name (defaults to configured container)
        expiry_hours: Hours until the URL expires
    
    Returns:
        str: Private URL with SAS token
    """
    if container_name is None:
        container_name = settings.azure_blob_container_name
    
    try:
        from datetime import timedelta
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=settings.azure_storage_account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=settings.azure_storage_account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        blob_url_with_sas = f"https://{settings.azure_storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        return blob_url_with_sas
        
    except Exception as e:
        logger.error(f"Error generating private blob URL: {str(e)}")
        raise


def extract_file_metadata(file_path: str) -> dict:
    """
    Extract metadata from a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        dict: File metadata including size, type, etc.
    """
    try:
        stat_info = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Determine MIME type based on extension
        mime_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        
        return {
            'filename': filename,
            'size': stat_info.st_size,
            'mime_type': mime_type_map.get(file_extension, 'application/octet-stream'),
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime),
            'extension': file_extension
        }
        
    except Exception as e:
        logger.error(f"Error extracting file metadata: {str(e)}")
        raise


def send_to_service_bus(message: dict, queue_name: Optional[str] = None):
    """
    Send a message to Azure Service Bus queue.
    
    Args:
        message: Message dictionary to send
        queue_name: Queue name (defaults to configured queue)
    """
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
    import json
    
    if queue_name is None:
        queue_name = settings.service_bus_queue_name
    
    try:
        with ServiceBusClient.from_connection_string(settings.service_bus_connection_string) as client:
            with client.get_queue_sender(queue_name=queue_name) as sender:
                message_body = json.dumps(message)
                service_bus_message = ServiceBusMessage(message_body)
                sender.send_messages(service_bus_message)
                logger.info(f"Message sent to Service Bus queue: {queue_name}")
                
    except Exception as e:
        logger.error(f"Error sending message to Service Bus: {str(e)}")
        raise


def auto_detect_email_provider(email_address: str) -> dict:
    """
    Auto-detect email provider settings based on email address.
    
    Args:
        email_address: The user's email address
    
    Returns:
        dict: Email provider configuration with host, port, and provider name
    """
    domain = email_address.split('@')[1].lower()
    
    # Common email provider configurations
    provider_configs = {
        'gmail.com': {
            'provider': 'Gmail',
            'host': 'imap.gmail.com',
            'port': 993
        },
        'outlook.com': {
            'provider': 'Outlook',
            'host': 'outlook.office365.com',
            'port': 993
        },
        'hotmail.com': {
            'provider': 'Outlook',
            'host': 'outlook.office365.com',
            'port': 993
        },
        'live.com': {
            'provider': 'Outlook',
            'host': 'outlook.office365.com',
            'port': 993
        },
        'yahoo.com': {
            'provider': 'Yahoo',
            'host': 'imap.mail.yahoo.com',
            'port': 993
        },
        'aol.com': {
            'provider': 'AOL',
            'host': 'imap.aol.com',
            'port': 993
        }
    }
    
    # Check if domain matches a known provider
    if domain in provider_configs:
        return provider_configs[domain]
    
    # Default to generic IMAP settings for unknown providers
    return {
        'provider': 'Generic IMAP',
        'host': f'imap.{domain}',
        'port': 993
    }
