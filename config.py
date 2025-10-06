"""
Configuration settings for News Crawler Desktop Application
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUT_DIR = BASE_DIR / "output"

# Database settings
DATABASE_URL = "sqlite:///./news_crawler.db"
DATABASE_PATH = BACKEND_DIR / "news_crawler.db"

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_BASE_URL = f"http://localhost:{API_PORT}"

# WebSocket settings
WS_URL = f"ws://localhost:{API_PORT}/ws"

# Crawler settings
DEFAULT_LIMIT = 50
MAX_LIMIT = 1000
REQUEST_DELAY = 1.0  # seconds between requests
REQUEST_TIMEOUT = 30.0  # seconds

# Summary settings
SUMMARY_STRATEGIES = [
    "rss_first",
    "ai_generated", 
    "hybrid",
    "simple"
]

DEFAULT_SUMMARY_STRATEGY = "rss_first"
SUMMARY_CACHE_DURATION_HOURS = 24

# Frontend settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"

# Development settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
RELOAD = DEBUG

# Default RSS sources
DEFAULT_RSS_SOURCES = [
    {
        "name": "Bing News",
        "url_template": "https://www.bing.com/news/search?q={query}&format=rss",
        "supports_query": True,
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Google News", 
        "url_template": "https://news.google.com/rss/search?q={query}",
        "supports_query": True,
        "priority": 2,
        "is_active": True
    },
    {
        "name": "Wall Street Journal",
        "url_template": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "supports_query": False,
        "priority": 3,
        "is_active": True
    },
    {
        "name": "Reuters",
        "url_template": "https://www.reuters.com/markets/rss",
        "supports_query": False,
        "priority": 4,
        "is_active": True
    },
    {
        "name": "Nasdaq",
        "url_template": "https://www.nasdaq.com/feed/rssoutbound?category=markets",
        "supports_query": False,
        "priority": 5,
        "is_active": True
    }
]

# Export settings
SUPPORTED_EXPORT_FORMATS = ["json", "csv", "jsonl"]
DEFAULT_EXPORT_FORMAT = "json"

# UI settings
THEME_COLORS = {
    "primary": "#1976d2",
    "secondary": "#6c757d", 
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8"
}

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_BURST = 10

# File paths
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "news_crawler.log"

# Create necessary directories
OUTPUT_DIR.mkdir(exist_ok=True)
(BASE_DIR / "logs").mkdir(exist_ok=True)

def get_config():
    """Get configuration as dictionary."""
    return {
        "database_url": DATABASE_URL,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "api_base_url": API_BASE_URL,
        "ws_url": WS_URL,
        "default_limit": DEFAULT_LIMIT,
        "max_limit": MAX_LIMIT,
        "request_delay": REQUEST_DELAY,
        "request_timeout": REQUEST_TIMEOUT,
        "summary_strategies": SUMMARY_STRATEGIES,
        "default_summary_strategy": DEFAULT_SUMMARY_STRATEGY,
        "summary_cache_duration_hours": SUMMARY_CACHE_DURATION_HOURS,
        "window_width": WINDOW_WIDTH,
        "window_height": WINDOW_HEIGHT,
        "min_window_width": MIN_WINDOW_WIDTH,
        "min_window_height": MIN_WINDOW_HEIGHT,
        "log_level": LOG_LEVEL,
        "debug": DEBUG,
        "reload": RELOAD,
        "default_rss_sources": DEFAULT_RSS_SOURCES,
        "supported_export_formats": SUPPORTED_EXPORT_FORMATS,
        "default_export_format": DEFAULT_EXPORT_FORMAT,
        "theme_colors": THEME_COLORS,
        "rate_limit_requests_per_minute": RATE_LIMIT_REQUESTS_PER_MINUTE,
        "rate_limit_burst": RATE_LIMIT_BURST
    }

def load_user_config():
    """Load user configuration from file."""
    if CONFIG_FILE.exists():
        import json
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user config: {e}")
            return {}
    return {}

def save_user_config(config):
    """Save user configuration to file."""
    import json
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving user config: {e}")
        return False
