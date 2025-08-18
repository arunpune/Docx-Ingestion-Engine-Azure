"""
Startup script for the Insurance AI Agent UI Application.
"""
import uvicorn
import sys
import os

def main():
    print("=" * 60)
    print("🏢 Insurance AI Agent - Web UI")
    print("=" * 60)
    print("🚀 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "ui_app:app", 
            host="0.0.0.0", 
            port=8080, 
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
