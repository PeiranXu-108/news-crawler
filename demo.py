#!/usr/bin/env python3
"""
Demo script for News Crawler Desktop Application
This script demonstrates the key features of the application.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from database import init_database, get_db, CrawlTask, Article, RSSSource
from crawler_service import CrawlerService
from summary_service import SummaryService

async def demo_crawler():
    """Demonstrate the crawler functionality."""
    print("🚀 News Crawler Desktop Application Demo")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing database...")
    init_database()
    print("✓ Database initialized")
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    print("🔧 Initializing services...")
    crawler_service = CrawlerService(db)
    summary_service = SummaryService(db)
    print("✓ Services initialized")
    
    # Create a demo task
    print("\n📝 Creating demo crawl task...")
    task = CrawlTask(
        query="artificial intelligence",
        limit=10
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    print(f"✓ Created task {task.id}: '{task.query}'")
    
    # Show available RSS sources
    print("\n📡 Available RSS sources:")
    sources = db.query(RSSSource).filter(RSSSource.is_active == True).all()
    for source in sources:
        print(f"  - {source.name}: {source.url_template}")
    
    # Run the crawler
    print(f"\n🕷️  Starting crawl for task {task.id}...")
    print("   This may take a few minutes...")
    
    start_time = time.time()
    success = await crawler_service.crawl_task(task.id)
    end_time = time.time()
    
    if success:
        print(f"✓ Crawling completed in {end_time - start_time:.1f} seconds")
        
        # Show results
        articles = db.query(Article).filter(Article.task_id == task.id).all()
        print(f"\n📰 Found {len(articles)} articles:")
        
        for i, article in enumerate(articles[:5], 1):  # Show first 5
            print(f"\n  {i}. {article.title}")
            print(f"     Source: {article.source}")
            print(f"     URL: {article.url}")
            print(f"     Published: {article.published}")
            print(f"     Summary: {article.summary[:100]}..." if article.summary else "     Summary: None")
            print(f"     Relevance Score: {article.relevance_score}")
        
        if len(articles) > 5:
            print(f"\n     ... and {len(articles) - 5} more articles")
        
        # Demonstrate summary generation
        print(f"\n🤖 Testing summary generation...")
        summary_stats = summary_service.get_summary_stats()
        print(f"   Current strategy: {summary_stats['current_strategy']}")
        print(f"   AI available: {summary_stats['ai_available']}")
        print(f"   Articles with summaries: {summary_stats['articles_with_summary']}")
        
        # Show task statistics
        print(f"\n📊 Task Statistics:")
        print(f"   Task ID: {task.id}")
        print(f"   Query: {task.query}")
        print(f"   Status: {task.status}")
        print(f"   Progress: {task.progress}%")
        print(f"   Total Articles: {task.total_articles}")
        print(f"   Processed Articles: {task.processed_articles}")
        print(f"   Created: {task.created_at}")
        print(f"   Started: {task.started_at}")
        print(f"   Completed: {task.completed_at}")
        
    else:
        print("❌ Crawling failed")
        print(f"   Error: {task.error_message}")
    
    print(f"\n🎉 Demo completed!")
    print(f"\n💡 Next steps:")
    print(f"   1. Start the desktop app: python start_all.py")
    print(f"   2. View the results in the Articles section")
    print(f"   3. Create new tasks with different queries")
    print(f"   4. Explore the RSS source management")
    print(f"   5. Try different summary generation strategies")

def main():
    """Main demo function."""
    try:
        asyncio.run(demo_crawler())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
