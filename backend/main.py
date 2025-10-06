"""
FastAPI backend service for news crawler with WebSocket support.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger
import uvicorn

from database import (
    get_db, init_database, CrawlTask, Article, RSSSource, AppConfig, CustomFeed,
    CrawlTaskCreate, CrawlTaskResponse, ArticleResponse, RSSSourceCreate, RSSSourceResponse
)
from crawler_service import CrawlerService
from summary_service import SummaryService

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress_update(self, task_id: int, progress: int, status: str, message: str = ""):
        """Send progress update to all connected clients."""
        data = {
            "type": "progress_update",
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected clients
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(data))
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Global services
crawler_service = None
summary_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global crawler_service, summary_service
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Initialize services
        db = next(get_db())
        crawler_service = CrawlerService(db)
        summary_service = SummaryService(db)
        logger.info("Services initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Continue without services for now
    
    yield
    
    # Cleanup
    logger.info("Shutting down services")

# Create FastAPI app
app = FastAPI(
    title="News Crawler API",
    description="Backend API for news crawling and management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task for crawling
async def run_crawl_task(task_id: int):
    """Background task to run crawling."""
    global crawler_service
    if crawler_service:
        success = await crawler_service.crawl_task(task_id)
        if success:
            await manager.send_progress_update(task_id, 100, "completed", "Crawling completed successfully")
        else:
            await manager.send_progress_update(task_id, 0, "failed", "Crawling failed")

# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "News Crawler API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Task Management Endpoints

@app.post("/tasks", response_model=CrawlTaskResponse)
async def create_crawl_task(
    task_data: CrawlTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new crawl task."""
    try:
        # Create task in database
        task = CrawlTask(
            query=task_data.query,
            since=task_data.since,
            limit=task_data.limit
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Add custom feeds if provided
        if task_data.custom_feeds:
            for feed_url in task_data.custom_feeds:
                custom_feed = CustomFeed(
                    task_id=task.id,
                    url=feed_url
                )
                db.add(custom_feed)
            db.commit()

        # Start background crawling task
        background_tasks.add_task(run_crawl_task, task.id)

        logger.info(f"Created crawl task {task.id} for query: {task_data.query}")
        return task

    except Exception as e:
        logger.error(f"Error creating crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks", response_model=List[CrawlTaskResponse])
async def get_crawl_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all crawl tasks with optional filtering."""
    query = db.query(CrawlTask)
    
    if status:
        query = query.filter(CrawlTask.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=CrawlTaskResponse)
async def get_crawl_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific crawl task."""
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}")
async def delete_crawl_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a crawl task and its articles."""
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Delete task (articles will be deleted due to cascade)
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}

@app.post("/tasks/{task_id}/retry")
async def retry_crawl_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed crawl task."""
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in ["failed", "completed"]:
        raise HTTPException(status_code=400, detail="Task is not in a retryable state")
    
    # Reset task status
    task.status = "pending"
    task.started_at = None
    task.completed_at = None
    task.error_message = None
    task.progress = 0
    task.processed_articles = 0
    db.commit()
    
    # Start background crawling task
    background_tasks.add_task(run_crawl_task, task.id)
    
    return {"message": "Task retry initiated"}

# Article Management Endpoints

@app.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    task_id: Optional[int] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get articles with optional filtering."""
    query = db.query(Article)
    
    if task_id:
        query = query.filter(Article.task_id == task_id)
    
    if source:
        query = query.filter(Article.source == source)
    
    articles = query.offset(skip).limit(limit).all()
    return articles

@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.post("/articles/{article_id}/regenerate-summary")
async def regenerate_article_summary(
    article_id: int,
    strategy: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Regenerate summary for a specific article."""
    global summary_service
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if summary_service:
        if strategy:
            summary_service.set_summary_strategy(strategy)
        
        summary = summary_service.generate_summary(article, force_regenerate=True)
        article.summary = summary
        db.commit()
        
        return {"message": "Summary regenerated", "summary": summary}
    else:
        raise HTTPException(status_code=500, detail="Summary service not available")

# RSS Source Management Endpoints

@app.get("/rss-sources", response_model=List[RSSSourceResponse])
async def get_rss_sources(db: Session = Depends(get_db)):
    """Get all RSS sources."""
    sources = db.query(RSSSource).all()
    return sources

@app.post("/rss-sources", response_model=RSSSourceResponse)
async def create_rss_source(
    source_data: RSSSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new RSS source."""
    # Check if source with same name already exists
    existing = db.query(RSSSource).filter(RSSSource.name == source_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="RSS source with this name already exists")
    
    source = RSSSource(**source_data.dict())
    db.add(source)
    db.commit()
    db.refresh(source)
    
    return source

@app.put("/rss-sources/{source_id}", response_model=RSSSourceResponse)
async def update_rss_source(
    source_id: int,
    source_data: RSSSourceCreate,
    db: Session = Depends(get_db)
):
    """Update an RSS source."""
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS source not found")
    
    # Update fields
    for field, value in source_data.dict().items():
        setattr(source, field, value)
    
    db.commit()
    db.refresh(source)
    
    return source

@app.delete("/rss-sources/{source_id}")
async def delete_rss_source(source_id: int, db: Session = Depends(get_db)):
    """Delete an RSS source."""
    source = db.query(RSSSource).filter(RSSSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="RSS source not found")
    
    db.delete(source)
    db.commit()
    
    return {"message": "RSS source deleted successfully"}

# Summary Service Endpoints

@app.get("/summary/stats")
async def get_summary_stats(db: Session = Depends(get_db)):
    """Get summary generation statistics."""
    global summary_service
    if summary_service:
        return summary_service.get_summary_stats()
    else:
        raise HTTPException(status_code=500, detail="Summary service not available")

@app.post("/summary/regenerate")
async def regenerate_summaries(
    article_ids: List[int],
    strategy: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Regenerate summaries for multiple articles."""
    global summary_service
    if summary_service:
        summary_service.batch_generate_summaries(article_ids, strategy)
        return {"message": f"Summaries regenerated for {len(article_ids)} articles"}
    else:
        raise HTTPException(status_code=500, detail="Summary service not available")

@app.put("/summary/strategy")
async def set_summary_strategy(
    strategy: str,
    db: Session = Depends(get_db)
):
    """Set summary generation strategy."""
    global summary_service
    if summary_service:
        summary_service.set_summary_strategy(strategy)
        return {"message": f"Summary strategy set to: {strategy}"}
    else:
        raise HTTPException(status_code=500, detail="Summary service not available")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
