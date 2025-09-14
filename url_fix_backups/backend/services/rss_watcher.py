#!/usr / bin / env python3
"""
RSS Watcher Service

This service continuously monitors RSS feeds and automatically triggers
video creation through the API when new items are detected.
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from utils.logger import get_logger

# Import existing RSS infrastructure

from breaking_news_watcher import NewsArticle, RSSIntelligenceEngine, TrendData

logger = get_logger(__name__)

@dataclass


class RSSVideoTrigger:
    """Represents a video creation trigger based on RSS feed items."""

    trigger_id: str
    title: str
    description: str
    source_url: str
    feed_name: str
    keywords: List[str]
    urgency_score: float
    created_at: datetime
    status: str = "pending"
    video_task_id: Optional[str] = None


class RSSWatcherService:
    """Service that monitors RSS feeds and auto - triggers video creation."""


    def __init__(
        self,
            api_base_url: str = "http://localhost:8080",
            config_path: str = "rss_feeds_example.json",
            db_path: str = "rss_watcher.db",
            ):
        self.api_base_url = api_base_url
        self.config_path = config_path
        self.db_path = db_path
        self.rss_engine = RSSIntelligenceEngine(config_path = config_path)
        self.running = False
        self.monitoring_interval = 300  # Check every 5 minutes
        self.min_urgency_threshold = 0.5  # Minimum urgency to trigger video

        # Video creation settings
        self.video_settings = {
            "style": "news_analysis",
                "duration": 60,  # 1 minute videos
            "include_affiliates": True,
                }

        # Initialize database
        self._init_database()

        # Background task for continuous monitoring
        self._monitoring_task = None

        logger.info("RSS Watcher Service initialized")


    def _init_database(self):
        """Initialize RSS watcher database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # RSS video triggers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rss_video_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    source_url TEXT NOT NULL,
                    feed_name TEXT NOT NULL,
                    keywords TEXT,
                    urgency_score REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    video_task_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
            )
        """
        )

        # RSS feed items tracking (to avoid duplicates)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rss_feed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_name TEXT NOT NULL,
                    item_url TEXT NOT NULL,
                    item_title TEXT NOT NULL,
                    item_hash TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(feed_name, item_hash)
            )
        """
        )

        # RSS watcher logs
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rss_watcher_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info("RSS Watcher database initialized")


    def _calculate_urgency_score(
        self, article: NewsArticle, feed_config: Dict
    ) -> float:
        """Calculate urgency score for an RSS item."""
        urgency_factors = {
            "recency": 0.0,
                "keyword_relevance": 0.0,
                "feed_priority": 0.0,
                "sentiment": 0.0,
                }

        # Recency factor (newer = higher urgency)
        now = datetime.now()
        age_hours = (now - article.published).total_seconds()/3600
        urgency_factors["recency"] = max(0, 1 - (age_hours / 24))  # Decay over 24 hours

        # Keyword relevance
        high_priority_keywords = [
            "breaking",
                "urgent",
                "alert",
                "developing",
                "exclusive",
                "scandal",
                "crisis",
                "emergency",
                "investigation",
                "leaked",
                ]

        content_text = f"{article.title} {article.content}".lower()
        keyword_matches = sum(
            1 for keyword in high_priority_keywords if keyword in content_text
        )
        urgency_factors["keyword_relevance"] = min(1.0, keyword_matches / 3)

        # Feed priority (from config)
        feed_priority = feed_config.get("priority", 0.5)
        urgency_factors["feed_priority"] = min(1.0, feed_priority)

        # Sentiment factor (extreme sentiment = higher urgency)
        urgency_factors["sentiment"] = min(1.0, abs(article.sentiment_score))

        # Weighted calculation
        weights = {
            "recency": 0.4,
                "keyword_relevance": 0.3,
                "feed_priority": 0.2,
                "sentiment": 0.1,
                }

        urgency_score = sum(
            urgency_factors[factor] * weights[factor] for factor in urgency_factors
        )

        logger.debug(
            f"Urgency calculation for '{article.title[:50]}...': {urgency_factors} -> {urgency_score:.3f}"
        )
        return urgency_score


    def _is_duplicate_item(self, feed_name: str, article: NewsArticle) -> bool:
        """Check if RSS item has already been processed."""
        try:
            # Create a hash from title and URL for duplicate detection
            item_hash = str(hash(f"{article.title}{article.url}"))

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM rss_feed_items
                WHERE feed_name = ? AND item_hash = ?
            """,
                (feed_name, item_hash),
                    )

            count = cursor.fetchone()[0]

            if count == 0:
                # Store new item
                cursor.execute(
                    """
                    INSERT INTO rss_feed_items (feed_name,
    item_url,
    item_title,
    item_hash)
                    VALUES (?, ?, ?, ?)
                """,
                    (feed_name, article.url, article.title, item_hash),
                        )
                conn.commit()

            conn.close()
            return count > 0

        except Exception as e:
            logger.error(f"Error checking duplicate item: {e}")
            return False


    async def _create_video_via_api(self, trigger: RSSVideoTrigger) -> Optional[str]:
        """Create video through the API endpoint."""
        try:
            # Prepare video creation prompt
            prompt = f"""
Create a news analysis video about: {trigger.title}

Description: {trigger.description}

Key points to cover:
- {', '.join(trigger.keywords[:5])}

Source: {trigger.feed_name}
Urgency: {trigger.urgency_score:.2f}

Style: Professional news analysis with Right Perspective approach
"""

            # API payload
            payload = {
                "prompt": prompt,
                    "style": self.video_settings["style"],
                    "duration": self.video_settings["duration"],
                    "include_affiliates": self.video_settings["include_affiliates"],
                    }

            # Make API call
            async with httpx.AsyncClient(timeout = 30.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api / create_video", json = payload
                )

                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get("task_id")

                    logger.info(
                        f"Video creation initiated: {task_id} for trigger {trigger.trigger_id}"
                    )
                    return task_id
                else:
                    logger.error(
                        f"API call failed: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error creating video via API: {e}")
            return None


    def _store_trigger(self, trigger: RSSVideoTrigger) -> bool:
        """Store video trigger in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO rss_video_triggers
                (trigger_id, title, description, source_url, feed_name,
                    keywords, urgency_score, status, video_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    trigger.trigger_id,
                        trigger.title,
                        trigger.description,
                        trigger.source_url,
                        trigger.feed_name,
                        json.dumps(trigger.keywords),
                        trigger.urgency_score,
                        trigger.status,
                        trigger.video_task_id,
                        ),
                    )

            # Log the action
            cursor.execute(
                """
                INSERT INTO rss_watcher_logs (action, details)
                VALUES (?, ?)
            """,
                (
                    "trigger_created",
                        f"Trigger {trigger.trigger_id}: {trigger.title[:50]}... (urgency: {trigger.urgency_score:.3f})",
                        ),
                    )

            conn.commit()
            conn.close()

            logger.info(f"Video trigger stored: {trigger.trigger_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing trigger: {e}")
            return False


    async def _process_rss_feeds(self):
        """Process all RSS feeds and create video triggers."""
        try:
            logger.info("Processing RSS feeds for video triggers...")

            triggers_created = 0

            # Process each configured feed
            for feed_config in self.rss_engine.feeds:
                if not feed_config.get("active", True):
                    continue

                feed_name = feed_config.get("name", feed_config.get("url", "Unknown"))
                logger.debug(f"Processing feed: {feed_name}")

                try:
                    # Parse feed articles
                    articles = self.rss_engine._parse_feed(feed_config)

                    for article in articles:
                        # Skip duplicates
                        if self._is_duplicate_item(feed_name, article):
                            continue

                        # Calculate urgency
                        urgency_score = self._calculate_urgency_score(
                            article, feed_config
                        )

                        # Only create trigger if urgency meets threshold
                        if urgency_score >= self.min_urgency_threshold:
                            # Create trigger
                            trigger_id = (
                                f"rss_{int(time.time())}_{hash(article.url) % 10000}"
                            )

                            trigger = RSSVideoTrigger(
                                trigger_id = trigger_id,
                                    title = article.title,
                                    description=(
                                    article.content[:500] + "..."
                                    if len(article.content) > 500
                                    else article.content
                                ),
                                    source_url = article.url,
                                    feed_name = feed_name,
                                    keywords = article.keywords[:10],  # Limit keywords
                                urgency_score = urgency_score,
                                    created_at = datetime.now(),
                                    )

                            # Create video via API
                            task_id = await self._create_video_via_api(trigger)

                            if task_id:
                                trigger.video_task_id = task_id
                                trigger.status = "processing"
                                triggers_created += 1
                            else:
                                trigger.status = "failed"

                            # Store trigger
                            self._store_trigger(trigger)

                            logger.info(
                                f"Created video trigger: {trigger.title[:50]}... (urgency: {urgency_score:.3f})"
                            )

                except Exception as e:
                    logger.error(f"Error processing feed {feed_name}: {e}")
                    continue

            logger.info(
                f"RSS processing complete. Created {triggers_created} video triggers."
            )

        except Exception as e:
            logger.error(f"Error processing RSS feeds: {e}")


    async def run_continuous_monitoring(self):
        """Run continuous RSS monitoring and video triggering."""
        self.running = True
        logger.info(
            f"Starting RSS watcher (interval: {self.monitoring_interval} seconds)"
        )

        while self.running:
            try:
                await self._process_rss_feeds()

                # Wait for next cycle
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in RSS monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


    def stop_monitoring(self):
        """Stop RSS monitoring."""
        self.running = False
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            self._monitoring_task = None
        logger.info("RSS watcher stopped")
        return {"status": "stopped", "message": "RSS monitoring stopped"}


    def start_monitoring(
        self,
            monitoring_interval: int = None,
            min_urgency_threshold: float = None,
            include_affiliates: bool = None,
            video_duration: int = None,
            ):
        """Start RSS monitoring with optional configuration updates."""
        # Update configuration if provided
        if monitoring_interval is not None:
            self.monitoring_interval = monitoring_interval
        if min_urgency_threshold is not None:
            self.min_urgency_threshold = min_urgency_threshold
        if include_affiliates is not None:
            self.video_settings["include_affiliates"] = include_affiliates
        if video_duration is not None:
            self.video_settings["duration"] = video_duration

        # Stop existing monitoring if running
        if self.running:
            self.stop_monitoring()

        # Start new monitoring task

        import asyncio

        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(self.run_continuous_monitoring())

        logger.info(
            f"RSS monitoring started (interval: {self.monitoring_interval}s,
    threshold: {self.min_urgency_threshold})"
        )
        return {
            "status": "started",
                "message": "RSS monitoring started",
                "config": {
                "monitoring_interval": self.monitoring_interval,
                    "min_urgency_threshold": self.min_urgency_threshold,
                    "include_affiliates": self.video_settings["include_affiliates"],
                    "video_duration": self.video_settings["duration"],
                    },
                }


    def get_status(self):
        """Get current RSS watcher status."""
        recent_triggers = self.get_recent_triggers(limit = 5)

        return {
            "running": self.running,
                "monitoring_interval": self.monitoring_interval,
                "min_urgency_threshold": self.min_urgency_threshold,
                "recent_triggers_count": len(recent_triggers),
                "last_check": recent_triggers[0]["created_at"] if recent_triggers else None,
                "video_settings": self.video_settings,
                }


    def get_recent_triggers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent video triggers."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT trigger_id, title, feed_name, urgency_score,
                    status, video_task_id, created_at
                FROM rss_video_triggers
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
                    )

            results = cursor.fetchall()
            conn.close()

            triggers = []
            for result in results:
                triggers.append(
                    {
                        "trigger_id": result[0],
                            "title": result[1],
                            "feed_name": result[2],
                            "urgency_score": result[3],
                            "status": result[4],
                            "video_task_id": result[5],
                            "created_at": result[6],
                            }
                )

            return triggers

        except Exception as e:
            logger.error(f"Error getting recent triggers: {e}")
            return []

if __name__ == "__main__":
    # Example usage


    async def main():
        watcher = RSSWatcherService()

        # Run a single processing cycle
        print("Running single RSS processing cycle...")
        await watcher._process_rss_feeds()

        # Show recent triggers
        triggers = watcher.get_recent_triggers(5)
        print(f"\\nRecent triggers: {len(triggers)}")
        for trigger in triggers:
            print(
                f"- {trigger['title'][:50]}... (urgency: {trigger['urgency_score']:.3f})"
            )

        # Uncomment to run continuous monitoring
        # await watcher.run_continuous_monitoring()

    asyncio.run(main())