# app / routers / oauth.py

import logging
import os
import secrets
import time
import urllib.parse
from typing import Dict, Optional

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# In - memory storage for OAuth states (use Redis in production)
OAUTH_STATES = {}


def _get_base_url(request: Request) -> str:
    """Get the base URL for OAuth callbacks."""
    return f"{request.url.scheme}://{request.url.netloc}"


def _cleanup_expired_states():
    """Remove expired OAuth states (older than 10 minutes)."""
    current_time = time.time()
    expired_keys = [
        k
        for k, v in OAUTH_STATES.items()
        if current_time - v.get("created_at", 0) > 600
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     ]
    for key in expired_keys:
        del OAUTH_STATES[key]

@router.get("/tiktok / start")


async def tiktok_oauth_start(request: Request, redirect_uri: Optional[str] = None):
    """Start TikTok OAuth flow."""
    # Check if TikTok OAuth is enabled
    client_id = os.getenv("TIKTOK_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code = 503, detail="TikTok OAuth not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with metadata
    _cleanup_expired_states()
    OAUTH_STATES[state] = {
        "provider": "tiktok",
            "created_at": time.time(),
            "redirect_uri": redirect_uri or f"{_get_base_url(request)}/oauth / success",
# BRACKET_SURGEON: disabled
#             }

    # Build TikTok OAuth URL
    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth / tiktok / callback"

    params = {
        "client_key": client_id,
            "scope": "user.info.basic,video.list",  # Basic scopes
        "response_type": "code",
            "redirect_uri": callback_url,
            "state": state,
# BRACKET_SURGEON: disabled
#             }

    auth_url = "https://www.tiktok.com / auth / authorize/?" + urllib.parse.urlencode(
        params
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    logger.info(f"Starting TikTok OAuth flow with state: {state}")
    return RedirectResponse(url = auth_url)

@router.get("/tiktok / callback")


async def tiktok_oauth_callback(
    request: Request,
        code: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        error_description: Optional[str] = Query(None),
# BRACKET_SURGEON: disabled
# ):
    """Handle TikTok OAuth callback."""
    if error:
        logger.error(f"TikTok OAuth error: {error} - {error_description}")
        raise HTTPException(status_code = 400, detail = f"OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code = 400, detail="Missing code or state parameter")

    # Verify state
    if state not in OAUTH_STATES:
        raise HTTPException(status_code = 400, detail="Invalid or expired state")

    state_data = OAUTH_STATES.pop(state)  # Remove used state

    # Exchange code for access token
    client_id = os.getenv("TIKTOK_CLIENT_ID")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code = 503, detail="TikTok OAuth credentials not configured"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth / tiktok / callback"

    token_data = {
        "client_key": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": callback_url,
# BRACKET_SURGEON: disabled
#             }

    try:
        token_response = requests.post(
            "https://open - api.tiktok.com / oauth / access_token/",
                json = token_data,
                timeout = 30,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        if token_response.status_code == 200:
            token_info = token_response.json()

            if token_info.get("data"):
                access_token = token_info["data"].get("access_token")
                refresh_token = token_info["data"].get("refresh_token")
                expires_in = token_info["data"].get("expires_in")

                # TODO: Store tokens securely (database, encrypted storage)
                logger.info(
                    f"TikTok OAuth successful for user: {"
                        token_info['data'].get('open_id')}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                # Report success to integrations registry
                try:
                    requests.post(
                        "http://localhost:8000 / integrations / report",
                            json={
                            "key": "tiktok",
                                "success": True,
                                "took_ms": 0,
                                "quota_remaining": None,
# BRACKET_SURGEON: disabled
#                                 },
                            timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                except Exception as e:
                    logger.warning(f"Failed to report TikTok OAuth success: {e}")

                # Redirect to success page or original redirect URI
                redirect_uri = state_data.get(
                    "redirect_uri", f"{base_url}/oauth / success"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                return RedirectResponse(
                    url = f"{redirect_uri}?provider = tiktok&status = success"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                logger.error(f"TikTok token response missing data: {token_info}")
                raise HTTPException(status_code = 400, detail="Invalid token response")
        else:
            logger.error(
                f"TikTok token request failed: {token_response.status_code} - {token_response.text}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            raise HTTPException(
                status_code = 400, detail="Failed to exchange code for token"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    except requests.RequestException as e:
        logger.error(f"TikTok token request error: {e}")
        raise HTTPException(status_code = 500, detail="OAuth token exchange failed")

@router.get("/instagram / start")


async def instagram_oauth_start(request: Request, redirect_uri: Optional[str] = None):
    """Start Instagram OAuth flow."""
    # Check if Instagram OAuth is enabled
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code = 503, detail="Instagram OAuth not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with metadata
    _cleanup_expired_states()
    OAUTH_STATES[state] = {
        "provider": "instagram",
            "created_at": time.time(),
            "redirect_uri": redirect_uri or f"{_get_base_url(request)}/oauth / success",
# BRACKET_SURGEON: disabled
#             }

    # Build Instagram OAuth URL
    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth / instagram / callback"

    params = {
        "client_id": client_id,
            "redirect_uri": callback_url,
            "scope": "user_profile,user_media",  # Basic scopes
        "response_type": "code",
            "state": state,
# BRACKET_SURGEON: disabled
#             }

    auth_url = "https://api.instagram.com / oauth / authorize?" + urllib.parse.urlencode(
        params
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    logger.info(f"Starting Instagram OAuth flow with state: {state}")
    return RedirectResponse(url = auth_url)

@router.get("/instagram / callback")


async def instagram_oauth_callback(
    request: Request,
        code: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        error_description: Optional[str] = Query(None),
# BRACKET_SURGEON: disabled
# ):
    """Handle Instagram OAuth callback."""
    if error:
        logger.error(f"Instagram OAuth error: {error} - {error_description}")
        raise HTTPException(status_code = 400, detail = f"OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code = 400, detail="Missing code or state parameter")

    # Verify state
    if state not in OAUTH_STATES:
        raise HTTPException(status_code = 400, detail="Invalid or expired state")

    state_data = OAUTH_STATES.pop(state)  # Remove used state

    # Exchange code for access token
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code = 503, detail="Instagram OAuth credentials not configured"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth / instagram / callback"

    token_data = {
        "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": callback_url,
            "code": code,
# BRACKET_SURGEON: disabled
#             }

    try:
        token_response = requests.post(
            "https://api.instagram.com / oauth / access_token", data = token_data, timeout = 30
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if token_response.status_code == 200:
            token_info = token_response.json()

            access_token = token_info.get("access_token")
            user_id = token_info.get("user_id")

            if access_token and user_id:
                # TODO: Store tokens securely (database, encrypted storage)
                logger.info(f"Instagram OAuth successful for user: {user_id}")

                # Report success to integrations registry
                try:
                    requests.post(
                        "http://localhost:8000 / integrations / report",
                            json={
                            "key": "instagram",
                                "success": True,
                                "took_ms": 0,
                                "quota_remaining": None,
# BRACKET_SURGEON: disabled
#                                 },
                            timeout = 10,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                except Exception as e:
                    logger.warning(f"Failed to report Instagram OAuth success: {e}")

                # Redirect to success page or original redirect URI
                redirect_uri = state_data.get(
                    "redirect_uri", f"{base_url}/oauth / success"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                return RedirectResponse(
                    url = f"{redirect_uri}?provider = instagram&status = success"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                logger.error(
                    f"Instagram token response missing required fields: {token_info}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                raise HTTPException(status_code = 400, detail="Invalid token response")
        else:
            logger.error(
                f"Instagram token request failed: {token_response.status_code} - {token_response.text}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            raise HTTPException(
                status_code = 400, detail="Failed to exchange code for token"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    except requests.RequestException as e:
        logger.error(f"Instagram token request error: {e}")
        raise HTTPException(status_code = 500, detail="OAuth token exchange failed")

@router.get("/success")


async def oauth_success(
    provider: Optional[str] = Query(None), status: Optional[str] = Query(None)
# BRACKET_SURGEON: disabled
# ):
    """OAuth success page."""
    return {
        "message": "OAuth flow completed",
            "provider": provider,
            "status": status,
            "timestamp": time.time(),
# BRACKET_SURGEON: disabled
#             }

@router.get("/status")


async def oauth_status():
    """Get OAuth configuration status."""
    status = {
        "tiktok": {
            "configured": bool(
                os.getenv("TIKTOK_CLIENT_ID") and os.getenv("TIKTOK_CLIENT_SECRET")
# BRACKET_SURGEON: disabled
#             ),
                "client_id_set": bool(os.getenv("TIKTOK_CLIENT_ID")),
                "client_secret_set": bool(os.getenv("TIKTOK_CLIENT_SECRET")),
# BRACKET_SURGEON: disabled
#                 },
            "instagram": {
            "configured": bool(
                os.getenv("INSTAGRAM_CLIENT_ID")
                and os.getenv("INSTAGRAM_CLIENT_SECRET")
# BRACKET_SURGEON: disabled
#             ),
                "client_id_set": bool(os.getenv("INSTAGRAM_CLIENT_ID")),
                "client_secret_set": bool(os.getenv("INSTAGRAM_CLIENT_SECRET")),
# BRACKET_SURGEON: disabled
#                 },
            "active_states": len(OAUTH_STATES),
# BRACKET_SURGEON: disabled
#             }

    return status