"""
Azure Storage Access Configuration Guide
========================================

This guide helps you configure your Azure Storage Account to allow public blob access
so that the Insurance AI Agent can store and retrieve email attachments.

OPTION 1: Enable Public Access (Easiest)
----------------------------------------

Step 1: Enable Blob Public Access on Storage Account
1. Go to Azure Portal (https://portal.azure.com)
2. Navigate to your Storage Account
3. In the left menu, click "Configuration" under Settings
4. Find "Allow Blob public access" 
5. Change it from "Disabled" to "Enabled"
6. Click "Save" at the top

Step 2: Set Container Access Level
1. Go to "Containers" in the left menu of your Storage Account
2. Click on your "insurance-emails" container
3. Click "Change access level" button at the top
4. Select "Blob (anonymous read access for blobs only)"
5. Click "OK"

OPTION 2: Keep Private Access (More Secure)
-------------------------------------------

If you prefer to keep your storage private (recommended for sensitive data):

1. Keep "Allow Blob public access" as "Disabled"
2. Keep container access level as "Private"
3. The application will provide you with:
   - Direct blob URLs (will show permission error but you can copy the path)
   - Azure Portal links to access files through the web interface

How to Access Your Files:
------------------------

After processing emails, you'll get:

1. DIRECT URL: 
   https://yourstorageaccount.blob.core.windows.net/insurance-emails/email_20240818_123456/
   
   - If public access is ENABLED: You can click this link directly
   - If public access is DISABLED: Copy the path and access via Azure Portal

2. AZURE PORTAL ACCESS:
   - Go to Azure Portal
   - Navigate to your Storage Account
   - Click "Storage Explorer" in the left menu
   - Navigate to Containers > insurance-emails
   - Find your email folder by timestamp

Folder Structure Created:
------------------------

For each processed email, this structure is created:

insurance-emails/
├── email_20240818_123456_123/
│   ├── original_email.eml       (Raw email file)
│   ├── metadata.json           (Email info: subject, from, date, etc.)
│   ├── attachments/
│   │   ├── document1.pdf
│   │   └── image1.jpg
│   └── ocr/
│       └── document1.pdf_text.txt (Extracted text from PDF)

Troubleshooting:
---------------

Error: "PublicAccessNotPermitted"
→ Enable public access (Option 1) or use Azure Portal to view files

Error: "BlobNotFound" 
→ Check if container "insurance-emails" exists
→ Verify storage account name and key are correct

Error: "AuthenticationFailed"
→ Verify storage account key is correct
→ Check connection string format

Security Recommendations:
------------------------

1. For Production: Keep storage private and use SAS tokens
2. For Testing: Public access is fine for non-sensitive data
3. Always use HTTPS URLs
4. Regularly rotate storage account keys
5. Set up access logging to monitor blob access

Need Help?
----------
If you're still having issues:
1. Check Azure Portal > Storage Account > Monitoring > Insights
2. Look at the Activity Log for any error messages
3. Verify your subscription has sufficient credits/quota
"""

def show_current_config():
    """Show current Azure configuration."""
    from ui_app import azure_config
    
    print("Current Azure Configuration:")
    print("=" * 30)
    for key, value in azure_config.items():
        if 'key' in key.lower():
            print(f"{key}: {'*' * 10}")  # Hide sensitive keys
        else:
            print(f"{key}: {value}")

def test_blob_access():
    """Test blob storage access."""
    try:
        from ui_app import azure_config
        from azure.storage.blob import BlobServiceClient
        
        if not azure_config.get("connection_string"):
            print("❌ Azure not configured yet. Please set up Azure first in the web UI.")
            return
            
        print("🔍 Testing Azure Blob Storage access...")
        
        blob_service_client = BlobServiceClient.from_connection_string(azure_config["connection_string"])
        
        # Test 1: List containers
        print("Step 1: Listing containers...")
        containers = list(blob_service_client.list_containers())
        print(f"✅ Found {len(containers)} containers")
        
        # Test 2: Check specific container
        container_name = azure_config.get("container_name", "insurance-emails")
        print(f"Step 2: Checking container '{container_name}'...")
        
        container_client = blob_service_client.get_container_client(container_name)
        
        try:
            props = container_client.get_container_properties()
            print(f"✅ Container exists. Public access: {props.public_access}")
        except Exception as e:
            print(f"❌ Container check failed: {e}")
            
        # Test 3: List blobs
        print("Step 3: Listing blobs in container...")
        blobs = list(container_client.list_blobs())
        print(f"✅ Found {len(blobs)} blobs in container")
        
        print("\n🎉 Azure Storage is working correctly!")
        
    except Exception as e:
        print(f"❌ Azure Storage test failed: {e}")
        print("💡 Make sure to configure Azure in the web UI first")

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*50)
    print("QUICK ACTIONS:")
    print("="*50)
    
    choice = input("\nWhat would you like to do?\n1. Show current config\n2. Test blob access\n3. Exit\n\nChoice (1-3): ")
    
    if choice == "1":
        show_current_config()
    elif choice == "2":
        test_blob_access()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
