"""
Web UI for Insurance AI Agent - One-click setup and email processing.
"""
import asyncio
import logging
import os
import tempfile
import re
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

app = FastAPI(title="Insurance AI Agent - Web UI", version="1.0.0")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
system_status = {
    "azure_connected": False,
    "email_connected": False,
    "prerequisites_installed": False,
    "processing_active": False
}

email_credentials = {
    "host": "",
    "port": 993,
    "username": "",
    "password": "",
    "folder": "INBOX"
}

azure_config = {
    "storage_account": "",
    "storage_key": "",
    "container_name": "insurance-emails"
}

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
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "system_status": system_status,
        "processed_emails": processed_emails
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
    username: str = Form(...),
    password: str = Form(...),
    folder: str = Form(default="INBOX")
):
    """Setup email connection with auto-detected provider settings."""
    try:
        # Auto-detect email provider settings
        provider_settings = detect_email_provider(username)
        host = provider_settings["host"]
        port = provider_settings["port"]
        
        logger.info(f"Auto-detected settings for {username}: {host}:{port}")
        
        # Test email connection
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(username, password)
        mail.select(folder)
        
        # Get basic info
        status, messages = mail.search(None, 'ALL')
        total_emails = len(messages[0].split()) if messages[0] else 0
        
        # Get unread emails count
        status, unread = mail.search(None, 'UNSEEN')
        unread_count = len(unread[0].split()) if unread[0] else 0
        
        mail.logout()
        
        email_credentials.update({
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "folder": folder
        })
        
        system_status["email_connected"] = True
        
        # Extract provider name from host
        provider_name = host.replace("imap.", "").replace(".com", "").title()
        
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
    """Process all unread emails."""
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
            return
        
        blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
        
        processed_count = 0
        for email_id in email_ids[:10]:  # Process max 10 emails at a time
            try:
                logger.info(f"Processing email {email_id.decode()}")
                await process_single_email(mail, email_id, blob_service_client)
                processed_count += 1
                logger.info(f"Successfully processed email {email_id.decode()}")
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {str(e)}")
                continue
        
        mail.logout()
        system_status["processing_active"] = False
        
        logger.info(f"Email processing completed. Processed {processed_count} out of {len(email_ids)} emails")
        
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        system_status["processing_active"] = False

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
    
    # Add to processed emails list
    processed_email = {
        "id": email_id.decode(),
        "subject": metadata.get("subject", "No Subject"),
        "from": metadata.get("from", "Unknown"),
        "date": metadata.get("date", "Unknown"),
        "folder_name": folder_name,
        "folder_url": folder_urls.get("direct_url") if isinstance(folder_urls, dict) else folder_urls,
        "portal_url": folder_urls.get("portal_url") if isinstance(folder_urls, dict) else None,
        "folder_path": folder_urls.get("folder_path") if isinstance(folder_urls, dict) else folder_name,
        "attachments_count": len(attachments_info),
        "ocr_results_count": len(ocr_results),
        "processed_at": datetime.now().isoformat()
    }
    
    processed_emails.append(processed_email)
    
    # Mark email as read
    mail.store(email_id, '+FLAGS', '\\Seen')

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
    return {
        "system_status": system_status,
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
