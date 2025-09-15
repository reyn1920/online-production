#!/usr/bin/env python3
""""""
Research Agent Tools Module

Implements comprehensive research capabilities including:
- Breaking news monitoring via RSS feeds
- Competitor analysis (TubeBuddy/VidIQ emulation)
- Market validation for digital products
- YouTube channel analysis and niche opportunity detection
""""""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

try:

    import feedparser
    import nltk
    import numpy as np
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
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
    keywords: List[str] = field(default_factory = list):
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
    niche_keywords: List[str] = field(default_factory = list):
    content_themes: List[str] = field(default_factory = list)
    opportunity_score: float = 0.0
    last_analyzed: datetime = field(default_factory = datetime.now)

@dataclass


class MarketOpportunity:
    """Represents a market opportunity for digital products"""

    niche: str
    keywords: List[str]
    search_volume: int
    competition_level: str  # low, medium, high
    trend_direction: str  # rising, stable, declining
    monetization_potential: float  # 0 - 1 score
    target_audience: str
    content_gaps: List[str] = field(default_factory = list):
    recommended_products: List[str] = field(default_factory = list)
    confidence_score: float = 0.0


class BreakingNewsWatcher:
    """Monitors RSS feeds for breaking news and trending topics"""


    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.feeds = self._get_default_feeds()
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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
        self.logger = logging.getLogger(__name__)


    def _get_default_feeds(self) -> List[Dict[str, str]]:
        """Get default RSS feeds for monitoring"""
        return [
            {
                "url": "https://feeds.feedburner.com/TechCrunch",
                    "category": NewsCategory.TECHNOLOGY,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://rss.cnn.com/rss/edition.rss",
                    "category": NewsCategory.GENERAL,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://feeds.reuters.com/reuters/businessNews",
                    "category": NewsCategory.BUSINESS,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://feeds.feedburner.com/venturebeat/SZYF",
                    "category": NewsCategory.TECHNOLOGY,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://feeds.feedburner.com/Mashable",
                    "category": NewsCategory.TECHNOLOGY,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://feeds.feedburner.com/socialmediaexaminer",
                    "category": NewsCategory.SOCIAL_MEDIA,
# BRACKET_SURGEON: disabled
#                     },
                {
                "url": "https://feeds.feedburner.com/MarketingLand",
                    "category": NewsCategory.MARKETING,
# BRACKET_SURGEON: disabled
#                     },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    async def monitor_feeds(self, duration_hours: int = 24) -> List[NewsItem]:
        """Monitor RSS feeds for specified duration"""
        if not feedparser:
            self.logger.error(
                "feedparser not available. Install with: pip install feedparser"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return []

        end_time = datetime.now() + timedelta(hours = duration_hours)
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

        results = await asyncio.gather(*tasks, return_exceptions = True)
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
                    title = entry.get("title", ""),
                        description = entry.get("description", ""),
                        link = entry.get("link", ""),
                        published = pub_date,
                        source = feed.feed.get("title", feed_config["url"]),
                        category = feed_config.get("category", NewsCategory.GENERAL),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

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
        """Process news items for sentiment, keywords, and relevance"""
        processed_items = []

        for item in news_items:
            try:
                # Extract keywords
                item.keywords = self._extract_keywords(
                    item.title + " " + item.description
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                # Calculate sentiment
                if TextBlob:
                    blob = TextBlob(item.title + " " + item.description)
                    item.sentiment_score = blob.sentiment.polarity

                # Calculate relevance score
                item.relevance_score = self._calculate_relevance(item)

                # Determine trend strength
                item.trend_strength = self._assess_trend_strength(item)

                processed_items.append(item)

            except Exception as e:
                self.logger.error(f"Error processing news item: {e}")
                processed_items.append(item)  # Add unprocessed item

        return processed_items


    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r"\\b\\w+\\b", text.lower())

        # Filter for relevant keywords
        relevant_keywords = []
        for keyword in self.keywords_of_interest:
            if keyword.lower() in text.lower():
                relevant_keywords.append(keyword)

        return relevant_keywords


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
# BRACKET_SURGEON: disabled
#                 }

        score += category_scores.get(item.category, 0.3)

        # Keyword relevance
        keyword_score = len(item.keywords) * 0.1
        score += min(keyword_score, 0.5)  # Cap at 0.5

        # Recency bonus
        hours_old = (datetime.now() - item.published).total_seconds()/3600
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


    def get_trending_topics(self, hours: int = 24) -> Dict[str, int]:
        """Get trending topics from recent news"""
        cutoff_time = datetime.now() - timedelta(hours = hours)
        recent_items = [
            item for item in self.news_cache.values() if item.published > cutoff_time
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        # Count keyword occurrences
        keyword_counts = {}
        for item in recent_items:
            for keyword in item.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Sort by frequency
        return dict(sorted(keyword_counts.items(),
    key = lambda x: x[1],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     reverse = True))


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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Analyze each channel
            analyzed_channels = []
            for channel_id in channel_ids:
                channel_data = await self._analyze_channel(channel_id)
                if channel_data:
                    analyzed_channels.append(channel_data)

            # Calculate opportunity scores
            self._calculate_opportunity_scores(analyzed_channels)

            return sorted(
                analyzed_channels, key = lambda x: x.opportunity_score, reverse = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

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
# BRACKET_SURGEON: disabled
#             ) as store:
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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ]:  # Limit to first 3 keywords to avoid quota exhaustion
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
# BRACKET_SURGEON: disabled
#                                 },
                            timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                fallback_channels = [
                    "UCBJycsmduvYEL83R_U4JriQ",  # Marques Brownlee (Tech)
                    "UCJ0 - OtVpF0wOKEqT2Z1HEtA",  # ElectroBOOM (Engineering)
                    "UCsooa4yRKGN_zEE8iknghZA",  # TED - Ed (Education)
                    "UC - lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie (Gaming/Entertainment)
                    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast (Entertainment)
                    "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers (Tech)
                    "UCEOXxzW2vU0P - 0THehuIIeg",  # Captain Disillusion (Science)
                    "UCHnyfMqiRRG1u - 2MsSQLbXA",  # Veritasium (Science)
                    "UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt (Science)
                    "UCR1IuLEqb6UEA_zQ81kwXfg",  # Real Engineering (Engineering)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]
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
                    channel_id = channel_id,
                        channel_name = channel_data["name"],
                        subscriber_count = channel_data["subscribers"],
                        total_views = channel_data["total_views"],
                        video_count = channel_data["video_count"],
                        upload_frequency = channel_data["upload_frequency"],
                        average_views = channel_data["average_views"],
                        engagement_rate = channel_data["engagement_rate"],
                        niche_keywords = channel_data["keywords"],
                        content_themes = channel_data["themes"],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

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
# BRACKET_SURGEON: disabled
#             ) as store:
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
# BRACKET_SURGEON: disabled
#                         },
                    timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            if channel_response.status_code != 200:
                self.logger.error(
                    f"YouTube API error for channel {channel_id}: {channel_response.status_code}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
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
# BRACKET_SURGEON: disabled
#                         },
                    timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

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
# BRACKET_SURGEON: disabled
#                                 },
                            timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

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
                                    total_engagement += (likes + comments)/views

                                # Extract keywords from video titles and descriptions
                                video_snippet = video.get("snippet", {})
                                title = video_snippet.get("title", "").lower()
                                description = video_snippet.get(
                                    "description", ""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 ).lower()

                                # Simple keyword extraction
                                for word in title.split():
                                    if len(word) > 3 and word not in keywords:
                                        keywords.append(word)

                            average_views = (
                                total_views//len(video_details)
                                if video_details
                                else 0
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            engagement_rate = (
                                total_engagement/len(video_details)
                                if video_details
                                else 0.0
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

                    # Calculate upload frequency based on recent videos
                    if len(video_items) >= 2:

                        from datetime import datetime

                        try:
                            latest_date = datetime.fromisoformat(
                                video_items[0]["snippet"]["publishedAt"].replace(
                                    "Z", "+00:00"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            oldest_date = datetime.fromisoformat(
                                video_items[-1]["snippet"]["publishedAt"].replace(
                                    "Z", "+00:00"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            days_diff = (latest_date - oldest_date).days
                            if days_diff > 0:
                                upload_frequency = (
                                    len(video_items) * 7
# BRACKET_SURGEON: disabled
#                                 )/days_diff  # videos per week
                        except Exception as e:
                            self.logger.warning(
                                f"Error calculating upload frequency: {e}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            upload_frequency = 1.0

                    # Extract themes from channel description and video categories
                    channel_description = snippet.get("description", "").lower()
                    if (
                        "tech" in channel_description
                        or "technology" in channel_description
# BRACKET_SURGEON: disabled
#                     ):
                        themes.append("Technology")
                    if "review" in channel_description:
                        themes.append("Reviews")
                    if (
                        "education" in channel_description
                        or "tutorial" in channel_description
# BRACKET_SURGEON: disabled
#                     ):
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
# BRACKET_SURGEON: disabled
#                 ),  # Minimum 0.1 videos per week
                "average_views": average_views,
                    "engagement_rate": min(engagement_rate, 1.0),  # Cap at 100%
                "keywords": keywords,
                    "themes": themes,
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            self.logger.error(
                f"Error fetching YouTube data for channel {channel_id}: {e}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
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
            sub_score = 1.0 - (channel.subscriber_count/max_subs)

            # Higher engagement rate = better niche
            engagement_score = channel.engagement_rate/max_engagement

            # Moderate upload frequency is optimal
            frequency_score = 1.0 - abs(channel.upload_frequency - 2.0)/max_frequency

            # Combine scores
            channel.opportunity_score = (
                sub_score * 0.4 + engagement_score * 0.4 + frequency_score * 0.2
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )


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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

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
# BRACKET_SURGEON: disabled
#     ) -> MarketOpportunity:
        """Validate a digital product idea"""
        try:
            # Analyze search volume and competition
            search_data = await self._analyze_search_metrics(target_keywords)

            # Assess market trends
            trend_data = await self._analyze_market_trends(
                product_concept, target_keywords
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Evaluate monetization potential
            monetization_score = self._assess_monetization_potential(
                product_concept, search_data
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Identify target audience
            target_audience = self._identify_target_audience(
                product_concept, target_keywords
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Find content gaps
            content_gaps = await self._identify_content_gaps(target_keywords)

            # Generate product recommendations
            recommended_products = self._generate_product_recommendations(
                product_concept, search_data
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                search_data, trend_data, monetization_score
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            opportunity = MarketOpportunity(
                niche = product_concept,
                    keywords = target_keywords,
                    search_volume = search_data["total_volume"],
                    competition_level = search_data["competition_level"],
                    trend_direction = trend_data["direction"],
                    monetization_potential = monetization_score,
                    target_audience = target_audience,
                    content_gaps = content_gaps,
                    recommended_products = recommended_products,
                    confidence_score = confidence_score,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            return opportunity

        except Exception as e:
            self.logger.error(f"Error validating product idea: {e}")
            # Return default opportunity with low confidence
            return MarketOpportunity(
                niche = product_concept,
                    keywords = target_keywords,
                    search_volume = 0,
                    competition_level="unknown",
                    trend_direction="unknown",
                    monetization_potential = 0.0,
                    target_audience="unknown",
                    confidence_score = 0.0,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def _analyze_search_metrics(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze search volume and competition for keywords using Google Ads API"""

        from backend.secret_store import SecretStore

        try:
            # Get Google Ads API credentials from secure storage
            with SecretStore(
                self.config.get("secrets_db", "data/secrets.sqlite")
# BRACKET_SURGEON: disabled
#             ) as store:
                api_key = store.get_secret("GOOGLE_ADS_API_KEY")
                customer_id = store.get_secret("GOOGLE_ADS_CUSTOMER_ID")
                developer_token = store.get_secret("GOOGLE_ADS_DEVELOPER_TOKEN")

                if not all([api_key, customer_id, developer_token]):
                    self.logger.error(
                        "Google Ads API credentials not configured in secret store"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    raise ValueError("Missing Google Ads API credentials")

            if not requests:
                self.logger.error("requests library not available")
                raise ImportError("requests library required for API calls")

            # Use Google Keyword Planner API to get real search volume data
            headers = {
                "Authorization": f"Bearer {api_key}",
                    "developer - token": developer_token,
                    "Content - Type": "application/json",
# BRACKET_SURGEON: disabled
#                     }

            # Prepare keyword ideas request
            keyword_ideas_request = {
                "customerId": customer_id,
                    "keywordPlanIdeaService": {
                    "generateKeywordIdeas": {
                        "keywordSeed": {
                            "keywords": keywords[
                                :10
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ]  # Limit to 10 keywords per request
# BRACKET_SURGEON: disabled
#                         },
                            "geoTargetConstants": [
                            "geoTargetConstants/2840"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],  # United States
                        "language": "languageConstants/1000",  # English
                        "keywordPlanNetwork": "GOOGLE_SEARCH",
# BRACKET_SURGEON: disabled
#                             }
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#                     }

            # Make API request to Google Ads
            response = requests.post(
                f"https://googleads.googleapis.com/v14/customers/{customer_id}/keywordPlanIdeas:generateKeywordIdeas",
                    headers = headers,
                    json = keyword_ideas_request,
                    timeout = 30,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            if response.status_code != 200:
                self.logger.error(
                    f"Google Ads API error: {response.status_code} - {response.text}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                raise ValueError(
                    f"API request failed with status {response.status_code}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

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
                sum(competition_scores)/len(competition_scores)
                if competition_scores
                else 0.5
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            if avg_competition < 0.3:
                competition_level = "low"
            elif avg_competition < 0.6:
                competition_level = "medium"
            else:
                competition_level = "high"

            self.logger.info(
                f"Retrieved search metrics for {len(keywords)} keywords: {total_volume} total volume"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            return {
                "total_volume": total_volume,
                    "competition_level": competition_level,
                    "avg_competition_score": avg_competition,
                    "keyword_count": len(results),
# BRACKET_SURGEON: disabled
#                     }

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                raise ImportError(
                    "pytrends library required for Google Trends analysis"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Initialize pytrends
            pytrends = TrendReq(hl="en - US", tz = 360)

            # Analyze trends for top keywords (limit to 5 for API efficiency)
            trend_keywords = keywords[:5] if len(keywords) >= 5 else keywords

            if not trend_keywords:
                self.logger.warning("No keywords provided for trend analysis")
                return {"direction": "stable", "confidence": "low"}

            # Build payload for Google Trends
            pytrends.build_payload(
                trend_keywords, cat = 0, timeframe="today 12 - m", geo="US", gprop=""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Get interest over time data
            interest_over_time = pytrends.interest_over_time()

            if interest_over_time.empty:
                self.logger.warning(
                    f"No trend data available for keywords: {trend_keywords}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
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
# BRACKET_SURGEON: disabled
#             )  # Average across all keywords and time
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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            return {
                "direction": direction,
                    "confidence": confidence,
                    "recent_avg": round(recent_avg, 2),
                    "older_avg": round(older_avg, 2),
                    "keywords_analyzed": len(trend_keywords),
# BRACKET_SURGEON: disabled
#                     }

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]
            has_trending = any(
                term in product_concept.lower()
                or any(term in keyword.lower() for keyword in keywords)
                for term in trending_terms
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            return {
                "direction": "rising" if has_trending else "stable",
                    "confidence": "low",
                    "error": str(e),
# BRACKET_SURGEON: disabled
#                     }


    def _assess_monetization_potential(
        self, product_concept: str, search_data: Dict
# BRACKET_SURGEON: disabled
#     ) -> float:
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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]
        if any(term in product_concept.lower() for term in high_value_terms):
            score += 0.4

        return min(score, 1.0)


    def _identify_target_audience(
        self, product_concept: str, keywords: List[str]
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Identify the target audience for the product"""
        # Simple audience identification based on keywords
        all_text = (product_concept + " " + " ".join(keywords)).lower()

        if any(term in all_text for term in ["business", "entrepreneur", "startup"]):
            return "Business Owners & Entrepreneurs"
        elif any(term in all_text for term in ["marketing", "social media", "content"]):
            return "Digital Marketers & Content Creators"
        elif any(
            term in all_text for term in ["developer", "programming", "code", "tech"]
# BRACKET_SURGEON: disabled
#         ):
            return "Developers & Tech Professionals"
        elif any(
            term in all_text for term in ["student", "learn", "education", "course"]
# BRACKET_SURGEON: disabled
#         ):
            return "Students & Learners"
        else:
            return "General Consumers"


    async def _identify_content_gaps(self, keywords: List[str]) -> List[str]:
        """Identify content gaps by analyzing existing content and search queries"""
        try:
            if not requests or not BeautifulSoup:
                self.logger.error(
                    "Required libraries not available for content gap analysis"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
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
                        "User - Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML,"
# BRACKET_SURGEON: disabled
#     like Gecko) Chrome/91.0.4472.124 Safari/537.36""
# BRACKET_SURGEON: disabled
#                     }

                    # Note: In production, consider using Google Custom Search API instead
                    # This is a basic implementation for content gap identification

                    # Analyze common content types that might be missing
                    common_content_types = [
                        f"Beginner's guide to {keyword}",'
                            f"Advanced {keyword} techniques",
                            f"{keyword} case studies",
                            f"{keyword} vs alternatives comparison",
                            f"{keyword} best practices",
                            f"{keyword} troubleshooting guide",
                            f"How to integrate {keyword}",
                            f"{keyword} ROI analysis",
                            f"{keyword} implementation checklist",
                            f"{keyword} common mistakes",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ]

                    # Simulate content gap detection based on keyword analysis
                    # In a full production system, this would:
                    # 1. Scrape search results to analyze existing content
                    # 2. Use SEO tools APIs to identify content gaps
                    # 3. Analyze competitor content comprehensiveness

                    # For now, identify gaps based on keyword characteristics
                    keyword_lower = keyword.lower()

                    if "tutorial" not in keyword_lower and "guide" not in keyword_lower:
                        content_gaps.append(f"Step - by - step {keyword} tutorial")

                    if (
                        "advanced" not in keyword_lower
                        and "expert" not in keyword_lower
# BRACKET_SURGEON: disabled
#                     ):
                        content_gaps.append(f"Advanced {keyword} strategies")

                    if "case" not in keyword_lower and "example" not in keyword_lower:
                        content_gaps.append(f"Real - world {keyword} case studies")

                    if "comparison" not in keyword_lower and "vs" not in keyword_lower:
                        content_gaps.append(f"{keyword} tool comparison")

                    # Add to analyzed topics to avoid duplicates
                    analyzed_topics.add(keyword_lower)

                except Exception as e:
                    self.logger.warning(
                        f"Error analyzing content gaps for keyword '{keyword}': {e}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    continue

            # Remove duplicates and limit results
            unique_gaps = list(set(content_gaps))

            # If no specific gaps found, provide general recommendations
            if not unique_gaps:
                unique_gaps = [
                    "Comprehensive beginner tutorials",
                        "Advanced implementation guides",
                        "Industry - specific case studies",
                        "Tool comparison and reviews",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ]

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
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]


    def _generate_product_recommendations(
        self, product_concept: str, search_data: Dict
    ) -> List[str]:
        """Generate recommended products based on market analysis"""
        recommendations = []

        # Base recommendations on search volume and competition
        if search_data["total_volume"] > 5000 and search_data["competition_level"] in [
            "low",
                "medium",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]:
            recommendations.extend(
                ["Online Course", "Digital Guide/Ebook", "Video Tutorial Series"]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        if search_data["competition_level"] == "low":
            recommendations.extend(["SaaS Tool", "Mobile App", "Consulting Service"])

        # Product - specific recommendations
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
# BRACKET_SURGEON: disabled
#     ) -> float:
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
        print("\\n1. Testing Breaking News Watcher...")
        news_watcher = BreakingNewsWatcher()

        # Test feed fetching (short duration for testing)
        try:
            news_items = await news_watcher.monitor_feeds(
                duration_hours = 0.1
# BRACKET_SURGEON: disabled
#             )  # 6 minutes
            print(f"Found {len(news_items)} news items")

            if news_items:
                print(f"Sample item: {news_items[0].title}")
                print(f"Relevance: {news_items[0].relevance_score}")
                print(f"Keywords: {news_items[0].keywords}")
        except Exception as e:
            print(f"News monitoring test failed: {e}")

        # Test trending topics
        trending = news_watcher.get_trending_topics()
        print(f"Trending topics: {list(trending.keys())[:5]}")

        # Test Competitor Analyzer
        print("\\n2. Testing Competitor Analyzer...")
        analyzer = CompetitorAnalyzer()

        try:
            niche_keywords = ["tech review", "smartphone", "gadget"]
            competitors = await analyzer.analyze_niche(niche_keywords, max_channels = 5)
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
            print("\\n3. Testing Market Validator...")
        validator = MarketValidator()

        try:
            product_concept = "AI - powered content creation tool"
            keywords = ["ai content", "automated writing", "content generator"]

            opportunity = await validator.validate_product_idea(
                product_concept, keywords
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
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

        print("\\nResearch tools testing completed!")

    # Run the test
    asyncio.run(test_research_tools())