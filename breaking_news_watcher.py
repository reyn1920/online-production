#!/usr/bin/env python3
"""
Breaking News Watcher - Core RSS Intelligence Engine

This module serves as the central RSS intelligence system that continuously
parses RSS feeds, extracts key information, and provides real-time intelligence
to the Research, Planner, and Content agents.
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import re
import hashlib

import feedparser
import requests
from bs4 import BeautifulSoup
from textstat import flesch_reading_ease

from utils.logger import get_logger
from backend.secret_store import SecretStore

logger = get_logger(__name__)

@dataclass
class NewsArticle:
    """Represents a parsed news article with extracted intelligence."""
    title: str
    url: str
    content: str
    published: datetime
    source: str
    category: str
    keywords: List[str]
    entities: List[str]
    sentiment_score: float
    readability_score: float
    hash_id: str

@dataclass
class TrendData:
    """Represents trend analysis data for topics and keywords."""
    keyword: str
    frequency: int
    trend_score: float
    first_seen: datetime
    last_seen: datetime
    sources: List[str]
    related_articles: List[str]

class RSSIntelligenceEngine:
    """Core RSS intelligence engine for continuous news monitoring and analysis."""
    
    def __init__(self, db_path: str = "right_perspective.db", config_path: str = "rss_feeds_example.json"):
        self.db_path = db_path
        self.config_path = config_path
        self.secret_store = SecretStore()
        self.feeds = self._load_rss_feeds()
        self.running = False
        self.trend_window_hours = 24
        self.min_trend_frequency = 3
        
        # Initialize database tables
        self._init_intelligence_tables()
        
        logger.info(f"RSS Intelligence Engine initialized with {len(self.feeds)} feeds")
    
    def _load_rss_feeds(self) -> List[Dict]:
        """Load RSS feeds configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('feeds', [])
        except FileNotFoundError:
            logger.warning(f"RSS config file {self.config_path} not found, using empty feed list")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing RSS config: {e}")
            return []
    
    def _init_intelligence_tables(self):
        """Initialize database tables for intelligence storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # News articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content TEXT,
                published TIMESTAMP,
                source TEXT,
                category TEXT,
                keywords TEXT,
                entities TEXT,
                sentiment_score REAL,
                readability_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trend analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                trend_score REAL DEFAULT 0.0,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                sources TEXT,
                related_articles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Hypocrisy tracker table - matches master schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hypocrisy_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                subject_type TEXT CHECK (subject_type IN ('person', 'organization', 'publication', 'politician', 'celebrity', 'influencer')),
                statement_1 TEXT NOT NULL,
                statement_2 TEXT NOT NULL,
                context_1 TEXT,
                context_2 TEXT,
                date_1 DATE,
                date_2 DATE,
                source_1 TEXT,
                source_2 TEXT,
                contradiction_type TEXT CHECK (contradiction_type IN ('direct', 'contextual', 'temporal', 'value', 'policy_shift', 'audience_based')),
                severity_score INTEGER CHECK (severity_score BETWEEN 1 AND 10),
                confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
                verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'disputed', 'debunked')),
                evidence_links JSON,
                tags JSON,
                analysis_notes TEXT,
                public_impact_score INTEGER CHECK (public_impact_score BETWEEN 1 AND 10),
                media_coverage_count INTEGER DEFAULT 0,
                social_media_mentions INTEGER DEFAULT 0,
                fact_check_results JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                content_used BOOLEAN DEFAULT FALSE,
                content_used_at TIMESTAMP
            )
        """)
        
        # Intelligence briefings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intelligence_briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                briefing_data TEXT NOT NULL,
                relevance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Intelligence database tables initialized")
    
    def _generate_article_hash(self, title: str, url: str, published: datetime) -> str:
        """Generate unique hash for article deduplication."""
        content = f"{title}{url}{published.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using simple NLP techniques."""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Extract words (3+ characters, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Return top keywords by frequency
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(10)]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (simple pattern matching)."""
        # Simple entity extraction - capitalized words/phrases
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))[:10]  # Deduplicate and limit
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate basic sentiment score (-1 to 1)."""
        # Simple sentiment analysis using keyword matching
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'success', 'win', 'victory', 'breakthrough', 'achievement']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'failure', 'lose', 'defeat', 'crisis', 'disaster', 'scandal', 'controversy']
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))  # Clamp to [-1, 1]
    
    def _fetch_article_content(self, url: str) -> str:
        """Fetch and extract article content from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text from common article containers
            content_selectors = [
                'article', '.article-content', '.post-content', 
                '.entry-content', '.content', 'main', '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break
            
            if not content:
                # Fallback to body text
                content = soup.get_text(strip=True)
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
            return content[:5000]  # Limit content length
            
        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {e}")
            return ""
    
    def _parse_feed(self, feed_config: Dict) -> List[NewsArticle]:
        """Parse a single RSS feed and extract articles."""
        articles = []
        
        try:
            feed_url = feed_config['url']
            source = feed_config.get('name', 'Unknown')
            category = feed_config.get('category', 'General')
            
            logger.info(f"Parsing feed: {source} ({feed_url})")
            
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent articles
                try:
                    # Parse publication date
                    published = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    
                    # Generate article hash for deduplication
                    hash_id = self._generate_article_hash(entry.title, entry.link, published)
                    
                    # Check if article already exists
                    if self._article_exists(hash_id):
                        continue
                    
                    # Extract content
                    content = entry.get('summary', '')
                    if len(content) < 200:  # If summary is short, fetch full content
                        full_content = self._fetch_article_content(entry.link)
                        if full_content:
                            content = full_content
                    
                    # Extract intelligence data
                    keywords = self._extract_keywords(f"{entry.title} {content}")
                    entities = self._extract_entities(f"{entry.title} {content}")
                    sentiment = self._calculate_sentiment(content)
                    readability = flesch_reading_ease(content) if content else 0.0
                    
                    article = NewsArticle(
                        title=entry.title,
                        url=entry.link,
                        content=content,
                        published=published,
                        source=source,
                        category=category,
                        keywords=keywords,
                        entities=entities,
                        sentiment_score=sentiment,
                        readability_score=readability,
                        hash_id=hash_id
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Error parsing article from {source}: {e}")
                    continue
            
            logger.info(f"Parsed {len(articles)} new articles from {source}")
            
        except Exception as e:
            logger.error(f"Error parsing feed {feed_config.get('name', 'Unknown')}: {e}")
        
        return articles
    
    def _article_exists(self, hash_id: str) -> bool:
        """Check if article already exists in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM news_articles WHERE hash_id = ?", (hash_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def _store_article(self, article: NewsArticle) -> bool:
        """Store article in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO news_articles 
                (hash_id, title, url, content, published, source, category, 
                 keywords, entities, sentiment_score, readability_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.hash_id,
                article.title,
                article.url,
                article.content,
                article.published,
                article.source,
                article.category,
                json.dumps(article.keywords),
                json.dumps(article.entities),
                article.sentiment_score,
                article.readability_score
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            return False
    
    def _update_trend_analysis(self, articles: List[NewsArticle]):
        """Update trend analysis based on new articles."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Collect all keywords from new articles
        keyword_sources = defaultdict(list)
        keyword_articles = defaultdict(list)
        
        for article in articles:
            for keyword in article.keywords:
                keyword_sources[keyword].append(article.source)
                keyword_articles[keyword].append(article.url)
        
        # Update trend data
        for keyword, sources in keyword_sources.items():
            # Check if keyword trend exists
            cursor.execute(
                "SELECT frequency, sources, related_articles FROM trend_analysis WHERE keyword = ?",
                (keyword,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing trend
                frequency, existing_sources, existing_articles = result
                new_frequency = frequency + len(sources)
                
                # Merge sources and articles
                all_sources = json.loads(existing_sources) + sources
                all_articles = json.loads(existing_articles) + keyword_articles[keyword]
                
                # Calculate trend score (frequency over time)
                trend_score = self._calculate_trend_score(keyword, new_frequency)
                
                cursor.execute("""
                    UPDATE trend_analysis 
                    SET frequency = ?, trend_score = ?, last_seen = CURRENT_TIMESTAMP,
                        sources = ?, related_articles = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE keyword = ?
                """, (
                    new_frequency,
                    trend_score,
                    json.dumps(list(set(all_sources))),
                    json.dumps(list(set(all_articles))),
                    keyword
                ))
            else:
                # Create new trend
                trend_score = self._calculate_trend_score(keyword, len(sources))
                
                cursor.execute("""
                    INSERT INTO trend_analysis 
                    (keyword, frequency, trend_score, first_seen, last_seen, sources, related_articles)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
                """, (
                    keyword,
                    len(sources),
                    trend_score,
                    json.dumps(sources),
                    json.dumps(keyword_articles[keyword])
                ))
        
        conn.commit()
        conn.close()
    
    def _calculate_trend_score(self, keyword: str, frequency: int) -> float:
        """Calculate trend score for a keyword based on frequency and recency."""
        # Simple trend scoring: frequency weighted by recency
        base_score = min(frequency / 10.0, 1.0)  # Normalize to 0-1
        
        # Add recency bonus (keywords seen recently get higher scores)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT last_seen FROM trend_analysis WHERE keyword = ?",
            (keyword,)
        )
        result = cursor.fetchone()
        
        if result:
            last_seen = datetime.fromisoformat(result[0])
            hours_since = (datetime.now() - last_seen).total_seconds() / 3600
            recency_bonus = max(0, 1 - (hours_since / 24))  # Decay over 24 hours
            base_score += recency_bonus * 0.5
        
        conn.close()
        return min(base_score, 2.0)  # Cap at 2.0
    
    def get_trending_topics(self, limit: int = 10) -> List[TrendData]:
        """Get current trending topics based on analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT keyword, frequency, trend_score, first_seen, last_seen, sources, related_articles
            FROM trend_analysis
            WHERE frequency >= ? AND last_seen > datetime('now', '-24 hours')
            ORDER BY trend_score DESC, frequency DESC
            LIMIT ?
        """, (self.min_trend_frequency, limit))
        
        trends = []
        for row in cursor.fetchall():
            keyword, frequency, trend_score, first_seen, last_seen, sources, related_articles = row
            
            trend = TrendData(
                keyword=keyword,
                frequency=frequency,
                trend_score=trend_score,
                first_seen=datetime.fromisoformat(first_seen),
                last_seen=datetime.fromisoformat(last_seen),
                sources=json.loads(sources),
                related_articles=json.loads(related_articles)
            )
            trends.append(trend)
        
        conn.close()
        return trends
    
    def get_intelligence_briefing(self, topic: str, max_articles: int = 5) -> Dict:
        """Generate intelligence briefing for a specific topic."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search for articles related to the topic
        cursor.execute("""
            SELECT title, url, content, published, source, sentiment_score
            FROM news_articles
            WHERE (title LIKE ? OR content LIKE ? OR keywords LIKE ?)
            AND published > datetime('now', '-48 hours')
            ORDER BY published DESC
            LIMIT ?
        """, (f"%{topic}%", f"%{topic}%", f"%{topic}%", max_articles))
        
        articles = cursor.fetchall()
        
        # Get trend data for the topic
        cursor.execute(
            "SELECT frequency, trend_score FROM trend_analysis WHERE keyword LIKE ?",
            (f"%{topic}%",)
        )
        trend_data = cursor.fetchone()
        
        conn.close()
        
        briefing = {
            'topic': topic,
            'generated_at': datetime.now().isoformat(),
            'article_count': len(articles),
            'articles': [
                {
                    'title': article[0],
                    'url': article[1],
                    'summary': article[2][:200] + '...' if len(article[2]) > 200 else article[2],
                    'published': article[3],
                    'source': article[4],
                    'sentiment': article[5]
                }
                for article in articles
            ],
            'trend_data': {
                'frequency': trend_data[0] if trend_data else 0,
                'trend_score': trend_data[1] if trend_data else 0.0
            } if trend_data else None
        }
        
        return briefing
    
    def get_latest_intelligence_briefing(self, briefing_type: str = None) -> Dict[str, Any]:
        """Get the latest intelligence briefing from recent articles."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent articles from the last 24 hours
        cursor.execute("""
            SELECT title, url, content, published, source, sentiment_score
            FROM news_articles
            WHERE published > datetime('now', '-24 hours')
            ORDER BY published DESC
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        # Get trending topics
        cursor.execute("""
            SELECT keyword, frequency, trend_score
            FROM trend_analysis
            ORDER BY trend_score DESC
            LIMIT 5
        """)
        
        trending = cursor.fetchall()
        conn.close()
        
        return {
            'briefing_type': briefing_type or 'general',
            'generated_at': datetime.now().isoformat(),
            'article_count': len(articles),
            'articles': [
                {
                    'title': article[0],
                    'url': article[1],
                    'summary': article[2][:200] + '...' if len(article[2]) > 200 else article[2],
                    'published': article[3],
                    'source': article[4],
                    'sentiment': article[5]
                }
                for article in articles
            ],
            'trending_topics': [
                {
                    'keyword': trend[0],
                    'frequency': trend[1],
                    'trend_score': trend[2]
                }
                for trend in trending
            ]
        }
    
    async def run_continuous_monitoring(self, interval_minutes: int = 30):
        """Run continuous RSS monitoring and analysis."""
        self.running = True
        logger.info(f"Starting continuous RSS monitoring (interval: {interval_minutes} minutes)")
        
        while self.running:
            try:
                logger.info("Starting RSS feed parsing cycle")
                
                all_articles = []
                for feed_config in self.feeds:
                    articles = self._parse_feed(feed_config)
                    all_articles.extend(articles)
                    
                    # Store articles
                    for article in articles:
                        self._store_article(article)
                
                # Update trend analysis
                if all_articles:
                    self._update_trend_analysis(all_articles)
                    logger.info(f"Processed {len(all_articles)} new articles")
                else:
                    logger.info("No new articles found")
                
                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in RSS monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.running = False
        logger.info("RSS monitoring stopped")

if __name__ == "__main__":
    # Example usage
    engine = RSSIntelligenceEngine()
    
    # Run a single parsing cycle
    print("Running single RSS parsing cycle...")
    all_articles = []
    for feed_config in engine.feeds:
        articles = engine._parse_feed(feed_config)
        all_articles.extend(articles)
        
        for article in articles:
            engine._store_article(article)
    
    if all_articles:
        engine._update_trend_analysis(all_articles)
        print(f"Processed {len(all_articles)} articles")
        
        # Show trending topics
        trends = engine.get_trending_topics(5)
        print("\nTop trending topics:")
        for trend in trends:
            print(f"- {trend.keyword}: {trend.frequency} mentions (score: {trend.trend_score:.2f})")
    else:
        print("No new articles found")