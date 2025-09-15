from __future__ import annotations
from typing import TypedDict

# Example TypedDicts to replace Dict[str, Any]
class LinkedInAuth(TypedDict, total=False):
    access_token: str
    refresh_token: str
    expires_at: int

class SharePayload(TypedDict, total=False):
    text: str
    link: str
    hashtags: list[str]

# Function signatures – replace deprecated/Any with precise types
def build_share_payload(text: str, link: str | None = None, hashtags: list[str] | None = None) -> SharePayload:
    payload: SharePayload = {"text": text}
    if link:
        payload["link"] = link
    if hashtags:
        payload["hashtags"] = hashtags
    return payload

def store_tokens(user_id: str, tokens: LinkedInAuth) -> None:
    ...