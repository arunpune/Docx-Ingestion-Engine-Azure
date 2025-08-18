# Insurance AI Agent - Quick Setup Guide

## Step 1: Install Core Dependencies

First, let's install the basic dependencies that are working:

```bash
pip install fastapi uvicorn python-dotenv requests sqlalchemy
```

## Step 2: Create Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with basic settings:

```env
# Basic Configuration
DEBUG=True
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=sqlite:///insurance_ai.db

# Azure Configuration (optional for basic testing)
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_key
AZURE_BLOB_CONTAINER_NAME=insurance-documents

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_key
```

## Step 3: Test Basic Configuration

Run the configuration test:

```bash
python test_basic.py
```

## Step 4: Run Simple API Server

Start the basic API server:

```bash
python simple_server.py
```

The server will be available at: http://localhost:8000

## Step 5: Test API Endpoints

Open your browser or use curl to test:

- Health check: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

## Troubleshooting

If you encounter dependency issues:

1. **Pydantic version conflicts**: We've simplified the configuration to avoid BaseSettings
2. **Missing Azure packages**: These are optional for basic testing
3. **Database issues**: Using SQLite by default for simplicity

## Next Steps

Once basic setup works:

1. Install Azure packages: `pip install azure-storage-blob azure-servicebus`
2. Install OCR packages: `pip install PyPDF2 Pillow pytesseract`
3. Install AI packages: `pip install openai`
4. Configure Azure Logic Apps
5. Set up production database
