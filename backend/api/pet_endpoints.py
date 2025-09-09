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

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime
import asyncio

# Import services
try:
    from backend.services.pet_care_apis import PetCareAPIManager, VetServicesManager, APIResponse
except ImportError:
    # Fallback for development
    from services.pet_care_apis import PetCareAPIManager, VetServicesManager, APIResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/pets", tags=["pet-care"])

# Request/Response Models
class BirdObservationRequest(BaseModel):
    """Request model for bird observations"""
    region_code: str = Field(default="US", min_length=2, max_length=10)
    days_back: int = Field(default=7, ge=1, le=30)
    
    @validator('region_code')
    def validate_region_code(cls, v):
        # Basic validation for region codes
        if not v.isalnum():
            raise ValueError('Region code must be alphanumeric')
        return v.upper()

class PetSearchRequest(BaseModel):
    """Request model for pet search"""
    animal_type: str = Field(default="dog", min_length=3, max_length=20)
    location: str = Field(default="10001", min_length=5, max_length=20)
    limit: int = Field(default=20, ge=1, le=100)
    
    @validator('animal_type')
    def validate_animal_type(cls, v):
        allowed_types = ['dog', 'cat', 'rabbit', 'bird', 'horse', 'pig', 'reptile', 'small-furry']
        if v.lower() not in allowed_types:
            raise ValueError(f'Animal type must be one of: {", ".join(allowed_types)}')
        return v.lower()

class APIStatusResponse(BaseModel):
    """Response model for API status"""
    success: bool
    timestamp: datetime
    services: Dict[str, Any]
    message: str

class SecureAPIResponse(BaseModel):
    """Secure response wrapper"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: datetime
    rate_limit_info: Optional[Dict[str, Any]] = None

# Rate limiting (simple in-memory implementation)
rate_limit_store = {}

def check_rate_limit(request: Request, max_requests: int = 100, window_minutes: int = 60) -> bool:
    """Simple rate limiting check"""
    client_ip = request.client.host
    current_time = datetime.now()
    
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    
    # Clean old requests
    cutoff_time = current_time.timestamp() - (window_minutes * 60)
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip] 
        if req_time > cutoff_time
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[client_ip]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(current_time.timestamp())
    return True

def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    if not check_rate_limit(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    return True

# Endpoints
@router.get("/status", response_model=APIStatusResponse)
async def get_api_status():
    """Get status of all pet care APIs"""
    try:
        async with PetCareAPIManager() as pet_manager:
            pet_status = pet_manager.get_api_status()
        
        vet_manager = VetServicesManager()
        vet_status = vet_manager.get_service_status()
        
        return APIStatusResponse(
            success=True,
            timestamp=datetime.now(),
            services={
                "pet_care_apis": pet_status,
                "veterinary_services": vet_status
            },
            message="API status retrieved successfully"
        )
    
    except Exception as e:
        logger.error(f"Error getting API status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving API status"
        )

@router.get("/birds/observations", response_model=SecureAPIResponse)
async def get_bird_observations(
    request: Request,
    region_code: str = Query("US", min_length=2, max_length=10),
    days_back: int = Query(7, ge=1, le=30),
    _: bool = Depends(rate_limit_dependency)
):
    """Get recent bird observations from eBird API"""
    try:
        # Validate input
        bird_request = BirdObservationRequest(
            region_code=region_code,
            days_back=days_back
        )
        
        async with PetCareAPIManager() as pet_manager:
            response = await pet_manager.get_bird_observations(
                region_code=bird_request.region_code,
                days_back=bird_request.days_back
            )
        
        if not response.success:
            raise HTTPException(
                status_code=400 if "not configured" in response.error else 503,
                detail=response.error
            )
        
        return SecureAPIResponse(
            success=True,
            data={
                "observations": response.data,
                "region": bird_request.region_code,
                "days_back": bird_request.days_back
            },
            message="Bird observations retrieved successfully",
            timestamp=datetime.now(),
            rate_limit_info={
                "remaining": response.rate_limit_remaining
            } if response.rate_limit_remaining is not None else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bird observations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving bird observations"
        )

@router.get("/breeds/dogs", response_model=SecureAPIResponse)
async def get_dog_breeds(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(rate_limit_dependency)
):
    """Get dog breed information"""
    try:
        async with PetCareAPIManager() as pet_manager:
            response = await pet_manager.get_dog_breeds(limit=limit)
        
        if not response.success:
            raise HTTPException(
                status_code=400 if "not configured" in response.error else 503,
                detail=response.error
            )
        
        return SecureAPIResponse(
            success=True,
            data={
                "breeds": response.data,
                "limit": limit
            },
            message="Dog breeds retrieved successfully",
            timestamp=datetime.now(),
            rate_limit_info={
                "remaining": response.rate_limit_remaining
            } if response.rate_limit_remaining is not None else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dog breeds: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving dog breeds"
        )

@router.get("/breeds/cats", response_model=SecureAPIResponse)
async def get_cat_breeds(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(rate_limit_dependency)
):
    """Get cat breed information"""
    try:
        async with PetCareAPIManager() as pet_manager:
            response = await pet_manager.get_cat_breeds(limit=limit)
        
        if not response.success:
            raise HTTPException(
                status_code=400 if "not configured" in response.error else 503,
                detail=response.error
            )
        
        return SecureAPIResponse(
            success=True,
            data={
                "breeds": response.data,
                "limit": limit
            },
            message="Cat breeds retrieved successfully",
            timestamp=datetime.now(),
            rate_limit_info={
                "remaining": response.rate_limit_remaining
            } if response.rate_limit_remaining is not None else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cat breeds: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving cat breeds"
        )

@router.get("/adoptable", response_model=SecureAPIResponse)
async def search_adoptable_pets(
    request: Request,
    animal_type: str = Query("dog", min_length=3, max_length=20),
    location: str = Query("10001", min_length=5, max_length=20),
    limit: int = Query(20, ge=1, le=100),
    _: bool = Depends(rate_limit_dependency)
):
    """Search for adoptable pets"""
    try:
        # Validate input
        search_request = PetSearchRequest(
            animal_type=animal_type,
            location=location,
            limit=limit
        )
        
        async with PetCareAPIManager() as pet_manager:
            response = await pet_manager.search_adoptable_pets(
                animal_type=search_request.animal_type,
                location=search_request.location,
                limit=search_request.limit
            )
        
        if not response.success:
            raise HTTPException(
                status_code=400 if "not configured" in response.error else 503,
                detail=response.error
            )
        
        return SecureAPIResponse(
            success=True,
            data={
                "pets": response.data,
                "search_params": {
                    "animal_type": search_request.animal_type,
                    "location": search_request.location,
                    "limit": search_request.limit
                }
            },
            message="Adoptable pets retrieved successfully",
            timestamp=datetime.now(),
            rate_limit_info={
                "remaining": response.rate_limit_remaining
            } if response.rate_limit_remaining is not None else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching adoptable pets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while searching adoptable pets"
        )

@router.get("/vet/availability/{service}", response_model=SecureAPIResponse)
async def check_vet_availability(
    request: Request,
    service: str,
    _: bool = Depends(rate_limit_dependency)
):
    """Check availability for veterinary services"""
    try:
        # Validate service name
        allowed_services = ['vetster', 'pawp', 'airvet', 'calendly']
        if service.lower() not in allowed_services:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service. Allowed services: {', '.join(allowed_services)}"
            )
        
        vet_manager = VetServicesManager()
        response = await vet_manager.check_availability(service.lower())
        
        if not response.success:
            raise HTTPException(
                status_code=400 if "not configured" in response.error else 503,
                detail=response.error
            )
        
        return SecureAPIResponse(
            success=True,
            data=response.data,
            message=f"Availability for {service} checked successfully",
            timestamp=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking vet availability: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking vet availability"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "pet-care-api"
    }

# Export router
__all__ = ["router"]