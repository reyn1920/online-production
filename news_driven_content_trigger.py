#!/usr/bin/env python3
"""
News-Driven Content Trigger Service

This service continuously monitors political RSS feeds and automatically triggers
Right Perspective video content creation when breaking news or trending political
topics are detected.
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

from breaking_news_watcher import NewsArticle, RSSIntelligenceEngine, TrendData

logger = get_logger(__name__)


@dataclass
class ContentTrigger:
    """Represents a content creation trigger based on news events."""

    trigger_id: str
    topic: str
    urgency_score: float
    article_count: int
    trend_score: float
    keywords: List[str]
    sources: List[str]
    created_at: datetime
    content_type: str = "right_perspective_video"
    status: str = "pending"


class NewsDrivenContentTrigger:
    """Service that monitors political news and triggers Right Perspective content creation."""

    def __init__(self, config_path: str = "rss_feeds_example.json"):
        self.config_path = config_path
        self.rss_engine = RSSIntelligenceEngine(config_path=config_path)
        self.running = False
        self.monitoring_interval = 15  # Check every 15 minutes
        self.urgency_threshold = 0.7  # Minimum urgency score to trigger content
        self.political_keywords = [
            "biden",
            "trump",
            "congress",
            "senate",
            "house",
            "election",
            "vote",
            "voting",
            "democrat",
            "republican",
            "politics",
            "political",
            "government",
            "federal",
            "supreme court",
            "legislation",
            "bill",
            "law",
            "policy",
            "campaign",
            "scandal",
            "investigation",
            "impeachment",
            "corruption",
            "controversy",
            "debate",
            "primary",
            "caucus",
            "poll",
            "polling",
            "approval rating",
        ]

        # Initialize trigger database
        self._init_trigger_database()

        logger.info("News-Driven Content Trigger Service initialized")

    def _init_trigger_database(self):
        """Initialize database tables for content triggers."""
        conn = sqlite3.connect("right_perspective.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id TEXT UNIQUE NOT NULL,
                topic TEXT NOT NULL,
                urgency_score REAL NOT NULL,
                article_count INTEGER NOT NULL,
                trend_score REAL NOT NULL,
                keywords TEXT NOT NULL,
                sources TEXT NOT NULL,
                content_type TEXT DEFAULT 'right_perspective_video',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                video_created BOOLEAN DEFAULT FALSE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trigger_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info("Content trigger database initialized")

    def _calculate_urgency_score(
        self, articles: List[NewsArticle], trend_data: Optional[TrendData]
    ) -> float:
        """Calculate urgency score based on article characteristics and trends."""
        if not articles:
            return 0.0

        urgency_factors = {
            "recency": 0.0,
            "volume": 0.0,
            "sentiment": 0.0,
            "trend": 0.0,
            "political_relevance": 0.0,
        }

        # Recency factor (newer articles get higher scores)
        now = datetime.now()
        avg_age_hours = sum(
            [(now - article.published).total_seconds() / 3600 for article in articles]
        ) / len(articles)
        urgency_factors["recency"] = max(
            0, 1 - (avg_age_hours / 24)
        )  # Decay over 24 hours

        # Volume factor (more articles = higher urgency)
        urgency_factors["volume"] = min(1.0, len(articles) / 10)  # Cap at 10 articles

        # Sentiment factor (extreme sentiment = higher urgency)
        avg_sentiment = sum(
            [abs(article.sentiment_score) for article in articles]
        ) / len(articles)
        urgency_factors["sentiment"] = min(1.0, avg_sentiment)

        # Trend factor
        if trend_data:
            urgency_factors["trend"] = min(1.0, trend_data.trend_score / 100)

        # Political relevance factor
        political_keyword_count = 0
        total_content = " ".join(
            [f"{article.title} {article.content}" for article in articles]
        ).lower()
        for keyword in self.political_keywords:
            if keyword in total_content:
                political_keyword_count += 1

        urgency_factors["political_relevance"] = min(
            1.0, political_keyword_count / len(self.political_keywords)
        )

        # Weighted average
        weights = {
            "recency": 0.3,
            "volume": 0.2,
            "sentiment": 0.2,
            "trend": 0.15,
            "political_relevance": 0.15,
        }

        urgency_score = sum(
            [urgency_factors[factor] * weights[factor] for factor in urgency_factors]
        )

        logger.debug(f"Urgency calculation: {urgency_factors} -> {urgency_score:.3f}")
        return urgency_score

    def _extract_topic_from_articles(self, articles: List[NewsArticle]) -> str:
        """Extract main topic from a collection of articles."""
        if not articles:
            return "Unknown Topic"

        # Simple approach: use most common keywords
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.keywords)

        if not all_keywords:
            # Fallback to first article title
            return articles[0].title[:50] + "..."

        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Get top keywords
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[
            :3
        ]
        topic = ", ".join([kw[0] for kw in top_keywords])

        return topic if topic else articles[0].title[:50] + "..."

    def _create_content_trigger(
        self, articles: List[NewsArticle], trend_data: Optional[TrendData]
    ) -> ContentTrigger:
        """Create a content trigger from news articles and trend data."""
        urgency_score = self._calculate_urgency_score(articles, trend_data)
        topic = self._extract_topic_from_articles(articles)

        # Extract unique keywords and sources
        all_keywords = set()
        all_sources = set()

        for article in articles:
            all_keywords.update(article.keywords)
            all_sources.add(article.source)

        trigger_id = f"trigger_{int(time.time())}_{hash(topic) % 10000}"

        trigger = ContentTrigger(
            trigger_id=trigger_id,
            topic=topic,
            urgency_score=urgency_score,
            article_count=len(articles),
            trend_score=trend_data.trend_score if trend_data else 0.0,
            keywords=list(all_keywords)[:10],  # Limit to top 10 keywords
            sources=list(all_sources),
            created_at=datetime.now(),
        )

        return trigger

    def _store_trigger(self, trigger: ContentTrigger) -> bool:
        """Store content trigger in database."""
        try:
            conn = sqlite3.connect("right_perspective.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO content_triggers 
                (trigger_id, topic, urgency_score, article_count, trend_score, 
                 keywords, sources, content_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    trigger.trigger_id,
                    trigger.topic,
                    trigger.urgency_score,
                    trigger.article_count,
                    trigger.trend_score,
                    json.dumps(trigger.keywords),
                    json.dumps(trigger.sources),
                    trigger.content_type,
                    trigger.status,
                ),
            )

            # Log trigger creation
            cursor.execute(
                """
                INSERT INTO trigger_history (trigger_id, action, details)
                VALUES (?, ?, ?)
            """,
                (
                    trigger.trigger_id,
                    "created",
                    f"Urgency: {trigger.urgency_score:.3f}, Articles: {trigger.article_count}",
                ),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Content trigger stored: {trigger.trigger_id} - {trigger.topic}"
            )
            return True

        except Exception as e:
            logger.error(f"Error storing content trigger: {e}")
            return False

    async def _trigger_content_creation(self, trigger: ContentTrigger) -> bool:
        """Trigger Right Perspective video content creation."""
        try:
            # Import here to avoid circular imports
            from backend.agents.base_agents import PlannerAgent
            from backend.agents.specialized_agents import ContentAgent

            logger.info(f"Triggering content creation for: {trigger.topic}")

            # Create content requirements
            requirements = {
                "content_type": "right_perspective_video",
                "topic": trigger.topic,
                "urgency_score": trigger.urgency_score,
                "keywords": trigger.keywords,
                "sources": trigger.sources,
                "trigger_id": trigger.trigger_id,
                "breaking_news": True,
                "political_content": True,
            }

            # Initialize agents
            planner = PlannerAgent()
            content_agent = ContentAgent()

            # Create protected Right Perspective plan
            plan = await planner._create_protected_right_perspective_plan(
                requirements=requirements, priority=planner.TaskPriority.HIGH
            )

            # Execute the plan
            result = await planner.execute_plan(plan)

            if result.get("success", False):
                # Update trigger status
                conn = sqlite3.connect("right_perspective.db")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE content_triggers 
                    SET status = 'completed', processed_at = CURRENT_TIMESTAMP, video_created = TRUE
                    WHERE trigger_id = ?
                """,
                    (trigger.trigger_id,),
                )

                cursor.execute(
                    """
                    INSERT INTO trigger_history (trigger_id, action, details)
                    VALUES (?, ?, ?)
                """,
                    (
                        trigger.trigger_id,
                        "content_created",
                        f"Video creation successful: {result.get('video_id', 'unknown')}",
                    ),
                )

                conn.commit()
                conn.close()

                logger.info(
                    f"Content creation successful for trigger: {trigger.trigger_id}"
                )
                return True
            else:
                logger.error(
                    f"Content creation failed for trigger: {trigger.trigger_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error triggering content creation: {e}")
            return False

    async def _monitor_political_news(self):
        """Monitor political news feeds and create triggers."""
        try:
            logger.info("Monitoring political news feeds...")

            # Parse all RSS feeds
            all_articles = []
            for feed_config in self.rss_engine.feeds:
                if feed_config.get("category") == "politics" and feed_config.get(
                    "active", True
                ):
                    articles = self.rss_engine._parse_feed(feed_config)
                    all_articles.extend(articles)

                    # Store articles in database
                    for article in articles:
                        self.rss_engine._store_article(article)

            if not all_articles:
                logger.info("No new political articles found")
                return

            logger.info(f"Found {len(all_articles)} new political articles")

            # Update trend analysis
            self.rss_engine._update_trend_analysis(all_articles)

            # Group articles by topic/keywords for trigger creation
            topic_groups = self._group_articles_by_topic(all_articles)

            for topic, articles in topic_groups.items():
                if len(articles) >= 2:  # Require at least 2 articles for a trigger
                    # Get trend data for this topic
                    trend_data = self._get_trend_data_for_topic(topic)

                    # Create content trigger
                    trigger = self._create_content_trigger(articles, trend_data)

                    # Check if trigger meets urgency threshold
                    if trigger.urgency_score >= self.urgency_threshold:
                        # Store trigger
                        if self._store_trigger(trigger):
                            # Trigger content creation
                            await self._trigger_content_creation(trigger)
                        else:
                            logger.error(f"Failed to store trigger for topic: {topic}")
                    else:
                        logger.info(
                            f"Topic '{topic}' urgency score {trigger.urgency_score:.3f} below threshold {self.urgency_threshold}"
                        )

        except Exception as e:
            logger.error(f"Error monitoring political news: {e}")

    def _group_articles_by_topic(
        self, articles: List[NewsArticle]
    ) -> Dict[str, List[NewsArticle]]:
        """Group articles by similar topics/keywords."""
        topic_groups = {}

        for article in articles:
            # Simple grouping by first keyword or title words
            if article.keywords:
                primary_keyword = article.keywords[0]
            else:
                # Fallback to first significant word in title
                title_words = article.title.lower().split()
                primary_keyword = next(
                    (word for word in title_words if len(word) > 4), "general"
                )

            if primary_keyword not in topic_groups:
                topic_groups[primary_keyword] = []

            topic_groups[primary_keyword].append(article)

        return topic_groups

    def _get_trend_data_for_topic(self, topic: str) -> Optional[TrendData]:
        """Get trend data for a specific topic."""
        try:
            conn = sqlite3.connect("right_perspective.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT keyword, frequency, trend_score, first_seen, last_seen, sources, related_articles
                FROM trend_analysis
                WHERE keyword LIKE ?
                ORDER BY trend_score DESC
                LIMIT 1
            """,
                (f"%{topic}%",),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return TrendData(
                    keyword=result[0],
                    frequency=result[1],
                    trend_score=result[2],
                    first_seen=datetime.fromisoformat(result[3]),
                    last_seen=datetime.fromisoformat(result[4]),
                    sources=json.loads(result[5]) if result[5] else [],
                    related_articles=json.loads(result[6]) if result[6] else [],
                )

            return None

        except Exception as e:
            logger.error(f"Error getting trend data for topic '{topic}': {e}")
            return None

    async def run_continuous_monitoring(self):
        """Run continuous political news monitoring and content triggering."""
        self.running = True
        logger.info(
            f"Starting continuous political news monitoring (interval: {self.monitoring_interval} minutes)"
        )

        while self.running:
            try:
                await self._monitor_political_news()

                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval * 60)

            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.running = False
        logger.info("Political news monitoring stopped")

    def get_pending_triggers(self) -> List[Dict[str, Any]]:
        """Get all pending content triggers."""
        try:
            conn = sqlite3.connect("right_perspective.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT trigger_id, topic, urgency_score, article_count, trend_score, 
                       keywords, sources, created_at, status
                FROM content_triggers
                WHERE status = 'pending'
                ORDER BY urgency_score DESC, created_at DESC
            """
            )

            results = cursor.fetchall()
            conn.close()

            triggers = []
            for result in results:
                triggers.append(
                    {
                        "trigger_id": result[0],
                        "topic": result[1],
                        "urgency_score": result[2],
                        "article_count": result[3],
                        "trend_score": result[4],
                        "keywords": json.loads(result[5]) if result[5] else [],
                        "sources": json.loads(result[6]) if result[6] else [],
                        "created_at": result[7],
                        "status": result[8],
                    }
                )

            return triggers

        except Exception as e:
            logger.error(f"Error getting pending triggers: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    async def main():
        trigger_service = NewsDrivenContentTrigger()

        # Run a single monitoring cycle
        print("Running single political news monitoring cycle...")
        await trigger_service._monitor_political_news()

        # Show pending triggers
        pending_triggers = trigger_service.get_pending_triggers()
        print(f"\nPending triggers: {len(pending_triggers)}")
        for trigger in pending_triggers:
            print(f"- {trigger['topic']}: urgency {trigger['urgency_score']:.3f}")

        # Uncomment to run continuous monitoring
        # await trigger_service.run_continuous_monitoring()

    asyncio.run(main())
