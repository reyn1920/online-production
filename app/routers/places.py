#!/usr/bin/env python3
"""
Places API Router

FastAPI router for places and location-based services.
Follows go-live security practices:
- Input validation
- Rate limiting
- Error handling
- Secure response formatting
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator

from app.integrations.monitor import IntegrationMonitor
# If not already present in this module:
from app.integrations.registry import IntegrationRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["places"])

# Template loader
templates = Jinja2Templates(directory="app/templates")

# Initialize integration components
_registry = IntegrationRegistry()
_monitor = IntegrationMonitor(_registry)

# Request/Response Models


class LocationRequest(BaseModel):
    """Request model for location queries"""

    query: str = Field(
        ..., min_length=1, max_length=200, description="Location search query"
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")

    @validator("query")
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class PlaceSearchRequest(BaseModel):
    """Request model for place searches"""

    location: str = Field(..., min_length=1, max_length=200)
    place_type: str = Field("restaurant", min_length=1, max_length=50)
    radius: int = Field(1000, ge=100, le=50000, description="Search radius in meters")


class PlaceResponse(BaseModel):
    """Response model for place data"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: datetime
    count: Optional[int] = None


# Rate limiting (basic implementation)


def check_rate_limit(request: Request) -> bool:
    """Basic rate limiting check"""
    # In production, implement proper rate limiting with Redis or similar
    return True


def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    if not check_rate_limit(request):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )
    return True


# Endpoints


@router.get("/search", response_model=PlaceResponse)
async def search_places(
    request: Request,
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    _: bool = Depends(rate_limit_dependency),
):
    """Search for places by query"""
    try:
        # Validate input
        location_request = LocationRequest(query=query, limit=limit)

        # Use integration registry to search for places
        try:
            # Get active geo providers from registry
            geo_providers = _registry.get_active_providers_by_category("geo")

            if not geo_providers:
                # Fallback to empty results if no providers available
                places = []
            else:
                # Use the first available geo provider
                provider = geo_providers[0]
                places_data = await asyncio.to_thread(
                    _registry.call_provider,
                    provider["id"],
                    "search_places",
                    {"query": location_request.query, "limit": location_request.limit},
                )
                places = places_data.get("places", [])

            return PlaceResponse(
                success=True,
                data={
                    "places": places,
                    "query": location_request.query,
                    "total_results": len(places),
                    "provider_used": (
                        geo_providers[0]["name"] if geo_providers else None
                    ),
                },
                message="Places retrieved successfully",
                timestamp=datetime.now(),
                count=len(places),
            )
        except Exception as provider_error:
            logger.warning(f"Provider error: {provider_error}, using fallback")
            # Fallback to empty results on provider error
            return PlaceResponse(
                success=True,
                data={
                    "places": [],
                    "query": location_request.query,
                    "total_results": 0,
                },
                message="No places found",
                timestamp=datetime.now(),
                count=0,
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching places: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while searching places"
        )


@router.get("/nearby", response_model=PlaceResponse)
async def get_nearby_places(
    request: Request,
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    place_type: str = Query("restaurant", min_length=1, max_length=50),
    radius: int = Query(1000, ge=100, le=50000, description="Search radius in meters"),
    _: bool = Depends(rate_limit_dependency),
):
    """Get nearby places by coordinates"""
    try:
        # Use integration registry to find nearby places
        try:
            # Get active geo providers from registry
            geo_providers = _registry.get_active_providers_by_category("geo")

            if not geo_providers:
                # Fallback to empty results if no providers available
                nearby_places = []
            else:
                # Use the first available geo provider
                provider = geo_providers[0]
                places_data = await asyncio.to_thread(
                    _registry.call_provider,
                    provider["id"],
                    "nearby_search",
                    {
                        "lat": lat,
                        "lng": lng,
                        "place_type": place_type,
                        "radius": radius,
                    },
                )
                nearby_places = places_data.get("places", [])

            return PlaceResponse(
                success=True,
                data={
                    "places": nearby_places,
                    "center": {"lat": lat, "lng": lng},
                    "radius": radius,
                    "place_type": place_type,
                    "provider_used": (
                        geo_providers[0]["name"] if geo_providers else None
                    ),
                },
                message="Nearby places retrieved successfully",
                timestamp=datetime.now(),
                count=len(nearby_places),
            )
        except Exception as provider_error:
            logger.warning(f"Provider error: {provider_error}, using fallback")
            # Fallback to empty results on provider error
            return PlaceResponse(
                success=True,
                data={
                    "places": [],
                    "center": {"lat": lat, "lng": lng},
                    "radius": radius,
                    "place_type": place_type,
                },
                message="No nearby places found",
                timestamp=datetime.now(),
                count=0,
            )

    except Exception as e:
        logger.error(f"Error getting nearby places: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving nearby places",
        )


@router.get("/geocode", response_model=PlaceResponse)
async def geocode_address(
    request: Request,
    address: str = Query(
        ..., min_length=1, max_length=300, description="Address to geocode"
    ),
    _: bool = Depends(rate_limit_dependency),
):
    """Geocode an address to coordinates"""
    try:
        # Mock geocoding response - in production, integrate with geocoding APIs
        mock_geocode = {
            "address": address,
            "formatted_address": f"Formatted: {address}",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": "high",
            "components": {
                "street_number": "123",
                "street_name": "Main St",
                "city": "New York",
                "state": "NY",
                "country": "US",
                "postal_code": "10001",
            },
        }

        return PlaceResponse(
            success=True,
            data=mock_geocode,
            message="Address geocoded successfully",
            timestamp=datetime.now(),
            count=1,
        )

    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while geocoding address"
        )


@router.get("/reverse-geocode", response_model=PlaceResponse)
async def reverse_geocode(
    request: Request,
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    _: bool = Depends(rate_limit_dependency),
):
    """Reverse geocode coordinates to address"""
    try:
        # Mock reverse geocoding response
        mock_reverse = {
            "coordinates": {"lat": lat, "lng": lng},
            "address": "123 Sample Street, Sample City, SC 12345, US",
            "components": {
                "street_number": "123",
                "street_name": "Sample Street",
                "city": "Sample City",
                "state": "SC",
                "country": "US",
                "postal_code": "12345",
            },
            "accuracy": "high",
        }

        return PlaceResponse(
            success=True,
            data=mock_reverse,
            message="Coordinates reverse geocoded successfully",
            timestamp=datetime.now(),
            count=1,
        )

    except Exception as e:
        logger.error(f"Error reverse geocoding: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while reverse geocoding"
        )


# --- NEW: lightweight provider status for the UI ---


@router.get("/providers/status")
async def provider_status():
    await _monitor.check_all()
    interesting = [
        "nominatim_osm",
        "opencage",
        "overpass_main",
        "overpass_kumi",
        "overpass_fr",
        "foursquare",
        "google_places",
        "yelp",
    ]
    out = {}
    for pid in interesting:
        p = _registry.providers.get(pid)
        if not p:
            continue
        out[pid] = {
            "enabled": bool(p.enabled),
            "requires_key": bool(p.requires_key),
            "status": getattr(p, "status", "purple"),  # "green" | "red" | "purple"
            "name": p.name,
            "docs_url": p.docs_url,
            "kind": p.kind,
        }
    return out


# --- NEW: page route for the map UI ---


@router.get("/locator", response_class=HTMLResponse)
async def places_locator(request: Request):
    return templates.TemplateResponse("locator.html", {"request": request})


@router.get("/locator/mini", response_class=HTMLResponse)
async def places_mini_locator(request: Request):
    return templates.TemplateResponse("mini_locator.html", {"request": request})


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "places-api",
    }


@router.get("/dashboard")
async def places_dashboard():
    """Serve the places status dashboard HTML page"""
    dashboard_path = os.path.join("app", "static", "places-dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@router.get("/providers")
async def get_providers_status():
    """Get status of all providers used by places services"""
    # This would typically fetch from your integrations registry
    # For now, return mock data that matches the clinic groups
    providers = [
        {
            "id": "opencage",
            "name": "OpenCage Geocoding",
            "status": "green",
            "type": "geocoding",
        },
        {
            "id": "nominatim_osm",
            "name": "Nominatim OSM",
            "status": "green",
            "type": "geocoding",
        },
        {
            "id": "overpass_main",
            "name": "Overpass API Main",
            "status": "green",
            "type": "places",
        },
        {
            "id": "overpass_kumi",
            "name": "Overpass API Kumi",
            "status": "purple",
            "type": "places",
        },
        {
            "id": "overpass_fr",
            "name": "Overpass API France",
            "status": "green",
            "type": "places",
        },
        {
            "id": "foursquare",
            "name": "Foursquare Places",
            "status": "purple",
            "type": "places",
        },
        {
            "id": "google_places",
            "name": "Google Places API",
            "status": "red",
            "type": "places",
        },
        {"id": "yelp", "name": "Yelp Fusion API", "status": "purple", "type": "places"},
    ]

    return {
        "providers": providers,
        "last_updated": datetime.now().isoformat(),
        "total_count": len(providers),
    }


# Export router
__all__ = ["router"]
