#!/usr/bin/env python3
"""
Dashboard Router
Provides dashboard endpoints for monitoring system metrics and status.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Pydantic models
class DashboardMetrics(BaseModel):
    total_users: int
    active_sessions: int
    api_calls_today: int
    system_uptime: str
    memory_usage: float
    cpu_usage: float

class SystemStatus(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# In-memory storage for demo purposes
dashboard_data = {
    "metrics": {
        "total_users": 1250,
        "active_sessions": 45,
        "api_calls_today": 8750,
        "system_uptime": "15 days, 4 hours",
        "memory_usage": 68.5,
        "cpu_usage": 23.2
    },
    "system_status": {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "healthy",
            "api": "healthy",
            "cache": "healthy",
            "storage": "healthy"
        }
    }
}

@router.get("/", response_class=HTMLResponse)
async def get_dashboard_html():
    """Get the main dashboard HTML page"""
    try:
        logger.info("Serving dashboard HTML page")
        
        # Get current metrics
        metrics = dashboard_data["metrics"]
        status = dashboard_data["system_status"]
        
        # Safely get status string
        status_text = str(status.get("status", "unknown")).title() if isinstance(status, dict) else "Unknown"
        
        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Production Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
                .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }}
                .metric-title {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                .services {{ margin-top: 30px; }}
                .service-item {{ display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }}
                .status-active {{ color: #28a745; font-weight: bold; }}
                .nav-links {{ text-align: center; margin-top: 30px; }}
                .nav-links a {{ margin: 0 15px; color: #007bff; text-decoration: none; }}
                .nav-links a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Production Dashboard</h1>
                    <p>System Status: <span class="status-active">{status_text}</span></p>
                </div>
                
                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-title">Total Users</div>
                        <div class="metric-value">{metrics.get('total_users', 0):,}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Active Sessions</div>
                        <div class="metric-value">{metrics.get('active_sessions', 0)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">API Calls Today</div>
                        <div class="metric-value">{metrics.get('api_calls_today', 0):,}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">System Uptime</div>
                        <div class="metric-value">{metrics.get('system_uptime', 'Unknown')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Memory Usage</div>
                        <div class="metric-value">{metrics.get('memory_usage', 0)}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">CPU Usage</div>
                        <div class="metric-value">{metrics.get('cpu_usage', 0)}%</div>
                    </div>
                </div>
                
                <div class="services">
                    <h3>Service Status</h3>
        """
        
        # Add service status items
        services = status.get("services", {}) if isinstance(status, dict) else {}
        if isinstance(services, dict):
            for service, service_status in services.items():
                status_class = "status-active" if service_status == "healthy" else "status-error"
                html_content += f"""
                    <div class="service-item">
                        <span>{service.title()}</span>
                        <span class="{status_class}">{service_status.title()}</span>
                    </div>
                """
        
        html_content += """
                </div>
                
                <div class="nav-links">
                    <a href="/api/health">Health Check</a>
                    <a href="/api/metrics">Raw Metrics</a>
                    <a href="/docs">API Documentation</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail="Dashboard unavailable")

@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get current dashboard metrics"""
    try:
        logger.info("Fetching dashboard metrics")
        
        metrics_data = dashboard_data["metrics"]
        
        # Safely convert values with fallbacks
        total_users_val = metrics_data.get("total_users", 0)
        active_sessions_val = metrics_data.get("active_sessions", 0)
        api_calls_val = metrics_data.get("api_calls_today", 0)
        memory_val = metrics_data.get("memory_usage", 0)
        cpu_val = metrics_data.get("cpu_usage", 0)
        
        return DashboardMetrics(
            total_users=int(total_users_val) if isinstance(total_users_val, (int, float)) or (isinstance(total_users_val, str) and total_users_val.isdigit()) else 0,
            active_sessions=int(active_sessions_val) if isinstance(active_sessions_val, (int, float)) or (isinstance(active_sessions_val, str) and active_sessions_val.isdigit()) else 0,
            api_calls_today=int(api_calls_val) if isinstance(api_calls_val, (int, float)) or (isinstance(api_calls_val, str) and api_calls_val.isdigit()) else 0,
            system_uptime=str(metrics_data.get("system_uptime", "0 days")),
            memory_usage=float(memory_val) if isinstance(memory_val, (int, float)) or (isinstance(memory_val, str) and memory_val.replace('.', '').isdigit()) else 0.0,
            cpu_usage=float(cpu_val) if isinstance(cpu_val, (int, float)) or (isinstance(cpu_val, str) and cpu_val.replace('.', '').isdigit()) else 0.0
        )
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status"""
    try:
        logger.info("Fetching system status")
        
        status_data = dashboard_data["system_status"]
        
        services_data = status_data.get("services", {})
        services_dict = {}
        if isinstance(services_data, dict):
            services_dict = {str(k): str(v) for k, v in services_data.items()}
        
        return SystemStatus(
            status=str(status_data.get("status", "unknown")),
            timestamp=str(status_data.get("timestamp", datetime.now().isoformat())),
            services=services_dict
        )
        
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        raise HTTPException(status_code=500, detail="Status unavailable")

@router.post("/metrics/update")
async def update_metrics(new_metrics: Dict[str, Any]):
    """Update dashboard metrics"""
    try:
        logger.info(f"Updating metrics: {new_metrics}")
        
        # Update metrics in storage
        dashboard_data["metrics"].update(new_metrics)
        
        # Update timestamp
        dashboard_data["system_status"]["timestamp"] = datetime.now().isoformat()
        
        return {"message": "Metrics updated successfully", "updated_at": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metrics")