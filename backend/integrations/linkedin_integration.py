from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict
from ._base_social import BaseSocialClient

@dataclass
class LinkedInClient(BaseSocialClient):
    """LinkedIn integration client for social media posting."""
    name = "linkedin"
    client_id: str | None = None
    client_secret: str | None = None
    access_token: str | None = None

    @classmethod
    def from_env(cls) -> "LinkedInClient":
        """Create LinkedInClient instance from environment variables."""
        return cls(
            client_id=os.getenv("LI_CLIENT_ID"),
            client_secret=os.getenv("LI_CLIENT_SECRET"),
            access_token=os.getenv("LI_ACCESS_TOKEN"),
        )

    def _check_ready(self) -> bool:
        """Check if LinkedIn client is ready for use."""
        return bool(self.client_id and self.client_secret and self.access_token)

    def ready(self) -> bool:
        """Check if LinkedIn client is ready for use."""
        return self._check_ready()

    def post_message(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Post a message to LinkedIn."""
        if not self.ready():
            return {"ok": False, "reason": "linkedin_not_configured"}
        
        # TODO: Use LinkedIn API to post message
        # Placeholder for real call (intentionally not calling any API here).
        return {"ok": True, "provider": "linkedin", "message_len": len(message), "link": link}

    def post(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.post_message(message, link)