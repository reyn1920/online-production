# app/routers/paste.py - Paste functionality router
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import socket
import requests
import math
import time
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# In-memory storage for pastes (in production, use a database)
pastes_storage = []

# Provider status for places functionality
PROVIDER_STATUS = {
    "overpass": {
        "name": "OpenStreetMap Overpass",
        "color": "green",
        "last_error": None,
        "requires_key": False},
    "nominatim": {
        "name": "OpenStreetMap Nominatim",
        "color": "green",
        "last_error": None,
        "requires_key": False},
}


class PasteCreate(BaseModel):
    content: str
    title: Optional[str] = None


class PasteResponse(BaseModel):
    id: int
    content: str
    title: Optional[str]
    timestamp: str


@router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "healthy",
        "providers": PROVIDER_STATUS,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": "paste_service"}


@router.get("/providers")
async def places_providers():
    """Get available place search providers"""
    return {
        "providers": PROVIDER_STATUS,
        "default": "overpass"
    }


@router.post("/paste", response_model=PasteResponse)
async def create_paste(paste_data: PasteCreate):
    """Create a new paste"""
    if not paste_data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    paste_id = len(pastes_storage) + 1
    new_paste = {
        "id": paste_id,
        "content": paste_data.content,
        "title": paste_data.title,
        "timestamp": datetime.now().isoformat()
    }

    pastes_storage.append(new_paste)
    return new_paste


@router.get("/pastes", response_model=List[PasteResponse])
async def get_pastes(limit: int = 10, offset: int = 0):
    """Get all pastes with pagination"""
    start = offset
    end = offset + limit
    return pastes_storage[start:end]


@router.get("/paste/{paste_id}", response_model=PasteResponse)
async def get_paste(paste_id: int):
    """Get a specific paste by ID"""
    for paste in pastes_storage:
        if paste["id"] == paste_id:
            return paste
    raise HTTPException(status_code=404, detail="Paste not found")

# OSM Tags for place search
_OSM_TAGS = {
    "veterinary": {"amenity": "veterinary"},
    "clinic": {"amenity": "clinic"},
    "hospital": {"amenity": "hospital"},
    "pharmacy": {"amenity": "pharmacy"},
    "pet_store": {"shop": "pet"},
    "dog_park": {"leisure": "dog_park"},
}


def _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit):
    """Query Overpass API for places"""
    query = f"""
    [out:json][timeout:25];
    (
      node["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
      way["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
      relation["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
    );
    out center {limit};
    """

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        PROVIDER_STATUS["overpass"]["last_error"] = str(e)
        PROVIDER_STATUS["overpass"]["color"] = "red"
        raise


def _elements_to_items(js):
    """Convert Overpass API response to standardized format"""
    items = []
    for el in js.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed")

        # Get coordinates
        if "lat" in el and "lon" in el:
            lat, lng = el["lat"], el["lon"]
        elif "center" in el:
            lat, lng = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        # Build address
        addr_parts = []
        for key in ["addr:housenumber", "addr:street", "addr:city"]:
            if key in tags:
                addr_parts.append(tags[key])
        address = ", ".join(addr_parts) if addr_parts else ""

        items.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "address": address,
            "tags": tags
        })

    return items


@router.get("/places/search")
async def places_search(
    category: str = "veterinary",
    lat: float = 40.7128,
    lng: float = -74.0060,
    radius_m: int = 5000,
    limit: int = 50
):
    """Search for places using OpenStreetMap data"""
    if category not in _OSM_TAGS:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    tag_info = _OSM_TAGS[category]
    tag_key, tag_val = next(iter(tag_info.items()))

    try:
        overpass_data = _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit)
        items = _elements_to_items(overpass_data)

        PROVIDER_STATUS["overpass"]["color"] = "green"
        PROVIDER_STATUS["overpass"]["last_error"] = None

        return {
            "items": items,
            "provider": "overpass",
            "query": {
                "category": category,
                "lat": lat,
                "lng": lng,
                "radius_m": radius_m,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# HTML Templates
PASTE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Paste App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        textarea { width: 100%; height: 300px; margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
        button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .paste-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 4px; background: #f9f9f9; }
        .paste-meta { color: #666; font-size: 0.9em; margin-bottom: 10px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Paste App</h1>
        <form id="pasteForm">
            <input type="text" id="title" placeholder="Optional title..." style="width: 100%; margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <textarea id="content" placeholder="Enter your text here..."></textarea><br>
            <button type="submit">Save Paste</button>
            <button type="button" onclick="loadPastes()">Refresh</button>
        </form>
        <div id="pastes"></div>
    </div>

    <script>
        let pastes = [];

        document.getElementById('pasteForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const content = document.getElementById('content').value;
            const title = document.getElementById('title').value;

            if (content.trim()) {
                try {
                    const response = await fetch('/paste/paste', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            content: content,
                            title: title || null
                        })
                    });

                    if (response.ok) {
                        document.getElementById('content').value = '';
                        document.getElementById('title').value = '';
                        loadPastes();
                    } else {
                        alert('Failed to save paste');
                    }
                } catch (error) {
                    alert('Error saving paste: ' + error.message);
                }
            }
        });

        async function loadPastes() {
            try {
                const response = await fetch('/paste/pastes');
                if (response.ok) {
                    pastes = await response.json();
                    renderPastes();
                }
            } catch (error) {
                console.error('Error loading pastes:', error);
            }
        }

        function renderPastes() {
            const container = document.getElementById('pastes');
            container.innerHTML = pastes.map(paste => `
                <div class="paste-item">
                    <div class="paste-meta">
                        ${paste.title ? `<strong>${paste.title}</strong> - ` : ''}
                        Saved: ${new Date(paste.timestamp).toLocaleString()}
                    </div>
                    <pre>${paste.content}</pre>
                </div>
            `).join('');
        }

        // Load pastes on page load
        loadPastes();
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def paste_interface():
    """Main paste interface"""
    return HTMLResponse(content=PASTE_HTML_TEMPLATE)
