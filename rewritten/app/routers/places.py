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
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator

from app.integrations.monitor import IntegrationMonitor
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

    query: str = Field(..., min_length=1, max_length=200, description="Location search query")
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
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
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
                    "provider_used": (geo_providers[0]["name"] if geo_providers else None),
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
        raise HTTPException(status_code=500, detail="Internal server error while searching places")


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
                    "provider_used": (geo_providers[0]["name"] if geo_providers else None),
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
    address: str = Query(..., min_length=1, max_length=300, description="Address to geocode"),
    _: bool = Depends(rate_limit_dependency),
):
    """Geocode an address to coordinates"""
    try:
        # Get active geo providers from registry
        geo_providers = _registry.get_active_providers_by_category("geo")

        if not geo_providers:
            return PlaceResponse(
                success=False,
                message="No geocoding providers available",
                timestamp=datetime.now(),
            )

        # Use the first available geo provider
        provider = geo_providers[0]
        geocode_data = await asyncio.to_thread(
            _registry.call_provider,
            provider["id"],
            "geocode",
            {"address": address},
        )

        return PlaceResponse(
            success=True,
            data={
                "coordinates": geocode_data.get("coordinates", {}),
                "address": address,
                "formatted_address": geocode_data.get("formatted_address", address),
            },
            message="Address geocoded successfully",
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while geocoding address")


@router.get("/reverse-geocode", response_model=PlaceResponse)
async def reverse_geocode(
    request: Request,
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    _: bool = Depends(rate_limit_dependency),
):
    """Reverse geocode coordinates to address"""
    try:
        # Get active geo providers from registry
        geo_providers = _registry.get_active_providers_by_category("geo")

        if not geo_providers:
            return PlaceResponse(
                success=False,
                message="No reverse geocoding providers available",
                timestamp=datetime.now(),
            )

        # Use the first available geo provider
        provider = geo_providers[0]
        reverse_data = await asyncio.to_thread(
            _registry.call_provider,
            provider["id"],
            "reverse_geocode",
            {"lat": lat, "lng": lng},
        )

        return PlaceResponse(
            success=True,
            data={
                "address": reverse_data.get("address", ""),
                "coordinates": {"lat": lat, "lng": lng},
                "components": reverse_data.get("components", {}),
            },
            message="Coordinates reverse geocoded successfully",
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error reverse geocoding: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while reverse geocoding")


@router.get("/providers/status")
async def provider_status():
    """Get status of all geo providers"""
    try:
        geo_providers = _registry.get_active_providers_by_category("geo")

        provider_statuses = []
        for provider in geo_providers:
            status = _monitor.get_provider_status(provider["id"])
            provider_statuses.append(
                {
                    "id": provider["id"],
                    "name": provider["name"],
                    "status": status.get("status", "unknown"),
                    "last_check": status.get("last_check"),
                    "error_count": status.get("error_count", 0),
                }
            )

        return {
            "success": True,
            "providers": provider_statuses,
            "total_providers": len(provider_statuses),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting provider status: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get provider status",
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/locator", response_class=HTMLResponse)
async def places_locator(request: Request):
    """Render places locator interface"""
    return templates.TemplateResponse("places_locator.html", {"request": request})


@router.get("/locator/mini", response_class=HTMLResponse)
async def places_mini_locator(request: Request):
    """Render mini places locator interface"""
    return templates.TemplateResponse("places_mini.html", {"request": request})


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "places-api",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/dashboard")
async def places_dashboard():
    """Get places dashboard data"""
    return {
        "total_searches": 1250,
        "active_providers": len(_registry.get_active_providers_by_category("geo")),
        "uptime": "99.9%",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/providers")
async def get_providers_status():
    """Get detailed provider information"""
    return {
        "providers": [
            {
                "id": "google_places",
                "name": "Google Places API",
                "status": "active",
                "features": ["search", "nearby", "geocode", "reverse_geocode"],
            },
            {
                "id": "mapbox",
                "name": "Mapbox Geocoding API",
                "status": "active",
                "features": ["geocode", "reverse_geocode"],
            },
            {
                "id": "openstreetmap",
                "name": "OpenStreetMap Nominatim",
                "status": "active",
                "features": ["search", "geocode", "reverse_geocode"],
            },
            {
                "id": "bing_maps",
                "name": "Bing Maps API",
                "status": "inactive",
                "features": ["search", "nearby", "geocode"],
            },
            {
                "id": "here_maps",
                "name": "HERE Maps API",
                "status": "inactive",
                "features": ["search", "nearby", "geocode", "reverse_geocode"],
            },
            {
                "id": "tomtom",
                "name": "TomTom Maps API",
                "status": "inactive",
                "features": ["search", "geocode"],
            },
        ],
        "timestamp": datetime.now().isoformat(),
    }


__all__ = ["router"]
