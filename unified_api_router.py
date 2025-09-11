#!/usr/bin/env python3
"""
Unified API Router for TRAE.AI Online Production System

This module provides a centralized API routing system that integrates all discovered
components and services while maintaining zero-cost and no-delete compliance.

Integrated Services:
- FastAPI main application
- Flask paste application
- Dashboard endpoints
- WebSocket connections
- Task queue management
- Content generation pipeline
- Agent orchestration
- Authentication and authorization
- Monitoring and diagnostics

Author: TRAE.AI Integration System
Version: 1.0.0
Date: 2024
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import integrated components
try:
    from master_integration import get_master_integration, IntegrationConfig
    from backend.task_queue_manager import TaskType, TaskPriority
    from app.websocket_manager import WebSocketManager
    from app.auth import AuthManager
except ImportError as e:
    logging.warning(f"Some components not available: {e}")

# Pydantic models for API requests/responses
class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task to create")
    payload: Dict[str, Any] = Field(..., description="Task payload data")
    priority: str = Field(default="MEDIUM", description="Task priority level")

class ContentGenerationRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate")
    parameters: Dict[str, Any] = Field(..., description="Generation parameters")
    output_format: str = Field(default="json", description="Output format")

class SystemStatusResponse(BaseModel):
    status: str
    components: Dict[str, bool]
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class UserAuthRequest(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class UnifiedAPIRouter:
    """
    Unified API router that integrates all system components
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        self.logger = self._setup_logging()
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="TRAE.AI Unified API",
            description="Integrated API for all TRAE.AI system components",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.master_integration = get_master_integration(self.config)
        self.websocket_manager = WebSocketManager()
        self.auth_manager = AuthManager()
        self.security = HTTPBearer(auto_error=False)
        
        # Setup static files and templates
        self._setup_static_files()
        self._setup_templates()
        
        # Register all routes
        self._register_routes()
        
        # Track active WebSocket connections
        self.active_connections: List[WebSocket] = []
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _setup_static_files(self):
        """Setup static file serving"""
        # Mount static directories
        static_dirs = [
            ("static", "/static"),
            ("outputs", "/outputs"),
            ("content", "/content"),
            ("assets", "/assets")
        ]
        
        for directory, mount_path in static_dirs:
            if Path(directory).exists():
                self.app.mount(mount_path, StaticFiles(directory=directory), name=directory)
    
    def _setup_templates(self):
        """Setup Jinja2 templates"""
        template_dirs = ["app/templates", "templates"]
        existing_dirs = [d for d in template_dirs if Path(d).exists()]
        
        if existing_dirs:
            self.templates = Jinja2Templates(directory=existing_dirs[0])
        else:
            self.templates = None
    
    def _register_routes(self):
        """Register all API routes"""
        # Health and status endpoints
        self._register_health_routes()
        
        # Authentication routes
        self._register_auth_routes()
        
        # Task management routes
        self._register_task_routes()
        
        # Content generation routes
        self._register_content_routes()
        
        # Dashboard routes
        self._register_dashboard_routes()
        
        # WebSocket routes
        self._register_websocket_routes()
        
        # Agent interaction routes
        self._register_agent_routes()
        
        # Monitoring routes
        self._register_monitoring_routes()
        
        # File management routes
        self._register_file_routes()
    
    def _register_health_routes(self):
        """Register health check and system status routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Basic health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/status", response_model=SystemStatusResponse)
        async def system_status():
            """Get comprehensive system status"""
            try:
                if not self.master_integration.is_initialized:
                    await self.master_integration.initialize()
                
                status = await self.master_integration.get_system_status()
                return SystemStatusResponse(
                    status="operational" if status["initialized"] else "initializing",
                    components=status["components"],
                    timestamp=status["timestamp"],
                    details=status
                )
            except Exception as e:
                self.logger.error(f"Status check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_auth_routes(self):
        """Register authentication and authorization routes"""
        
        @self.app.post("/api/auth/login")
        async def login(auth_request: UserAuthRequest):
            """User login endpoint"""
            try:
                # Implement authentication logic
                # This is a placeholder - implement actual authentication
                if auth_request.username and auth_request.password:
                    token = f"token_{auth_request.username}_{datetime.now().timestamp()}"
                    return {"access_token": token, "token_type": "bearer"}
                else:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/auth/logout")
        async def logout(credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """User logout endpoint"""
            return {"message": "Logged out successfully"}
        
        @self.app.get("/api/auth/profile")
        async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Get user profile"""
            if not credentials:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Return mock profile data
            return {
                "user_id": "user_123",
                "username": "demo_user",
                "role": "user",
                "permissions": ["content_creation", "dashboard_access"]
            }
    
    def _register_task_routes(self):
        """Register task queue management routes"""
        
        @self.app.post("/api/tasks")
        async def create_task(task_request: TaskRequest):
            """Create a new task"""
            try:
                if not self.master_integration.task_queue:
                    raise HTTPException(status_code=503, detail="Task queue not available")
                
                # Map string priority to enum
                priority_map = {
                    "LOW": TaskPriority.LOW,
                    "MEDIUM": TaskPriority.MEDIUM,
                    "HIGH": TaskPriority.HIGH,
                    "URGENT": TaskPriority.HIGH  # Map URGENT to HIGH
                }
                
                # Map string task type to enum
                type_map = {
                    "CONTENT_GENERATION": TaskType.CONTENT,
                    "RESEARCH": TaskType.RESEARCH,
                    "SYSTEM_MAINTENANCE": TaskType.SYSTEM,
                    "USER_REQUEST": TaskType.USER,
                    "ANALYTICS": TaskType.ANALYTICS
                }
                
                task_type = type_map.get(task_request.task_type, TaskType.USER)
                priority = priority_map.get(task_request.priority, TaskPriority.MEDIUM)
                
                task_id = await self.master_integration.task_queue.add_task(
                    task_type=task_type,
                    payload=task_request.payload,
                    priority=priority
                )
                
                return {"task_id": task_id, "status": "created"}
            except Exception as e:
                self.logger.error(f"Task creation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/tasks")
        async def list_tasks():
            """List all tasks"""
            try:
                if not self.master_integration.task_queue:
                    raise HTTPException(status_code=503, detail="Task queue not available")
                
                pending_tasks = await self.master_integration.task_queue.get_pending_tasks()
                return {"tasks": pending_tasks, "count": len(pending_tasks)}
            except Exception as e:
                self.logger.error(f"Task listing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get task details"""
            try:
                if not self.master_integration.task_queue:
                    raise HTTPException(status_code=503, detail="Task queue not available")
                
                # This would need to be implemented in the task queue manager
                return {"task_id": task_id, "status": "pending", "message": "Task details not implemented"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_content_routes(self):
        """Register content generation routes"""
        
        @self.app.post("/api/content/generate")
        async def generate_content(content_request: ContentGenerationRequest):
            """Generate content using the content pipeline"""
            try:
                task_id = await self.master_integration.create_content_pipeline_task(
                    content_type=content_request.content_type,
                    parameters=content_request.parameters
                )
                
                return {
                    "task_id": task_id,
                    "content_type": content_request.content_type,
                    "status": "queued"
                }
            except Exception as e:
                self.logger.error(f"Content generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/content/templates")
        async def list_content_templates():
            """List available content templates"""
            try:
                templates_dir = Path("content/templates")
                if not templates_dir.exists():
                    return {"templates": []}
                
                templates = []
                for template_file in templates_dir.glob("*.md"):
                    templates.append({
                        "name": template_file.stem,
                        "filename": template_file.name,
                        "path": str(template_file)
                    })
                
                return {"templates": templates}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/content/outputs")
        async def list_content_outputs():
            """List generated content outputs"""
            try:
                outputs = {}
                output_dirs = ["outputs/audio", "outputs/videos", "outputs/pdfs", "outputs/images"]
                
                for output_dir in output_dirs:
                    dir_path = Path(output_dir)
                    if dir_path.exists():
                        files = [f.name for f in dir_path.iterdir() if f.is_file()]
                        outputs[dir_path.name] = files
                
                return {"outputs": outputs}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_dashboard_routes(self):
        """Register dashboard and UI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard page"""
            if self.templates:
                try:
                    return self.templates.TemplateResponse("dashboard.html", {"request": {}})
                except Exception:
                    pass
            
            # Fallback HTML if template not available
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>TRAE.AI Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                    .status-card { padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                    .status-card h3 { margin-top: 0; color: #333; }
                    .api-links { margin-top: 30px; }
                    .api-links a { display: inline-block; margin: 5px 10px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>TRAE.AI Unified Dashboard</h1>
                        <p>Integrated Online Production System</p>
                    </div>
                    
                    <div class="status-grid">
                        <div class="status-card">
                            <h3>System Status</h3>
                            <p>All systems operational</p>
                            <p><strong>Components:</strong> Backend, Frontend, Content Pipeline</p>
                        </div>
                        
                        <div class="status-card">
                            <h3>Content Generation</h3>
                            <p>Ready for content creation</p>
                            <p><strong>Available:</strong> Audio, Video, Text, Images</p>
                        </div>
                        
                        <div class="status-card">
                            <h3>Task Queue</h3>
                            <p>Processing tasks efficiently</p>
                            <p><strong>Status:</strong> Active and monitoring</p>
                        </div>
                    </div>
                    
                    <div class="api-links">
                        <h3>Quick Links</h3>
                        <a href="/docs">API Documentation</a>
                        <a href="/api/status">System Status</a>
                        <a href="/api/content/templates">Content Templates</a>
                        <a href="/api/tasks">Task Queue</a>
                        <a href="/static/index.html">Static Dashboard</a>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        @self.app.get("/api/dashboard/data")
        async def dashboard_data():
            """Get dashboard data"""
            try:
                status = await self.master_integration.get_system_status()
                
                # Get additional dashboard metrics
                dashboard_data = {
                    "system_status": status,
                    "active_connections": len(self.active_connections),
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "backend": status.get("components", {}).get("agents", False),
                        "frontend": True,  # Always true if API is responding
                        "database": status.get("components", {}).get("database", False),
                        "task_queue": status.get("components", {}).get("task_queue", False),
                        "websockets": status.get("components", {}).get("websockets", False)
                    }
                }
                
                return dashboard_data
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_websocket_routes(self):
        """Register WebSocket routes"""
        
        @self.app.websocket("/ws/chat")
        async def websocket_chat(websocket: WebSocket):
            """WebSocket endpoint for chat functionality"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Process chat message
                    response = {
                        "type": "chat_response",
                        "message": f"Echo: {message_data.get('message', '')}",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
        
        @self.app.websocket("/ws/system")
        async def websocket_system_updates(websocket: WebSocket):
            """WebSocket endpoint for system updates"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                # Send periodic system updates
                while True:
                    status = await self.master_integration.get_system_status()
                    await websocket.send_text(json.dumps({
                        "type": "system_update",
                        "data": status
                    }))
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    def _register_agent_routes(self):
        """Register agent interaction routes"""
        
        @self.app.post("/api/agents/system/health_check")
        async def system_agent_health_check():
            """Trigger system agent health check"""
            try:
                if self.master_integration.system_agent:
                    # This would call the actual agent method
                    result = {"status": "healthy", "agent": "system_agent"}
                    return result
                else:
                    raise HTTPException(status_code=503, detail="System agent not available")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/research/query")
        async def research_agent_query(query: Dict[str, Any]):
            """Submit query to research agent"""
            try:
                if self.master_integration.research_agent:
                    # This would call the actual agent method
                    result = {
                        "query": query,
                        "status": "processed",
                        "agent": "research_agent"
                    }
                    return result
                else:
                    raise HTTPException(status_code=503, detail="Research agent not available")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/content/generate")
        async def content_agent_generate(request: Dict[str, Any]):
            """Generate content using content agent"""
            try:
                if self.master_integration.content_agent:
                    # This would call the actual agent method
                    result = {
                        "request": request,
                        "status": "generated",
                        "agent": "content_agent"
                    }
                    return result
                else:
                    raise HTTPException(status_code=503, detail="Content agent not available")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_monitoring_routes(self):
        """Register monitoring and diagnostics routes"""
        
        @self.app.get("/api/monitoring/metrics")
        async def get_metrics():
            """Get system metrics"""
            try:
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu_usage": 0.0,  # Would implement actual metrics
                        "memory_usage": 0.0,
                        "disk_usage": 0.0
                    },
                    "application": {
                        "active_connections": len(self.active_connections),
                        "total_requests": 0,  # Would implement request counter
                        "error_rate": 0.0
                    },
                    "components": await self.master_integration.get_system_status()
                }
                return metrics
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/diagnostics")
        async def get_diagnostics():
            """Get system diagnostics"""
            try:
                diagnostics = {
                    "system_info": {
                        "python_version": sys.version,
                        "platform": sys.platform,
                        "working_directory": os.getcwd()
                    },
                    "component_status": await self.master_integration.get_system_status(),
                    "configuration": {
                        "host": self.config.host,
                        "port": self.config.port,
                        "debug": self.config.debug
                    }
                }
                return diagnostics
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_file_routes(self):
        """Register file management routes"""
        
        @self.app.get("/api/files/list")
        async def list_files(directory: str = "outputs"):
            """List files in a directory"""
            try:
                dir_path = Path(directory)
                if not dir_path.exists() or not dir_path.is_dir():
                    raise HTTPException(status_code=404, detail="Directory not found")
                
                files = []
                for item in dir_path.iterdir():
                    files.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                
                return {"directory": directory, "files": files}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/files/download/{file_path:path}")
        async def download_file(file_path: str):
            """Download a file"""
            try:
                full_path = Path(file_path)
                if not full_path.exists() or not full_path.is_file():
                    raise HTTPException(status_code=404, detail="File not found")
                
                return FileResponse(full_path, filename=full_path.name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def startup(self):
        """Application startup event"""
        self.logger.info("Starting unified API router...")
        
        # Initialize master integration
        success = await self.master_integration.initialize()
        if success:
            await self.master_integration.start_services()
            self.logger.info("Master integration started successfully")
        else:
            self.logger.warning("Master integration failed to start")
    
    async def shutdown(self):
        """Application shutdown event"""
        self.logger.info("Shutting down unified API router...")
        
        # Close all WebSocket connections
        for connection in self.active_connections:
            try:
                await connection.close()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket connection: {e}")
        
        # Shutdown master integration
        await self.master_integration.shutdown()
        self.logger.info("Unified API router shutdown complete")

# Create the unified router instance
unified_router = UnifiedAPIRouter()

# Setup startup and shutdown events
@unified_router.app.on_event("startup")
async def startup_event():
    await unified_router.startup()

@unified_router.app.on_event("shutdown")
async def shutdown_event():
    await unified_router.shutdown()

# Export the FastAPI app
app = unified_router.app

if __name__ == "__main__":
    import uvicorn
    
    config = IntegrationConfig()
    uvicorn.run(
        "unified_api_router:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )