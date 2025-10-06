"""
Summary generation service with multiple strategies and caching.
"""

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Using simple summarization.")

from database import Article, AppConfig


class SummaryService:
    """Service for generating article summaries with multiple strategies."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
        
        # Initialize models if available
        self.summarizer = None
        self.tokenizer = None
        self.model = None
        
        if TRANSFORMERS_AVAILABLE:
            self._load_models()

    def _load_models(self):
        """Load summarization models."""
        try:
            # Use a lightweight model for better performance
            model_name = "facebook/bart-large-cnn"
            logger.info(f"Loading summarization model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Create pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Summarization model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
            self.summarizer = None

    def get_summary_strategy(self) -> str:
        """Get current summary strategy from config."""
        config = self.db.query(AppConfig).filter(AppConfig.key == "summary_strategy").first()
        if config:
            return config.value
        return "rss_first"  # Default strategy

    def set_summary_strategy(self, strategy: str):
        """Set summary strategy in config."""
        config = self.db.query(AppConfig).filter(AppConfig.key == "summary_strategy").first()
        if config:
            config.value = strategy
            config.updated_at = datetime.utcnow()
        else:
            config = AppConfig(
                key="summary_strategy",
                value=strategy,
                description="Summary generation strategy: rss_first, ai_generated, hybrid"
            )
            self.db.add(config)
        
        self.db.commit()

    def _get_cache_key(self, text: str, strategy: str) -> str:
        """Generate cache key for text and strategy."""
        content = f"{text}_{strategy}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_summary(self, cache_key: str) -> Optional[str]:
        """Get cached summary if available and not expired."""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['summary']
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None

    def _cache_summary(self, cache_key: str, summary: str):
        """Cache summary with timestamp."""
        self.cache[cache_key] = {
            'summary': summary,
            'timestamp': datetime.now()
        }

    def generate_summary(self, article: Article, force_regenerate: bool = False) -> str:
        """Generate summary for an article using the configured strategy."""
        strategy = self.get_summary_strategy()
        
        # Check if we already have a summary and don't need to regenerate
        if not force_regenerate and article.summary:
            if strategy == "rss_first":
                return article.summary
            elif strategy == "ai_generated":
                # Check if this is an AI-generated summary
                if len(article.summary) > 200:  # Simple heuristic
                    return article.summary
        
        # Generate cache key
        text_to_summarize = article.text or article.title
        cache_key = self._get_cache_key(text_to_summarize, strategy)
        
        # Check cache first
        if not force_regenerate:
            cached_summary = self._get_cached_summary(cache_key)
            if cached_summary:
                return cached_summary

        # Generate summary based on strategy
        summary = ""
        
        if strategy == "rss_first":
            summary = self._rss_first_strategy(article)
        elif strategy == "ai_generated":
            summary = self._ai_generated_strategy(article)
        elif strategy == "hybrid":
            summary = self._hybrid_strategy(article)
        else:
            summary = self._simple_strategy(article)

        # Cache the result
        if summary:
            self._cache_summary(cache_key, summary)

        return summary

    def _rss_first_strategy(self, article: Article) -> str:
        """Use RSS summary if available, otherwise generate simple summary."""
        if article.summary and len(article.summary.strip()) > 10:
            return article.summary
        
        return self._simple_strategy(article)

    def _ai_generated_strategy(self, article: Article) -> str:
        """Use AI model to generate summary."""
        if not self.summarizer:
            logger.warning("AI summarizer not available, falling back to simple strategy")
            return self._simple_strategy(article)

        text = article.text or article.title
        if not text or len(text.strip()) < 50:
            return self._simple_strategy(article)

        try:
            # Truncate text if too long
            max_length = 1024
            if len(text) > max_length:
                text = text[:max_length]

            # Generate summary
            result = self.summarizer(
                text,
                max_length=150,
                min_length=30,
                do_sample=False,
                truncation=True
            )
            
            summary = result[0]['summary_text']
            return summary.strip()

        except Exception as e:
            logger.error(f"Error in AI summarization: {e}")
            return self._simple_strategy(article)

    def _hybrid_strategy(self, article: Article) -> str:
        """Combine RSS summary with AI enhancement."""
        rss_summary = article.summary or ""
        text = article.text or article.title

        # If RSS summary is good enough, use it
        if len(rss_summary.strip()) > 50:
            return rss_summary

        # Otherwise, use AI to generate from full text
        if self.summarizer and text and len(text.strip()) > 100:
            try:
                result = self.summarizer(
                    text,
                    max_length=150,
                    min_length=30,
                    do_sample=False,
                    truncation=True
                )
                return result[0]['summary_text'].strip()
            except Exception as e:
                logger.error(f"Error in hybrid summarization: {e}")

        return self._simple_strategy(article)

    def _simple_strategy(self, article: Article) -> str:
        """Generate simple summary using text extraction."""
        text = article.text or article.title
        if not text:
            return ""

        # Simple summary: first paragraph or first few sentences
        sentences = text.split('. ')
        if len(sentences) >= 2:
            return sentences[0] + '. ' + sentences[1] + '.'
        elif len(sentences) == 1:
            return sentences[0] + '.'

        return text[:200] + '...' if len(text) > 200 else text

    def batch_generate_summaries(self, article_ids: list, strategy: str = None):
        """Generate summaries for multiple articles in batch."""
        if strategy:
            self.set_summary_strategy(strategy)
        
        articles = self.db.query(Article).filter(Article.id.in_(article_ids)).all()
        
        for article in articles:
            try:
                summary = self.generate_summary(article, force_regenerate=True)
                article.summary = summary
                self.db.commit()
                logger.info(f"Generated summary for article {article.id}")
            except Exception as e:
                logger.error(f"Error generating summary for article {article.id}: {e}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary generation statistics."""
        total_articles = self.db.query(Article).count()
        articles_with_summary = self.db.query(Article).filter(Article.summary.isnot(None)).count()
        
        return {
            "total_articles": total_articles,
            "articles_with_summary": articles_with_summary,
            "coverage_percentage": (articles_with_summary / total_articles * 100) if total_articles > 0 else 0,
            "current_strategy": self.get_summary_strategy(),
            "cache_size": len(self.cache),
            "ai_available": self.summarizer is not None
        }
