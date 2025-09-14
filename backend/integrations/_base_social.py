from __future__ import annotations
import os
from typing import Dict, Any

class BaseSocialClient:
    name: str = "base"

    def __init__(self, env: Dict[str, str] | None = None) -> None:
        self.env = env or os.environ
        self._ready = self._check_ready()

    def _check_ready(self) -> bool:
        """Override in subclasses: return True only if required env vars exist."""
        return False

    def ready(self) -> bool:
        return self._ready

    def post(self, **kwargs: Any) -> Dict[str, Any]:
        if not self.ready():
            return {"ok": False, "reason": f"{self.name}_not_configured"}
        raise NotImplementedError("Implement provider post()")