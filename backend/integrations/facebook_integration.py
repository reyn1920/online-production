from __future__ import annotations
import os
from typing import Dict, Any
from ._base_social import BaseSocialClient

class FacebookClient(BaseSocialClient):
    name = "facebook"

    @classmethod
    def from_env(cls) -> FacebookClient:
        """Create FacebookClient instance from environment variables"""
        return cls()

    def _check_ready(self) -> bool:
        # Minimum: Page token
        return bool(self.env.get("FACEBOOK_PAGE_ACCESS_TOKEN"))

    def is_configured(self) -> bool:
        """Check if Facebook integration is configured"""
        return self.ready()

    async def post_message(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Post a message to Facebook"""
        if not self.ready():
            return {"ok": False, "error": "Facebook not configured"}
        # TODO: Use Facebook Graph API with PAGE token
        # Placeholder for real call (intentionally not calling any API here).
        return {"ok": True, "provider": "facebook", "message_len": len(message), "link": link}

    def post(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        if not self.ready():
            return {"ok": False, "reason": "facebook_not_configured"}
        # TODO: Use Facebook Graph API with PAGE token
        # Placeholder for real call (intentionally not calling any API here).
        return {"ok": True, "provider": "facebook", "message_len": len(message), "link": link}