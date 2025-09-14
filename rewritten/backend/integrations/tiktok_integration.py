import json
import os
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
# Content Posting API (Direct Post)
TIKTOK_DIRECT_POST_INIT = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_STATUS_FETCH = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def _now() -> int:
    return int(time.time())


@dataclass
class TikTokTokens:
    access_token: str
    refresh_token: Optional[str]
    expires_at: int  # epoch seconds
    open_id: Optional[str] = None
    scope: Optional[str] = None


class TikTokClient:
    """
    Official TikTok Open API v2 (Developers) client.
    Supports OAuth (authorization_code & refresh) and Content Posting API:
      - Direct Post (PULL_FROM_URL) -> publish_id
      - Status polling
    """

    def __init__(
        self,
        client_key: str,
        client_secret: str,
        redirect_uri: str,
        token_path: str,
        scopes=("video.upload", "video.publish"),
        enabled: bool = False,
        session: Optional[requests.Session] = None,
    ):
        self.client_key = client_key or ""
        self.client_secret = client_secret or ""
        self.redirect_uri = redirect_uri or ""
        self.token_path = token_path or "./config/tiktok.tokens.json"
        self.scopes = list(scopes) if scopes else []
        self.enabled = bool(enabled)
        self.http = session or requests.Session()
        self._tokens: Optional[TikTokTokens] = None
        self._load_tokens()

    @classmethod
    def from_env(cls) -> "TikTokClient":
        enabled = os.getenv("TIKTOK_ENABLED", "false").lower() == "true"
        scopes = [
            s.strip()
            for s in os.getenv("TIKTOK_SCOPES", "video.upload,video.publish").split(",")
            if s.strip()
        ]
        return cls(
            client_key=os.getenv("TIKTOK_CLIENT_KEY", ""),
            client_secret=os.getenv("TIKTOK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("TIKTOK_REDIRECT_URI", ""),
            token_path=os.getenv("TIKTOK_TOKEN_FILE", "./config/tiktok.tokens.json"),
            scopes=scopes,
            enabled=enabled,
        )

    # ---------- status/light helpers ----------

    def status_light(self) -> Tuple[str, Dict]:
        """
        Returns ("green" | "purple" | "red", meta)
        - purple: missing keys/disabled
        - red: enabled but not authenticated/token invalid
        - green: authenticated & ready
        """
        meta = {"enabled": self.enabled}
        if not self.enabled:
            return ("purple", {**meta, "reason": "disabled"})
        if not self.client_key or not self.client_secret or not self.redirect_uri:
            return ("purple", {**meta, "reason": "missing_keys"})
        if not self._tokens or not self._tokens.access_token or self._expired():
            return ("red", {**meta, "reason": "auth_required"})
        return (
            "green",
            {**meta, "open_id": self._tokens.open_id, "scopes": self._tokens.scope},
        )

    def ready(self) -> bool:
        color, _ = self.status_light()
        return color == "green"

    # ---------- token storage ----------

    def _load_tokens(self):
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, "r") as f:
                    data = json.load(f)
                self._tokens = TikTokTokens(
                    access_token=data.get("access_token", ""),
                    refresh_token=data.get("refresh_token"),
                    expires_at=int(data.get("expires_at", 0)),
                    open_id=data.get("open_id"),
                    scope=data.get("scope"),
                )
        except Exception:
            self._tokens = None

    def _save_tokens(self, tokens: TikTokTokens):
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, "w") as f:
            json.dump(
                {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                    "expires_at": tokens.expires_at,
                    "open_id": tokens.open_id,
                    "scope": tokens.scope,
                },
                f,
                indent=2,
            )
        self._tokens = tokens

    def _expired(self) -> bool:
        return not self._tokens or _now() >= max(0, self._tokens.expires_at - 60)

    # ---------- OAuth ----------

    def authorize_url(self, state: str) -> str:
        scope_str = " ".join(self.scopes)  # space - delimited per TikTok docs
        q = {
            "client_key": self.client_key,
            "response_type": "code",
            "scope": scope_str,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        return f"{TIKTOK_AUTH_URL}?{urllib.parse.urlencode(q)}"

    def exchange_code(self, code: str) -> TikTokTokens:
        """
        Exchange authorization code for tokens.
        Docs: open.tiktokapis.com/v2/oauth/token/(grant_type = authorization_code)
        """
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        r = self.http.post(TIKTOK_TOKEN_URL, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json().get("data") or {}
        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token")
        expires_in = int(data.get("expires_in", 0))
        open_id = data.get("open_id")
        scope = data.get("scope")
        tokens = TikTokTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=_now() + expires_in,
            open_id=open_id,
            scope=scope,
        )
        self._save_tokens(tokens)
        return tokens

    def refresh(self) -> TikTokTokens:
        if not self._tokens or not self._tokens.refresh_token:
            raise RuntimeError("No refresh_token available.")
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self._tokens.refresh_token,
        }
        r = self.http.post(TIKTOK_TOKEN_URL, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json().get("data") or {}
        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", self._tokens.refresh_token)
        expires_in = int(data.get("expires_in", 0))
        open_id = data.get("open_id", self._tokens.open_id)
        scope = data.get("scope", self._tokens.scope)
        tokens = TikTokTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=_now() + expires_in,
            open_id=open_id,
            scope=scope,
        )
        self._save_tokens(tokens)
        return tokens

    def _auth_headers(self) -> Dict[str, str]:
        if self._expired() and self._tokens and self._tokens.refresh_token:
            try:
                self.refresh()
            except Exception as e:
                # Log the refresh failure but continue with existing token
                print(f"Warning: Failed to refresh TikTok token: {e}")
        if not self._tokens or not self._tokens.access_token:
            raise RuntimeError("TikTok not authenticated.")
        return {"Authorization": f"Bearer {self._tokens.access_token}"}

    # ---------- Content Posting (Direct Post) ----------

    def direct_post_from_url(self, video_url: str, caption: str) -> Dict:
        """
        Direct Post (PULL_FROM_URL).
        Requires scopes: video.upload + video.publish.
        Returns {publish_id, status_hint}
        """
        headers = {
            **self._auth_headers(),
            "Content - Type": "application/json; charset = UTF - 8",
        }
        payload = {
            "source_info": {"source": "PULL_FROM_URL", "video_url": video_url},
            "post_info": {"title": caption},
        }
        r = self.http.post(TIKTOK_DIRECT_POST_INIT, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        j = r.json()
        err = (j.get("error") or {}).get("code")
        if err not in (None, "", "ok"):
            raise RuntimeError(f"TikTok init error: {j}")
        publish_id = (j.get("data") or {}).get("publish_id")
        return {
            "publish_id": publish_id,
            "hint": "use/tiktok/status?publish_id=... to poll",
        }

    def fetch_status(self, publish_id: str) -> Dict:
        headers = {
            **self._auth_headers(),
            "Content - Type": "application/json; charset = UTF - 8",
        }
        r = self.http.post(
            TIKTOK_STATUS_FETCH,
            headers=headers,
            json={"publish_id": publish_id},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    # Stub methods for compatibility with social router

    def post_video(self, caption: str, video_url: str) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("TikTok not configured")
        return self.direct_post_from_url(video_url, caption)

    def insights(self) -> Dict[str, Any]:
        if not self.ready():
            raise RuntimeError("TikTok not configured")
        return {"ok": True, "followers": 0, "views": 0, "engagement": 0}
