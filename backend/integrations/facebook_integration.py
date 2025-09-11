from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass


class FacebookClient:
    page_access_token: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None

    @classmethod


    def from_env(cls) -> "FacebookClient":
        return cls(
            page_access_token = os.getenv("FB_PAGE_ACCESS_TOKEN"),
                app_id = os.getenv("FB_APP_ID"),
                app_secret = os.getenv("FB_APP_SECRET"),
                )


    def ready(self) -> bool:
        # OFF by default: returns True only when creds exist
        return bool(self.page_access_token or (self.app_id and self.app_secret))

    # --- Stubs (no network calls yet) ---


        def post_message(self, message: str, media_url: str = "") -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("Facebook not configured")
        return {
            "ok": True,
                "id": "fb_post_stub",
                "message": message,
                "media": media_url,
                }


    def post_photo(self, caption: str, photo_url: str) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("Facebook not configured")
        return {
            "ok": True,
                "id": "fb_photo_stub",
                "caption": caption,
                "media": photo_url,
                }


    def insights(self) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("Facebook not configured")
        return {"ok": True, "followers": 0, "reach": 0, "impressions": 0}
