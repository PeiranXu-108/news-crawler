"""
Crawler service that handles news crawling operations.
"""

import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import dateparser
import feedparser
import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from tqdm import tqdm
from loguru import logger
from sqlalchemy.orm import Session

from database import CrawlTask, Article, RSSSource


class ArticlePipeline:
    """Handles article processing pipeline."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        self.request_delay = 1.0
        self.last_request_time = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request_time = time.time()

    async def fetch_article_content(self, article_url: str) -> str:
        """Fetch and extract article content."""
        try:
            await self.rate_limit()

            logger.info(f"Fetching article content: {article_url}")
            response = await self.client.get(article_url)
            response.raise_for_status()

            # Try trafilatura first
            content = trafilatura.extract(response.text)
            if content:
                return self.clean_text(content)

            # Fallback to readability
            doc = Document(response.text)
            content = doc.summary()
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                return self.clean_text(soup.get_text())

            return ""

        except Exception as e:
            logger.error(f"Error fetching article content {article_url}: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common noise
        text = re.sub(r'Advertisement|Subscribe|Newsletter',
                      '', text, flags=re.IGNORECASE)

        return text.strip()

    def generate_summary(self, article: Dict) -> str:
        """Generate article summary."""
        # If we already have a summary from RSS, use it
        if article.get('summary'):
            return article['summary']

        # Otherwise, extract from article text
        text = article.get('text', '')
        if not text:
            return ""

        # Simple summary: first paragraph or first few sentences
        sentences = text.split('. ')
        if len(sentences) >= 2:
            return sentences[0] + '. ' + sentences[1] + '.'
        elif len(sentences) == 1:
            return sentences[0] + '.'

        return text[:200] + '...' if len(text) > 200 else text

    def calculate_relevance_score(self, article: Dict, query: str) -> int:
        """Calculate relevance score for an article."""
        query_words = set(query.lower().split())
        
        # Check title (weight: 3)
        title_words = set(re.findall(r'\b\w+\b', article.get('title', '').lower()))
        title_matches = len(query_words.intersection(title_words))
        
        # Check summary (weight: 2)
        summary_words = set(re.findall(r'\b\w+\b', article.get('summary', '').lower()))
        summary_matches = len(query_words.intersection(summary_words))
        
        # Check text content (weight: 1)
        text_words = set(re.findall(r'\b\w+\b', article.get('text', '').lower()))
        text_matches = len(query_words.intersection(text_words))
        
        # Calculate weighted score (0-100)
        total_matches = title_matches * 3 + summary_matches * 2 + text_matches
        max_possible = len(query_words) * 6  # Maximum possible matches
        
        if max_possible == 0:
            return 0
            
        score = min(100, int((total_matches / max_possible) * 100))
        return score


class CrawlerService:
    """Main crawler service that manages crawling operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.seen_urls: Set[str] = set()

    def get_rss_sources(self, supports_query: bool = None) -> List[RSSSource]:
        """Get RSS sources from database."""
        query = self.db.query(RSSSource).filter(RSSSource.is_active == True)
        
        if supports_query is not None:
            query = query.filter(RSSSource.supports_query == supports_query)
            
        return query.order_by(RSSSource.priority).all()

    def filter_feeds_by_query(self, sources: List[RSSSource], query: str) -> List[str]:
        """Filter feeds that support query parameters."""
        query_feeds = []
        general_feeds = []

        for source in sources:
            if source.supports_query and '{query}' in source.url_template:
                query_feeds.append(source.url_template.replace('{query}', query))
            elif not source.supports_query:
                general_feeds.append(source.url_template)

        # Prioritize query-specific feeds
        return query_feeds + general_feeds

    async def fetch_rss_feed(self, feed_url: str, task: CrawlTask, pipeline: ArticlePipeline) -> List[Dict]:
        """Fetch and parse RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            response = await pipeline.client.get(feed_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            if feed.bozo:
                logger.warning(f"RSS feed parsing issues for {feed_url}: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries:
                if task.processed_articles >= task.limit:
                    break

                article = self.parse_rss_entry(entry, feed_url, task)
                if article and self.is_relevant(article, task.query):
                    articles.append(article)

            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    def parse_rss_entry(self, entry, feed_url: str, task: CrawlTask) -> Optional[Dict]:
        """Parse RSS entry into standardized article format."""
        try:
            # Extract basic info
            title = getattr(entry, 'title', '').strip()
            url = getattr(entry, 'link', '').strip()
            summary = getattr(entry, 'summary', '').strip()

            if not title or not url:
                return None

            # Skip if already seen
            if url in self.seen_urls:
                return None
            self.seen_urls.add(url)

            # Parse published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(
                    *entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(
                    *entry.updated_parsed[:6], tzinfo=timezone.utc)

            # Filter by date if specified
            if task.since and published:
                since_date = task.since
                if published.replace(tzinfo=None) < since_date:
                    return None

            # Extract source from feed URL or entry
            source = self.extract_source(feed_url, entry)

            # Clean summary
            if summary:
                summary = self.clean_text(summary)

            return {
                'title': title,
                'source': source,
                'url': url,
                'published': published.isoformat() if published else None,
                'summary': summary,
                'text': '',  # Will be filled later
                'tags': self.extract_tags(entry)
            }

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    def extract_source(self, feed_url: str, entry) -> str:
        """Extract source name from feed URL or entry."""
        # Try to get source from entry first
        if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
            return entry.source.title

        # Extract from feed URL
        parsed = urlparse(feed_url)
        domain = parsed.netloc.lower()

        # Map common domains to readable names
        source_map = {
            'www.bing.com': 'Bing News',
            'news.google.com': 'Google News',
            'feeds.a.dj.com': 'Wall Street Journal',
            'www.reuters.com': 'Reuters',
            'www.nasdaq.com': 'Nasdaq'
        }

        return source_map.get(domain, domain)

    def extract_tags(self, entry) -> List[str]:
        """Extract tags from RSS entry."""
        tags = []

        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    tags.append(tag.term)

        if hasattr(entry, 'category'):
            tags.append(entry.category)

        return tags

    def is_relevant(self, article: Dict, query: str) -> bool:
        """Check if article is relevant to the query."""
        query_words = set(query.lower().split())

        # Check title and summary
        text_to_check = f"{article['title']} {article['summary']}".lower()
        text_words = set(re.findall(r'\b\w+\b', text_to_check))

        # Simple relevance check - at least one query word should be present
        return bool(query_words.intersection(text_words))

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common noise
        text = re.sub(r'Advertisement|Subscribe|Newsletter',
                      '', text, flags=re.IGNORECASE)

        return text.strip()

    async def crawl_task(self, task_id: int) -> bool:
        """Main crawling method for a specific task."""
        task = self.db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        try:
            # Update task status
            task.status = "running"
            task.started_at = datetime.utcnow()
            self.db.commit()

            # Get RSS sources
            sources = self.get_rss_sources()
            if not sources:
                logger.error("No RSS sources available")
                task.status = "failed"
                task.error_message = "No RSS sources available"
                self.db.commit()
                return False

            # Filter feeds by query support
            feed_urls = self.filter_feeds_by_query(sources, task.query)

            logger.info(f"Starting crawl for task {task_id} with {len(feed_urls)} feeds, limit: {task.limit}")

            # Initialize article pipeline
            async with ArticlePipeline(self.db) as pipeline:
                # Fetch RSS feeds concurrently
                tasks_list = [self.fetch_rss_feed(feed_url, task, pipeline) for feed_url in feed_urls]
                results = await asyncio.gather(*tasks_list, return_exceptions=True)

                # Collect articles
                articles = []
                for result in results:
                    if isinstance(result, list):
                        articles.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Feed fetch error: {result}")

                logger.info(f"Found {len(articles)} articles from RSS feeds")

                # Process articles
                if articles:
                    task.total_articles = len(articles)
                    self.db.commit()

                    logger.info("Processing articles...")
                    for i, article in enumerate(articles):
                        if task.processed_articles >= task.limit:
                            break

                        # Fetch article content
                        content = await pipeline.fetch_article_content(article['url'])
                        article['text'] = content
                        article['summary'] = pipeline.generate_summary(article)
                        article['relevance_score'] = pipeline.calculate_relevance_score(article, task.query)

                        # Save article to database
                        db_article = Article(
                            task_id=task.id,
                            title=article['title'],
                            source=article['source'],
                            url=article['url'],
                            published=datetime.fromisoformat(article['published'].replace('Z', '+00:00')) if article['published'] else None,
                            summary=article['summary'],
                            text=article['text'],
                            tags=article['tags'],
                            relevance_score=article['relevance_score']
                        )
                        self.db.add(db_article)

                        task.processed_articles += 1
                        task.progress = int((task.processed_articles / min(task.total_articles, task.limit)) * 100)
                        self.db.commit()

                        # Update progress
                        logger.info(f"Processed {task.processed_articles}/{min(task.total_articles, task.limit)} articles")

            # Mark task as completed
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.progress = 100
            self.db.commit()

            logger.info(f"Crawling completed for task {task_id}. Processed {task.processed_articles} articles")
            return True

        except Exception as e:
            logger.error(f"Error in crawl_task {task_id}: {e}")
            task.status = "failed"
            task.error_message = str(e)
            self.db.commit()
            return False
