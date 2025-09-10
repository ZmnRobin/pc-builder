"""
Startup script for PC Builder API
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB is running")
        return True
    except Exception as e:
        print(f"❌ MongoDB is not running: {e}")
        print("Please start MongoDB before running the API")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_database():
    """Initialize database"""
    print("🗄️ Initializing database...")
    try:
        from database import initialize_database
        initialize_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def start_api():
    """Start the FastAPI server"""
    print("🚀 Starting PC Builder API...")
    try:
        # Start the API server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down PC Builder API...")
    except Exception as e:
        print(f"❌ Failed to start API: {e}")

def main():
    """Main startup function"""
    print("🖥️ PC Builder API Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found. Please run this script from the project root directory.")
        return
    
    # Check MongoDB
    if not check_mongodb():
        print("\nTo start MongoDB:")
        print("1. Install MongoDB if not already installed")
        print("2. Start MongoDB service:")
        print("   - Windows: net start MongoDB")
        print("   - Linux/Mac: sudo systemctl start mongod")
        print("   - Or run: mongod")
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Initialize database
    if not initialize_database():
        return
    
    print("\n🎉 Setup complete! Starting API server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🌐 API Base URL: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Start the API
    start_api()

if __name__ == "__main__":
    main()
