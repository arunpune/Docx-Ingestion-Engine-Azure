# 🏢 Insurance AI Agent

A comprehensive email processing system that automatically scans, extracts, and stores insurance-related documents using Azure services and OCR technology.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Azure Setup Guide](#azure-setup-guide)
- [Email Configuration](#email-configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)

## 🎯 Overview

The Insurance AI Agent is a web-based application that:
- **Connects to your email** (Gmail, Outlook, Yahoo, etc.)
- **Scans unread emails** for attachments and documents
- **Extracts text** from PDFs using OCR technology
- **Stores everything** in Azure Blob Storage
- **Provides easy access** with clickable links to processed files

## ✨ Features

### 📧 Email Processing
- **Auto-detects email providers** (Gmail, Outlook, Yahoo, etc.)
- **Secure authentication** with App Passwords support
- **Real-time email scanning** for unread messages
- **Attachment extraction** and processing

### 🔍 OCR & Document Processing
- **PDF text extraction** for selectable text
- **OCR scanning** for image-based PDFs using Tesseract
- **Multiple PDF libraries** (PyPDF2, pdfplumber, PyMuPDF)
- **Automatic text classification** and storage

### ☁️ Azure Integration
- **Blob Storage** for secure file storage
- **Automatic container creation** and management
- **Organized folder structure** for each email
- **Public or private access** configuration

### 🌐 Web Interface
- **One-click setup** for all prerequisites
- **Real-time status updates** during processing
- **Processed emails dashboard** with clickable links
- **Debug tools** for troubleshooting

## 🔧 Prerequisites

### Required Software
- **Python 3.8+** (tested with Python 3.13)
- **pip** (Python package manager)
- **Git** (for cloning the repository)

### Required Accounts
- **Azure Account** (free tier available)
- **Email Account** (Gmail, Outlook, Yahoo, etc.)

## 📥 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Insurance-AI-Agent.git
cd Insurance-AI-Agent
```

### 2. Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install basic dependencies first
pip install -r requirements-basic.txt
```

### 3. Install OCR Dependencies (Optional but Recommended)
```bash
pip install PyPDF2 pdfplumber pytesseract PyMuPDF
```

For Tesseract OCR on Windows:
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Or use: `choco install tesseract` (if you have Chocolatey)

## ☁️ Azure Setup Guide

### Step 1: Create Azure Storage Account

#### Option A: Azure Portal (Recommended)
1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Storage account"** and click **Create**
4. Fill in the details:
   - **Subscription**: Choose your subscription
   - **Resource Group**: Create new `insurance-ai-rg`
   - **Storage account name**: `insuranceai[random-number]`
   - **Region**: Choose closest to you
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage)
5. Click **"Review + Create"** then **"Create"**

#### Option B: Azure CLI
```bash
# Login to Azure
az login

# Create resource group
az group create --name insurance-ai-rg --location "East US"

# Create storage account
az storage account create \
    --name insuranceai$(shuf -i 1000-9999 -n 1) \
    --resource-group insurance-ai-rg \
    --location "East US" \
    --sku Standard_LRS
```

### Step 2: Create Container
1. Go to your storage account in Azure Portal
2. Click **"Containers"** in the left menu
3. Click **"+ Container"**
4. Enter details:
   - **Name**: `insurance-emails`
   - **Public access level**: **Private** (recommended) or **Blob** (for direct access)
5. Click **"Create"**

### Step 3: Get Credentials
1. In your storage account, go to **"Access keys"**
2. Click **"Show keys"**
3. Copy the following:
   - **Storage account name**
   - **Key1** (or Key2)
   - **Connection string** (optional, for advanced users)

### Step 4: Configure Public Access (Optional)
For direct blob access without authentication:
1. Go to **Configuration** in your storage account
2. Set **"Allow Blob public access"** to **"Enabled"**
3. Go to **Containers** → **insurance-emails** → **Change access level**
4. Select **"Blob (anonymous read access for blobs only)"**

## 📧 Email Configuration

### Gmail Setup (Recommended)
1. **Enable 2-Step Verification**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable "2-Step Verification"

2. **Create App Password**:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Enter "Insurance AI Agent"
   - Copy the 16-character password

3. **Enable IMAP**:
   - Go to [Gmail Settings](https://mail.google.com/mail/u/0/#settings/fwdandpop)
   - Click "Forwarding and POP/IMAP"
   - Enable "IMAP Access"

### Outlook/Hotmail Setup
1. **Modern Authentication** (Recommended):
   - Use your regular Microsoft account credentials
   - Enable "Less secure app access" if needed

2. **App Password** (Alternative):
   - Go to [Microsoft Account Security](https://account.microsoft.com/security)
   - Create an app password for "Mail"

### Yahoo Setup
1. **Generate App Password**:
   - Go to [Yahoo Account Security](https://account.yahoo.com/account/security)
   - Enable "Two-step verification"
   - Generate app password for "Mail"

### Other Email Providers
- **iCloud**: Use app-specific password
- **Custom IMAP**: Provide host and port manually

## 🚀 Running the Application

### 1. Start the Web Interface
```bash
python start_ui.py
```

### 2. Open in Browser
Navigate to: [http://localhost:8080](http://localhost:8080)

### 3. Setup Process
1. **Prerequisites**: Click "Install Prerequisites" (automatic)
2. **Azure Setup**: Enter your storage account name and key
3. **Email Setup**: Enter your email and password/app password
4. **Process Emails**: Click "Start Email Processing"

## 🔧 How It Works

### Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email Server  │───▶│  Insurance AI   │───▶│  Azure Storage  │
│   (IMAP/SSL)    │    │     Agent       │    │   (Blob/OCR)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Processing Flow
1. **Email Connection**: Connects to your email via IMAP
2. **Scan Unread**: Searches for unread emails
3. **Extract Attachments**: Downloads PDF and image files
4. **OCR Processing**: Extracts text using multiple methods:
   - PyPDF2 for selectable text
   - pdfplumber for better extraction
   - Tesseract OCR for image-based PDFs
5. **Storage**: Uploads to Azure Blob Storage with organized structure:
   ```
   insurance-emails/
   ├── email_20240818_123456_001/
   │   ├── original_email.eml
   │   ├── metadata.json
   │   ├── attachments/
   │   │   ├── document1.pdf
   │   │   └── image1.jpg
   │   └── ocr/
   │       └── document1.pdf_text.txt
   ```

### Folder Structure
Each processed email creates a timestamped folder containing:
- **original_email.eml**: Raw email file
- **metadata.json**: Email information (subject, from, date, etc.)
- **attachments/**: All email attachments
- **ocr/**: Extracted text from PDFs

## 🐛 Troubleshooting

### Common Issues

#### Email Connection Errors
**Error**: `[AUTHENTICATIONFAILED] Invalid credentials`
- **Gmail**: Use App Password, not regular password
- **Outlook**: Enable "Less secure app access" or use app password
- **Yahoo**: Use app-specific password
- **General**: Check if IMAP is enabled

#### Azure Storage Errors
**Error**: `PublicAccessNotPermitted`
- Enable public access in Azure Portal (see Azure Setup Step 4)
- Or access files through Azure Portal → Storage Explorer

**Error**: `BlobNotFound`
- Check if container "insurance-emails" exists
- Verify storage account credentials
- Use debug endpoint: `/api/blob-debug/{folder_name}`

**Error**: `AuthenticationFailed`
- Verify storage account name and key
- Check connection string format

#### OCR Issues
**Error**: `PyPDF2 not installed`
```bash
pip install PyPDF2 pdfplumber pytesseract PyMuPDF
```

**Error**: `pytesseract not found`
- Install Tesseract OCR system package
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

### Debug Tools

#### Email Test Script
```bash
python email_test.py
```

#### Blob Storage Debug
```bash
python debug_blob.py
```

#### Azure Access Guide
```bash
python azure_access_guide.py
```

### Log Files
- Check terminal output for detailed error messages
- Use browser Developer Tools (F12) for JavaScript errors
- Monitor Azure Portal for storage activity

## 📡 API Documentation

### Endpoints

#### Setup Endpoints
- `POST /setup/prerequisites` - Install required packages
- `POST /setup/azure` - Configure Azure Storage
- `POST /setup/email` - Test email connection

#### Processing Endpoints
- `POST /process/start` - Start email processing
- `POST /process/stop` - Stop email processing
- `GET /api/unread-emails` - List unread emails

#### Status Endpoints
- `GET /api/status` - Get system status
- `GET /api/processed-emails` - List processed emails
- `GET /api/blob-debug/{folder_name}` - Debug blob storage

### Example Usage

#### Check System Status
```javascript
fetch('/api/status')
.then(response => response.json())
.then(data => console.log(data));
```

#### Get Unread Emails
```javascript
fetch('/api/unread-emails')
.then(response => response.json())
.then(data => console.log(data.unread_emails));
```

## 🔐 Security Best Practices

### Email Security
- **Use App Passwords** instead of regular passwords
- **Enable 2FA** on your email account
- **Limit IMAP access** to specific applications only

### Azure Security
- **Use private containers** for sensitive data
- **Rotate storage keys** regularly
- **Enable access logging** for audit trails
- **Set up SAS tokens** for temporary access

### Application Security
- **Don't commit credentials** to version control
- **Use environment variables** for sensitive data
- **Regular security updates** for dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Getting Help
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check this README and inline code comments

### Useful Links
- [Azure Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)

---

## 🎉 Quick Start Summary

1. **Clone**: `git clone [repository-url]`
2. **Install**: `pip install -r requirements.txt`
3. **Azure**: Create storage account and container
4. **Email**: Setup app password (Gmail) or enable IMAP
5. **Run**: `python start_ui.py`
6. **Setup**: Open [localhost:8080](http://localhost:8080) and configure
7. **Process**: Click "Start Email Processing"

That's it! Your emails will be processed and stored in Azure with OCR text extraction. 🚀
