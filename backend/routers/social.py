from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, Field

from backend.integrations.facebook_integration import FacebookClient
from backend.integrations.linkedin_integration import LinkedInClient
from backend.integrations.pinterest_integration import PinterestClient
from backend.integrations.reddit_integration import RedditClient

router = APIRouter(prefix="/api/social", tags=["social"])

# ----- Schemas -----
class FacebookPost(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    link: HttpUrl | None = None

class LinkedInPost(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    url: HttpUrl | None = None

class PinterestPost(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    link: HttpUrl | None = None
    image_path: str | None = None  # path to already-stored file

class RedditPost(BaseModel):
    subreddit: str = Field(..., min_length=2)
    title: str = Field(..., min_length=1, max_length=300)
    text: str | None = None
    url: HttpUrl | None = None

def _raise_if_not_ok(res: dict) -> dict:
    if not res.get("ok"):
        # 400 for not configured; adjust to 502 if upstream error
        raise HTTPException(status_code=400, detail=res.get("error", "Service not configured"))
    return res

# ----- Facebook Endpoints -----
@router.post("/facebook")
async def post_to_facebook(post: FacebookPost):
    client = FacebookClient.from_env()
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="Facebook not configured")
    
    result = await client.post_message(post.message, post.link)
    return _raise_if_not_ok(result)

# ----- LinkedIn Endpoints -----
@router.post("/linkedin")
async def post_to_linkedin(post: LinkedInPost):
    client = LinkedInClient.from_env()
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="LinkedIn not configured")
    
    result = await client.post_content(post.text, post.url)
    return _raise_if_not_ok(result)

# ----- Pinterest Endpoints -----
@router.post("/pinterest")
async def post_to_pinterest(post: PinterestPost):
    client = PinterestClient.from_env()
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="Pinterest not configured")
    
    result = await client.create_pin(post.title, post.link, post.image_path)
    return _raise_if_not_ok(result)

# ----- Reddit Endpoints -----
@router.post("/reddit")
async def post_to_reddit(post: RedditPost):
    client = RedditClient.from_env()
    if not client.is_configured():
        raise HTTPException(status_code=400, detail="Reddit not configured")
    
    result = await client.submit_post(post.subreddit, post.title, post.text, post.url)
    return _raise_if_not_ok(result)

# ----- Health Check -----
@router.get("/health")
async def social_health():
    """Check social integrations health."""
    return {
        "ok": True,
        "services": {
            "facebook": FacebookClient().is_configured(),
            "linkedin": LinkedInClient().is_configured(),
            "pinterest": PinterestClient().is_configured(),
            "reddit": RedditClient().is_configured()
        }
    }
