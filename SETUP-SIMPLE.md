# Insurance AI Agent - Simplified Setup

This is the **simplified version** where Azure credentials are pre-configured and dependencies are auto-installed. Users only need to provide their email credentials.

## Quick Start

1. **Run the application:**
   ```bash
   # Windows Command Prompt
   start_ui.bat
   
   # OR PowerShell
   .\start_ui.ps1
   ```

2. **Open your browser** to: http://localhost:8000

3. **Enter your email credentials:**
   - Email address (Gmail, Outlook, Yahoo, etc.)
   - App password (not your regular password)

4. **Click "Connect & Process Emails"** - that's it!

## What happens automatically:

✅ **Dependencies**: Auto-installed from requirements.txt  
✅ **Azure Services**: Pre-configured (CosmosDB, Service Bus, Storage)  
✅ **Email Provider**: Auto-detected based on your email address  
✅ **Processing**: Starts immediately after email connection  

## Supported Email Providers

- **Gmail**: Requires app password ([Setup Guide](https://support.google.com/accounts/answer/185833))
- **Outlook/Hotmail**: Requires app password ([Setup Guide](https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944))
- **Yahoo**: Requires app password
- **Other IMAP providers**: Should work with standard IMAP settings

## Azure Configuration

The following Azure services are pre-configured in `.env`:

- **CosmosDB**: `insuranceapp123.documents.azure.com`
- **Service Bus**: Email processing queue
- **Storage Account**: `insuranceapp123` blob storage
- **AI Services**: OCR and document processing

## Files Structure

- `ui_app.py`: Main FastAPI application (simplified version)
- `simple_ui.py`: Alternative minimal interface
- `templates/simple_dashboard.html`: Clean, single-form interface
- `.env`: Pre-configured Azure credentials
- `requirements.txt`: All necessary dependencies

## Troubleshooting

**Email connection fails?**
- Ensure you're using an app password, not your regular password
- Check that IMAP is enabled in your email account settings

**Azure services fail?**
- Check `.env` file for correct Azure credentials
- Verify Azure services are running and accessible

**Dependencies missing?**
- Run: `pip install -r requirements.txt`
- Check that you're in the virtual environment

## Technical Details

The system processes emails by:
1. Connecting to your email via IMAP
2. Downloading unread emails with attachments
3. Uploading to Azure Blob Storage
4. Processing through Azure AI services (OCR, classification)
5. Storing metadata in CosmosDB
6. Coordinating via Service Bus messages

All of this happens automatically after you provide your email credentials!
