#!/usr/bin/env python3
"""
Start script to run both backend and frontend services.
支持Vue版本和原版前端
"""

import sys
import os
import subprocess
import threading
import time
import signal
from pathlib import Path

def start_backend():
    """Start the backend service."""
    backend_dir = Path(__file__).parent / "backend"
    
    # Install dependencies if needed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing backend dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_dir)
    
    print("Starting backend service...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ], cwd=backend_dir)

def start_vue_frontend():
    """Start the Vue frontend application."""
    # Wait a bit for backend to start
    time.sleep(3)
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Install dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("Installing Vue frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir)
    
    print("Starting Vue frontend application...")
    # 使用concurrently同时启动Vite和Electron
    subprocess.run(["npm", "run", "electron:dev"], cwd=frontend_dir)

def start_original_frontend():
    """Start the original frontend application."""
    # Wait a bit for backend to start
    time.sleep(3)
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Install dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir)
    
    print("Starting original frontend application...")
    subprocess.run(["npm", "start"], cwd=frontend_dir)

def main():
    print("🚀 启动新闻爬虫桌面应用")
    print("=" * 50)
    
    # 检查前端类型
    frontend_type = "vue"  # 默认使用Vue版本
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--original":
            frontend_type = "original"
        elif sys.argv[1] == "--vue":
            frontend_type = "vue"
        elif sys.argv[1] == "--help":
            print("使用方法:")
            print("  python start_all.py          # 启动Vue版本 (默认)")
            print("  python start_all.py --vue    # 启动Vue版本")
            print("  python start_all.py --original # 启动原版")
            print("  python start_all.py --help   # 显示帮助")
            return
    
    print(f"📱 前端类型: {frontend_type.upper()}")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to initialize
    time.sleep(2)
    
    # Start frontend based on type
    try:
        if frontend_type == "vue":
            start_vue_frontend()
        else:
            start_original_frontend()
    except KeyboardInterrupt:
        print("\n🛑 正在关闭应用...")
        sys.exit(0)

if __name__ == "__main__":
    main()