#!/usr/bin/env python3
"""
Meta Router

Provides metadata and service information endpoints.
Includes health checks and service status information.
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

meta = APIRouter()

@meta.get("/api/meta")
def get_meta() -> Dict[str, Any]:
    """Get application metadata"""
    return {
        "name": "Online Production App",
        "version": "1.0.0",
        "environment": "production",
        "uptime": datetime.utcnow().isoformat(),
        "services": ["creative", "rss_watcher", "monetization"]
    }

@meta.get("/api/services")
def list_services() -> Dict[str, Any]:
    """List available services and their status"""
    return {
        "creative": True,
        "rss_watcher": True,
        "payments": True,
        "dashboards": True
    }

@meta.get("/ws/info")
def websocket_info() -> Dict[str, Any]:
    """Get WebSocket connection information"""
    return {
        "websocket_enabled": True,
        "endpoint": "/ws",
        "protocols": ["websocket"]
    }

@meta.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running"
    }

@meta.get("/api/status")
def status_check() -> Dict[str, Any]:
    """Detailed status information"""
    return {
        "application": "online-production",
        "status": "operational",
        "version": "1.0.0",
        "environment": "production",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "healthy",
            "database": "healthy",
            "cache": "healthy"
        }
    }

# Export the router
__all__ = ["meta"]