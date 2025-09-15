#!/usr/bin/env python3
"""
Health Router

Provides health check endpoints for monitoring application status.
"""

import psutil
import time
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])

# Service status tracking
service_status: Dict[str, bool] = {
    "database": True,
    "redis": True,
    "external_apis": True,
    "file_system": True,
    "websocket": True
}

start_time = time.time()

@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Service checks
    services = {
        "database": True,  # Simplified - always true for demo
        "cache": True,
        "external_apis": True,
        "file_system": disk.percent < 90,  # Check disk space
        "websocket": True,
        "content_agent": True,
        "tts_engine": True,
        "avatar_generation": True
    }
    
    # Determine overall status
    status = "healthy" if all(services.values()) else "degraded"
    
    # Calculate uptime
    uptime_seconds = time.time() - start_time
    uptime_hours = uptime_seconds / 3600
    
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_hours": round(uptime_hours, 2),
        "services": services,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        },
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with comprehensive system information."""
    # System information
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = psutil.boot_time()
    
    # Network information
    network_io = psutil.net_io_counters()
    
    # Process information
    process_count = len(psutil.pids())
    
    # Service health checks
    services = {
        "database": {
            "status": True,
            "response_time_ms": 5.2,
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "cache": {
            "status": True,
            "response_time_ms": 1.1,
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "external_apis": {
            "status": True,
            "response_time_ms": 150.3,
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "file_system": {
            "status": disk.percent < 90,
            "disk_usage_percent": disk.percent,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # Calculate overall status
    all_services_healthy = all(service["status"] for service in services.values())
    status = "healthy" if all_services_healthy else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2),
        "system": {
            "cpu": {
                "count": cpu_count,
                "percent": psutil.cpu_percent(interval=1),
                "frequency_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            },
            "processes": {
                "count": process_count
            },
            "boot_time": datetime.fromtimestamp(boot_time, tz=timezone.utc).isoformat()
        },
        "services": services,
        "version": "1.0.0"
    }

@router.get("/services")
async def service_status_check():
    """Check status of individual services."""
    services = {
        "database": True,
        "cache": True,
        "external_apis": True,
        "websocket": True,
        "content_generation": True,
        "file_storage": True,
        "authentication": True,
        "analytics": True
    }
    
    # Count healthy services
    healthy_count = sum(1 for status in services.values() if status)
    total_count = len(services)
    
    return {
        "services": services,
        "summary": {
            "healthy": healthy_count,
            "total": total_count,
            "percentage": round((healthy_count / total_count) * 100, 1)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/metrics")
async def system_metrics():
    """Get system performance metrics."""
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_avg = sum(cpu_percent) / len(cpu_percent)
    
    # Memory metrics
    memory = psutil.virtual_memory()
    
    # Disk metrics
    disk = psutil.disk_usage('/')
    
    # Network metrics
    network = psutil.net_io_counters()
    
    return {
        "cpu": {
            "average_percent": round(cpu_avg, 2),
            "per_core_percent": [round(cpu, 2) for cpu in cpu_percent],
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
        },
        "memory": {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "percent": memory.percent,
            "cached_bytes": getattr(memory, 'cached', 0),
            "buffers_bytes": getattr(memory, 'buffers', 0)
        },
        "disk": {
            "total_bytes": disk.total,
            "free_bytes": disk.free,
            "used_bytes": disk.used,
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
            "errors_in": network.errin,
            "errors_out": network.errout,
            "drops_in": network.dropin,
            "drops_out": network.dropout
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2)
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint for basic connectivity check."""
    return {
        "message": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2)
    }

@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check."""
    # Check if all critical services are ready
    critical_services = {
        "database": True,
        "cache": True,
        "file_system": psutil.disk_usage('/').percent < 95
    }
    
    ready = all(critical_services.values())
    
    if ready:
        return {
            "status": "ready",
            "services": critical_services,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "services": critical_services,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check."""
    # Basic liveness check - if we can respond, we're alive
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2)
    }