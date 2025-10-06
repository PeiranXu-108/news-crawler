#!/usr/bin/env python3
"""
Start script for the News Crawler backend service.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Get backend directory
    backend_dir = Path(__file__).parent / "backend"
    
    # Install dependencies if needed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing backend dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_dir)
    
    # Start the backend service
    print("Starting News Crawler backend service...")
    print("API will be available at: http://localhost:8000")
    print("WebSocket will be available at: ws://localhost:8000/ws")
    print("Press Ctrl+C to stop the service")
    
    # Start the full backend service
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ], cwd=backend_dir)

if __name__ == "__main__":
    main()
