"""
Database models and configuration for the news crawler backend.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, field_validator
from pathlib import Path

# Database configuration
DATABASE_URL = "sqlite:///./news_crawler.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class CrawlTask(Base):
    """Crawl task model."""
    __tablename__ = "crawl_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False, index=True)
    since = Column(DateTime, nullable=True)
    limit = Column(Integer, default=50)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    total_articles = Column(Integer, default=0)
    processed_articles = Column(Integer, default=0)
    
    # Relationships
    articles = relationship("Article", back_populates="task", cascade="all, delete-orphan")
    custom_feeds = relationship("CustomFeed", back_populates="task", cascade="all, delete-orphan")


class Article(Base):
    """Article model."""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("crawl_tasks.id"), nullable=False)
    title = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False, unique=True, index=True)
    published = Column(DateTime, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    relevance_score = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("CrawlTask", back_populates="articles")


class CustomFeed(Base):
    """Custom RSS feed model."""
    __tablename__ = "custom_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("crawl_tasks.id"), nullable=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("CrawlTask", back_populates="custom_feeds")


class RSSSource(Base):
    """RSS source configuration model."""
    __tablename__ = "rss_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    url_template = Column(String, nullable=False)
    supports_query = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppConfig(Base):
    """Application configuration model."""
    __tablename__ = "app_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Pydantic models for API
class CrawlTaskCreate(BaseModel):
    query: str
    since: Optional[datetime] = None
    limit: int = 50
    custom_feeds: Optional[List[str]] = None

    @field_validator('since', mode='before')
    @classmethod
    def parse_since(cls, value):
        """Accept ISO datetime strings or simple dates from the UI."""
        if value in (None, ''):
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            try:
                if len(value) == 10:  # Received date only (YYYY-MM-DD)
                    return datetime.fromisoformat(f"{value}T00:00:00")
                return datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(
                    "Invalid datetime format. Use ISO 8601, e.g. 2025-10-07 or 2025-10-07T12:00:00"
                ) from exc

        return value


class CrawlTaskResponse(BaseModel):
    id: int
    query: str
    since: Optional[datetime]
    limit: int
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    progress: int
    total_articles: int
    processed_articles: int
    
    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    id: int
    task_id: int
    title: str
    source: str
    url: str
    published: Optional[datetime]
    summary: Optional[str]
    text: Optional[str]
    tags: Optional[List[str]]
    relevance_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RSSSourceCreate(BaseModel):
    name: str
    url_template: str
    supports_query: bool = False
    is_active: bool = True
    priority: int = 0


class RSSSourceResponse(BaseModel):
    id: int
    name: str
    url_template: str
    supports_query: bool
    is_active: bool
    priority: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Database initialization
def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    
    # Initialize default RSS sources
    db = SessionLocal()
    try:
        # Check if sources already exist
        if not db.query(RSSSource).first():
            default_sources = [
                RSSSource(
                    name="Bing News",
                    url_template="https://www.bing.com/news/search?q={query}&format=rss",
                    supports_query=True,
                    priority=1
                ),
                RSSSource(
                    name="Google News",
                    url_template="https://news.google.com/rss/search?q={query}",
                    supports_query=True,
                    priority=2
                ),
                RSSSource(
                    name="Wall Street Journal",
                    url_template="https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
                    supports_query=False,
                    priority=3
                ),
                RSSSource(
                    name="Reuters",
                    url_template="https://www.reuters.com/markets/rss",
                    supports_query=False,
                    priority=4
                ),
                RSSSource(
                    name="Nasdaq",
                    url_template="https://www.nasdaq.com/feed/rssoutbound?category=markets",
                    supports_query=False,
                    priority=5
                )
            ]
            
            for source in default_sources:
                db.add(source)
            
            db.commit()
            print("Default RSS sources initialized")
    finally:
        db.close()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
