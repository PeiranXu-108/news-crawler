#!/usr/bin/env python3
"""
启动桌面版新闻爬虫应用
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser

def start_backend():
    """启动后端服务"""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ], cwd=backend_dir)

def start_vue_dev():
    """启动Vue开发服务器"""
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)

def main():
    print("🚀 启动新闻爬虫桌面应用")
    print("=" * 50)
    
    # 启动后端
    print("📡 启动后端服务...")
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # 等待后端启动
    time.sleep(3)
    
    # 启动Vue开发服务器
    print("🌐 启动Vue开发服务器...")
    vue_thread = threading.Thread(target=start_vue_dev, daemon=True)
    vue_thread.start()
    
    # 等待Vue服务器启动
    time.sleep(5)
    
    print("✅ 服务启动完成!")
    print("📱 应用地址: http://localhost:5173")
    print("🔧 API地址: http://localhost:8000")
    print("⏹️  按 Ctrl+C 停止应用")
    
    # 自动打开浏览器
    try:
        webbrowser.open('http://localhost:5173')
        print("🌐 已在浏览器中打开应用")
    except:
        print("⚠️  请手动打开浏览器访问: http://localhost:5173")
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在关闭应用...")
        sys.exit(0)

if __name__ == '__main__':
    main()
