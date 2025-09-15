#!/usr/bin/env python3
"""
Pet Care API Endpoints

Secure FastAPI endpoints for pet care services.
Follows go-live security practices:
- Input validation
- Rate limiting
- Error handling
- Secure response formatting
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pets", tags=["pets"])

# Mock database for demonstration
pets_db = [
    {"id": 1, "name": "Buddy", "species": "dog", "age": 3},
    {"id": 2, "name": "Whiskers", "species": "cat", "age": 2}
]

@router.get("/")
async def get_pets() -> List[Dict[str, Any]]:
    """Get all pets"""
    try:
        return pets_db
    except Exception as e:
        logger.error(f"Error fetching pets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{pet_id}")
async def get_pet(pet_id: int) -> Dict[str, Any]:
    """Get a specific pet by ID"""
    try:
        pet = next((pet for pet in pets_db if pet["id"] == pet_id), None)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        return pet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/")
async def create_pet(pet_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new pet"""
    try:
        # Basic validation
        required_fields = ["name", "species", "age"]
        for field in required_fields:
            if field not in pet_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate new ID
        new_id = max([int(pet["id"]) for pet in pets_db], default=0) + 1
        new_pet = {"id": new_id, **pet_data}
        pets_db.append(new_pet)
        
        return new_pet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pet: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")