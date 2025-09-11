from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LinkedInClient:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LinkedInClient":
        return cls(
            client_id=os.getenv("LI_CLIENT_ID"),
            client_secret=os.getenv("LI_CLIENT_SECRET"),
            access_token=os.getenv("LI_ACCESS_TOKEN"),
        )

    def ready(self) -> bool:
        # OFF by default: returns True only when creds exist
        return bool(self.access_token or (self.client_id and self.client_secret))

    # --- Stubs (no network calls yet) ---
    def post_text(self, text: str, media_url: str = "") -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("LinkedIn not configured")
        return {"ok": True, "id": "li_post_stub", "text": text, "media": media_url}

    def post_article(
        self, title: str, content: str, media_url: str = ""
    ) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("LinkedIn not configured")
        return {
            "ok": True,
            "id": "li_article_stub",
            "title": title,
            "content": content,
            "media": media_url,
        }

    def insights(self) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("LinkedIn not configured")
        return {"ok": True, "followers": 0, "impressions": 0, "engagement": 0}
