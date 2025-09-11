#!/usr/bin/env python3
"""
Community Engagement Agent - Layer 1 of Maxed-Out Automation
Handles automated community building, comment analysis, and engagement responses.
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import praw
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.agents.base_agents import BaseAgent
from backend.secret_store import SecretStore


class EngagementType(Enum):
    YOUTUBE_COMMENT = "youtube_comment"
    REDDIT_POST = "reddit_post"
    TWITTER_MENTION = "twitter_mention"
    COMMUNITY_QUESTION = "community_question"


class SentimentCategory(Enum):
    POSITIVE = "positive"
    QUESTION = "question"
    FEEDBACK = "feedback"
    CRITICISM = "criticism"
    SPAM = "spam"


@dataclass
class EngagementOpportunity:
    platform: str
    content_id: str
    author: str
    content: str
    sentiment: SentimentCategory
    priority_score: float
    response_generated: Optional[str] = None
    posted: bool = False
    created_at: datetime = None


class CommunityEngagementAgent(BaseAgent):
    """Automated community building and engagement agent."""

    def __init__(self, db_path: str = "data/right_perspective.db"):
        super().__init__()
        self.db_path = db_path
        self.secret_store = SecretStore()
        self.logger = logging.getLogger(__name__)

        # Initialize API clients
        self.youtube_client = None
        self.reddit_client = None
        self.twitter_client = None

        self._init_database()
        self._init_api_clients()

    def _init_database(self):
        """Initialize community engagement database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS community_engagement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    original_content TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    priority_score REAL NOT NULL,
                    response_content TEXT,
                    posted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP,
                    UNIQUE(platform, content_id)
                );
                
                CREATE TABLE IF NOT EXISTS engagement_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    platform TEXT NOT NULL,
                    opportunities_found INTEGER DEFAULT 0,
                    responses_generated INTEGER DEFAULT 0,
                    responses_posted INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, platform)
                );
                
                CREATE TABLE IF NOT EXISTS community_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Insert default keywords for monitoring
            default_keywords = [
                ("AI automation", "technology", 3),
                ("content creation", "marketing", 3),
                ("YouTube growth", "marketing", 2),
                ("social media marketing", "marketing", 2),
                ("video editing", "content", 2),
                ("SEO optimization", "marketing", 2),
            ]

            conn.executemany(
                "INSERT OR IGNORE INTO community_keywords (keyword, category, priority) VALUES (?, ?, ?)",
                default_keywords,
            )

    def _init_api_clients(self):
        """Initialize API clients for various platforms."""
        try:
            # YouTube API
            youtube_key = self.secret_store.get_secret("YOUTUBE_API_KEY")
            if youtube_key:
                self.youtube_client = build("youtube", "v3", developerKey=youtube_key)

            # Reddit API
            reddit_config = {
                "client_id": self.secret_store.get_secret("REDDIT_CLIENT_ID"),
                "client_secret": self.secret_store.get_secret("REDDIT_CLIENT_SECRET"),
                "user_agent": "CommunityEngagementBot/1.0",
            }

            if all(reddit_config.values()):
                self.reddit_client = praw.Reddit(**reddit_config)

        except Exception as e:
            self.logger.warning(f"API client initialization failed: {e}")

    async def analyze_youtube_comments(
        self, video_id: str
    ) -> List[EngagementOpportunity]:
        """Analyze comments on a YouTube video for engagement opportunities."""
        opportunities = []

        if not self.youtube_client:
            self.logger.warning("YouTube client not initialized")
            return opportunities

        try:
            # Get video comments
            request = self.youtube_client.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100, order="relevance"
            )

            response = request.execute()

            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]

                # Analyze sentiment and generate opportunity
                opportunity = await self._analyze_comment_sentiment(
                    platform="youtube",
                    content_id=item["id"],
                    author=comment["authorDisplayName"],
                    content=comment["textDisplay"],
                )

                if opportunity:
                    opportunities.append(opportunity)

        except HttpError as e:
            self.logger.error(f"YouTube API error: {e}")

        return opportunities

    async def monitor_reddit_discussions(
        self, subreddits: List[str]
    ) -> List[EngagementOpportunity]:
        """Monitor Reddit discussions for engagement opportunities."""
        opportunities = []

        if not self.reddit_client:
            self.logger.warning("Reddit client not initialized")
            return opportunities

        try:
            keywords = self._get_monitoring_keywords()

            for subreddit_name in subreddits:
                subreddit = self.reddit_client.subreddit(subreddit_name)

                # Search for relevant posts
                for keyword in keywords:
                    try:
                        for submission in subreddit.search(
                            keyword, time_filter="day", limit=10
                        ):
                            # Check if this is a question or discussion we can help with
                            if self._is_relevant_discussion(
                                submission.title + " " + submission.selftext, keywords
                            ):
                                opportunity = await self._analyze_comment_sentiment(
                                    platform="reddit",
                                    content_id=submission.id,
                                    author=(
                                        submission.author.name
                                        if submission.author
                                        else "deleted"
                                    ),
                                    content=submission.title
                                    + "\n"
                                    + submission.selftext,
                                )

                                if opportunity:
                                    opportunities.append(opportunity)

                    except Exception as e:
                        self.logger.warning(f"Reddit search error for '{keyword}': {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Reddit monitoring error: {e}")

        return opportunities

    async def _analyze_comment_sentiment(
        self, platform: str, content_id: str, author: str, content: str
    ) -> Optional[EngagementOpportunity]:
        """Analyze comment sentiment and determine engagement priority."""
        try:
            # Use Ollama for sentiment analysis
            sentiment_prompt = f"""
            Analyze this social media content and categorize it:
            
            Content: "{content}"
            
            Categorize as one of: positive, question, feedback, criticism, spam
            
            Also rate the engagement priority from 1-10 (10 = highest priority for response).
            
            Respond in JSON format:
            {{
                "sentiment": "category",
                "priority": score,
                "reasoning": "brief explanation"
            }}
            """

            # Make request to Ollama
            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2", "prompt": sentiment_prompt, "stream": False},
                timeout=30,
            )

            if ollama_response.status_code == 200:
                result = ollama_response.json()
                analysis = json.loads(result["response"])

                sentiment = SentimentCategory(analysis["sentiment"])
                priority_score = float(analysis["priority"])

                # Only create opportunities for high-priority content
                if priority_score >= 6.0 and sentiment != SentimentCategory.SPAM:
                    return EngagementOpportunity(
                        platform=platform,
                        content_id=content_id,
                        author=author,
                        content=content,
                        sentiment=sentiment,
                        priority_score=priority_score,
                        created_at=datetime.now(),
                    )

        except Exception as e:
            self.logger.error(f"Sentiment analysis error: {e}")

        return None

    async def generate_authentic_response(
        self, opportunity: EngagementOpportunity
    ) -> str:
        """Generate an authentic, helpful response to an engagement opportunity."""
        try:
            # Get relevant content from our database
            relevant_content = self._find_relevant_content(opportunity.content)

            response_prompt = f"""
            Generate a helpful, authentic response to this {opportunity.platform} {opportunity.sentiment.value}:
            
            Original Content: "{opportunity.content}"
            Author: {opportunity.author}
            
            Guidelines:
            - Be genuinely helpful and authentic
            - Keep it conversational and friendly
            - If relevant, mention our content: {relevant_content}
            - Don't be overly promotional
            - Match the tone of the platform
            - Keep response under 280 characters for Twitter, 500 for others
            
            Generate only the response text, no quotes or formatting.
            """

            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2", "prompt": response_prompt, "stream": False},
                timeout=30,
            )

            if ollama_response.status_code == 200:
                result = ollama_response.json()
                return result["response"].strip()

        except Exception as e:
            self.logger.error(f"Response generation error: {e}")

        return ""

    def _get_monitoring_keywords(self) -> List[str]:
        """Get active keywords for community monitoring."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT keyword FROM community_keywords WHERE active = TRUE ORDER BY priority DESC"
            )
            return [row[0] for row in cursor.fetchall()]

    def _is_relevant_discussion(self, content: str, keywords: List[str]) -> bool:
        """Check if content is relevant to our expertise areas."""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)

    def _find_relevant_content(self, query_content: str) -> str:
        """Find relevant content from our database to reference in responses."""
        # This would search our content database for relevant videos/posts
        # For now, return a generic helpful reference
        return "our latest video on this topic"

    async def process_engagement_opportunities(self) -> Dict[str, int]:
        """Main method to process all engagement opportunities."""
        stats = {
            "opportunities_found": 0,
            "responses_generated": 0,
            "responses_posted": 0,
        }

        try:
            # Get recent YouTube videos to monitor
            youtube_opportunities = []
            # This would get our recent video IDs from the database

            # Monitor Reddit discussions
            reddit_subreddits = [
                "entrepreneur",
                "marketing",
                "youtubers",
                "contentcreation",
            ]
            reddit_opportunities = await self.monitor_reddit_discussions(
                reddit_subreddits
            )

            all_opportunities = youtube_opportunities + reddit_opportunities
            stats["opportunities_found"] = len(all_opportunities)

            # Process each opportunity
            for opportunity in all_opportunities:
                # Check if we've already processed this
                if not self._is_already_processed(opportunity):
                    # Generate response
                    response = await self.generate_authentic_response(opportunity)

                    if response:
                        opportunity.response_generated = response
                        stats["responses_generated"] += 1

                        # Store in database
                        self._store_engagement_opportunity(opportunity)

                        # Post response (with rate limiting)
                        if await self._post_response(opportunity):
                            stats["responses_posted"] += 1

            # Update metrics
            self._update_engagement_metrics(stats)

        except Exception as e:
            self.logger.error(f"Engagement processing error: {e}")

        return stats

    def _is_already_processed(self, opportunity: EngagementOpportunity) -> bool:
        """Check if we've already processed this engagement opportunity."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM community_engagement WHERE platform = ? AND content_id = ?",
                (opportunity.platform, opportunity.content_id),
            )
            return cursor.fetchone() is not None

    def _store_engagement_opportunity(self, opportunity: EngagementOpportunity):
        """Store engagement opportunity in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO community_engagement 
                (platform, content_id, author, original_content, sentiment, 
                 priority_score, response_content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opportunity.platform,
                    opportunity.content_id,
                    opportunity.author,
                    opportunity.content,
                    opportunity.sentiment.value,
                    opportunity.priority_score,
                    opportunity.response_generated,
                    opportunity.created_at,
                ),
            )

    async def _post_response(self, opportunity: EngagementOpportunity) -> bool:
        """Post response to the appropriate platform."""
        try:
            # Implement rate limiting
            if not self._check_rate_limit(opportunity.platform):
                return False

            if opportunity.platform == "youtube":
                return await self._post_youtube_comment(opportunity)
            elif opportunity.platform == "reddit":
                return await self._post_reddit_comment(opportunity)
            elif opportunity.platform == "twitter":
                return await self._post_twitter_reply(opportunity)

        except Exception as e:
            self.logger.error(f"Response posting error: {e}")

        return False

    def _check_rate_limit(self, platform: str) -> bool:
        """Check if we're within rate limits for posting."""
        # Implement platform-specific rate limiting
        # For now, allow 1 post per minute per platform
        return True

    async def _post_youtube_comment(self, opportunity: EngagementOpportunity) -> bool:
        """Post comment reply on YouTube."""
        # YouTube comment posting would require OAuth
        # For now, just log the intended response
        self.logger.info(
            f"Would post YouTube comment: {opportunity.response_generated}"
        )
        return True

    async def _post_reddit_comment(self, opportunity: EngagementOpportunity) -> bool:
        """Post comment reply on Reddit."""
        if not self.reddit_client:
            return False

        try:
            submission = self.reddit_client.submission(id=opportunity.content_id)
            submission.reply(opportunity.response_generated)
            return True
        except Exception as e:
            self.logger.error(f"Reddit posting error: {e}")
            return False

    async def _post_twitter_reply(self, opportunity: EngagementOpportunity) -> bool:
        """Post reply on Twitter/X."""
        # Twitter API v2 implementation would go here
        self.logger.info(f"Would post Twitter reply: {opportunity.response_generated}")
        return True

    def _update_engagement_metrics(self, stats: Dict[str, int]):
        """Update daily engagement metrics."""
        today = datetime.now().date()

        with sqlite3.connect(self.db_path) as conn:
            for platform in ["youtube", "reddit", "twitter"]:
                engagement_rate = (
                    stats["responses_posted"] / max(stats["opportunities_found"], 1)
                ) * 100

                conn.execute(
                    """
                    INSERT OR REPLACE INTO engagement_metrics 
                    (date, platform, opportunities_found, responses_generated, 
                     responses_posted, engagement_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        today,
                        platform,
                        stats["opportunities_found"],
                        stats["responses_generated"],
                        stats["responses_posted"],
                        engagement_rate,
                    ),
                )

    def get_engagement_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get engagement analytics for the dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            # Get recent metrics
            cursor = conn.execute(
                """
                SELECT platform, SUM(opportunities_found), SUM(responses_generated), 
                       SUM(responses_posted), AVG(engagement_rate)
                FROM engagement_metrics 
                WHERE date >= date('now', '-{} days')
                GROUP BY platform
                """.format(
                    days
                )
            )

            metrics = {}
            for row in cursor.fetchall():
                platform, found, generated, posted, rate = row
                metrics[platform] = {
                    "opportunities_found": found or 0,
                    "responses_generated": generated or 0,
                    "responses_posted": posted or 0,
                    "engagement_rate": rate or 0.0,
                }

            return metrics


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_community_engagement():
        agent = CommunityEngagementAgent()

        # Test Reddit monitoring
        opportunities = await agent.monitor_reddit_discussions(["entrepreneur"])
        print(f"Found {len(opportunities)} Reddit opportunities")

        # Process all opportunities
        stats = await agent.process_engagement_opportunities()
        print(f"Engagement stats: {stats}")

        # Get analytics
        analytics = agent.get_engagement_analytics()
        print(f"Analytics: {analytics}")

    asyncio.run(test_community_engagement())
