#!/usr/bin/env python3
"""
News Crawler MVP
Aggregates news articles from RSS feeds based on keywords and outputs to JSONL/CSV.
"""

import argparse
import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import dateparser
import feedparser
import httpx
import pandas as pd
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """Main news crawler class."""

    def __init__(self,
                 query: str,
                 since: Optional[str] = None,
                 limit: int = 50,
                 custom_feeds: Optional[List[str]] = None):
        self.query = query
        self.since = since
        self.limit = limit
        self.custom_feeds = custom_feeds
        self.seen_urls: Set[str] = set()
        self.articles: List[Dict] = []

        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0

        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def load_default_feeds(self) -> List[str]:
        """Load default RSS feeds from config file."""
        config_file = Path(__file__).parent / "config" / "feeds.default.txt"
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return []

        feeds = []
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    feeds.append(line)

        return feeds

    def get_feeds(self) -> List[str]:
        """Get list of RSS feeds to crawl."""
        if self.custom_feeds:
            return self.custom_feeds

        return self.load_default_feeds()

    def filter_feeds_by_query(self, feeds: List[str]) -> List[str]:
        """Filter feeds that support query parameters."""
        query_feeds = []
        general_feeds = []

        for feed in feeds:
            if '{query}' in feed:
                query_feeds.append(feed.replace('{query}', self.query))
            else:
                general_feeds.append(feed)

        # Prioritize query-specific feeds
        return query_feeds + general_feeds

    async def rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request_time = time.time()

    async def fetch_rss_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS feed."""
        try:
            await self.rate_limit()

            logger.info(f"Fetching RSS feed: {feed_url}")
            response = await self.client.get(feed_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            if feed.bozo:
                logger.warning(
                    f"RSS feed parsing issues for {feed_url}: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries:
                if len(self.articles) >= self.limit:
                    break

                article = self.parse_rss_entry(entry, feed_url)
                if article and self.is_relevant(article):
                    articles.append(article)

            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    def parse_rss_entry(self, entry, feed_url: str) -> Optional[Dict]:
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
            if self.since and published:
                since_date = dateparser.parse(self.since)
                if since_date and published.replace(tzinfo=None) < since_date:
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

    def is_relevant(self, article: Dict) -> bool:
        """Check if article is relevant to the query."""
        query_words = set(self.query.lower().split())

        # Check title and summary
        text_to_check = f"{article['title']} {article['summary']}".lower()
        text_words = set(re.findall(r'\b\w+\b', text_to_check))

        # Simple relevance check - at least one query word should be present
        return bool(query_words.intersection(text_words))

    async def fetch_article_content(self, article: Dict) -> str:
        """Fetch and extract article content."""
        try:
            await self.rate_limit()

            logger.info(f"Fetching article content: {article['url']}")
            response = await self.client.get(article['url'])
            response.raise_for_status()

            # Try trafilatura first
            content = trafilatura.extract(response.text)
            if content:
                return self.clean_text(content)

            # Fallback to readability
            doc = Document(response.text)
            content = doc.summary()
            if content:
                # Parse with BeautifulSoup to get text
                soup = BeautifulSoup(content, 'html.parser')
                return self.clean_text(soup.get_text())

            return ""

        except Exception as e:
            logger.error(
                f"Error fetching article content {article['url']}: {e}")
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
        if article['summary']:
            return article['summary']

        # Otherwise, extract from article text
        text = article['text']
        if not text:
            return ""

        # Simple summary: first paragraph or first few sentences
        sentences = text.split('. ')
        if len(sentences) >= 2:
            return sentences[0] + '. ' + sentences[1] + '.'
        elif len(sentences) == 1:
            return sentences[0] + '.'

        return text[:200] + '...' if len(text) > 200 else text

    async def crawl(self):
        """Main crawling method."""
        feeds = self.get_feeds()
        if not feeds:
            logger.error("No RSS feeds available")
            return

        # Filter feeds by query support
        query_feeds = self.filter_feeds_by_query(feeds)

        logger.info(
            f"Starting crawl with {len(query_feeds)} feeds, limit: {self.limit}")

        # Fetch RSS feeds concurrently
        tasks = [self.fetch_rss_feed(feed) for feed in query_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect articles
        for result in results:
            if isinstance(result, list):
                self.articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch error: {result}")

        logger.info(f"Found {len(self.articles)} articles from RSS feeds")

        # Fetch article content
        if self.articles:
            logger.info("Fetching article content...")
            for article in tqdm(self.articles, desc="Fetching content"):
                if len(self.articles) > self.limit:
                    break

                content = await self.fetch_article_content(article)
                article['text'] = content
                article['summary'] = self.generate_summary(article)

        # Limit final results
        self.articles = self.articles[:self.limit]

        logger.info(f"Crawling completed. Found {len(self.articles)} articles")

    def save_to_jsonl(self, output_dir: Path):
        """Save articles to JSONL format."""
        output_file = output_dir / "news.jsonl"

        with open(output_file, 'w', encoding='utf-8') as f:
            for article in self.articles:
                json.dump(article, f, ensure_ascii=False)
                f.write('\n')

        logger.info(f"Saved {len(self.articles)} articles to {output_file}")

    def save_to_csv(self, output_dir: Path):
        """Save articles to CSV format."""
        if not self.articles:
            return

        output_file = output_dir / "news.csv"

        # Convert to DataFrame
        df = pd.DataFrame(self.articles)

        # Reorder columns
        column_order = [
            'title',
            'source',
            'url',
            'published',
            'summary',
            'text',
            'tags']
        df = df.reindex(columns=column_order)

        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')

        logger.info(f"Saved {len(self.articles)} articles to {output_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='News Crawler MVP')
    parser.add_argument('--q', '--query', required=True,
                        help='Search query (required)')
    parser.add_argument('--since', help='Start date (ISO format YYYY-MM-DD)')
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of articles (default: 50)')
    parser.add_argument('--feeds', help='Custom RSS feeds (comma-separated)')

    args = parser.parse_args()

    # Parse custom feeds
    custom_feeds = None
    if args.feeds:
        custom_feeds = [feed.strip() for feed in args.feeds.split(',')]

    # Create output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Run crawler
    async with NewsCrawler(
        query=args.q,
        since=args.since,
        limit=args.limit,
        custom_feeds=custom_feeds
    ) as crawler:
        await crawler.crawl()
        crawler.save_to_jsonl(output_dir)
        crawler.save_to_csv(output_dir)


if __name__ == "__main__":
    asyncio.run(main())
