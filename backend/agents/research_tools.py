#!/usr/bin/env python3
"""
Research Agent Tools Module

Implements comprehensive research capabilities including:
- Breaking news monitoring via RSS feeds
- Competitor analysis (TubeBuddy/VidIQ emulation)
- Market validation for digital products
- YouTube channel analysis and niche opportunity detection
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

# Import hypocrisy database manager
try:
    from backend.database.hypocrisy_db_manager import (HypocrisyDatabaseManager,
                                                       HypocrisyFinding)
except ImportError:
    HypocrisyDatabaseManager = None
    HypocrisyFinding = None
    logging.warning(
        "HypocrisyDatabaseManager not available. Hypocrisy tracking will be limited."
    )

# Import performance analytics agent
try:
    from backend.agents.performance_analytics_agent import PerformanceAnalyticsAgent
except ImportError:
    PerformanceAnalyticsAgent = None
    logging.warning(
        "PerformanceAnalyticsAgent not available. Performance analytics will be limited."
    )

try:
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    import feedparser
    import nltk
    import numpy as np
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)
    from textblob import TextBlob
except ImportError as e:
    logging.warning(f"Optional dependency missing: {e}. Some features may be limited.")
    feedparser = None
    requests = None
    BeautifulSoup = None
    nltk = None
    TextBlob = None
    pd = None
    np = None
    SimpleDocTemplate = None
    Paragraph = None
    getSampleStyleSheet = None
    smtplib = None
    MIMEMultipart = None


class NewsCategory(Enum):
    """Categories for news classification"""

    TECHNOLOGY = "technology"
    BUSINESS = "business"
    MARKETING = "marketing"
    SOCIAL_MEDIA = "social_media"
    AI_ML = "ai_ml"
    CRYPTO = "crypto"
    FINANCE = "finance"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"


class TrendStrength(Enum):
    """Strength levels for trend analysis"""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VIRAL = "viral"


class CompetitorMetric(Enum):
    """Metrics for competitor analysis"""

    SUBSCRIBER_COUNT = "subscriber_count"
    VIEW_COUNT = "view_count"
    ENGAGEMENT_RATE = "engagement_rate"
    UPLOAD_FREQUENCY = "upload_frequency"
    AVERAGE_VIEWS = "average_views"
    TRENDING_SCORE = "trending_score"
    NICHE_SATURATION = "niche_saturation"


@dataclass
class NewsItem:
    """Represents a single news item from RSS feeds"""

    title: str
    description: str
    link: str
    published: datetime
    source: str
    category: NewsCategory = NewsCategory.GENERAL
    sentiment_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    trend_strength: TrendStrength = TrendStrength.WEAK
    relevance_score: float = 0.0


@dataclass
class CompetitorChannel:
    """Represents a YouTube competitor channel"""

    channel_id: str
    channel_name: str
    subscriber_count: int
    total_views: int
    video_count: int
    upload_frequency: float  # videos per week
    average_views: float
    engagement_rate: float
    niche_keywords: List[str] = field(default_factory=list)
    content_themes: List[str] = field(default_factory=list)
    opportunity_score: float = 0.0
    last_analyzed: datetime = field(default_factory=datetime.now)


@dataclass
class MarketOpportunity:
    """Represents a market opportunity for digital products"""

    niche: str
    keywords: List[str]
    search_volume: int
    competition_level: str  # low, medium, high
    trend_direction: str  # rising, stable, declining
    monetization_potential: float  # 0-1 score
    target_audience: str
    content_gaps: List[str] = field(default_factory=list)
    recommended_products: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class SEOAuditResult:
    """Represents the results of an SEO audit"""

    website_url: str
    audit_date: datetime
    overall_score: float  # 0-100
    technical_seo: Dict[str, Any]
    on_page_seo: Dict[str, Any]
    content_analysis: Dict[str, Any]
    competitor_analysis: Dict[str, Any]
    recommendations: List[str]
    priority_issues: List[str]
    opportunities: List[str]
    report_file_path: Optional[str] = None


@dataclass
class SEOAuditRequest:
    """Represents an SEO audit request"""

    website_url: str
    email: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    target_keywords: List[str] = field(default_factory=list)
    request_id: str = field(default_factory=lambda: f"audit_{int(time.time())}")
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=datetime.now)


class BreakingNewsWatcher:
    """Enhanced RSS Intelligence Engine for continuous knowledge base enrichment"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.feeds = self._load_rss_feeds()
        self.news_cache: Dict[str, NewsItem] = {}
        self.keywords_of_interest = self.config.get(
            "keywords",
            [
                "AI",
                "artificial intelligence",
                "machine learning",
                "automation",
                "digital marketing",
                "social media",
                "content creation",
                "YouTube",
                "affiliate marketing",
                "online business",
                "SaaS",
                "startup",
            ],
        )
        self.intelligence_db_path = self.config.get(
            "intelligence_db", "data/intelligence.db"
        )
        self.intelligence_db = (
            self.intelligence_db_path
        )  # Add missing intelligence_db attribute
        self.evidence_db_path = self.config.get(
            "evidence_db", "data/right_perspective.db"
        )
        self.trend_analysis_cache = {}

        # Get singleton hypocrisy database manager
        try:
            from backend.database.db_singleton import get_hypocrisy_db_manager

            self.hypocrisy_db = get_hypocrisy_db_manager()
        except ImportError:
            self.hypocrisy_db = None
            self.logger.warning("Database singleton not available")
        self._initialize_intelligence_db()

    def _load_rss_feeds(self) -> List[Dict[str, str]]:
        """Load RSS feeds using singleton manager to prevent redundant loading"""
        try:
            from backend.utils.rss_singleton import get_rss_feed_manager

            rss_manager = get_rss_feed_manager()
            return rss_manager.get_rss_feeds()
        except ImportError:
            self.logger.warning(
                "RSS singleton manager not available, falling back to direct loading"
            )
            return self._load_rss_feeds_direct()

    def _load_rss_feeds_direct(self) -> List[Dict[str, str]]:
        """Direct RSS feed loading (fallback method)"""
        try:
            rss_config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "rss_feeds_example.json",
            )

            if os.path.exists(rss_config_path):
                with open(rss_config_path, "r") as f:
                    config = json.load(f)
                    feeds = []
                    for feed in config.get("feeds", []):
                        if feed.get("active", True):
                            feeds.append(
                                {
                                    "url": feed["url"],
                                    "category": self._map_category(
                                        feed.get("category", "general")
                                    ),
                                    "name": feed.get("name", "Unknown"),
                                }
                            )
                    self.logger.info(
                        f"Loaded {len(feeds)} RSS feeds from configuration (direct)"
                    )
                    return feeds
            else:
                self.logger.warning("RSS config file not found, using default feeds")
                return self._get_default_feeds()

        except Exception as e:
            self.logger.error(f"Error loading RSS feeds: {e}")
            return self._get_default_feeds()

    def _map_category(self, category_str: str) -> NewsCategory:
        """Map string category to NewsCategory enum"""
        category_map = {
            "technology": NewsCategory.TECHNOLOGY,
            "business": NewsCategory.BUSINESS,
            "marketing": NewsCategory.MARKETING,
            "social_media": NewsCategory.SOCIAL_MEDIA,
            "ai": NewsCategory.AI_ML,
            "crypto": NewsCategory.CRYPTO,
            "finance": NewsCategory.FINANCE,
            "health": NewsCategory.HEALTH,
            "entertainment": NewsCategory.ENTERTAINMENT,
            "general": NewsCategory.GENERAL,
        }
        return category_map.get(category_str.lower(), NewsCategory.GENERAL)

    def _get_default_feeds(self) -> List[Dict[str, str]]:
        """Get default RSS feeds for monitoring"""
        return [
            {
                "url": "https://feeds.feedburner.com/TechCrunch",
                "category": NewsCategory.TECHNOLOGY,
                "name": "TechCrunch",
            },
            {
                "url": "https://rss.cnn.com/rss/edition.rss",
                "category": NewsCategory.GENERAL,
                "name": "CNN",
            },
            {
                "url": "https://feeds.reuters.com/reuters/businessNews",
                "category": NewsCategory.BUSINESS,
                "name": "Reuters Business",
            },
            {
                "url": "https://feeds.feedburner.com/venturebeat/SZYF",
                "category": NewsCategory.TECHNOLOGY,
                "name": "VentureBeat",
            },
            {
                "url": "https://feeds.feedburner.com/Mashable",
                "category": NewsCategory.TECHNOLOGY,
                "name": "Mashable",
            },
            {
                "url": "https://feeds.feedburner.com/socialmediaexaminer",
                "category": NewsCategory.SOCIAL_MEDIA,
                "name": "Social Media Examiner",
            },
            {
                "url": "https://feeds.feedburner.com/MarketingLand",
                "category": NewsCategory.MARKETING,
                "name": "Marketing Land",
            },
        ]

    def _initialize_intelligence_db(self):
        """Initialize intelligence database for storing processed news and trends"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.intelligence_db_path), exist_ok=True)

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            # Create tables for intelligence data
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE,
                    published_date DATETIME,
                    source TEXT,
                    category TEXT,
                    keywords TEXT,
                    sentiment_score REAL,
                    relevance_score REAL,
                    trend_strength TEXT,
                    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trend_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    frequency INTEGER,
                    trend_direction TEXT,
                    confidence_score REAL,
                    trend_score REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    time_window TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS intelligence_briefings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    summary TEXT,
                    key_points TEXT,
                    sources TEXT,
                    content TEXT,
                    priority TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    briefing_type TEXT
                )
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("Intelligence database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize intelligence database: {e}")

    async def monitor_feeds(self, duration_hours: int = 24) -> List[NewsItem]:
        """Monitor RSS feeds for specified duration"""
        if not feedparser:
            self.logger.error(
                "feedparser not available. Install with: pip install feedparser"
            )
            return []

        end_time = datetime.now() + timedelta(hours=duration_hours)
        all_news = []

        while datetime.now() < end_time:
            try:
                batch_news = await self._fetch_all_feeds()
                new_items = self._filter_new_items(batch_news)

                if new_items:
                    processed_items = await self._process_news_items(new_items)
                    all_news.extend(processed_items)
                    self.logger.info(f"Found {len(new_items)} new items")

                # Wait before next check (every 30 minutes)
                await asyncio.sleep(1800)

            except Exception as e:
                self.logger.error(f"Error monitoring feeds: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

        return all_news

    async def _fetch_all_feeds(self) -> List[NewsItem]:
        """Fetch news from all configured RSS feeds"""
        tasks = []
        for feed_config in self.feeds:
            task = asyncio.create_task(self._fetch_feed(feed_config))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_news = []

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Feed fetch error: {result}")

        return all_news

    async def _fetch_feed(self, feed_config: Dict) -> List[NewsItem]:
        """Fetch and parse a single RSS feed"""
        try:
            feed = feedparser.parse(feed_config["url"])
            news_items = []

            for entry in feed.entries:
                # Parse publication date
                pub_date = datetime.now()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])

                news_item = NewsItem(
                    title=entry.get("title", ""),
                    description=entry.get("description", ""),
                    link=entry.get("link", ""),
                    published=pub_date,
                    source=feed.feed.get("title", feed_config["url"]),
                    category=feed_config.get("category", NewsCategory.GENERAL),
                )

                news_items.append(news_item)

            return news_items

        except Exception as e:
            self.logger.error(f"Error fetching feed {feed_config['url']}: {e}")
            return []

    def _filter_new_items(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Filter out already processed news items"""
        new_items = []

        for item in news_items:
            item_key = f"{item.source}:{item.title}:{item.published.isoformat()}"
            if item_key not in self.news_cache:
                self.news_cache[item_key] = item
                new_items.append(item)

        return new_items

    async def _process_news_items(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Process news items for sentiment, keywords, relevance, and continuous knowledge base enrichment"""
        processed_items = []

        for item in news_items:
            try:
                # Extract keywords
                item.keywords = self._extract_keywords(
                    item.title + " " + item.description
                )

                # Calculate sentiment
                if TextBlob:
                    blob = TextBlob(item.title + " " + item.description)
                    item.sentiment_score = blob.sentiment.polarity

                # Calculate relevance score
                item.relevance_score = self._calculate_relevance(item)

                # Determine trend strength
                item.trend_strength = self._assess_trend_strength(item)

                # Store in intelligence database for continuous knowledge enrichment
                await self._store_news_article(item)

                # Extract facts, statistics, and quotes for evidence database
                await self._extract_and_store_evidence(item)

                processed_items.append(item)

            except Exception as e:
                self.logger.error(f"Error processing news item: {e}")
                processed_items.append(item)  # Add unprocessed item

        # Perform trend analysis after processing all items
        await self._update_trend_analysis(processed_items)

        return processed_items

    async def _update_trend_analysis(self, news_items: List[NewsItem]):
        """Update trend analysis with new news items for emerging topic detection"""
        try:
            import sqlite3
            from collections import Counter

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            # Aggregate keywords from all items
            all_keywords = []
            for item in news_items:
                all_keywords.extend(item.keywords)

            # Count keyword frequencies
            keyword_counts = Counter(all_keywords)

            # Update trend analysis table
            current_time = datetime.now().isoformat()
            for keyword, count in keyword_counts.items():
                # Calculate trend strength based on frequency and recency
                trend_score = min(count * 0.1, 1.0)  # Cap at 1.0

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO trend_analysis 
                    (keyword, frequency, trend_score, last_updated, time_window)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (keyword, count, trend_score, current_time, "hourly"),
                )

            # Store intelligence briefing for Planner Agent
            trending_keywords = [kw for kw, count in keyword_counts.most_common(10)]
            briefing_content = {
                "trending_topics": trending_keywords,
                "total_articles_processed": len(news_items),
                "high_relevance_count": len(
                    [item for item in news_items if item.relevance_score > 0.7]
                ),
                "sentiment_summary": {
                    "positive": len(
                        [item for item in news_items if item.sentiment_score > 0.1]
                    ),
                    "negative": len(
                        [item for item in news_items if item.sentiment_score < -0.1]
                    ),
                    "neutral": len(
                        [
                            item
                            for item in news_items
                            if -0.1 <= item.sentiment_score <= 0.1
                        ]
                    ),
                },
            }

            cursor.execute(
                """
                INSERT INTO intelligence_briefings 
                (briefing_type, content, created_at, priority)
                VALUES (?, ?, ?, ?)
            """,
                (
                    "trend_analysis",
                    json.dumps(briefing_content),
                    current_time,
                    "high" if len(trending_keywords) > 5 else "medium",
                ),
            )

            conn.commit()
            conn.close()

            self.logger.info(
                f"Updated trend analysis with {len(keyword_counts)} keywords"
            )

        except Exception as e:
            self.logger.error(f"Error updating trend analysis: {e}")

    async def _store_news_article(self, item: NewsItem):
        """Store news article in intelligence database for knowledge base enrichment"""
        try:
            import sqlite3

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO news_articles 
                (title, description, url, published_date, source, category, sentiment_score, keywords, relevance_score, trend_strength)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item.title,
                    item.description,
                    item.link,
                    item.published.isoformat(),
                    item.source,
                    item.category.value,
                    item.sentiment_score,
                    ",".join(item.keywords),
                    item.relevance_score,
                    item.trend_strength.value,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error storing news article: {e}")

    async def _extract_and_store_evidence(self, item: NewsItem):
        """Extract facts, statistics, and quotes from news item and store in evidence database"""
        try:
            import re
            import sqlite3

            # Connect to right_perspective.db evidence table
            conn = sqlite3.connect("data/right_perspective.db")
            cursor = conn.cursor()

            full_text = f"{item.title} {item.description}"

            # Extract statistics (numbers with context)
            stats_pattern = r"(\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|million|billion|thousand|users|people|companies|dollars|\$)?)"
            statistics = re.findall(stats_pattern, full_text, re.IGNORECASE)

            # Extract quotes (text in quotation marks)
            quotes_pattern = r'["\u201c]([^"\u201d]+)["\u201d]'
            quotes = re.findall(quotes_pattern, full_text)

            # Store extracted evidence
            for stat in statistics:
                cursor.execute(
                    """
                    INSERT INTO evidence (claim, source, date_added, category, credibility_score)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        f"Statistical data: {stat}",
                        f"{item.source} - {item.link}",
                        datetime.now().isoformat(),
                        "statistics",
                        item.relevance_score,
                    ),
                )

            for quote in quotes:
                if len(quote.strip()) > 10:  # Filter out short quotes
                    cursor.execute(
                        """
                        INSERT INTO evidence (claim, source, date_added, category, credibility_score)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            f"Quote: {quote.strip()}",
                            f"{item.source} - {item.link}",
                            datetime.now().isoformat(),
                            "quote",
                            item.relevance_score,
                        ),
                    )

            # Store key facts from title and description
            if item.relevance_score > 0.7:  # Only store high-relevance facts
                cursor.execute(
                    """
                    INSERT INTO evidence (claim, source, date_added, category, credibility_score)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        item.title,
                        f"{item.source} - {item.link}",
                        datetime.now().isoformat(),
                        "fact",
                        item.relevance_score,
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error extracting and storing evidence: {e}")

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r"\b\w+\b", text.lower())

        # Filter for relevant keywords
        relevant_keywords = []
        for keyword in self.keywords_of_interest:
            if keyword.lower() in text.lower():
                relevant_keywords.append(keyword)

        return relevant_keywords

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current trending topics for Planner Agent dynamic scheduling"""
        try:
            import sqlite3

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT keyword, frequency, trend_score, last_updated
                FROM trend_analysis
                WHERE datetime(last_updated) > datetime('now', '-24 hours')
                ORDER BY trend_score DESC, frequency DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = cursor.fetchall()
            conn.close()

            trending_topics = []
            for row in results:
                trending_topics.append(
                    {
                        "keyword": row[0],
                        "frequency": row[1],
                        "trend_score": row[2],
                        "last_updated": row[3],
                    }
                )

            return trending_topics

        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []

    def get_latest_intelligence_briefing(
        self, briefing_type: str = None
    ) -> Dict[str, Any]:
        """Get latest intelligence briefing for Content Agent live briefing prompts"""
        try:
            import sqlite3

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            if briefing_type:
                cursor.execute(
                    """
                    SELECT briefing_type, content, created_at, priority
                    FROM intelligence_briefings
                    WHERE briefing_type = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (briefing_type,),
                )
            else:
                cursor.execute(
                    """
                    SELECT briefing_type, content, created_at, priority
                    FROM intelligence_briefings
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                )

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "briefing_type": result[0],
                    "content": json.loads(result[1]),
                    "created_at": result[2],
                    "priority": result[3],
                }

            return {}

        except Exception as e:
            self.logger.error(f"Error getting intelligence briefing: {e}")
            return {}

    def get_topic_headlines(self, topic: str, limit: int = 5) -> List[Dict[str, str]]:
        """Get latest headlines for a specific topic for Content Agent live briefing"""
        try:
            import sqlite3

            conn = sqlite3.connect(self.intelligence_db_path)
            cursor = conn.cursor()

            # Search for articles containing the topic in title, description, or keywords
            cursor.execute(
                """
                SELECT title, description, source, url, published_date
                FROM news_articles
                WHERE (title LIKE ? OR description LIKE ? OR keywords LIKE ?)
                AND datetime(published) > datetime('now', '-48 hours')
                ORDER BY relevance_score DESC, published DESC
                LIMIT ?
            """,
                (f"%{topic}%", f"%{topic}%", f"%{topic}%", limit),
            )

            results = cursor.fetchall()
            conn.close()

            headlines = []
            for row in results:
                headlines.append(
                    {
                        "title": row[0],
                        "description": (
                            row[1][:200] + "..." if len(row[1]) > 200 else row[1]
                        ),
                        "source": row[2],
                        "link": row[3],
                        "published": row[4],
                    }
                )

            return headlines

        except Exception as e:
            self.logger.error(f"Error getting topic headlines: {e}")
            return []

    def _calculate_relevance(self, item: NewsItem) -> float:
        """Calculate relevance score based on keywords and category"""
        score = 0.0

        # Base score by category
        category_scores = {
            NewsCategory.TECHNOLOGY: 0.8,
            NewsCategory.BUSINESS: 0.7,
            NewsCategory.MARKETING: 0.9,
            NewsCategory.SOCIAL_MEDIA: 0.9,
            NewsCategory.AI_ML: 1.0,
            NewsCategory.GENERAL: 0.3,
        }

        score += category_scores.get(item.category, 0.3)

        # Keyword relevance
        keyword_score = len(item.keywords) * 0.1
        score += min(keyword_score, 0.5)  # Cap at 0.5

        # Recency bonus
        hours_old = (datetime.now() - item.published).total_seconds() / 3600
        if hours_old < 1:
            score += 0.3
        elif hours_old < 6:
            score += 0.2
        elif hours_old < 24:
            score += 0.1

        return min(score, 1.0)

    def _assess_trend_strength(self, item: NewsItem) -> TrendStrength:
        """Assess the trend strength of a news item"""
        # Simple heuristic - can be enhanced with social media data
        if item.relevance_score > 0.8 and len(item.keywords) > 3:
            return TrendStrength.STRONG
        elif item.relevance_score > 0.6 and len(item.keywords) > 2:
            return TrendStrength.MODERATE
        elif item.relevance_score > 0.4:
            return TrendStrength.WEAK
        else:
            return TrendStrength.WEAK

    def get_trending_keywords(self, hours: int = 24) -> Dict[str, int]:
        """Get trending keywords from recent news"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_items = [
            item for item in self.news_cache.values() if item.published > cutoff_time
        ]

        # Count keyword occurrences
        keyword_counts = {}
        for item in recent_items:
            for keyword in item.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Sort by frequency
        return dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))

    async def scan_for_hypocrisy(self, hours_back: int = 48) -> List[Dict[str, Any]]:
        """Proactively scan political RSS feeds for contradictory statements from public figures"""
        try:
            # Get recent political news items
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            political_items = [
                item
                for item in self.news_cache.values()
                if item.published > cutoff_time
                and (
                    "politic" in item.title.lower()
                    or "politic" in item.description.lower()
                )
            ]

            hypocrisy_findings = []

            # Extract public figures from recent news
            public_figures = self._extract_public_figures(political_items)

            for figure in public_figures:
                # Find contradictory statements for this figure
                contradictions = await self._find_contradictory_statements(
                    figure, political_items
                )

                for contradiction in contradictions:
                    # Calculate contradiction score
                    score = self._calculate_contradiction_score(contradiction)

                    if score > 0.6:  # Only high-confidence contradictions
                        hypocrisy_finding = {
                            "figure": figure,
                            "contradiction_score": score,
                            "topic": self._extract_contradiction_topic(contradiction),
                            "statement_1": contradiction["statement_1"],
                            "statement_2": contradiction["statement_2"],
                            "source_1": contradiction["source_1"],
                            "source_2": contradiction["source_2"],
                            "date_1": contradiction["date_1"],
                            "date_2": contradiction["date_2"],
                            "time_gap_days": (
                                contradiction["date_2"] - contradiction["date_1"]
                            ).days,
                            "discovered_at": datetime.now().isoformat(),
                        }

                        # Store in hypocrisy database
                        await self._store_hypocrisy_finding(hypocrisy_finding)
                        hypocrisy_findings.append(hypocrisy_finding)

            self.logger.info(
                f"Discovered {len(hypocrisy_findings)} hypocrisy opportunities"
            )
            return hypocrisy_findings

        except Exception as e:
            self.logger.error(f"Error scanning for hypocrisy: {e}")
            return []

    def _extract_public_figures(self, news_items: List[NewsItem]) -> List[str]:
        """Extract public figure names from news items"""
        figures = set()

        # Common political figure patterns
        political_keywords = [
            "president",
            "senator",
            "congressman",
            "governor",
            "mayor",
            "minister",
            "secretary",
            "representative",
            "candidate",
        ]

        for item in news_items:
            text = f"{item.title} {item.description}".lower()

            # Simple name extraction (can be enhanced with NER)
            words = text.split()
            for i, word in enumerate(words):
                if word in political_keywords and i + 1 < len(words):
                    # Get the next 1-2 words as potential name
                    name_parts = []
                    for j in range(1, min(3, len(words) - i)):
                        next_word = words[i + j]
                        if next_word.istitle() and next_word.isalpha():
                            name_parts.append(next_word)
                        else:
                            break

                    if name_parts:
                        figures.add(" ".join(name_parts))

        return list(figures)[:20]  # Limit to top 20 figures

    async def _find_contradictory_statements(
        self, figure: str, recent_items: List[NewsItem]
    ) -> List[Dict[str, Any]]:
        """Find contradictory statements for a specific public figure"""
        contradictions = []

        # Get statements from this figure in recent news
        figure_statements = []
        for item in recent_items:
            if (
                figure.lower() in item.title.lower()
                or figure.lower() in item.description.lower()
            ):
                figure_statements.append(
                    {
                        "text": item.description,
                        "source": item.source,
                        "date": item.published,
                        "link": item.link,
                        "title": item.title,
                    }
                )

        # Compare statements for contradictions
        for i, stmt1 in enumerate(figure_statements):
            for stmt2 in figure_statements[i + 1 :]:
                # Check if statements are about the same topic but contradictory
                common_words = self._find_common_important_words(
                    stmt1["text"], stmt2["text"]
                )

                if len(common_words) >= 2:  # Same topic
                    # Simple contradiction detection (can be enhanced with NLP)
                    contradiction_indicators = [
                        ("support", "oppose"),
                        ("agree", "disagree"),
                        ("yes", "no"),
                        ("will", "will not"),
                        ("should", "should not"),
                        ("favor", "against"),
                    ]

                    text1_lower = stmt1["text"].lower()
                    text2_lower = stmt2["text"].lower()

                    for pos, neg in contradiction_indicators:
                        if (pos in text1_lower and neg in text2_lower) or (
                            neg in text1_lower and pos in text2_lower
                        ):
                            contradictions.append(
                                {
                                    "statement_1": stmt1["text"][:200],
                                    "statement_2": stmt2["text"][:200],
                                    "source_1": stmt1["source"],
                                    "source_2": stmt2["source"],
                                    "date_1": stmt1["date"],
                                    "date_2": stmt2["date"],
                                    "link_1": stmt1["link"],
                                    "link_2": stmt2["link"],
                                    "common_topic": common_words,
                                }
                            )
                            break

        return contradictions

    def _calculate_contradiction_score(self, contradiction: Dict[str, Any]) -> float:
        """Calculate how strong/clear the contradiction is"""
        score = 0.5  # Base score

        # Time gap factor (more recent = higher score)
        time_gap = abs((contradiction["date_2"] - contradiction["date_1"]).days)
        if time_gap < 30:
            score += 0.3
        elif time_gap < 90:
            score += 0.2
        elif time_gap < 365:
            score += 0.1

        # Source credibility (different sources = higher score)
        if contradiction["source_1"] != contradiction["source_2"]:
            score += 0.2

        # Topic relevance (more common words = clearer contradiction)
        common_topic_count = len(contradiction.get("common_topic", []))
        score += min(common_topic_count * 0.05, 0.2)

        return min(score, 1.0)

    def _find_common_important_words(self, text1: str, text2: str) -> List[str]:
        """Find important words common to both texts"""
        # Simple keyword extraction (can be enhanced with TF-IDF)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
        }

        words1 = set(
            word.lower().strip('.,!?"')
            for word in text1.split()
            if len(word) > 3 and word.lower() not in stop_words
        )
        words2 = set(
            word.lower().strip('.,!?"')
            for word in text2.split()
            if len(word) > 3 and word.lower() not in stop_words
        )

        return list(words1.intersection(words2))

    def _extract_contradiction_topic(self, contradiction: Dict[str, Any]) -> str:
        """Extract the main topic of the contradiction"""
        common_words = contradiction.get("common_topic", [])
        if common_words:
            return " ".join(common_words[:3])  # Use top 3 common words
        return "general policy"

    async def _store_hypocrisy_finding(self, finding: Dict[str, Any]) -> None:
        """Store hypocrisy finding in the database using the database manager"""
        try:
            if not self.hypocrisy_db:
                self.logger.warning("Hypocrisy database manager not available")
                return

            # Convert finding dict to HypocrisyFinding dataclass
            hypocrisy_finding = HypocrisyFinding(
                subject_name=finding["figure"],
                subject_type="politician",  # Default type for political figures
                statement_1=finding["statement_1"],
                statement_2=finding["statement_2"],
                context_1=f"Source: {finding['source_1']}",
                context_2=f"Source: {finding['source_2']}",
                date_1=finding["date_1"],
                date_2=finding["date_2"],
                source_1=finding["source_1"],
                source_2=finding["source_2"],
                contradiction_type="temporal",  # Policy changes over time - valid constraint value
                severity_score=max(
                    1, min(10, int(finding["contradiction_score"] * 10) or 1)
                ),  # Convert to 1-10 scale, ensure >= 1
                confidence_score=finding[
                    "contradiction_score"
                ],  # Keep as 0.0-1.0 range
                verification_status="pending",
                evidence_links=[
                    link
                    for link in [finding.get("link_1", ""), finding.get("link_2", "")]
                    if link
                ],
                tags=[finding["topic"]] if finding.get("topic") else [],
                analysis_notes=f"Time gap: {finding['time_gap_days']} days",
                public_impact_score=max(
                    1, min(10, int(finding["contradiction_score"] * 10) or 1)
                ),
                media_coverage_count=1,  # At least one source
                social_media_mentions=0,  # Default
                fact_check_results={"status": "pending"},
            )

            # Store using the database manager
            finding_id = self.hypocrisy_db.store_finding(hypocrisy_finding)
            if finding_id:
                self.logger.info(f"Stored hypocrisy finding with ID: {finding_id}")
            else:
                self.logger.error("Failed to store hypocrisy finding")

        except Exception as e:
            self.logger.error(f"Error storing hypocrisy finding: {e}")

    def get_hypocrisy_content_opportunities(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get unused hypocrisy findings for content creation"""
        try:
            if not self.hypocrisy_db:
                self.logger.warning(
                    "Hypocrisy database manager not available, falling back to direct SQLite"
                )
                # Fallback to direct SQLite access
                import sqlite3

                conn = sqlite3.connect("data/right_perspective.db")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, figure, topic, contradiction_score, statement_1, statement_2,
                           source_1, source_2, date_1, date_2, time_gap_days, discovered_at
                    FROM hypocrisy_findings
                    WHERE content_used = FALSE
                    ORDER BY contradiction_score DESC, discovered_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                results = cursor.fetchall()
                conn.close()

                opportunities = []
                for row in results:
                    opportunities.append(
                        {
                            "id": row[0],
                            "figure": row[1],
                            "topic": row[2],
                            "contradiction_score": row[3],
                            "statement_1": row[4],
                            "statement_2": row[5],
                            "source_1": row[6],
                            "source_2": row[7],
                            "date_1": row[8],
                            "date_2": row[9],
                            "time_gap_days": row[10],
                            "discovered_at": row[11],
                        }
                    )

                return opportunities

            # Use the new database manager
            db_opportunities = self.hypocrisy_db.get_content_opportunities(limit=limit)

            # Convert to the expected format for backward compatibility
            opportunities = []
            for opp in db_opportunities:
                opportunities.append(
                    {
                        "id": opp["id"],
                        "figure": opp["subject_name"],
                        "topic": opp["tags"],
                        "contradiction_score": opp["severity_score"]
                        / 10.0,  # Convert back to 0-1 scale
                        "statement_1": opp["statement_1"],
                        "statement_2": opp["statement_2"],
                        "source_1": opp["source_1"],
                        "source_2": opp["source_2"],
                        "date_1": opp["date_1"],
                        "date_2": opp["date_2"],
                        "time_gap_days": (
                            (opp["date_2"] - opp["date_1"]).days
                            if opp["date_2"] and opp["date_1"]
                            else 0
                        ),
                        "discovered_at": opp["created_at"],
                    }
                )

            return opportunities

        except Exception as e:
            self.logger.error(f"Error getting hypocrisy opportunities: {e}")
            return []

    def mark_hypocrisy_content_used(self, finding_id: int) -> bool:
        """Mark a hypocrisy finding as used for content creation"""
        try:
            if not self.hypocrisy_db:
                self.logger.warning(
                    "Hypocrisy database manager not available, falling back to direct SQLite"
                )
                # Fallback to direct SQLite access
                import sqlite3

                conn = sqlite3.connect("data/right_perspective.db")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE hypocrisy_findings
                    SET content_used = TRUE
                    WHERE id = ?
                """,
                    (finding_id,),
                )

                conn.commit()
                conn.close()

                return True

            # Use the new database manager
            success = self.hypocrisy_db.mark_content_used(finding_id)
            if success:
                self.logger.info(f"Marked hypocrisy finding {finding_id} as used")
            return success

        except Exception as e:
            self.logger.error(f"Error marking hypocrisy content as used: {e}")
            return False

    def get_latest_news(
        self, limit: int = 10, category: Optional[NewsCategory] = None
    ) -> List[NewsItem]:
        """Get the latest news items from the database"""
        try:
            if not self.intelligence_db:
                self.logger.warning("Intelligence database not available")
                return []

            conn = sqlite3.connect(self.intelligence_db)
            cursor = conn.cursor()

            # Build query based on category filter
            if category:
                query = """
                    SELECT title, description, url, published_date, source, category, 
                           sentiment_score, keywords, trend_strength, relevance_score
                    FROM news_articles 
                    WHERE category = ?
                    ORDER BY published_date DESC 
                    LIMIT ?
                """
                cursor.execute(query, (category.value, limit))
            else:
                query = """
                    SELECT title, description, url, published_date, source, category, 
                           sentiment_score, keywords, trend_strength, relevance_score
                    FROM news_articles 
                    ORDER BY published_date DESC 
                    LIMIT ?
                """
                cursor.execute(query, (limit,))

            results = cursor.fetchall()
            conn.close()

            # Convert results to NewsItem objects
            news_items = []
            for row in results:
                try:
                    # Parse keywords from JSON string
                    keywords = json.loads(row[7]) if row[7] else []

                    # Parse published date
                    published = (
                        datetime.fromisoformat(row[3]) if row[3] else datetime.now()
                    )

                    # Map category string to enum
                    category_enum = (
                        self._map_category(row[5]) if row[5] else NewsCategory.GENERAL
                    )

                    # Map trend strength string to enum
                    trend_strength = (
                        TrendStrength(row[8]) if row[8] else TrendStrength.WEAK
                    )

                    news_item = NewsItem(
                        title=row[0] or "",
                        description=row[1] or "",
                        link=row[2] or "",
                        published=published,
                        source=row[4] or "",
                        category=category_enum,
                        sentiment_score=float(row[6]) if row[6] else 0.0,
                        keywords=keywords,
                        trend_strength=trend_strength,
                        relevance_score=float(row[9]) if row[9] else 0.0,
                    )
                    news_items.append(news_item)

                except Exception as e:
                    self.logger.warning(f"Error parsing news item: {e}")
                    continue

            return news_items

        except Exception as e:
            self.logger.error(f"Error getting latest news: {e}")
            return []


class CompetitorAnalyzer:
    """Analyzes YouTube competitors similar to TubeBuddy/VidIQ"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_key = self.config.get("youtube_api_key", "")
        self.channels_cache: Dict[str, CompetitorChannel] = {}
        self.logger = logging.getLogger(__name__)

    async def analyze_niche(
        self, niche_keywords: List[str], max_channels: int = 50
    ) -> List[CompetitorChannel]:
        """Analyze competitors in a specific niche"""
        if not requests:
            self.logger.error("requests library not available")
            return []

        try:
            # Search for channels in the niche
            channel_ids = await self._search_channels_by_keywords(
                niche_keywords, max_channels
            )

            # Analyze each channel
            analyzed_channels = []
            for channel_id in channel_ids:
                channel_data = await self._analyze_channel(channel_id)
                if channel_data:
                    analyzed_channels.append(channel_data)

            # Calculate opportunity scores
            self._calculate_opportunity_scores(analyzed_channels)

            return sorted(
                analyzed_channels, key=lambda x: x.opportunity_score, reverse=True
            )

        except Exception as e:
            self.logger.error(f"Error analyzing niche: {e}")
            return []

    async def _search_channels_by_keywords(
        self, keywords: List[str], max_results: int
    ) -> List[str]:
        """Search for YouTube channels by keywords using YouTube Data API"""
        from backend.secret_store import SecretStore

        try:
            # Get YouTube API key from secure storage
            with SecretStore(
                self.config.get("secrets_db", "data/secrets.sqlite")
            ) as store:
                api_key = store.get_secret("YOUTUBE_API_KEY")
                if not api_key:
                    self.logger.error("YouTube API key not configured in secret store")
                    return []

            if not requests:
                self.logger.error("requests library not available")
                return []

            channel_ids = set()
            base_url = "https://www.googleapis.com/youtube/v3"

            # Search for channels using each keyword
            for keyword in keywords[
                :3
            ]:  # Limit to first 3 keywords to avoid quota exhaustion
                try:
                    # Search for channels
                    search_response = requests.get(
                        f"{base_url}/search",
                        params={
                            "part": "snippet",
                            "type": "channel",
                            "q": keyword,
                            "maxResults": min(20, max_results),
                            "order": "relevance",
                            "key": api_key,
                        },
                        timeout=10,
                    )

                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        items = search_data.get("items", [])

                        for item in items:
                            channel_id = item.get("id", {}).get("channelId")
                            if channel_id:
                                channel_ids.add(channel_id)

                                # Stop if we have enough channels
                                if len(channel_ids) >= max_results:
                                    break
                    else:
                        self.logger.warning(
                            f"YouTube search API error for keyword '{keyword}': {search_response.status_code}"
                        )

                except Exception as e:
                    self.logger.warning(f"Error searching for keyword '{keyword}': {e}")
                    continue

                # Stop if we have enough channels
                if len(channel_ids) >= max_results:
                    break

            # If no channels found through search, try some popular channels in common niches
            if not channel_ids:
                self.logger.warning(
                    "No channels found through search, using fallback popular channels"
                )
                fallback_channels = [
                    "UCBJycsmduvYEL83R_U4JriQ",  # Marques Brownlee (Tech)
                    "UCJ0-OtVpF0wOKEqT2Z1HEtA",  # ElectroBOOM (Engineering)
                    "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed (Education)
                    "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie (Gaming/Entertainment)
                    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast (Entertainment)
                    "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers (Tech)
                    "UCEOXxzW2vU0P-0THehuIIeg",  # Captain Disillusion (Science)
                    "UCHnyfMqiRRG1u-2MsSQLbXA",  # Veritasium (Science)
                    "UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt (Science)
                    "UCR1IuLEqb6UEA_zQ81kwXfg",  # Real Engineering (Engineering)
                ]
                return fallback_channels[: min(max_results, len(fallback_channels))]

            return list(channel_ids)[:max_results]

        except Exception as e:
            self.logger.error(f"Error searching channels by keywords: {e}")
            return []

    async def _analyze_channel(self, channel_id: str) -> Optional[CompetitorChannel]:
        """Analyze a single YouTube channel"""
        try:
            # Check cache first
            if channel_id in self.channels_cache:
                cached_channel = self.channels_cache[channel_id]
                # Return cached data if less than 24 hours old
                if (datetime.now() - cached_channel.last_analyzed).hours < 24:
                    return cached_channel

            # Fetch real channel data using YouTube Data API
            channel_data = self._fetch_channel_data(channel_id)

            if channel_data:
                competitor_channel = CompetitorChannel(
                    channel_id=channel_id,
                    channel_name=channel_data["name"],
                    subscriber_count=channel_data["subscribers"],
                    total_views=channel_data["total_views"],
                    video_count=channel_data["video_count"],
                    upload_frequency=channel_data["upload_frequency"],
                    average_views=channel_data["average_views"],
                    engagement_rate=channel_data["engagement_rate"],
                    niche_keywords=channel_data["keywords"],
                    content_themes=channel_data["themes"],
                )

                # Cache the result
                self.channels_cache[channel_id] = competitor_channel
                return competitor_channel

        except Exception as e:
            self.logger.error(f"Error analyzing channel {channel_id}: {e}")

        return None

    def _fetch_channel_data(self, channel_id: str) -> Optional[Dict]:
        """Fetch real YouTube channel data using YouTube Data API v3"""
        from backend.secret_store import SecretStore

        try:
            # Get YouTube API key from secure storage
            with SecretStore(
                self.config.get("secrets_db", "data/secrets.sqlite")
            ) as store:
                api_key = store.get_secret("YOUTUBE_API_KEY")
                if not api_key:
                    self.logger.error("YouTube API key not configured in secret store")
                    return None

            if not requests:
                self.logger.error("requests library not available")
                return None

            # Fetch channel statistics from YouTube Data API
            base_url = "https://www.googleapis.com/youtube/v3"

            # Get channel details
            channel_response = requests.get(
                f"{base_url}/channels",
                params={
                    "part": "snippet,statistics,brandingSettings",
                    "id": channel_id,
                    "key": api_key,
                },
                timeout=10,
            )

            if channel_response.status_code != 200:
                self.logger.error(
                    f"YouTube API error for channel {channel_id}: {channel_response.status_code}"
                )
                return None

            channel_data = channel_response.json()
            if not channel_data.get("items"):
                self.logger.warning(f"No data found for channel {channel_id}")
                return None

            channel_info = channel_data["items"][0]
            snippet = channel_info.get("snippet", {})
            statistics = channel_info.get("statistics", {})

            # Get recent videos to calculate upload frequency and engagement
            videos_response = requests.get(
                f"{base_url}/search",
                params={
                    "part": "snippet",
                    "channelId": channel_id,
                    "type": "video",
                    "order": "date",
                    "maxResults": 50,
                    "key": api_key,
                },
                timeout=10,
            )

            upload_frequency = 0.0
            average_views = 0
            engagement_rate = 0.0
            keywords = []
            themes = []

            if videos_response.status_code == 200:
                videos_data = videos_response.json()
                video_items = videos_data.get("items", [])

                if video_items:
                    # Calculate upload frequency (videos per week)
                    video_ids = [item["id"]["videoId"] for item in video_items[:10]]

                    # Get detailed video statistics
                    video_stats_response = requests.get(
                        f"{base_url}/videos",
                        params={
                            "part": "statistics,snippet",
                            "id": ",".join(video_ids),
                            "key": api_key,
                        },
                        timeout=10,
                    )

                    if video_stats_response.status_code == 200:
                        video_stats = video_stats_response.json()
                        video_details = video_stats.get("items", [])

                        if video_details:
                            # Calculate average views and engagement
                            total_views = 0
                            total_engagement = 0

                            for video in video_details:
                                stats = video.get("statistics", {})
                                views = int(stats.get("viewCount", 0))
                                likes = int(stats.get("likeCount", 0))
                                comments = int(stats.get("commentCount", 0))

                                total_views += views
                                if views > 0:
                                    total_engagement += (likes + comments) / views

                                # Extract keywords from video titles and descriptions
                                video_snippet = video.get("snippet", {})
                                title = video_snippet.get("title", "").lower()
                                description = video_snippet.get(
                                    "description", ""
                                ).lower()

                                # Simple keyword extraction
                                for word in title.split():
                                    if len(word) > 3 and word not in keywords:
                                        keywords.append(word)

                            average_views = (
                                total_views // len(video_details)
                                if video_details
                                else 0
                            )
                            engagement_rate = (
                                total_engagement / len(video_details)
                                if video_details
                                else 0.0
                            )

                    # Calculate upload frequency based on recent videos
                    if len(video_items) >= 2:
                        from datetime import datetime

                        try:
                            latest_date = datetime.fromisoformat(
                                video_items[0]["snippet"]["publishedAt"].replace(
                                    "Z", "+00:00"
                                )
                            )
                            oldest_date = datetime.fromisoformat(
                                video_items[-1]["snippet"]["publishedAt"].replace(
                                    "Z", "+00:00"
                                )
                            )
                            days_diff = (latest_date - oldest_date).days
                            if days_diff > 0:
                                upload_frequency = (
                                    len(video_items) * 7
                                ) / days_diff  # videos per week
                        except Exception as e:
                            self.logger.warning(
                                f"Error calculating upload frequency: {e}"
                            )
                            upload_frequency = 1.0

                    # Extract themes from channel description and video categories
                    channel_description = snippet.get("description", "").lower()
                    if (
                        "tech" in channel_description
                        or "technology" in channel_description
                    ):
                        themes.append("Technology")
                    if "review" in channel_description:
                        themes.append("Reviews")
                    if (
                        "education" in channel_description
                        or "tutorial" in channel_description
                    ):
                        themes.append("Education")
                    if "gaming" in channel_description or "game" in channel_description:
                        themes.append("Gaming")
                    if "music" in channel_description:
                        themes.append("Music")
                    if "entertainment" in channel_description:
                        themes.append("Entertainment")

                    if not themes:
                        themes = ["General Content"]

            # Limit keywords to top 10 most relevant
            keywords = keywords[:10] if keywords else ["content", "video", "youtube"]

            return {
                "name": snippet.get("title", f"Channel_{channel_id[:8]}"),
                "subscribers": int(statistics.get("subscriberCount", 0)),
                "total_views": int(statistics.get("viewCount", 0)),
                "video_count": int(statistics.get("videoCount", 0)),
                "upload_frequency": max(
                    upload_frequency, 0.1
                ),  # Minimum 0.1 videos per week
                "average_views": average_views,
                "engagement_rate": min(engagement_rate, 1.0),  # Cap at 100%
                "keywords": keywords,
                "themes": themes,
            }

        except Exception as e:
            self.logger.error(
                f"Error fetching YouTube data for channel {channel_id}: {e}"
            )
            return None

    def _calculate_opportunity_scores(self, channels: List[CompetitorChannel]) -> None:
        """Calculate opportunity scores for channels"""
        if not channels:
            return

        # Normalize metrics for scoring
        subscriber_counts = [c.subscriber_count for c in channels]
        engagement_rates = [c.engagement_rate for c in channels]
        upload_frequencies = [c.upload_frequency for c in channels]

        max_subs = max(subscriber_counts) if subscriber_counts else 1
        max_engagement = max(engagement_rates) if engagement_rates else 1
        max_frequency = max(upload_frequencies) if upload_frequencies else 1

        for channel in channels:
            # Lower subscriber count = higher opportunity (less saturated)
            sub_score = 1.0 - (channel.subscriber_count / max_subs)

            # Higher engagement rate = better niche
            engagement_score = channel.engagement_rate / max_engagement

            # Moderate upload frequency is optimal
            frequency_score = 1.0 - abs(channel.upload_frequency - 2.0) / max_frequency

            # Combine scores
            channel.opportunity_score = (
                sub_score * 0.4 + engagement_score * 0.4 + frequency_score * 0.2
            )

    def find_content_gaps(self, channels: List[CompetitorChannel]) -> List[str]:
        """Identify content gaps in the analyzed niche"""
        all_themes = set()
        for channel in channels:
            all_themes.update(channel.content_themes)

        # Common content themes that might be missing
        potential_themes = [
            "Beginner Tutorials",
            "Advanced Techniques",
            "Tool Reviews",
            "Industry News",
            "Behind the Scenes",
            "Q&A Sessions",
            "Collaboration Videos",
            "Live Streams",
            "Short Form Content",
            "Educational Series",
            "Case Studies",
            "Interviews",
        ]

        # Find gaps
        content_gaps = [theme for theme in potential_themes if theme not in all_themes]
        return content_gaps


class MarketValidator:
    """Validates market opportunities for digital products"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    async def validate_product_idea(
        self, product_concept: str, target_keywords: List[str]
    ) -> MarketOpportunity:
        """Validate a digital product idea"""
        try:
            # Analyze search volume and competition
            search_data = await self._analyze_search_metrics(target_keywords)

            # Assess market trends
            trend_data = await self._analyze_market_trends(
                product_concept, target_keywords
            )

            # Evaluate monetization potential
            monetization_score = self._assess_monetization_potential(
                product_concept, search_data
            )

            # Identify target audience
            target_audience = self._identify_target_audience(
                product_concept, target_keywords
            )

            # Find content gaps
            content_gaps = await self._identify_content_gaps(target_keywords)

            # Generate product recommendations
            recommended_products = self._generate_product_recommendations(
                product_concept, search_data
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                search_data, trend_data, monetization_score
            )

            opportunity = MarketOpportunity(
                niche=product_concept,
                keywords=target_keywords,
                search_volume=search_data["total_volume"],
                competition_level=search_data["competition_level"],
                trend_direction=trend_data["direction"],
                monetization_potential=monetization_score,
                target_audience=target_audience,
                content_gaps=content_gaps,
                recommended_products=recommended_products,
                confidence_score=confidence_score,
            )

            return opportunity

        except Exception as e:
            self.logger.error(f"Error validating product idea: {e}")
            # Return default opportunity with low confidence
            return MarketOpportunity(
                niche=product_concept,
                keywords=target_keywords,
                search_volume=0,
                competition_level="unknown",
                trend_direction="unknown",
                monetization_potential=0.0,
                target_audience="unknown",
                confidence_score=0.0,
            )

    async def _analyze_search_metrics(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze search volume and competition for keywords using Google Ads API"""
        from backend.secret_store import SecretStore

        try:
            # Get Google Ads API credentials from secure storage
            with SecretStore(
                self.config.get("secrets_db", "data/secrets.sqlite")
            ) as store:
                api_key = store.get_secret("GOOGLE_ADS_API_KEY")
                customer_id = store.get_secret("GOOGLE_ADS_CUSTOMER_ID")
                developer_token = store.get_secret("GOOGLE_ADS_DEVELOPER_TOKEN")

                if not all([api_key, customer_id, developer_token]):
                    self.logger.error(
                        "Google Ads API credentials not configured in secret store"
                    )
                    raise ValueError("Missing Google Ads API credentials")

            if not requests:
                self.logger.error("requests library not available")
                raise ImportError("requests library required for API calls")

            # Use Google Keyword Planner API to get real search volume data
            headers = {
                "Authorization": f"Bearer {api_key}",
                "developer-token": developer_token,
                "Content-Type": "application/json",
            }

            # Prepare keyword ideas request
            keyword_ideas_request = {
                "customerId": customer_id,
                "keywordPlanIdeaService": {
                    "generateKeywordIdeas": {
                        "keywordSeed": {
                            "keywords": keywords[
                                :10
                            ]  # Limit to 10 keywords per request
                        },
                        "geoTargetConstants": [
                            "geoTargetConstants/2840"
                        ],  # United States
                        "language": "languageConstants/1000",  # English
                        "keywordPlanNetwork": "GOOGLE_SEARCH",
                    }
                },
            }

            # Make API request to Google Ads
            response = requests.post(
                f"https://googleads.googleapis.com/v14/customers/{customer_id}/keywordPlanIdeas:generateKeywordIdeas",
                headers=headers,
                json=keyword_ideas_request,
                timeout=30,
            )

            if response.status_code != 200:
                self.logger.error(
                    f"Google Ads API error: {response.status_code} - {response.text}"
                )
                raise ValueError(
                    f"API request failed with status {response.status_code}"
                )

            data = response.json()
            results = data.get("results", [])

            total_volume = 0
            competition_scores = []

            for result in results:
                keyword_idea = result.get("keywordIdeaMetrics", {})

                # Extract search volume
                avg_monthly_searches = keyword_idea.get("avgMonthlySearches", 0)
                total_volume += int(avg_monthly_searches)

                # Extract competition level
                competition = keyword_idea.get("competition", "UNKNOWN")
                if competition == "LOW":
                    competition_scores.append(0.2)
                elif competition == "MEDIUM":
                    competition_scores.append(0.5)
                elif competition == "HIGH":
                    competition_scores.append(0.8)
                else:
                    competition_scores.append(0.5)  # Default to medium

            # Calculate average competition
            avg_competition = (
                sum(competition_scores) / len(competition_scores)
                if competition_scores
                else 0.5
            )

            if avg_competition < 0.3:
                competition_level = "low"
            elif avg_competition < 0.6:
                competition_level = "medium"
            else:
                competition_level = "high"

            self.logger.info(
                f"Retrieved search metrics for {len(keywords)} keywords: {total_volume} total volume"
            )

            return {
                "total_volume": total_volume,
                "competition_level": competition_level,
                "avg_competition_score": avg_competition,
                "keyword_count": len(results),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing search metrics: {e}")
            raise ValueError(f"Failed to analyze search metrics: {e}")

    async def _analyze_market_trends(
        self, product_concept: str, keywords: List[str]
    ) -> Dict[str, str]:
        """Analyze market trends using Google Trends API"""
        try:
            if not requests:
                self.logger.error("requests library not available")
                raise ImportError("requests library required for API calls")

            # Use pytrends library for Google Trends data
            try:
                from pytrends.request import TrendReq
            except ImportError:
                self.logger.error(
                    "pytrends library not available. Install with: pip install pytrends"
                )
                raise ImportError(
                    "pytrends library required for Google Trends analysis"
                )

            # Initialize pytrends
            pytrends = TrendReq(hl="en-US", tz=360)

            # Analyze trends for top keywords (limit to 5 for API efficiency)
            trend_keywords = keywords[:5] if len(keywords) >= 5 else keywords

            if not trend_keywords:
                self.logger.warning("No keywords provided for trend analysis")
                return {"direction": "stable", "confidence": "low"}

            # Build payload for Google Trends
            pytrends.build_payload(
                trend_keywords, cat=0, timeframe="today 12-m", geo="US", gprop=""
            )

            # Get interest over time data
            interest_over_time = pytrends.interest_over_time()

            if interest_over_time.empty:
                self.logger.warning(
                    f"No trend data available for keywords: {trend_keywords}"
                )
                return {"direction": "stable", "confidence": "low"}

            # Calculate trend direction based on recent vs older data
            # Compare last 3 months average vs first 3 months average
            total_rows = len(interest_over_time)
            if total_rows < 6:  # Need at least 6 data points
                return {"direction": "stable", "confidence": "low"}

            # Calculate averages for trend analysis
            recent_period = interest_over_time.tail(3)
            older_period = interest_over_time.head(3)

            recent_avg = (
                recent_period.mean().mean()
            )  # Average across all keywords and time
            older_avg = older_period.mean().mean()

            # Determine trend direction
            if recent_avg > older_avg * 1.2:  # 20% increase
                direction = "rising"
                confidence = "high"
            elif recent_avg < older_avg * 0.8:  # 20% decrease
                direction = "declining"
                confidence = "high"
            elif recent_avg > older_avg * 1.1:  # 10% increase
                direction = "rising"
                confidence = "medium"
            elif recent_avg < older_avg * 0.9:  # 10% decrease
                direction = "declining"
                confidence = "medium"
            else:
                direction = "stable"
                confidence = "medium"

            # Get related queries for additional insights
            try:
                related_queries = pytrends.related_queries()
                related_count = sum(
                    len(queries.get("top", [])) if queries.get("top") is not None else 0
                    for queries in related_queries.values()
                )

                # Adjust confidence based on related query volume
                if related_count > 50:
                    confidence = "high"
                elif related_count > 20:
                    confidence = "medium"
                else:
                    confidence = "low"

            except Exception as e:
                self.logger.warning(f"Could not retrieve related queries: {e}")

            self.logger.info(
                f"Trend analysis complete: {direction} trend with {confidence} confidence"
            )

            return {
                "direction": direction,
                "confidence": confidence,
                "recent_avg": round(recent_avg, 2),
                "older_avg": round(older_avg, 2),
                "keywords_analyzed": len(trend_keywords),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing market trends: {e}")
            # Fallback to basic analysis if API fails
            trending_terms = [
                "ai",
                "automation",
                "saas",
                "digital",
                "online",
                "remote",
                "machine learning",
                "blockchain",
            ]
            has_trending = any(
                term in product_concept.lower()
                or any(term in keyword.lower() for keyword in keywords)
                for term in trending_terms
            )

            return {
                "direction": "rising" if has_trending else "stable",
                "confidence": "low",
                "error": str(e),
            }

    def _assess_monetization_potential(
        self, product_concept: str, search_data: Dict
    ) -> float:
        """Assess the monetization potential of the product"""
        score = 0.0

        # Base score from search volume
        if search_data["total_volume"] > 10000:
            score += 0.3
        elif search_data["total_volume"] > 5000:
            score += 0.2
        elif search_data["total_volume"] > 1000:
            score += 0.1

        # Competition level impact
        if search_data["competition_level"] == "low":
            score += 0.3
        elif search_data["competition_level"] == "medium":
            score += 0.2

        # Product type impact
        high_value_terms = [
            "course",
            "software",
            "tool",
            "platform",
            "service",
            "consulting",
        ]
        if any(term in product_concept.lower() for term in high_value_terms):
            score += 0.4

        return min(score, 1.0)

    def _identify_target_audience(
        self, product_concept: str, keywords: List[str]
    ) -> str:
        """Identify the target audience for the product"""
        # Simple audience identification based on keywords
        all_text = (product_concept + " " + " ".join(keywords)).lower()

        if any(term in all_text for term in ["business", "entrepreneur", "startup"]):
            return "Business Owners & Entrepreneurs"
        elif any(term in all_text for term in ["marketing", "social media", "content"]):
            return "Digital Marketers & Content Creators"
        elif any(
            term in all_text for term in ["developer", "programming", "code", "tech"]
        ):
            return "Developers & Tech Professionals"
        elif any(
            term in all_text for term in ["student", "learn", "education", "course"]
        ):
            return "Students & Learners"
        else:
            return "General Consumers"

    async def _identify_content_gaps(self, keywords: List[str]) -> List[str]:
        """Identify content gaps by analyzing existing content and search queries"""
        try:
            if not requests or not BeautifulSoup:
                self.logger.error(
                    "Required libraries not available for content gap analysis"
                )
                return ["Content analysis tools not available"]

            content_gaps = []
            analyzed_topics = set()

            # Analyze each keyword for content gaps
            for keyword in keywords[:5]:  # Limit to 5 keywords for efficiency
                try:
                    # Search for existing content on the topic
                    search_query = f"{keyword} tutorial guide how to"
                    search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

                    # Use a more realistic user agent
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }

                    # Note: In production, consider using Google Custom Search API instead
                    # This is a basic implementation for content gap identification

                    # Analyze common content types that might be missing
                    common_content_types = [
                        f"Beginner's guide to {keyword}",
                        f"Advanced {keyword} techniques",
                        f"{keyword} case studies",
                        f"{keyword} vs alternatives comparison",
                        f"{keyword} best practices",
                        f"{keyword} troubleshooting guide",
                        f"How to integrate {keyword}",
                        f"{keyword} ROI analysis",
                        f"{keyword} implementation checklist",
                        f"{keyword} common mistakes",
                    ]

                    # Simulate content gap detection based on keyword analysis
                    # In a full production system, this would:
                    # 1. Scrape search results to analyze existing content
                    # 2. Use SEO tools APIs to identify content gaps
                    # 3. Analyze competitor content comprehensiveness

                    # For now, identify gaps based on keyword characteristics
                    keyword_lower = keyword.lower()

                    if "tutorial" not in keyword_lower and "guide" not in keyword_lower:
                        content_gaps.append(f"Step-by-step {keyword} tutorial")

                    if (
                        "advanced" not in keyword_lower
                        and "expert" not in keyword_lower
                    ):
                        content_gaps.append(f"Advanced {keyword} strategies")

                    if "case" not in keyword_lower and "example" not in keyword_lower:
                        content_gaps.append(f"Real-world {keyword} case studies")

                    if "comparison" not in keyword_lower and "vs" not in keyword_lower:
                        content_gaps.append(f"{keyword} tool comparison")

                    # Add to analyzed topics to avoid duplicates
                    analyzed_topics.add(keyword_lower)

                except Exception as e:
                    self.logger.warning(
                        f"Error analyzing content gaps for keyword '{keyword}': {e}"
                    )
                    continue

            # Remove duplicates and limit results
            unique_gaps = list(set(content_gaps))

            # If no specific gaps found, provide general recommendations
            if not unique_gaps:
                unique_gaps = [
                    "Comprehensive beginner tutorials",
                    "Advanced implementation guides",
                    "Industry-specific case studies",
                    "Tool comparison and reviews",
                ]

            # Limit to top 6 most relevant gaps
            return unique_gaps[:6]

        except Exception as e:
            self.logger.error(f"Error in content gap analysis: {e}")
            # Fallback to basic content gap suggestions
            return [
                "Educational content for beginners",
                "Advanced technique guides",
                "Practical implementation examples",
                "Comparative analysis content",
            ]

    def _generate_product_recommendations(
        self, product_concept: str, search_data: Dict
    ) -> List[str]:
        """Generate recommended products based on market analysis"""
        recommendations = []

        # Base recommendations on search volume and competition
        if search_data["total_volume"] > 5000 and search_data["competition_level"] in [
            "low",
            "medium",
        ]:
            recommendations.extend(
                ["Online Course", "Digital Guide/Ebook", "Video Tutorial Series"]
            )

        if search_data["competition_level"] == "low":
            recommendations.extend(["SaaS Tool", "Mobile App", "Consulting Service"])

        # Product-specific recommendations
        concept_lower = product_concept.lower()
        if "marketing" in concept_lower:
            recommendations.append("Marketing Automation Tool")
        if "content" in concept_lower:
            recommendations.append("Content Creation Template Pack")
        if "business" in concept_lower:
            recommendations.append("Business Plan Template")

        return list(set(recommendations))  # Remove duplicates

    def _calculate_confidence_score(
        self, search_data: Dict, trend_data: Dict, monetization_score: float
    ) -> float:
        """Calculate overall confidence score for the opportunity"""
        score = 0.0

        # Search volume confidence
        if search_data["total_volume"] > 10000:
            score += 0.4
        elif search_data["total_volume"] > 1000:
            score += 0.2

        # Competition level confidence
        if search_data["competition_level"] == "low":
            score += 0.3
        elif search_data["competition_level"] == "medium":
            score += 0.2

        # Trend confidence
        if trend_data["direction"] == "rising":
            score += 0.2
        elif trend_data["direction"] == "stable":
            score += 0.1

        # Monetization confidence
        score += monetization_score * 0.1

        return min(score, 1.0)


# Example usage and testing
if __name__ == "__main__":

    async def test_research_tools():
        """Test the research tools"""
        print("Testing Research Agent Tools...")

        # Test Breaking News Watcher
        print("\n1. Testing Breaking News Watcher...")
        news_watcher = BreakingNewsWatcher()

        # Test feed fetching (short duration for testing)
        try:
            news_items = await news_watcher.monitor_feeds(
                duration_hours=0.1
            )  # 6 minutes
            print(f"Found {len(news_items)} news items")

            if news_items:
                print(f"Sample item: {news_items[0].title}")
                print(f"Relevance: {news_items[0].relevance_score}")
                print(f"Keywords: {news_items[0].keywords}")
        except Exception as e:
            print(f"News monitoring test failed: {e}")

        # Test trending topics
        trending = news_watcher.get_trending_keywords()
        print(f"Trending keywords: {list(trending.keys())[:5]}")

        # Test Competitor Analyzer
        print("\n2. Testing Competitor Analyzer...")
        analyzer = CompetitorAnalyzer()

        try:
            niche_keywords = ["tech review", "smartphone", "gadget"]
            competitors = await analyzer.analyze_niche(niche_keywords, max_channels=5)
            print(f"Found {len(competitors)} competitors")

            if competitors:
                top_competitor = competitors[0]
                print(f"Top opportunity: {top_competitor.channel_name}")
                print(f"Opportunity score: {top_competitor.opportunity_score:.3f}")
                print(f"Subscribers: {top_competitor.subscriber_count:,}")

            # Test content gaps
            gaps = analyzer.find_content_gaps(competitors)
            print(f"Content gaps: {gaps[:3]}")

        except Exception as e:
            print(f"Competitor analysis test failed: {e}")

        # Test Market Validator
        print("\n3. Testing Market Validator...")
        validator = MarketValidator()

        try:
            product_concept = "AI-powered content creation tool"
            keywords = ["ai content", "automated writing", "content generator"]

            opportunity = await validator.validate_product_idea(
                product_concept, keywords
            )
            print(f"Market opportunity for: {opportunity.niche}")
            print(f"Search volume: {opportunity.search_volume:,}")
            print(f"Competition: {opportunity.competition_level}")
            print(f"Trend: {opportunity.trend_direction}")
            print(f"Monetization potential: {opportunity.monetization_potential:.2f}")
            print(f"Target audience: {opportunity.target_audience}")
            print(f"Confidence score: {opportunity.confidence_score:.2f}")
            print(f"Recommended products: {opportunity.recommended_products[:3]}")

        except Exception as e:
            print(f"Market validation test failed: {e}")

        print("\nResearch tools testing completed!")


class SEOAuditService:
    """AI-Powered SEO Audit Service with PDF Report Generation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get("db_path", "right_perspective.db")
        self.reports_dir = config.get("reports_dir", "seo_reports")
        self.smtp_config = config.get("smtp_config", {})

        # Create reports directory
        os.makedirs(self.reports_dir, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SEO audit database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # SEO audit requests table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seo_audit_requests (
                request_id TEXT PRIMARY KEY,
                website_url TEXT NOT NULL,
                email TEXT NOT NULL,
                company_name TEXT,
                industry TEXT,
                target_keywords TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                report_file_path TEXT
            )
        """
        )

        # SEO audit results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seo_audit_results (
                request_id TEXT PRIMARY KEY,
                website_url TEXT NOT NULL,
                overall_score REAL,
                technical_seo TEXT,
                on_page_seo TEXT,
                content_analysis TEXT,
                competitor_analysis TEXT,
                recommendations TEXT,
                priority_issues TEXT,
                opportunities TEXT,
                audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES seo_audit_requests (request_id)
            )
        """
        )

        conn.commit()
        conn.close()

    async def submit_audit_request(self, request: SEOAuditRequest) -> str:
        """Submit a new SEO audit request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO seo_audit_requests 
                (request_id, website_url, email, company_name, industry, target_keywords, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request.request_id,
                    request.website_url,
                    request.email,
                    request.company_name,
                    request.industry,
                    json.dumps(request.target_keywords),
                    request.status,
                ),
            )

            conn.commit()
            logging.info(f"SEO audit request submitted: {request.request_id}")

            # Start audit processing asynchronously
            await self._process_audit_request(request.request_id)

            return request.request_id

        except Exception as e:
            logging.error(f"Error submitting SEO audit request: {e}")
            raise
        finally:
            conn.close()

    async def _process_audit_request(self, request_id: str):
        """Process an SEO audit request"""
        try:
            # Update status to processing
            self._update_request_status(request_id, "processing")

            # Get request details
            request_data = self._get_request_data(request_id)
            if not request_data:
                raise ValueError(f"Request not found: {request_id}")

            website_url = request_data["website_url"]

            # Perform SEO audit
            audit_result = await self._perform_seo_audit(website_url, request_data)

            # Generate PDF report
            report_path = await self._generate_pdf_report(audit_result, request_data)

            # Save results to database
            await self._save_audit_results(request_id, audit_result, report_path)

            # Send email with report
            await self._send_audit_report_email(request_data, report_path)

            # Update status to completed
            self._update_request_status(request_id, "completed")

            logging.info(f"SEO audit completed: {request_id}")

        except Exception as e:
            logging.error(f"Error processing SEO audit {request_id}: {e}")
            self._update_request_status(request_id, "failed")

    async def _perform_seo_audit(
        self, website_url: str, request_data: Dict
    ) -> SEOAuditResult:
        """Perform comprehensive SEO audit"""
        try:
            # Fetch website content
            if not requests:
                raise ImportError("requests library not available")

            response = requests.get(website_url, timeout=30)
            response.raise_for_status()

            if not BeautifulSoup:
                raise ImportError("BeautifulSoup library not available")

            soup = BeautifulSoup(response.content, "html.parser")

            # Technical SEO Analysis
            technical_seo = await self._analyze_technical_seo(
                website_url, soup, response
            )

            # On-Page SEO Analysis
            on_page_seo = await self._analyze_on_page_seo(
                soup, request_data.get("target_keywords", [])
            )

            # Content Analysis
            content_analysis = await self._analyze_content(soup)

            # Competitor Analysis
            competitor_analysis = await self._analyze_competitors(
                request_data.get("industry", ""),
                request_data.get("target_keywords", []),
            )

            # Generate recommendations
            recommendations, priority_issues, opportunities = (
                self._generate_recommendations(
                    technical_seo, on_page_seo, content_analysis, competitor_analysis
                )
            )

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                technical_seo, on_page_seo, content_analysis
            )

            return SEOAuditResult(
                website_url=website_url,
                audit_date=datetime.now(),
                overall_score=overall_score,
                technical_seo=technical_seo,
                on_page_seo=on_page_seo,
                content_analysis=content_analysis,
                competitor_analysis=competitor_analysis,
                recommendations=recommendations,
                priority_issues=priority_issues,
                opportunities=opportunities,
            )

        except Exception as e:
            logging.error(f"Error performing SEO audit for {website_url}: {e}")
            raise

    async def _analyze_technical_seo(
        self, url: str, soup: BeautifulSoup, response
    ) -> Dict[str, Any]:
        """Analyze technical SEO factors"""
        technical_seo = {
            "page_speed": {"score": 0, "issues": []},
            "mobile_friendly": {"score": 0, "issues": []},
            "https": {"score": 0, "issues": []},
            "meta_tags": {"score": 0, "issues": []},
            "structured_data": {"score": 0, "issues": []},
            "crawlability": {"score": 0, "issues": []},
        }

        # HTTPS Check
        if url.startswith("https://"):
            technical_seo["https"]["score"] = 100
        else:
            technical_seo["https"]["score"] = 0
            technical_seo["https"]["issues"].append("Website not using HTTPS")

        # Meta tags analysis
        title_tag = soup.find("title")
        meta_description = soup.find("meta", attrs={"name": "description"})

        if title_tag and title_tag.text.strip():
            if 10 <= len(title_tag.text) <= 60:
                technical_seo["meta_tags"]["score"] += 50
            else:
                technical_seo["meta_tags"]["issues"].append(
                    f"Title tag length ({len(title_tag.text)} chars) not optimal (10-60 chars)"
                )
        else:
            technical_seo["meta_tags"]["issues"].append("Missing or empty title tag")

        if meta_description and meta_description.get("content", "").strip():
            desc_length = len(meta_description.get("content", ""))
            if 120 <= desc_length <= 160:
                technical_seo["meta_tags"]["score"] += 50
            else:
                technical_seo["meta_tags"]["issues"].append(
                    f"Meta description length ({desc_length} chars) not optimal (120-160 chars)"
                )
        else:
            technical_seo["meta_tags"]["issues"].append("Missing meta description")

        # Mobile viewport check
        viewport_meta = soup.find("meta", attrs={"name": "viewport"})
        if viewport_meta:
            technical_seo["mobile_friendly"]["score"] = 80
        else:
            technical_seo["mobile_friendly"]["score"] = 20
            technical_seo["mobile_friendly"]["issues"].append(
                "Missing viewport meta tag"
            )

        # Structured data check
        json_ld = soup.find_all("script", type="application/ld+json")
        if json_ld:
            technical_seo["structured_data"]["score"] = 80
        else:
            technical_seo["structured_data"]["score"] = 20
            technical_seo["structured_data"]["issues"].append(
                "No structured data found"
            )

        # Basic page speed analysis (response time)
        response_time = getattr(response, "elapsed", None)
        if response_time:
            response_seconds = response_time.total_seconds()
            if response_seconds < 2:
                technical_seo["page_speed"]["score"] = 90
            elif response_seconds < 4:
                technical_seo["page_speed"]["score"] = 70
            else:
                technical_seo["page_speed"]["score"] = 40
                technical_seo["page_speed"]["issues"].append(
                    f"Slow response time: {response_seconds:.2f}s"
                )

        return technical_seo

    async def _analyze_on_page_seo(
        self, soup: BeautifulSoup, target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze on-page SEO factors"""
        on_page_seo = {
            "keyword_optimization": {"score": 0, "issues": []},
            "heading_structure": {"score": 0, "issues": []},
            "internal_linking": {"score": 0, "issues": []},
            "image_optimization": {"score": 0, "issues": []},
            "content_quality": {"score": 0, "issues": []},
        }

        # Heading structure analysis
        h1_tags = soup.find_all("h1")
        if len(h1_tags) == 1:
            on_page_seo["heading_structure"]["score"] += 40
        elif len(h1_tags) == 0:
            on_page_seo["heading_structure"]["issues"].append("Missing H1 tag")
        else:
            on_page_seo["heading_structure"]["issues"].append(
                f"Multiple H1 tags found ({len(h1_tags)})"
            )

        # Check for proper heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if len(headings) >= 3:
            on_page_seo["heading_structure"]["score"] += 30
        else:
            on_page_seo["heading_structure"]["issues"].append(
                "Insufficient heading structure"
            )

        # Image optimization
        images = soup.find_all("img")
        images_with_alt = [img for img in images if img.get("alt")]
        if images:
            alt_ratio = len(images_with_alt) / len(images)
            on_page_seo["image_optimization"]["score"] = int(alt_ratio * 100)
            if alt_ratio < 0.8:
                on_page_seo["image_optimization"]["issues"].append(
                    f"{len(images) - len(images_with_alt)} images missing alt text"
                )
        else:
            on_page_seo["image_optimization"]["score"] = 50

        # Internal linking
        internal_links = soup.find_all("a", href=True)
        if len(internal_links) >= 5:
            on_page_seo["internal_linking"]["score"] = 80
        else:
            on_page_seo["internal_linking"]["score"] = 40
            on_page_seo["internal_linking"]["issues"].append("Limited internal linking")

        # Keyword optimization (if target keywords provided)
        if target_keywords:
            page_text = soup.get_text().lower()
            keyword_found = any(
                keyword.lower() in page_text for keyword in target_keywords
            )
            if keyword_found:
                on_page_seo["keyword_optimization"]["score"] = 70
            else:
                on_page_seo["keyword_optimization"]["score"] = 20
                on_page_seo["keyword_optimization"]["issues"].append(
                    "Target keywords not found in content"
                )

        return on_page_seo

    async def _analyze_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content quality and structure"""
        content_analysis = {
            "word_count": 0,
            "readability": {"score": 0, "issues": []},
            "content_structure": {"score": 0, "issues": []},
            "uniqueness": {"score": 0, "issues": []},
        }

        # Extract main content text
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        words = text.split()
        content_analysis["word_count"] = len(words)

        # Word count analysis
        if len(words) >= 300:
            content_analysis["content_structure"]["score"] += 40
        else:
            content_analysis["content_structure"]["issues"].append(
                f"Low word count: {len(words)} words"
            )

        # Basic readability analysis
        if TextBlob:
            try:
                blob = TextBlob(text)
                sentences = blob.sentences
                if sentences:
                    avg_sentence_length = len(words) / len(sentences)
                    if 15 <= avg_sentence_length <= 25:
                        content_analysis["readability"]["score"] = 80
                    else:
                        content_analysis["readability"]["score"] = 50
                        content_analysis["readability"]["issues"].append(
                            f"Average sentence length: {avg_sentence_length:.1f} words"
                        )
            except Exception as e:
                logging.warning(f"TextBlob analysis failed: {e}")
                content_analysis["readability"]["score"] = 50

        return content_analysis

    async def _analyze_competitors(
        self, industry: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze competitor landscape"""
        competitor_analysis = {
            "competition_level": "medium",
            "top_competitors": [],
            "opportunities": [],
            "market_insights": [],
        }

        # This would typically involve more sophisticated competitor research
        # For now, provide basic analysis based on industry and keywords
        if industry:
            competitor_analysis["market_insights"].append(f"Industry: {industry}")

        if keywords:
            competitor_analysis["market_insights"].append(
                f'Target keywords: {", ".join(keywords[:5])}'
            )

            # Simulate competition analysis
            if len(keywords) > 5:
                competitor_analysis["competition_level"] = "high"
            elif len(keywords) < 3:
                competitor_analysis["competition_level"] = "low"

        return competitor_analysis

    def _generate_recommendations(
        self,
        technical_seo: Dict,
        on_page_seo: Dict,
        content_analysis: Dict,
        competitor_analysis: Dict,
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate SEO recommendations based on audit results"""
        recommendations = []
        priority_issues = []
        opportunities = []

        # Technical SEO recommendations
        for category, data in technical_seo.items():
            if data["score"] < 70:
                for issue in data["issues"]:
                    if data["score"] < 40:
                        priority_issues.append(f"Technical SEO - {category}: {issue}")
                    else:
                        recommendations.append(f"Improve {category}: {issue}")

        # On-page SEO recommendations
        for category, data in on_page_seo.items():
            if data["score"] < 70:
                for issue in data["issues"]:
                    if data["score"] < 40:
                        priority_issues.append(f"On-page SEO - {category}: {issue}")
                    else:
                        recommendations.append(f"Optimize {category}: {issue}")

        # Content recommendations
        if content_analysis["word_count"] < 300:
            priority_issues.append("Increase content length to at least 300 words")
        elif content_analysis["word_count"] < 500:
            recommendations.append(
                "Consider expanding content to 500+ words for better SEO"
            )

        # Opportunities
        opportunities.extend(
            [
                "Implement schema markup for better search visibility",
                "Create topic clusters around main keywords",
                "Optimize for featured snippets",
                "Improve page loading speed",
                "Build high-quality backlinks",
            ]
        )

        return recommendations, priority_issues, opportunities

    def _calculate_overall_score(
        self, technical_seo: Dict, on_page_seo: Dict, content_analysis: Dict
    ) -> float:
        """Calculate overall SEO score"""
        technical_scores = [data["score"] for data in technical_seo.values()]
        on_page_scores = [data["score"] for data in on_page_seo.values()]

        technical_avg = (
            sum(technical_scores) / len(technical_scores) if technical_scores else 0
        )
        on_page_avg = sum(on_page_scores) / len(on_page_scores) if on_page_scores else 0

        # Content score based on word count and structure
        content_score = (
            min(100, (content_analysis["word_count"] / 500) * 100)
            if content_analysis["word_count"] > 0
            else 0
        )

        # Weighted average: 40% technical, 40% on-page, 20% content
        overall_score = (
            (technical_avg * 0.4) + (on_page_avg * 0.4) + (content_score * 0.2)
        )

        return round(overall_score, 1)

    async def _generate_pdf_report(
        self, audit_result: SEOAuditResult, request_data: Dict
    ) -> str:
        """Generate PDF report from audit results"""
        if not SimpleDocTemplate:
            raise ImportError("ReportLab library not available for PDF generation")

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seo_audit_{request_data['request_id']}_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
        )
        story.append(Paragraph("AI-Powered SEO Audit Report", title_style))
        story.append(Spacer(1, 20))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        summary_text = f"""
        Website: {audit_result.website_url}<br/>
        Audit Date: {audit_result.audit_date.strftime('%B %d, %Y')}<br/>
        Overall SEO Score: <b>{audit_result.overall_score}/100</b><br/>
        Priority Issues: {len(audit_result.priority_issues)}<br/>
        Recommendations: {len(audit_result.recommendations)}
        """
        story.append(Paragraph(summary_text, styles["Normal"]))
        story.append(Spacer(1, 20))

        # Technical SEO Section
        story.append(Paragraph("Technical SEO Analysis", styles["Heading2"]))
        tech_data = []
        tech_data.append(["Category", "Score", "Status"])

        for category, data in audit_result.technical_seo.items():
            status = (
                "Good"
                if data["score"] >= 70
                else "Needs Improvement" if data["score"] >= 40 else "Critical"
            )
            tech_data.append(
                [category.replace("_", " ").title(), f"{data['score']}/100", status]
            )

        tech_table = Table(tech_data)
        tech_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(tech_table)
        story.append(Spacer(1, 20))

        # Priority Issues
        if audit_result.priority_issues:
            story.append(Paragraph("Priority Issues", styles["Heading2"]))
            for issue in audit_result.priority_issues[:10]:  # Limit to top 10
                story.append(Paragraph(f"• {issue}", styles["Normal"]))
            story.append(Spacer(1, 20))

        # Recommendations
        story.append(Paragraph("Recommendations", styles["Heading2"]))
        for rec in audit_result.recommendations[:15]:  # Limit to top 15
            story.append(Paragraph(f"• {rec}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Opportunities
        story.append(Paragraph("Growth Opportunities", styles["Heading2"]))
        for opp in audit_result.opportunities[:10]:  # Limit to top 10
            story.append(Paragraph(f"• {opp}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Call to Action
        cta_style = ParagraphStyle(
            "CTA",
            parent=styles["Normal"],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10,
        )
        story.append(Paragraph("Ready to Improve Your SEO?", styles["Heading2"]))
        story.append(
            Paragraph(
                "This audit has identified key areas for improvement. Our digital marketing products can help you implement these recommendations and boost your search rankings.",
                cta_style,
            )
        )
        story.append(
            Paragraph(
                "Visit our website to explore our SEO optimization tools and courses designed to help you succeed online.",
                styles["Normal"],
            )
        )

        # Build PDF
        doc.build(story)

        logging.info(f"PDF report generated: {filepath}")
        return filepath

    async def _send_audit_report_email(self, request_data: Dict, report_path: str):
        """Send audit report via email"""
        if not smtplib or not MIMEMultipart:
            logging.warning("Email libraries not available, skipping email send")
            return

        if not self.smtp_config:
            logging.warning("SMTP configuration not provided, skipping email send")
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.get("from_email", "")
            msg["To"] = request_data["email"]
            msg["Subject"] = f"Your SEO Audit Report - {request_data['website_url']}"

            # Email body
            body = f"""
            Dear {request_data.get('company_name', 'Valued Customer')},
            
            Thank you for requesting an SEO audit for {request_data['website_url']}.
            
            Please find your comprehensive SEO audit report attached. This report includes:
            
            • Technical SEO analysis
            • On-page optimization recommendations
            • Content quality assessment
            • Priority issues to address
            • Growth opportunities
            
            Our AI-powered analysis has identified specific areas where you can improve your search engine rankings and drive more organic traffic to your website.
            
            If you have any questions about the report or would like to learn more about our SEO optimization services, please don't hesitate to contact us.
            
            Best regards,
            The SEO Audit Team
            """

            msg.attach(MIMEText(body, "plain"))

            # Attach PDF report
            if os.path.exists(report_path):
                with open(report_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(report_path)}",
                )
                msg.attach(part)

            # Send email
            server = smtplib.SMTP(
                self.smtp_config.get("smtp_server", ""),
                self.smtp_config.get("smtp_port", 587),
            )
            server.starttls()
            server.login(
                self.smtp_config.get("username", ""),
                self.smtp_config.get("password", ""),
            )
            text = msg.as_string()
            server.sendmail(
                self.smtp_config.get("from_email", ""), request_data["email"], text
            )
            server.quit()

            logging.info(f"Audit report emailed to {request_data['email']}")

        except Exception as e:
            logging.error(f"Error sending audit report email: {e}")

    def _update_request_status(self, request_id: str, status: str):
        """Update request status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if status == "completed":
                cursor.execute(
                    "UPDATE seo_audit_requests SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE request_id = ?",
                    (status, request_id),
                )
            else:
                cursor.execute(
                    "UPDATE seo_audit_requests SET status = ? WHERE request_id = ?",
                    (status, request_id),
                )
            conn.commit()
        finally:
            conn.close()

    def _get_request_data(self, request_id: str) -> Optional[Dict]:
        """Get request data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM seo_audit_requests WHERE request_id = ?", (request_id,)
            )
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            conn.close()

    async def _save_audit_results(
        self, request_id: str, audit_result: SEOAuditResult, report_path: str
    ):
        """Save audit results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO seo_audit_results 
                (request_id, website_url, overall_score, technical_seo, on_page_seo, 
                 content_analysis, competitor_analysis, recommendations, priority_issues, opportunities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    audit_result.website_url,
                    audit_result.overall_score,
                    json.dumps(audit_result.technical_seo),
                    json.dumps(audit_result.on_page_seo),
                    json.dumps(audit_result.content_analysis),
                    json.dumps(audit_result.competitor_analysis),
                    json.dumps(audit_result.recommendations),
                    json.dumps(audit_result.priority_issues),
                    json.dumps(audit_result.opportunities),
                ),
            )

            # Update request with report path
            cursor.execute(
                "UPDATE seo_audit_requests SET report_file_path = ? WHERE request_id = ?",
                (report_path, request_id),
            )

            conn.commit()
        finally:
            conn.close()

    async def get_audit_status(self, request_id: str) -> Optional[Dict]:
        """Get audit status and results"""
        request_data = self._get_request_data(request_id)
        if not request_data:
            return None

        # Get results if completed
        if request_data["status"] == "completed":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "SELECT * FROM seo_audit_results WHERE request_id = ?",
                    (request_id,),
                )
                result_row = cursor.fetchone()

                if result_row:
                    columns = [description[0] for description in cursor.description]
                    result_data = dict(zip(columns, result_row))
                    request_data["results"] = result_data
            finally:
                conn.close()

        return request_data
