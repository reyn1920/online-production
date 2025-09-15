from __future__ import annotations
import os
from typing import Dict, Any

class BaseSocialClient:
    """Base class for social media client integrations."""
    name: str = "base"

    def __init__(self, env: Dict[str, str] | None = None) -> None:
        """Initialize the social client with environment variables."""
        self.env = env or os.environ
        self._ready = self._check_ready()

    def _check_ready(self) -> bool:
        """Check if the client is ready for use. Override in subclasses."""
        return True

    def ready(self) -> bool:
        """Check if the client is ready for use."""
        return self._ready

    def post_message(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Post a message. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement post_message")

    def post(self, message: str, link: str | None = None) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.post_message(message, link)