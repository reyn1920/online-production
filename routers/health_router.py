from fastapi import APIRouter
from datetime import datetime, timezone
import time, psutil
from typing import Dict, Any
from config.runtime_flags import health_cache_ttl_seconds

router = APIRouter()
_cache: Dict[str, Any] = {"ts": 0.0, "payload": None}

def _collect() -> Dict[str, Any]:
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
    except Exception:
        cpu, mem = None, None
    services = {
        "text_generation": True,
        "video_creation": True,
        "tts_engine": True,
        "avatar_generation": True,
    }
    status = "healthy" if all(services.values()) else "degraded"
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content_agent": True,
        "services": services,
        "cpu": cpu, "mem": mem,
    }

@router.get("/api/health")
async def api_health():
    now = time.time()
    ttl = health_cache_ttl_seconds()
    if _cache["payload"] is None or (now - _cache["ts"]) > ttl:
        _cache["payload"] = _collect()
        _cache["ts"] = now
    return _cache["payload"]

@router.get("/dashboard/api/health")
async def dashboard_health():
    # Same payload for dashboard health endpoint
    return await api_health()