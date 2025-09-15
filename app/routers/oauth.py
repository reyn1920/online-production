#!/usr/bin/env python3
"""
OAuth Router

Handles OAuth authentication flows for social media platforms.
Supports TikTok and Instagram OAuth integrations.
"""

import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs

from fastapi import APIRouter, HTTPException, Request, Response, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter(prefix="/oauth", tags=["oauth"])

# In-memory storage for demo purposes
oauth_sessions: Dict[str, Dict[str, Any]] = {}
access_tokens: Dict[str, Dict[str, Any]] = {}

class OAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    platform: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    platform: str

class UserProfile(BaseModel):
    user_id: str
    username: str
    display_name: str
    email: Optional[str] = None
    profile_image: Optional[str] = None
    platform: str

# OAuth configurations (would be loaded from environment in production)
OAUTH_CONFIGS = {
    "tiktok": {
        "client_id": os.getenv("TIKTOK_CLIENT_ID", "demo_tiktok_client_id"),
        "client_secret": os.getenv("TIKTOK_CLIENT_SECRET", "demo_tiktok_secret"),
        "redirect_uri": os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/oauth/tiktok/callback"),
        "scope": "user.info.basic,video.list",
        "auth_url": "https://www.tiktok.com/auth/authorize/",
        "token_url": "https://open-api.tiktok.com/oauth/access_token/"
    },
    "instagram": {
        "client_id": os.getenv("INSTAGRAM_CLIENT_ID", "demo_instagram_client_id"),
        "client_secret": os.getenv("INSTAGRAM_CLIENT_SECRET", "demo_instagram_secret"),
        "redirect_uri": os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/oauth/instagram/callback"),
        "scope": "user_profile,user_media",
        "auth_url": "https://api.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token"
    }
}

def generate_state() -> str:
    """Generate a secure random state parameter for OAuth."""
    return secrets.token_urlsafe(32)

def validate_state(state: str, session_state: str) -> bool:
    """Validate OAuth state parameter."""
    return state == session_state

@router.get("/authorize/{platform}")
async def authorize(platform: str, request: Request):
    """Initiate OAuth authorization flow for a platform."""
    platform = platform.lower()
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    config = OAUTH_CONFIGS[platform]
    state = generate_state()
    
    # Store state in session
    session_id = f"oauth_{platform}_{int(time.time())}"
    oauth_sessions[session_id] = {
        "state": state,
        "platform": platform,
        "created_at": datetime.now().isoformat(),
        "client_ip": request.client.host if request.client else "unknown"
    }
    
    # Build authorization URL
    auth_params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": config["scope"],
        "response_type": "code",
        "state": state
    }
    
    auth_url = f"{config['auth_url']}?{urlencode(auth_params)}"
    
    # Set session cookie and redirect
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key=f"oauth_session_{platform}",
        value=session_id,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    
    return response

@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle OAuth callback from platform."""
    platform = platform.lower()
    
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    # Get session from cookie
    session_id = request.cookies.get(f"oauth_session_{platform}")
    if not session_id or session_id not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth session")
    
    session = oauth_sessions[session_id]
    
    # Validate state
    if not validate_state(state, session["state"]):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    config = OAUTH_CONFIGS[platform]
    
    # Exchange code for access token (mock implementation)
    try:
        # In a real implementation, you would make an HTTP request to the token endpoint
        # For demo purposes, we'll create a mock token
        access_token = f"mock_{platform}_token_{secrets.token_urlsafe(16)}"
        
        token_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"refresh_{platform}_{secrets.token_urlsafe(16)}",
            "scope": config["scope"],
            "platform": platform,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=3600)).isoformat()
        }
        
        # Store token
        access_tokens[access_token] = token_data
        
        # Clean up session
        del oauth_sessions[session_id]
        
        # Return success response
        response = {
            "message": f"Successfully authenticated with {platform}",
            "token_info": {
                "access_token": access_token,
                "token_type": token_data["token_type"],
                "expires_in": token_data["expires_in"],
                "scope": token_data["scope"],
                "platform": platform
            }
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

@router.get("/profile/{platform}")
async def get_user_profile(
    platform: str,
    access_token: str = Query(..., description="Access token for the platform")
):
    """Get user profile information using access token."""
    platform = platform.lower()
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    if access_token not in access_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    token_data = access_tokens[access_token]
    
    if token_data["platform"] != platform:
        raise HTTPException(status_code=400, detail="Token platform mismatch")
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.now() > expires_at:
        raise HTTPException(status_code=401, detail="Access token expired")
    
    # Mock user profile data
    if platform == "tiktok":
        profile = UserProfile(
            user_id="tiktok_user_123",
            username="demo_tiktok_user",
            display_name="Demo TikTok User",
            profile_image="https://example.com/tiktok_avatar.jpg",
            platform="tiktok"
        )
    elif platform == "instagram":
        profile = UserProfile(
            user_id="instagram_user_456",
            username="demo_instagram_user",
            display_name="Demo Instagram User",
            email="demo@instagram.com",
            profile_image="https://example.com/instagram_avatar.jpg",
            platform="instagram"
        )
    else:
        raise HTTPException(status_code=400, detail="Profile not available for this platform")
    
    return profile

@router.post("/refresh/{platform}")
async def refresh_token(
    platform: str,
    refresh_token: str = Query(..., description="Refresh token")
):
    """Refresh an expired access token."""
    platform = platform.lower()
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    # Find token by refresh token
    token_entry = None
    for token, data in access_tokens.items():
        if data.get("refresh_token") == refresh_token and data["platform"] == platform:
            token_entry = (token, data)
            break
    
    if not token_entry:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    old_token, old_data = token_entry
    
    # Generate new tokens
    new_access_token = f"mock_{platform}_token_{secrets.token_urlsafe(16)}"
    new_refresh_token = f"refresh_{platform}_{secrets.token_urlsafe(16)}"
    
    new_token_data = {
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": new_refresh_token,
        "scope": old_data["scope"],
        "platform": platform,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=3600)).isoformat()
    }
    
    # Replace old token with new one
    del access_tokens[old_token]
    access_tokens[new_access_token] = new_token_data
    
    return TokenResponse(**new_token_data)

@router.delete("/revoke/{platform}")
async def revoke_token(
    platform: str,
    access_token: str = Query(..., description="Access token to revoke")
):
    """Revoke an access token."""
    platform = platform.lower()
    
    if platform not in OAUTH_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    if access_token not in access_tokens:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token_data = access_tokens[access_token]
    
    if token_data["platform"] != platform:
        raise HTTPException(status_code=400, detail="Token platform mismatch")
    
    # Remove token
    del access_tokens[access_token]
    
    return {
        "message": f"Access token for {platform} revoked successfully",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/tokens")
async def list_active_tokens():
    """List all active tokens (for debugging/admin purposes)."""
    active_tokens = []
    
    for token, data in access_tokens.items():
        expires_at = datetime.fromisoformat(data["expires_at"])
        is_expired = datetime.now() > expires_at
        
        active_tokens.append({
            "token_id": token[:16] + "...",  # Partial token for security
            "platform": data["platform"],
            "created_at": data["created_at"],
            "expires_at": data["expires_at"],
            "is_expired": is_expired,
            "scope": data["scope"]
        })
    
    return {
        "active_tokens": active_tokens,
        "total_count": len(active_tokens),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/sessions")
async def list_oauth_sessions():
    """List active OAuth sessions."""
    return {
        "sessions": list(oauth_sessions.values()),
        "total_count": len(oauth_sessions),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/platforms")
async def list_supported_platforms():
    """List supported OAuth platforms and their configurations."""
    platforms = []
    
    for platform, config in OAUTH_CONFIGS.items():
        platforms.append({
            "platform": platform,
            "client_id": config["client_id"][:8] + "...",  # Partial for security
            "redirect_uri": config["redirect_uri"],
            "scope": config["scope"],
            "auth_url": config["auth_url"]
        })
    
    return {
        "platforms": platforms,
        "total_count": len(platforms),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def oauth_health():
    """Check OAuth service health."""
    return {
        "ok": True,
        "active_sessions": len(oauth_sessions),
        "active_tokens": len(access_tokens),
        "supported_platforms": list(OAUTH_CONFIGS.keys()),
        "timestamp": datetime.now().isoformat()
    }