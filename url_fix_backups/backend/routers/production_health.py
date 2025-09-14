#!/usr / bin / env python3
"""
Production Health Check Router
Implements comprehensive health monitoring for go - live requirements
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import psutil
import requests
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

production_health_router = APIRouter()


class ProductionHealthMonitor:
    """Comprehensive health monitoring for production environment"""

    def __init__(self):
        self.start_time = time.time()
        self.health_cache = {}
        self.cache_ttl = 30  # 30 seconds cache
        self.last_check = 0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "load_avg": (
                        list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None
                    ),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "uptime_seconds": int(time.time() - self.start_time),
            }
        except Exception as e:
            return {"error": f"Failed to get system metrics: {str(e)}"}

    def check_service_health(self, service_url: str, timeout: int = 5) -> Dict[str, Any]:
        """Check health of a specific service"""
        try:
            start_time = time.time()
            response = requests.get(service_url, timeout=timeout)
            response_time = time.time() - start_time

            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": round(response_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "error": "Service timeout",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_application_health(self) -> Dict[str, Any]:
        """Get application - specific health metrics"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": "production",
            "services": {},
            "dependencies": {},
            "metrics": self.get_system_metrics(),
        }

        # Check critical services
        services_to_check = [
            ("main_api", "http://localhost:8000 / api / health"),
            ("dashboard", "http://localhost:8000 / dashboard / api / health"),
        ]

        unhealthy_services = 0
        for service_name, service_url in services_to_check:
            service_health = self.check_service_health(service_url)
            health_data["services"][service_name] = service_health
            if service_health["status"] != "healthy":
                unhealthy_services += 1

        # Overall health assessment
        if unhealthy_services > 0:
            health_data["status"] = (
                "degraded" if unhealthy_services < len(services_to_check) else "unhealthy"
            )

        # System resource checks
        metrics = health_data["metrics"]
        if not isinstance(metrics, dict) or "error" in metrics:
            health_data["status"] = "degraded"
        else:
            cpu_usage = metrics.get("cpu", {}).get("usage_percent", 0)
            memory_usage = metrics.get("memory", {}).get("percent", 0)
            disk_usage = metrics.get("disk", {}).get("percent", 0)

            if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
                health_data["status"] = "degraded"
                health_data["warnings"] = []
                if cpu_usage > 90:
                    health_data["warnings"].append(f"High CPU usage: {cpu_usage}%")
                if memory_usage > 90:
                    health_data["warnings"].append(f"High memory usage: {memory_usage}%")
                if disk_usage > 90:
                    health_data["warnings"].append(f"High disk usage: {disk_usage}%")

        return health_data

    def get_cached_health(self) -> Dict[str, Any]:
        """Get health data with caching"""
        current_time = time.time()
        if current_time - self.last_check > self.cache_ttl:
            self.health_cache = self.get_application_health()
            self.last_check = current_time
        return self.health_cache


# Global health monitor instance
health_monitor = ProductionHealthMonitor()


@production_health_router.get("/api / production / health")
async def production_health_check():
    """Comprehensive production health check endpoint"""
    try:
        health_data = health_monitor.get_cached_health()

        # Determine HTTP status code based on health
        if health_data["status"] == "healthy":
            status_code = status.HTTP_200_OK
        elif health_data["status"] == "degraded":
            status_code = status.HTTP_200_OK  # Still operational
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(content=health_data, status_code=status_code)
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@production_health_router.get("/api / production / readiness")
async def readiness_check():
    """Kubernetes - style readiness probe"""
    try:
        # Quick checks for readiness
        health_data = health_monitor.get_application_health()

        if health_data["status"] in ["healthy", "degraded"]:
            return JSONResponse(
                content={"status": "ready", "timestamp": datetime.utcnow().isoformat()},
                status_code=status.HTTP_200_OK,
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@production_health_router.get("/api / production / liveness")
async def liveness_check():
    """Kubernetes - style liveness probe"""
    try:
        # Simple liveness check - just verify the service is responding
        return JSONResponse(
            content={
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": int(time.time() - health_monitor.start_time),
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@production_health_router.get("/api / production / metrics")
async def production_metrics():
    """Detailed production metrics endpoint"""
    try:
        metrics = health_monitor.get_system_metrics()
        return JSONResponse(
            content={"metrics": metrics, "timestamp": datetime.utcnow().isoformat()},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
