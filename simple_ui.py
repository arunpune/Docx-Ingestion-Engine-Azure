"""
Simplified Web UI for Insurance AI Agent - Email and App Password Only
Pre-configured with Azure credentials, automatic dependency installation.
"""
import asyncio
import logging
import os
import sys
import subprocess
import tempfile
import re
import uuid
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Insurance AI Agent", description="Automated Email Processing")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

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

# Global state
system_status = {
    "dependencies_ready": False,
    "azure_ready": False,
    "email_connected": False
}

email_config = {}

def auto_install_dependencies():
    """Automatically install required dependencies."""
    try:
        logger.info("Auto-installing dependencies...")
        packages = [
            "azure-cosmos",
            "azure-servicebus", 
            "azure-storage-blob",
            "azure-identity",
            "azure-ai-formrecognizer",
            "fastapi",
            "uvicorn",
            "python-dotenv",
            "Pillow"
        ]
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"✅ Installed {package}")
            except Exception as e:
                logger.warning(f"⚠️ Could not install {package}: {e}")
        
        system_status["dependencies_ready"] = True
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
        
        system_status["azure_ready"] = True
        logger.info("✅ Azure configuration ready")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking Azure config: {e}")
        return False

def detect_email_provider(email_address: str) -> Dict[str, any]:
    """Auto-detect email provider settings."""
    try:
        domain = email_address.split('@')[1].lower()
        return EMAIL_PROVIDERS.get(domain, {"host": f"imap.{domain}", "port": 993})
    except:
        return {"host": "imap.gmail.com", "port": 993}

async def test_email_connection(email_address: str, password: str) -> Dict:
    """Test email connection with provided credentials."""
    try:
        provider = detect_email_provider(email_address)
        host = provider["host"]
        port = provider["port"]
        
        logger.info(f"Testing connection to {host}:{port} for {email_address}")
        
        # Test connection
        mail = imaplib.IMAP4_SSL(host, port)
        result = mail.login(email_address, password)
        
        # Get folder info
        folders = mail.list()
        status, messages = mail.select('INBOX')
        total_emails = int(messages[0]) if messages[0] else 0
        
        mail.logout()
        
        return {
            "status": "success",
            "message": f"Connected successfully! Found {total_emails} emails in INBOX",
            "host": host,
            "port": port,
            "total_emails": total_emails
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Connection failed: {str(e)}"
        }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page - simplified email setup only."""
    return templates.TemplateResponse("simple_dashboard.html", {
        "request": request,
        "system_status": system_status
    })

@app.post("/setup/auto")
async def auto_setup():
    """Automatically setup dependencies and Azure configuration."""
    try:
        results = {
            "dependencies": False,
            "azure": False,
            "errors": []
        }
        
        # Install dependencies
        if auto_install_dependencies():
            results["dependencies"] = True
        else:
            results["errors"].append("Failed to install some dependencies")
        
        # Check Azure config
        if check_azure_config():
            results["azure"] = True
        else:
            results["errors"].append("Azure configuration missing or incomplete")
        
        status = "success" if results["dependencies"] and results["azure"] else "partial"
        
        return {
            "status": status,
            "results": results,
            "message": "Auto-setup complete" if status == "success" else "Auto-setup completed with issues"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/setup/email")
async def setup_email(
    email_address: str = Form(...),
    app_password: str = Form(...)
):
    """Setup email connection with just email and app password."""
    try:
        # Test connection
        result = await test_email_connection(email_address, app_password)
        
        if result["status"] == "success":
            # Save email config
            email_config.update({
                "email": email_address,
                "password": app_password,
                "host": result["host"],
                "port": result["port"]
            })
            
            system_status["email_connected"] = True
            
            # Update environment variables
            os.environ["EMAIL_USERNAME"] = email_address
            os.environ["EMAIL_PASSWORD"] = app_password
            os.environ["EMAIL_HOST"] = result["host"]
            os.environ["EMAIL_PORT"] = str(result["port"])
            
            return {
                "status": "success",
                "message": f"Email connected! {result['message']}",
                "ready_to_process": True
            }
        else:
            return result
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process/emails")
async def process_emails():
    """Process emails from connected account."""
    try:
        if not system_status["email_connected"]:
            return {"status": "error", "message": "Email not connected"}
        
        if not system_status["azure_ready"]:
            return {"status": "error", "message": "Azure not configured"}
        
        # Import ingestion engine (only after dependencies are ready)
        from src.ingestion_engine.ingestion_processor import IngestionEngine
        
        engine = IngestionEngine()
        
        # Connect to email
        mail = imaplib.IMAP4_SSL(email_config["host"], email_config["port"])
        mail.login(email_config["email"], email_config["password"])
        mail.select('INBOX')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        processed_count = 0
        errors = []
        
        for email_id in email_ids[:10]:  # Process up to 10 emails
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email data
                email_data = {
                    "id": str(uuid.uuid4()),
                    "from": email_message.get("From", ""),
                    "to": email_message.get("To", ""),
                    "subject": email_message.get("Subject", ""),
                    "date": email_message.get("Date", ""),
                    "body": ""
                }
                
                # Get email body
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            email_data["body"] = part.get_payload(decode=True).decode()
                            break
                else:
                    email_data["body"] = email_message.get_payload(decode=True).decode()
                
                # Process attachments (simplified)
                attachments = []
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename:
                                attachments.append({
                                    "filename": filename,
                                    "uri": f"email_attachment_{len(attachments)}"
                                })
                
                # Send to ingestion engine
                ingestion_message = {
                    "processing_id": str(uuid.uuid4()),
                    "source_type": "email",
                    "email": email_data,
                    "attachments": attachments
                }
                
                if engine.process_ingestion_message(ingestion_message):
                    processed_count += 1
                    # Mark as read
                    mail.store(email_id, '+FLAGS', '\\Seen')
                else:
                    errors.append(f"Failed to process email: {email_data['subject']}")
                    
            except Exception as e:
                errors.append(f"Error processing email {email_id}: {str(e)}")
        
        mail.logout()
        
        return {
            "status": "success",
            "processed": processed_count,
            "total_found": len(email_ids),
            "errors": errors
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/status")
async def get_status():
    """Get current system status."""
    return {
        "system_status": system_status,
        "email_config": {k: v for k, v in email_config.items() if k != "password"}
    }

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
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
    else:
        logger.error("❌ Azure configuration incomplete")
    
    logger.info("✅ Startup complete - System ready for email setup")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
