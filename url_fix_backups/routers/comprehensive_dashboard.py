import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import psutil
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import system monitoring components
try:

    from app.bridge_to_system import SystemBridge
    from monitoring.performance_monitor import PerformanceMonitor
        from system_monitor import SystemMonitor

except ImportError as e:
    logging.warning(f"Some monitoring components not available: {e}")
    SystemMonitor = None
    PerformanceMonitor = None
    SystemBridge = None

# Import existing modules
try:

    from backend.marketing_monetization_engine import MarketingMonetizationEngine

except ImportError:
    MarketingMonetizationEngine = None

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# WebSocket connection manager


class ConnectionManager:


    def __init__(self):
        self.active_connections: List[WebSocket] = []


    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )


    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )


    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)


    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Global variables for caching
start_time = time.time()
system_metrics_cache = {}
revenue_cache = {}
services_cache = {}
integrations_cache = {}

# Initialize monitoring components
system_monitor = None
performance_monitor = None
system_bridge = None

try:
    if SystemMonitor:
        system_monitor = SystemMonitor()
    if PerformanceMonitor:
        performance_monitor = PerformanceMonitor()
    if SystemBridge:
        system_bridge = SystemBridge()
except Exception as e:
    logging.warning(f"Failed to initialize monitoring components: {e}")

@router.get("/comprehensive - dashboard", response_class = HTMLResponse)


async def comprehensive_dashboard(request: Request):
    """Serve the comprehensive dashboard HTML page"""
    return templates.TemplateResponse(
        "comprehensive_dashboard.html", {"request": request}
    )

@router.websocket("/ws / dashboard")


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real - time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates every 5 seconds
            await asyncio.sleep(5)
            dashboard_data = await get_all_dashboard_data()
            await manager.send_personal_message(
                json.dumps({"type": "dashboard_update", "data": dashboard_data}),
                    websocket,
                    )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.get("/api / system / metrics")


async def get_system_metrics():
    """Get current system performance metrics using advanced monitoring components"""
    try:
        # Use advanced system monitoring if available
        if system_monitor:
            try:
                system_metrics = system_monitor.collect_system_metrics()
                metrics = {
                    "cpu_percent": system_metrics.cpu_percent,
                        "memory_percent": system_metrics.memory_percent,
                        "memory_used_gb": system_metrics.memory_used_gb,
                        "memory_total_gb": system_metrics.memory_total_gb,
                        "disk_percent": system_metrics.disk_usage_percent,
                        "disk_used_gb": system_metrics.disk_used_gb,
                        "disk_total_gb": system_metrics.disk_total_gb,
                        "active_connections": getattr(
                        system_metrics, "active_connections", 0
                    ),
                        "uptime_seconds": system_metrics.uptime_seconds,
                        "response_time_ms": getattr(system_metrics, "response_time_ms",
    50),
                        "health_score": getattr(system_metrics, "health_score", 100),
                        "load_average": getattr(system_metrics, "load_average", [0,
    0,
    0]),
                        "process_count": getattr(system_metrics, "process_count", 0),
                        "network_bytes_sent": getattr(
                        system_metrics, "network_bytes_sent", 0
                    ),
                        "network_bytes_recv": getattr(
                        system_metrics, "network_bytes_recv", 0
                    ),
                        "timestamp": system_metrics.timestamp,
                        }

                # Cache the metrics

                system_metrics_cache = metrics

                return metrics
            except Exception as e:
                logger.warning(
                    f"Advanced system monitoring failed, falling back to basic: {e}"
                )

        # Fallback to basic psutil monitoring
        cpu_percent = psutil.cpu_percent(interval = 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get network connections count
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            connections = 0

        # Calculate uptime
        uptime_seconds = time.time() - start_time

        # Simulate response time (in production, this would come from actual monitoring)
        response_time_ms = 50 + (cpu_percent * 2)  # Simulate correlation with CPU

        # Get additional system info
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            load_avg = [0, 0, 0]  # Windows fallback

        process_count = len(psutil.pids())

        # Network stats
        try:
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
        except Exception:
            network_bytes_sent = 0
            network_bytes_recv = 0

        metrics = {
            "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used/(1024**3),
                "memory_total_gb": memory.total/(1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used/(1024**3),
                "disk_total_gb": disk.total/(1024**3),
                "active_connections": connections,
                "uptime_seconds": uptime_seconds,
                "response_time_ms": response_time_ms,
                "health_score": 100,  # Basic fallback
            "load_average": load_avg,
                "process_count": process_count,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv,
                "timestamp": datetime.now().isoformat(),
                }

        # Cache the metrics
        system_metrics_cache = metrics

        return metrics

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get system metrics")

@router.get("/api / revenue / dashboard")


async def get_revenue_dashboard():
    """Get revenue dashboard data"""
    try:
        # Try to use the marketing monetization engine if available
        if MarketingMonetizationEngine:
            try:
                engine = MarketingMonetizationEngine()
                revenue_data = engine.get_revenue_dashboard()

                # Cache the revenue data

                revenue_cache = revenue_data

                return revenue_data
            except Exception as e:
                logger.warning(f"Error using MarketingMonetizationEngine: {e}")

        # Fallback to mock data if engine is not available
        mock_revenue_data = {
            "total_monthly_target": 10000.0,
                "total_current_revenue": 7500.0,
                "overall_progress": 75.0,
                "revenue_by_stream": {
                "digital_products": {
                    "current": 2500.0,
                        "target": 3000.0,
                        "progress": 83.3,
                        },
                    "affiliate_marketing": {
                    "current": 1800.0,
                        "target": 2000.0,
                        "progress": 90.0,
                        },
                    "consulting": {"current": 1500.0, "target": 2000.0, "progress": 75.0},
                    "courses": {"current": 1200.0, "target": 1500.0, "progress": 80.0},
                    "subscriptions": {"current": 500.0, "target": 1500.0, "progress": 33.3},
                    },
                "recent_revenue": {
                "digital_products": 450.0,
                    "affiliate_marketing": 320.0,
                    "consulting": 280.0,
                    "courses": 180.0,
                    "subscriptions": 75.0,
                    },
                "active_campaigns": 8,
                "conversion_rate": 3.2,
                "avg_order_value": 127.50,
                "customer_ltv": 450.0,
                "churn_rate": 2.1,
                "timestamp": datetime.now().isoformat(),
                }

        # Cache the mock data
        revenue_cache = mock_revenue_data

        return mock_revenue_data

    except Exception as e:
        logger.error(f"Error getting revenue dashboard: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get revenue data")

@router.get("/api / services / status")


async def get_services_status():
    """Get status of all services using advanced monitoring components"""
    try:
        # Use performance monitor if available
        if performance_monitor:
            try:
                services_data = performance_monitor.get_services_status()
                if services_data:
                    # Cache the services data

                    services_cache = services_data
                    return services_data
            except Exception as e:
                logger.warning(
                    f"Performance monitor failed, falling back to basic: {e}"
                )

        # Use system bridge if available
        if system_bridge:
            try:
                bridge_services = system_bridge.get_system_services()
                if bridge_services:
                    # Cache the services data
                    services_cache = bridge_services
                    return bridge_services
            except Exception as e:
                logger.warning(f"System bridge failed, falling back to basic: {e}")

        # Fallback to basic process monitoring
        services = {}

        # Get running processes
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info", "status"]
        ):
            try:
                proc_info = proc.info
                proc_name = proc_info["name"]

                # Filter for relevant services
                if any(
                    keyword in proc_name.lower()
                    for keyword in [
                        "python",
                            "node",
                            "nginx",
                            "apache",
                            "redis",
                            "postgres",
                            "mysql",
                            "mongodb",
                            ]
                ):

                    # Determine service status
                    status = (
                        "running"
                        if proc_info["status"] == psutil.STATUS_RUNNING
                        else "stopped"
                    )

                    # Get memory usage in MB
                    memory_mb = (
                        proc_info["memory_info"].rss / (1024 * 1024)
                        if proc_info["memory_info"]
                        else 0
                    )

                    # Simulate response time based on CPU usage
                    cpu_percent = proc_info["cpu_percent"] or 0
                    response_time_ms = 50 + (cpu_percent * 10)

                    services[f"{proc_name}_{proc_info['pid']}"] = {
                        "status": status,
                            "cpu_percent": cpu_percent,
                            "memory_mb": memory_mb,
                            "response_time_ms": response_time_ms,
                            "pid": proc_info["pid"],
                            "health_score": 100 if status == "running" else 0,
                            }

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Add some mock services if no relevant processes found
        if not services:
            services = {
                "web_server": {
                    "status": "running",
                        "cpu_percent": 15.2,
                        "memory_mb": 256.8,
                        "response_time_ms": 85,
                        "pid": 1234,
                        "health_score": 95,
                        },
                    "api_server": {
                    "status": "running",
                        "cpu_percent": 8.7,
                        "memory_mb": 128.4,
                        "response_time_ms": 45,
                        "pid": 1235,
                        "health_score": 98,
                        },
                    "database": {
                    "status": "running",
                        "cpu_percent": 5.3,
                        "memory_mb": 512.1,
                        "response_time_ms": 12,
                        "pid": 1236,
                        "health_score": 100,
                        },
                    "payment_processor": {
                    "status": "running",
                        "cpu_percent": 2.1,
                        "memory_mb": 64.2,
                        "response_time_ms": 120,
                        "pid": 1237,
                        "health_score": 92,
                        },
                    "analytics_service": {
                    "status": "running",
                        "cpu_percent": 12.8,
                        "memory_mb": 192.6,
                        "response_time_ms": 95,
                        "pid": 1238,
                        "health_score": 88,
                        },
                    }

        # Cache the services data
        services_cache = services

        return services

    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get services status")

@router.get("/api / integrations / status")


async def get_integrations_status():
    """Get status of all integrations"""
    try:
        # In a real application, this would check actual integration status
        # For now, we'll return mock data with realistic statuses
        integrations = {
            "Stripe": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 5)).isoformat(),
                    "health_score": 98,
                    "transactions_today": 47,
                    },
                "PayPal": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 8)).isoformat(),
                    "health_score": 95,
                    "transactions_today": 23,
                    },
                "Shopify": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 2)).isoformat(),
                    "health_score": 100,
                    "orders_today": 15,
                    },
                "WooCommerce": {
                "status": "warning",
                    "last_sync": (datetime.now() - timedelta(hours = 2)).isoformat(),
                    "health_score": 75,
                    "orders_today": 8,
                    },
                "Mailchimp": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 15)).isoformat(),
                    "health_score": 92,
                    "emails_sent_today": 1250,
                    },
                "Google Analytics": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 1)).isoformat(),
                    "health_score": 100,
                    "sessions_today": 2847,
                    },
                "Facebook Ads": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 10)).isoformat(),
                    "health_score": 88,
                    "spend_today": 156.78,
                    },
                "Affiliate Network": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(minutes = 30)).isoformat(),
                    "health_score": 85,
                    "commissions_today": 89.45,
                    },
                "Zapier": {
                "status": "error",
                    "last_sync": (datetime.now() - timedelta(hours = 6)).isoformat(),
                    "health_score": 0,
                    "automations_failed": 3,
                    },
                "Slack": {
                "status": "connected",
                    "last_sync": (datetime.now() - timedelta(seconds = 30)).isoformat(),
                    "health_score": 100,
                    "notifications_sent": 12,
                    },
                }

        # Cache the integrations data

        integrations_cache = integrations

        return integrations

    except Exception as e:
        logger.error(f"Error getting integrations status: {e}")
        raise HTTPException(status_code = 500,
    detail="Failed to get integrations status")

@router.get("/api / dashboard / all")


async def get_all_dashboard_data():
    """Get all dashboard data in one request"""
    try:
        # Get all data concurrently
        system_data = await get_system_metrics()
        revenue_data = await get_revenue_dashboard()
        services_data = await get_services_status()
        integrations_data = await get_integrations_status()

        return {
            "system": system_data,
                "revenue": revenue_data,
                "services": services_data,
                "integrations": integrations_data,
                "timestamp": datetime.now().isoformat(),
                }

    except Exception as e:
        logger.error(f"Error getting all dashboard data: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get dashboard data")

@router.post("/api / dashboard / alert")


async def send_dashboard_alert(alert_data: dict):
    """Send an alert to all connected dashboard clients"""
    try:
        message = json.dumps({"type": "alert", "data": alert_data})
        await manager.broadcast(message)
        return {"status": "success", "message": "Alert sent to all clients"}

    except Exception as e:
        logger.error(f"Error sending dashboard alert: {e}")
        raise HTTPException(status_code = 500, detail="Failed to send alert")

@router.get("/api / dashboard / health")


async def dashboard_health_check():
    """Comprehensive health check endpoint using advanced monitoring components"""
    try:
        # Use system bridge for comprehensive health if available
        if system_bridge:
            try:
                system_health = system_bridge.get_system_health()
                return {
                    "status": system_health.status,
                        "timestamp": system_health.timestamp.isoformat(),
                        "uptime": system_health.uptime,
                        "active_websocket_connections": len(manager.active_connections),
                        "components": system_health.components,
                        "memory_usage": system_health.memory_usage,
                        "active_agents": system_health.active_agents,
                        "queue_size": system_health.queue_size,
                        "health_score": system_bridge._get_system_health_score(),
                        }
            except Exception as e:
                logger.warning(f"System bridge health check failed, falling back: {e}")

        # Use performance monitor if available
        if performance_monitor:
            try:
                health_status = performance_monitor.get_health_status()
                return {
                    "status": health_status["status"],
                        "timestamp": health_status["timestamp"],
                        "uptime_seconds": health_status.get(
                        "uptime_seconds", time.time() - start_time
                    ),
                        "active_websocket_connections": len(manager.active_connections),
                        "system_metrics": health_status.get("system_metrics", {}),
                        "application_metrics": health_status.get("application_metrics", {}),
                        "alerts": health_status.get("alerts", []),
                        }
            except Exception as e:
                logger.warning(
                    f"Performance monitor health check failed, falling back: {e}"
                )

        # Fallback to basic health check
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        # Determine overall health
        health_status = "healthy"
        alerts = []

        if cpu_percent > 80 or memory_percent > 80:
            health_status = "warning"
            if cpu_percent > 80:
                alerts.append(
                    {"type": "high_cpu", "severity": "warning", "value": cpu_percent}
                )
            if memory_percent > 80:
                alerts.append(
                    {
                        "type": "high_memory",
                            "severity": "warning",
                            "value": memory_percent,
                            }
                )

        if cpu_percent > 95 or memory_percent > 95:
            health_status = "critical"
            alerts = [alert for alert in alerts if alert["severity"] != "warning"]
            if cpu_percent > 95:
                alerts.append(
                    {
                        "type": "critical_cpu",
                            "severity": "critical",
                            "value": cpu_percent,
                            }
                )
            if memory_percent > 95:
                alerts.append(
                    {
                        "type": "critical_memory",
                            "severity": "critical",
                            "value": memory_percent,
                            }
                )

        return {
            "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - start_time,
                "active_websocket_connections": len(manager.active_connections),
                "system_metrics": {
                "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    },
                "alerts": alerts,
                "health_score": max(0,
    100 - (cpu_percent * 0.5) - (memory_percent * 0.5)),
                }

    except Exception as e:
        logger.error(f"Error in dashboard health check: {e}")
        return {
            "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "health_score": 0,
                }

# Background task to send periodic updates


async def periodic_dashboard_updates():
    """Send periodic updates to all connected clients"""
    while True:
        try:
            await asyncio.sleep(30)  # Update every 30 seconds

            if manager.active_connections:
                dashboard_data = await get_all_dashboard_data()
                message = json.dumps(
                    {"type": "dashboard_update", "data": dashboard_data}
                )
                await manager.broadcast(message)

        except Exception as e:
            logger.error(f"Error in periodic dashboard updates: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start the background task when the module is imported
# Note: In a real application, this would be started in the main app startup
try:

    import asyncio

    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(periodic_dashboard_updates())
except Exception as e:
    logger.warning(f"Could not start periodic updates task: {e}")