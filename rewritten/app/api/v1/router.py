"""Main API router for v1 endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Create the main API router
api_router = APIRouter(prefix="/api/v1")


@api_router.get("/status")
async def api_status():
    """Get API status."""
    return JSONResponse(content={"status": "ok", "version": "1.0.0", "message": "API is running"})


@api_router.get("/info")
async def api_info():
    """Get API information."""
    return JSONResponse(
        content={
            "name": "FastAPI Application",
            "version": "1.0.0",
            "description": "Production-ready FastAPI application",
            "endpoints": ["/api/v1/status", "/api/v1/info"],
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     )