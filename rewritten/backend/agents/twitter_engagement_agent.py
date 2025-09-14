#!/usr/bin/env python3
"""
TRAE.AI Twitter Community Engagement Agent

Intelligently searches for relevant conversations on Twitter and generates
appropriate, contextual replies using AI to build community engagement.

Features:
- Smart conversation discovery based on keywords and trends
- AI - powered reply generation with context awareness
- Engagement scoring and prioritization
- Conversation thread analysis
- Sentiment analysis and tone matching
- Anti - spam and authenticity measures
- Engagement tracking and optimization

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.integrations.ollama_integration import OllamaIntegration
from backend.integrations.twitter_integration import (
    SearchResult,
    TweetData,
    TweetType,
    TwitterIntegration,
)

from backend.secret_store import SecretStore


class EngagementType(Enum):
    """Types of engagement interactions."""

    REPLY = "reply"
    QUOTE_TWEET = "quote_tweet"
    LIKE = "like"
    RETWEET = "retweet"
    FOLLOW = "follow"


class ConversationPriority(Enum):
    """Priority levels for conversations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentType(Enum):
    """Sentiment analysis results."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class EngagementStatus(Enum):
    """Status of engagement attempts."""

    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class ConversationContext:
    """Context information for a conversation."""

    tweet_id: str
    author_username: str
    tweet_text: str
    created_at: datetime
    engagement_metrics: Dict[str, int]
    thread_context: List[str]  # Previous tweets in thread
    mentions: List[str]
    hashtags: List[str]
    sentiment: SentimentType
    topic_keywords: List[str]
    relevance_score: float


@dataclass
class EngagementOpportunity:
    """An opportunity for community engagement."""

    opportunity_id: str
    conversation: ConversationContext
    engagement_type: EngagementType
    priority: ConversationPriority
    suggested_reply: str
    confidence_score: float
    reasoning: str
    keywords_matched: List[str]
    created_at: datetime
    expires_at: datetime


@dataclass
class EngagementResult:
    """Result of an engagement attempt."""

    opportunity_id: str
    status: EngagementStatus
    posted_content: Optional[str]
    tweet_id: Optional[str]
    engagement_metrics: Dict[str, int]
    posted_at: Optional[datetime]
    error_message: Optional[str]


@dataclass
class TopicProfile:
    """Profile for tracking engagement topics."""

    topic: str
    keywords: List[str]
    priority_weight: float
    engagement_style: str
    max_daily_engagements: int
    current_daily_count: int
    last_reset_date: datetime


class TwitterEngagementAgent:
    """
    Intelligent Twitter engagement agent that discovers relevant conversations
    and generates contextual, valuable replies to build community presence.
    """

    def __init__(self, db_path: str = "data/engagement_tracking.sqlite"):
        self.logger = setup_logger("twitter_engagement")
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
        self.max_daily_engagements = 50
        self.min_confidence_score = 0.7
        self.max_reply_length = 280
        self.engagement_cooldown_hours = 24  # Don't engage with same user too frequently

        # Topic profiles for targeted engagement
        self.topic_profiles = self._load_topic_profiles()

        # Initialize database
        self._init_database()

        self.logger.info("Twitter Engagement Agent initialized")

    def _init_database(self) -> None:
        """
        Initialize the engagement tracking database.
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Engagement opportunities table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS engagement_opportunities (
                opportunity_id TEXT PRIMARY KEY,
                    tweet_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    tweet_text TEXT NOT NULL,
                    engagement_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    suggested_reply TEXT,
                    confidence_score REAL,
                    reasoning TEXT,
                    keywords_matched TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    status TEXT DEFAULT 'pending'
            )
        """
        )

        # Engagement results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS engagement_results (
                opportunity_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    posted_content TEXT,
                    tweet_id TEXT,
                    engagement_metrics TEXT,
                    posted_at TIMESTAMP,
                    error_message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # User interaction history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_interactions (
                username TEXT,
                    interaction_type TEXT,
                    interaction_date TIMESTAMP,
                    tweet_id TEXT,
                    success BOOLEAN,
                    PRIMARY KEY (username, interaction_date)
            )
        """
        )

        # Topic engagement tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_engagement (
                topic TEXT,
                    date DATE,
                    engagement_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    PRIMARY KEY (topic, date)
            )
        """
        )

        # Conversation context cache
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_cache (
                tweet_id TEXT PRIMARY KEY,
                    context_data TEXT,
                    sentiment TEXT,
                    relevance_score REAL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

        self.logger.info("Engagement database initialized")

    def _load_topic_profiles(self) -> List[TopicProfile]:
        """
        Load topic profiles for targeted engagement.

        Returns:
            List[TopicProfile]: Configured topic profiles
        """
        return [
            TopicProfile(
                topic="AI & Machine Learning",
                keywords=[
                    "AI",
                    "machine learning",
                    "neural network",
                    "deep learning",
                    "artificial intelligence",
                    "ML",
                    "algorithm",
                    "data science",
                ],
                priority_weight=1.0,
                engagement_style="educational_helpful",
                max_daily_engagements=15,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
            ),
            TopicProfile(
                topic="Programming & Development",
                keywords=[
                    "programming",
                    "coding",
                    "developer",
                    "software",
                    "python",
                    "javascript",
                    "react",
                    "nodejs",
                    "github",
                    "opensource",
                ],
                priority_weight=0.9,
                engagement_style="technical_supportive",
                max_daily_engagements=12,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
            ),
            TopicProfile(
                topic="YouTube & Content Creation",
                keywords=[
                    "youtube",
                    "content creator",
                    "video",
                    "streaming",
                    "creator",
                    "youtuber",
                    "content",
                    "channel",
                    "subscriber",
                ],
                priority_weight=0.8,
                engagement_style="encouraging_collaborative",
                max_daily_engagements=10,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
            ),
            TopicProfile(
                topic="Technology & Innovation",
                keywords=[
                    "technology",
                    "tech",
                    "innovation",
                    "startup",
                    "digital",
                    "automation",
                    "future",
                    "trends",
                    "disruption",
                ],
                priority_weight=0.7,
                engagement_style="insightful_forward_thinking",
                max_daily_engagements=8,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
            ),
        ]

    async def discover_engagement_opportunities(
        self, max_opportunities: int = 20
    ) -> List[EngagementOpportunity]:
        """
        Discover new engagement opportunities by searching for relevant conversations.

        Args:
            max_opportunities (int): Maximum opportunities to discover

        Returns:
            List[EngagementOpportunity]: Discovered opportunities
        """
        opportunities = []

        try:
            # Search for conversations based on topic profiles
            for profile in self.topic_profiles:
                if profile.current_daily_count >= profile.max_daily_engagements:
                    continue

                # Reset daily count if needed
                if profile.last_reset_date < datetime.now().date():
                    profile.current_daily_count = 0
                    profile.last_reset_date = datetime.now().date()

                # Search for tweets matching this topic
                search_queries = self._generate_search_queries(profile)

                for query in search_queries[:3]:  # Limit queries per topic
                    try:
                        results = self.twitter.search_tweets(
                            query=query,
                            max_results=10,
                            tweet_fields=[
                                "created_at",
                                "author_id",
                                "public_metrics",
                                "context_annotations",
                            ],
                        )

                        for result in results:
                            if len(opportunities) >= max_opportunities:
                                break

                            # Analyze conversation for engagement potential
                            opportunity = await self._analyze_engagement_potential(result, profile)

                            if (
                                opportunity
                                and opportunity.confidence_score >= self.min_confidence_score
                            ):
                                opportunities.append(opportunity)

                        # Rate limiting between searches
                        time.sleep(2)

                    except Exception as e:
                        self.logger.error(f"Search failed for query '{query}': {e}")
                        continue

            # Sort opportunities by priority and confidence
            opportunities.sort(key=lambda x: (x.priority.value, x.confidence_score), reverse=True)

            # Save opportunities to database
            for opportunity in opportunities:
                self._save_opportunity(opportunity)

            self.logger.info(f"Discovered {len(opportunities)} engagement opportunities")
            return opportunities

        except Exception as e:
            self.logger.error(f"Failed to discover engagement opportunities: {e}")
            return []

    def _generate_search_queries(self, profile: TopicProfile) -> List[str]:
        """
        Generate search queries for a topic profile.

        Args:
            profile (TopicProfile): Topic profile

        Returns:
            List[str]: Search queries
        """
        queries = []

        # Direct keyword searches
        for keyword in profile.keywords[:5]:  # Limit to avoid too many queries
            queries.append(f"{keyword} -is:retweet lang:en")

        # Question - based searches (high engagement potential)
        question_starters = ["how to", "what is", "why does", "help with"]
        for starter in question_starters[:2]:
            for keyword in profile.keywords[:2]:
                queries.append(f"{starter} {keyword} -is:retweet lang:en")

        return queries

    async def _analyze_engagement_potential(
        self, search_result: SearchResult, profile: TopicProfile
    ) -> Optional[EngagementOpportunity]:
        """
        Analyze a search result for engagement potential.

        Args:
            search_result (SearchResult): Tweet search result
            profile (TopicProfile): Relevant topic profile

        Returns:
            Optional[EngagementOpportunity]: Engagement opportunity if viable
        """
        try:
            # Check if we've recently engaged with this user
            if self._recently_engaged_with_user(search_result.author_username):
                return None

            # Check if tweet is too old (engagement window passed)
            if (datetime.now() - search_result.created_at).hours > 6:
                return None

            # Analyze conversation context
            context = self._build_conversation_context(search_result, profile)

            # Skip if context analysis fails
            if not context or context.relevance_score < 0.5:
                return None

            # Generate suggested reply
            (
                suggested_reply,
                confidence,
                reasoning,
            ) = await self._generate_contextual_reply(context, profile)

            if not suggested_reply or confidence < self.min_confidence_score:
                return None

            # Determine priority based on engagement metrics and relevance
            priority = self._calculate_priority(context, profile)

            # Create opportunity
            opportunity_id = f"eng_{search_result.tweet_id}_{int(time.time())}"

            opportunity = EngagementOpportunity(
                opportunity_id=opportunity_id,
                conversation=context,
                engagement_type=EngagementType.REPLY,
                priority=priority,
                suggested_reply=suggested_reply,
                confidence_score=confidence,
                reasoning=reasoning,
                keywords_matched=self._find_matched_keywords(search_result.text, profile.keywords),
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=4),  # Engagement window
            )

            return opportunity

        except Exception as e:
            self.logger.error(f"Failed to analyze engagement potential: {e}")
            return None

    def _recently_engaged_with_user(self, username: str) -> bool:
        """
        Check if we've recently engaged with a user.

        Args:
            username (str): Username to check

        Returns:
            bool: True if recently engaged
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=self.engagement_cooldown_hours)

            cursor.execute(
                "SELECT COUNT(*) FROM user_interactions WHERE username = ? AND interaction_date > ?",
                (username, cutoff_time),
            )

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            self.logger.error(f"Failed to check user interaction history: {e}")
            return False

    def _build_conversation_context(
        self, search_result: SearchResult, profile: TopicProfile
    ) -> Optional[ConversationContext]:
        """
        Build comprehensive context for a conversation.

        Args:
            search_result (SearchResult): Tweet search result
            profile (TopicProfile): Topic profile

        Returns:
            Optional[ConversationContext]: Conversation context
        """
        try:
            # Analyze sentiment
            sentiment = self._analyze_sentiment(search_result.text)

            # Extract mentions and hashtags
            mentions = re.findall(r"@(\\w+)", search_result.text)
            hashtags = re.findall(r"#(\\w+)", search_result.text)

            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(search_result.text, profile.keywords)

            # Extract topic keywords
            topic_keywords = self._extract_topic_keywords(search_result.text, profile.keywords)

            context = ConversationContext(
                tweet_id=search_result.tweet_id,
                author_username=search_result.author_username,
                tweet_text=search_result.text,
                created_at=search_result.created_at,
                engagement_metrics=search_result.engagement_metrics,
                thread_context=[],  # Could be expanded to fetch thread
                mentions=mentions,
                hashtags=hashtags,
                sentiment=sentiment,
                topic_keywords=topic_keywords,
                relevance_score=relevance_score,
            )

            return context

        except Exception as e:
            self.logger.error(f"Failed to build conversation context: {e}")
            return None

    def _analyze_sentiment(self, text: str) -> SentimentType:
        """
        Analyze sentiment of tweet text using AI.

        Args:
            text (str): Tweet text

        Returns:
            SentimentType: Detected sentiment
        """
        try:
            prompt = f"""
            Analyze the sentiment of this tweet and respond with only one word:

            Tweet: "{text}"

            Respond with exactly one of these words: positive, negative, neutral, mixed
            """

            response = self.ollama.generate_response(
                prompt=prompt, model="llama3.2:3b", max_tokens=10, temperature=0.1
            )

            sentiment_text = response.strip().lower()

            if sentiment_text in ["positive", "negative", "neutral", "mixed"]:
                return SentimentType(sentiment_text)
            else:
                return SentimentType.NEUTRAL

        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            return SentimentType.NEUTRAL

    def _calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate relevance score based on keyword matches.

        Args:
            text (str): Tweet text
            keywords (List[str]): Topic keywords

        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        return min(matches / len(keywords), 1.0) if keywords else 0.0

    def _extract_topic_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """
        Extract topic keywords found in the text.

        Args:
            text (str): Tweet text
            keywords (List[str]): Topic keywords

        Returns:
            List[str]: Found keywords
        """
        text_lower = text.lower()
        return [keyword for keyword in keywords if keyword.lower() in text_lower]

    def _find_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """
        Find keywords that match in the text.

        Args:
            text (str): Text to search
            keywords (List[str]): Keywords to find

        Returns:
            List[str]: Matched keywords
        """
        return self._extract_topic_keywords(text, keywords)

    async def _generate_contextual_reply(
        self, context: ConversationContext, profile: TopicProfile
    ) -> Tuple[str, float, str]:
        """
        Generate a contextual reply using AI.

        Args:
            context (ConversationContext): Conversation context
            profile (TopicProfile): Topic profile

        Returns:
            Tuple[str, float, str]: (reply_text, confidence_score, reasoning)
        """
        try:
            # Determine engagement style based on profile and sentiment
            style_guidance = self._get_style_guidance(profile.engagement_style, context.sentiment)

            prompt = f"""
            Generate a helpful, engaging reply to this Twitter conversation:

            Original Tweet: "{context.tweet_text}"
            Author: @{context.author_username}
            Sentiment: {context.sentiment.value}
            Topic: {profile.topic}
            Matched Keywords: {', '.join(context.topic_keywords)}

            Style Guidelines: {style_guidance}

            Requirements:
            - Maximum 250 characters (leaving room for mentions)
            - Be genuinely helpful and add value
            - Match the conversation tone
            - Don't be promotional or salesy
            - Be authentic and conversational
            - Include relevant emojis if appropriate
            - Don't repeat information already in the original tweet

            Generate only the reply text, nothing else.
            """

            response = await self.ollama.query_llm(prompt=prompt, model_name="llama3.2:3b")

            reply_text = response.response_text.strip()

            # Validate reply quality
            confidence, reasoning = self._evaluate_reply_quality(reply_text, context, profile)

            # Ensure reply length is appropriate
            if len(reply_text) > self.max_reply_length - 50:  # Leave room for mentions
                reply_text = reply_text[: self.max_reply_length - 53] + "..."

            return reply_text, confidence, reasoning

        except Exception as e:
            self.logger.error(f"Failed to generate contextual reply: {e}")
            return "", 0.0, f"Generation failed: {e}"

    def _get_style_guidance(self, engagement_style: str, sentiment: SentimentType) -> str:
        """
        Get style guidance based on engagement style and sentiment.

        Args:
            engagement_style (str): Engagement style
            sentiment (SentimentType): Conversation sentiment

        Returns:
            str: Style guidance
        """
        style_map = {
            "educational_helpful": "Be informative \
    and educational. Share knowledge or resources.",
            "technical_supportive": "Offer technical insights or solutions. Be precise \
    and helpful.",
            "encouraging_collaborative": "Be supportive \
    and encouraging. Suggest collaboration.",
            "insightful_forward_thinking": "Share insights about trends \
    and future implications.",
        }

        base_guidance = style_map.get(engagement_style, "Be helpful and authentic.")

        # Adjust based on sentiment
        if sentiment == SentimentType.NEGATIVE:
            base_guidance += " Be empathetic and offer constructive support."
        elif sentiment == SentimentType.POSITIVE:
            base_guidance += " Match the positive energy and enthusiasm."

        return base_guidance

    def _evaluate_reply_quality(
        self, reply_text: str, context: ConversationContext, profile: TopicProfile
    ) -> Tuple[float, str]:
        """
        Evaluate the quality of a generated reply.

        Args:
            reply_text (str): Generated reply
            context (ConversationContext): Conversation context
            profile (TopicProfile): Topic profile

        Returns:
            Tuple[float, str]: (confidence_score, reasoning)
        """
        confidence = 0.5  # Base confidence
        reasoning_parts = []

        # Check length appropriateness
        if 20 <= len(reply_text) <= 250:
            confidence += 0.1
            reasoning_parts.append("appropriate length")

        # Check for topic relevance
        topic_matches = sum(
            1 for keyword in profile.keywords if keyword.lower() in reply_text.lower()
        )
        if topic_matches > 0:
            confidence += 0.2
            reasoning_parts.append(f"mentions {topic_matches} topic keywords")

        # Check for question responsiveness
        if "?" in context.tweet_text and any(
            word in reply_text.lower() for word in ["yes", "no", "try", "use", "check"]
        ):
            confidence += 0.15
            reasoning_parts.append("responds to question")

        # Check for value - adding words
        value_words = [
            "help",
            "try",
            "check",
            "consider",
            "suggest",
            "recommend",
            "tip",
        ]
        if any(word in reply_text.lower() for word in value_words):
            confidence += 0.1
            reasoning_parts.append("offers helpful suggestions")

        # Penalize promotional language
        promo_words = ["buy", "purchase", "sale", "discount", "offer", "deal"]
        if any(word in reply_text.lower() for word in promo_words):
            confidence -= 0.2
            reasoning_parts.append("contains promotional language (penalty)")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "basic quality check"

        return min(confidence, 1.0), reasoning

    def _calculate_priority(
        self, context: ConversationContext, profile: TopicProfile
    ) -> ConversationPriority:
        """
        Calculate priority for an engagement opportunity.

        Args:
            context (ConversationContext): Conversation context
            profile (TopicProfile): Topic profile

        Returns:
            ConversationPriority: Calculated priority
        """
        score = 0.0

        # Factor in topic priority weight
        score += profile.priority_weight * 0.3

        # Factor in relevance score
        score += context.relevance_score * 0.3

        # Factor in engagement metrics
        metrics = context.engagement_metrics
        engagement_score = (
            metrics.get("like_count", 0) * 0.1
            + metrics.get("retweet_count", 0) * 0.2
            + metrics.get("reply_count", 0) * 0.3
        ) / 10  # Normalize
        score += min(engagement_score, 0.3)

        # Factor in recency (newer tweets get higher priority)
        hours_old = (datetime.now() - context.created_at).total_seconds() / 3600
        recency_score = max(0, (6 - hours_old) / 6)  # 6 - hour window
        score += recency_score * 0.1

        # Convert to priority level
        if score >= 0.8:
            return ConversationPriority.CRITICAL
        elif score >= 0.6:
            return ConversationPriority.HIGH
        elif score >= 0.4:
            return ConversationPriority.MEDIUM
        else:
            return ConversationPriority.LOW

    def _save_opportunity(self, opportunity: EngagementOpportunity) -> None:
        """
        Save engagement opportunity to database.

        Args:
            opportunity (EngagementOpportunity): Opportunity to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO engagement_opportunities (
                    opportunity_id, tweet_id, author_username, tweet_text,
                        engagement_type, priority, suggested_reply, confidence_score,
                        reasoning, keywords_matched, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    opportunity.opportunity_id,
                    opportunity.conversation.tweet_id,
                    opportunity.conversation.author_username,
                    opportunity.conversation.tweet_text,
                    opportunity.engagement_type.value,
                    opportunity.priority.value,
                    opportunity.suggested_reply,
                    opportunity.confidence_score,
                    opportunity.reasoning,
                    json.dumps(opportunity.keywords_matched),
                    opportunity.created_at,
                    opportunity.expires_at,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to save opportunity: {e}")

    def execute_engagement(self, opportunity_id: str) -> EngagementResult:
        """
        Execute an engagement opportunity.

        Args:
            opportunity_id (str): Opportunity ID to execute

        Returns:
            EngagementResult: Result of engagement attempt
        """
        try:
            # Load opportunity
            opportunity = self._load_opportunity(opportunity_id)
            if not opportunity:
                return EngagementResult(
                    opportunity_id=opportunity_id,
                    status=EngagementStatus.FAILED,
                    posted_content=None,
                    tweet_id=None,
                    engagement_metrics={},
                    posted_at=None,
                    error_message="Opportunity not found",
                )

            # Check if opportunity has expired
            if datetime.now() > opportunity.expires_at:
                return EngagementResult(
                    opportunity_id=opportunity_id,
                    status=EngagementStatus.SKIPPED,
                    posted_content=None,
                    tweet_id=None,
                    engagement_metrics={},
                    posted_at=None,
                    error_message="Opportunity expired",
                )

            # Prepare reply tweet
            reply_text = (
                f"@{opportunity.conversation.author_username} {opportunity.suggested_reply}"
            )

            tweet_data = TweetData(
                text=reply_text,
                tweet_type=TweetType.ENGAGEMENT,
                reply_to_id=opportunity.conversation.tweet_id,
            )

            # Post reply
            result = self.twitter.post_tweet(tweet_data)
            tweet_id = result.get("data", {}).get("id")

            if tweet_id:
                # Record successful engagement
                self._record_user_interaction(
                    opportunity.conversation.author_username,
                    EngagementType.REPLY,
                    tweet_id,
                    True,
                )

                engagement_result = EngagementResult(
                    opportunity_id=opportunity_id,
                    status=EngagementStatus.POSTED,
                    posted_content=reply_text,
                    tweet_id=tweet_id,
                    engagement_metrics={},
                    posted_at=datetime.now(),
                    error_message=None,
                )
            else:
                engagement_result = EngagementResult(
                    opportunity_id=opportunity_id,
                    status=EngagementStatus.FAILED,
                    posted_content=reply_text,
                    tweet_id=None,
                    engagement_metrics={},
                    posted_at=None,
                    error_message="Tweet posting failed",
                )

            # Save result
            self._save_engagement_result(engagement_result)

            return engagement_result

        except Exception as e:
            self.logger.error(f"Failed to execute engagement {opportunity_id}: {e}")
            return EngagementResult(
                opportunity_id=opportunity_id,
                status=EngagementStatus.FAILED,
                posted_content=None,
                tweet_id=None,
                engagement_metrics={},
                posted_at=None,
                error_message=str(e),
            )

    def _load_opportunity(self, opportunity_id: str) -> Optional[EngagementOpportunity]:
        """
        Load engagement opportunity from database.

        Args:
            opportunity_id (str): Opportunity ID

        Returns:
            Optional[EngagementOpportunity]: Loaded opportunity
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM engagement_opportunities WHERE opportunity_id = ?",
                (opportunity_id,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            # Reconstruct opportunity object
            context = ConversationContext(
                tweet_id=result[1],
                author_username=result[2],
                tweet_text=result[3],
                created_at=datetime.now(),  # Approximate
                engagement_metrics={},
                thread_context=[],
                mentions=[],
                hashtags=[],
                sentiment=SentimentType.NEUTRAL,
                topic_keywords=json.loads(result[9]) if result[9] else [],
                relevance_score=0.5,
            )

            opportunity = EngagementOpportunity(
                opportunity_id=result[0],
                conversation=context,
                engagement_type=EngagementType(result[4]),
                priority=ConversationPriority(result[5]),
                suggested_reply=result[6] or "",
                confidence_score=result[7] or 0.0,
                reasoning=result[8] or "",
                keywords_matched=json.loads(result[9]) if result[9] else [],
                created_at=datetime.fromisoformat(result[10]),
                expires_at=datetime.fromisoformat(result[11]),
            )

            return opportunity

        except Exception as e:
            self.logger.error(f"Failed to load opportunity {opportunity_id}: {e}")
            return None

    def _record_user_interaction(
        self,
        username: str,
        interaction_type: EngagementType,
        tweet_id: str,
        success: bool,
    ) -> None:
        """
        Record user interaction in database.

        Args:
            username (str): Username
            interaction_type (EngagementType): Type of interaction
            tweet_id (str): Tweet ID
            success (bool): Whether interaction was successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO user_interactions (
                    username, interaction_type, interaction_date, tweet_id, success
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (username, interaction_type.value, datetime.now(), tweet_id, success),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to record user interaction: {e}")

    def _save_engagement_result(self, result: EngagementResult) -> None:
        """
        Save engagement result to database.

        Args:
            result (EngagementResult): Result to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO engagement_results (
                    opportunity_id, status, posted_content, tweet_id,
                        engagement_metrics, posted_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.opportunity_id,
                    result.status.value,
                    result.posted_content,
                    result.tweet_id,
                    json.dumps(result.engagement_metrics),
                    result.posted_at,
                    result.error_message,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to save engagement result: {e}")

    def process_pending_engagements(self, max_engagements: int = 10) -> int:
        """
        Process pending engagement opportunities.

        Args:
            max_engagements (int): Maximum engagements to process

        Returns:
            int: Number of engagements processed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get pending opportunities, prioritized
            cursor.execute(
                """
                SELECT opportunity_id FROM engagement_opportunities
                WHERE status = 'pending' AND expires_at > ?
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 4
                        WHEN 'high' THEN 3
                        WHEN 'medium' THEN 2
                        ELSE 1
                    END DESC,
                        confidence_score DESC,
                        created_at ASC
                LIMIT ?
            """,
                (datetime.now(), max_engagements),
            )

            opportunity_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            processed = 0
            for opportunity_id in opportunity_ids:
                result = self.execute_engagement(opportunity_id)
                if result.status == EngagementStatus.POSTED:
                    processed += 1

                # Add delay between engagements
                time.sleep(3)

            if processed > 0:
                self.logger.info(f"Processed {processed} engagement opportunities")

            return processed

        except Exception as e:
            self.logger.error(f"Failed to process pending engagements: {e}")
            return 0

    def get_engagement_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get engagement analytics.

        Args:
            days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            # Get engagement statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_opportunities,
                        SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as successful_engagements,
                        AVG(confidence_score) as avg_confidence,
                        COUNT(DISTINCT author_username) as unique_users_engaged
                FROM engagement_opportunities eo
                LEFT JOIN engagement_results er ON eo.opportunity_id = er.opportunity_id
                WHERE eo.created_at >= ?
            """,
                (cutoff_date,),
            )

            stats = cursor.fetchone()

            # Get top topics
            cursor.execute(
                """
                SELECT keywords_matched, COUNT(*) as count
                FROM engagement_opportunities
                WHERE created_at >= ? AND keywords_matched IS NOT NULL
                GROUP BY keywords_matched
                ORDER BY count DESC
                LIMIT 5
            """,
                (cutoff_date,),
            )

            top_topics = cursor.fetchall()

            conn.close()

            return {
                "period_days": days,
                "total_opportunities": stats[0] or 0,
                "successful_engagements": stats[1] or 0,
                "success_rate": (stats[1] / stats[0]) if stats[0] > 0 else 0,
                "avg_confidence": stats[2] or 0,
                "unique_users_engaged": stats[3] or 0,
                "top_topics": [
                    {"keywords": json.loads(row[0]) if row[0] else [], "count": row[1]}
                    for row in top_topics
                ],
            }

        except Exception as e:
            self.logger.error(f"Failed to get engagement analytics: {e}")
            return {}

    async def search_and_engage(
        self, keywords: List[str], max_engagements: int = 5
    ) -> Dict[str, Any]:
        """
        Search for conversations based on keywords and engage with them.

        Args:
            keywords (List[str]): Keywords to search for
                max_engagements (int): Maximum number of engagements to perform

        Returns:
            Dict[str, Any]: Results of the engagement process
        """
        try:
            # Discover opportunities based on keywords
            opportunities = await self.discover_engagement_opportunities(
                max_opportunities=max_engagements * 2
            )

            # Filter opportunities by keywords
            filtered_opportunities = []
            for opportunity in opportunities:
                matched_keywords = self._find_matched_keywords(
                    opportunity.conversation.tweet_text, keywords
                )
                if matched_keywords:
                    opportunity.keywords_matched = matched_keywords
                    filtered_opportunities.append(opportunity)

            # Limit to max_engagements
            filtered_opportunities = filtered_opportunities[:max_engagements]

            # Process the engagements
            successful_engagements = 0
            failed_engagements = 0

            for opportunity in filtered_opportunities:
                try:
                    # Save opportunity to database
                    self._save_opportunity(opportunity)
                    successful_engagements += 1
                except Exception as e:
                    self.logger.error(f"Failed to process engagement opportunity: {e}")
                    failed_engagements += 1

            return {
                "success": True,
                "total_opportunities": len(filtered_opportunities),
                "successful_engagements": successful_engagements,
                "failed_engagements": failed_engagements,
                "keywords_used": keywords,
            }

        except Exception as e:
            self.logger.error(f"Failed to search and engage: {e}")
            return {"success": False, "error": str(e), "keywords_used": keywords}

    async def monitor_topics(self, topics: List[str]) -> Dict[str, Any]:
        """
        Monitor specified topics for engagement opportunities.

        Args:
            topics (List[str]): Topics to monitor

        Returns:
            Dict[str, Any]: Results of the monitoring process
        """
        try:
            total_opportunities = 0
            topic_results = {}

            for topic in topics:
                # Find matching topic profile
                matching_profile = None
                for profile in self.topic_profiles:
                    if topic.lower() in profile.topic.lower() or any(
                        keyword.lower() in topic.lower() for keyword in profile.keywords
                    ):
                        matching_profile = profile
                        break

                # If no matching profile, create a temporary one
                if not matching_profile:
                    matching_profile = TopicProfile(
                        topic=topic,
                        keywords=[topic],
                        priority_weight=0.5,
                        engagement_style="helpful_informative",
                        max_daily_engagements=5,
                        current_daily_count=0,
                        last_reset_date=datetime.now().date(),
                    )

                # Search for opportunities for this topic
                search_queries = self._generate_search_queries(matching_profile)
                topic_opportunities = 0

                for query in search_queries[:2]:  # Limit queries per topic
                    try:
                        results = self.twitter.search_tweets(
                            query=query,
                            max_results=5,
                            tweet_fields=[
                                "created_at",
                                "author_id",
                                "public_metrics",
                                "context_annotations",
                            ],
                        )

                        for result in results:
                            opportunity = await self._analyze_engagement_potential(
                                result, matching_profile
                            )

                            if (
                                opportunity
                                and opportunity.confidence_score >= self.min_confidence_score
                            ):
                                self._save_opportunity(opportunity)
                                topic_opportunities += 1

                        # Rate limiting
                        time.sleep(1)

                    except Exception as e:
                        self.logger.error(f"Search failed for topic '{topic}' query '{query}': {e}")
                        continue

                topic_results[topic] = {
                    "opportunities_found": topic_opportunities,
                    "profile_used": matching_profile.topic,
                }
                total_opportunities += topic_opportunities

            return {
                "success": True,
                "total_opportunities": total_opportunities,
                "topics_monitored": len(topics),
                "topic_results": topic_results,
            }

        except Exception as e:
            self.logger.error(f"Failed to monitor topics: {e}")
            return {"success": False, "error": str(e), "topics": topics}


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize engagement agent
        agent = TwitterEngagementAgent()

        try:
            # Discover engagement opportunities
            opportunities = await agent.discover_engagement_opportunities(max_opportunities=5)
            print(f"✓ Discovered {len(opportunities)} opportunities")

            # Process pending engagements
            processed = agent.process_pending_engagements(max_engagements=3)
            print(f"✓ Processed {processed} engagements")

            # Get analytics
            analytics = agent.get_engagement_analytics(7)
            print(f"✓ Analytics: {analytics}")

        except Exception as e:
            print(f"✗ Error: {e}")

    asyncio.run(main())
