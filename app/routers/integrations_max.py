#!/usr/bin/env python3
"""
Integrations Max Router

Simplified FastAPI router for integrations.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Simple in-memory storage for demo
integrations_data = {
    "providers": {
        "openai": {"name": "OpenAI", "status": "active", "enabled": True},
        "anthropic": {"name": "Anthropic", "status": "active", "enabled": True}
    },
    "affiliates": {
        "partner1": {"name": "Partner 1", "status": "active", "commission": 0.1}
    }
}

@router.get("/")
async def get_integrations() -> Dict[str, Any]:
    """Get all integrations"""
    return integrations_data

@router.get("/providers")
async def get_providers() -> Dict[str, Any]:
    """Get all providers"""
    return integrations_data["providers"]

@router.get("/affiliates")
async def get_affiliates() -> Dict[str, Any]:
    """Get all affiliates"""
    return integrations_data["affiliates"]

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "integrations"}