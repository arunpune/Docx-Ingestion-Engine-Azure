# 👥 Authors & File Attribution - Insurance AI Agent

This document provides a comprehensive overview of all files in the project and their respective authors, along with a brief explanation of each file's purpose.

## 📊 Author Distribution Summary

- **Rachit Patekar**: 7 files (Email processing, AI classification, configuration)
- **Shrvan Hatte**: 7 files (File processing, OCR, utilities, deployment) 
- **Utsav Pat**: 6 files (Ingestion engine, database, UI, documentation)

---

## 📁 File Attribution by Category

### 🚀 Core Application Files

| File | Author | Purpose |
|------|--------|---------|
| `main.py` | **Rachit Patekar** | Main application entry point and orchestration |
| `ui_app.py` | **Utsav Pat** | Web UI application with dashboard and email processing interface |
| `simple_server.py` | **Shrvan Hatte** | Lightweight FastAPI server for testing and development |

### 📧 Email Processing Module

| File | Author | Purpose |
|------|--------|---------|
| `src/email_processor/email_listener.py` | **Rachit Patekar** | Azure Logic App integration for email processing requests |
| `src/email_processor/email_handler.py` | **Rachit Patekar** | Email processing, attachment extraction, and blob storage integration |

### 📁 File Ingestion Module

| File | Author | Purpose |
|------|--------|---------|
| `src/file_ingestion/file_listener.py` | **Shrvan Hatte** | HTTP endpoints for direct file uploads and processing |
| `src/file_ingestion/file_handler.py` | **Shrvan Hatte** | Direct file processing, validation, and storage management |

### 🔄 Ingestion Engine

| File | Author | Purpose |
|------|--------|---------|
| `src/ingestion_engine/ingestion_processor.py` | **Utsav Pat** | Core ingestion engine with CosmosDB integration and processing coordination |

### 🔍 OCR & Classification Engine

| File | Author | Purpose |
|------|--------|---------|
| `src/ocr_engine/ocr_processor.py` | **Shrvan Hatte** | Text extraction using multiple OCR technologies and Azure Form Recognizer |
| `src/ocr_engine/document_classifier.py` | **Rachit Patekar** | AI-powered document classification using OpenAI GPT models |

### 🔧 Shared Components

| File | Author | Purpose |
|------|--------|---------|
| `src/shared/config.py` | **Rachit Patekar** | Centralized configuration management and environment settings |
| `src/shared/models.py` | **Utsav Pat** | SQLAlchemy database models and schema definitions |
| `src/shared/utils.py` | **Shrvan Hatte** | Common utility functions for Azure services and file operations |

### 🌐 Templates & UI

| File | Author | Purpose |
|------|--------|---------|
| `templates/dashboard.html` | **Utsav Pat** | Main dashboard template with comprehensive setup and monitoring |
| `templates/simple_dashboard.html` | **Shrvan Hatte** | Simplified dashboard template for quick email processing setup |

### ⚙️ Configuration & Deployment

| File | Author | Purpose |
|------|--------|---------|
| `requirements.txt` | **Rachit Patekar** | Python package dependencies specification |
| `package.json` | **Utsav Pat** | Node.js dependencies for Azure MCP integration |
| `Dockerfile` | **Shrvan Hatte** | Docker container configuration with OCR dependencies |
| `docker-compose.yml` | **Shrvan Hatte** | Multi-service Docker orchestration configuration |
| `.env.example` | **Shrvan Hatte** | Environment variables template with Azure service configurations |
| `.gitignore` | **Rachit Patekar** | Git ignore rules for Python, Node.js, and Azure artifacts |

### 🔄 Azure Logic Apps

| File | Author | Purpose |
|------|--------|---------|
| `logic_apps/email-processor-logic-app.json` | **Rachit Patekar** | Azure Logic App template for automated email processing workflow |
| `logic_apps/file-processor-logic-app.json` | **Rachit Patekar** | Azure Logic App template for file processing and integration |
| `logic_apps/AUTHORS.md` | **Project Team** | Author attribution for Logic Apps JSON files |

### 📖 Documentation

| File | Author | Purpose |
|------|--------|---------|
| `README.md` | **Utsav Pat** | Main project documentation with setup instructions and features |
| `Copilot-Rules.md` | **Utsav Pat** | GitHub Copilot coding rules and conventions for the project |
| `.github/copilot-instructions.md` | **Utsav Pat** | Workspace-specific Copilot instructions and project context |

---

## 🎯 Responsibility Areas by Author

### 👨‍💻 Rachit Patekar
**Focus**: Email Processing & AI Classification
- Email inbox monitoring and processing
- Azure Logic Apps integration  
- AI document classification using GPT models
- System configuration management
- Git repository management

### 👨‍💻 Shrvan Hatte  
**Focus**: File Processing & OCR
- Direct file upload and processing
- OCR text extraction from documents
- Docker containerization and deployment
- Shared utilities and helper functions
- Environment configuration templates

### 👨‍💻 Utsav Pat
**Focus**: Ingestion Engine & Database
- Core data ingestion and coordination
- Database modeling and management
- Web UI and dashboard development  
- Project documentation and guidelines
- Copilot integration and instructions

---

## 📋 Task Alignment

This attribution aligns with the original task distribution:

| Task Category | Primary Author | Files |
|---------------|----------------|-------|
| Email Processing | Rachit Patekar | email_listener.py, email_handler.py |
| File Processing | Shrvan Hatte | file_listener.py, file_handler.py |
| Ingestion Engine | Utsav Pat | ingestion_processor.py |
| OCR Processing | Shrvan Hatte | ocr_processor.py |
| AI Classification | Rachit Patekar | document_classifier.py |

Additional files have been distributed equally among the three authors to maintain balanced workload and clear ownership.

---

*Last Updated: August 24, 2025*
