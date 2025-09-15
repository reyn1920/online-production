#!/usr/bin/env python3
"""
Places API Router

Simplified FastAPI router for places and location-based services.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter(prefix="/places", tags=["places"])

# Simple in-memory storage for demo
places_data = {
    "cities": [
        {"id": 1, "name": "New York", "country": "USA", "lat": 40.7128, "lng": -74.0060},
        {"id": 2, "name": "London", "country": "UK", "lat": 51.5074, "lng": -0.1278},
        {"id": 3, "name": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503}
    ],
    "restaurants": [
        {"id": 1, "name": "Central Park Cafe", "city_id": 1, "rating": 4.5},
        {"id": 2, "name": "Thames View Restaurant", "city_id": 2, "rating": 4.2},
        {"id": 3, "name": "Sushi Master", "city_id": 3, "rating": 4.8}
    ]
}

class PlaceSearch(BaseModel):
    query: str
    limit: int = 10

@router.get("/")
async def get_places() -> Dict[str, Any]:
    """Get all places"""
    return places_data

@router.get("/cities")
async def get_cities() -> List[Dict[str, Any]]:
    """Get all cities"""
    return places_data["cities"]

@router.get("/cities/{city_id}")
async def get_city(city_id: int) -> Dict[str, Any]:
    """Get city by ID"""
    city = next((c for c in places_data["cities"] if c["id"] == city_id), None)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city

@router.get("/restaurants")
async def get_restaurants() -> List[Dict[str, Any]]:
    """Get all restaurants"""
    return places_data["restaurants"]

@router.post("/search")
async def search_places(search: PlaceSearch) -> Dict[str, Any]:
    """Search places by query"""
    query = search.query.lower()
    
    # Simple search in cities
    matching_cities = [
        city for city in places_data["cities"]
        if query in str(city["name"]).lower() or query in str(city["country"]).lower()
    ]
    
    # Simple search in restaurants
    matching_restaurants = [
        restaurant for restaurant in places_data["restaurants"]
        if query in str(restaurant["name"]).lower()
    ]
    
    results = {
        "cities": matching_cities[:search.limit],
        "restaurants": matching_restaurants[:search.limit],
        "total": len(matching_cities) + len(matching_restaurants)
    }
    
    return results

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "places"}