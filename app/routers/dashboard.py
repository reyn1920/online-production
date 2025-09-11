#!/usr/bin/env python3
"""
Dashboard Router - FastAPI router for dashboard functionality
Integrates dashboard endpoints with the main FastAPI application
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr

from ..analytics import (analytics_engine, track_api_call, track_page_view,
                         track_user_action)
from ..auth import (Permission, User, UserRole, auth_manager, get_current_user,
                    require_permission, require_role, validate_password_strength)

# Initialize router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize templates
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# Dashboard data storage (in production, use a proper database)
dashboard_data = {
    "system_status": {
        "status": "operational",
        "uptime": "99.9%",
        "last_updated": datetime.now().isoformat(),
    },
    "metrics": {
        "total_users": 1250,
        "active_sessions": 45,
        "api_calls_today": 8750,
        "revenue_today": 2340.50,
    },
    "services": {
        "youtube_automation": {"status": "active", "last_run": "2024-01-15T10:30:00Z"},
        "content_pipeline": {"status": "active", "last_run": "2024-01-15T11:15:00Z"},
        "marketing_agent": {"status": "active", "last_run": "2024-01-15T09:45:00Z"},
        "financial_tracking": {"status": "active", "last_run": "2024-01-15T12:00:00Z"},
    },
}


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    try:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Production Dashboard",
                "data": dashboard_data,
            },
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Fallback to simple HTML response
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Production Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .header { text-align: center; margin-bottom: 40px; }
                    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
                    .metric-card { background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }
                    .metric-title { font-size: 14px; color: #666; margin-bottom: 8px; }
                    .metric-value { font-size: 24px; font-weight: bold; color: #333; }
                    .services { margin-top: 30px; }
                    .service-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }
                    .status-active { color: #28a745; font-weight: bold; }
                    .nav-links { text-align: center; margin-top: 30px; }
                    .nav-links a { margin: 0 15px; color: #007bff; text-decoration: none; }
                    .nav-links a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 Production Dashboard</h1>
                        <p>System Status: <span class="status-active">Operational</span></p>
                    </div>

                    <div class="metrics">
                        <div class="metric-card">
                            <div class="metric-title">Total Users</div>
                            <div class="metric-value">1,250</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Active Sessions</div>
                            <div class="metric-value">45</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">API Calls Today</div>
                            <div class="metric-value">8,750</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Revenue Today</div>
                            <div class="metric-value">$2,340.50</div>
                        </div>
                    </div>

                    <div class="services">
                        <h3>Service Status</h3>
                        <div class="service-item">
                            <span>YouTube Automation</span>
                            <span class="status-active">Active</span>
                        </div>
                        <div class="service-item">
                            <span>Content Pipeline</span>
                            <span class="status-active">Active</span>
                        </div>
                        <div class="service-item">
                            <span>Marketing Agent</span>
                            <span class="status-active">Active</span>
                        </div>
                        <div class="service-item">
                            <span>Financial Tracking</span>
                            <span class="status-active">Active</span>
                        </div>
                    </div>

                    <div class="nav-links">
                        <a href="/api/docs">API Documentation</a>
                        <a href="/paste">Paste Service</a>
                        <a href="/chat">Chat Interface</a>
                        <a href="/avatar">Avatar Services</a>
                    </div>

                    <div class="paste-section" style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 30px;">
                        <h3>📋 Paste Information</h3>
                        <p style="color: #666; margin-bottom: 20px;">Paste information here to share with the AI assistant:</p>
                        <form id="pasteForm" style="margin-bottom: 20px;">
                            <textarea id="pasteContent" placeholder="Paste your content here..."
                                style="width: 100%; height: 200px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; font-family: monospace; font-size: 14px; resize: vertical;"></textarea>
                            <div style="margin-top: 15px; display: flex; gap: 10px; align-items: center;">
                                <button type="submit" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">Submit Paste</button>
                                <button type="button" onclick="clearPaste()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">Clear</button>
                                <span id="pasteStatus" style="margin-left: 10px; font-size: 14px;"></span>
                            </div>
                        </form>
                        <div id="pasteHistory" style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; border-radius: 6px; padding: 15px; background: #f8f9fa;">
                            <h4 style="margin-top: 0; color: #666;">Recent Pastes:</h4>
                            <div id="pasteList">No pastes yet.</div>
                        </div>
                    </div>

                    <script>
                        let pasteHistory = JSON.parse(localStorage.getItem('pasteHistory') || '[]');

                        function updatePasteDisplay() {
                            const pasteList = document.getElementById('pasteList');
                            if (pasteHistory.length === 0) {
                                pasteList.innerHTML = 'No pastes yet.';
                                return;
                            }

                            pasteList.innerHTML = pasteHistory.slice(-5).reverse().map((paste, index) => `
                                <div style="margin-bottom: 15px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #007bff;">
                                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">${paste.timestamp}</div>
                                    <div style="font-family: monospace; font-size: 13px; max-height: 100px; overflow-y: auto; white-space: pre-wrap;">${paste.content.substring(0, 200)}${paste.content.length > 200 ? '...' : ''}</div>
                                </div>
                            `).join('');
                        }

                        function clearPaste() {
                            document.getElementById('pasteContent').value = '';
                            document.getElementById('pasteStatus').textContent = '';
                        }

                        document.getElementById('pasteForm').addEventListener('submit', async function(e) {
                            e.preventDefault();
                            const content = document.getElementById('pasteContent').value.trim();
                            const statusEl = document.getElementById('pasteStatus');

                            if (!content) {
                                statusEl.textContent = 'Please enter some content to paste.';
                                statusEl.style.color = '#dc3545';
                                return;
                            }

                            try {
                                statusEl.textContent = 'Submitting...';
                                statusEl.style.color = '#007bff';

                                const response = await fetch('/dashboard/api/paste', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({ content: content })
                                });

                                const result = await response.json();

                                if (response.ok) {
                                    // Add to history
                                    pasteHistory.push({
                                        content: content,
                                        timestamp: new Date().toLocaleString(),
                                        id: result.id || Date.now()
                                    });

                                    // Keep only last 10 pastes
                                    if (pasteHistory.length > 10) {
                                        pasteHistory = pasteHistory.slice(-10);
                                    }

                                    localStorage.setItem('pasteHistory', JSON.stringify(pasteHistory));
                                    updatePasteDisplay();

                                    statusEl.textContent = 'Paste submitted successfully!';
                                    statusEl.style.color = '#28a745';

                                    // Clear form after successful submission
                                    setTimeout(() => {
                                        clearPaste();
                                    }, 2000);
                                } else {
                                    statusEl.textContent = result.message || 'Failed to submit paste.';
                                    statusEl.style.color = '#dc3545';
                                }
                            } catch (error) {
                                statusEl.textContent = 'Error submitting paste: ' + error.message;
                                statusEl.style.color = '#dc3545';
                            }
                        });

                        // Initialize display
                        updatePasteDisplay();
                    </script>
                </div>
            </body>
            </html>
            """,
            status_code=200,
        )


@router.get("/api/status")
async def get_dashboard_status():
    """Get current dashboard status and metrics."""
    return JSONResponse(
        content={
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    return JSONResponse(
        content={
            "status": "success",
            "metrics": dashboard_data["metrics"],
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/api/services")
async def get_services_status():
    """Get status of all services."""
    return JSONResponse(
        content={
            "status": "success",
            "services": dashboard_data["services"],
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.post("/api/metrics/update")
async def update_metrics(metrics: Dict[str, Any]):
    """Update dashboard metrics."""
    try:
        dashboard_data["metrics"].update(metrics)
        dashboard_data["system_status"]["last_updated"] = datetime.now().isoformat()

        return JSONResponse(
            content={
                "status": "success",
                "message": "Metrics updated successfully",
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metrics")


@router.get("/api/system-info")
async def get_system_info():
    """Get system information."""
    try:
        import platform

        import psutil

        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "used": psutil.disk_usage("/").used,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            },
        }

        return JSONResponse(
            content={
                "status": "success",
                "system_info": system_info,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except ImportError:
        # Fallback if psutil is not available
        return JSONResponse(
            content={
                "status": "success",
                "system_info": {
                    "platform": "Unknown",
                    "message": "System monitoring not available (psutil not installed)",
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system information")


@router.post("/api/paste")
async def submit_paste(request: Request):
    """Handle paste submissions from the dashboard."""
    try:
        data = await request.json()
        content = data.get("content", "").strip()

        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        # Store paste data (in production, use a proper database)
        paste_id = f"paste_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}_{
            hash(content) %
            10000}"

        # Log the paste for the AI assistant to access
        logger.info(
            f"Paste received [{paste_id}]: {content[:100]}{'...' if len(content) > 100 else ''}"
        )

        # Store in dashboard data for retrieval
        if "pastes" not in dashboard_data:
            dashboard_data["pastes"] = []

        dashboard_data["pastes"].append(
            {
                "id": paste_id,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "length": len(content),
            }
        )

        # Keep only last 50 pastes
        if len(dashboard_data["pastes"]) > 50:
            dashboard_data["pastes"] = dashboard_data["pastes"][-50:]

        return JSONResponse(
            content={
                "status": "success",
                "message": "Paste submitted successfully",
                "id": paste_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error handling paste submission: {e}")
        raise HTTPException(status_code=500, detail="Failed to process paste")


@router.get("/api/pastes")
async def get_pastes(limit: int = 10):
    """Get recent paste submissions."""
    try:
        pastes = dashboard_data.get("pastes", [])
        recent_pastes = pastes[-limit:] if pastes else []

        return JSONResponse(
            content={
                "status": "success",
                "pastes": recent_pastes,
                "total": len(pastes),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving pastes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pastes")


@router.get("/health")
async def dashboard_health_check():
    """Dashboard health check endpoint."""
    track_api_call("/health", "GET", 200, 50)
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "dashboard",
            "timestamp": datetime.now().isoformat(),
            "uptime": "operational",
        }
    )


# Analytics Endpoints


@router.get("/api/analytics/overview")
async def get_analytics_overview(days: int = Query(7, ge=1, le=365)):
    """Get analytics overview for specified number of days"""
    try:
        track_api_call("/api/analytics/overview", "GET", 200, 150)
        overview = analytics_engine.get_dashboard_overview(days)
        return overview
    except Exception as e:
        track_api_call("/api/analytics/overview", "GET", 500, 150)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/performance")
async def get_performance_analytics(days: int = Query(7, ge=1, le=365)):
    """Get performance analytics"""
    try:
        track_api_call("/api/analytics/performance", "GET", 200, 120)
        performance = analytics_engine.get_performance_metrics(days)
        return performance
    except Exception as e:
        track_api_call("/api/analytics/performance", "GET", 500, 120)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/users")
async def get_user_analytics(days: int = Query(7, ge=1, le=365)):
    """Get user behavior analytics"""
    try:
        track_api_call("/api/analytics/users", "GET", 200, 100)
        users = analytics_engine.get_user_analytics(days)
        return users
    except Exception as e:
        track_api_call("/api/analytics/users", "GET", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/features")
async def get_feature_analytics(days: int = Query(7, ge=1, le=365)):
    """Get feature usage analytics"""
    try:
        track_api_call("/api/analytics/features", "GET", 200, 80)
        features = analytics_engine.get_feature_usage(days)
        return features
    except Exception as e:
        track_api_call("/api/analytics/features", "GET", 500, 80)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/realtime")
async def get_realtime_analytics():
    """Get real-time analytics"""
    try:
        track_api_call("/api/analytics/realtime", "GET", 200, 60)
        realtime = analytics_engine.get_real_time_stats()
        return realtime
    except Exception as e:
        track_api_call("/api/analytics/realtime", "GET", 500, 60)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/report")
async def get_analytics_report(days: int = Query(7, ge=1, le=365)):
    """Get comprehensive analytics report"""
    try:
        track_api_call("/api/analytics/report", "GET", 200, 200)
        report = analytics_engine.generate_report(days)
        return report
    except Exception as e:
        track_api_call("/api/analytics/report", "GET", 500, 200)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/export")
async def export_analytics_data(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
):
    """Export analytics data in specified format"""
    try:
        track_api_call("/api/analytics/export", "GET", 200, 300)
        data = analytics_engine.export_data(format, days)

        if format == "json":
            return JSONResponse(
                content=json.loads(data),
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_{days}days.json"
                },
            )
        else:  # CSV
            from fastapi.responses import Response

            return Response(
                content=data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_{days}days.csv"
                },
            )
    except Exception as e:
        track_api_call("/api/analytics/export", "GET", 500, 300)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/analytics/track")
async def track_custom_event(
    event_type: str = Form(...),
    properties: str = Form(None),
    user_id: str = Form(None),
    session_id: str = Form(None),
):
    """Track a custom analytics event"""
    try:
        props = json.loads(properties) if properties else {}

        from ..analytics import AnalyticsEvent

        event = AnalyticsEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            properties=props,
        )

        analytics_engine.track_event(event)
        track_api_call("/api/analytics/track", "POST", 200, 50)

        return {"status": "success", "message": "Event tracked successfully"}
    except Exception as e:
        track_api_call("/api/analytics/track", "POST", 500, 50)
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic models for request/response


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole = UserRole.VIEWER


class CreateUserRequest(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


# Authentication Endpoints


@router.post("/api/auth/login")
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        user = auth_manager.authenticate_user(request.username, request.password)
        if not user:
            track_api_call("/api/auth/login", "POST", 401, 100)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        access_token = auth_manager.create_access_token(user)
        refresh_token = auth_manager.create_refresh_token(user)

        track_api_call("/api/auth/login", "POST", 200, 150)
        track_user_action("login", user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        track_api_call("/api/auth/login", "POST", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    """Refresh access token"""
    try:
        new_access_token = auth_manager.refresh_access_token(refresh_token)
        if not new_access_token:
            track_api_call("/api/auth/refresh", "POST", 401, 50)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        track_api_call("/api/auth/refresh", "POST", 200, 50)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        track_api_call("/api/auth/refresh", "POST", 500, 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/register")
async def register(
    request: RegisterRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Register new user (admin only)"""
    try:
        # Validate password strength
        password_validation = validate_password_strength(request.password)
        if not password_validation["is_valid"]:
            track_api_call("/api/auth/register", "POST", 400, 100)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Password does not meet requirements",
                    "validation": password_validation,
                },
            )

        user = auth_manager.create_user(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            role=request.role,
        )

        track_api_call("/api/auth/register", "POST", 201, 150)
        track_user_action(
            "user_created", current_user.id, properties={"new_user_id": user.id}
        )

        return {"message": "User created successfully", "user": user.to_dict()}
    except ValueError as e:
        track_api_call("/api/auth/register", "POST", 400, 100)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        track_api_call("/api/auth/register", "POST", 500, 150)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    track_api_call("/api/auth/me", "GET", 200, 50)
    return current_user.to_dict()


@router.put("/api/auth/me")
async def update_current_user(
    request: UpdateUserRequest, current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    try:
        # Users can only update their own basic info (not role)
        allowed_updates = {}
        if request.email:
            allowed_updates["email"] = request.email
        if request.full_name:
            allowed_updates["full_name"] = request.full_name

        # Only admins can change roles and active status
        if current_user.has_permission(Permission.MANAGE_USERS):
            if request.role:
                allowed_updates["role"] = request.role
            if request.is_active is not None:
                allowed_updates["is_active"] = request.is_active

        updated_user = auth_manager.update_user(current_user.id, **allowed_updates)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        track_api_call("/api/auth/me", "PUT", 200, 100)
        track_user_action("profile_updated", current_user.id)

        return {"message": "User updated successfully", "user": updated_user.to_dict()}
    except Exception as e:
        track_api_call("/api/auth/me", "PUT", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/change-password")
async def change_password(
    request: PasswordChangeRequest, current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Verify current password
        if not auth_manager.verify_password(
            request.current_password, current_user.password_hash
        ):
            track_api_call("/api/auth/change-password", "POST", 400, 100)
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Validate new password strength
        password_validation = validate_password_strength(request.new_password)
        if not password_validation["is_valid"]:
            track_api_call("/api/auth/change-password", "POST", 400, 100)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "New password does not meet requirements",
                    "validation": password_validation,
                },
            )

        # Update password
        auth_manager.update_user(current_user.id, password=request.new_password)

        track_api_call("/api/auth/change-password", "POST", 200, 100)
        track_user_action("password_changed", current_user.id)

        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        track_api_call("/api/auth/change-password", "POST", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


# User Management Endpoints (Admin only)


@router.get("/api/users")
async def list_users(
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """List all users (admin only)"""
    try:
        users = auth_manager.list_users()
        stats = auth_manager.get_user_stats()

        track_api_call("/api/users", "GET", 200, 100)

        return {"users": users, "stats": stats}
    except Exception as e:
        track_api_call("/api/users", "GET", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/users")
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Create new user (admin only)"""
    try:
        # Validate password strength
        password_validation = validate_password_strength(request.password)
        if not password_validation["is_valid"]:
            track_api_call("/api/users", "POST", 400, 100)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Password does not meet requirements",
                    "validation": password_validation,
                },
            )

        # Check if username already exists
        existing_user = auth_manager.get_user_by_username(request.username)
        if existing_user:
            track_api_call("/api/users", "POST", 400, 100)
            raise HTTPException(status_code=400, detail="Username already exists")

        # Create the user
        new_user = auth_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
            is_active=request.is_active,
        )

        if not new_user:
            track_api_call("/api/users", "POST", 500, 100)
            raise HTTPException(status_code=500, detail="Failed to create user")

        track_api_call("/api/users", "POST", 201, 100)
        track_user_action(
            "user_created", current_user.id, properties={"created_user_id": new_user.id}
        )

        return {"message": "User created successfully", "user": new_user.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        track_api_call("/api/users", "POST", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Get specific user (admin only)"""
    try:
        user = auth_manager.get_user_by_id(user_id)
        if not user:
            track_api_call(f"/api/users/{user_id}", "GET", 404, 50)
            raise HTTPException(status_code=404, detail="User not found")

        track_api_call(f"/api/users/{user_id}", "GET", 200, 50)
        return user.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        track_api_call(f"/api/users/{user_id}", "GET", 500, 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Update user (admin only)"""
    try:
        updates = {}
        if request.email:
            updates["email"] = request.email
        if request.full_name:
            updates["full_name"] = request.full_name
        if request.role:
            updates["role"] = request.role
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.password:
            # Validate password strength
            password_validation = validate_password_strength(request.password)
            if not password_validation["is_valid"]:
                track_api_call(f"/api/users/{user_id}", "PUT", 400, 100)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Password does not meet requirements",
                        "validation": password_validation,
                    },
                )
            updates["password"] = request.password

        updated_user = auth_manager.update_user(user_id, **updates)
        if not updated_user:
            track_api_call(f"/api/users/{user_id}", "PUT", 404, 100)
            raise HTTPException(status_code=404, detail="User not found")

        track_api_call(f"/api/users/{user_id}", "PUT", 200, 100)
        track_user_action(
            "user_updated", current_user.id, properties={"updated_user_id": user_id}
        )

        return {"message": "User updated successfully", "user": updated_user.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        track_api_call(f"/api/users/{user_id}", "PUT", 500, 100)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Delete user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            track_api_call(f"/api/users/{user_id}", "DELETE", 400, 50)
            raise HTTPException(
                status_code=400, detail="Cannot delete your own account"
            )

        success = auth_manager.delete_user(user_id)
        if not success:
            track_api_call(f"/api/users/{user_id}", "DELETE", 404, 50)
            raise HTTPException(status_code=404, detail="User not found")

        track_api_call(f"/api/users/{user_id}", "DELETE", 200, 50)
        track_user_action(
            "user_deleted", current_user.id, properties={"deleted_user_id": user_id}
        )

        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        track_api_call(f"/api/users/{user_id}", "DELETE", 500, 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/validate-password")
async def validate_password(password: str = Form(...)):
    """Validate password strength"""
    try:
        validation = validate_password_strength(password)
        track_api_call("/api/auth/validate-password", "POST", 200, 30)
        return validation
    except Exception as e:
        track_api_call("/api/auth/validate-password", "POST", 500, 30)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics")
async def get_analytics():
    """Get analytics data for dashboard charts"""
    try:
        # Mock analytics data - replace with real data source
        analytics_data = {
            "api_usage": {
                "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                "data": [120, 190, 300, 500, 200, 300],
            },
            "performance": {
                "labels": ["CPU", "Memory", "Disk", "Network"],
                "data": [65, 45, 30, 25],
            },
            "user_activity": {
                "total_users": 1247,
                "active_sessions": 89,
                "new_users_today": 23,
                "bounce_rate": 34.5,
            },
            "revenue": {"today": 2847.50, "this_month": 45230.75, "growth": 12.3},
        }
        return {"analytics": analytics_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/logs")
async def get_logs(level: str = "all", limit: int = 100):
    """Get system logs with optional filtering"""
    try:
        # Mock log data - replace with real log aggregation
        import random
        from datetime import datetime, timedelta

        log_levels = ["info", "warning", "error", "debug"]
        if level != "all" and level in log_levels:
            filtered_levels = [level]
        else:
            filtered_levels = log_levels

        logs = []
        for i in range(min(limit, 50)):
            log_level = random.choice(filtered_levels)
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 1440))

            messages = {
                "info": [
                    "User logged in successfully",
                    "API request processed",
                    "Cache updated",
                    "Backup completed",
                ],
                "warning": [
                    "High memory usage detected",
                    "Slow query detected",
                    "Rate limit approaching",
                ],
                "error": [
                    "Database connection failed",
                    "API timeout",
                    "Authentication failed",
                ],
                "debug": ["Processing request", "Cache miss", "Query executed"],
            }

            logs.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "level": log_level,
                    "message": random.choice(messages[log_level]),
                }
            )

        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/services/{service_name}/restart")
async def restart_service(service_name: str):
    """Restart a specific service"""
    try:
        # Mock service restart - replace with actual service management
        valid_services = [
            "youtube_automation",
            "content_pipeline",
            "marketing_agent",
            "financial_tracking",
        ]

        if service_name not in valid_services:
            raise HTTPException(status_code=404, detail="Service not found")

        # Simulate restart delay
        import asyncio

        await asyncio.sleep(1)

        return {
            "status": "success",
            "message": f"Service {service_name} restarted successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/services/{service_name}/logs")
async def get_service_logs(service_name: str, limit: int = 50):
    """Get logs for a specific service"""
    try:
        # Mock service-specific logs
        import random
        from datetime import datetime, timedelta

        logs = []
        for i in range(min(limit, 20)):
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
            level = random.choice(["info", "warning", "error"])

            service_messages = {
                "youtube_automation": [
                    "Video processed",
                    "Upload completed",
                    "Thumbnail generated",
                ],
                "content_pipeline": [
                    "Content analyzed",
                    "Pipeline executed",
                    "Output generated",
                ],
                "marketing_agent": [
                    "Campaign created",
                    "Audience targeted",
                    "Metrics updated",
                ],
                "financial_tracking": [
                    "Transaction recorded",
                    "Report generated",
                    "Budget updated",
                ],
            }

            default_messages = ["Service running", "Task completed", "Status updated"]
            messages = service_messages.get(service_name, default_messages)

            logs.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "level": level,
                    "service": service_name,
                    "message": random.choice(messages),
                }
            )

        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"logs": logs, "service": service_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        import random

        performance_data = {
            "cpu": {
                "current": random.uniform(20, 80),
                "average": random.uniform(30, 60),
                "peak": random.uniform(60, 95),
            },
            "memory": {
                "used": random.uniform(2, 8),
                "total": 16,
                "percentage": random.uniform(20, 70),
            },
            "disk": {
                "used": random.uniform(50, 200),
                "total": 500,
                "percentage": random.uniform(10, 40),
            },
            "network": {
                "bytes_sent": random.randint(1000000, 10000000),
                "bytes_received": random.randint(5000000, 50000000),
                "connections": random.randint(10, 100),
            },
            "response_times": {
                "api_avg": random.uniform(50, 200),
                "db_avg": random.uniform(10, 50),
                "cache_avg": random.uniform(1, 10),
            },
        }

        return {"performance": performance_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts")
async def get_alerts():
    """Get system alerts and notifications"""
    try:
        import random
        from datetime import datetime, timedelta

        alert_types = ["info", "warning", "error", "success"]
        alerts = []

        # Generate some mock alerts
        for i in range(random.randint(0, 5)):
            alert_type = random.choice(alert_types)
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 120))

            alert_messages = {
                "info": "System backup completed successfully",
                "warning": "High CPU usage detected on server",
                "error": "Failed to connect to external API",
                "success": "All services are running normally",
            }

            alerts.append(
                {
                    "id": f"alert_{i}",
                    "type": alert_type,
                    "message": alert_messages[alert_type],
                    "timestamp": timestamp.isoformat(),
                    "read": random.choice([True, False]),
                }
            )

        alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/{alert_id}/mark-read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read"""
    try:
        # Mock alert marking - replace with actual alert management
        return {
            "status": "success",
            "message": f"Alert {alert_id} marked as read",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
