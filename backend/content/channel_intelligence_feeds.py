#!/usr/bin/env python3
"""
Channel Intelligence Feeds System

Automatically monitors and processes RSS feeds for each channel,
extracting relevant content and storing it in channel-specific knowledge bases.
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import feedparser
import nltk
from bs4 import BeautifulSoup
from textstat import flesch_reading_ease

try:
    from .universal_channel_protocol import ChannelType, get_protocol
except ImportError:
    # Fallback for development
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from universal_channel_protocol import ChannelType, get_protocol


@dataclass
class FeedItem:
    """Represents a single item from an RSS feed"""

    title: str
    content: str
    url: str
    published: datetime
    author: str = ""
    tags: List[str] = None
    summary: str = ""
    relevance_score: float = 0.0
    credibility_score: float = 0.5

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ChannelIntelligenceFeeds:
    """
    Manages RSS feed monitoring and content extraction for all channels
    """

    def __init__(self, db_path: str = "data/right_perspective.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.protocol = get_protocol()
        self.session = None
        self.feed_cache = {}
        self.content_extractors = self._initialize_extractors()

        # Download NLTK data if needed
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

    def _initialize_extractors(self) -> Dict[ChannelType, Dict[str, Any]]:
        """Initialize content extractors for different channel types"""
        return {
            ChannelType.TECH: {
                "keywords": [
                    "technology",
                    "software",
                    "hardware",
                    "AI",
                    "machine learning",
                    "programming",
                    "coding",
                    "development",
                    "innovation",
                    "startup",
                ],
                "relevance_boost": [
                    "breakthrough",
                    "revolutionary",
                    "cutting-edge",
                    "beta",
                    "launch",
                ],
                "credibility_sources": [
                    "techcrunch.com",
                    "arstechnica.com",
                    "wired.com",
                    "theverge.com",
                ],
            },
            ChannelType.WELLNESS: {
                "keywords": [
                    "health",
                    "wellness",
                    "nutrition",
                    "fitness",
                    "mental health",
                    "exercise",
                    "diet",
                    "meditation",
                    "yoga",
                    "supplements",
                ],
                "relevance_boost": [
                    "study shows",
                    "research",
                    "clinical trial",
                    "proven",
                    "effective",
                ],
                "credibility_sources": [
                    "healthline.com",
                    "webmd.com",
                    "mayoclinic.org",
                    "nih.gov",
                ],
            },
            ChannelType.FINANCE: {
                "keywords": [
                    "finance",
                    "investment",
                    "stock",
                    "market",
                    "economy",
                    "trading",
                    "cryptocurrency",
                    "bitcoin",
                    "portfolio",
                    "retirement",
                ],
                "relevance_boost": [
                    "earnings",
                    "profit",
                    "loss",
                    "bull market",
                    "bear market",
                ],
                "credibility_sources": [
                    "bloomberg.com",
                    "reuters.com",
                    "wsj.com",
                    "marketwatch.com",
                ],
            },
            ChannelType.POLITICAL: {
                "keywords": [
                    "politics",
                    "government",
                    "election",
                    "policy",
                    "congress",
                    "senate",
                    "president",
                    "conservative",
                    "liberal",
                    "democrat",
                    "republican",
                ],
                "relevance_boost": [
                    "breaking",
                    "scandal",
                    "investigation",
                    "vote",
                    "bill passed",
                ],
                "credibility_sources": [
                    "breitbart.com",
                    "dailywire.com",
                    "townhall.com",
                    "foxnews.com",
                ],
            },
            ChannelType.BUSINESS: {
                "keywords": [
                    "business",
                    "entrepreneur",
                    "startup",
                    "company",
                    "CEO",
                    "revenue",
                    "growth",
                    "strategy",
                    "marketing",
                    "sales",
                ],
                "relevance_boost": [
                    "acquisition",
                    "merger",
                    "IPO",
                    "funding",
                    "expansion",
                ],
                "credibility_sources": [
                    "forbes.com",
                    "businessinsider.com",
                    "entrepreneur.com",
                ],
            },
            ChannelType.SCIENCE: {
                "keywords": [
                    "science",
                    "research",
                    "discovery",
                    "experiment",
                    "study",
                    "theory",
                    "physics",
                    "chemistry",
                    "biology",
                    "space",
                ],
                "relevance_boost": [
                    "breakthrough",
                    "discovery",
                    "published",
                    "peer-reviewed",
                ],
                "credibility_sources": [
                    "nature.com",
                    "sciencemag.org",
                    "newscientist.com",
                ],
            },
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "TRAE.AI Channel Intelligence Bot 1.0"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def monitor_all_channels(self):
        """Monitor RSS feeds for all channels"""
        channels = self.protocol.get_all_channels()

        tasks = []
        for channel_id, config in channels.items():
            if config.rss_feeds:
                task = asyncio.create_task(self.monitor_channel_feeds(channel_id))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def monitor_channel_feeds(self, channel_id: str):
        """Monitor RSS feeds for a specific channel"""
        config = self.protocol.get_channel_config(channel_id)
        if not config:
            return

        self.logger.info(f"Monitoring feeds for channel: {channel_id}")

        for feed_url in config.rss_feeds:
            try:
                await self.process_feed(channel_id, feed_url)
            except Exception as e:
                self.logger.error(
                    f"Error processing feed {feed_url} for {channel_id}: {e}"
                )
                self._log_feed_error(channel_id, feed_url, str(e))

    async def process_feed(self, channel_id: str, feed_url: str):
        """Process a single RSS feed"""
        try:
            # Check if we've processed this feed recently
            if self._should_skip_feed(channel_id, feed_url):
                return

            # Fetch feed content
            feed_content = await self._fetch_feed(feed_url)
            if not feed_content:
                return

            # Parse feed
            feed = feedparser.parse(feed_content)
            if not feed.entries:
                self.logger.warning(f"No entries found in feed: {feed_url}")
                return

            # Update feed metadata
            self._update_feed_metadata(channel_id, feed_url, feed)

            # Process each entry
            processed_count = 0
            for entry in feed.entries[:20]:  # Limit to 20 most recent entries
                if await self._process_feed_entry(channel_id, feed_url, entry):
                    processed_count += 1

            self.logger.info(
                f"Processed {processed_count} entries from {feed_url} for {channel_id}"
            )

        except Exception as e:
            self.logger.error(f"Error processing feed {feed_url}: {e}")
            self._log_feed_error(channel_id, feed_url, str(e))

    async def _fetch_feed(self, feed_url: str) -> Optional[str]:
        """Fetch RSS feed content"""
        try:
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.warning(f"HTTP {response.status} for feed: {feed_url}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching feed {feed_url}: {e}")
            return None

    def _should_skip_feed(self, channel_id: str, feed_url: str) -> bool:
        """Check if feed should be skipped based on last check time"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT last_checked FROM channel_rss_feeds 
                WHERE channel_id = ? AND feed_url = ?
            """,
                (channel_id, feed_url),
            )

            row = cursor.fetchone()
            if row and row[0]:
                last_checked = datetime.fromisoformat(row[0])
                # Skip if checked within last hour
                if datetime.now() - last_checked < timedelta(hours=1):
                    return True

        return False

    def _update_feed_metadata(self, channel_id: str, feed_url: str, feed):
        """Update feed metadata in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE channel_rss_feeds 
                SET feed_title = ?, feed_description = ?, last_checked = ?, 
                    last_updated = ?, status = 'active', error_count = 0
                WHERE channel_id = ? AND feed_url = ?
            """,
                (
                    getattr(feed.feed, "title", ""),
                    getattr(feed.feed, "description", ""),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    channel_id,
                    feed_url,
                ),
            )
            conn.commit()

    async def _process_feed_entry(self, channel_id: str, feed_url: str, entry) -> bool:
        """Process a single feed entry"""
        try:
            # Extract basic information
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "")
            content = getattr(entry, "content", [{}])

            if isinstance(content, list) and content:
                content_text = content[0].get("value", summary)
            else:
                content_text = summary

            # Parse publication date
            published = self._parse_date(getattr(entry, "published", ""))

            # Skip if too old (older than 7 days)
            if published and (datetime.now() - published).days > 7:
                return False

            # Check if already processed
            if self._is_entry_processed(channel_id, link):
                return False

            # Create feed item
            feed_item = FeedItem(
                title=title,
                content=content_text,
                url=link,
                published=published or datetime.now(),
                author=getattr(entry, "author", ""),
                summary=summary,
            )

            # Calculate relevance and credibility scores
            config = self.protocol.get_channel_config(channel_id)
            if config:
                feed_item.relevance_score = self._calculate_relevance_score(
                    feed_item, config.channel_type
                )
                feed_item.credibility_score = self._calculate_credibility_score(
                    feed_item, feed_url, config.channel_type
                )

            # Only store if relevance score is above threshold
            if feed_item.relevance_score >= 0.3:
                await self._store_feed_item(channel_id, feed_item)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error processing entry from {feed_url}: {e}")
            return False

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse publication date from various formats"""
        if not date_str:
            return None

        try:
            # Try parsing with feedparser's built-in parser
            import email.utils

            timestamp = email.utils.parsedate_tz(date_str)
            if timestamp:
                return datetime.fromtimestamp(email.utils.mktime_tz(timestamp))
        except:
            pass

        # Fallback to current time
        return datetime.now()

    def _is_entry_processed(self, channel_id: str, url: str) -> bool:
        """Check if entry has already been processed"""
        url_hash = hashlib.md5(url.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM channel_knowledge_base 
                WHERE channel_id = ? AND source_url = ?
            """,
                (channel_id, url),
            )

            return cursor.fetchone() is not None

    def _calculate_relevance_score(
        self, item: FeedItem, channel_type: ChannelType
    ) -> float:
        """Calculate relevance score for a feed item"""
        if channel_type not in self.content_extractors:
            return 0.5

        extractor = self.content_extractors[channel_type]
        text = f"{item.title} {item.content} {item.summary}".lower()

        # Base score from keyword matching
        keyword_score = 0.0
        for keyword in extractor["keywords"]:
            if keyword.lower() in text:
                keyword_score += 0.1

        # Boost score for relevance indicators
        boost_score = 0.0
        for boost_term in extractor["relevance_boost"]:
            if boost_term.lower() in text:
                boost_score += 0.15

        # Normalize score
        total_score = min(1.0, keyword_score + boost_score)

        return total_score

    def _calculate_credibility_score(
        self, item: FeedItem, feed_url: str, channel_type: ChannelType
    ) -> float:
        """Calculate credibility score for a feed item"""
        base_score = 0.5

        if channel_type not in self.content_extractors:
            return base_score

        extractor = self.content_extractors[channel_type]

        # Check if source is in credible sources list
        domain = urlparse(feed_url).netloc.lower()
        for credible_source in extractor["credibility_sources"]:
            if credible_source in domain:
                base_score += 0.3
                break

        # Check content quality indicators
        text = item.content or item.summary
        if text:
            # Length indicator (longer articles often more credible)
            if len(text) > 1000:
                base_score += 0.1

            # Readability score
            try:
                readability = flesch_reading_ease(text)
                if 30 <= readability <= 70:  # Good readability range
                    base_score += 0.1
            except:
                pass

        return min(1.0, base_score)

    async def _store_feed_item(self, channel_id: str, item: FeedItem):
        """Store feed item in channel knowledge base"""
        # Determine entry type based on content
        entry_type = self._classify_entry_type(item)

        # Determine appropriate table
        config = self.protocol.get_channel_config(channel_id)
        if not config or not config.knowledge_base_tables:
            return

        # Use the first general table or a specific one based on type
        table_name = config.knowledge_base_tables[0]
        if entry_type == "study" and "research" in str(config.knowledge_base_tables):
            table_name = next(
                (
                    t
                    for t in config.knowledge_base_tables
                    if "research" in t or "study" in t
                ),
                table_name,
            )
        elif entry_type == "news" and "news" in str(config.knowledge_base_tables):
            table_name = next(
                (t for t in config.knowledge_base_tables if "news" in t), table_name
            )

        # Extract tags
        tags = self._extract_tags(item, config.channel_type)

        # Store in database
        success = self.protocol.add_knowledge_entry(
            channel_id=channel_id,
            table_name=table_name,
            entry_type=entry_type,
            title=item.title,
            content=item.content or item.summary,
            source_url=item.url,
            credibility=item.credibility_score,
            relevance=item.relevance_score,
            tags=tags,
        )

        if success:
            self.logger.debug(
                f"Stored feed item: {item.title[:50]}... for {channel_id}"
            )

    def _classify_entry_type(self, item: FeedItem) -> str:
        """Classify the type of content entry"""
        text = f"{item.title} {item.content}".lower()

        if any(term in text for term in ["study", "research", "analysis", "report"]):
            return "study"
        elif any(term in text for term in ["quote", "said", "statement", "interview"]):
            return "quote"
        elif any(term in text for term in ["statistic", "data", "number", "percent"]):
            return "statistic"
        elif any(term in text for term in ["fact", "evidence", "proof", "confirmed"]):
            return "fact"
        else:
            return "news"

    def _extract_tags(self, item: FeedItem, channel_type: ChannelType) -> List[str]:
        """Extract relevant tags from feed item"""
        tags = []
        text = f"{item.title} {item.content}".lower()

        if channel_type in self.content_extractors:
            keywords = self.content_extractors[channel_type]["keywords"]
            for keyword in keywords:
                if keyword.lower() in text:
                    tags.append(keyword)

        # Add publication date as tag
        if item.published:
            tags.append(f"published_{item.published.strftime('%Y-%m')}")

        # Add credibility level as tag
        if item.credibility_score >= 0.8:
            tags.append("high_credibility")
        elif item.credibility_score >= 0.6:
            tags.append("medium_credibility")
        else:
            tags.append("low_credibility")

        return list(set(tags))  # Remove duplicates

    def _log_feed_error(self, channel_id: str, feed_url: str, error_msg: str):
        """Log feed processing error"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE channel_rss_feeds 
                SET error_count = error_count + 1, last_error = ?, 
                    status = CASE WHEN error_count >= 5 THEN 'error' ELSE 'active' END
                WHERE channel_id = ? AND feed_url = ?
            """,
                (error_msg, channel_id, feed_url),
            )
            conn.commit()

    async def get_latest_intelligence(
        self, channel_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get latest intelligence for a channel"""
        return self.protocol.get_channel_knowledge_base(channel_id)[:limit]

    async def search_intelligence(
        self, channel_id: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search intelligence for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM channel_knowledge_base 
                WHERE channel_id = ? AND (
                    title LIKE ? OR content LIKE ? OR tags LIKE ?
                )
                ORDER BY relevance_score DESC, created_at DESC
                LIMIT ?
            """,
                (channel_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "channel_id": row[1],
                        "table_name": row[2],
                        "entry_type": row[3],
                        "title": row[4],
                        "content": row[5],
                        "source_url": row[6],
                        "source_credibility": row[7],
                        "relevance_score": row[8],
                        "tags": json.loads(row[9]) if row[9] else [],
                        "created_at": row[10],
                        "updated_at": row[11],
                    }
                )

            return results


# Background task runner
async def run_intelligence_monitoring():
    """Run continuous intelligence monitoring for all channels"""
    logger = logging.getLogger(__name__)

    while True:
        try:
            async with ChannelIntelligenceFeeds() as intelligence:
                await intelligence.monitor_all_channels()

            # Wait 1 hour before next monitoring cycle
            await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"Error in intelligence monitoring: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error


if __name__ == "__main__":
    # Run intelligence monitoring
    asyncio.run(run_intelligence_monitoring())
