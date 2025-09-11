import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.integrations.facebook_integration import FacebookClient
# Import all platform clients
from backend.integrations.instagram_integration import InstagramClient
from backend.integrations.linkedin_integration import LinkedInClient
from backend.integrations.pinterest_integration import PinterestClient
from backend.integrations.reddit_integration import RedditClient
from backend.integrations.tiktok_integration import TikTokClient

router = APIRouter(prefix="/social", tags=["social"])


# Pydantic models
class PostRequest(BaseModel):
    platform: str
    content: str
    media_url: Optional[str] = ""
    extra: Optional[Dict[str, Any]] = {}


class ScheduleRequest(BaseModel):
    platform: str
    content: str
    media_url: Optional[str] = ""
    scheduled_time: str  # ISO format
    extra: Optional[Dict[str, Any]] = {}


# Simple file-backed queue for scheduling
SCHEDULE_FILE = "scheduled_posts.json"


def load_schedule() -> List[Dict[str, Any]]:
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return []


def save_schedule(schedule: List[Dict[str, Any]]):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)


# Platform clients
clients = {
    "instagram": InstagramClient.from_env(),
    "tiktok": TikTokClient.from_env(),
    "facebook": FacebookClient.from_env(),
    "linkedin": LinkedInClient.from_env(),
    "pinterest": PinterestClient.from_env(),
    "reddit": RedditClient.from_env(),
}


@router.get("/status")
async def get_provider_status():
    """Provider status lights - shows which platforms are configured and ready"""
    status = {}
    for platform, client in clients.items():
        status[platform] = {
            "ready": client.ready(),
            "status": "🟢 Ready" if client.ready() else "🔴 Not Configured",
        }
    return status


@router.post("/post")
async def post_content(request: PostRequest):
    """Post content to a specific platform"""
    platform = request.platform.lower()

    if platform not in clients:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    client = clients[platform]
    if not client.ready():
        raise HTTPException(status_code=400, detail=f"{platform} not configured")

    try:
        # Route to appropriate platform method
        if platform == "instagram":
            if request.media_url:
                result = client.post_image(request.content, request.media_url)
            else:
                result = {"ok": False, "error": "Instagram requires media_url"}
        elif platform == "tiktok":
            if request.media_url:
                result = client.direct_post(request.media_url, request.content)
            else:
                result = {"ok": False, "error": "TikTok requires media_url"}
        elif platform == "facebook":
            result = client.post_message(request.content, request.media_url)
        elif platform == "linkedin":
            result = client.post_text(request.content, request.media_url)
        elif platform == "pinterest":
            if request.media_url:
                result = client.create_pin(
                    request.content,
                    request.media_url,
                    request.extra.get("board_id", ""),
                )
            else:
                result = {"ok": False, "error": "Pinterest requires media_url"}
        elif platform == "reddit":
            subreddit = request.extra.get("subreddit", "test")
            result = client.submit_post(
                subreddit, request.content[:300], request.content, request.media_url
            )

        return {"platform": platform, "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_post(request: ScheduleRequest):
    """Schedule a post for later"""
    platform = request.platform.lower()

    if platform not in clients:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    # Add to schedule queue
    schedule = load_schedule()
    scheduled_post = {
        "id": f"{platform}_{len(schedule)}_{datetime.now().timestamp()}",
        "platform": platform,
        "content": request.content,
        "media_url": request.media_url,
        "scheduled_time": request.scheduled_time,
        "extra": request.extra,
        "status": "scheduled",
        "created_at": datetime.now().isoformat(),
    }

    schedule.append(scheduled_post)
    save_schedule(schedule)

    return {"message": "Post scheduled successfully", "id": scheduled_post["id"]}


@router.get("/schedule")
async def get_scheduled_posts():
    """Get all scheduled posts"""
    return load_schedule()


@router.get("/insights/{platform}")
async def get_platform_insights(platform: str):
    """Get insights for a specific platform"""
    platform = platform.lower()

    if platform not in clients:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    client = clients[platform]
    if not client.ready():
        raise HTTPException(status_code=400, detail=f"{platform} not configured")

    try:
        insights = client.insights()
        return {"platform": platform, "insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_all_insights():
    """Get insights from all configured platforms"""
    all_insights = {}

    for platform, client in clients.items():
        if client.ready():
            try:
                all_insights[platform] = client.insights()
            except Exception as e:
                all_insights[platform] = {"error": str(e)}
        else:
            all_insights[platform] = {"error": "Not configured"}

    return all_insights
