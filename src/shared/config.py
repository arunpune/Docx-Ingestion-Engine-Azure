"""
Configuration Management for Insurance AI Agent System
======================================================
Author: Rachit Patekar

This module provides centralized configuration management for the Insurance AI Agent system.
It loads and validates environment variables for all system components including Azure services,
database connections, OCR engines, AI models, and communication services.

Configuration Categories:
- Azure Storage: Blob storage for documents and files
- Database: SQLAlchemy database connections
- OCR Services: Azure Form Recognizer and local OCR engines
- AI Models: OpenAI GPT and Google Gemini configurations
- Email Services: IMAP email processing configuration
- Service Bus: Azure Service Bus for asynchronous messaging
- Caching: Redis configuration for performance optimization

Environment Variables:
All configuration is loaded from environment variables, typically defined in a .env file.
This approach ensures security and flexibility across different deployment environments.

Author: Insurance AI Agent Team
Version: 1.0
Dependencies: python-dotenv, os
"""

# Standard library imports
import os                    # Operating system interface for environment variables
from typing import Optional  # Type hints for optional configuration values


class Settings:
    """
    Application settings manager that loads configuration from environment variables.
    
    This class centralizes all configuration management for the Insurance AI Agent system.
    It loads settings from environment variables and provides sensible defaults where
    appropriate. All sensitive information (API keys, connection strings) should be
    stored in environment variables rather than hardcoded.
    
    Usage:
        settings = Settings()
        storage_account = settings.azure_storage_account_name
        
    Configuration Categories:
        - Azure cloud services (Storage, Form Recognizer, Service Bus)
        - Database connectivity (SQLAlchemy URLs)
        - AI/ML services (OpenAI, Google Gemini)
        - Email processing (IMAP settings)
        - Caching and performance (Redis)
    """
    
    def __init__(self):
        """
        Initialize settings by loading all environment variables.
        
        Loads configuration from environment variables using python-dotenv.
        If a .env file exists, it will be loaded automatically.
        """
        # Load environment variables from .env file if present
        from dotenv import load_dotenv
        load_dotenv()
        
        # ========== AZURE STORAGE CONFIGURATION ==========
        # Azure Blob Storage settings for document and file management
        self.azure_storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
        self.azure_storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
        self.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        self.azure_blob_container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME", "insurance-documents")
        
        # ========== DATABRICKS CONFIGURATION ==========
        # Databricks settings for big data processing and analytics
        self.databricks_server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
        self.databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        self.databricks_access_token = os.getenv("DATABRICKS_ACCESS_TOKEN", "")
        
        # ========== DATABASE CONFIGURATION ==========
        # Database connection settings (supports SQLite, PostgreSQL, SQL Server)
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///insurance_ai.db")
        
        # ========== OCR SERVICES CONFIGURATION ==========
        # Azure Form Recognizer for intelligent document processing
        self.azure_form_recognizer_endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
        self.azure_form_recognizer_key = os.getenv("AZURE_FORM_RECOGNIZER_KEY", "")
        
        # ========== AI/ML SERVICES CONFIGURATION ==========
        # OpenAI GPT configuration for document classification
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Google Gemini configuration for enhanced document classification
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")
        
        # ========== EMAIL PROCESSING CONFIGURATION ==========
        # IMAP email server settings for email monitoring
        self.email_host = os.getenv("EMAIL_HOST", "")
        self.email_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        
        # ========== AZURE SERVICE BUS CONFIGURATION ==========
        # Service Bus settings for asynchronous message processing
        self.service_bus_connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING", "")
        self.service_bus_queue_name = os.getenv("SERVICE_BUS_QUEUE_NAME", "ingestion-queue")
        
        # ========== CACHING CONFIGURATION ==========
        # Redis configuration for performance optimization and caching
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Application Settings
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
# Global settings instance
settings = Settings()
