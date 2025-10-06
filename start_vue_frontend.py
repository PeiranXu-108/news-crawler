#!/usr/bin/env python3
"""
启动Vue版本的前端应用
"""

import subprocess
import sys
import os
import time
import signal
import threading

def run_command(cmd, cwd=None):
    """运行命令并返回进程"""
    return subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=None if os.name == 'nt' else os.setsid
    )

def main():
    print("🚀 启动Vue版本的前端应用...")
    
    # 检查是否在正确的目录
    if not os.path.exists('frontend/package.json'):
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查Node.js是否安装
    try:
        subprocess.run(['node', '--version'], check=True, capture_output=True)
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: 请先安装Node.js和npm")
        sys.exit(1)
    
    # 进入frontend目录
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    
    # 检查依赖是否安装
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("📦 安装依赖...")
        install_process = run_command('npm install', cwd=frontend_dir)
        install_process.wait()
        if install_process.returncode != 0:
            print("❌ 依赖安装失败")
            sys.exit(1)
        print("✅ 依赖安装完成")
    
    # 启动Vue开发服务器
    print("🌐 启动Vue开发服务器...")
    vue_process = run_command('npm run dev', cwd=frontend_dir)
    
    # 等待Vue服务器启动
    time.sleep(3)
    
    # 启动Electron
    print("🖥️  启动Electron应用...")
    electron_process = run_command('npm run electron', cwd=frontend_dir)
    
    def cleanup():
        print("\n🛑 正在关闭应用...")
        try:
            if os.name == 'nt':
                vue_process.terminate()
                electron_process.terminate()
            else:
                os.killpg(os.getpgid(vue_process.pid), signal.SIGTERM)
                os.killpg(os.getpgid(electron_process.pid), signal.SIGTERM)
        except:
            pass
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())
    
    try:
        print("✅ 应用已启动!")
        print("📱 如果Electron窗口没有自动打开，请手动访问: http://localhost:5173")
        print("⏹️  按 Ctrl+C 停止应用")
        
        # 等待进程结束
        while True:
            if vue_process.poll() is not None:
                print("❌ Vue开发服务器已停止")
                break
            if electron_process.poll() is not None:
                print("❌ Electron应用已停止")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        cleanup()
    
    print("👋 应用已关闭")

if __name__ == '__main__':
    main()
