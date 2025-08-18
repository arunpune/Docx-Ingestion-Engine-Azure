"""
Shared configuration module for the Insurance AI Agent system.
"""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Azure Storage Configuration
        self.azure_storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
        self.azure_storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
        self.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        self.azure_blob_container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME", "insurance-documents")
        
        # Databricks Configuration
        self.databricks_server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
        self.databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        self.databricks_access_token = os.getenv("DATABRICKS_ACCESS_TOKEN", "")
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///insurance_ai.db")
        
        # OCR Configuration
        self.azure_form_recognizer_endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
        self.azure_form_recognizer_key = os.getenv("AZURE_FORM_RECOGNIZER_KEY", "")
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Email Configuration
        self.email_host = os.getenv("EMAIL_HOST", "")
        self.email_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        
        # Service Bus Configuration
        self.service_bus_connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING", "")
        self.service_bus_queue_name = os.getenv("SERVICE_BUS_QUEUE_NAME", "ingestion-queue")
        
        # Redis Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Application Settings
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
# Global settings instance
settings = Settings()
