#!/usr/bin/env python3
"""
Avatar API Router

Handles avatar generation, customization, and management.
Provides endpoints for creating and retrieving user avatars.
"""

import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import quote, unquote

from fastapi import APIRouter, HTTPException, Request, Query, Form
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/avatar", tags=["avatar"])

# In-memory storage for demo purposes
avatars: Dict[str, Dict[str, Any]] = {}
avatar_stats: Dict[str, int] = {"total_created": 0, "total_requests": 0}

class AvatarCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    style: Optional[str] = Field("default", description="Avatar style")
    color_scheme: Optional[str] = Field("monochrome", description="Color scheme")
    size: Optional[int] = Field(128, ge=32, le=512, description="Avatar size in pixels")
    background_color: Optional[str] = Field("#FFFFFF", description="Background color")
    seed: Optional[str] = Field(None, description="Random seed for consistent generation")

class AvatarResponse(BaseModel):
    avatar_id: str
    user_id: str
    style: str
    color_scheme: str
    size: int
    background_color: str
    created_at: str
    url: str
    svg_data: Optional[str]

class AvatarInfo(BaseModel):
    avatar_id: str
    user_id: str
    style: str
    color_scheme: str
    size: int
    created_at: str
    request_count: int

def generate_avatar_id() -> str:
    """Generate a unique avatar ID."""
    return secrets.token_urlsafe(8)

def generate_simple_svg(user_id: str, style: str, color_scheme: str, size: int, bg_color: str) -> str:
    """Generate a simple SVG avatar."""
    # Simple geometric avatar generation
    hash_val = hash(user_id + style + color_scheme)
    
    # Color schemes
    color_schemes = {
        "monochrome": {"primary": "#000000", "secondary": "#FFFFFF"},
        "vibrant": {"primary": "#FF6B6B", "secondary": "#4ECDC4"},
        "pastel": {"primary": "#FFB3BA", "secondary": "#BAFFC9"},
        "neon": {"primary": "#FF073A", "secondary": "#39FF14"},
        "earth": {"primary": "#8B4513", "secondary": "#228B22"},
        "ocean": {"primary": "#006994", "secondary": "#87CEEB"}
    }
    
    colors = color_schemes.get(color_scheme, color_schemes["monochrome"])
    primary = colors["primary"]
    secondary = colors["secondary"]
    
    # Generate simple geometric shapes based on hash
    shapes = []
    for i in range(3):
        x = (hash_val >> (i * 8)) % (size - 40) + 20
        y = (hash_val >> ((i + 3) * 8)) % (size - 40) + 20
        radius = (hash_val >> ((i + 6) * 8)) % 20 + 10
        color = primary if i % 2 == 0 else secondary
        shapes.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" opacity="0.8"/>')
    
    svg_content = f'''
    <svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{size}" height="{size}" fill="{bg_color}"/>
        {''.join(shapes)}
    </svg>
    '''.strip()
    
    return svg_content

@router.post("/create", response_model=AvatarResponse)
async def create_avatar(avatar: AvatarCreate):
    """Create a new avatar."""
    # Check if avatar already exists for this user
    existing_avatar = None
    for avatar_data in avatars.values():
        if avatar_data["user_id"] == avatar.user_id:
            existing_avatar = avatar_data
            break
    
    if existing_avatar:
        # Update existing avatar
        avatar_id = existing_avatar["avatar_id"]
        avatar_data = existing_avatar
        avatar_data.update({
            "style": avatar.style,
            "color_scheme": avatar.color_scheme,
            "size": avatar.size,
            "background_color": avatar.background_color,
            "updated_at": datetime.now().isoformat()
        })
    else:
        # Create new avatar
        avatar_id = generate_avatar_id()
        while avatar_id in avatars:
            avatar_id = generate_avatar_id()
        
        avatar_data = {
            "avatar_id": avatar_id,
            "user_id": avatar.user_id,
            "style": avatar.style or "default",
            "color_scheme": avatar.color_scheme or "monochrome",
            "size": avatar.size or 128,
            "background_color": avatar.background_color or "#FFFFFF",
            "created_at": datetime.now().isoformat(),
            "request_count": 0
        }
        
        avatars[avatar_id] = avatar_data
        avatar_stats["total_created"] += 1
    
    # Generate SVG
    svg_data = generate_simple_svg(
        avatar_data["user_id"],
        avatar_data["style"],
        avatar_data["color_scheme"],
        avatar_data["size"],
        avatar_data["background_color"]
    )
    
    avatar_data["svg_data"] = svg_data
    avatar_data["request_count"] += 1
    avatar_stats["total_requests"] += 1
    
    return AvatarResponse(
        avatar_id=avatar_data["avatar_id"],
        user_id=avatar_data["user_id"],
        style=avatar_data["style"],
        color_scheme=avatar_data["color_scheme"],
        size=avatar_data["size"],
        background_color=avatar_data["background_color"],
        created_at=avatar_data["created_at"],
        url=f"/avatar/{avatar_id}",
        svg_data=svg_data
    )

@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar(avatar_id: str):
    """Retrieve an avatar by ID."""
    if avatar_id not in avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    avatar_data = avatars[avatar_id]
    
    # Generate fresh SVG
    svg_data = generate_simple_svg(
        avatar_data["user_id"],
        avatar_data["style"],
        avatar_data["color_scheme"],
        avatar_data["size"],
        avatar_data["background_color"]
    )
    
    avatar_data["request_count"] += 1
    avatar_stats["total_requests"] += 1
    
    return AvatarResponse(
        avatar_id=avatar_data["avatar_id"],
        user_id=avatar_data["user_id"],
        style=avatar_data["style"],
        color_scheme=avatar_data["color_scheme"],
        size=avatar_data["size"],
        background_color=avatar_data["background_color"],
        created_at=avatar_data["created_at"],
        url=f"/avatar/{avatar_id}",
        svg_data=svg_data
    )

@router.get("/{avatar_id}/svg")
async def get_avatar_svg(avatar_id: str):
    """Get avatar as SVG."""
    if avatar_id not in avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    avatar_data = avatars[avatar_id]
    
    # Generate SVG
    svg_data = generate_simple_svg(
        avatar_data["user_id"],
        avatar_data["style"],
        avatar_data["color_scheme"],
        avatar_data["size"],
        avatar_data["background_color"]
    )
    
    avatar_data["request_count"] += 1
    avatar_stats["total_requests"] += 1
    
    return Response(content=svg_data, media_type="image/svg+xml")

@router.get("/user/{user_id}", response_model=AvatarResponse)
async def get_user_avatar(user_id: str):
    """Get avatar by user ID."""
    # Find avatar for user
    for avatar_data in avatars.values():
        if avatar_data["user_id"] == user_id:
            # Generate fresh SVG
            svg_data = generate_simple_svg(
                avatar_data["user_id"],
                avatar_data["style"],
                avatar_data["color_scheme"],
                avatar_data["size"],
                avatar_data["background_color"]
            )
            
            avatar_data["request_count"] += 1
            avatar_stats["total_requests"] += 1
            
            return AvatarResponse(
                avatar_id=avatar_data["avatar_id"],
                user_id=avatar_data["user_id"],
                style=avatar_data["style"],
                color_scheme=avatar_data["color_scheme"],
                size=avatar_data["size"],
                background_color=avatar_data["background_color"],
                created_at=avatar_data["created_at"],
                url=f"/avatar/{avatar_data['avatar_id']}",
                svg_data=svg_data
            )
    
    raise HTTPException(status_code=404, detail="Avatar not found for user")

@router.get("/user/{user_id}/svg")
async def get_user_avatar_svg(user_id: str):
    """Get user avatar as SVG."""
    # Find avatar for user
    for avatar_data in avatars.values():
        if avatar_data["user_id"] == user_id:
            # Generate SVG
            svg_data = generate_simple_svg(
                avatar_data["user_id"],
                avatar_data["style"],
                avatar_data["color_scheme"],
                avatar_data["size"],
                avatar_data["background_color"]
            )
            
            avatar_data["request_count"] += 1
            avatar_stats["total_requests"] += 1
            
            return Response(content=svg_data, media_type="image/svg+xml")
    
    raise HTTPException(status_code=404, detail="Avatar not found for user")

@router.put("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(avatar_id: str, avatar: AvatarCreate):
    """Update an existing avatar."""
    if avatar_id not in avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    avatar_data = avatars[avatar_id]
    
    # Update avatar properties
    avatar_data.update({
        "style": avatar.style or avatar_data["style"],
        "color_scheme": avatar.color_scheme or avatar_data["color_scheme"],
        "size": avatar.size or avatar_data["size"],
        "background_color": avatar.background_color or avatar_data["background_color"],
        "updated_at": datetime.now().isoformat()
    })
    
    # Generate fresh SVG
    svg_data = generate_simple_svg(
        avatar_data["user_id"],
        avatar_data["style"],
        avatar_data["color_scheme"],
        avatar_data["size"],
        avatar_data["background_color"]
    )
    
    return AvatarResponse(
        avatar_id=avatar_data["avatar_id"],
        user_id=avatar_data["user_id"],
        style=avatar_data["style"],
        color_scheme=avatar_data["color_scheme"],
        size=avatar_data["size"],
        background_color=avatar_data["background_color"],
        created_at=avatar_data["created_at"],
        url=f"/avatar/{avatar_id}",
        svg_data=svg_data
    )

@router.delete("/{avatar_id}")
async def delete_avatar(avatar_id: str):
    """Delete an avatar."""
    if avatar_id not in avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    avatar_data = avatars[avatar_id]
    del avatars[avatar_id]
    
    return {
        "message": "Avatar deleted successfully",
        "avatar_id": avatar_id,
        "user_id": avatar_data["user_id"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/list/all")
async def list_avatars(
    limit: int = Query(10, ge=1, le=100, description="Number of avatars to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """List avatars."""
    filtered_avatars = []
    
    for avatar_data in avatars.values():
        if user_id and avatar_data["user_id"] != user_id:
            continue
        
        filtered_avatars.append({
            "avatar_id": avatar_data["avatar_id"],
            "user_id": avatar_data["user_id"],
            "style": avatar_data["style"],
            "color_scheme": avatar_data["color_scheme"],
            "size": avatar_data["size"],
            "created_at": avatar_data["created_at"],
            "request_count": avatar_data["request_count"]
        })
    
    # Sort by creation time (newest first)
    filtered_avatars.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "avatars": filtered_avatars[:limit],
        "total_count": len(filtered_avatars),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/styles")
async def get_avatar_styles():
    """Get available avatar styles."""
    styles = [
        "default", "geometric", "abstract", "minimal", "retro", "modern"
    ]
    
    return {
        "styles": styles,
        "total_count": len(styles),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/color-schemes")
async def get_color_schemes():
    """Get available color schemes."""
    color_schemes = {
        "monochrome": {"primary": "#000000", "secondary": "#FFFFFF"},
        "vibrant": {"primary": "#FF6B6B", "secondary": "#4ECDC4"},
        "pastel": {"primary": "#FFB3BA", "secondary": "#BAFFC9"},
        "neon": {"primary": "#FF073A", "secondary": "#39FF14"},
        "earth": {"primary": "#8B4513", "secondary": "#228B22"},
        "ocean": {"primary": "#006994", "secondary": "#87CEEB"}
    }
    
    return {
        "color_schemes": color_schemes,
        "total_count": len(color_schemes),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/stats")
async def get_avatar_stats():
    """Get avatar service statistics."""
    # Calculate style distribution
    style_stats = {}
    color_scheme_stats = {}
    size_stats = {}
    
    for avatar_data in avatars.values():
        style = avatar_data["style"]
        color_scheme = avatar_data["color_scheme"]
        size = avatar_data["size"]
        
        style_stats[style] = style_stats.get(style, 0) + 1
        color_scheme_stats[color_scheme] = color_scheme_stats.get(color_scheme, 0) + 1
        size_stats[size] = size_stats.get(size, 0) + 1
    
    return {
        "total_avatars": len(avatars),
        "total_created": avatar_stats["total_created"],
        "total_requests": avatar_stats["total_requests"],
        "style_distribution": style_stats,
        "color_scheme_distribution": color_scheme_stats,
        "size_distribution": size_stats,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def avatar_health():
    """Check avatar service health."""
    return {
        "ok": True,
        "total_avatars": len(avatars),
        "total_created": avatar_stats["total_created"],
        "total_requests": avatar_stats["total_requests"],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/generate-random")
async def generate_random_avatar(
    user_id: str = Query(..., description="User identifier"),
    size: int = Query(128, ge=32, le=512, description="Avatar size")
):
    """Generate a random avatar for a user."""
    import random
    
    styles = ["default", "geometric", "abstract", "minimal", "retro", "modern"]
    color_schemes = ["monochrome", "vibrant", "pastel", "neon", "earth", "ocean"]
    backgrounds = ["#FFFFFF", "#F0F0F0", "#E0E0E0", "#D0D0D0", "#C0C0C0"]
    
    avatar_create = AvatarCreate(
        user_id=user_id,
        style=random.choice(styles),
        color_scheme=random.choice(color_schemes),
        size=size,
        background_color=random.choice(backgrounds),
        seed=str(random.randint(1000, 9999))
    )
    
    return await create_avatar(avatar_create)