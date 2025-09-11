import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.integrations.facebook_integration import FacebookClient
# Import platform clients for insights
from backend.integrations.instagram_integration import InstagramClient
from backend.integrations.linkedin_integration import LinkedInClient
from backend.integrations.pinterest_integration import PinterestClient
from backend.integrations.reddit_integration import RedditClient
from backend.integrations.tiktok_integration import TikTokClient

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Pydantic models


class DateRange(BaseModel):
    start_date: str  # ISO format
    end_date: str  # ISO format


class PlatformMetrics(BaseModel):
    platform: str
    followers: int
    impressions: int
    engagement: int
    reach: Optional[int] = 0
    posts: Optional[int] = 0
    last_updated: str


class UnifiedMetrics(BaseModel):
    total_followers: int
    total_impressions: int
    total_engagement: int
    total_reach: int
    total_posts: int
    platforms_active: int
    platforms_configured: int
    last_updated: str

# Platform clients
clients = {
    "instagram": InstagramClient.from_env(),
        "tiktok": TikTokClient.from_env(),
        "facebook": FacebookClient.from_env(),
        "linkedin": LinkedInClient.from_env(),
        "pinterest": PinterestClient.from_env(),
        "reddit": RedditClient.from_env(),
}

# Simple file - based cache for analytics data
ANALYTICS_CACHE_FILE = "analytics_cache.json"
CACHE_DURATION = 300  # 5 minutes


def load_analytics_cache() -> Dict[str, Any]:
    """Load cached analytics data"""
    if os.path.exists(ANALYTICS_CACHE_FILE):
        with open(ANALYTICS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_analytics_cache(data: Dict[str, Any]):
    """Save analytics data to cache"""
    data["cached_at"] = datetime.now().isoformat()
    with open(ANALYTICS_CACHE_FILE, "w") as f:
        json.dump(data, f, indent = 2)


def is_cache_valid(cached_at: str) -> bool:
    """Check if cache is still valid"""
    try:
        cache_time = datetime.fromisoformat(cached_at)
        return datetime.now() - cache_time < timedelta(seconds = CACHE_DURATION)
    except Exception:
        return False

@router.get("/overview")


async def get_analytics_overview():
    """Get unified analytics overview from all platforms"""
    # Check cache first
    cache = load_analytics_cache()
    if cache.get("cached_at") and is_cache_valid(cache["cached_at"]):
        return cache.get("overview", {})

    platform_metrics = []
    total_followers = 0
    total_impressions = 0
    total_engagement = 0
    total_reach = 0
    total_posts = 0
    platforms_active = 0
    platforms_configured = 0

    for platform, client in clients.items():
        if client.ready():
            platforms_configured += 1
            try:
                insights = client.insights()
                if insights.get("ok", True):  # Assume success if 'ok' not present
                    platforms_active += 1

                    # Extract metrics with fallbacks
                    followers = insights.get("followers", 0)
                    impressions = insights.get("impressions", 0)
                    engagement = insights.get(
                        "engagement", insights.get("saves", insights.get("karma", 0))
                    )
                    reach = insights.get(
                        "reach", impressions
                    )  # Use impressions as fallback
                    posts = insights.get("posts", insights.get("pins", 0))

                    # Add to totals
                    total_followers += followers
                    total_impressions += impressions
                    total_engagement += engagement
                    total_reach += reach
                    total_posts += posts

                    platform_metrics.append(
                        PlatformMetrics(
                            platform = platform,
                                followers = followers,
                                impressions = impressions,
                                engagement = engagement,
                                reach = reach,
                                posts = posts,
                                last_updated = datetime.now().isoformat(),
                                ).dict()
                    )
                else:
                    platform_metrics.append(
                        {
                            "platform": platform,
                                "error": insights.get("error", "Unknown error"),
                                "last_updated": datetime.now().isoformat(),
                                }
                    )
            except Exception as e:
                platform_metrics.append(
                    {
                        "platform": platform,
                            "error": str(e),
                            "last_updated": datetime.now().isoformat(),
                            }
                )

    # Create unified metrics
    unified = UnifiedMetrics(
        total_followers = total_followers,
            total_impressions = total_impressions,
            total_engagement = total_engagement,
            total_reach = total_reach,
            total_posts = total_posts,
            platforms_active = platforms_active,
            platforms_configured = platforms_configured,
            last_updated = datetime.now().isoformat(),
            )

    overview = {
        "unified_metrics": unified.dict(),
            "platform_metrics": platform_metrics,
            "engagement_rate": round((total_engagement / max(total_followers, 1)) * 100, 2),
            "reach_rate": round((total_reach / max(total_impressions, 1)) * 100, 2),
            }

    # Cache the results
    cache_data = {"overview": overview}
    save_analytics_cache(cache_data)

    return overview

@router.get("/platform/{platform}")


async def get_platform_analytics(platform: str):
    """Get detailed analytics for a specific platform"""
    platform = platform.lower()

    if platform not in clients:
        raise HTTPException(status_code = 400, detail = f"Unsupported platform: {platform}")

    client = clients[platform]
    if not client.ready():
        raise HTTPException(status_code = 400, detail = f"{platform} not configured")

    try:
        insights = client.insights()

        # Add platform - specific calculations
        if platform == "instagram":
            # Instagram - specific metrics
            insights["engagement_rate"] = round(
                (insights.get("engagement", 0) / max(insights.get("followers", 1), 1))
                * 100,
                    2,
                    )
            insights["story_views"] = insights.get("story_views", 0)
        elif platform == "tiktok":
            # TikTok - specific metrics
            insights["video_views"] = insights.get("video_views", 0)
            insights["shares"] = insights.get("shares", 0)
        elif platform == "facebook":
            # Facebook - specific metrics
            insights["page_likes"] = insights.get(
                "page_likes", insights.get("followers", 0)
            )
            insights["post_reach"] = insights.get(
                "post_reach", insights.get("reach", 0)
            )
        elif platform == "linkedin":
            # LinkedIn - specific metrics
            insights["connections"] = insights.get(
                "connections", insights.get("followers", 0)
            )
            insights["profile_views"] = insights.get("profile_views", 0)
        elif platform == "pinterest":
            # Pinterest - specific metrics
            insights["monthly_views"] = insights.get(
                "monthly_views", insights.get("impressions", 0)
            )
            insights["pin_clicks"] = insights.get(
                "pin_clicks", insights.get("engagement", 0)
            )
        elif platform == "reddit":
            # Reddit - specific metrics
            insights["comment_karma"] = insights.get("comment_karma", 0)
            insights["post_karma"] = insights.get(
                "post_karma", insights.get("karma", 0)
            )

        return {
            "platform": platform,
                "insights": insights,
                "last_updated": datetime.now().isoformat(),
                }

    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))

@router.get("/comparison")


async def get_platform_comparison():
    """Get side - by - side comparison of all platforms"""
    comparison = {}

    for platform, client in clients.items():
        if client.ready():
            try:
                insights = client.insights()
                if insights.get("ok", True):
                    comparison[platform] = {
                        "followers": insights.get("followers", 0),
                            "impressions": insights.get("impressions", 0),
                            "engagement": insights.get(
                            "engagement",
                                insights.get("saves", insights.get("karma", 0)),
                                ),
                            "engagement_rate": round(
                            (
                                insights.get("engagement", 0)
                                / max(insights.get("followers", 1), 1)
                            )
                            * 100,
                                2,
                                ),
                            "status": "active",
                            }
                else:
                    comparison[platform] = {
                        "status": "error",
                            "error": insights.get("error", "Unknown error"),
                            }
            except Exception as e:
                comparison[platform] = {"status": "error", "error": str(e)}
        else:
            comparison[platform] = {"status": "not_configured"}

    return {"comparison": comparison, "last_updated": datetime.now().isoformat()}

@router.get("/trends")


async def get_trends_analysis():
    """Get trends analysis (mock data for now)"""
    # TODO: Implement actual trends analysis with historical data
    return {
        "trends": {
            "follower_growth": {
                "instagram": {"7d": "+5.2%", "30d": "+18.7%"},
                    "tiktok": {"7d": "+12.1%", "30d": "+45.3%"},
                    "facebook": {"7d": "+2.1%", "30d": "+8.9%"},
                    "linkedin": {"7d": "+3.4%", "30d": "+12.6%"},
                    "pinterest": {"7d": "+1.8%", "30d": "+7.2%"},
                    "reddit": {"7d": "+0.9%", "30d": "+4.1%"},
                    },
                "engagement_trends": {
                "best_performing_platform": "tiktok",
                    "highest_engagement_rate": "instagram",
                    "fastest_growing": "tiktok",
                    },
                "content_performance": {
                "top_content_type": "video",
                    "best_posting_time": "18:00 - 20:00",
                    "optimal_frequency": "2 - 3 posts / day",
                    },
                },
            "recommendations": [
            "Focus more content on TikTok for growth",
                "Maintain Instagram engagement with stories",
                "Cross - post successful content to Facebook",
                "Use LinkedIn for professional content",
                ],
            "last_updated": datetime.now().isoformat(),
            }

@router.post("/refresh")


async def refresh_analytics_cache():
    """Force refresh of analytics cache"""
    # Clear cache
    if os.path.exists(ANALYTICS_CACHE_FILE):
        os.remove(ANALYTICS_CACHE_FILE)

    # Get fresh data
    overview = await get_analytics_overview()

    return {
        "message": "Analytics cache refreshed",
            "timestamp": datetime.now().isoformat(),
            "overview": overview,
            }

@router.get("/health")


async def analytics_health():
    """Health check for analytics service"""
    return {
        "status": "healthy",
            "platforms_available": len(clients),
            "platforms_configured": sum(1 for client in clients.values() if client.ready()),
            "cache_exists": os.path.exists(ANALYTICS_CACHE_FILE),
            "timestamp": datetime.now().isoformat(),
            }
