import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_api import APIError, BaseAPI, RateLimitConfig

logger = logging.getLogger(__name__)


class YouTubeAPI(BaseAPI):
    """YouTube Data API v3 integration for video and channel analysis"""

    def __init__(self, api_key: Optional[str] = None):
        # YouTube API has strict quota limits
        rate_config = RateLimitConfig(
            requests_per_minute=100,  # Conservative rate limiting
            requests_per_hour=1000,
            requests_per_day=10000,  # Default quota is 10,000 units/day
            burst_limit=10,
        )
        super().__init__(rate_config)
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

        # YouTube API quota costs per operation
        self.quota_costs = {
            "search": 100,
            "videos": 1,
            "channels": 1,
            "playlists": 1,
            "playlistItems": 1,
            "commentThreads": 1,
            "comments": 1,
        }

        # Video categories mapping
        self.categories = {
            "1": "Film & Animation",
            "2": "Autos & Vehicles",
            "10": "Music",
            "15": "Pets & Animals",
            "17": "Sports",
            "19": "Travel & Events",
            "20": "Gaming",
            "22": "People & Blogs",
            "23": "Comedy",
            "24": "Entertainment",
            "25": "News & Politics",
            "26": "Howto & Style",
            "27": "Education",
            "28": "Science & Technology",
        }

    async def health_check(self) -> bool:
        """Check if YouTube API is accessible"""
        if not self.api_key:
            logger.error("YouTube API key not provided")
            return False

        try:
            # Simple test query
            result = await self.search_videos(query="test", max_results=1)
            return len(result.get("videos", [])) > 0
        except Exception as e:
            logger.error(f"YouTube health check failed: {e}")
            return False

    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            "service": "YouTube Data API v3",
            "daily_limit": self.rate_limiter.config.requests_per_day,
            "daily_used": self.rate_limiter.daily_count,
            "hourly_limit": self.rate_limiter.config.requests_per_hour,
            "hourly_used": self.rate_limiter.hourly_count,
            "tokens_available": int(self.rate_limiter.tokens),
            "quota_costs": self.quota_costs,
            "api_key_provided": bool(self.api_key),
        }

    async def search_videos(
        self,
        query: str,
        max_results: int = 50,
        order: str = "relevance",
        published_after: Optional[datetime] = None,
        published_before: Optional[datetime] = None,
        region_code: str = "US",
        category_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for videos on YouTube"""
        if not self.api_key:
            raise APIError("YouTube API key not provided")

        await self.rate_limiter.acquire()

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),  # YouTube API limit
            "order": order,
            "regionCode": region_code,
            "key": self.api_key,
        }

        if published_after:
            params["publishedAfter"] = published_after.isoformat() + "Z"

        if published_before:
            params["publishedBefore"] = published_before.isoformat() + "Z"

        if category_id:
            params["videoCategoryId"] = category_id

        try:
            endpoint = f"{self.base_url}/search"
            response_data = await self._make_youtube_request(endpoint, params)

            # Get detailed video information
            video_ids = [
                item["id"]["videoId"] for item in response_data.get("items", [])
            ]
            detailed_videos = (
                await self.get_video_details(video_ids) if video_ids else []
            )

            return {
                "query": query,
                "total_results": response_data.get("pageInfo", {}).get(
                    "totalResults", 0
                ),
                "videos": detailed_videos,
                "next_page_token": response_data.get("nextPageToken"),
                "search_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to search YouTube videos: {e}")

    async def get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information about specific videos"""
        if not self.api_key:
            raise APIError("YouTube API key not provided")

        if not video_ids:
            return []

        await self.rate_limiter.acquire()

        # YouTube API allows up to 50 IDs per request
        video_chunks = [video_ids[i : i + 50] for i in range(0, len(video_ids), 50)]
        all_videos = []

        for chunk in video_chunks:
            params = {
                "part": "snippet,statistics,contentDetails,status",
                "id": ",".join(chunk),
                "key": self.api_key,
            }

            try:
                endpoint = f"{self.base_url}/videos"
                response_data = await self._make_youtube_request(endpoint, params)

                for item in response_data.get("items", []):
                    video = self._parse_video_data(item)
                    all_videos.append(video)

                # Rate limiting between chunks
                if len(video_chunks) > 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to get video details for chunk: {e}")
                continue

        return all_videos

    async def get_trending_videos(
        self,
        region_code: str = "US",
        category_id: Optional[str] = None,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get trending videos from YouTube"""
        if not self.api_key:
            raise APIError("YouTube API key not provided")

        await self.rate_limiter.acquire()

        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": min(max_results, 50),
            "key": self.api_key,
        }

        if category_id:
            params["videoCategoryId"] = category_id

        try:
            endpoint = f"{self.base_url}/videos"
            response_data = await self._make_youtube_request(endpoint, params)

            videos = []
            for item in response_data.get("items", []):
                video = self._parse_video_data(item)
                videos.append(video)

            return videos

        except Exception as e:
            raise APIError(f"Failed to get trending videos: {e}")

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get detailed information about a YouTube channel"""
        if not self.api_key:
            raise APIError("YouTube API key not provided")

        await self.rate_limiter.acquire()

        params = {
            "part": "snippet,statistics,contentDetails,brandingSettings",
            "id": channel_id,
            "key": self.api_key,
        }

        try:
            endpoint = f"{self.base_url}/channels"
            response_data = await self._make_youtube_request(endpoint, params)

            items = response_data.get("items", [])
            if not items:
                raise APIError(f"Channel {channel_id} not found")

            return self._parse_channel_data(items[0])

        except Exception as e:
            raise APIError(f"Failed to get channel info: {e}")

    async def analyze_video_trends(
        self, keywords: List[str], days_back: int = 30, region_code: str = "US"
    ) -> Dict[str, Any]:
        """Analyze video trends for given keywords"""
        try:
            trend_analysis = {}

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            for keyword in keywords:
                try:
                    # Search for videos with this keyword
                    search_result = await self.search_videos(
                        query=keyword,
                        max_results=50,
                        order="date",
                        published_after=start_date,
                        region_code=region_code,
                    )

                    videos = search_result.get("videos", [])

                    if not videos:
                        trend_analysis[keyword] = {
                            "keyword": keyword,
                            "video_count": 0,
                            "total_views": 0,
                            "avg_views": 0,
                            "trend_score": 0,
                            "top_videos": [],
                        }
                        continue

                    # Calculate metrics
                    total_views = sum(
                        int(video.get("view_count", 0)) for video in videos
                    )
                    avg_views = total_views / len(videos) if videos else 0

                    # Calculate trend score based on recency and engagement
                    trend_score = 0
                    for video in videos:
                        days_old = (
                            datetime.utcnow()
                            - datetime.fromisoformat(
                                video.get("published_at", "").replace("Z", "+00:00")
                            )
                        ).days

                        # More recent videos get higher scores
                        recency_factor = max(0, (days_back - days_old) / days_back)
                        engagement = (
                            int(video.get("view_count", 0))
                            + int(video.get("like_count", 0)) * 10
                        )

                        trend_score += engagement * recency_factor

                    # Sort videos by view count
                    top_videos = sorted(
                        videos, key=lambda x: int(x.get("view_count", 0)), reverse=True
                    )[:5]

                    trend_analysis[keyword] = {
                        "keyword": keyword,
                        "video_count": len(videos),
                        "total_views": total_views,
                        "avg_views": int(avg_views),
                        "trend_score": int(trend_score),
                        "top_videos": [
                            {
                                "title": video.get("title", ""),
                                "channel": video.get("channel_title", ""),
                                "views": int(video.get("view_count", 0)),
                                "likes": int(video.get("like_count", 0)),
                                "published": video.get("published_at", ""),
                                "url": f"https://youtube.com/watch?v={video.get('video_id', '')}",
                            }
                            for video in top_videos
                        ],
                    }

                    # Add delay between requests
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Failed to analyze trend for {keyword}: {e}")
                    continue

            # Rank keywords by trend score
            ranked_trends = sorted(
                trend_analysis.items(), key=lambda x: x[1]["trend_score"], reverse=True
            )

            return {
                "keywords": trend_analysis,
                "ranked_trends": [{"keyword": k, **v} for k, v in ranked_trends],
                "analysis_period_days": days_back,
                "region_code": region_code,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to analyze video trends: {e}")

    async def find_viral_content(
        self,
        category_id: Optional[str] = None,
        region_code: str = "US",
        min_views: int = 100000,
        days_back: int = 7,
    ) -> Dict[str, Any]:
        """Find viral content based on view thresholds and engagement"""
        try:
            # Get trending videos
            trending_videos = await self.get_trending_videos(
                region_code=region_code, category_id=category_id, max_results=50
            )

            # Filter for viral content
            viral_videos = []
            for video in trending_videos:
                view_count = int(video.get("view_count", 0))
                published_date = datetime.fromisoformat(
                    video.get("published_at", "").replace("Z", "+00:00")
                )

                # Check if video is recent and has high views
                days_old = (
                    datetime.utcnow().replace(tzinfo=published_date.tzinfo)
                    - published_date
                ).days

                if view_count >= min_views and days_old <= days_back:
                    # Calculate viral score
                    like_count = int(video.get("like_count", 0))
                    comment_count = int(video.get("comment_count", 0))

                    # Engagement rate
                    engagement_rate = (
                        (like_count + comment_count) / max(view_count, 1) * 100
                    )

                    # Viral score considers views, engagement, and recency
                    viral_score = (
                        (view_count / 1000)  # Views in thousands
                        + (engagement_rate * 100)  # Engagement boost
                        + ((days_back - days_old + 1) * 10)  # Recency boost
                    )

                    video["viral_score"] = int(viral_score)
                    video["engagement_rate"] = round(engagement_rate, 2)
                    video["days_old"] = days_old

                    viral_videos.append(video)

            # Sort by viral score
            viral_videos.sort(key=lambda x: x["viral_score"], reverse=True)

            return {
                "viral_videos": viral_videos,
                "total_found": len(viral_videos),
                "criteria": {
                    "min_views": min_views,
                    "max_days_old": days_back,
                    "category_id": category_id,
                    "region_code": region_code,
                },
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to find viral content: {e}")

    async def _make_youtube_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make request to YouTube API and return JSON data"""
        if not self.session:
            raise APIError("Session not initialized")

        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 403:
                    error_data = await response.json()
                    error_reason = (
                        error_data.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "unknown")
                    )

                    if error_reason == "quotaExceeded":
                        raise APIError("YouTube API quota exceeded")
                    elif error_reason == "keyInvalid":
                        raise APIError("Invalid YouTube API key")
                    else:
                        raise APIError(f"YouTube API error: {error_reason}")

                if response.status != 200:
                    raise APIError(f"YouTube API returned status {response.status}")

                return await response.json()

        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to make YouTube request: {e}")

    def _parse_video_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse YouTube video data into standardized format"""
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        return {
            "video_id": item.get("id", ""),
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnails": snippet.get("thumbnails", {}),
            "category_id": snippet.get("categoryId", ""),
            "tags": snippet.get("tags", []),
            "duration": content_details.get("duration", ""),
            "view_count": statistics.get("viewCount", "0"),
            "like_count": statistics.get("likeCount", "0"),
            "comment_count": statistics.get("commentCount", "0"),
            "favorite_count": statistics.get("favoriteCount", "0"),
        }

    def _parse_channel_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse YouTube channel data into standardized format"""
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        branding = item.get("brandingSettings", {})

        return {
            "channel_id": item.get("id", ""),
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnails": snippet.get("thumbnails", {}),
            "country": snippet.get("country", ""),
            "subscriber_count": statistics.get("subscriberCount", "0"),
            "video_count": statistics.get("videoCount", "0"),
            "view_count": statistics.get("viewCount", "0"),
            "uploads_playlist_id": content_details.get("relatedPlaylists", {}).get(
                "uploads", ""
            ),
            "keywords": branding.get("channel", {}).get("keywords", ""),
            "banner_image": branding.get("image", {}).get("bannerExternalUrl", ""),
        }
