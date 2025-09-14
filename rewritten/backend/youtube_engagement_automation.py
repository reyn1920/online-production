#!/usr/bin/env python3
"""
TRAE.AI YouTube Engagement Automation System

Comprehensive engagement automation that provides:
- Intelligent comment management and moderation
- AI - powered response generation and interaction
- Community post automation and scheduling
- Subscriber engagement campaigns and outreach
- Sentiment analysis and reputation monitoring
- Automated community building and growth
- Cross - platform engagement coordination
- Influencer and collaboration management

Features:
- Natural language processing for comments
- Automated spam detection and filtering
- Personalized response generation
- Community sentiment tracking
- Engagement optimization algorithms
- Multi - language support
- Real - time interaction monitoring

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import nltk
import openai
import spacy
from langdetect import detect
from textblob import TextBlob
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.integrations.youtube_integration import YouTubeIntegration
from backend.secret_store import SecretStore


class EngagementType(Enum):
    """Types of engagement interactions."""

    COMMENT_REPLY = "comment_reply"
    COMMUNITY_POST = "community_post"
    LIVE_CHAT = "live_chat"
    SUBSCRIBER_OUTREACH = "subscriber_outreach"
    COLLABORATION_REQUEST = "collaboration_request"
    FEEDBACK_RESPONSE = "feedback_response"
    MILESTONE_CELEBRATION = "milestone_celebration"
    CONTENT_PROMOTION = "content_promotion"


class SentimentType(Enum):
    """Sentiment analysis categories."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    SPAM = "spam"
    TOXIC = "toxic"


class ResponseTone(Enum):
    """Response tone options."""

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    EDUCATIONAL = "educational"
    HUMOROUS = "humorous"
    SUPPORTIVE = "supportive"


class EngagementPriority(Enum):
    """Priority levels for engagement."""

    CRITICAL = "critical"  # Negative feedback, complaints
    HIGH = "high"  # Questions, collaboration requests
    MEDIUM = "medium"  # General comments, feedback
    LOW = "low"  # Simple reactions, spam


class CommunityPostType(Enum):
    """Types of community posts."""

    ANNOUNCEMENT = "announcement"
    BEHIND_SCENES = "behind_scenes"
    POLL = "poll"
    QUESTION = "question"
    MILESTONE = "milestone"
    PROMOTION = "promotion"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"

@dataclass


class CommentData:
    """YouTube comment data structure."""

    comment_id: str
    video_id: str
    channel_id: str
    author_name: str
    author_channel_id: str
    text: str
    like_count: int
    reply_count: int
    published_at: datetime
    updated_at: datetime
    parent_id: Optional[str]  # For replies
    sentiment: SentimentType
    language: str
    toxicity_score: float
    spam_score: float
    engagement_score: float
    keywords: List[str]
    mentions: List[str]
    questions: List[str]
    processed_at: datetime

@dataclass


class EngagementResponse:
    """Generated engagement response."""

    response_id: str
    original_comment_id: str
    response_text: str
    response_tone: ResponseTone
    confidence_score: float
    personalization_level: float
    estimated_engagement: float
    language: str
    contains_cta: bool  # Call to action
    contains_question: bool
    contains_emoji: bool
    word_count: int
    generated_at: datetime
    approved: bool
    posted: bool
    posted_at: Optional[datetime]
    performance_metrics: Dict[str, Any]

@dataclass


class CommunityPost:
    """Community post data structure."""

    post_id: str
    channel_id: str
    post_type: CommunityPostType
    title: str
    content: str
    media_urls: List[str]
    poll_options: Optional[List[str]]
    scheduled_time: Optional[datetime]
    published_at: Optional[datetime]
    engagement_metrics: Dict[str, int]
    target_audience: Dict[str, Any]
    hashtags: List[str]
    mentions: List[str]
    performance_score: float
    created_at: datetime

@dataclass


class EngagementCampaign:
    """Engagement campaign configuration."""

    campaign_id: str
    name: str
    campaign_type: EngagementType
    target_audience: Dict[str, Any]
    content_templates: List[str]
    scheduling_rules: Dict[str, Any]
    success_metrics: Dict[str, float]
    budget_limits: Dict[str, float]
    duration: timedelta
    status: str  # active, paused, completed
    performance_data: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

@dataclass


class EngagementInsight:
    """Engagement analytics insight."""

    insight_id: str
    insight_type: str
    title: str
    description: str
    impact_score: float
    confidence_level: float
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    actionable_items: List[str]
    expected_improvement: str
    priority: str
    created_at: datetime
    expires_at: Optional[datetime]


class YouTubeEngagementAutomation:
    """
    Advanced YouTube engagement automation system with AI - powered responses,
        community management, and intelligent interaction optimization.
    """


    def __init__(self, config_path: str = "config/engagement_config.json"):
        self.logger = setup_logger("youtube_engagement")
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize database
        self.db_path = self.config.get(
            "database_path", "data/youtube_engagement.sqlite"
        )
        self._init_database()

        # Initialize integrations
        self.youtube_integration = YouTubeIntegration()
        self.secret_store = SecretStore()

        # Initialize AI models
        self._init_ai_models()

        # Engagement data
        self.pending_comments = []
        self.generated_responses = []
        self.community_posts = []
        self.active_campaigns = []

        # Response templates
        self.response_templates = self._load_response_templates()

        # Tracking state
        self.last_comment_check = None
        self.last_community_post = None
        self.engagement_stats = defaultdict(int)

        self.logger.info("YouTube Engagement Automation initialized")


    def _load_config(self) -> Dict[str, Any]:
        """Load engagement configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading engagement config: {e}")

        return {
            "database_path": "data/youtube_engagement.sqlite",
                "comment_monitoring": {
                "enabled": True,
                    "check_interval_minutes": 15,
                    "max_comments_per_check": 100,
                    "languages": ["en", "es", "fr", "de", "it", "pt"],
                    "auto_reply_enabled": True,
                    "moderation_enabled": True,
                    },
                "response_generation": {
                "ai_model": "gpt - 3.5 - turbo",
                    "max_response_length": 280,
                    "personalization_level": 0.7,
                    "tone_adaptation": True,
                    "emoji_usage": True,
                    "cta_inclusion_rate": 0.3,
                    },
                "sentiment_analysis": {
                "enabled": True,
                    "toxicity_threshold": 0.7,
                    "spam_threshold": 0.8,
                    "sentiment_model": "cardiffnlp/twitter - roberta - base - sentiment - latest",
                    },
                "community_posts": {
                "enabled": True,
                    "posting_frequency": "daily",
                    "optimal_times": ["09:00", "15:00", "20:00"],
                    "content_types": ["announcement", "behind_scenes", "poll", "question"],
                    "auto_generate": True,
                    },
                "engagement_campaigns": {
                "enabled": True,
                    "max_active_campaigns": 5,
                    "subscriber_outreach": True,
                    "collaboration_requests": True,
                    "milestone_celebrations": True,
                    },
                "moderation": {
                "auto_moderate": True,
                    "spam_action": "hide",  # hide, delete, report
                "toxic_action": "delete",
                    "manual_review_threshold": 0.5,
                    "whitelist_channels": [],
                    "blacklist_keywords": [],
                    },
                "analytics": {
                "track_engagement_metrics": True,
                    "generate_insights": True,
                    "performance_reporting": True,
                    "optimization_suggestions": True,
                    },
                }


    def _init_database(self):
        """Initialize engagement database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok = True)

        with sqlite3.connect(self.db_path) as conn:
            # Comments table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        comment_id TEXT UNIQUE,
                        video_id TEXT,
                        channel_id TEXT,
                        author_name TEXT,
                        author_channel_id TEXT,
                        text TEXT,
                        like_count INTEGER,
                        reply_count INTEGER,
                        published_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        parent_id TEXT,
                        sentiment TEXT,
                        language TEXT,
                        toxicity_score REAL,
                        spam_score REAL,
                        engagement_score REAL,
                        keywords TEXT,
                        mentions TEXT,
                        questions TEXT,
                        processed_at TIMESTAMP
                )
            """
            )

            # Responses table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        response_id TEXT UNIQUE,
                        original_comment_id TEXT,
                        response_text TEXT,
                        response_tone TEXT,
                        confidence_score REAL,
                        personalization_level REAL,
                        estimated_engagement REAL,
                        language TEXT,
                        contains_cta BOOLEAN,
                        contains_question BOOLEAN,
                        contains_emoji BOOLEAN,
                        word_count INTEGER,
                        generated_at TIMESTAMP,
                        approved BOOLEAN,
                        posted BOOLEAN,
                        posted_at TIMESTAMP,
                        performance_metrics TEXT
                )
            """
            )

            # Community posts table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id TEXT UNIQUE,
                        channel_id TEXT,
                        post_type TEXT,
                        title TEXT,
                        content TEXT,
                        media_urls TEXT,
                        poll_options TEXT,
                        scheduled_time TIMESTAMP,
                        published_at TIMESTAMP,
                        engagement_metrics TEXT,
                        target_audience TEXT,
                        hashtags TEXT,
                        mentions TEXT,
                        performance_score REAL,
                        created_at TIMESTAMP
                )
            """
            )

            # Engagement campaigns table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS engagement_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id TEXT UNIQUE,
                        name TEXT,
                        campaign_type TEXT,
                        target_audience TEXT,
                        content_templates TEXT,
                        scheduling_rules TEXT,
                        success_metrics TEXT,
                        budget_limits TEXT,
                        duration_seconds INTEGER,
                        status TEXT,
                        performance_data TEXT,
                        created_at TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP
                )
            """
            )

            # Engagement insights table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS engagement_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_id TEXT UNIQUE,
                        insight_type TEXT,
                        title TEXT,
                        description TEXT,
                        impact_score REAL,
                        confidence_level REAL,
                        recommendations TEXT,
                        supporting_data TEXT,
                        actionable_items TEXT,
                        expected_improvement TEXT,
                        priority TEXT,
                        created_at TIMESTAMP,
                        expires_at TIMESTAMP
                )
            """
            )

            conn.commit()


    def _init_ai_models(self):
        """Initialize AI models for engagement automation."""
        try:
            # Sentiment analysis model
            model_name = self.config["sentiment_analysis"]["sentiment_model"]
            self.sentiment_analyzer = pipeline(
                "sentiment - analysis", model = model_name, tokenizer = model_name
            )

            # Toxicity detection model
            self.toxicity_analyzer = pipeline(
                "text - classification", model="unitary/toxic - bert"
            )

            # Language detection
            self.language_detector = detect

            # Initialize OpenAI for response generation
            openai.api_key = self.secret_store.get_secret("OPENAI_API_KEY")

            # Load spaCy model for NLP
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning(
                    "spaCy English model not found. Some features may be limited."
                )
                self.nlp = None

            self.logger.info("AI models initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing AI models: {e}")


    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates for different scenarios."""
        return {
            "greeting": [
                "Thanks for watching! {emoji}",
                    "Great to see you here! {emoji}",
                    "Welcome to the channel! {emoji}",
                    ],
                "question_response": [
                "Great question! {answer} {emoji}",
                    "Thanks for asking! {answer}",
                    "That's a really good point. {answer} {emoji}",
                    ],
                "positive_feedback": [
                "Thank you so much! That means a lot {emoji}",
                    "I'm so glad you enjoyed it! {emoji}",
                    "Your support is amazing! {emoji}",
                    ],
                "constructive_criticism": [
                "Thanks for the feedback! I'll definitely consider that for future videos {emoji}",
                    "I appreciate your honest input! Always looking to improve {emoji}",
                    "Great point! I'll keep that in mind {emoji}",
                    ],
                "collaboration_interest": [
                "That sounds interesting! Feel free to reach out via email {emoji}",
                    "I'd love to hear more about your idea! {emoji}",
                    "Thanks for reaching out! Let's connect {emoji}",
                    ],
                "technical_help": [
                "I'll try to help! {answer} {emoji}",
                    "Good question! {answer}",
                    "Here's what I know: {answer} {emoji}",
                    ],
                "milestone_celebration": [
                "We did it! Thanks to amazing viewers like you! {emoji}",
                    "Couldn't have done it without you all! {emoji}",
                    "This community is incredible! {emoji}",
                    ],
                }


    async def monitor_comments(self, video_ids: List[str]) -> List[CommentData]:
        """Monitor and process new comments on specified videos."""
        try:
            self.logger.info(f"Monitoring comments for {len(video_ids)} videos")

            new_comments = []

            for video_id in video_ids:
                try:
                    # Get comments from YouTube API
                    comments_data = await self.youtube_integration.get_video_comments(
                        video_id,
                            max_results = self.config["comment_monitoring"][
                            "max_comments_per_check"
                        ],
                            )

                    for comment_data in comments_data:
                        # Process comment
                        processed_comment = await self._process_comment(comment_data)

                        if processed_comment:
                            new_comments.append(processed_comment)

                            # Store in database
                            await self._store_comment(processed_comment)

                            # Generate response if needed
                            if self._should_respond_to_comment(processed_comment):
                                response = await self._generate_response(
                                    processed_comment
                                )
                                if response:
                                    await self._store_response(response)

                except Exception as e:
                    self.logger.error(
                        f"Error processing comments for video {video_id}: {e}"
                    )
                    continue

            self.last_comment_check = datetime.now()
            self.logger.info(f"Processed {len(new_comments)} new comments")

            return new_comments

        except Exception as e:
            self.logger.error(f"Error monitoring comments: {e}")
            return []


    async def _process_comment(
        self, comment_data: Dict[str, Any]
    ) -> Optional[CommentData]:
        """Process raw comment data into structured format."""
        try:
            text = comment_data.get("text", "")

            # Skip empty comments
            if not text.strip():
                return None

            # Detect language
            try:
                language = detect(text)
            except Exception:
                language = "unknown"

            # Skip if language not supported
            supported_languages = self.config["comment_monitoring"]["languages"]
            if (
                language not in supported_languages
                and "unknown" not in supported_languages
            ):
                return None

            # Analyze sentiment
            sentiment = await self._analyze_sentiment(text)

            # Calculate toxicity and spam scores
            toxicity_score = await self._analyze_toxicity(text)
            spam_score = await self._analyze_spam(text)

            # Extract keywords, mentions, and questions
            keywords = self._extract_keywords(text)
            mentions = self._extract_mentions(text)
            questions = self._extract_questions(text)

            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(
                comment_data, sentiment, toxicity_score, spam_score
            )

            comment = CommentData(
                comment_id = comment_data.get("id", ""),
                    video_id = comment_data.get("video_id", ""),
                    channel_id = comment_data.get("channel_id", ""),
                    author_name = comment_data.get("author_name", ""),
                    author_channel_id = comment_data.get("author_channel_id", ""),
                    text = text,
                    like_count = comment_data.get("like_count", 0),
                    reply_count = comment_data.get("reply_count", 0),
                    published_at = datetime.fromisoformat(
                    comment_data.get("published_at", datetime.now().isoformat())
                ),
                    updated_at = datetime.fromisoformat(
                    comment_data.get("updated_at", datetime.now().isoformat())
                ),
                    parent_id = comment_data.get("parent_id"),
                    sentiment = sentiment,
                    language = language,
                    toxicity_score = toxicity_score,
                    spam_score = spam_score,
                    engagement_score = engagement_score,
                    keywords = keywords,
                    mentions = mentions,
                    questions = questions,
                    processed_at = datetime.now(),
                    )

            return comment

        except Exception as e:
            self.logger.error(f"Error processing comment: {e}")
            return None


    async def _analyze_sentiment(self, text: str) -> SentimentType:
        """Analyze sentiment of comment text."""
        try:
            result = self.sentiment_analyzer(text)[0]
            label = result["label"].lower()
            confidence = result["score"]

            # Map model output to our sentiment types
            if "positive" in label or "pos" in label:
                return (
                    SentimentType.POSITIVE
                    if confidence > 0.7
                    else SentimentType.NEUTRAL
                )
            elif "negative" in label or "neg" in label:
                return (
                    SentimentType.NEGATIVE
                    if confidence > 0.7
                    else SentimentType.NEUTRAL
                )
            else:
                return SentimentType.NEUTRAL

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return SentimentType.NEUTRAL


    async def _analyze_toxicity(self, text: str) -> float:
        """Analyze toxicity level of comment text."""
        try:
            result = self.toxicity_analyzer(text)[0]
            if result["label"] == "TOXIC":
                return result["score"]
            else:
                return 1.0 - result["score"]  # Invert if label is 'NOT_TOXIC'
        except Exception as e:
            self.logger.error(f"Error analyzing toxicity: {e}")
            return 0.0


    async def _analyze_spam(self, text: str) -> float:
        """Analyze spam likelihood of comment text."""
        try:
            spam_indicators = [
                r"http[s]?://(?:[a - zA - Z]|[0 - 9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0 - 9a - fA - F][0 - 9a - fA - F]))+",  # URLs
                r"\\b(?:subscribe|like|follow|check out|visit)\\b.*\\b(?:channel|page|profile)\\b",  # Self - promotion
                r"\\b(?:free|win|prize|giveaway|contest)\\b",  # Spam keywords
                r"[A - Z]{5,}",  # Excessive caps
                r"(.)\\1{4,}",  # Repeated characters
                r"[!@#$%^&*()]{3,}",  # Excessive punctuation
            ]

            spam_score = 0.0
            for pattern in spam_indicators:
                if re.search(pattern, text, re.IGNORECASE):
                    spam_score += 0.2

            return min(spam_score, 1.0)

        except Exception as e:
            self.logger.error(f"Error analyzing spam: {e}")
            return 0.0


    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from comment text."""
        try:
            if not self.nlp:
                # Simple keyword extraction without spaCy
                words = re.findall(r"\\b\\w+\\b", text.lower())
                # Filter out common stop words
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
                        "be",
                        "been",
                        "being",
                        "have",
                        "has",
                        "had",
                        "do",
                        "does",
                        "did",
                        "will",
                        "would",
                        "could",
                        "should",
                        "may",
                        "might",
                        "must",
                        "can",
                        "this",
                        "that",
                        "these",
                        "those",
                        "i",
                        "you",
                        "he",
                        "she",
                        "it",
                        "we",
                        "they",
                        "me",
                        "him",
                        "her",
                        "us",
                        "them",
                        }
                keywords = [
                    word for word in words if word not in stop_words and len(word) > 2
                ]
                return keywords[:10]  # Limit to top 10

            doc = self.nlp(text)
            keywords = []

            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "PRODUCT", "EVENT"]:
                    keywords.append(ent.text.lower())

            # Extract important nouns and adjectives
            for token in doc:
                if (
                    token.pos_ in ["NOUN", "ADJ"]
                    and not token.is_stop
                    and not token.is_punct
                    and len(token.text) > 2
                ):
                    keywords.append(token.lemma_.lower())

            return list(set(keywords))[:10]  # Remove duplicates and limit

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []


    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from comment text."""
        try:
            mentions = re.findall(r"@([a - zA - Z0 - 9_]+)", text)
            return mentions
        except Exception as e:
            self.logger.error(f"Error extracting mentions: {e}")
            return []


    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from comment text."""
        try:
            # Split text into sentences
            sentences = re.split(r"[.!?]+", text)
            questions = []

            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and (
                    "?" in sentence
                    or sentence.lower().startswith(
                        (
                            "what",
                                "how",
                                "why",
                                "when",
                                "where",
                                "who",
                                "which",
                                "can",
                                "could",
                                "would",
                                "should",
                                "is",
                                "are",
                                "do",
                                "does",
                                "did",
                                )
                    )
                ):
                    questions.append(sentence)

            return questions

        except Exception as e:
            self.logger.error(f"Error extracting questions: {e}")
            return []


    def _calculate_engagement_score(
        self,
            comment_data: Dict[str, Any],
            sentiment: SentimentType,
            toxicity_score: float,
            spam_score: float,
            ) -> float:
        """Calculate engagement score for comment prioritization."""
        try:
            score = 0.0

            # Base score from likes and replies
            like_count = comment_data.get("like_count", 0)
            reply_count = comment_data.get("reply_count", 0)

            score += min(like_count * 2, 20)  # Max 20 points from likes
            score += min(reply_count * 5, 25)  # Max 25 points from replies

            # Sentiment bonus/penalty
            if sentiment == SentimentType.POSITIVE:
                score += 15
            elif sentiment == SentimentType.NEGATIVE:
                score += 10  # Negative comments need attention
            elif sentiment == SentimentType.NEUTRAL:
                score += 5

            # Toxicity penalty
            score -= toxicity_score * 30

            # Spam penalty
            score -= spam_score * 40

            # Question bonus
            text = comment_data.get("text", "")
            if "?" in text:
                score += 10

            # Length bonus (longer comments often more thoughtful)
            text_length = len(text)
            if 50 < text_length < 500:
                score += 5
            elif text_length >= 500:
                score += 3

            return max(0.0, min(100.0, score))  # Clamp between 0 - 100

        except Exception as e:
            self.logger.error(f"Error calculating engagement score: {e}")
            return 0.0


    def _should_respond_to_comment(self, comment: CommentData) -> bool:
        """Determine if we should respond to a comment."""
        try:
            # Don't respond to spam or toxic comments
            if (
                comment.spam_score > self.config["sentiment_analysis"]["spam_threshold"]
                or comment.toxicity_score
                > self.config["sentiment_analysis"]["toxicity_threshold"]
            ):
                return False

            # Don't respond if auto - reply is disabled
            if not self.config["comment_monitoring"]["auto_reply_enabled"]:
                return False

            # Respond to high engagement score comments
            if comment.engagement_score > 50:
                return True

            # Respond to questions
            if comment.questions:
                return True

            # Respond to negative sentiment (damage control)
            if (
                comment.sentiment == SentimentType.NEGATIVE
                and comment.engagement_score > 20
            ):
                return True

            # Respond to mentions
            if comment.mentions:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error determining response need: {e}")
            return False


    async def _generate_response(
        self, comment: CommentData
    ) -> Optional[EngagementResponse]:
        """Generate AI - powered response to comment."""
        try:
            # Determine response tone based on comment sentiment and content
            response_tone = self._determine_response_tone(comment)

            # Generate response using OpenAI
            response_text = await self._generate_ai_response(comment, response_tone)

            if not response_text:
                return None

            # Analyze generated response
            contains_cta = self._contains_call_to_action(response_text)
            contains_question = "?" in response_text
            contains_emoji = bool(
                re.search(
                    r"[\\U0001F600-\\U0001F64F\\U0001F300-\\U0001F5FF\\U0001F680-\\U0001F6FF\\U0001F1E0-\\U0001F1FF]",
                        response_text,
                        )
            )
            word_count = len(response_text.split())

            # Calculate confidence and personalization scores
            confidence_score = self._calculate_response_confidence(
                comment, response_text
            )
            personalization_level = self._calculate_personalization_level(
                comment, response_text
            )
            estimated_engagement = self._estimate_response_engagement(
                comment, response_text
            )

            response = EngagementResponse(
                response_id = f"resp_{comment.comment_id}_{int(time.time())}",
                    original_comment_id = comment.comment_id,
                    response_text = response_text,
                    response_tone = response_tone,
                    confidence_score = confidence_score,
                    personalization_level = personalization_level,
                    estimated_engagement = estimated_engagement,
                    language = comment.language,
                    contains_cta = contains_cta,
                    contains_question = contains_question,
                    contains_emoji = contains_emoji,
                    word_count = word_count,
                    generated_at = datetime.now(),
                    approved = confidence_score
                > 0.7,  # Auto - approve high confidence responses
                posted = False,
                    posted_at = None,
                    performance_metrics={},
                    )

            return response

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None


    def _determine_response_tone(self, comment: CommentData) -> ResponseTone:
        """Determine appropriate response tone based on comment."""
        try:
            # Negative sentiment - supportive tone
            if comment.sentiment == SentimentType.NEGATIVE:
                return ResponseTone.SUPPORTIVE

            # Questions - educational tone
            if comment.questions:
                return ResponseTone.EDUCATIONAL

            # High engagement - enthusiastic tone
            if comment.engagement_score > 70:
                return ResponseTone.ENTHUSIASTIC

            # Default to friendly
            return ResponseTone.FRIENDLY

        except Exception as e:
            self.logger.error(f"Error determining response tone: {e}")
            return ResponseTone.FRIENDLY


    async def _generate_ai_response(
        self, comment: CommentData, tone: ResponseTone
    ) -> Optional[str]:
        """Generate AI response using OpenAI."""
        try:
            # Prepare context for AI
            context = f"""
            You are a friendly YouTube content creator responding to a comment on your video.

            Comment: "{comment.text}"
            Comment sentiment: {comment.sentiment.value}
            Comment language: {comment.language}
            Response tone: {tone.value}

            Generate a {tone.value} response that:
            - Is authentic and personal
            - Addresses the comment directly
            - Is under {self.config['response_generation']['max_response_length']} characters
            - Matches the tone specified
            - Includes an emoji if appropriate
            - Encourages further engagement

            Response:
            """

            response = await openai.ChatCompletion.acreate(
                model = self.config["response_generation"]["ai_model"],
                    messages=[
                    {
                        "role": "system",
                            "content": "You are a helpful YouTube content creator assistant.",
                            },
                        {"role": "user", "content": context},
                        ],
                    max_tokens = 100,
                    temperature = 0.7,
                    )

            generated_text = response.choices[0].message.content.strip()

            # Clean up the response
            generated_text = self._clean_response_text(generated_text)

            return generated_text

        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return None


    def _clean_response_text(self, text: str) -> str:
        """Clean and format response text."""
        try:
            # Remove quotes if present
            text = text.strip("\\"'")

            # Ensure proper capitalization
            if text and text[0].islower():
                text = text[0].upper() + text[1:]

            # Add emoji if configured and not present
            if self.config["response_generation"]["emoji_usage"] and not re.search(
                r"[\\U0001F600-\\U0001F64F\\U0001F300-\\U0001F5FF\\U0001F680-\\U0001F6FF\\U0001F1E0-\\U0001F1FF]",
                    text,
                    ):

                # Add appropriate emoji based on content
                if any(
                    word in text.lower()
                    for word in ["thanks", "thank you", "appreciate"]
                ):
                    text += " 😊"
                elif any(
                    word in text.lower()
                    for word in ["great", "awesome", "amazing", "love"]
                ):
                    text += " 🎉"
                elif "?" in text:
                    text += " 🤔"
                else:
                    text += " 👍"

            return text

        except Exception as e:
            self.logger.error(f"Error cleaning response text: {e}")
            return text


    def _contains_call_to_action(self, text: str) -> bool:
        """Check if response contains a call to action."""
        cta_patterns = [
            r"\\b(?:subscribe|like|share|comment|check out|visit|follow)\\b",
                r"\\b(?:let me know|tell me|what do you think)\\b",
                r"\\b(?:try|watch|see|read)\\b.*\\b(?:video|channel|content)\\b",
                ]

        for pattern in cta_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False


    def _calculate_response_confidence(
        self, comment: CommentData, response: str
    ) -> float:
        """Calculate confidence score for generated response."""
        try:
            score = 0.5  # Base score

            # Length appropriateness
            if (
                10
                <= len(response)
                <= self.config["response_generation"]["max_response_length"]
            ):
                score += 0.2

            # Relevance (simple keyword matching)
            comment_words = set(comment.text.lower().split())
            response_words = set(response.lower().split())
            overlap = len(comment_words.intersection(response_words))
            if overlap > 0:
                score += min(overlap * 0.05, 0.2)

            # Question handling
            if comment.questions and "?" not in response:
                score -= 0.1  # Penalty for not addressing questions
            elif comment.questions and any(
                word in response.lower()
                for word in ["answer", "think", "believe", "know"]
            ):
                score += 0.1

            # Sentiment appropriateness
            if comment.sentiment == SentimentType.NEGATIVE and any(
                word in response.lower() for word in ["sorry", "understand", "help"]
            ):
                score += 0.1

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.error(f"Error calculating response confidence: {e}")
            return 0.5


    def _calculate_personalization_level(
        self, comment: CommentData, response: str
    ) -> float:
        """Calculate personalization level of response."""
        try:
            score = 0.0

            # Uses commenter's name or reference
            if comment.author_name.lower() in response.lower():
                score += 0.3

            # References specific content from comment
            comment_keywords = set(self._extract_keywords(comment.text))
            response_keywords = set(self._extract_keywords(response))
            overlap = len(comment_keywords.intersection(response_keywords))
            if overlap > 0:
                score += min(overlap * 0.1, 0.4)

            # Addresses specific questions or points
            if comment.questions and any(
                q_word in response.lower() for q_word in ["question", "ask", "answer"]
            ):
                score += 0.2

            # Uses personal pronouns appropriately
            if any(
                pronoun in response.lower() for pronoun in ["you", "your", "i", "my"]
            ):
                score += 0.1

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.error(f"Error calculating personalization level: {e}")
            return 0.0


    def _estimate_response_engagement(
        self, comment: CommentData, response: str
    ) -> float:
        """Estimate potential engagement for response."""
        try:
            base_score = comment.engagement_score/100.0  # Normalize to 0 - 1

            # Response quality factors
            if self._contains_call_to_action(response):
                base_score += 0.1

            if "?" in response:  # Questions encourage replies
                base_score += 0.15

            if len(response.split()) > 5:  # Substantial responses
                base_score += 0.1

            # Emoji usage
            if re.search(
                r"[\\U0001F600-\\U0001F64F\\U0001F300-\\U0001F5FF\\U0001F680-\\U0001F6FF\\U0001F1E0-\\U0001F1FF]",
                    response,
                    ):
                base_score += 0.05

            return max(0.0, min(1.0, base_score))

        except Exception as e:
            self.logger.error(f"Error estimating response engagement: {e}")
            return 0.0


    async def post_approved_responses(self) -> int:
        """Post approved responses to YouTube."""
        try:
            # Get approved, unposted responses
            approved_responses = await self._get_approved_responses()

            posted_count = 0

            for response in approved_responses:
                try:
                    # Post response to YouTube
                    success = await self.youtube_integration.reply_to_comment(
                        response.original_comment_id, response.response_text
                    )

                    if success:
                        # Update response status
                        response.posted = True
                        response.posted_at = datetime.now()
                        await self._update_response_status(response)
                        posted_count += 1

                        self.logger.info(
                            f"Posted response to comment {response.original_comment_id}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error posting response {response.response_id}: {e}"
                    )
                    continue

            return posted_count

        except Exception as e:
            self.logger.error(f"Error posting approved responses: {e}")
            return 0

    # Database helper methods


    async def _store_comment(self, comment: CommentData):
        """Store comment in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO comments
                    (comment_id,
    video_id,
    channel_id,
    author_name,
    author_channel_id,
    text,
                        like_count, reply_count, published_at, updated_at, parent_id, sentiment,
                         language, toxicity_score, spam_score, engagement_score, keywords,
                         mentions, questions, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        comment.comment_id,
                            comment.video_id,
                            comment.channel_id,
                            comment.author_name,
                            comment.author_channel_id,
                            comment.text,
                            comment.like_count,
                            comment.reply_count,
                            comment.published_at.isoformat(),
                            comment.updated_at.isoformat(),
                            comment.parent_id,
                            comment.sentiment.value,
                            comment.language,
                            comment.toxicity_score,
                            comment.spam_score,
                            comment.engagement_score,
                            json.dumps(comment.keywords),
                            json.dumps(comment.mentions),
                            json.dumps(comment.questions),
                            comment.processed_at.isoformat(),
                            ),
                        )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing comment: {e}")


    async def _store_response(self, response: EngagementResponse):
        """Store response in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO responses
                    (response_id, original_comment_id, response_text, response_tone,
                        confidence_score, personalization_level, estimated_engagement,
                         language, contains_cta, contains_question, contains_emoji,
                         word_count, generated_at, approved, posted, posted_at,
                         performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        response.response_id,
                            response.original_comment_id,
                            response.response_text,
                            response.response_tone.value,
                            response.confidence_score,
                            response.personalization_level,
                            response.estimated_engagement,
                            response.language,
                            response.contains_cta,
                            response.contains_question,
                            response.contains_emoji,
                            response.word_count,
                            response.generated_at.isoformat(),
                            response.approved,
                            response.posted,
                            response.posted_at.isoformat() if response.posted_at else None,
                            json.dumps(response.performance_metrics),
                            ),
                        )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing response: {e}")


    async def _get_approved_responses(self) -> List[EngagementResponse]:
        """Get approved responses that haven't been posted yet."""
        # Implementation would query database for approved, unposted responses
        return []


    async def _update_response_status(self, response: EngagementResponse):
        """Update response status in database."""
        # Implementation would update response status
        pass


    def get_engagement_status(self) -> Dict[str, Any]:
        """Get current engagement system status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count various metrics
                cursor = conn.execute("SELECT COUNT(*) FROM comments")
                total_comments = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM responses WHERE approved = 1"
                )
                approved_responses = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM responses WHERE posted = 1")
                posted_responses = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM community_posts")
                community_posts = cursor.fetchone()[0]

                return {
                    "status": "active",
                        "last_comment_check": (
                        self.last_comment_check.isoformat()
                        if self.last_comment_check
                        else None
                    ),
                        "total_comments_processed": total_comments,
                        "approved_responses": approved_responses,
                        "posted_responses": posted_responses,
                        "community_posts": community_posts,
                        "engagement_stats": dict(self.engagement_stats),
                        "config": self.config,
                        }
        except Exception as e:
            self.logger.error(f"Error getting engagement status: {e}")
            return {"error": str(e)}

# Factory function


def create_youtube_engagement_automation() -> YouTubeEngagementAutomation:
    """Create and return YouTube engagement automation instance."""
    return YouTubeEngagementAutomation()

# CLI interface for testing
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="YouTube Engagement Automation")
    parser.add_argument("--monitor", type = str, help="Monitor comments for video ID")
    parser.add_argument(
        "--post - responses", action="store_true", help="Post approved responses"
    )
    parser.add_argument("--status", action="store_true", help="Get system status")

    args = parser.parse_args()

    engagement = create_youtube_engagement_automation()

    if args.monitor:
        # Monitor comments for video
        result = asyncio.run(engagement.monitor_comments([args.monitor]))
        print(f"Processed {len(result)} comments")

    elif args.post_responses:
        # Post approved responses
        result = asyncio.run(engagement.post_approved_responses())
        print(f"Posted {result} responses")

    elif args.status:
        status = engagement.get_engagement_status()
        print(json.dumps(status, indent = 2, default = str))

    else:
        print("Use --monitor, --post - responses, or --status")