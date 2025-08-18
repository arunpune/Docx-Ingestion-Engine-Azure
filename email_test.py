"""
Email Connection Test Script
This will help diagnose email connection issues step by step.
"""
import imaplib
import ssl
import getpass

def test_email_connection():
    print("🔍 Email Connection Troubleshooter")
    print("=" * 50)
    
    # Get email settings
    print("\n📧 Enter your email settings:")
    host = input("IMAP Host (e.g., imap.gmail.com): ").strip()
    if not host:
        host = "imap.gmail.com"
    
    port_input = input("Port (default 993): ").strip()
    port = int(port_input) if port_input else 993
    
    username = input("Email address: ").strip()
    password = getpass.getpass("Password/App Password: ")
    
    print(f"\n🔗 Testing connection to {host}:{port}...")
    
    try:
        # Test 1: Basic connection
        print("Step 1: Testing basic connection...")
        mail = imaplib.IMAP4_SSL(host, port)
        print("✅ SSL connection established")
        
        # Test 2: Authentication
        print("Step 2: Testing authentication...")
        result = mail.login(username, password)
        print(f"✅ Authentication successful: {result}")
        
        # Test 3: List folders
        print("Step 3: Testing folder access...")
        folders = mail.list()
        print(f"✅ Found {len(folders[1])} folders")
        
        # Test 4: Select INBOX
        print("Step 4: Testing INBOX access...")
        status, messages = mail.select('INBOX')
        total_emails = int(messages[0]) if messages[0] else 0
        print(f"✅ INBOX selected, {total_emails} total emails")
        
        # Test 5: Check for unread emails
        print("Step 5: Checking unread emails...")
        status, unread = mail.search(None, 'UNSEEN')
        unread_count = len(unread[0].split()) if unread[0] else 0
        print(f"✅ Found {unread_count} unread emails")
        
        mail.logout()
        
        print("\n🎉 All tests passed! Your email connection is working!")
        print("\nYou can now use these settings in the UI:")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Username: {username}")
        print("Password: [Use the same password you just entered]")
        
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"\n❌ IMAP Error: {e}")
        print("\nTroubleshooting suggestions:")
        print("1. Check if IMAP is enabled in your email settings")
        print("2. For Gmail: Use App Password, not regular password")
        print("3. For Outlook: Enable 'Less secure app access'")
        return False
        
    except ssl.SSLError as e:
        print(f"\n❌ SSL Error: {e}")
        print("\nTrying non-SSL connection...")
        try:
            mail = imaplib.IMAP4(host, 143)  # Try non-SSL port
            mail.starttls()  # Upgrade to TLS
            mail.login(username, password)
            print("✅ Non-SSL connection with STARTTLS worked!")
            mail.logout()
            return True
        except Exception as e2:
            print(f"❌ Non-SSL also failed: {e2}")
            return False
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nCommon solutions:")
        print("1. Check your internet connection")
        print("2. Verify host and port settings")
        print("3. Check if firewall is blocking the connection")
        return False

def show_common_settings():
    print("\n📋 Common Email Provider Settings:")
    print("=" * 40)
    print("Gmail:")
    print("  Host: imap.gmail.com")
    print("  Port: 993")
    print("  Security: SSL/TLS")
    print("  Note: Use App Password, not regular password")
    print("")
    print("Outlook/Hotmail:")
    print("  Host: outlook.office365.com")
    print("  Port: 993")
    print("  Security: SSL/TLS")
    print("")
    print("Yahoo:")
    print("  Host: imap.mail.yahoo.com")
    print("  Port: 993")
    print("  Security: SSL/TLS")
    print("  Note: Use App Password")
    print("")

def gmail_app_password_guide():
    print("\n🔑 Gmail App Password Setup Guide:")
    print("=" * 40)
    print("1. Go to https://myaccount.google.com")
    print("2. Click 'Security' in the left menu")
    print("3. Under 'Signing in to Google', click '2-Step Verification'")
    print("4. If not enabled, enable 2-Step Verification first")
    print("5. Go back to Security, click 'App passwords'")
    print("6. Select 'Mail' and 'Other (Custom name)'")
    print("7. Enter 'Insurance AI Agent' as the name")
    print("8. Click 'Generate'")
    print("9. Use the 16-character password (without spaces)")
    print("10. Use this password in the UI, not your regular Gmail password")

if __name__ == "__main__":
    print("🏢 Insurance AI Agent - Email Troubleshooter")
    print("=" * 50)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Test email connection")
        print("2. Show common email settings")
        print("3. Gmail App Password guide")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            test_email_connection()
        elif choice == "2":
            show_common_settings()
        elif choice == "3":
            gmail_app_password_guide()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")
        print("\n" + "=" * 50)
