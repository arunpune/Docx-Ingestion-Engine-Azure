# Insurance AI Agent - Simple Setup

🚀 **One-click email processing with pre-configured Azure services**

## Quick Start

### Windows Users

1. **Double-click** `start_simple.bat` 
2. Enter your **email** and **app password** in the web interface
3. Click **"Start Processing Emails"**

### PowerShell Users

1. Run: `.\start_simple.ps1`
2. Enter your **email** and **app password** in the web interface  
3. Click **"Start Processing Emails"**

### Manual Start

```bash
python simple_ui.py
```

Then open: http://127.0.0.1:8000

## What You Need

### ✅ Pre-configured (Already Done)
- Azure CosmosDB
- Azure Service Bus  
- Azure Storage
- All dependencies auto-install

### 📧 You Only Need
1. **Email address** (Gmail, Outlook, Yahoo, etc.)
2. **App password** (not your regular password)

## Email App Password Setup

### Gmail
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"

### Outlook/Hotmail
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Advanced security options → App passwords
3. Create new app password

### Yahoo
1. Go to Yahoo Account Security
2. Generate app password for "Mail"

## Features

- ✅ **Auto-detects** email provider settings
- ✅ **Auto-installs** all dependencies
- ✅ **Pre-configured** Azure services
- ✅ **Processes** unread emails automatically
- ✅ **Extracts** attachments for OCR
- ✅ **Stores** everything in Azure CosmosDB

## Process Flow

1. **Connect** → Test email connection
2. **Scan** → Find unread emails  
3. **Extract** → Get email content & attachments
4. **Process** → Send to AI processing pipeline
5. **Store** → Save to Azure database

## Troubleshooting

### Email Connection Issues
- Make sure you're using an **app password**, not your regular password
- Enable **IMAP** in your email settings
- For Gmail: Enable "Less secure app access" or use app password

### Dependencies Issues
- Ensure Python 3.8+ is installed
- Run as Administrator if installation fails
- Check internet connection

### Azure Issues
- Verify `.env` file has correct Azure credentials
- Check Azure service status

## Support

For issues:
1. Check the web interface error messages
2. Look at console output for detailed logs
3. Verify email app password is correct
4. Ensure Azure credentials in `.env` are valid

---

🎉 **That's it!** The system handles everything else automatically.
