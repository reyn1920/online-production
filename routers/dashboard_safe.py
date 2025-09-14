from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
import os
from datetime import datetime
from functools import wraps

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def ok(data=None, available=True, reason=None):
    """Standard response format for dashboard endpoints"""
    out = {
        "available": bool(available),
        "timestamp": datetime.utcnow().isoformat(),
    }
    if data is not None:
        out["data"] = data
    if reason:
        out["reason"] = reason
    return out

def soft_guard(default_reason="unavailable"):
    """Decorator to ensure endpoints never return 500, always return structured response"""
    def deco(fn):
        @wraps(fn)
        async def _inner(*args, **kwargs):
            try:
                # Handle both sync and async functions
                if callable(getattr(fn, "__await__", None)):
                    data = await fn(*args, **kwargs)
                else:
                    data = fn(*args, **kwargs)
                return {
                    "available": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data,
                }
            except Exception as e:
                return {
                    "available": False,
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": f"{default_reason}: {type(e).__name__}",
                }
        return _inner
    return deco

ENABLE_DASHBOARD = os.getenv("ENABLE_DASHBOARD", "1") not in ("0", "false", "False")

@router.get("/analytics")
async def dashboard_analytics():
    """Dashboard analytics - never fails, always returns 200"""
    # Feature-flag first — still return 200 with reason
    if not ENABLE_DASHBOARD:
        return ok(available=False, reason="disabled_by_flag")

    # Hardening wrapper — NEVER raise; report truthfully
    try:
        # Example analytics payload - replace with real data
        stats = {
            "active_sessions": 0,
            "endpoints": ["/api/version", "/api/system/status", "/api/services"],
            "p95_latency_ms": 42,
            "rps": 3.1,
            "five_xx_rate": 0.0,
            "total_requests": 1000,
            "error_rate": 0.01
        }
        return ok(data=stats)
    except Exception as e:
        # Never 500; surface unavailability instead
        return ok(available=False, reason=f"unavailable: {type(e).__name__}")

@router.get("/api/health")
async def dashboard_health():
    """Dashboard health check"""
    # Keep it boring and green unless actually disabled
    return ok(
        data={"ui_bundle": "served", "spa": True}, 
        available=ENABLE_DASHBOARD
    )

@router.get("/api/status")
async def dashboard_status():
    """Dashboard status information"""
    status = {
        "ready": ENABLE_DASHBOARD,
        "widgets_loaded": ENABLE_DASHBOARD,
        "feature_flags": {"ENABLE_DASHBOARD": ENABLE_DASHBOARD},
    }
    return ok(data=status, available=ENABLE_DASHBOARD)

@router.get("/api/system-info")
async def dashboard_sysinfo():
    """Dashboard system information"""
    info = {
        "node": "local", 
        "env": os.getenv("ENVIRONMENT", "production"),
        "version": "1.0.0"
    }
    return ok(data=info, available=ENABLE_DASHBOARD)

@router.get("/api/services/{service_name}/restart")
@soft_guard("service_restart_error")
async def restart_service(service_name: str):
    """Restart service endpoint - soft guarded"""
    # This would contain actual restart logic
    # For now, just return a safe response
    return {
        "service": service_name,
        "action": "restart",
        "status": "simulated",
        "message": "Service restart simulation (not implemented)"
    }

@router.get("/settings")
@soft_guard("settings_error")
async def dashboard_settings():
    """Dashboard settings - soft guarded"""
    return {
        "theme": "dark",
        "auto_refresh": True,
        "notifications": True,
        "dashboard_enabled": ENABLE_DASHBOARD
    }