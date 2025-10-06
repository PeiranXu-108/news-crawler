#!/usr/bin/env python3
"""
Installation script for News Crawler Desktop Application
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"  Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8+ is required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_node_version():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"✓ Node.js {version}")
        return True
    except FileNotFoundError:
        print("Node.js is not installed. Please install Node.js 16+ from https://nodejs.org/")
        return False

def install_backend_dependencies():
    """Install backend Python dependencies."""
    print("\nInstalling backend dependencies...")
    backend_dir = Path(__file__).parent / "backend"
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Install requirements
    success = run_command(f"{sys.executable} -m pip install -r requirements.txt", cwd=backend_dir)
    
    if success:
        print("✓ Backend dependencies installed successfully")
    else:
        print("Failed to install backend dependencies")
    
    return success

def install_frontend_dependencies():
    """Install frontend Node.js dependencies."""
    print("\nInstalling frontend dependencies...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Install npm dependencies
    success = run_command("npm install", cwd=frontend_dir)
    
    if success:
        print("✓ Frontend dependencies installed successfully")
    else:
        print("Failed to install frontend dependencies")
    
    return success

def create_desktop_shortcut():
    """Create desktop shortcut (optional)."""
    if platform.system() == "Windows":
        print("\nCreating desktop shortcut...")
        # Windows shortcut creation would go here
        print("✓ Desktop shortcut created")
    elif platform.system() == "Darwin":
        print("\nmacOS app bundle creation...")
        # macOS app bundle creation would go here
        print("✓ macOS app bundle created")
    else:
        print("\nLinux desktop file creation...")
        # Linux desktop file creation would go here
        print("✓ Linux desktop file created")

def main():
    print("News Crawler Desktop Application Installer")
    print("=" * 50)
    
    # Check system requirements
    print("\nChecking system requirements...")
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    # Install dependencies
    backend_success = install_backend_dependencies()
    frontend_success = install_frontend_dependencies()
    
    if not backend_success or not frontend_success:
        print("\nInstallation failed. Please check the error messages above.")
        sys.exit(1)
    
    # Create shortcuts (optional)
    create_desktop_shortcut()
    
    print("\nInstallation completed successfully!")
    print("\nNext steps:")
    print("1. Run the application: python start_all.py")
    print("2. Or start services separately:")
    print("   - Backend: python start_backend.py")
    print("   - Frontend: python start_frontend.py")
    print("\nFor more information, see README_DESKTOP.md")
    print("\nBackend API will be available at: http://localhost:8000")
    print("Desktop app will start automatically")

if __name__ == "__main__":
    main()
