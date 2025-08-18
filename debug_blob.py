"""
Debug script to test blob storage operations
"""
import os
import json
from datetime import datetime

def test_blob_operations():
    print("🔍 Testing Blob Storage Operations")
    print("=" * 50)
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        # Get connection string from environment or config
        connection_string = input("Enter Azure Storage connection string: ").strip()
        if not connection_string:
            print("❌ No connection string provided")
            return
        
        container_name = "insurance-emails"
        
        # Test 1: Create blob client
        print("Step 1: Creating blob service client...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        print("✅ Blob service client created")
        
        # Test 2: Check container exists
        print("Step 2: Checking container exists...")
        try:
            container_client = blob_service_client.get_container_client(container_name)
            properties = container_client.get_container_properties()
            print(f"✅ Container '{container_name}' exists")
        except Exception as e:
            print(f"⚠️ Container issue: {e}")
            print("Creating container...")
            container_client = blob_service_client.create_container(container_name)
            print(f"✅ Container '{container_name}' created")
        
        # Test 3: Upload a test file
        print("Step 3: Testing file upload...")
        test_data = f"Test file created at {datetime.now()}"
        test_blob_name = f"test_folder/test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=test_blob_name
        )
        
        upload_result = blob_client.upload_blob(test_data, overwrite=True)
        print(f"✅ Test file uploaded: {test_blob_name}")
        print(f"Upload result: {upload_result}")
        
        # Test 4: List blobs
        print("Step 4: Listing blobs...")
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = list(container_client.list_blobs(name_starts_with="test_folder/"))
        print(f"✅ Found {len(blob_list)} blobs in test_folder/")
        
        for blob in blob_list:
            print(f"  - {blob.name} ({blob.size} bytes)")
        
        # Test 5: Generate SAS URL
        print("Step 5: Testing SAS URL generation...")
        try:
            from azure.storage.blob import generate_container_sas, ContainerSasPermissions
            from datetime import timedelta
            import re
            
            # Extract account name and key
            account_name_match = re.search(r'AccountName=([^;]+)', connection_string)
            account_key_match = re.search(r'AccountKey=([^;]+)', connection_string)
            
            if account_name_match and account_key_match:
                account_name = account_name_match.group(1)
                account_key = account_key_match.group(1)
                
                sas_token = generate_container_sas(
                    account_name=account_name,
                    container_name=container_name,
                    account_key=account_key,
                    permission=ContainerSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )
                
                folder_url = f"https://{account_name}.blob.core.windows.net/{container_name}?restype=container&comp=list&prefix=test_folder/&{sas_token}"
                print(f"✅ SAS URL generated successfully")
                print(f"URL: {folder_url}")
                
            else:
                print("⚠️ Could not extract account details for SAS token")
                
        except Exception as e:
            print(f"❌ SAS URL generation failed: {e}")
        
        # Test 6: Download test file
        print("Step 6: Testing file download...")
        try:
            download_stream = blob_client.download_blob()
            downloaded_data = download_stream.readall().decode('utf-8')
            print(f"✅ Downloaded file content: {downloaded_data[:50]}...")
        except Exception as e:
            print(f"❌ Download failed: {e}")
        
        print("\n🎉 All blob storage tests completed!")
        
    except Exception as e:
        print(f"❌ Blob storage test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blob_operations()
