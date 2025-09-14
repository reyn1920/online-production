from __future__ import annotations
import os
from typing import Dict, Any
from ._base_social import BaseSocialClient

class RedditClient(BaseSocialClient):
    name = "reddit"

    @classmethod
    def from_env(cls) -> RedditClient:
        """Create RedditClient instance from environment variables"""
        return cls()

    def _check_ready(self) -> bool:
        need = ["REDDIT_CLIENT_ID","REDDIT_CLIENT_SECRET","REDDIT_USERNAME","REDDIT_PASSWORD","REDDIT_USER_AGENT"]
        return all(self.env.get(k) for k in need)

    def is_configured(self) -> bool:
        """Check if Reddit integration is configured"""
        return self.ready()

    async def submit_post(self, subreddit: str, title: str, text: str | None = None, url: str | None = None) -> Dict[str, Any]:
        """Submit a post to Reddit"""
        if not self.ready():
            return {"ok": False, "error": "Reddit not configured"}
        # TODO: PRAW or Reddit API call
        return {"ok": True, "provider": "reddit", "subreddit": subreddit, "title_len": len(title), "mode": "self" if text else "link"}

    def post(self, subreddit: str, title: str, text: str | None = None, url: str | None = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        if not self.ready():
            return {"ok": False, "reason": "reddit_not_configured"}
        # TODO: PRAW or Reddit API call
        return {"ok": True, "provider": "reddit", "subreddit": subreddit, "title_len": len(title), "mode": "self" if text else "link"}