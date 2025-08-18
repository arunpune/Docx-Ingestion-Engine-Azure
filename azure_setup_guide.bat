@echo off
echo ===========================================
echo   Insurance AI Agent - Azure Setup Guide
echo ===========================================
echo.

echo Step 1: Azure Portal Method (Recommended)
echo ==========================================
echo 1. Go to https://portal.azure.com
echo 2. Click "Create a resource"
echo 3. Search for "Storage account" and click Create
echo 4. Fill in:
echo    - Storage account name: insuranceai%RANDOM%
echo    - Resource group: Create new "insurance-ai-rg"
echo    - Region: Choose closest to you
echo    - Performance: Standard
echo    - Redundancy: LRS
echo 5. Click "Review + Create" then "Create"
echo.
echo 6. After creation, go to your storage account
echo 7. Click "Containers" in the left menu
echo 8. Click "+ Container"
echo 9. Name: insurance-emails
echo 10. Public access level: Private
echo 11. Click "Create"
echo.
echo 12. Go to "Access keys" in left menu
echo 13. Click "Show keys"
echo 14. Copy the "Connection string" from Key1
echo.

echo Step 2: What you need to copy
echo ==============================
echo You need these values for the UI:
echo - Storage Account Name: (from step 4)
echo - Storage Key: (from Access keys - Key1)
echo - Container Name: insurance-emails
echo.

echo Step 3: Alternative - Use Azure CLI
echo ===================================
echo If you have Azure CLI installed:
echo 1. Run: az login
echo 2. Run: powershell -ExecutionPolicy Bypass -File create_azure_resources.ps1
echo.

echo ===========================================
echo   After creating Azure resources:
echo ===========================================
echo 1. Open the Insurance AI Agent web UI
echo 2. Go to Azure Setup section
echo 3. Enter your Storage Account Name and Key
echo 4. Click "Setup Azure Storage"
echo.

pause
