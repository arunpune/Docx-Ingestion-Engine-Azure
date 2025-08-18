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

## Features

- **Email Processing**: Automated email monitoring and attachment extraction
- **File Ingestion**: Direct file upload processing via API endpoints
- **OCR Engine**: Text extraction from various document formats (PDF, images, Word documents)
- **AI Document Classification**: Intelligent document type classification using OpenAI GPT
- **Azure Integration**: Built for Azure cloud services (Logic Apps, Blob Storage, Service Bus, Databricks)

## Architecture

### Components

1. **Email Processor** (`src/email_processor/`)
   - Receives emails via Azure Logic Apps
   - Extracts metadata and attachments
   - Stores files in Azure Blob Storage
   - Creates transactional records in database

2. **File Ingestion** (`src/file_ingestion/`)
   - Handles direct file uploads (Google Forms integration)
   - Processes various file formats
   - Validates and stores files securely

3. **Ingestion Engine** (`src/ingestion_engine/`)
   - Coordinates processing workflow
   - Manages database transactions
   - Routes files to OCR processing

4. **OCR Engine** (`src/ocr_engine/`)
   - Extracts text from documents using multiple methods
   - Supports PDF, images, Word documents
   - Uses Azure Form Recognizer and Tesseract OCR

5. **Document Classifier** (`src/ocr_engine/document_classifier.py`)
   - AI-powered document classification
   - Extracts key entities and metadata
   - Risk assessment and priority scoring

### Azure Services Used

- **Azure Logic Apps**: Email monitoring and file processing workflows
- **Azure Blob Storage**: Document storage with private access URLs
- **Azure Service Bus**: Message queuing between components
- **Azure Form Recognizer**: Advanced OCR capabilities
- **Databricks**: Data processing and analytics platform

## Installation

### Prerequisites

- Python 3.9+
- Azure subscription
- OpenAI API access

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Insurace-AI-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure and OpenAI credentials
   ```

4. **Initialize the database**
   ```bash
   python -c "from src.shared.models import create_tables; create_tables()"
   ```

### Configuration

Edit the `.env` file with your specific configuration:

```env
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
AZURE_BLOB_CONTAINER_NAME=insurance-documents

# Databricks
DATABRICKS_SERVER_HOSTNAME=your_databricks_hostname
DATABRICKS_ACCESS_TOKEN=your_databricks_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Service Bus
SERVICE_BUS_CONNECTION_STRING=your_service_bus_connection_string
```

## Usage

### Running the System

1. **Start the main application**
   ```bash
   python main.py
   ```

2. **Access the APIs**
   - Main API: `http://localhost:8000`
   - Email Processor: `http://localhost:8000/email`
   - File Ingestion: `http://localhost:8000/files`
   - Health Check: `http://localhost:8000/health`

### API Endpoints

#### Email Processing
- `POST /email/process-email` - Process uploaded email file
- `POST /email/process-email-url` - Process email from URL

#### File Ingestion
- `POST /files/upload-file` - Upload single file
- `POST /files/upload-files` - Upload multiple files
- `GET /files/supported-formats` - Get supported file formats

#### System Status
- `GET /health` - Health check
- `GET /status` - Detailed system status and metrics

### Azure Logic Apps

Deploy the Logic Apps templates:

1. **Email Processor Logic App**
   ```bash
   az deployment group create \
     --resource-group your-rg \
     --template-file logic_apps/email-processor-logic-app.json \
     --parameters emailProcessorEndpoint="https://your-api-endpoint.com/email"
   ```

2. **File Processor Logic App**
   ```bash
   az deployment group create \
     --resource-group your-rg \
     --template-file logic_apps/file-processor-logic-app.json \
     --parameters fileProcessorEndpoint="https://your-api-endpoint.com/files"
   ```

## Document Processing Workflow

1. **Email Reception**
   - Azure Logic App monitors email inbox
   - Extracts email metadata and attachments
   - Stores files in Blob Storage
   - Sends processing request to Ingestion Engine

2. **File Processing**
   - Ingestion Engine creates database records
   - Routes files to OCR Engine via Service Bus
   - Tracks processing status

3. **Text Extraction**
   - OCR Engine downloads files from Blob Storage
   - Extracts text using appropriate method (PyPDF2, Tesseract, Azure Form Recognizer)
   - Stores results in database

4. **AI Classification**
   - Document Classifier analyzes extracted text
   - Classifies document type (claim, policy, medical report, etc.)
   - Extracts entities and assesses risk
   - Updates database with classification results

## Supported Document Types

- **Claim Forms**: Insurance claim applications and forms
- **Policy Documents**: Insurance policies and contracts
- **Medical Reports**: Medical records and doctor's notes
- **Accident Reports**: Incident and accident documentation
- **Financial Documents**: Invoices, receipts, financial statements
- **Legal Documents**: Court papers and legal notices
- **Correspondence**: Letters and email communications
- **Identification**: ID documents and licenses
- **Photo Evidence**: Damage photos and evidence images

## Database Schema

### Processing Records (Master Table)
- `unique_processing_id`: Unique identifier for each processing job
- `source_type`: Email or file upload
- `status`: pending, processing, completed, failed
- Email-specific fields: from, to, cc, subject, body, date
- File-specific fields: filename, file_uri, file_size

### Attachment Records (Child Table)
- Links to processing records
- Attachment metadata: filename, URI, size, MIME type

### OCR Results
- Extracted text and confidence scores
- Processing time and page count
- Links to source files

### Document Classifications
- AI classification results
- Document type and confidence
- Extracted entities (JSON)
- Risk assessment and priority

## Security Considerations

- All blob storage URLs use SAS tokens with limited time access
- API endpoints should be secured with authentication in production
- Environment variables contain sensitive credentials
- Database connections should use encrypted connections

## Monitoring and Logging

- Comprehensive logging throughout the system
- Health check endpoints for monitoring
- Processing status tracking in database
- Error handling and retry mechanisms

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Deployment

### Azure Container Instances
1. Build Docker image
2. Push to Azure Container Registry
3. Deploy with environment variables

### Azure App Service
1. Deploy Python application
2. Configure environment variables
3. Set up monitoring and scaling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
