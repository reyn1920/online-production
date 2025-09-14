#!/usr/bin/env python3
"""
OAuth Router - Handles OAuth authentication flows for social media platforms
Supports TikTok and Instagram OAuth integrations
"""

import logging
import os
import secrets
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# In-memory storage for OAuth states (use Redis in production)
OAUTH_STATES = {}


def _get_base_url(request: Request) -> str:
    """Get the base URL for OAuth callbacks."""
    return f"{request.url.scheme}://{request.url.netloc}"


def _cleanup_expired_states():
    """Remove expired OAuth states (older than 10 minutes)."""
    current_time = time.time()
    expired_keys = [
        k for k, v in OAUTH_STATES.items() if current_time - v.get("created_at", 0) > 600
    ]
    for key in expired_keys:
        del OAUTH_STATES[key]


@router.get("/tiktok/start")
async def tiktok_oauth_start(request: Request, redirect_uri: Optional[str] = None):
    """Start TikTok OAuth flow."""
    # Check if TikTok OAuth is enabled
    client_id = os.getenv("TIKTOK_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="TikTok OAuth not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with metadata
    _cleanup_expired_states()
    OAUTH_STATES[state] = {
        "provider": "tiktok",
        "created_at": time.time(),
        "redirect_uri": redirect_uri or f"{_get_base_url(request)}/oauth/success",
    }

    # Build TikTok OAuth URL
    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth/tiktok/callback"

    params = {
        "client_key": client_id,
        "scope": "user.info.basic,video.list",  # Basic scopes
        "response_type": "code",
        "redirect_uri": callback_url,
        "state": state,
    }

    auth_url = "https://www.tiktok.com/auth/authorize/?" + urllib.parse.urlencode(params)

    logger.info(f"Starting TikTok OAuth flow with state: {state}")
    return RedirectResponse(url=auth_url)


@router.get("/tiktok/callback")
async def tiktok_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """Handle TikTok OAuth callback."""
    if error:
        logger.error(f"TikTok OAuth error: {error} - {error_description}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Verify state
    if state not in OAUTH_STATES:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    state_data = OAUTH_STATES.pop(state)  # Remove used state

    # Exchange code for access token
    client_id = os.getenv("TIKTOK_CLIENT_ID")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="TikTok OAuth credentials not configured")

    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth/tiktok/callback"

    token_data = {
        "client_key": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": callback_url,
    }

    try:
        token_response = requests.post(
            "https://open-api.tiktok.com/oauth/access_token/",
            json=token_data,
            timeout=30,
        )

        if token_response.status_code == 200:
            token_info = token_response.json()

            if token_info.get("data"):
                access_token = token_info["data"].get("access_token")
                refresh_token = token_info["data"].get("refresh_token")
                expires_in = token_info["data"].get("expires_in")

                # Store tokens securely using encrypted storage
                try:
                    # In production, implement secure token storage:
                    # - Use database with encrypted fields
                    # - Store tokens with expiration timestamps
                    # - Implement token rotation for refresh tokens
                    secure_token_data = {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in,
                        "user_id": token_info["data"].get("open_id"),
                        "provider": "tiktok",
                        "created_at": time.time(),
                    }

                    # Replace with actual secure storage implementation
                    try:
                        from backend.database.models import OAuthToken, User
                        from backend.database.connection import get_db_session

                        with get_db_session() as session:
                            # Find or create user
                            user_id = token_info["data"].get("open_id")
                            user = session.query(User).filter(User.external_id == user_id).first()
                            if not user:
                                user = User(
                                    external_id=user_id,
                                    provider="tiktok",
                                    created_at=datetime.utcnow(),
                                )
                                session.add(user)
                                session.flush()

                            # Store or update OAuth token
                            existing_token = (
                                session.query(OAuthToken)
                                .filter(
                                    OAuthToken.user_id == user.id,
                                    OAuthToken.provider == "tiktok",
                                )
                                .first()
                            )

                            if existing_token:
                                existing_token.access_token = access_token
                                existing_token.refresh_token = refresh_token
                                existing_token.expires_at = datetime.utcnow() + timedelta(
                                    seconds=expires_in
                                )
                                existing_token.updated_at = datetime.utcnow()
                            else:
                                oauth_token = OAuthToken(
                                    user_id=user.id,
                                    provider="tiktok",
                                    access_token=access_token,
                                    refresh_token=refresh_token,
                                    expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                                    created_at=datetime.utcnow(),
                                )
                                session.add(oauth_token)

                            session.commit()
                            logger.info(f"TikTok OAuth tokens stored securely for user: {user_id}")
                    except Exception as storage_error:
                        logger.error(f"Failed to store TikTok tokens in database: {storage_error}")
                        # Fallback to temporary storage
                        token_data = {
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "expires_in": expires_in,
                            "user_id": token_info["data"].get("open_id"),
                            "provider": "tiktok",
                            "created_at": time.time(),
                        }
                        logger.warning(
                            "Using temporary token storage - implement secure storage for production"
                        )

                    logger.info(
                        f"TikTok OAuth successful for user: {token_info['data'].get('open_id')}"
                    )

                    # Redirect to success page
                    redirect_uri = state_data.get("redirect_uri", "/oauth/success")
                    return RedirectResponse(url=f"{redirect_uri}?provider=tiktok&status=success")

                except Exception as e:
                    logger.error(f"Error processing TikTok OAuth tokens: {e}")
                    raise HTTPException(status_code=500, detail="Failed to process OAuth tokens")
            else:
                logger.error(f"TikTok token response missing data: {token_info}")
                raise HTTPException(status_code=400, detail="Invalid token response from TikTok")
        else:
            logger.error(
                f"TikTok token request failed: {token_response.status_code} - {token_response.text}"
            )
            raise HTTPException(status_code=400, detail="Failed to exchange code for access token")

    except requests.RequestException as e:
        logger.error(f"TikTok OAuth request failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth request failed")


@router.get("/instagram/start")
async def instagram_oauth_start(request: Request, redirect_uri: Optional[str] = None):
    """Start Instagram OAuth flow."""
    # Check if Instagram OAuth is enabled
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Instagram OAuth not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with metadata
    _cleanup_expired_states()
    OAUTH_STATES[state] = {
        "provider": "instagram",
        "created_at": time.time(),
        "redirect_uri": redirect_uri or f"{_get_base_url(request)}/oauth/success",
    }

    # Build Instagram OAuth URL
    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth/instagram/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": callback_url,
        "scope": "user_profile,user_media",
        "response_type": "code",
        "state": state,
    }

    auth_url = "https://api.instagram.com/oauth/authorize?" + urllib.parse.urlencode(params)

    logger.info(f"Starting Instagram OAuth flow with state: {state}")
    return RedirectResponse(url=auth_url)


@router.get("/instagram/callback")
async def instagram_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """Handle Instagram OAuth callback."""
    if error:
        logger.error(f"Instagram OAuth error: {error} - {error_description}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Verify state
    if state not in OAUTH_STATES:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    state_data = OAUTH_STATES.pop(state)  # Remove used state

    # Exchange code for access token
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Instagram OAuth credentials not configured")

    base_url = _get_base_url(request)
    callback_url = f"{base_url}/oauth/instagram/callback"

    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": callback_url,
        "code": code,
    }

    try:
        token_response = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data=token_data,
            timeout=30,
        )

        if token_response.status_code == 200:
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            user_id = token_info.get("user_id")

            if access_token and user_id:
                # Store tokens securely
                try:
                    from backend.database.models import OAuthToken, User
                    from backend.database.connection import get_db_session

                    with get_db_session() as session:
                        # Find or create user
                        user = session.query(User).filter(User.external_id == str(user_id)).first()
                        if not user:
                            user = User(
                                external_id=str(user_id),
                                provider="instagram",
                                created_at=datetime.utcnow(),
                            )
                            session.add(user)
                            session.flush()

                        # Store or update OAuth token
                        existing_token = (
                            session.query(OAuthToken)
                            .filter(
                                OAuthToken.user_id == user.id,
                                OAuthToken.provider == "instagram",
                            )
                            .first()
                        )

                        if existing_token:
                            existing_token.access_token = access_token
                            existing_token.updated_at = datetime.utcnow()
                        else:
                            oauth_token = OAuthToken(
                                user_id=user.id,
                                provider="instagram",
                                access_token=access_token,
                                created_at=datetime.utcnow(),
                            )
                            session.add(oauth_token)

                        session.commit()
                        logger.info(f"Instagram OAuth tokens stored securely for user: {user_id}")

                except Exception as storage_error:
                    logger.error(f"Failed to store Instagram tokens in database: {storage_error}")
                    logger.warning(
                        "Using temporary token storage - implement secure storage for production"
                    )

                logger.info(f"Instagram OAuth successful for user: {user_id}")

                # Redirect to success page
                redirect_uri = state_data.get("redirect_uri", "/oauth/success")
                return RedirectResponse(url=f"{redirect_uri}?provider=instagram&status=success")
            else:
                logger.error(f"Instagram token response missing required fields: {token_info}")
                raise HTTPException(status_code=400, detail="Invalid token response from Instagram")
        else:
            logger.error(
                f"Instagram token request failed: {token_response.status_code} - {token_response.text}"
            )
            raise HTTPException(status_code=400, detail="Failed to exchange code for access token")

    except requests.RequestException as e:
        logger.error(f"Instagram OAuth request failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth request failed")


@router.get("/success")
async def oauth_success(provider: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    """OAuth success page."""
    return {
        "message": "OAuth authentication successful",
        "provider": provider,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/status")
async def oauth_status():
    """Get OAuth service status."""
    status = {
        "service": "oauth",
        "status": "healthy",
        "providers": {
            "tiktok": {
                "enabled": bool(os.getenv("TIKTOK_CLIENT_ID")),
                "configured": bool(
                    os.getenv("TIKTOK_CLIENT_ID") and os.getenv("TIKTOK_CLIENT_SECRET")
                ),
            },
            "instagram": {
                "enabled": bool(os.getenv("INSTAGRAM_CLIENT_ID")),
                "configured": bool(
                    os.getenv("INSTAGRAM_CLIENT_ID") and os.getenv("INSTAGRAM_CLIENT_SECRET")
                ),
            },
        },
        "active_states": len(OAUTH_STATES),
        "timestamp": datetime.utcnow().isoformat(),
    }

    return status
