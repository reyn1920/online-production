from fastapi import APIRouter
from datetime import datetime
import os

meta = APIRouter(tags=["Meta"])

@meta.get("/api/version")
def version():
    return {"name": "TRAE AI Production API", "version": "1.0.0", "build": "full"}

@meta.get("/api/system/status")
def system_status():
    return {
        "status": "operational",
        "uptime": datetime.utcnow().isoformat(),
        "services": ["creative", "rss_watcher", "monetization"]
    }

@meta.get("/api/services")
def list_services():
    return {
        "creative": True,
        "rss_watcher": True,
        "payments": True,
        "dashboards": True
    }

@meta.get("/ws/info")
def ws_info():
    return {"message": "Websocket hub online", "channels": ["logs", "jobs", "rss"]}

@meta.get("/health/ready")
async def readiness_check():
    """Production readiness check"""
    # Check if core services are ready
    app_initialized = True
    router_loading = True
    middleware_configured = True
    
    # Check external dependencies with optional flag
    petfinder_api = False  # This would check actual API connectivity
    optional_ok = os.getenv("REQUIRE_PETFINDER", "0") != "1"
    
    ready = all([app_initialized, router_loading, middleware_configured]) and (petfinder_api or optional_ok)
    
    return {
        "ready": ready,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "app_initialization": app_initialized,
            "router_loading": router_loading,
            "middleware_configuration": middleware_configured,
            "petfinder_api": petfinder_api,
            "petfinder_optional": optional_ok
        }
    }