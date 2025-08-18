"""
Shared utilities for the Insurance AI Agent system.
"""
import uuid
import logging
import os
from datetime import datetime
from typing import Optional
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential
from .config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """Generate a unique processing ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"PROC_{timestamp}_{unique_id}"


def get_blob_service_client() -> BlobServiceClient:
    """Get Azure Blob Storage service client."""
    return BlobServiceClient(
        account_url=f"https://{settings.azure_storage_account_name}.blob.core.windows.net",
        credential=settings.azure_storage_account_key
    )


def upload_file_to_blob(file_path: str, blob_name: str, container_name: Optional[str] = None) -> str:
    """
    Upload a file to Azure Blob Storage and return the blob URI.
    
    Args:
        file_path: Local path to the file to upload
        blob_name: Name for the blob in storage
        container_name: Container name (defaults to configured container)
    
    Returns:
        str: URI of the uploaded blob
    """
    if container_name is None:
        container_name = settings.azure_blob_container_name
    
    try:
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
