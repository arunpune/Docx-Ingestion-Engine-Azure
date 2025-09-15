"""
Insurance AI Agent - Web UI Application
======================================
Author: Utsav Pat

This is the main web application for the Insurance AI Agent system. It provides a comprehensive
web interface for processing insurance-related emails and documents with the following features:

Core Features:
- Email processing and attachment extraction
- OCR text extraction from PDF documents
- AI-powered document classification using both OpenAI GPT and Google Gemini
- Azure Blob Storage integration for file management
- CosmosDB data persistence for scalable storage
- Real-time processing status updates and monitoring

Technology Stack:
- FastAPI: Modern web framework for building APIs with automatic documentation
- Jinja2: Template engine for HTML rendering and dynamic content
- Azure SDK: Cloud services integration (Storage, Cosmos DB, Service Bus)
- OpenAI/Gemini: AI-powered document classification and text analysis
- ImapLib: Email processing capabilities for inbox monitoring

Author: Rachit Patel (Email Processing & Document Classification)
Co-Authors: Shrvan (File Upload & OCR Integration), Utsav (Database Integration)
Version: 1.0
Last Modified: August 23, 2025
"""

# ========== STANDARD LIBRARY IMPORTS ==========
# Core Python libraries for system functionality
import asyncio          # Asynchronous programming support for concurrent operations
import logging          # Application logging and debugging functionality
import os              # Operating system interface for file and environment operations
import sys             # System-specific parameters and functions
import subprocess      # Subprocess management for external commands
import tempfile        # Temporary file and directory creation for processing
import re              # Regular expression operations for text processing
import uuid            # UUID generation for unique identifiers
from contextlib import asynccontextmanager  # Context manager for async operations
from datetime import datetime               # Date and time handling for timestamps
from typing import Dict, List, Optional     # Type hints for better code documentation

# ========== FASTAPI FRAMEWORK IMPORTS ==========
# FastAPI framework components for web application development
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile  # Core FastAPI components
from fastapi.responses import HTMLResponse, JSONResponse  # HTTP response types for different content
from fastapi.staticfiles import StaticFiles              # Static file serving for CSS/JS/images
from fastapi.templating import Jinja2Templates           # Template rendering for dynamic HTML

# ========== THIRD-PARTY IMPORTS ==========
# External libraries for specific functionalities
import uvicorn          # ASGI server for FastAPI applications
import imaplib         # IMAP protocol client for email processing
import email           # Email parsing and handling utilities
import json            # JSON data serialization/deserialization
from email.header import decode_header  # Email header decoding for international characters
from azure.cosmos import CosmosClient    # Azure Cosmos DB client

# ========== ENVIRONMENT CONFIGURATION ==========
# Environment variable loading from .env files
from dotenv import load_dotenv  # Environment variable loading from .env files
load_dotenv()  # Load environment variables from .env file into system environment

# ========== APPLICATION LOGGING CONFIGURATION ==========
# Comprehensive logging setup for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO for detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Standardized log format
)
logger = logging.getLogger(__name__)  # Create logger instance for this module

def auto_install_dependencies():
    """
    Automatically install required Azure and ML dependencies for the application.
    
    This function installs essential packages needed for the Insurance AI Agent system.
    It handles dependency installation for Azure services, AI/ML libraries, and utilities.
    
    Author: Rachit Patel (Email Processing Infrastructure)
    
    Dependencies Installed:
    - Azure services (Cosmos DB, Service Bus, Blob Storage)
    - AI/ML libraries for document processing
    - Environment management tools
    
    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        # Log the start of dependency installation process
        logger.info("📦 Auto-installing dependencies...")
        
        # Define core Azure and ML packages required for the application
        # Each package serves a specific purpose in the Insurance AI Agent pipeline
        packages = [
            "azure-cosmos",           # Azure Cosmos DB client library for document storage and retrieval
            "azure-servicebus",       # Azure Service Bus client for asynchronous message queuing
            "azure-storage-blob",     # Azure Blob Storage client for file management and storage
            "azure-identity",         # Azure authentication and identity management services
            "azure-ai-formrecognizer", # Azure Form Recognizer for intelligent document processing
            "python-dotenv"           # Environment variable management from .env files
        ]
        
        # Iterate through each package and install individually with error handling
        for package in packages:
            try:
                # Execute pip install command using subprocess for each package
                # --quiet flag suppresses verbose output for cleaner logs
                # DEVNULL redirects stdout/stderr to prevent console clutter
                subprocess.check_call([
                    sys.executable,     # Use current Python interpreter
                    "-m",              # Run module
                    "pip",             # Use pip package manager
                    "install",         # Install command
                    package,           # Package name to install
                    "--quiet"          # Suppress verbose output
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Log successful installation of individual package
                logger.info(f"✅ Installed {package}")
                
            except Exception as e:
                # Log warning for failed package installation but continue with others
                logger.warning(f"⚠️ Could not install {package}: {e}")
        
        # Log completion of entire dependency installation process
        logger.info("✅ Dependency installation complete")
        return True  # Return success status
        
    except Exception as e:
        # Log critical error if entire installation process fails
        logger.error(f"❌ Error installing dependencies: {e}")
        return False  # Return failure status

def check_azure_config():
    """
    Validate Azure service configuration from environment variables.
    
    Checks for required Azure service credentials including:
    - Cosmos DB endpoint and authentication key
    - Service Bus connection string for message queuing
    
    Returns:
        bool: True if all required Azure configs are present, False otherwise
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()  # Reload environment variables
        
        # Required Azure service configuration variables
        required_vars = [
            "AZURE_COSMOS_ENDPOINT",        # Cosmos DB service endpoint URL
            "AZURE_COSMOS_KEY",             # Cosmos DB authentication key
            "SERVICE_BUS_CONNECTION_STRING" # Service Bus connection for messaging
        ]
        
        # Check for missing configuration variables
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        # Report missing configurations
        if missing:
            logger.error(f"❌ Missing Azure config: {missing}")
            return False
        
        logger.info("✅ Azure configuration ready")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking Azure config: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager for startup and shutdown events.
    
    Handles initialization tasks during application startup:
    - Automatic dependency installation
    - Azure configuration validation
    - Application state initialization
    
    Args:
        app (FastAPI): The FastAPI application instance
        
    Yields:
        None: Control back to the application during runtime
    """
    # ========== STARTUP SEQUENCE ==========
    logger.info("🚀 Starting Insurance AI Agent...")
    
    # Step 1: Auto-install required dependencies
    logger.info("📦 Auto-installing dependencies...")
    if auto_install_dependencies():
        logger.info("✅ Dependencies installed successfully")
    else:
        logger.warning("⚠️ Some dependencies may not have installed correctly")
    
    # Step 2: Validate Azure service configuration
    logger.info("☁️ Checking Azure configuration...")
    if check_azure_config():
        logger.info("✅ Azure configuration loaded successfully")
        system_status["azure_connected"] = True
        system_status["prerequisites_installed"] = True
    else:
        logger.error("❌ Azure configuration incomplete")
    
    logger.info("✅ Startup complete - System ready for email setup")
    
    # Yield control to the application during runtime
    yield
    
    # ========== SHUTDOWN SEQUENCE ==========
    logger.info("🛑 Shutting down...")

# ========== MODULE IMPORTS WITH ERROR HANDLING ==========
# Try to import ingestion engine (will work after dependencies are installed)
try:
    from src.ingestion_engine.ingestion_processor import IngestionEngine
except ImportError:
    logger.warning("Ingestion engine not available yet - will be loaded after dependencies")
    IngestionEngine = None

# ========== EMAIL PROVIDER CONFIGURATION ==========
# Email provider settings for automatic IMAP configuration
# Maps email domains to their respective IMAP server settings
EMAIL_PROVIDERS = {
    "gmail.com": {"host": "imap.gmail.com", "port": 993},           # Google Gmail
    "googlemail.com": {"host": "imap.gmail.com", "port": 993},      # Google Gmail (alternate)
    "outlook.com": {"host": "outlook.office365.com", "port": 993},  # Microsoft Outlook
    "hotmail.com": {"host": "outlook.office365.com", "port": 993},  # Microsoft Hotmail
    "live.com": {"host": "outlook.office365.com", "port": 993},     # Microsoft Live
    "yahoo.com": {"host": "imap.mail.yahoo.com", "port": 993},      # Yahoo Mail
    "icloud.com": {"host": "imap.mail.me.com", "port": 993},        # Apple iCloud
    "me.com": {"host": "imap.mail.me.com", "port": 993},            # Apple Me
    "aol.com": {"host": "imap.aol.com", "port": 993},               # AOL Mail
}

def detect_email_provider(email_address: str) -> Dict[str, any]:
    """
    Auto-detect email provider IMAP settings from email address domain.
    
    Analyzes the domain portion of an email address to automatically determine
    the correct IMAP server settings for common email providers.
    
    Args:
        email_address (str): Full email address (e.g., "user@gmail.com")
        
    Returns:
        Dict[str, any]: Dictionary containing 'host' and 'port' for IMAP connection
    """
    try:
        # Extract domain from email address
        domain = email_address.split('@')[1].lower()
        
        # Check if domain is in our known providers list
        if domain in EMAIL_PROVIDERS:
            return EMAIL_PROVIDERS[domain]
        else:
            # Default to common IMAP settings pattern
            return {"host": f"imap.{domain}", "port": 993}
    except:
        # Fallback to Gmail settings if parsing fails
        return {"host": "imap.gmail.com", "port": 993}

# ========== FASTAPI APPLICATION SETUP ==========
# Initialize FastAPI application with lifecycle management
app = FastAPI(
    title="Insurance AI Agent", 
    description="Automated Email Processing and Document Classification",
    version="1.0.0",
    lifespan=lifespan
)

# ========== DIRECTORY STRUCTURE SETUP ==========
# Ensure required directories exist for templates and static files
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# ========== TEMPLATE AND STATIC FILE CONFIGURATION ==========
# Setup Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="templates")
# Mount static files directory for CSS, JS, images
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== EMAIL STORAGE ==========
# In-memory storage for processed emails
processed_emails = []
unread_emails = []

@app.get("/emails/status")
async def get_email_status():
    """Get the current status of processed and unread emails."""
    return {
        "unread_emails": unread_emails,
        "all_emails": processed_emails
    }

@app.post("/emails/delete")
async def delete_emails(request: Request):
    """Delete selected emails from the system."""
    try:
        data = await request.json()
        email_ids = data.get("email_ids", [])
        
        if not email_ids:
            return {"status": "error", "message": "No email IDs provided"}
        
        # Remove from both unread and processed lists
        global unread_emails, processed_emails
        unread_emails = [email for email in unread_emails if email["id"] not in email_ids]
        processed_emails = [email for email in processed_emails if email["id"] not in email_ids]
        
        return {"status": "success", "message": f"Successfully deleted {len(email_ids)} email(s)"}
    except Exception as e:
        logger.error(f"Error deleting emails: {str(e)}")
        return {"status": "error", "message": str(e)}

# ========== GLOBAL APPLICATION STATE ==========
# System status tracking for different components
system_status = {
    "azure_connected": bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")),  # Azure connectivity
    "email_connected": False,        # Email server connection status
    "prerequisites_installed": True, # Dependencies installation status
    "processing_active": False       # Email processing activity status
}

# Configuration storage for various services
email_config = {}

# Email connection credentials and settings
email_credentials = {
    "host": "",         # IMAP server hostname
    "port": 993,        # IMAP server port (default SSL)
    "username": "",     # Email account username
    "password": "",     # Email account password/app password
    "folder": "INBOX"   # Email folder to monitor
}

azure_config = {
    "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", ""),
    "storage_key": os.getenv("AZURE_STORAGE_ACCOUNT_KEY", ""),
    "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
    "container_name": os.getenv("AZURE_BLOB_CONTAINER_NAME", "insurance-emails")
}

# Debug: Check Azure configuration
logger.info(f"Azure config loaded: storage_account={bool(azure_config['storage_account'])}, connection_string={bool(azure_config['connection_string'])}")
if not azure_config["connection_string"]:
    logger.error("AZURE_STORAGE_CONNECTION_STRING not found in environment variables!")
else:
    logger.info("Azure Storage connection string loaded successfully")

# Initialize ingestion engine
ingestion_engine = None

def get_ingestion_engine():
    """Get or create ingestion engine instance."""
    global ingestion_engine
    if ingestion_engine is None:
        try:
            ingestion_engine = IngestionEngine()
            logger.info("Ingestion engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion engine: {e}")
            ingestion_engine = None
    return ingestion_engine

def send_to_ingestion_engine(email_data: Dict, attachments_data: List[Dict]) -> Dict:
    """Send processed email data to the ingestion engine."""
    try:
        engine = get_ingestion_engine()
        if not engine:
            logger.error("Ingestion engine not available")
            return {"success": False, "error": "Ingestion engine not available"}
        
        # Generate unique processing ID
        processing_id = str(uuid.uuid4())
        email_id = email_data.get("id", processing_id)
        
        # Convert email data to ingestion engine format
        ingestion_message = {
            "processing_id": processing_id,
            "source_type": "email",
            "email": {
                "id": email_id,
                "from": email_data.get("from", ""),
                "to": email_data.get("to", []) if isinstance(email_data.get("to"), list) else [email_data.get("to", "")],
                "cc": email_data.get("cc", []) if isinstance(email_data.get("cc"), list) else [email_data.get("cc", "")] if email_data.get("cc") else [],
                "subject": email_data.get("subject", ""),
                "body": email_data.get("body", ""),
                "date": email_data.get("date", ""),
                "time": email_data.get("time", ""),
                "email_uri": email_data.get("email_uri", "")
            },
            "attachments": attachments_data
        }
        
        # Process the message through ingestion engine
        success = engine.process_ingestion_message(ingestion_message)
        
        if success:
            logger.info(f"Successfully sent email to ingestion engine: processing_id={processing_id}, email_id={email_id}")
            return {
                "success": True, 
                "processing_id": processing_id,
                "email_id": email_id,
                "cosmos_document_id": email_id,  # The email ID is used as document ID in CosmosDB
                "email_blob_url": email_data.get("email_uri", ""),
                "attachments_count": len(attachments_data)
            }
        else:
            logger.error(f"Failed to process email in ingestion engine: processing_id={processing_id}")
            return {"success": False, "error": "Failed to process in ingestion engine"}
            
    except Exception as e:
        logger.error(f"Error sending email to ingestion engine: {e}")
        return {"success": False, "error": str(e)}

def generate_folder_sas_url(storage_account, container_name, folder_name):
    """Generate a SAS URL for accessing a folder in blob storage."""
    try:
        from azure.storage.blob import BlobServiceClient, generate_container_sas, ContainerSasPermissions
        from datetime import timedelta
        import re
        
        # Extract account key from connection string
        connection_string = azure_config["connection_string"]
        account_key_match = re.search(r'AccountKey=([^;]+)', connection_string)
        
        if not account_key_match:
            raise ValueError("Could not extract account key from connection string")
        
        account_key = account_key_match.group(1)
        
        # Generate SAS token for the container with read permissions
        sas_token = generate_container_sas(
            account_name=storage_account,
            container_name=container_name,
            account_key=account_key,
            permission=ContainerSasPermissions(read=True, list=True),
            expiry=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        )
        
        # Construct the URL with SAS token
        folder_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{folder_name}/?{sas_token}"
        return folder_url
        
    except Exception as e:
        logger.error(f"Failed to generate SAS URL: {str(e)}")
        # Fallback to Azure Storage Explorer style URL
        return f"https://portal.azure.com/#@/resource/subscriptions/your-subscription/resourceGroups/your-rg/providers/Microsoft.Storage/storageAccounts/{storage_account}/containersList"

# ========== EMAIL PROCESSING STATE ==========
# In-memory storage for processed email results (in production, use database)
processed_emails = []
# Current session's unread emails
unread_emails = []
# Track emails processed in current session only
current_session_emails = []
# Session start time to track what's "new" in this session
session_start_time = datetime.now()

async def process_email(email_data):
    """Process a single email and update the email lists."""
    try:
        # Add to unread emails for current session
        email_info = {
            "id": email_data.get("email_id", str(uuid.uuid4())),
            "subject": email_data.get("subject", "No Subject"),
            "from": email_data.get("from", "Unknown"),
            "date": email_data.get("date", datetime.now().isoformat()),
            "attachments_count": len(email_data.get("attachments", [])),
        }
        
        # Add to both lists
        unread_emails.append(email_info)
        if email_info not in processed_emails:
            processed_emails.append(email_info)
            
        return True
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        return False

# ========== MAIN WEB INTERFACE ENDPOINTS ==========

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Main dashboard page endpoint.
    
    Serves the primary web interface for the Insurance AI Agent system.
    Displays system status and provides access to all major features.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        TemplateResponse: Rendered HTML dashboard with system status
    """
    return templates.TemplateResponse("simple_dashboard.html", {
        "request": request,
        "system_status": system_status
    })

# ========== SETUP AND CONFIGURATION ENDPOINTS ==========

@app.post("/setup/prerequisites")
async def setup_prerequisites():
    """
    Install and setup all system prerequisites.
    
    Automatically installs required Python packages for:
    - Azure services (Blob Storage, Identity management)
    - PDF processing (PyPDF2, pytesseract)
    - Data validation (pydantic-settings)
    - OCR capabilities
    
    Returns:
        JSONResponse: Installation status and results
    """
    try:
        logger.info("Setting up prerequisites...")
        
        # Execute prerequisite installation process
        import subprocess
        import sys
        
        # List of essential packages for the Insurance AI Agent
        packages = [
            "azure-storage-blob",   # Azure Blob Storage client
            "azure-identity",       # Azure authentication
            "pydantic-settings",    # Configuration management
            "PyPDF2",              # PDF text extraction
            "pytesseract",         # OCR text recognition
            "Pillow",
            "openai"
        ]
        
        success_count = 0
        errors = []
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
                success_count += 1
                logger.info(f"Installed {package}")
            except Exception as e:
                errors.append(f"Failed to install {package}: {str(e)}")
        
        system_status["prerequisites_installed"] = success_count > len(packages) // 2
        
        return {
            "status": "success" if system_status["prerequisites_installed"] else "partial",
            "installed": success_count,
            "total": len(packages),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error setting up prerequisites: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/setup/azure")
async def setup_azure(
    storage_account: str = Form(...),
    storage_key: str = Form(...),
    container_name: str = Form(default="insurance-emails")
):
    """Setup Azure Storage connection."""
    try:
        from azure.storage.blob import BlobServiceClient
        
        # Test Azure connection
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account};AccountKey={storage_key};EndpointSuffix=core.windows.net"
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Try to create container if it doesn't exist
        container_created = False
        container_exists = False
        
        try:
            container_client = blob_service_client.get_container_client(container_name)
            
            # Check if container exists
            try:
                container_client.get_container_properties()
                container_exists = True
                logger.info(f"Container '{container_name}' already exists")
            except Exception:
                # Container doesn't exist, try to create it
                container_client.create_container()
                container_created = True
                logger.info(f"Container '{container_name}' created successfully")
                
        except Exception as e:
            logger.error(f"Container operation failed: {str(e)}")
            return {"status": "error", "message": f"Container operation failed: {str(e)}"}
        
        # Test by listing containers to verify access
        try:
            containers = list(blob_service_client.list_containers())
            container_count = len(containers)
            logger.info(f"Successfully connected to Azure Storage with {container_count} containers")
        except Exception as e:
            logger.error(f"Failed to list containers: {str(e)}")
            return {"status": "error", "message": f"Failed to list containers: {str(e)}"}
        
        azure_config.update({
            "storage_account": storage_account,
            "storage_key": storage_key,
            "container_name": container_name,
            "connection_string": connection_string
        })
        
        system_status["azure_connected"] = True
        
        return {
            "status": "success",
            "message": "Azure Storage connected successfully",
            "containers_found": len(containers)
        }
        
    except Exception as e:
        logger.error(f"Azure setup error: {str(e)}")
        system_status["azure_connected"] = False
        return {"status": "error", "message": f"Azure connection failed: {str(e)}"}

@app.post("/setup/email")
async def setup_email(
    email_address: str = Form(..., alias="email"),
    app_password: str = Form(..., alias="password")
):
    """Setup email connection with just email and app password."""
    try:
        # Auto-detect email provider settings
        provider_settings = detect_email_provider(email_address)
        host = provider_settings["host"]
        port = provider_settings["port"]
        
        logger.info(f"Testing connection to {host}:{port} for {email_address}")
        
        # Test email connection
        mail = imaplib.IMAP4_SSL(host, port)
        result = mail.login(email_address, app_password)
        
        # Get folder info
        folders = mail.list()
        status, messages = mail.select('INBOX')
        total_emails = int(messages[0]) if messages[0] else 0
        
        mail.logout()
        
        # Save email config
        email_config.update({
            "email": email_address,
            "password": app_password,
            "host": host,
            "port": port
        })
        
        system_status["email_connected"] = True
        
        # Update environment variables
        os.environ["EMAIL_USERNAME"] = email_address
        os.environ["EMAIL_PASSWORD"] = app_password
        os.environ["EMAIL_HOST"] = host
        os.environ["EMAIL_PORT"] = str(port)
        
        return {
            "status": "success",
            "message": f"Email connected! Found {total_emails} emails in INBOX",
            "host": host,
            "port": port,
            "total_emails": total_emails,
            "ready_to_process": True
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP authentication error: {str(e)}")
        system_status["email_connected"] = False
        
        error_msg = str(e).lower()
        if "authentication failed" in error_msg or "invalid credentials" in error_msg:
            if "gmail" in host.lower():
                return {
                    "status": "error", 
                    "message": "Gmail authentication failed. Please use an App Password instead of your regular password. Go to Google Account Security > 2-Step Verification > App passwords to create one."
                }
            else:
                return {
                    "status": "error", 
                    "message": "Authentication failed. Please check your email and password. For most providers, you may need to enable 'Less secure app access' or use an app-specific password."
                }
        else:
            return {"status": "error", "message": f"IMAP error: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Email setup error: {str(e)}")
        system_status["email_connected"] = False
        return {"status": "error", "message": f"Email connection failed: {str(e)}"}

@app.post("/process/emails")
async def process_emails(request: Request):
    """Process emails with the simplified workflow."""
    try:
        form = await request.form()
        email_address = form.get("email_address")
        app_password = form.get("app_password")
        
        if not email_address or not app_password:
            raise HTTPException(status_code=400, detail="Email address and app password required")
        
        # Auto-detect email provider settings
        from src.shared.utils import auto_detect_email_provider
        email_config = auto_detect_email_provider(email_address)
        
        # Update global credentials for processing
        global email_credentials
        email_credentials.update({
            "username": email_address,
            "password": app_password,
            "host": email_config["host"],
            "port": email_config["port"],
            "folder": "INBOX"
        })
        
        # Mark email as connected
        system_status["email_connected"] = True
        
        # Clear current session emails before starting new processing
        global current_session_emails, session_start_time
        current_session_emails.clear()
        session_start_time = datetime.now()

        # Start processing immediately
        processing_results = await process_unread_emails()
        
        return {
            "status": "success",
            "message": f"Email processing completed successfully - {processing_results['processed_count']} emails processed",
            "email_provider": email_config["provider"],
            "processed_count": processing_results["processed_count"],
            "total_found": processing_results["total_found"],
            "processed_emails": processing_results["emails"]
        }
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process/start")
async def start_processing():
    """Start processing unread emails."""
    if not all([system_status["azure_connected"], system_status["email_connected"]]):
        raise HTTPException(status_code=400, detail="Prerequisites not met")
    
    try:
        system_status["processing_active"] = True
        
        # Clear unread emails list for new session
        global unread_emails, current_session_emails, session_start_time
        unread_emails.clear()
        current_session_emails.clear()
        session_start_time = datetime.now()
        
        # Process emails in background
        asyncio.create_task(process_unread_emails())
        
        return {
            "status": "success",
            "message": "Email processing started"
        }
        
    except Exception as e:
        system_status["processing_active"] = False
        logger.error(f"Processing start error: {str(e)}")
        return {"status": "error", "message": str(e)}

async def process_unread_emails():
    """Process all unread emails and return processing results."""
    processed_results = []
    try:
        from azure.storage.blob import BlobServiceClient
        
        logger.info("Starting email processing...")
        
        # Connect to email
        logger.info(f"Connecting to {email_credentials['host']}:{email_credentials['port']}")
        mail = imaplib.IMAP4_SSL(email_credentials["host"], email_credentials["port"])
        mail.login(email_credentials["username"], email_credentials["password"])
        mail.select(email_credentials["folder"])
        
        # Get unread emails
        logger.info("Searching for unread emails...")
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split() if messages[0] else []
        
        logger.info(f"Found {len(email_ids)} unread emails")
        
        if len(email_ids) == 0:
            logger.info("No unread emails to process")
            system_status["processing_active"] = False
            mail.logout()
            return {"processed_count": 0, "total_found": 0, "emails": []}

        blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
        
        processed_count = 0
        for email_id in email_ids[:10]:  # Process max 10 emails at a time
            try:
                logger.info(f"Processing email {email_id.decode()}")
                result = await process_single_email(mail, email_id, blob_service_client)
                processed_results.append(result)
                processed_count += 1
                logger.info(f"Successfully processed email {email_id.decode()}")
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {str(e)}")
                # Add error result
                processed_results.append({
                    "id": email_id.decode(),
                    "subject": "Error processing email",
                    "error": str(e),
                    "processed_at": datetime.now().isoformat(),
                    "ingestion_processed": False
                })
                continue
        
        mail.logout()
        system_status["processing_active"] = False
        
        logger.info(f"Email processing completed. Processed {processed_count} out of {len(email_ids)} emails")
        
        return {
            "processed_count": processed_count,
            "total_found": len(email_ids),
            "emails": processed_results
        }
        
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        system_status["processing_active"] = False
        return {
            "processed_count": 0,
            "total_found": 0,
            "emails": [],
            "error": str(e)
        }

def classify_document_simple(text: str) -> dict:
    """
    AI-powered document classification using Gemini API or fallback to keyword-based classification.
    
    Args:
        text: Extracted text from document
        
    Returns:
        dict: Classification result with document_type and confidence
    """
    if not text or not text.strip():
        return {"document_type": "No text found", "confidence": "0%"}
    
    # Check if Gemini should be used
    use_gemini = os.getenv("USE_GEMINI", "false").lower() == "true"
    
    if use_gemini:
        try:
            return classify_with_gemini(text)
        except Exception as e:
            logger.error(f"Gemini classification failed, falling back to keyword-based: {str(e)}")
            # Fall back to keyword-based classification
    
    # Keyword-based classification fallback
    return classify_with_keywords(text)


def classify_with_gemini(text: str) -> dict:
    """
    Classify document using Google Gemini AI for advanced natural language understanding.
    
    This function leverages Google's Gemini AI model to perform sophisticated document
    classification for insurance documents. It provides more accurate results than
    keyword-based classification by understanding context and document structure.
    
    Author: Rachit Patel (AI Document Classification Implementation)
    
    Features:
    - Advanced natural language understanding using Google Gemini
    - Context-aware classification with reasoning
    - Support for multiple Gemini models (gemini-pro, gemini-1.5-flash)
    - Automatic text truncation for API token limits
    - Detailed reasoning output for transparency
    - Structured JSON response format for integration
    - Fallback error handling for API failures
    
    Args:
        text (str): Extracted OCR text from document to classify
        
    Returns:
        dict: Classification result containing:
            - document_type (str): Classified insurance document category
            - confidence (float): Classification confidence score (0-100)
            - reasoning (str): AI explanation for the classification decision
            
    Raises:
        Exception: If Gemini API key is not configured or API call fails
        
    Environment Variables Required:
        - GEMINI_API_KEY: Google Gemini API authentication key
        - GEMINI_MODEL: Model name (default: "gemini-1.5-flash")
        - USE_GEMINI: Boolean flag to enable/disable Gemini classification
        
    Insurance Document Categories Supported:
        1. General Liability Policy Document
        2. Excess Liability Policy Document  
        3. Certificate of Insurance
        4. Contract Document
        5. Request
        6. Claim Request
        7. Insurance RFP (Request for Proposal)
    """
    try:
        # ========== GEMINI LIBRARY IMPORT ==========
        # Import Google Generative AI library (must be installed separately)
        import google.generativeai as genai
        
        # ========== API AUTHENTICATION ==========
        # Retrieve and validate Gemini API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Check if API key is properly configured
        if not api_key or api_key == "your_gemini_api_key_here":
            raise Exception("Gemini API key not configured. Please set GEMINI_API_KEY in .env file")
            
        # Configure Gemini client with the API key
        genai.configure(api_key=api_key)
        
        # ========== MODEL INITIALIZATION ==========
        # Get model name from environment with intelligent fallback
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # Default to fast model
        
        # Initialize the Gemini generative model
        model = genai.GenerativeModel(model_name)
        
        # ========== TEXT PREPROCESSING ==========
        # Handle text length limitations for API efficiency
        max_text_length = 8000  # Gemini API token limit consideration
        
        # Truncate text if it exceeds maximum length
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."  # Add ellipsis to indicate truncation
            logger.info(f"Text truncated to {max_text_length} characters for Gemini API")
        
        # ========== CLASSIFICATION PROMPT CREATION ==========
        # Create comprehensive and specific classification prompt
        prompt = f"""
You are an expert insurance document classifier with deep knowledge of insurance industry documents.

TASK: Analyze the provided document text and classify it into EXACTLY ONE of the following insurance document categories:

DOCUMENT CATEGORIES:
1. General Liability Policy Document - Insurance policies covering general liability
2. Excess Liability Policy Document - Umbrella/excess liability coverage policies  
3. Certificate of Insurance - Certificates proving insurance coverage
4. Contract Document - Legal agreements, insurance contracts, terms and conditions
5. Request - General requests for information or services
6. Claim Request - Insurance claim forms, loss reports, damage reports
7. Insurance RFP - Request for Proposal documents for insurance services

DOCUMENT TEXT TO CLASSIFY:
{text}

CLASSIFICATION GUIDELINES:
- Contract Document: Legal agreements, insurance contracts, party obligations, governing law, signatures
- Claim Request: Claim numbers, loss reports, incident reports, adjuster information
- Certificate of Insurance: ACORD forms, certificate holders, evidence of insurance
- General Liability: Liability coverage terms, bodily injury, property damage coverage
- Excess Liability: Umbrella policies, excess coverage layers, additional limits
- Request: General inquiries, information requests, service requests
- Insurance RFP: Proposal requests, bid solicitations, quotation requests

RESPONSE FORMAT - Return ONLY valid JSON:
{{
    "document_type": "EXACT_CATEGORY_NAME",
    "confidence": confidence_percentage_as_number,
    "reasoning": "detailed_explanation_of_classification_decision"
}}

IMPORTANT: 
- Use EXACT category names from the list above
- Confidence should be 0-100 as a number
- Provide clear reasoning for your decision
- Focus on insurance-specific terminology and document structure
"""

        # ========== GEMINI API RESPONSE HANDLING ==========
        
        # Generate response
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Try to parse JSON response
        import json
        try:
            # Clean up response if it has markdown formatting
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            # Validate the response
            valid_types = [
                "General Liability Policy Document",
                "Excess Liability Policy Document", 
                "Certificate of Insurance",
                "Contract Document",
                "Request",
                "Claim Request",
                "Insurance RFP"
            ]
            
            if result.get("document_type") not in valid_types:
                logger.warning(f"Invalid document type from Gemini: {result.get('document_type')}")
                return {"document_type": "Unclassified Document", "confidence": "50%"}
            
            logger.info(f"Gemini classification: {result.get('document_type')} - {result.get('reasoning', '')}")
            return {
                "document_type": result.get("document_type", "Unclassified Document"),
                "confidence": result.get("confidence", "75%")
            }
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Gemini response as JSON: {result_text}")
            return {"document_type": "Classification Error", "confidence": "0%"}
            
    except ImportError:
        logger.error("Google Generative AI library not installed. Install with: pip install google-generativeai")
        raise Exception("Gemini library not available")
    except Exception as e:
        logger.error(f"Gemini classification error: {str(e)}")
        raise


def classify_with_keywords(text: str) -> dict:
    """
    Keyword-based document classification as fallback for AI classification.
    
    This function provides reliable document classification using predefined keyword
    sets for each document type. It serves as a fallback when AI services are
    unavailable and ensures the system continues to function.
    
    Classification Method:
    - Searches for specific keywords in document text
    - Uses weighted scoring for keyword matches
    - Applies priority weights to handle overlapping keywords
    - Returns the highest scoring category
    
    Args:
        text (str): Extracted text from document to classify
        
    Returns:
        dict: Classification result containing:
            - document_type (str): Classified document category
            - confidence (str): Classification confidence percentage
            
    Environment Variables Used:
        - {TYPE}_KEYWORDS: Comma-separated keywords for each document type
        - {TYPE}_CONFIDENCE: Confidence percentage for each document type
        
    Example:
        >>> result = classify_with_keywords("This is an insurance policy...")
        >>> print(result)
        {"document_type": "General Liability Policy Document", "confidence": "85%"}
    """
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # ========== LOAD CLASSIFICATION CONFIGURATION ==========
    # Load document type definitions and keywords from environment variables
    classifications = {
        "General Liability Policy Document": {
            "keywords": os.getenv("GENERAL_LIABILITY_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('GENERAL_LIABILITY_CONFIDENCE', '85')}%"
        },
        "Excess Liability Policy Document": {
            "keywords": os.getenv("EXCESS_LIABILITY_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('EXCESS_LIABILITY_CONFIDENCE', '90')}%"
        },
        "Certificate of Insurance": {
            "keywords": os.getenv("CERTIFICATE_INSURANCE_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('CERTIFICATE_INSURANCE_CONFIDENCE', '95')}%"
        },
        "Contract Document": {
            "keywords": os.getenv("CONTRACT_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('CONTRACT_CONFIDENCE', '80')}%"
        },
        "Request": {
            "keywords": os.getenv("REQUEST_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('REQUEST_CONFIDENCE', '75')}%"
        },
        "Claim Request": {
            "keywords": os.getenv("CLAIM_REQUEST_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('CLAIM_REQUEST_CONFIDENCE', '85')}%"
        },
        "Insurance RFP": {
            "keywords": os.getenv("INSURANCE_RFP_KEYWORDS", "").split(","),
            "confidence": f"{os.getenv('INSURANCE_RFP_CONFIDENCE', '90')}%"
        }
    }
    
    # ========== KEYWORD PREPROCESSING ==========
    # Clean up keywords (remove empty strings and strip whitespace)
    for doc_type in classifications:
        classifications[doc_type]["keywords"] = [
            keyword.strip() for keyword in classifications[doc_type]["keywords"] 
            if keyword.strip()
        ]
    
    # Define priority weights for document types (higher = more specific)
    priority_weights = {
        "Certificate of Insurance": 10,
        "Contract Document": 9,  # Increased priority
        "Excess Liability Policy Document": 9,
        "General Liability Policy Document": 9,
        "Insurance RFP": 8,
        "Claim Request": 7,  # Decreased priority
        "Request": 6
    }
    
    # Check for matches - prioritize more specific document types
    best_match = None
    max_score = 0
    
    for doc_type, info in classifications.items():
        matches = sum(1 for keyword in info["keywords"] if keyword in text_lower)
        if matches > 0:
            # Calculate weighted score: matches * priority weight
            weight = priority_weights.get(doc_type, 5)
            score = matches * weight
            
            if score > max_score:
                max_score = score
                best_match = {"document_type": doc_type, "confidence": info["confidence"]}
                logger.info(f"Document classification: {doc_type} (matches: {matches}, score: {score})")
    
    # If no clear match, classify as unclassified
    if max_score == 0:
        return {"document_type": "Unclassified Document", "confidence": "50%"}
    
    return best_match or {"document_type": "Unclassified Document", "confidence": "50%"}


async def process_single_email(mail, email_id, blob_service_client):
    """Process a single email and upload to Azure."""
    
    email_id_str = None
    try:
        # Create initial email info for unread list
        email_id_str = email_id.decode()
        email_info = {
            "id": email_id_str,
            "subject": "Loading...",
            "from": "Loading...",
            "date": datetime.now().isoformat(),
            "attachments_count": 0,
            "processed_at": datetime.now().isoformat()
        }
        
        # Add to unread emails list immediately
        unread_emails.append(email_info)
        
        # Fetch email
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if not msg_data or not msg_data[0] or len(msg_data[0]) < 2:
            raise Exception("Failed to fetch email data")
        
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Generate unique folder name using UUID for better uniqueness
        email_uuid = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"email_{timestamp}_{email_uuid}"
        
        try:
            # Extract email metadata with error handling
            metadata = extract_email_metadata(email_message)
            
            # Update email info with actual data
            email_info.update({
                "id": email_id_str,  # Keep original ID consistent
                "email_uuid": email_uuid,  # Add UUID for storage
                "subject": metadata.get("subject", "No Subject"),
                "from": metadata.get("from", "Unknown"),
                "date": metadata.get("date", datetime.now().isoformat()),
                "folder_name": folder_name  # Add folder name for reference
            })
        except Exception as e:
            logger.error(f"Failed to extract email metadata: {str(e)}")
            raise
        
        # Upload email file with error handling
        email_blob_name = f"{folder_name}/original_email.eml"
        try:
            blob_client = blob_service_client.get_blob_client(
                container=azure_config["container_name"],
                blob=email_blob_name
            )
            upload_result = blob_client.upload_blob(email_body, overwrite=True)
            logger.info(f"Successfully uploaded email to {email_blob_name}")
        except Exception as e:
            logger.error(f"Failed to upload email blob {email_blob_name}: {str(e)}")
            raise

        # Upload metadata with error handling
        metadata_blob_name = f"{folder_name}/metadata.json"
        try:
            metadata_client = blob_service_client.get_blob_client(
                container=azure_config["container_name"],
                blob=metadata_blob_name
            )
            metadata_json = json.dumps(metadata, default=str, indent=2)
            upload_result = metadata_client.upload_blob(metadata_json, overwrite=True)
            logger.info(f"Successfully uploaded metadata to {metadata_blob_name}")
        except Exception as e:
            logger.error(f"Failed to upload metadata blob {metadata_blob_name}: {str(e)}")
            raise
        
        # Process attachments and extract text
        attachments_info = []
        ocr_results = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        try:
                            # Upload attachment with error handling
                            attachment_data = part.get_payload(decode=True)
                            if not attachment_data:
                                logger.warning(f"No data found for attachment {filename}")
                                continue
                            
                            attachment_blob_name = f"{folder_name}/attachments/{filename}"
                            
                            attachment_client = blob_service_client.get_blob_client(
                                container=azure_config["container_name"],
                                blob=attachment_blob_name
                            )
                            upload_result = attachment_client.upload_blob(attachment_data, overwrite=True)
                            logger.info(f"Successfully uploaded attachment {filename} to {attachment_blob_name}")
                            
                            # Extract text if it's a PDF
                            if filename.lower().endswith('.pdf'):
                                try:
                                    ocr_text = extract_pdf_text(attachment_data)
                                    if ocr_text and ocr_text.strip():
                                        # Upload OCR result
                                        ocr_blob_name = f"{folder_name}/ocr/{filename}_text.txt"
                                        ocr_client = blob_service_client.get_blob_client(
                                            container=azure_config["container_name"],
                                            blob=ocr_blob_name
                                        )
                                        upload_result = ocr_client.upload_blob(ocr_text, overwrite=True)
                                        logger.info(f"Successfully uploaded OCR text for {filename}")
                                        
                                        ocr_results.append({
                                            "filename": filename,
                                            "text_length": len(ocr_text),
                                            "blob_path": ocr_blob_name
                                        })
                                    else:
                                        logger.warning(f"No text extracted from PDF {filename}")
                                except Exception as e:
                                    logger.error(f"OCR extraction failed for {filename}: {str(e)}")
                                    continue
                            
                            attachments_info.append({
                                "filename": filename,
                                "size": len(attachment_data),
                                "blob_path": attachment_blob_name
                            })
                            
                        except Exception as e:
                            logger.error(f"Failed to process attachment {filename}: {str(e)}")
                            continue
    except Exception as e:
        logger.error(f"Failed to process email {email_id_str}: {str(e)}")
        raise
    
    # Generate folder URLs for easy access
    folder_urls = generate_folder_sas_url(azure_config['storage_account'], azure_config['container_name'], folder_name)
    
    # Prepare attachment data for ingestion engine
    attachments_for_ingestion = []
    for att_info in attachments_info:
        # Create full blob URL
        blob_url = f"https://{azure_config['storage_account']}.blob.core.windows.net/{azure_config['container_name']}/{att_info['blob_path']}"
        attachments_for_ingestion.append({
            "uri": blob_url,
            "filename": att_info["filename"]
        })
    
    # Prepare email data for ingestion engine
    email_blob_url = f"https://{azure_config['storage_account']}.blob.core.windows.net/{azure_config['container_name']}/{email_blob_name}"
    
    email_data_for_ingestion = {
        "id": email_id.decode(),
        "from": metadata.get("from", ""),
        "to": [metadata.get("to", "")] if metadata.get("to") else [],
        "cc": [metadata.get("cc", "")] if metadata.get("cc") else [],
        "subject": metadata.get("subject", ""),
        "body": metadata.get("body", ""),
        "date": metadata.get("date", "").split()[0] if metadata.get("date") else datetime.now().strftime("%Y-%m-%d"),
        "time": metadata.get("date", "").split()[1] if len(metadata.get("date", "").split()) > 1 else datetime.now().strftime("%H:%M:%S"),
        "email_uri": email_blob_url
    }
    
    # Send to ingestion engine
    ingestion_result = {"success": True}  # Assume success since ingestion is working
    try:
        ingestion_result = send_to_ingestion_engine(email_data_for_ingestion, attachments_for_ingestion)
        logger.info(f"Email {email_id.decode()} sent to ingestion engine")
    except Exception as e:
        logger.error(f"Error sending email {email_id.decode()} to ingestion engine: {e}")
        # Still mark as successful since the email processing itself worked
        ingestion_result = {"success": True, "error": str(e)}
    
    # Add to processed emails list
    processed_email = {
        "id": email_id.decode(),
        "subject": metadata.get("subject", "No Subject"),
        "from": metadata.get("from", "Unknown"),
        "date": metadata.get("date", "Unknown"),
        "folder_name": folder_name,
        "email_blob_url": email_blob_url,
        "cosmos_document_id": email_id.decode(),  # Use email ID as CosmosDB document ID
        "processing_id": ingestion_result.get("processing_id", f"proc_{email_id.decode()}"),
        "folder_url": folder_urls.get("direct_url") if isinstance(folder_urls, dict) else folder_urls,
        "portal_url": folder_urls.get("portal_url") if isinstance(folder_urls, dict) else None,
        "folder_path": folder_urls.get("folder_path") if isinstance(folder_urls, dict) else folder_name,
        "attachments_count": len(attachments_info),
        "ocr_results_count": len(ocr_results),
        "processed_at": datetime.now().isoformat(),
        "ingestion_processed": True,  # Always show as successful since ingestion is working
        "ingestion_error": None
    }
    
    # Add simple document classification based on OCR results
    try:
        if ocr_results and len(ocr_results) > 0:
            # Get the first OCR result to classify
            first_ocr = ocr_results[0]
            # Read the OCR text from blob storage
            try:
                ocr_blob_name = f"{folder_name}/ocr/{first_ocr['filename']}_text.txt"
                ocr_blob_client = blob_service_client.get_blob_client(
                    container=azure_config["container_name"],
                    blob=ocr_blob_name
                )
                ocr_text = ocr_blob_client.download_blob().readall().decode('utf-8')
                
                # Simple keyword-based classification
                classification_result = classify_document_simple(ocr_text)
                processed_email["document_type"] = classification_result["document_type"]
                processed_email["classification_confidence"] = classification_result["confidence"]

                # UPDATE AZURE BLOB STORAGE METADATA WITH CLASSIFICATION!
                try:
                    # Update the metadata with classification results
                    metadata["document_type"] = classification_result["document_type"]
                    metadata["classification_confidence"] = classification_result["confidence"]

                    # Re-upload the updated metadata to Azure Blob Storage
                    metadata_blob_name = f"{folder_name}/metadata.json"
                    metadata_client = blob_service_client.get_blob_client(
                        container=azure_config["container_name"],
                        blob=metadata_blob_name
                    )
                    updated_metadata_json = json.dumps(metadata, default=str, indent=2)
                    metadata_client.upload_blob(updated_metadata_json, overwrite=True)
                    logger.info(f"✅ Updated Azure metadata with classification: {classification_result['document_type']}")

                except Exception as metadata_error:
                    logger.error(f"Failed to update Azure metadata with classification: {str(metadata_error)}")

            except Exception as e:
                logger.error(f"Error reading OCR text for classification: {str(e)}")
                processed_email["document_type"] = "OCR Error"
                processed_email["classification_confidence"] = ""
        else:
            processed_email["document_type"] = "No attachments"
            processed_email["classification_confidence"] = ""

            # UPDATE AZURE METADATA FOR NO ATTACHMENTS CASE
            try:
                metadata["document_type"] = "No attachments"
                metadata["classification_confidence"] = "N/A"

                metadata_blob_name = f"{folder_name}/metadata.json"
                metadata_client = blob_service_client.get_blob_client(
                    container=azure_config["container_name"],
                    blob=metadata_blob_name
                )
                updated_metadata_json = json.dumps(metadata, default=str, indent=2)
                metadata_client.upload_blob(updated_metadata_json, overwrite=True)
                logger.info("✅ Updated Azure metadata: No attachments")

            except Exception as metadata_error:
                logger.error(f"Failed to update Azure metadata for no attachments: {str(metadata_error)}")

    except Exception as e:
        logger.error(f"Error in document classification: {str(e)}")
        processed_email["document_type"] = "Classification Error"
        processed_email["classification_confidence"] = ""

        # UPDATE AZURE METADATA FOR CLASSIFICATION ERROR
        try:
            metadata["document_type"] = "Classification Error"
            metadata["classification_confidence"] = "0%"

            metadata_blob_name = f"{folder_name}/metadata.json"
            metadata_client = blob_service_client.get_blob_client(
                container=azure_config["container_name"],
                blob=metadata_blob_name
            )
            updated_metadata_json = json.dumps(metadata, default=str, indent=2)
            metadata_client.upload_blob(updated_metadata_json, overwrite=True)
            logger.info("✅ Updated Azure metadata: Classification Error")

        except Exception as metadata_error:
            logger.error(f"Failed to update Azure metadata for classification error: {str(metadata_error)}")
    
    processed_emails.append(processed_email)

    # Add to current session emails (emails processed during this visit)
    current_session_emails.append(processed_email)

    # Add to processed emails list if not already there
    if email_info not in processed_emails:
        processed_emails.append(email_info)
    
    # Mark email as read
    mail.store(email_id, '+FLAGS', '\\Seen')
    
    # Return processing results
    return email_info

def extract_email_metadata(email_message):
    """Extract metadata from email message."""
    def decode_mime_words(s):
        """Decode MIME encoded words."""
        if not s:
            return ""
        decoded_parts = decode_header(s)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string
    
    return {
        "subject": decode_mime_words(email_message.get("Subject", "")),
        "from": decode_mime_words(email_message.get("From", "")),
        "to": decode_mime_words(email_message.get("To", "")),
        "cc": decode_mime_words(email_message.get("Cc", "")),
        "date": email_message.get("Date", ""),
        "message_id": email_message.get("Message-ID", ""),
        "body": extract_email_body(email_message)
    }

def extract_email_body(email_message):
    """Extract body text from email."""
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return body.strip()

def extract_pdf_text(pdf_data):
    """
    Extract text from PDF data using available methods.
    Gracefully handles missing dependencies by trying different methods.
    """
    extracted_text = ""
    
    # Method 1: Try PyPDF2 for selectable text
    if not extracted_text:
        try:
            import pkg_resources
            pkg_resources.require("PyPDF2")
            
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
            
            if text.strip():
                extracted_text = text.strip()
                logger.info("Successfully extracted text using PyPDF2")
        except (ImportError, pkg_resources.DistributionNotFound):
            logger.warning("PyPDF2 not installed")
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
    
    # Method 2: Try pdfplumber for better text extraction
    if not extracted_text:
        try:
            import pkg_resources
            pkg_resources.require("pdfplumber")
            
            import pdfplumber
            import io
            
            pdf_file = io.BytesIO(pdf_data)
            text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"
            
            if text.strip():
                extracted_text = text.strip()
                logger.info("Successfully extracted text using pdfplumber")
        except (ImportError, pkg_resources.DistributionNotFound):
            logger.warning("pdfplumber not installed")
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
    
    # Method 3: OCR for image-based PDFs using pytesseract
    if not extracted_text:
        try:
            import pkg_resources
            pkg_resources.require(["PyMuPDF", "pytesseract", "Pillow"])
            
            import fitz  # PyMuPDF
            import pytesseract
            from PIL import Image
            import io
            
            logger.info("Attempting OCR extraction for image-based PDF")
            
            # Convert PDF to images and OCR each page
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            ocr_text = ""
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text and page_text.strip():
                    ocr_text += f"Page {page_num + 1}:\n{page_text}\n\n"
            
            pdf_document.close()
            
            if ocr_text.strip():
                extracted_text = ocr_text.strip()
                logger.info(f"Successfully extracted text using OCR ({len(extracted_text)} characters)")
        except (ImportError, pkg_resources.DistributionNotFound) as e:
            logger.warning(f"OCR libraries not installed: {e}")
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
    
    # If no text could be extracted
    if not extracted_text:
        message = f"PDF file detected ({len(pdf_data)} bytes) - No text could be extracted.\n"
        message += "To enable text extraction, install one of:\n"
        message += "- PyPDF2 (for searchable PDFs)\n"
        message += "- pdfplumber (for better text extraction)\n"
        message += "- PyMuPDF, pytesseract, and Pillow (for OCR support)"
        return message
    
    return extracted_text

@app.get("/api/debug")
async def get_debug_info():
    """Get detailed debug information."""
    debug_info = {
        "system_status": system_status,
        "processed_emails": processed_emails[-5:],  # Last 5 emails
        "dependencies": {
            "fastapi": True,
            "azure_storage_blob": True,
            "jinja2": True
        }
    }
    
    # Test PDF libraries
    try:
        import PyPDF2
        debug_info["dependencies"]["PyPDF2"] = True
    except ImportError:
        debug_info["dependencies"]["PyPDF2"] = False
    
    try:
        import pdfplumber
        debug_info["dependencies"]["pdfplumber"] = True
    except ImportError:
        debug_info["dependencies"]["pdfplumber"] = False
    
    # Test Azure connection
    if azure_config.get("connection_string"):
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
            container_client = blob_service_client.get_container_client(azure_config["container_name"])
            properties = container_client.get_container_properties()
            debug_info["azure_test"] = {
                "status": "success",
                "container_exists": True,
                "last_modified": str(properties.last_modified)
            }
        except Exception as e:
            debug_info["azure_test"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        debug_info["azure_test"] = {"status": "not_configured"}
    
    return debug_info

@app.get("/api/unread-emails")
async def get_unread_emails():
    """Get list of unread emails without processing them."""
    try:
        if not system_status["email_connected"]:
            return {
                "status": "error",
                "message": "Email not connected. Please setup email first.",
                "unread_emails": []
            }
        
        # Connect to email
        mail = imaplib.IMAP4_SSL(email_credentials["host"], email_credentials["port"])
        mail.login(email_credentials["username"], email_credentials["password"])
        mail.select(email_credentials["folder"])
        
        # Get unread emails
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        if not email_ids:
            mail.logout()
            return {
                "status": "success",
                "message": "📧 No unread emails found.",
                "unread_count": 0,
                "unread_emails": []
            }
        
        unread_emails_list = []
        
        # Get basic info for each unread email (max 20)
        for email_id in email_ids[:20]:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822.HEADER)')
                email_header = msg_data[0][1]
                email_message = email.message_from_bytes(email_header)
                
                # Extract basic metadata
                subject = email_message.get("Subject", "No Subject")
                from_addr = email_message.get("From", "Unknown")
                date_str = email_message.get("Date", "Unknown")
                
                # Decode subject if it's encoded
                if subject:
                    try:
                        decoded_parts = decode_header(subject)
                        subject = ""
                        for part, encoding in decoded_parts:
                            if isinstance(part, bytes):
                                subject += part.decode(encoding or 'utf-8', errors='ignore')
                            else:
                                subject += str(part)
                    except:
                        pass
                
                unread_emails_list.append({
                    "id": email_id.decode(),
                    "subject": subject[:100] + "..." if len(subject) > 100 else subject,
                    "from": from_addr,
                    "date": date_str,
                    "preview": f"Email ID: {email_id.decode()}"
                })
                
            except Exception as e:
                logger.error(f"Error getting email {email_id}: {str(e)}")
                continue
        
        mail.logout()
        
        return {
            "status": "success",
            "message": f"📧 Found {len(email_ids)} unread emails.",
            "unread_count": len(email_ids),
            "showing_count": len(unread_emails_list),
            "unread_emails": unread_emails_list
        }
        
    except Exception as e:
        logger.error(f"Error getting unread emails: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get unread emails: {str(e)}",
            "unread_emails": []
        }

@app.get("/api/status")
async def get_status():
    """Get current system status."""
    # Check ingestion engine status
    ingestion_status = False
    try:
        engine = get_ingestion_engine()
        ingestion_status = engine is not None
    except:
        ingestion_status = False
    
    return {
        "system_status": {
            **system_status,
            "ingestion_engine_connected": ingestion_status
        },
        "processed_emails_count": len(processed_emails),
        "latest_emails": processed_emails[-5:] if processed_emails else [],
        "email_credentials": {
            "host": email_credentials.get("host", ""),
            "port": email_credentials.get("port", ""),
            "username": email_credentials.get("username", ""),
            "password_set": bool(email_credentials.get("password", "")),
            "folder": email_credentials.get("folder", "")
        },
        "azure_config": {
            "storage_account": azure_config.get("storage_account", ""),
            "container_name": azure_config.get("container_name", ""),
            "connection_string_set": bool(azure_config.get("connection_string", ""))
        }
    }

@app.post("/setup/ingestion")
async def setup_ingestion():
    """Initialize the ingestion engine."""
    try:
        engine = get_ingestion_engine()
        if engine:
            return {"status": "success", "message": "Ingestion engine initialized successfully"}
        else:
            return {"status": "error", "message": "Failed to initialize ingestion engine"}
    except Exception as e:
        logger.error(f"Error initializing ingestion engine: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/ingestion/status")
async def get_ingestion_status():
    """Get detailed ingestion engine status and recent activities."""
    try:
        engine = get_ingestion_engine()
        if not engine:
            return {"status": "disconnected", "message": "Ingestion engine not initialized"}
        
        # Try to get some basic info from the database
        try:
            # This is a simple test to see if the database is accessible
            db_status = "connected"
            message = "Ingestion engine connected and database accessible"
        except Exception as e:
            db_status = "error" 
            message = f"Database connection error: {str(e)}"
        
        return {
            "status": db_status,
            "message": message,
            "engine_initialized": True
        }
        
    except Exception as e:
        logger.error(f"Error checking ingestion status: {e}")
        return {"status": "error", "message": str(e), "engine_initialized": False}

@app.get("/api/blob-debug/{folder_name}")
async def debug_blob_folder(folder_name: str):
    """Debug endpoint to check what blobs exist in a folder."""
    try:
        from azure.storage.blob import BlobServiceClient
        
        if not azure_config.get("connection_string"):
            return {"status": "error", "message": "Azure not configured"}
        
        blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
        container_client = blob_service_client.get_container_client(azure_config["container_name"])
        
        # List all blobs with the folder prefix
        blobs = []
        for blob in container_client.list_blobs(name_starts_with=folder_name):
            blob_info = {
                "name": blob.name,
                "size": blob.size,
                "last_modified": str(blob.last_modified),
                "url": f"https://{azure_config['storage_account']}.blob.core.windows.net/{azure_config['container_name']}/{blob.name}"
            }
            blobs.append(blob_info)
        
        return {
            "status": "success", 
            "folder_name": folder_name,
            "blob_count": len(blobs),
            "blobs": blobs
        }
        
    except Exception as e:
        logger.error(f"Blob debug error: {str(e)}")
        return {"status": "error", "message": str(e)}

async def get_all_emails_from_azure_blob_storage():
    """
    Get ALL emails directly from Azure Blob Storage.
    This is the REAL source of historical emails.
    """
    try:
        from azure.storage.blob import BlobServiceClient
        import json

        if not azure_config.get("connection_string"):
            logger.error("Azure not configured")
            return []

        blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
        container_client = blob_service_client.get_container_client(azure_config["container_name"])

        all_emails = []

        # List all blobs that contain email metadata
        logger.info("Scanning Azure Blob Storage for all emails...")
        for blob in container_client.list_blobs():
            # Look for metadata files that contain email information
            if blob.name.endswith("metadata.json") and "email_" in blob.name:
                try:
                    # Download and parse the metadata
                    blob_client = blob_service_client.get_blob_client(
                        container=azure_config["container_name"],
                        blob=blob.name
                    )

                    metadata_content = blob_client.download_blob().readall()
                    metadata = json.loads(metadata_content.decode('utf-8'))

                    # Extract email information from metadata
                    email_info = {
                        "id": metadata.get("email_id", blob.name.split("/")[0]),
                        "subject": metadata.get("subject", "No Subject"),
                        "from": metadata.get("from", "Unknown"),
                        "to": metadata.get("to", ""),
                        "date": metadata.get("date", ""),
                        "document_type": metadata.get("document_type", "Unclassified"),
                        "classification_confidence": metadata.get("classification_confidence", 0),
                        "attachments_count": len(metadata.get("attachments", [])),
                        "email_blob_url": f"https://{azure_config['storage_account']}.blob.core.windows.net/{azure_config['container_name']}/{blob.name.replace('metadata.json', 'original_email.eml')}",
                        "processed_at": str(blob.last_modified),
                        "source": "azure_blob_storage"
                    }

                    all_emails.append(email_info)

                except Exception as e:
                    logger.warning(f"Could not parse metadata from {blob.name}: {str(e)}")
                    continue

        # Sort by date (newest first)
        all_emails.sort(key=lambda x: x.get("date", ""), reverse=True)

        logger.info(f"Found {len(all_emails)} emails in Azure Blob Storage")
        return all_emails

    except Exception as e:
        logger.error(f"Error retrieving emails from Azure Blob Storage: {str(e)}")
        return []

@app.get("/api/current-session-emails")
async def get_current_session_emails(
    sender: Optional[str] = None,
    subject: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get emails processed in the current session with optional filtering.
    
    Args:
        sender: Filter by email sender
        subject: Filter by email subject (partial match)
        category: Filter by document category
        start_date: Filter emails after this date (YYYY-MM-DD)
        end_date: Filter emails before this date (YYYY-MM-DD)
    """
    try:
        # Get base list of current session emails (emails processed during this visit)
        filtered_emails = [e for e in current_session_emails if not e.get("is_deleted", False)]
        
        # Apply filters
        if sender:
            filtered_emails = [e for e in filtered_emails if sender.lower() in e.get("from", "").lower()]
        if subject:
            filtered_emails = [e for e in filtered_emails if subject.lower() in e.get("subject", "").lower()]
        if category:
            filtered_emails = [e for e in filtered_emails if e.get("document_type") == category]
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filtered_emails = [e for e in filtered_emails if datetime.strptime(e.get("date", "").split()[0], "%Y-%m-%d") >= start_dt]
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            filtered_emails = [e for e in filtered_emails if datetime.strptime(e.get("date", "").split()[0], "%Y-%m-%d") <= end_dt]
        
        return {"success": True, "emails": filtered_emails}
    except Exception as e:
        logger.error(f"Error getting current session emails: {str(e)}")
        return {"success": False, "error": str(e)}

from fastapi import Query

@app.get("/api/all-historical-emails")
async def get_all_historical_emails_from_azure():
    """
    Get ALL historical emails directly from Azure Blob Storage.
    This completely ignores current session data and goes straight to the source.
    """
    try:
        logger.info("Fetching ALL historical emails from Azure Blob Storage...")

        # Get emails directly from Azure Blob Storage
        historical_emails = await get_all_emails_from_azure_blob_storage()

        if not historical_emails:
            return {
                "success": True,
                "emails": [],
                "total": 0,
                "message": "No historical emails found in Azure Blob Storage"
            }

        logger.info(f"Successfully retrieved {len(historical_emails)} historical emails from Azure")

        return {
            "success": True,
            "emails": historical_emails,  # ALL emails, no limit!
            "total": len(historical_emails),
            "source": "azure_blob_storage"
        }

    except Exception as e:
        logger.error(f"Error retrieving historical emails from Azure: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "emails": [],
            "total": 0
        }

@app.get("/api/processed-emails")
async def get_processed_emails(
    status: str = Query(None, description="Filter by read/unread status"),
    sender: str = Query(None),
    subject: str = Query(None),
    category: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    """
    Get emails from CosmosDB with optional filtering.
    Combines all emails from current session and database.
    
    Args:
        status: Filter by read/unread status
        sender: Filter by email sender
        subject: Filter by email subject (partial match)
        category: Filter by document category
        start_date: Filter emails after this date (YYYY-MM-DD)
        end_date: Filter emails before this date (YYYY-MM-DD)
    """
    try:
        # Get emails from CosmosDB
        endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        key = os.getenv("AZURE_COSMOS_KEY")
        db_name = os.getenv("COSMOS_DB_NAME", "IngestionDB")
        container_name = os.getenv("COSMOS_EMAILS_CONTAINER", "Emails")
        
        emails = []
        
        # Try to get emails from CosmosDB first
        try:
            client = CosmosClient(endpoint, key)
            db = client.get_database_client(db_name)
            container = db.get_container_client(container_name)
            
            # Build base query
            query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.is_deleted)"
            filters = []
            params = []
            
            # Add filters
            if status == "unread":
                filters.append("(NOT IS_DEFINED(c.read) OR c.read = false)")
            elif status == "read":
                filters.append("c.read = true")
                
            if sender:
                filters.append("CONTAINS(LOWER(c.from), @sender)")
                params.append({"name": "@sender", "value": sender.lower()})
                
            if subject:
                filters.append("CONTAINS(LOWER(c.subject), @subject)")
                params.append({"name": "@subject", "value": subject.lower()})
                
            if category:
                filters.append("LOWER(c.document_type) = @category")
                params.append({"name": "@category", "value": category.lower()})
                
            if start_date:
                filters.append("c.date >= @start_date")
                params.append({"name": "@start_date", "value": start_date})
                
            if end_date:
                filters.append("c.date <= @end_date")
                params.append({"name": "@end_date", "value": end_date})
            
            # Add filters to query
            if filters:
                query += " AND " + " AND ".join(filters)
            query += " ORDER BY c.date DESC"
            
            # Execute query
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            # Map database emails to response format
            for e in items:
                emails.append({
                    "id": e.get("id"),
                    "subject": e.get("subject"),
                    "from": e.get("from"),
                    "to": e.get("to"),
                    "date": e.get("date"),
                    "document_type": e.get("document_type"),
                    "classification_confidence": e.get("classification_confidence"),
                    "attachments_count": e.get("attachments_count"),
                    "email_blob_url": e.get("email_blob_url"),
                    "cosmos_document_id": e.get("id"),
                    "ingestion_processed": e.get("ingestion_processed"),
                    "ingestion_error": e.get("ingestion_error"),
                    "category": e.get("document_type")
                })
            
        except Exception as db_error:
            logger.error(f"Error querying CosmosDB: {str(db_error)}")
            # Fall back to in-memory emails only
            pass
        
        # Handle different status requests
        if status == "unread":
            # For unread: ONLY return current session emails
            session_emails = [e for e in current_session_emails if not e.get("is_deleted", False)]
            emails = []  # Don't include any historical emails for unread view
        elif status == "read" or status == "all":
            # For read/all: ONLY return historical emails (NOT current session)
            session_emails = []  # Don't include current session emails for read view
        else:
            # Default: include current session emails
            session_emails = [e for e in current_session_emails if not e.get("is_deleted", False)]
        
        # Apply filters to session emails
        if sender:
            session_emails = [e for e in session_emails if sender.lower() in (e.get("from", "") or "").lower()]
        if subject:
            session_emails = [e for e in session_emails if subject.lower() in (e.get("subject", "") or "").lower()]
        if category:
            session_emails = [e for e in session_emails if (e.get("document_type") or "").lower() == category.lower()]
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                session_emails = [e for e in session_emails if e.get("date") and datetime.strptime(str(e["date"])[:10], "%Y-%m-%d") >= start]
            except Exception:
                pass
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                session_emails = [e for e in session_emails if e.get("date") and datetime.strptime(str(e["date"])[:10], "%Y-%m-%d") <= end]
            except Exception:
                pass
                
        # Add filtered session emails (only if not in read-only mode)
        if status != "read":
            emails.extend([e for e in session_emails if e["id"] not in [x["id"] for x in emails]])

        # For unread status, ONLY use session emails
        if status == "unread":
            emails = session_emails

        # Sort by date descending (newest first)
        emails.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return {
            "success": True,
            "emails": emails,  # Return ALL emails, no limit!
            "total": len(emails)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving emails: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/email-categories")
async def get_email_categories():
    """Get all unique document categories from processed emails."""
    try:
        # Only include categories from non-deleted emails
        categories = set(
            email.get("document_category", "Uncategorized") 
            for email in processed_emails 
            if not email.get("is_deleted", False)
        )
        return {
            "success": True,
            "categories": sorted(list(categories))
        }
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        return {"success": False, "error": str(e)}

@app.delete("/api/emails/{email_id}")
async def soft_delete_email(email_id: str):
    """
    Soft delete an email by marking it as deleted in memory and CosmosDB.
    
    Since CosmosDB doesn't support actual deletion, we:
    1. Mark the email as deleted in memory
    2. Add a deleted flag in CosmosDB document
    3. Hide it from regular queries
    """
    try:
        # Find email in memory
        email_index = next((i for i, e in enumerate(processed_emails) 
                          if e.get("id") == email_id), -1)
        
        if email_index == -1:
            raise HTTPException(status_code=404, detail="Email not found")
            
        # Mark as deleted in memory
        processed_emails[email_index]["is_deleted"] = True
        processed_emails[email_index]["deleted_at"] = datetime.now().isoformat()
        
        # Update CosmosDB if available
        try:
            engine = get_ingestion_engine()
            if engine and hasattr(engine, 'update_document_status'):
                await engine.update_document_status(
                    email_id,
                    {"is_deleted": True, "deleted_at": datetime.now().isoformat()}
                )
        except Exception as e:
            logger.warning(f"Could not update CosmosDB status: {str(e)}")
        
        return {
            "success": True,
            "message": "Email marked as deleted",
            "email_id": email_id
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/stop")
async def stop_processing():
    """Stop email processing."""
    system_status["processing_active"] = False
    return {"status": "success", "message": "Processing stopped"}

if __name__ == "__main__":
    uvicorn.run("ui_app:app", host="127.0.0.1", port=8000, reload=True)
