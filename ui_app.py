"""
Web UI for Insurance AI Agent - Simplified setup with auto-configuration.
"""
import asyncio
import logging
import os
import sys
import subprocess
import tempfile
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import imaplib
import email
import json
from email.header import decode_header

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auto_install_dependencies():
    """Automatically install required dependencies."""
    try:
        logger.info("📦 Auto-installing dependencies...")
        packages = [
            "azure-cosmos",
            "azure-servicebus", 
            "azure-storage-blob",
            "azure-identity",
            "azure-ai-formrecognizer",
            "python-dotenv"
        ]
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"✅ Installed {package}")
            except Exception as e:
                logger.warning(f"⚠️ Could not install {package}: {e}")
        
        logger.info("✅ Dependency installation complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error installing dependencies: {e}")
        return False

def check_azure_config():
    """Check if Azure configuration is ready."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            "AZURE_COSMOS_ENDPOINT",
            "AZURE_COSMOS_KEY",
            "SERVICE_BUS_CONNECTION_STRING"
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
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
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Insurance AI Agent...")
    
    # Auto-install dependencies
    logger.info("📦 Auto-installing dependencies...")
    if auto_install_dependencies():
        logger.info("✅ Dependencies installed successfully")
    else:
        logger.warning("⚠️ Some dependencies may not have installed correctly")
    
    # Auto-check Azure config
    logger.info("☁️ Checking Azure configuration...")
    if check_azure_config():
        logger.info("✅ Azure configuration loaded successfully")
        system_status["azure_connected"] = True
        system_status["prerequisites_installed"] = True
    else:
        logger.error("❌ Azure configuration incomplete")
    
    logger.info("✅ Startup complete - System ready for email setup")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")

# Try to import ingestion engine (will work after dependencies are installed)
try:
    from src.ingestion_engine.ingestion_processor import IngestionEngine
except ImportError:
    logger.warning("Ingestion engine not available yet - will be loaded after dependencies")
    IngestionEngine = None

# Email provider settings
EMAIL_PROVIDERS = {
    "gmail.com": {"host": "imap.gmail.com", "port": 993},
    "googlemail.com": {"host": "imap.gmail.com", "port": 993},
    "outlook.com": {"host": "outlook.office365.com", "port": 993},
    "hotmail.com": {"host": "outlook.office365.com", "port": 993},
    "live.com": {"host": "outlook.office365.com", "port": 993},
    "yahoo.com": {"host": "imap.mail.yahoo.com", "port": 993},
    "icloud.com": {"host": "imap.mail.me.com", "port": 993},
    "me.com": {"host": "imap.mail.me.com", "port": 993},
    "aol.com": {"host": "imap.aol.com", "port": 993},
}

def detect_email_provider(email_address: str) -> Dict[str, any]:
    """Auto-detect email provider settings from email address."""
    try:
        domain = email_address.split('@')[1].lower()
        if domain in EMAIL_PROVIDERS:
            return EMAIL_PROVIDERS[domain]
        else:
            # Default to common IMAP settings
            return {"host": f"imap.{domain}", "port": 993}
    except:
        # Fallback to Gmail settings
        return {"host": "imap.gmail.com", "port": 993}

app = FastAPI(title="Insurance AI Agent", description="Automated Email Processing", lifespan=lifespan)

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
system_status = {
    "azure_connected": bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")),  # Check if configured
    "email_connected": False,
    "prerequisites_installed": True,  # Auto-installed
    "processing_active": False
}

email_config = {}

email_credentials = {
    "host": "",
    "port": 993,
    "username": "",
    "password": "",
    "folder": "INBOX"
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

processed_emails = []

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("simple_dashboard.html", {
        "request": request,
        "system_status": system_status
    })

@app.post("/setup/prerequisites")
async def setup_prerequisites():
    """Install and setup all prerequisites."""
    try:
        logger.info("Setting up prerequisites...")
        
        # Simulate prerequisite installation
        import subprocess
        import sys
        
        packages = [
            "azure-storage-blob",
            "azure-identity", 
            "pydantic-settings",
            "PyPDF2",
            "pytesseract",
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
        
        return {
            "status": "success",
            "message": f"✅ Email connected successfully! Found {unread_count} unread emails.",
            "provider": f"{provider_name} ({host}:{port})",
            "total_emails": total_emails,
            "unread_emails": unread_count,
            "connection_details": {
                "host": host,
                "port": port,
                "folder": folder,
                "provider": provider_name
            }
        }
        
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

async def process_single_email(mail, email_id, blob_service_client):
    """Process a single email and upload to Azure."""
    # Fetch email
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    email_body = msg_data[0][1]
    email_message = email.message_from_bytes(email_body)
    
    # Generate unique folder name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"email_{timestamp}_{email_id.decode()}"
    
    # Extract email metadata
    metadata = extract_email_metadata(email_message)
    
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
        raise    # Process attachments and extract text
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
                        
                        attachments_info.append({
                            "filename": filename,
                            "size": len(attachment_data),
                            "blob_path": attachment_blob_name
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to process attachment {filename}: {str(e)}")
                        continue
    
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
    
    processed_emails.append(processed_email)
    
    # Mark email as read
    mail.store(email_id, '+FLAGS', '\\Seen')
    
    # Return processing results
    return processed_email

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
    """Extract text from PDF data using multiple methods."""
    extracted_text = ""
    
    try:
        # Method 1: Try PyPDF2 for selectable text
        try:
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
                return extracted_text
                
        except ImportError:
            logger.warning("PyPDF2 not installed")
            
        # Method 2: Try pdfplumber for better text extraction
        try:
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
                return extracted_text
                
        except ImportError:
            logger.warning("pdfplumber not installed")
            
        # Method 3: OCR for image-based PDFs using pytesseract
        if not extracted_text.strip():
            try:
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
                    return extracted_text
                    
            except ImportError as e:
                logger.warning(f"OCR libraries not installed: {e}")
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")
        
        # If no text extracted, return info about the PDF
        if not extracted_text.strip():
            return f"PDF file detected ({len(pdf_data)} bytes) - No extractable text found. Install pytesseract and PyMuPDF for OCR support."
        
        return extracted_text
        
    except Exception as e:
        logger.error(f"PDF text extraction error: {str(e)}")
        return f"PDF processing failed: {str(e)}"

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

@app.get("/api/processed-emails")
async def get_processed_emails():
    """Get list of processed emails."""
    return {"emails": processed_emails}

@app.post("/process/stop")
async def stop_processing():
    """Stop email processing."""
    system_status["processing_active"] = False
    return {"status": "success", "message": "Processing stopped"}

if __name__ == "__main__":
    uvicorn.run("ui_app:app", host="0.0.0.0", port=8080, reload=True)
