from __future__ import annotations

import json
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

GRAPH = "https://graph.facebook.com / v21.0"  # bump if needed
ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
CONFIG.mkdir(parents = True, exist_ok = True)
TOKENS = (
    CONFIG / "instagram.tokens.json"
)  # use your encrypted store later if you prefer


def _load() -> dict:
    if TOKENS.exists():
        try:
            return json.loads(TOKENS.read_text())
        except Exception:
            pass
    return {}


def _save(d: dict) -> None:
    TOKENS.write_text(json.dumps(d, indent = 2))


def _http(method: str, url: str, **kw) -> Tuple[int, dict]:
    resp = requests.request(method, url, timeout = 60, **kw)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"raw": resp.text}

@dataclass


class InstagramClient:
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    scopes: str = (
        "pages_show_list,instagram_basic,instagram_content_publish,pages_read_engagement,business_management"
    )

    # hydrated at runtime
    user_access_token: Optional[str] = None  # long - lived user token
    page_id: Optional[str] = None
    page_access_token: Optional[str] = None
    ig_user_id: Optional[str] = None

    @classmethod


    def from_env(cls) -> "InstagramClient":
        data = _load()
        return cls(
            app_id = os.getenv("FB_APP_ID"),
                app_secret = os.getenv("FB_APP_SECRET"),
                redirect_uri = os.getenv(
                "FB_REDIRECT_URI"
            ),  # e.g. https://your.host / social / oauth / instagram / callback
            scopes = os.getenv("FB_APP_SCOPES", cls.scopes),
                user_access_token = data.get("user_access_token"),
                page_id = data.get("page_id"),
                page_access_token = data.get("page_access_token"),
                ig_user_id = data.get("ig_user_id"),
                )


    def ready(self) -> bool:
        return bool(self.page_access_token and self.ig_user_id)

    # ---------- OAUTH FLOW ----------


        def get_auth_url(self, state: str) -> str:
        if not self.app_id or not self.redirect_uri:
            raise RuntimeError("FB_APP_ID / FB_REDIRECT_URI not set")
        params = {
            "client_id": self.app_id,
                "redirect_uri": self.redirect_uri,
                "scope": self.scopes,
                "response_type": "code",
                "state": state,
                }
        q = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
        return f"https://www.facebook.com / v21.0 / dialog / oauth?{q}"


    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        # 1) short - lived user token
        url = f"{GRAPH}/oauth / access_token"
        params = dict(
            client_id = self.app_id,
                client_secret = self.app_secret,
                redirect_uri = self.redirect_uri,
                code = code,
                )
        sc, j = _http("GET", url, params = params)
        if sc != 200:
            return {"ok": False, "step": "short_token", "status": sc, "error": j}

        short = j.get("access_token")

        # 2) long - lived user token
        url = f"{GRAPH}/oauth / access_token"
        params = dict(
            grant_type="fb_exchange_token",
                client_id = self.app_id,
                client_secret = self.app_secret,
                fb_exchange_token = short,
                )
        sc, j = _http("GET", url, params = params)
        if sc != 200:
            return {"ok": False, "step": "long_token", "status": sc, "error": j}

        user_ll = j.get("access_token")

        # 3) page list -> choose first (you can store mapping in UI later)
        sc, j = _http("GET", f"{GRAPH}/me / accounts", params={"access_token": user_ll})
        if sc != 200 or not j.get("data"):
            return {"ok": False, "step": "pages", "status": sc, "error": j}

        page = j["data"][0]
        page_id = page.get("id")
        page_token = page.get("access_token")

        # 4) get IG business account id from page
        sc, j = _http(
            "GET",
                f"{GRAPH}/{page_id}",
                params={"fields": "instagram_business_account", "access_token": page_token},
                )
        ig_user_id = (j.get("instagram_business_account") or {}).get("id")

        if not ig_user_id:
            return {"ok": False, "step": "ig_user", "status": sc, "error": j}

        _save(
            {
                "saved_at": int(time.time()),
                    "user_access_token": user_ll,
                    "page_id": page_id,
                    "page_access_token": page_token,
                    "ig_user_id": ig_user_id,
                    }
        )
        self.user_access_token = user_ll
        self.page_id = page_id
        self.page_access_token = page_token
        self.ig_user_id = ig_user_id
        return {"ok": True, "page_id": page_id, "ig_user_id": ig_user_id}

    # ---------- POSTING ----------


        def _publish_creation(self, creation_id: str) -> Dict[str, Any]:
        sc, j = _http(
            "POST",
                f"{GRAPH}/{self.ig_user_id}/media_publish",
                data={"creation_id": creation_id, "access_token": self.page_access_token},
                )
        return {"status": sc, **j}


    def post_image(self, caption: str, image_url: str) -> Dict[str, Any]:
        if not self.ready():
            return {"ok": False, "reason": "Not configured"}
        data = {
            "caption": caption or "",
                "image_url": image_url,
                "access_token": self.page_access_token,
                }
        sc, j = _http("POST", f"{GRAPH}/{self.ig_user_id}/media", data = data)
        if sc != 200 or "id" not in j:
            return {"ok": False, "step": "create_media", "status": sc, "error": j}
        publish = self._publish_creation(j["id"])
        return {"ok": publish.get("status") == 200, "creation": j, "publish": publish}


    def post_reel(
        self, caption: str, video_url: str, share_to_feed: bool = True
    ) -> Dict[str, Any]:
        if not self.ready():
            return {"ok": False, "reason": "Not configured"}
        data = {
            "caption": caption or "",
                "media_type": "REELS",
                "video_url": video_url,
                "share_to_feed": str(share_to_feed).lower(),
                "access_token": self.page_access_token,
                }
        sc, j = _http("POST", f"{GRAPH}/{self.ig_user_id}/media", data = data)
        if sc != 200 or "id" not in j:
            return {"ok": False, "step": "create_reel", "status": sc, "error": j}
        # (optional) poll status via /{creation_id}?fields = status_code
        publish = self._publish_creation(j["id"])
        return {"ok": publish.get("status") == 200, "creation": j, "publish": publish}

    # ---------- INSIGHTS ----------


        def insights(self) -> Dict[str, Any]:
        if not self.ready():
            return {"ok": False, "reason": "Not configured"}
        params = {
            "metric": "impressions,reach,profile_views,follower_count",
                "period": "day",
                "access_token": self.page_access_token,
                }
        sc, j = _http("GET", f"{GRAPH}/{self.ig_user_id}/insights", params = params)
        return {"ok": sc == 200, "status": sc, "data": j}