#!/usr/bin/env python3
"""
Paste Router

Handles paste/clipboard functionality and text sharing.
Provides endpoints for creating, retrieving, and managing text pastes.
"""

import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import quote, unquote

from fastapi import APIRouter, HTTPException, Request, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/paste", tags=["paste"])

# In-memory storage for demo purposes
pastes: Dict[str, Dict[str, Any]] = {}
paste_stats: Dict[str, int] = {"total_created": 0, "total_views": 0}

class PasteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=100000, description="Paste content")
    title: Optional[str] = Field(None, max_length=200, description="Optional paste title")
    language: Optional[str] = Field("text", max_length=50, description="Programming language for syntax highlighting")
    expires_in: Optional[int] = Field(3600, description="Expiration time in seconds (default: 1 hour)")
    password: Optional[str] = Field(None, max_length=100, description="Optional password protection")
    is_private: bool = Field(False, description="Whether the paste is private")

class PasteResponse(BaseModel):
    paste_id: str
    title: Optional[str]
    content: str
    language: str
    created_at: str
    expires_at: Optional[str]
    view_count: int
    is_private: bool
    has_password: bool

class PasteInfo(BaseModel):
    paste_id: str
    title: Optional[str]
    language: str
    created_at: str
    expires_at: Optional[str]
    view_count: int
    content_length: int
    is_private: bool
    has_password: bool

def generate_paste_id() -> str:
    """Generate a unique paste ID."""
    return secrets.token_urlsafe(8)

def is_paste_expired(paste_data: Dict[str, Any]) -> bool:
    """Check if a paste has expired."""
    if not paste_data.get("expires_at"):
        return False
    
    expires_at = datetime.fromisoformat(paste_data["expires_at"])
    return datetime.now() > expires_at

def cleanup_expired_pastes():
    """Remove expired pastes from storage."""
    expired_ids = []
    for paste_id, paste_data in pastes.items():
        if is_paste_expired(paste_data):
            expired_ids.append(paste_id)
    
    for paste_id in expired_ids:
        del pastes[paste_id]
    
    return len(expired_ids)

def validate_password(paste_data: Dict[str, Any], provided_password: Optional[str]) -> bool:
    """Validate paste password if required."""
    if not paste_data.get("password"):
        return True
    
    return paste_data["password"] == provided_password

@router.post("/create", response_model=dict)
async def create_paste(paste: PasteCreate):
    """Create a new paste."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    # Generate unique paste ID
    paste_id = generate_paste_id()
    while paste_id in pastes:
        paste_id = generate_paste_id()
    
    # Calculate expiration time
    expires_at = None
    if paste.expires_in and paste.expires_in > 0:
        expires_at = (datetime.now() + timedelta(seconds=paste.expires_in)).isoformat()
    
    # Create paste data
    paste_data = {
        "paste_id": paste_id,
        "title": paste.title,
        "content": paste.content,
        "language": paste.language or "text",
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "view_count": 0,
        "is_private": paste.is_private,
        "password": paste.password,
        "content_length": len(paste.content)
    }
    
    # Store paste
    pastes[paste_id] = paste_data
    paste_stats["total_created"] += 1
    
    return {
        "paste_id": paste_id,
        "url": f"/paste/{paste_id}",
        "raw_url": f"/paste/{paste_id}/raw",
        "expires_at": expires_at,
        "message": "Paste created successfully"
    }

@router.get("/{paste_id}", response_model=PasteResponse)
async def get_paste(
    paste_id: str,
    password: Optional[str] = Query(None, description="Password for protected pastes")
):
    """Retrieve a paste by ID."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    if paste_id not in pastes:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    paste_data = pastes[paste_id]
    
    # Check if paste is expired
    if is_paste_expired(paste_data):
        del pastes[paste_id]
        raise HTTPException(status_code=404, detail="Paste has expired")
    
    # Check password if required
    if not validate_password(paste_data, password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Increment view count
    paste_data["view_count"] += 1
    paste_stats["total_views"] += 1
    
    return PasteResponse(
        paste_id=paste_data["paste_id"],
        title=paste_data["title"],
        content=paste_data["content"],
        language=paste_data["language"],
        created_at=paste_data["created_at"],
        expires_at=paste_data["expires_at"],
        view_count=paste_data["view_count"],
        is_private=paste_data["is_private"],
        has_password=bool(paste_data.get("password"))
    )

@router.get("/{paste_id}/raw")
async def get_paste_raw(
    paste_id: str,
    password: Optional[str] = Query(None, description="Password for protected pastes")
):
    """Get paste content as plain text."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    if paste_id not in pastes:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    paste_data = pastes[paste_id]
    
    # Check if paste is expired
    if is_paste_expired(paste_data):
        del pastes[paste_id]
        raise HTTPException(status_code=404, detail="Paste has expired")
    
    # Check password if required
    if not validate_password(paste_data, password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Increment view count
    paste_data["view_count"] += 1
    paste_stats["total_views"] += 1
    
    return paste_data["content"]

@router.get("/{paste_id}/info", response_model=PasteInfo)
async def get_paste_info(
    paste_id: str,
    password: Optional[str] = Query(None, description="Password for protected pastes")
):
    """Get paste metadata without content."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    if paste_id not in pastes:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    paste_data = pastes[paste_id]
    
    # Check if paste is expired
    if is_paste_expired(paste_data):
        del pastes[paste_id]
        raise HTTPException(status_code=404, detail="Paste has expired")
    
    # For info endpoint, we don't require password but show limited info
    return PasteInfo(
        paste_id=paste_data["paste_id"],
        title=paste_data["title"],
        language=paste_data["language"],
        created_at=paste_data["created_at"],
        expires_at=paste_data["expires_at"],
        view_count=paste_data["view_count"],
        content_length=paste_data["content_length"],
        is_private=paste_data["is_private"],
        has_password=bool(paste_data.get("password"))
    )

@router.delete("/{paste_id}")
async def delete_paste(
    paste_id: str,
    password: Optional[str] = Query(None, description="Password for protected pastes")
):
    """Delete a paste."""
    if paste_id not in pastes:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    paste_data = pastes[paste_id]
    
    # Check password if required
    if not validate_password(paste_data, password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Delete paste
    del pastes[paste_id]
    
    return {
        "message": "Paste deleted successfully",
        "paste_id": paste_id,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/list/recent")
async def list_recent_pastes(
    limit: int = Query(10, ge=1, le=100, description="Number of pastes to return"),
    include_private: bool = Query(False, description="Include private pastes")
):
    """List recent public pastes."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    # Filter and sort pastes
    filtered_pastes = []
    for paste_data in pastes.values():
        if not include_private and paste_data["is_private"]:
            continue
        
        filtered_pastes.append({
            "paste_id": paste_data["paste_id"],
            "title": paste_data["title"],
            "language": paste_data["language"],
            "created_at": paste_data["created_at"],
            "expires_at": paste_data["expires_at"],
            "view_count": paste_data["view_count"],
            "content_length": paste_data["content_length"],
            "has_password": bool(paste_data.get("password"))
        })
    
    # Sort by creation time (newest first)
    filtered_pastes.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "pastes": filtered_pastes[:limit],
        "total_count": len(filtered_pastes),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/search")
async def search_pastes(
    query: str = Query(..., min_length=1, description="Search query"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Search pastes by content or title."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    query_lower = query.lower()
    results = []
    
    for paste_data in pastes.values():
        # Skip private pastes and password-protected pastes
        if paste_data["is_private"] or paste_data.get("password"):
            continue
        
        # Filter by language if specified
        if language and paste_data["language"] != language:
            continue
        
        # Search in title and content
        title_match = paste_data.get("title") and query_lower in paste_data["title"].lower()
        content_match = query_lower in paste_data["content"].lower()
        
        if title_match or content_match:
            results.append({
                "paste_id": paste_data["paste_id"],
                "title": paste_data["title"],
                "language": paste_data["language"],
                "created_at": paste_data["created_at"],
                "expires_at": paste_data["expires_at"],
                "view_count": paste_data["view_count"],
                "content_length": paste_data["content_length"],
                "match_type": "title" if title_match else "content"
            })
    
    # Sort by creation time (newest first)
    results.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "results": results[:limit],
        "query": query,
        "total_matches": len(results),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/cleanup")
async def cleanup_pastes():
    """Manually trigger cleanup of expired pastes."""
    cleaned_count = cleanup_expired_pastes()
    
    return {
        "message": "Cleanup completed",
        "expired_pastes_removed": cleaned_count,
        "active_pastes": len(pastes),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/stats")
async def get_paste_stats():
    """Get paste service statistics."""
    # Clean up expired pastes
    cleanup_expired_pastes()
    
    # Calculate language distribution
    language_stats = {}
    for paste_data in pastes.values():
        lang = paste_data["language"]
        language_stats[lang] = language_stats.get(lang, 0) + 1
    
    # Calculate expiration stats
    expiring_soon = 0  # Within next hour
    never_expires = 0
    
    for paste_data in pastes.values():
        if not paste_data.get("expires_at"):
            never_expires += 1
        else:
            expires_at = datetime.fromisoformat(paste_data["expires_at"])
            if expires_at <= datetime.now() + timedelta(hours=1):
                expiring_soon += 1
    
    return {
        "total_pastes": len(pastes),
        "total_created": paste_stats["total_created"],
        "total_views": paste_stats["total_views"],
        "language_distribution": language_stats,
        "expiration_stats": {
            "expiring_soon": expiring_soon,
            "never_expires": never_expires
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages."""
    languages = [
        "text", "python", "javascript", "typescript", "java", "c", "cpp", "csharp",
        "php", "ruby", "go", "rust", "swift", "kotlin", "scala", "html", "css",
        "sql", "json", "xml", "yaml", "markdown", "bash", "powershell", "dockerfile"
    ]
    
    return {
        "languages": languages,
        "total_count": len(languages),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def paste_health():
    """Check paste service health."""
    # Clean up expired pastes
    cleaned_count = cleanup_expired_pastes()
    
    return {
        "ok": True,
        "active_pastes": len(pastes),
        "total_created": paste_stats["total_created"],
        "total_views": paste_stats["total_views"],
        "expired_cleaned": cleaned_count,
        "timestamp": datetime.now().isoformat()
    }

# Simple HTML interface for testing
@router.get("/ui", response_class=HTMLResponse)
async def paste_ui():
    """Simple HTML interface for creating and viewing pastes."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Paste Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            textarea { width: 100%; height: 300px; margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
            input, select { margin: 5px; padding: 8px; border: 1px solid #ddd; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; background: #e9ecef; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Paste Service</h1>
            <form id="pasteForm">
                <div>
                    <input type="text" id="title" placeholder="Paste title (optional)" style="width: 300px;">
                    <select id="language">
                        <option value="text">Plain Text</option>
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="html">HTML</option>
                        <option value="css">CSS</option>
                        <option value="json">JSON</option>
                    </select>
                </div>
                <textarea id="content" placeholder="Enter your paste content here..."></textarea>
                <div>
                    <input type="password" id="password" placeholder="Password (optional)" style="width: 200px;">
                    <label><input type="checkbox" id="private"> Private</label>
                    <select id="expires">
                        <option value="3600">1 Hour</option>
                        <option value="86400">1 Day</option>
                        <option value="604800">1 Week</option>
                        <option value="0">Never</option>
                    </select>
                </div>
                <button type="submit">Create Paste</button>
            </form>
            <div id="result" class="result" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('pasteForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    content: document.getElementById('content').value,
                    title: document.getElementById('title').value || null,
                    language: document.getElementById('language').value,
                    password: document.getElementById('password').value || null,
                    is_private: document.getElementById('private').checked,
                    expires_in: parseInt(document.getElementById('expires').value)
                };
                
                try {
                    const response = await fetch('/paste/create', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('result').innerHTML = `
                            <h3>Paste Created Successfully!</h3>
                            <p><strong>Paste ID:</strong> ${result.paste_id}</p>
                            <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${window.location.origin}${result.url}</a></p>
                            <p><strong>Raw URL:</strong> <a href="${result.raw_url}" target="_blank">${window.location.origin}${result.raw_url}</a></p>
                            ${result.expires_at ? `<p><strong>Expires:</strong> ${new Date(result.expires_at).toLocaleString()}</p>` : ''}
                        `;
                        document.getElementById('result').style.display = 'block';
                        document.getElementById('pasteForm').reset();
                    } else {
                        throw new Error(result.detail || 'Failed to create paste');
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <h3>Error</h3>
                        <p style="color: red;">${error.message}</p>
                    `;
                    document.getElementById('result').style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)