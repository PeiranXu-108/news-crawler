#!/usr/bin/env python3
"""
Start script for the News Crawler frontend desktop application.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Get frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Install dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir)
    
    # Start the Electron app
    print("Starting News Crawler desktop application...")
    print("Make sure the backend service is running on http://localhost:8000")
    
    subprocess.run(["npm", "start"], cwd=frontend_dir)

if __name__ == "__main__":
    main()
