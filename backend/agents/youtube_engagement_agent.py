#!/usr/bin/env python3
"""""""""
TRAE.AI YouTube Community Engagement Agent
""""""
Intelligently monitors YouTube comments and generates appropriate, contextual replies
using AI to build community engagement and foster meaningful conversations.
"""

TRAE.AI YouTube Community Engagement Agent



""""""


Features:



- Smart comment discovery and analysis
- AI - powered reply generation with context awareness
- Engagement scoring and prioritization
- Sentiment analysis and tone matching
- Anti - spam and authenticity measures
- Community participation monitoring
- Engagement tracking and optimization

Author: TRAE.AI System
Version: 1.0.0

"""

import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.integrations.ollama_integration import OllamaIntegration
from backend.integrations.youtube_integration import YouTubeIntegration
from backend.secret_store import SecretStore


class EngagementType(Enum):
    """Types of engagement interactions."""

    REPLY = "reply"
    LIKE = "like"
    HEART = "heart"
    PIN = "pin"


class CommentPriority(Enum):
    """Priority levels for comment engagement."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentType(Enum):
    """Sentiment analysis types."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class EngagementStatus(Enum):
    """Status of engagement actions."""

    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class CommentContext:
    """
Context information for a YouTube comment.


    comment_id: str
    video_id: str
    author_name: str
    comment_text: str
    created_at: datetime
    like_count: int
    reply_count: int
    is_reply: bool
    parent_comment_id: Optional[str]
    sentiment: SentimentType
    topic_keywords: List[str]
    relevance_score: float
    video_title: str
   
""""""

    video_category: str
   

    
   
"""
@dataclass
class EngagementOpportunity:
    """
Opportunity for community engagement.


    opportunity_id: str
    comment: CommentContext
    engagement_type: EngagementType
    priority: CommentPriority
    suggested_reply: str
    confidence_score: float
    reasoning: str
    keywords_matched: List[str]
    created_at: datetime
   
""""""

    expires_at: datetime
   

    
   
"""
@dataclass
class EngagementResult:
    """
Result of an engagement action.


    opportunity_id: str
    status: EngagementStatus
    posted_content: Optional[str]
    comment_id: Optional[str]
    engagement_metrics: Dict[str, int]
    posted_at: Optional[datetime]
   
""""""

    error_message: Optional[str]
   

    
   
"""
@dataclass
class TopicProfile:
    """
Profile for topic - based engagement.


    topic: str
    keywords: List[str]
    priority_weight: float
    engagement_style: str
    max_daily_engagements: int
    current_daily_count: int
   
""""""

    last_reset_date: datetime
   

    
   
"""
class YouTubeEngagementAgent:
   """

    
   

    TODO: Add documentation
   
""""""

    Intelligent YouTube community engagement agent that monitors comments
    and generates contextual replies to build community engagement.
   

    
   
""""""
    
   """
    def __init__(self, db_path: str = "data/youtube_engagement.sqlite"):
        self.logger = setup_logger("youtube_engagement")
        self.db_path = db_path
        self.youtube_integration = YouTubeIntegration()

        # Initialize Ollama with proper config
        ollama_config = {
            "ollama_endpoint": "http://localhost:11434",
            "default_model": "llama2:7b",
            "max_concurrent_requests": 3,
            "cache_enabled": True,
            "cache_ttl": 3600,
         }
        self.ollama_integration = OllamaIntegration(ollama_config)
        self.secret_store = SecretStore()

        # Configuration
        self.config = {
            "max_daily_engagements": 50,
            "min_confidence_score": 0.7,
            "engagement_cooldown_hours": 24,
            "max_reply_length": 500,
            "sentiment_threshold": 0.3,
            "relevance_threshold": 0.5,
         }

        # Initialize database
        self._init_database()

        # Load topic profiles
        self.topic_profiles = self._load_topic_profiles()

        self.logger.info("YouTube Engagement Agent initialized successfully")

    def _init_database(self) -> None:
        """
Initialize SQLite database for engagement tracking.

        try:
           
""""""

            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
           

            
           
""""""


            with sqlite3.connect(self.db_path) as conn:

            

           
""""""

            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
           

            
           
""""""

                
               

                cursor = conn.cursor()
               
""""""

                # Comments table
                cursor.execute(
                   

                    
                   
"""
                    CREATE TABLE IF NOT EXISTS comments (
                        comment_id TEXT PRIMARY KEY,
                            video_id TEXT NOT NULL,
                            author_name TEXT NOT NULL,
                            comment_text TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            like_count INTEGER DEFAULT 0,
                            reply_count INTEGER DEFAULT 0,
                            is_reply BOOLEAN DEFAULT FALSE,
                            parent_comment_id TEXT,
                            sentiment TEXT NOT NULL,
                            relevance_score REAL NOT NULL,
                            video_title TEXT,
                            video_category TEXT,
                            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (parent_comment_id) REFERENCES comments(comment_id)
                     )
                """"""

                

                 
                
"""
                 )
                """"""
                
               """

                cursor = conn.cursor()
               

                
               
"""
                # Engagement opportunities table
                cursor.execute(
                   """

                    
                   

                    CREATE TABLE IF NOT EXISTS engagement_opportunities (
                        opportunity_id TEXT PRIMARY KEY,
                            comment_id TEXT NOT NULL,
                            engagement_type TEXT NOT NULL,
                            priority TEXT NOT NULL,
                            suggested_reply TEXT NOT NULL,
                            confidence_score REAL NOT NULL,
                            reasoning TEXT NOT NULL,
                            keywords_matched TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            expires_at TIMESTAMP NOT NULL,
                            status TEXT DEFAULT 'pending',
                            FOREIGN KEY (comment_id) REFERENCES comments(comment_id)
                     )
                
""""""

                

                 
                
"""
                 )
                """

                 
                

                # Engagement results table
                cursor.execute(
                   
""""""
                    CREATE TABLE IF NOT EXISTS engagement_results (
                        result_id TEXT PRIMARY KEY,
                            opportunity_id TEXT NOT NULL,
                            status TEXT NOT NULL,
                            posted_content TEXT,
                            comment_id TEXT,
                            engagement_metrics TEXT,
                            posted_at TIMESTAMP,
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (opportunity_id) REFERENCES engagement_opportunities(opportunity_id)
                     )
                """"""

                

                 
                
"""
                 )
                """"""
                 
                """

                 )
                

                 
                
"""
                # Topic profiles table
                cursor.execute(
                   """

                    
                   

                    CREATE TABLE IF NOT EXISTS topic_profiles (
                        topic TEXT PRIMARY KEY,
                            keywords TEXT NOT NULL,
                            priority_weight REAL NOT NULL,
                            engagement_style TEXT NOT NULL,
                            max_daily_engagements INTEGER NOT NULL,
                            current_daily_count INTEGER DEFAULT 0,
                            last_reset_date DATE NOT NULL
                     )
                
""""""

                

                 
                
"""
                 )
                """

                 
                

                # Engagement history table
                cursor.execute(
                   
""""""
                    CREATE TABLE IF NOT EXISTS engagement_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            video_id TEXT NOT NULL,
                            comment_id TEXT NOT NULL,
                            engagement_type TEXT NOT NULL,
                            success BOOLEAN NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            response_text TEXT,
                            metrics TEXT
                     )
                """"""

                

                 
                
"""
                 )
                """"""
                 
                """

                 )
                

                 
                
"""
                conn.commit()
                self.logger.info("Database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def _load_topic_profiles(self) -> Dict[str, TopicProfile]:
        """
Load topic profiles from database or create defaults.

       
""""""

        profiles = {}
       

        
       
"""
        try:
            with sqlite3.connect(self.db_path) as conn:
       """

        
       

        profiles = {}
       
""""""
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM topic_profiles")
                rows = cursor.fetchall()

                for row in rows:
                    (
                        topic,
                        keywords_json,
                        priority_weight,
                        engagement_style,
                        max_daily,
                        current_count,
                        last_reset,
#                     ) = row
                    keywords = json.loads(keywords_json)
                    last_reset_date = datetime.fromisoformat(last_reset)

                    profiles[topic] = TopicProfile(
                        topic=topic,
                        keywords=keywords,
                        priority_weight=priority_weight,
                        engagement_style=engagement_style,
                        max_daily_engagements=max_daily,
                        current_daily_count=current_count,
                        last_reset_date=last_reset_date,
                     )

        except Exception as e:
            self.logger.warning(f"Failed to load topic profiles: {e}")

        # Create default profiles if none exist
        if not profiles:
            profiles = self._create_default_topic_profiles()

        return profiles

    def _create_default_topic_profiles(self) -> Dict[str, TopicProfile]:
        """Create default topic profiles for engagement."""
        default_profiles = {
            "ai_technology": TopicProfile(
                topic="ai_technology",
                keywords=[
                    "AI",
                    "artificial intelligence",
                    "machine learning",
                    "automation",
                    "technology",
                    "innovation",
                 ],
                priority_weight=1.0,
                engagement_style="informative",
                max_daily_engagements=15,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
             ),
            "content_creation": TopicProfile(
                topic="content_creation",
                keywords=[
                    "content",
                    "creation",
                    "video",
                    "editing",
                    "production",
                    "creative",
                    "tutorial",
                 ],
                priority_weight=0.9,
                engagement_style="helpful",
                max_daily_engagements=12,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
             ),
            "business_growth": TopicProfile(
                topic="business_growth",
                keywords=[
                    "business",
                    "growth",
                    "marketing",
                    "strategy",
                    "entrepreneurship",
                    "startup",
                 ],
                priority_weight=0.8,
                engagement_style="professional",
                max_daily_engagements=10,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
             ),
            "community_support": TopicProfile(
                topic="community_support",
                keywords=[
                    "help",
                    "support",
                    "question",
                    "problem",
                    "issue",
                    "assistance",
                 ],
                priority_weight=1.2,
                engagement_style="supportive",
                max_daily_engagements=20,
                current_daily_count=0,
                last_reset_date=datetime.now().date(),
             ),
         }

        # Save to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for profile in default_profiles.values():
                    cursor.execute(
                        """"""

                        INSERT OR REPLACE INTO topic_profiles
                        (topic,
    keywords,
    priority_weight,
    engagement_style,
    max_daily_engagements,
    current_daily_count,
#     last_reset_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    
,
"""
                        (
                            profile.topic,
                            json.dumps(profile.keywords),
                            profile.priority_weight,
                            profile.engagement_style,
                            profile.max_daily_engagements,
                            profile.current_daily_count,
                            profile.last_reset_date.isoformat(),
                         ),
                     )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save default topic profiles: {e}")

        return default_profiles

    async def monitor_video_comments(self, video_id: str) -> List[EngagementOpportunity]:
        """
Monitor comments on a specific video for engagement opportunities.

       
""""""

        opportunities = []
       

        
       
"""
        try:
            # Get video details
       """

        
       

        opportunities = []
       
""""""
            video_details = self.youtube_integration.get_video_details(video_id)
            if not video_details:
                self.logger.error(f"Could not fetch video details for {video_id}")
                return opportunities

            video_title = video_details.get("snippet", {}).get("title", "")
            video_category = video_details.get("snippet", {}).get("categoryId", "")

            # Fetch comments using YouTube API
            comments = await self._fetch_video_comments(video_id)

            for comment_data in comments:
                # Create comment context
                context = self._create_comment_context(comment_data, video_title, video_category)

                # Analyze comment for engagement opportunities
                opportunity = await self._analyze_comment_for_engagement(context)

                if opportunity:
                    opportunities.append(opportunity)
                    self._save_opportunity(opportunity)

            self.logger.info(
                f"Found {len(opportunities)} engagement opportunities for video {video_id}"
             )

        except Exception as e:
            self.logger.error(f"Failed to monitor comments for video {video_id}: {e}")

        return opportunities

    async def _fetch_video_comments(self, video_id: str) -> List[Dict[str, Any]]:
        """
Fetch comments for a video using YouTube API.

        try:
           
""""""

            # Use the YouTube integration to fetch comments
           

            
           
"""
            comment_data = self.youtube_integration.get_video_comments(
           """

            
           

            # Use the YouTube integration to fetch comments
           
""""""
                video_id=video_id, max_results=50, order="time"
             )

            self.logger.info(f"Fetched {len(comment_data)} comments for video {video_id}")
            return comment_data

        except Exception as e:
            self.logger.error(f"Failed to fetch comments for video {video_id}: {e}")
            return []

    def _create_comment_context(
        self, comment_data: Dict[str, Any], video_title: str, video_category: str
#     ) -> CommentContext:
        """
Create comment context from API data.

       
""""""

        # Handle both direct format and nested format from YouTube API
       

        
       
"""
        if "snippet" in comment_data and "topLevelComment" in comment_data["snippet"]:
            # Nested format from YouTube API
       """

        
       

        # Handle both direct format and nested format from YouTube API
       
""""""
            snippet = comment_data.get("snippet", {})
            top_level_comment = snippet.get("topLevelComment", {}).get("snippet", {})
            comment_text = top_level_comment.get("textDisplay", "")
            author_name = top_level_comment.get("authorDisplayName", "")
            published_at = top_level_comment.get("publishedAt", "")
            like_count = top_level_comment.get("likeCount", 0)
            reply_count = snippet.get("totalReplyCount", 0)
            comment_id = comment_data.get("id", "")
        else:
            # Direct format
            comment_text = comment_data.get("textDisplay", comment_data.get("text", ""))
            author_name = comment_data.get("authorDisplayName", comment_data.get("author", ""))
            published_at = comment_data.get("publishedAt", comment_data.get("published_at", ""))
            like_count = comment_data.get("likeCount", comment_data.get("like_count", 0))
            reply_count = comment_data.get("totalReplyCount", comment_data.get("reply_count", 0))
            comment_id = comment_data.get("id", "")

        # Parse datetime
        try:
            created_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now()

        # Analyze sentiment
        sentiment = self._analyze_sentiment(comment_text)

        # Extract topic keywords
        topic_keywords = self._extract_topic_keywords(comment_text)

        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(comment_text, topic_keywords)

        return CommentContext(
            comment_id=comment_id,
            video_id=comment_data.get("snippet", {}).get(
                "videoId", comment_data.get("video_id", "")
             ),
            author_name=author_name,
            comment_text=comment_text,
            created_at=created_at,
            like_count=like_count,
            reply_count=reply_count,
            is_reply=False,  # Top - level comments
            parent_comment_id=None,
            sentiment=sentiment,
            topic_keywords=topic_keywords,
            relevance_score=relevance_score,
            video_title=video_title,
            video_category=video_category,
         )

    def _analyze_sentiment(self, text: str) -> SentimentType:
        """
Analyze sentiment of comment text.

        try:
           
""""""

            # Simple keyword - based sentiment analysis
           

            
           
"""
            positive_words = [
                "great",
                "awesome",
                "amazing",
                "love",
                "excellent",
                "fantastic",
                "helpful",
                "thanks",
             ]
           """

            
           

            # Simple keyword - based sentiment analysis
           
""""""
            negative_words = [
                "bad",
                "terrible",
                "hate",
                "awful",
                "worst",
                "useless",
                "boring",
                "stupid",
             ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if positive_count > negative_count:
                return SentimentType.POSITIVE
            elif negative_count > positive_count:
                return SentimentType.NEGATIVE
            elif positive_count > 0 and negative_count > 0:
                return SentimentType.MIXED
            else:
                return SentimentType.NEUTRAL

        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            return SentimentType.NEUTRAL

    def _extract_topic_keywords(self, text: str) -> List[str]:
        """
Extract relevant topic keywords from comment text.

        keywords = []
       
""""""

        text_lower = text.lower()
       

        
       
"""
        for profile in self.topic_profiles.values():
            for keyword in profile.keywords:
       """

        
       

        text_lower = text.lower()
       
""""""

                if keyword.lower() in text_lower:
                    keywords.append(keyword)

        return list(set(keywords))  # Remove duplicates

    def _calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
        
Calculate relevance score based on keyword matches and text quality.
"""
        if not text.strip():
            """

            return 0.0
            

           
""""""

        # Base score from keyword matches
            

            return 0.0
            
"""
        keyword_score = min(len(keywords) * 0.2, 0.8)

        # Quality indicators
        quality_score = 0.0

        # Length bonus (not too short, not too long)
        text_length = len(text.split())
        if 5 <= text_length <= 100:
            quality_score += 0.1

        # Question bonus (indicates engagement opportunity)
        if "?" in text:
            quality_score += 0.1

        # Avoid spam indicators
        spam_indicators = ["subscribe", "like and subscribe", "check out my channel"]
        if any(indicator in text.lower() for indicator in spam_indicators):
            quality_score -= 0.3

        return min(keyword_score + quality_score, 1.0)

    async def _analyze_comment_for_engagement(
        self, context: CommentContext
    ) -> Optional[EngagementOpportunity]:
        """
Analyze a comment to determine if it presents an engagement opportunity.

        try:
           
""""""

            # Skip if relevance score is too low
           

            
           
"""
            if context.relevance_score < self.config["relevance_threshold"]:
           """

            
           

            # Skip if relevance score is too low
           
""""""
                return None

            # Find best matching topic profile
            best_profile = self._find_best_topic_profile(context)
            if not best_profile:
                return None

            # Check daily engagement limits
            if not self._check_engagement_limits(best_profile):
                return None

            # Generate contextual reply
            reply, confidence, reasoning = await self._generate_contextual_reply(
                context, best_profile
             )

            if confidence < self.config["min_confidence_score"]:
                return None

            # Calculate priority
            priority = self._calculate_priority(context, best_profile)

            # Create opportunity
            opportunity_id = hashlib.md5(
                f"{context.comment_id}_{datetime.now().isoformat()}".encode()
            ).hexdigest()

            return EngagementOpportunity(
                opportunity_id=opportunity_id,
                comment=context,
                engagement_type=EngagementType.REPLY,
                priority=priority,
                suggested_reply=reply,
                confidence_score=confidence,
                reasoning=reasoning,
                keywords_matched=context.topic_keywords,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
             )

        except Exception as e:
            self.logger.error(f"Failed to analyze comment for engagement: {e}")
            return None

    def _find_best_topic_profile(self, context: CommentContext) -> Optional[TopicProfile]:
        """
Find the best matching topic profile for a comment.

        best_profile = None
       
""""""

        best_score = 0.0
       

        
       
"""
        for profile in self.topic_profiles.values():
       """

        
       

        best_score = 0.0
       
""""""

            score = 0.0

            # Calculate keyword match score
            matched_keywords = [
                kw
                for kw in context.topic_keywords
                if kw.lower() in [pk.lower() for pk in profile.keywords]
             ]
            if matched_keywords:
                score = len(matched_keywords) * profile.priority_weight

                if score > best_score:
                    best_score = score
                    best_profile = profile

        return best_profile

    def _check_engagement_limits(self, profile: TopicProfile) -> bool:
        
Check if engagement limits allow for new engagement.
""""""

        
       

        # Reset daily count if it's a new day
       
""""""

        today = datetime.now().date()
       

        
       
"""
        # Reset daily count if it's a new day
       """

        
       

        if profile.last_reset_date < today:
            profile.current_daily_count = 0
            profile.last_reset_date = today
           
""""""

            self._update_topic_profile(profile)
           

            
           
""""""


            

           

            self._update_topic_profile(profile)
           
""""""

        return profile.current_daily_count < profile.max_daily_engagements

    def _update_topic_profile(self, profile: TopicProfile) -> None:
        
Update topic profile in database.
"""
        try:
            """

            with sqlite3.connect(self.db_path) as conn:
            

                cursor = conn.cursor()
                cursor.execute(
                   
""""""

                    UPDATE topic_profiles
                    SET current_daily_count = ?, last_reset_date = ?
                    WHERE topic = ?
                
,
"""
                    (
                        profile.current_daily_count,
                        profile.last_reset_date.isoformat(),
                        profile.topic,
                     ),
                 )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update topic profile: {e}")
            """

            with sqlite3.connect(self.db_path) as conn:
            

           
""""""

    async def _generate_contextual_reply(
        self, context: CommentContext, profile: TopicProfile
    ) -> Tuple[str, float, str]:
        
Generate a contextual reply using AI.
"""
        try:
           """

            
           

            # Create prompt for AI reply generation
           
""""""

           

            
           
"""
            style_guidance = self._get_style_guidance(profile.engagement_style, context.sentiment)
           """"""
            
           """

            # Create prompt for AI reply generation
           

            
           
""""""


            

           

            prompt = f
           
""""""



You are a helpful YouTube content creator responding to a comment on your video.

"""

Video Title: {context.video_title}
Comment: "{context.comment_text}"
Comment Sentiment: {context.sentiment.value}
Author: {context.author_name}
"""
You are a helpful YouTube content creator responding to a comment on your video.



Style Guidelines: {style_guidance}

Generate a helpful, engaging reply that:
1. Addresses the comment directly
2. Adds value to the conversation
3. Maintains a {profile.engagement_style} tone
4. Is under {self.config['max_reply_length']} characters
5. Encourages further engagement

Reply:
""""""
            # Generate reply using Ollama
           """

            
           

            response = await self.ollama_integration.generate_response(
           
""""""

            # Generate reply using Ollama
           

            
           
"""
                prompt=prompt, model="llama3.1:8b", max_tokens=150
             )

            if not response or not response.get("response"):
                return "", 0.0, "Failed to generate AI response"

            reply_text = response["response"].strip()

            # Evaluate reply quality
            confidence, reasoning = self._evaluate_reply_quality(reply_text, context, profile)

            return reply_text, confidence, reasoning

        except Exception as e:
            self.logger.error(f"Failed to generate contextual reply: {e}")
            return "", 0.0, f"Error generating reply: {str(e)}"

    def _get_style_guidance(self, engagement_style: str, sentiment: SentimentType) -> str:
        """Get style guidance for reply generation."""
        style_guides = {
            "informative": "Be educational \"
#     and provide useful information. Use clear explanations.",
            "helpful": "Be supportive \"
#     and offer practical assistance. Focus on solving problems.",
            "professional": "Maintain a business - appropriate tone. Be courteous \"
#     and authoritative.",
            "supportive": "Be encouraging \"
#     and empathetic. Show understanding \
#     and offer help.",
            "friendly": "Be warm and approachable. Use conversational language.",
         }

        base_guidance = style_guides.get(engagement_style, "Be helpful and engaging.")

        # Adjust for sentiment
        if sentiment == SentimentType.NEGATIVE:
            base_guidance += " Address concerns constructively and offer solutions."
        elif sentiment == SentimentType.POSITIVE:
            base_guidance += " Acknowledge the positive feedback and build on it."

        return base_guidance

    def _evaluate_reply_quality(
        self, reply_text: str, context: CommentContext, profile: TopicProfile
    ) -> Tuple[float, str]:
        """
Evaluate the quality of a generated reply.

        score = 0.0
       
""""""

        reasons = []
       

        
       
"""
        # Length check
       """

        
       

        reasons = []
       
""""""
        if len(reply_text) > self.config["max_reply_length"]:
            score -= 0.3
            reasons.append("Reply too long")
        elif len(reply_text) < 10:
            score -= 0.2
            reasons.append("Reply too short")
        else:
            score += 0.2
            reasons.append("Appropriate length")

        # Relevance check
        comment_words = set(context.comment_text.lower().split())
        reply_words = set(reply_text.lower().split())
        overlap = len(comment_words.intersection(reply_words))

        if overlap > 0:
            score += min(overlap * 0.1, 0.3)
            reasons.append(f"Good relevance ({overlap} shared words)")

        # Quality indicators
        if "?" in context.comment_text and any(
            word in reply_text.lower() for word in ["yes", "no", "here", "try", "can"]
#         ):
            score += 0.2
            reasons.append("Addresses question")

        # Avoid generic responses
        generic_phrases = [
            "thanks for watching",
            "please subscribe",
            "check out my other videos",
         ]
        if any(phrase in reply_text.lower() for phrase in generic_phrases):
            score -= 0.2
            reasons.append("Contains generic phrases")

        # Engagement potential
        if "?" in reply_text:
            score += 0.1
            reasons.append("Encourages further engagement")

        final_score = max(0.0, min(1.0, 0.5 + score))  # Base score of 0.5
        reasoning = "; ".join(reasons)

        return final_score, reasoning

    def _calculate_priority(
        self, context: CommentContext, profile: TopicProfile
#     ) -> CommentPriority:
        """
Calculate priority level for engagement opportunity.

       
""""""

        score = 0.0
       

        
       
"""
        # Base score from relevance and profile weight
        score += context.relevance_score * profile.priority_weight
       """

        
       

        score = 0.0
       
""""""
        # Engagement metrics bonus
        if context.like_count > 10:
            score += 0.2
        if context.like_count > 50:
            score += 0.3

        # Sentiment considerations
        if context.sentiment == SentimentType.NEGATIVE:
            score += 0.4  # Higher priority for addressing concerns
        elif context.sentiment == SentimentType.POSITIVE:
            score += 0.2  # Good opportunity to build on positive feedback

        # Question bonus
        if "?" in context.comment_text:
            score += 0.3

        # Recent comment bonus
        hours_old = (datetime.now() - context.created_at).total_seconds() / 3600
        if hours_old < 2:
            score += 0.2
        elif hours_old < 24:
            score += 0.1

        # Convert score to priority
        if score >= 1.5:
            return CommentPriority.CRITICAL
        elif score >= 1.0:
            return CommentPriority.HIGH
        elif score >= 0.6:
            return CommentPriority.MEDIUM
        else:
            return CommentPriority.LOW

    def _save_opportunity(self, opportunity: EngagementOpportunity) -> None:
        """
Save engagement opportunity to database.

        try:
            
"""
            with sqlite3.connect(self.db_path) as conn:
            """"""
                cursor = conn.cursor()
               """"""
            with sqlite3.connect(self.db_path) as conn:
            """"""
                # Save comment context first
                cursor.execute(
                   """

                    
                   

                    INSERT OR REPLACE INTO comments
                    (comment_id,
    video_id,
    author_name,
    comment_text,
    created_at,
    like_count,
                        reply_count, is_reply, parent_comment_id, sentiment, relevance_score,
#                          video_title, video_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                
""","""

                    (
                        opportunity.comment.comment_id,
                        opportunity.comment.video_id,
                        opportunity.comment.author_name,
                        opportunity.comment.comment_text,
                        opportunity.comment.created_at,
                        opportunity.comment.like_count,
                        opportunity.comment.reply_count,
                        opportunity.comment.is_reply,
                        opportunity.comment.parent_comment_id,
                        opportunity.comment.sentiment.value,
                        opportunity.comment.relevance_score,
                        opportunity.comment.video_title,
                        opportunity.comment.video_category,
                     ),
                

                 
                
"""
                 )
                """

                 
                

                # Save opportunity
                cursor.execute(
                   
""""""

                    INSERT OR REPLACE INTO engagement_opportunities
                    (opportunity_id,
    comment_id,
    engagement_type,
    priority,
    suggested_reply,
#                         confidence_score, reasoning, keywords_matched, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                
,
"""
                    (
                        opportunity.opportunity_id,
                        opportunity.comment.comment_id,
                        opportunity.engagement_type.value,
                        opportunity.priority.value,
                        opportunity.suggested_reply,
                        opportunity.confidence_score,
                        opportunity.reasoning,
                        json.dumps(opportunity.keywords_matched),
                        opportunity.created_at,
                        opportunity.expires_at,
                     ),
                """

                 
                

                 )
                
""""""

                

                 
                
"""
                 )
                """"""
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to save engagement opportunity: {e}")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
Process YouTube engagement tasks.

        try:
           
""""""

            # Check if community building is enabled
           

            
           
"""
            if not self.is_action_allowed("community_building"):
           """

            
           

            # Check if community building is enabled
           
""""""
                return {
                    "status": "error",
                    "message": "Community building is disabled in configuration",
                 }

            task_type = task.get("type")

            if task_type == "monitor_video_comments":
                video_id = task.get("video_id")
                if not video_id:
                    return {"status": "error", "message": "Video ID required"}

                opportunities = await self.monitor_video_comments(video_id)
                return {
                    "status": "success",
                    "opportunities_found": len(opportunities),
                    "opportunities": [asdict(opp) for opp in opportunities],
                 }

            elif task_type == "get_engagement_opportunities":
                opportunities = self._get_pending_opportunities()
                return {"status": "success", "opportunities": opportunities}

            elif task_type == "execute_engagement":
                opportunity_id = task.get("opportunity_id")
                if not opportunity_id:
                    return {"status": "error", "message": "Opportunity ID required"}

                result = await self._execute_engagement(opportunity_id)
                return result

            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}

        except Exception as e:
            self.logger.error(f"Failed to process task: {e}")
            return {"status": "error", "message": str(e)}

    def is_action_allowed(self, action: str) -> bool:
        """
Check if an action is allowed based on configuration.

        try:
           
""""""

            # Load configuration from state.json
           

            
           
"""
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "state.json",
             )
           """

            
           

            # Load configuration from state.json
           
""""""
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    return config.get("automation", {}).get(action, True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to check action permission: {e}")
            return True

    def _get_pending_opportunities(self) -> List[Dict[str, Any]]:
        """
Get pending engagement opportunities from database.

       
""""""

        opportunities = []
       

        
       
"""
        try:
            with sqlite3.connect(self.db_path) as conn:
       """

        
       

        opportunities = []
       
""""""

                cursor = conn.cursor()
                cursor.execute(
                   

                    
                   
"""
                    SELECT eo.*, c.comment_text, c.author_name, c.video_title
                    FROM engagement_opportunities eo
                    JOIN comments c ON eo.comment_id = c.comment_id
                    WHERE eo.status = 'pending' AND eo.expires_at > datetime('now')
                    ORDER BY eo.priority DESC, eo.confidence_score DESC
                    LIMIT 50
                """"""

                

                 
                
"""
                 )
                """"""
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                for row in rows:
                    opportunity = dict(zip(columns, row))
                    opportunity["keywords_matched"] = json.loads(opportunity["keywords_matched"])
                    opportunities.append(opportunity)

        except Exception as e:
            self.logger.error(f"Failed to get pending opportunities: {e}")

        return opportunities

    async def _execute_engagement(self, opportunity_id: str) -> Dict[str, Any]:
        """
Execute an engagement opportunity.

        try:
            # Get opportunity details
            
"""
            with sqlite3.connect(self.db_path) as conn:
            """

                cursor = conn.cursor()
                cursor.execute(
                   

                    
                   
"""
                    SELECT eo.*, c.*
                        FROM engagement_opportunities eo
                    JOIN comments c ON eo.comment_id = c.comment_id
                    WHERE eo.opportunity_id = ?
                """
,

                    (opportunity_id,),
                
""""""

                 )
                

                 
                
""""""

            with sqlite3.connect(self.db_path) as conn:
            

           
""""""
                row = cursor.fetchone()
                if not row:
                    return {"status": "error", "message": "Opportunity not found"}

            # Extract data from row
            suggested_reply = row[4]  # suggested_reply
            comment_id = row[1]  # comment_id
            engagement_type = row[2]  # engagement_type

            # Execute the engagement using YouTube API
            success = False
            posted_comment_id = None
            error_message = None

            try:
                if engagement_type == "reply":
                    # Post a reply to the comment
                    api_result = self.youtube_integration.post_comment_reply(
                        parent_comment_id=comment_id, reply_text=suggested_reply
                     )

                    if api_result.get("status") == "success":
                        success = True
                        posted_comment_id = api_result.get("comment_id")
                        self.logger.info(f"Successfully posted reply to comment {comment_id}")
                    else:
                        error_message = api_result.get("error", "Unknown error")
                        self.logger.error(f"Failed to post reply: {error_message}")

            except Exception as api_error:
                error_message = str(api_error)
                self.logger.error(f"API error during engagement: {api_error}")

            # Create result
            result = EngagementResult(
                opportunity_id=opportunity_id,
                status=EngagementStatus.POSTED if success else EngagementStatus.FAILED,
                posted_content=suggested_reply if success else None,
                comment_id=posted_comment_id,
                engagement_metrics={"likes": 0, "replies": 0},
                posted_at=datetime.now() if success else None,
                error_message=error_message,
             )

            # Save result
            self._save_engagement_result(result)

            # Update opportunity status
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """"""

                    UPDATE engagement_opportunities
                    SET status = ?
                    WHERE opportunity_id = ?
                
,
"""
                    ("posted" if success else "failed", opportunity_id),
                 )
                conn.commit()

            return {
                "status": "success" if success else "error",
                "message": (
                    "Engagement executed successfully"
                    if success
                    else f"Engagement failed: {error_message}"
                 ),
                "result": asdict(result),
             }

        except Exception as e:
            self.logger.error(f"Failed to execute engagement: {e}")
            return {"status": "error", "message": str(e)}

    def _save_engagement_result(self, result: EngagementResult) -> None:
        """
Save engagement result to database.

        try:
            
"""
            with sqlite3.connect(self.db_path) as conn:
            """

                cursor = conn.cursor()
                cursor.execute(
                   

                    
                   
"""
                    INSERT INTO engagement_results
                    (result_id, opportunity_id, status, posted_content, comment_id,
#                         engagement_metrics, posted_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        hashlib.md5(
                            f"{result.opportunity_id}_{datetime.now().isoformat()}".encode()
                        ).hexdigest(),
                        result.opportunity_id,
                        result.status.value,
                        result.posted_content,
                        result.comment_id,
                        json.dumps(result.engagement_metrics),
                        result.posted_at,
                        result.error_message,
                     ),
                 )
                conn.commit()
            """

            with sqlite3.connect(self.db_path) as conn:
            

           
""""""
        except Exception as e:
            self.logger.error(f"Failed to save engagement result: {e}")

    def get_engagement_stats(self) -> Dict[str, Any]:
        """Get engagement statistics."""
        stats = {
            "total_opportunities": 0,
            "pending_opportunities": 0,
            "completed_engagements": 0,
            "success_rate": 0.0,
            "daily_engagement_counts": {},
            "top_topics": [],
         }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total opportunities
                cursor.execute("SELECT COUNT(*) FROM engagement_opportunities")
                stats["total_opportunities"] = cursor.fetchone()[0]

                # Pending opportunities
                cursor.execute(
                    "SELECT COUNT(*) FROM engagement_opportunities WHERE status = 'pending'"
                 )
                stats["pending_opportunities"] = cursor.fetchone()[0]

                # Completed engagements
                cursor.execute("SELECT COUNT(*) FROM engagement_results WHERE status = 'posted'")
                stats["completed_engagements"] = cursor.fetchone()[0]

                # Success rate
                if stats["total_opportunities"] > 0:
                    stats["success_rate"] = (
                        stats["completed_engagements"] / stats["total_opportunities"]
                     )

                # Daily engagement counts by topic
                for topic, profile in self.topic_profiles.items():
                    stats["daily_engagement_counts"][topic] = {
                        "current": profile.current_daily_count,
                        "max": profile.max_daily_engagements,
                     }

        except Exception as e:
            self.logger.error(f"Failed to get engagement stats: {e}")

        return stats


if __name__ == "__main__":
    # Example usage

    import asyncio

    async def main():
        agent = YouTubeEngagementAgent()

        # Example: Monitor comments on a video
        video_id = "example_video_id"
        opportunities = await agent.monitor_video_comments(video_id)

        print(f"Found {len(opportunities)} engagement opportunities")

        # Get stats
        stats = agent.get_engagement_stats()
        print(f"Engagement stats: {stats}")

    asyncio.run(main())