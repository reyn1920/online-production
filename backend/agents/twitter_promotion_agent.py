#!/usr/bin/env python3
"""
TRAE.AI Twitter Promotion Agent

Automatically promotes new YouTube videos on Twitter with intelligent content generation,
hashtag optimization, and engagement tracking.

Features:
- Automatic tweet generation for new YouTube uploads
- AI-powered content optimization using Ollama
- Intelligent hashtag selection and trending analysis
- Media attachment handling (thumbnails)
- Promotion scheduling and queue management
- Performance tracking and analytics

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import os
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.integrations.ollama_integration import OllamaIntegration
from backend.integrations.twitter_integration import (TweetData, TweetType,
                                                      TwitterIntegration)
from backend.secret_store import SecretStore


class PromotionStatus(Enum):
    """Status of promotion campaigns."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PromotionStrategy(Enum):
    """Different promotion strategies."""

    IMMEDIATE = "immediate"  # Post immediately after upload
    SCHEDULED = "scheduled"  # Post at optimal time
    DELAYED = "delayed"  # Post after initial engagement
    SERIES = "series"  # Multi-tweet thread


@dataclass
class VideoMetadata:
    """Metadata for YouTube videos to be promoted."""

    video_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    duration: str
    upload_time: datetime
    tags: List[str]
    category: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0


@dataclass
class PromotionCampaign:
    """A Twitter promotion campaign for a video."""

    campaign_id: str
    video_metadata: VideoMetadata
    strategy: PromotionStrategy
    status: PromotionStatus
    tweet_content: str
    hashtags: List[str]
    scheduled_time: Optional[datetime]
    posted_time: Optional[datetime]
    tweet_id: Optional[str]
    engagement_metrics: Dict[str, int]
    created_at: datetime
    updated_at: datetime


@dataclass
class HashtagAnalysis:
    """Analysis of hashtag performance and trends."""

    hashtag: str
    trend_score: float
    usage_count: int
    engagement_rate: float
    relevance_score: float
    recommended: bool


class TwitterPromotionAgent:
    """
    Intelligent Twitter promotion agent that automatically creates and posts
    promotional tweets for new YouTube videos with AI-powered optimization.
    """

    def __init__(self, db_path: str = "data/promotion_campaigns.sqlite"):
        self.logger = setup_logger("twitter_promotion")
        self.db_path = db_path

        # Initialize integrations
        self.twitter = TwitterIntegration()

        # Initialize Ollama with proper config
        ollama_config = {
            "ollama_endpoint": "http://localhost:11434",
            "default_model": "llama2:7b",
            "max_concurrent_requests": 3,
            "cache_enabled": True,
            "cache_ttl": 3600,
        }
        self.ollama = OllamaIntegration(ollama_config)
        self.secret_store = SecretStore()

        # Configuration
        self.max_tweet_length = 280
        self.max_hashtags = 5
        self.optimal_posting_hours = [9, 12, 15, 18, 21]  # Peak engagement hours

        # Initialize database
        self._init_database()

        self.logger.info("Twitter Promotion Agent initialized")

    def _init_database(self) -> None:
        """
        Initialize the promotion campaigns database.
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Promotion campaigns table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promotion_campaigns (
                campaign_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                video_title TEXT NOT NULL,
                video_url TEXT NOT NULL,
                thumbnail_url TEXT,
                strategy TEXT NOT NULL,
                status TEXT NOT NULL,
                tweet_content TEXT,
                hashtags TEXT,
                scheduled_time TIMESTAMP,
                posted_time TIMESTAMP,
                tweet_id TEXT,
                engagement_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Hashtag performance tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hashtag_performance (
                hashtag TEXT PRIMARY KEY,
                usage_count INTEGER DEFAULT 0,
                total_engagement INTEGER DEFAULT 0,
                avg_engagement_rate REAL DEFAULT 0.0,
                last_used TIMESTAMP,
                trend_score REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Video promotion history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_promotions (
                video_id TEXT PRIMARY KEY,
                first_promoted TIMESTAMP,
                total_promotions INTEGER DEFAULT 0,
                best_performing_tweet TEXT,
                total_engagement INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

        self.logger.info("Promotion database initialized")

    def create_promotion_campaign(
        self,
        video_metadata: VideoMetadata,
        strategy: PromotionStrategy = PromotionStrategy.IMMEDIATE,
    ) -> str:
        """
        Create a new promotion campaign for a YouTube video.

        Args:
            video_metadata (VideoMetadata): Video information
            strategy (PromotionStrategy): Promotion strategy to use

        Returns:
            str: Campaign ID
        """
        try:
            campaign_id = f"promo_{video_metadata.video_id}_{int(time.time())}"

            # Generate optimized tweet content
            tweet_content = self._generate_tweet_content(video_metadata)

            # Select optimal hashtags
            hashtags = self._select_optimal_hashtags(video_metadata)

            # Determine posting time based on strategy
            scheduled_time = self._calculate_optimal_posting_time(strategy)

            # Create campaign
            campaign = PromotionCampaign(
                campaign_id=campaign_id,
                video_metadata=video_metadata,
                strategy=strategy,
                status=PromotionStatus.PENDING,
                tweet_content=tweet_content,
                hashtags=hashtags,
                scheduled_time=scheduled_time,
                posted_time=None,
                tweet_id=None,
                engagement_metrics={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Save to database
            self._save_campaign(campaign)

            self.logger.info(
                f"Created promotion campaign {campaign_id} for video {video_metadata.video_id}"
            )
            return campaign_id

        except Exception as e:
            self.logger.error(f"Failed to create promotion campaign: {e}")
            raise

    def _generate_tweet_content(self, video_metadata: VideoMetadata) -> str:
        """
        Generate optimized tweet content using AI.

        Args:
            video_metadata (VideoMetadata): Video information

        Returns:
            str: Generated tweet content
        """
        try:
            # Create prompt for AI content generation
            prompt = f"""
            Create an engaging Twitter post for this YouTube video:
            
            Title: {video_metadata.title}
            Description: {video_metadata.description[:200]}...
            Category: {video_metadata.category}
            Duration: {video_metadata.duration}
            
            Requirements:
            - Maximum 200 characters (leaving room for hashtags and URL)
            - Engaging and click-worthy
            - Include relevant emojis
            - Maintain professional tone
            - Highlight key value proposition
            - Don't include hashtags (they'll be added separately)
            
            Generate only the tweet text, nothing else.
            """

            # Generate content using Ollama
            response = self.ollama.generate_response(
                prompt=prompt, model="llama3.2:3b", max_tokens=100, temperature=0.7
            )

            # Clean and validate content
            tweet_content = response.strip()
            if len(tweet_content) > 200:
                tweet_content = tweet_content[:197] + "..."

            # Add video URL
            tweet_content += f" {video_metadata.url}"

            return tweet_content

        except Exception as e:
            self.logger.error(f"Failed to generate tweet content: {e}")
            # Fallback to simple format
            return f"New video: {video_metadata.title[:100]} {video_metadata.url}"

    def _select_optimal_hashtags(self, video_metadata: VideoMetadata) -> List[str]:
        """
        Select optimal hashtags based on video content and performance data.

        Args:
            video_metadata (VideoMetadata): Video information

        Returns:
            List[str]: Selected hashtags
        """
        try:
            # Get hashtag candidates from video tags and AI analysis
            candidates = set()

            # Add video tags as candidates
            for tag in video_metadata.tags[:10]:  # Limit to prevent overflow
                if len(tag) > 2 and len(tag) < 20:  # Reasonable hashtag length
                    candidates.add(tag.lower().replace(" ", "").replace("-", ""))

            # Generate additional hashtags using AI
            ai_hashtags = self._generate_ai_hashtags(video_metadata)
            candidates.update(ai_hashtags)

            # Add category-based hashtags
            category_hashtags = self._get_category_hashtags(video_metadata.category)
            candidates.update(category_hashtags)

            # Analyze and rank hashtags
            hashtag_scores = []
            for hashtag in candidates:
                if hashtag:
                    analysis = self._analyze_hashtag_performance(hashtag)
                    hashtag_scores.append(
                        (hashtag, analysis.relevance_score + analysis.trend_score)
                    )

            # Sort by score and select top hashtags
            hashtag_scores.sort(key=lambda x: x[1], reverse=True)
            selected_hashtags = [
                f"#{hashtag}" for hashtag, _ in hashtag_scores[: self.max_hashtags]
            ]

            # Ensure we have at least some basic hashtags
            if not selected_hashtags:
                selected_hashtags = ["#YouTube", "#NewVideo"]

            return selected_hashtags

        except Exception as e:
            self.logger.error(f"Failed to select hashtags: {e}")
            return ["#YouTube", "#NewVideo"]

    def _generate_ai_hashtags(self, video_metadata: VideoMetadata) -> List[str]:
        """
        Generate relevant hashtags using AI analysis.

        Args:
            video_metadata (VideoMetadata): Video information

        Returns:
            List[str]: AI-generated hashtags
        """
        try:
            prompt = f"""
            Generate 5 relevant hashtags for this YouTube video:
            
            Title: {video_metadata.title}
            Description: {video_metadata.description[:150]}
            Category: {video_metadata.category}
            
            Requirements:
            - Hashtags should be relevant and popular
            - No spaces or special characters
            - 3-15 characters each
            - Don't include # symbol
            - One hashtag per line
            
            Generate only the hashtag words, nothing else.
            """

            response = self.ollama.generate_response(
                prompt=prompt, model="llama3.2:3b", max_tokens=50, temperature=0.5
            )

            # Parse hashtags from response
            hashtags = []
            for line in response.strip().split("\n"):
                hashtag = line.strip().lower().replace("#", "").replace(" ", "")
                if hashtag and len(hashtag) >= 3 and len(hashtag) <= 15:
                    hashtags.append(hashtag)

            return hashtags[:5]

        except Exception as e:
            self.logger.error(f"Failed to generate AI hashtags: {e}")
            return []

    def _get_category_hashtags(self, category: str) -> List[str]:
        """
        Get relevant hashtags based on video category.

        Args:
            category (str): Video category

        Returns:
            List[str]: Category-specific hashtags
        """
        category_map = {
            "Education": ["education", "learning", "tutorial", "howto"],
            "Entertainment": ["entertainment", "fun", "viral", "trending"],
            "Gaming": ["gaming", "gamer", "gameplay", "esports"],
            "Technology": ["tech", "technology", "innovation", "digital"],
            "Music": ["music", "song", "artist", "audio"],
            "Sports": ["sports", "fitness", "athlete", "training"],
            "News": ["news", "breaking", "update", "current"],
            "Comedy": ["comedy", "funny", "humor", "laugh"],
        }

        return category_map.get(category, ["content", "video"])

    def _analyze_hashtag_performance(self, hashtag: str) -> HashtagAnalysis:
        """
        Analyze hashtag performance based on historical data.

        Args:
            hashtag (str): Hashtag to analyze

        Returns:
            HashtagAnalysis: Performance analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM hashtag_performance WHERE hashtag = ?", (hashtag,)
            )
            result = cursor.fetchone()

            if result:
                usage_count = result[1]
                total_engagement = result[2]
                avg_engagement_rate = result[3]
                trend_score = result[5]

                # Calculate relevance based on recent usage
                relevance_score = min(usage_count / 10.0, 1.0)

                recommended = avg_engagement_rate > 0.05 and trend_score > 0.3
            else:
                # New hashtag - assign default values
                usage_count = 0
                avg_engagement_rate = 0.5  # Neutral starting point
                trend_score = 0.5
                relevance_score = 0.3  # Lower for untested hashtags
                recommended = False

            conn.close()

            return HashtagAnalysis(
                hashtag=hashtag,
                trend_score=trend_score,
                usage_count=usage_count,
                engagement_rate=avg_engagement_rate,
                relevance_score=relevance_score,
                recommended=recommended,
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze hashtag {hashtag}: {e}")
            return HashtagAnalysis(
                hashtag=hashtag,
                trend_score=0.5,
                usage_count=0,
                engagement_rate=0.5,
                relevance_score=0.3,
                recommended=False,
            )

    def _calculate_optimal_posting_time(
        self, strategy: PromotionStrategy
    ) -> Optional[datetime]:
        """
        Calculate optimal posting time based on strategy.

        Args:
            strategy (PromotionStrategy): Promotion strategy

        Returns:
            Optional[datetime]: Scheduled posting time
        """
        now = datetime.now()

        if strategy == PromotionStrategy.IMMEDIATE:
            return None  # Post immediately

        elif strategy == PromotionStrategy.SCHEDULED:
            # Find next optimal hour
            current_hour = now.hour
            next_optimal_hours = [
                h for h in self.optimal_posting_hours if h > current_hour
            ]

            if next_optimal_hours:
                target_hour = next_optimal_hours[0]
                scheduled_time = now.replace(
                    hour=target_hour, minute=0, second=0, microsecond=0
                )
            else:
                # Next day's first optimal hour
                target_hour = self.optimal_posting_hours[0]
                scheduled_time = (now + timedelta(days=1)).replace(
                    hour=target_hour, minute=0, second=0, microsecond=0
                )

            return scheduled_time

        elif strategy == PromotionStrategy.DELAYED:
            # Post 2-4 hours after upload
            return now + timedelta(hours=3)

        else:
            return None

    def _save_campaign(self, campaign: PromotionCampaign) -> None:
        """
        Save promotion campaign to database.

        Args:
            campaign (PromotionCampaign): Campaign to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO promotion_campaigns (
                    campaign_id, video_id, video_title, video_url, thumbnail_url,
                    strategy, status, tweet_content, hashtags, scheduled_time,
                    posted_time, tweet_id, engagement_metrics, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    campaign.campaign_id,
                    campaign.video_metadata.video_id,
                    campaign.video_metadata.title,
                    campaign.video_metadata.url,
                    campaign.video_metadata.thumbnail_url,
                    campaign.strategy.value,
                    campaign.status.value,
                    campaign.tweet_content,
                    json.dumps(campaign.hashtags),
                    campaign.scheduled_time,
                    campaign.posted_time,
                    campaign.tweet_id,
                    json.dumps(campaign.engagement_metrics),
                    datetime.now(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to save campaign: {e}")
            raise

    def execute_promotion(self, campaign_id: str) -> bool:
        """
        Execute a promotion campaign by posting the tweet.

        Args:
            campaign_id (str): Campaign ID to execute

        Returns:
            bool: True if successful
        """
        try:
            # Load campaign
            campaign = self._load_campaign(campaign_id)
            if not campaign:
                self.logger.error(f"Campaign {campaign_id} not found")
                return False

            # Check if already posted
            if campaign.status == PromotionStatus.POSTED:
                self.logger.warning(f"Campaign {campaign_id} already posted")
                return True

            # Prepare tweet data
            full_text = campaign.tweet_content
            if campaign.hashtags:
                hashtag_text = " ".join(campaign.hashtags)
                # Ensure we don't exceed character limit
                if len(full_text) + len(hashtag_text) + 1 <= self.max_tweet_length:
                    full_text += f" {hashtag_text}"

            tweet_data = TweetData(
                text=full_text,
                tweet_type=TweetType.PROMOTION,
                hashtags=None,  # Already included in text
            )

            # Post tweet
            result = self.twitter.post_tweet(tweet_data)
            tweet_id = result.get("data", {}).get("id")

            if tweet_id:
                # Update campaign status
                campaign.status = PromotionStatus.POSTED
                campaign.posted_time = datetime.now()
                campaign.tweet_id = tweet_id
                campaign.updated_at = datetime.now()

                self._save_campaign(campaign)

                # Update hashtag performance
                self._update_hashtag_usage(campaign.hashtags)

                self.logger.info(
                    f"Successfully posted promotion for campaign {campaign_id}"
                )
                return True
            else:
                # Mark as failed
                campaign.status = PromotionStatus.FAILED
                campaign.updated_at = datetime.now()
                self._save_campaign(campaign)

                self.logger.error(f"Failed to post tweet for campaign {campaign_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to execute promotion {campaign_id}: {e}")
            return False

    def _load_campaign(self, campaign_id: str) -> Optional[PromotionCampaign]:
        """
        Load campaign from database.

        Args:
            campaign_id (str): Campaign ID

        Returns:
            Optional[PromotionCampaign]: Loaded campaign or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM promotion_campaigns WHERE campaign_id = ?",
                (campaign_id,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            # Reconstruct campaign object
            video_metadata = VideoMetadata(
                video_id=result[1],
                title=result[2],
                description="",  # Not stored separately
                url=result[3],
                thumbnail_url=result[4] or "",
                duration="",  # Not stored separately
                upload_time=datetime.now(),  # Approximate
                tags=[],  # Not stored separately
                category="",  # Not stored separately
            )

            campaign = PromotionCampaign(
                campaign_id=result[0],
                video_metadata=video_metadata,
                strategy=PromotionStrategy(result[5]),
                status=PromotionStatus(result[6]),
                tweet_content=result[7] or "",
                hashtags=json.loads(result[8]) if result[8] else [],
                scheduled_time=datetime.fromisoformat(result[9]) if result[9] else None,
                posted_time=datetime.fromisoformat(result[10]) if result[10] else None,
                tweet_id=result[11],
                engagement_metrics=json.loads(result[12]) if result[12] else {},
                created_at=datetime.fromisoformat(result[13]),
                updated_at=datetime.fromisoformat(result[14]),
            )

            return campaign

        except Exception as e:
            self.logger.error(f"Failed to load campaign {campaign_id}: {e}")
            return None

    def _update_hashtag_usage(self, hashtags: List[str]) -> None:
        """
        Update hashtag usage statistics.

        Args:
            hashtags (List[str]): Used hashtags
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for hashtag in hashtags:
                clean_hashtag = hashtag.lstrip("#").lower()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO hashtag_performance (
                        hashtag, usage_count, last_used, updated_at
                    ) VALUES (
                        ?, 
                        COALESCE((SELECT usage_count FROM hashtag_performance WHERE hashtag = ?), 0) + 1,
                        ?, ?
                    )
                """,
                    (clean_hashtag, clean_hashtag, datetime.now(), datetime.now()),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to update hashtag usage: {e}")

    def process_pending_campaigns(self) -> int:
        """
        Process all pending and scheduled campaigns.

        Returns:
            int: Number of campaigns processed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get campaigns ready for posting
            now = datetime.now()
            cursor.execute(
                """
                SELECT campaign_id FROM promotion_campaigns 
                WHERE status IN ('pending', 'scheduled') 
                AND (scheduled_time IS NULL OR scheduled_time <= ?)
                ORDER BY created_at ASC
            """,
                (now,),
            )

            campaign_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            processed = 0
            for campaign_id in campaign_ids:
                if self.execute_promotion(campaign_id):
                    processed += 1
                    # Add delay between posts to avoid rate limiting
                    time.sleep(2)

            if processed > 0:
                self.logger.info(f"Processed {processed} promotion campaigns")

            return processed

        except Exception as e:
            self.logger.error(f"Failed to process pending campaigns: {e}")
            return 0

    def get_campaign_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for promotion campaigns.

        Args:
            days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            # Get campaign statistics
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_campaigns,
                    SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as successful_posts,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_posts,
                    AVG(CASE WHEN status = 'posted' THEN 
                        (julianday(posted_time) - julianday(created_at)) * 24 
                        ELSE NULL END) as avg_posting_delay_hours
                FROM promotion_campaigns 
                WHERE created_at >= ?
            """,
                (cutoff_date,),
            )

            stats = cursor.fetchone()

            # Get top performing hashtags
            cursor.execute(
                """
                SELECT hashtag, usage_count, avg_engagement_rate 
                FROM hashtag_performance 
                WHERE updated_at >= ?
                ORDER BY avg_engagement_rate DESC 
                LIMIT 10
            """,
                (cutoff_date,),
            )

            top_hashtags = cursor.fetchall()

            conn.close()

            return {
                "period_days": days,
                "total_campaigns": stats[0] or 0,
                "successful_posts": stats[1] or 0,
                "failed_posts": stats[2] or 0,
                "success_rate": (stats[1] / stats[0]) if stats[0] > 0 else 0,
                "avg_posting_delay_hours": stats[3] or 0,
                "top_hashtags": [
                    {
                        "hashtag": row[0],
                        "usage_count": row[1],
                        "engagement_rate": row[2],
                    }
                    for row in top_hashtags
                ],
            }

        except Exception as e:
            self.logger.error(f"Failed to get campaign analytics: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Initialize promotion agent
    agent = TwitterPromotionAgent()

    # Example video metadata
    video = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Amazing AI Tutorial - Learn Machine Learning in 10 Minutes!",
        description="Complete guide to machine learning basics with practical examples...",
        url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        duration="10:30",
        upload_time=datetime.now(),
        tags=["AI", "MachineLearning", "Tutorial", "Programming"],
        category="Education",
    )

    # Create and execute promotion
    try:
        campaign_id = agent.create_promotion_campaign(
            video, PromotionStrategy.IMMEDIATE
        )
        print(f"✓ Created campaign: {campaign_id}")

        success = agent.execute_promotion(campaign_id)
        print(f"✓ Promotion {'successful' if success else 'failed'}")

        # Get analytics
        analytics = agent.get_campaign_analytics(7)
        print(f"✓ Analytics: {analytics}")

    except Exception as e:
        print(f"✗ Error: {e}")
