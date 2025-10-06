#!/usr/bin/env python3
"""
Test script to verify News Crawler setup
"""

import sys
import asyncio
import requests
import time
from pathlib import Path

def test_backend_dependencies():
    """Test if backend dependencies are installed."""
    print("🔍 Testing backend dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import httpx
        import feedparser
        import trafilatura
        import pandas
        print("✓ All backend dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def test_frontend_dependencies():
    """Test if frontend dependencies are installed."""
    print("🔍 Testing frontend dependencies...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if node_modules.exists():
        print("✓ Frontend dependencies are installed")
        return True
    else:
        print("❌ Frontend dependencies not found. Run: cd frontend && npm install")
        return False

def test_backend_startup():
    """Test if backend can start up."""
    print("🔍 Testing backend startup...")
    
    try:
        # Import backend modules
        sys.path.append(str(Path(__file__).parent / "backend"))
        from database import init_database
        from main import app
        
        # Initialize database
        init_database()
        print("✓ Backend modules can be imported and database initialized")
        return True
    except Exception as e:
        print(f"❌ Backend startup failed: {e}")
        return False

def test_api_connection():
    """Test if API is accessible."""
    print("🔍 Testing API connection...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is accessible")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Start it with: python start_backend.py")
        return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_websocket_connection():
    """Test if WebSocket is accessible."""
    print("🔍 Testing WebSocket connection...")
    
    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8000/ws", timeout=5)
        ws.close()
        print("✓ WebSocket is accessible")
        return True
    except ImportError:
        print("⚠️  WebSocket library not installed, skipping test")
        return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    print("🔍 Testing database operations...")
    
    try:
        sys.path.append(str(Path(__file__).parent / "backend"))
        from database import get_db, CrawlTask, Article, RSSSource
        from sqlalchemy.orm import Session
        
        # Get database session
        db = next(get_db())
        
        # Test basic queries
        task_count = db.query(CrawlTask).count()
        article_count = db.query(Article).count()
        source_count = db.query(RSSSource).count()
        
        print(f"✓ Database operations working (Tasks: {task_count}, Articles: {article_count}, Sources: {source_count})")
        return True
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def main():
    print("🧪 News Crawler Setup Test")
    print("=" * 40)
    
    tests = [
        ("Backend Dependencies", test_backend_dependencies),
        ("Frontend Dependencies", test_frontend_dependencies),
        ("Backend Startup", test_backend_startup),
        ("Database Operations", test_database_operations),
        ("API Connection", test_api_connection),
        ("WebSocket Connection", test_websocket_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n🚀 You can now run the application with:")
        print("   python start_all.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\n💡 Common solutions:")
        print("   - Install dependencies: python install.py")
        print("   - Start backend: python start_backend.py")
        print("   - Check error messages above")

if __name__ == "__main__":
    main()
