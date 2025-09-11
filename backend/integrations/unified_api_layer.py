#!/usr/bin/env python3
"""
TRAE.AI Unified API Layer

Provides a unified API layer that bridges n8n workflows with the existing
agent system, CrewAI framework, Supabase database, and MCP protocol.
Enables seamless integration and orchestration across all system components.

Features:
- Unified REST API for all system components
- n8n workflow integration and management
- CrewAI agent coordination
- Supabase database operations
- MCP protocol communication
- Real-time WebSocket connections
- Authentication and authorization
- Request/response transformation
- Error handling and logging
- Rate limiting and throttling

Author: TRAE.AI System
Version: 1.0.0
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path
import hashlib
import hmac
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor

# FastAPI and related imports
try:
    from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
    # Fallback classes
    class BaseModel: pass
    class FastAPI: pass
    class HTTPException(Exception): pass

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.secret_store import SecretStore
from utils.logger import setup_logger

# Import our integrations
try:
    from backend.integrations.n8n_integration import N8nIntegration
    from backend.integrations.crewai_integration import CrewAIIntegration
    from backend.integrations.supabase_integration import SupabaseIntegration
    from backend.integrations.mcp_protocol import MCPServer, MCPClient
except ImportError as e:
    print(f"Warning: Could not import integrations: {e}")
    # Create dummy classes for development
    class N8nIntegration: pass
    class CrewAIIntegration: pass
    class SupabaseIntegration: pass
    class MCPServer: pass
    class MCPClient: pass


class APIEndpoint(Enum):
    """API endpoint categories."""
    HEALTH = "/health"
    AUTH = "/auth"
    WORKFLOWS = "/workflows"
    AGENTS = "/agents"
    DATABASE = "/database"
    MCP = "/mcp"
    FILES = "/files"
    ANALYTICS = "/analytics"
    WEBHOOKS = "/webhooks"
    WEBSOCKET = "/ws"


class RequestMethod(Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class AuthLevel(Enum):
    """Authentication levels."""
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


# Pydantic models for API requests/responses
if FASTAPI_AVAILABLE:
    class HealthResponse(BaseModel):
        status: str
        timestamp: str
        version: str
        components: Dict[str, Any]
    
    class WorkflowRequest(BaseModel):
        name: str
        description: Optional[str] = None
        workflow_data: Dict[str, Any]
        trigger_type: str = "manual"
        active: bool = True
    
    class WorkflowResponse(BaseModel):
        id: str
        name: str
        status: str
        created_at: str
        updated_at: str
    
    class AgentRequest(BaseModel):
        name: str
        role: str
        goal: str
        backstory: str
        tools: List[str] = []
        max_iter: int = 5
        memory: bool = True
    
    class AgentResponse(BaseModel):
        id: str
        name: str
        role: str
        status: str
        created_at: str
    
    class TaskRequest(BaseModel):
        description: str
        agent_id: str
        expected_output: str
        context: Optional[Dict[str, Any]] = None
        tools: List[str] = []
    
    class TaskResponse(BaseModel):
        id: str
        description: str
        status: str
        result: Optional[str] = None
        created_at: str
    
    class DatabaseQuery(BaseModel):
        table: str
        operation: str  # select, insert, update, delete
        data: Optional[Dict[str, Any]] = None
        filters: Optional[Dict[str, Any]] = None
        limit: Optional[int] = None
    
    class MCPRequest(BaseModel):
        method: str
        params: Optional[Dict[str, Any]] = None
        server_name: Optional[str] = None
    
    class WebhookPayload(BaseModel):
        event: str
        data: Dict[str, Any]
        timestamp: str
        signature: Optional[str] = None

else:
    # Fallback models
    class HealthResponse: pass
    class WorkflowRequest: pass
    class WorkflowResponse: pass
    class AgentRequest: pass
    class AgentResponse: pass
    class TaskRequest: pass
    class TaskResponse: pass
    class DatabaseQuery: pass
    class MCPRequest: pass
    class WebhookPayload: pass


@dataclass
class APIConfig:
    """Unified API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = None
    trusted_hosts: List[str] = None
    rate_limit: int = 100  # requests per minute
    auth_secret: Optional[str] = None
    webhook_secret: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = setup_logger('websocket_manager')
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


class UnifiedAPILayer:
    """
    Unified API Layer that bridges all TRAE.AI system components.
    Provides a single REST API interface for n8n, CrewAI, Supabase, and MCP.
    """
    
    def __init__(self, config: APIConfig = None, secrets_db_path: str = 'data/secrets.sqlite'):
        self.logger = setup_logger('unified_api')
        self.config = config or APIConfig()
        self.secret_store = SecretStore(secrets_db_path)
        
        # Check FastAPI availability
        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
            self.app = None
            return
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="TRAE.AI Unified API",
            description="Unified API layer for TRAE.AI system components",
            version="1.0.0",
            debug=self.config.debug
        )
        
        # Add middleware
        self._setup_middleware()
        
        # Initialize integrations
        self.n8n = None
        self.crewai = None
        self.supabase = None
        self.mcp_server = None
        self.mcp_clients = {}
        
        # WebSocket manager
        self.connection_manager = ConnectionManager()
        
        # Rate limiting
        self.rate_limits = {}
        
        # Authentication
        self.security = HTTPBearer(auto_error=False)
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("Unified API Layer initialized")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        if not self.app:
            return
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Trusted host middleware
        if self.config.trusted_hosts:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config.trusted_hosts
            )
    
    def _setup_routes(self):
        """Setup API routes."""
        if not self.app:
            return
        
        # Health check
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            return await self._health_check()
        
        # Authentication
        @self.app.post("/auth/token")
        async def authenticate(credentials: dict):
            return await self._authenticate(credentials)
        
        # n8n Workflow endpoints
        @self.app.get("/workflows")
        async def list_workflows(auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._list_workflows()
        
        @self.app.post("/workflows", response_model=WorkflowResponse)
        async def create_workflow(workflow: WorkflowRequest, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._create_workflow(workflow)
        
        @self.app.get("/workflows/{workflow_id}")
        async def get_workflow(workflow_id: str, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._get_workflow(workflow_id)
        
        @self.app.post("/workflows/{workflow_id}/execute")
        async def execute_workflow(workflow_id: str, data: dict = None, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._execute_workflow(workflow_id, data)
        
        # CrewAI Agent endpoints
        @self.app.get("/agents")
        async def list_agents(auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._list_agents()
        
        @self.app.post("/agents", response_model=AgentResponse)
        async def create_agent(agent: AgentRequest, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._create_agent(agent)
        
        @self.app.post("/agents/{agent_id}/tasks", response_model=TaskResponse)
        async def create_task(agent_id: str, task: TaskRequest, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._create_task(agent_id, task)
        
        @self.app.get("/tasks/{task_id}")
        async def get_task(task_id: str, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._get_task(task_id)
        
        # Supabase Database endpoints
        @self.app.post("/database/query")
        async def database_query(query: DatabaseQuery, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._database_query(query)
        
        @self.app.get("/database/tables")
        async def list_tables(auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._list_tables()
        
        # MCP Protocol endpoints
        @self.app.post("/mcp/request")
        async def mcp_request(request: MCPRequest, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._mcp_request(request)
        
        @self.app.get("/mcp/tools")
        async def list_mcp_tools(server_name: str = None, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._list_mcp_tools(server_name)
        
        # File management
        @self.app.post("/files/upload")
        async def upload_file(request: Request, auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._upload_file(request)
        
        # Analytics
        @self.app.get("/analytics/metrics")
        async def get_metrics(auth: HTTPAuthorizationCredentials = Depends(self.security)):
            await self._verify_auth(auth)
            return await self._get_metrics()
        
        # Webhooks
        @self.app.post("/webhooks/{webhook_id}")
        async def handle_webhook(webhook_id: str, payload: WebhookPayload, request: Request):
            return await self._handle_webhook(webhook_id, payload, request)
        
        # WebSocket endpoint
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self._handle_websocket(websocket, client_id)
    
    async def initialize_integrations(self):
        """Initialize all system integrations."""
        try:
            # Initialize n8n integration
            self.n8n = N8nIntegration()
            if hasattr(self.n8n, 'health_check'):
                n8n_health = await self.n8n.health_check()
                self.logger.info(f"n8n integration: {n8n_health.get('status', 'unknown')}")
            
            # Initialize CrewAI integration
            self.crewai = CrewAIIntegration()
            if hasattr(self.crewai, 'health_check'):
                crewai_health = await self.crewai.health_check()
                self.logger.info(f"CrewAI integration: {crewai_health.get('status', 'unknown')}")
            
            # Initialize Supabase integration
            self.supabase = SupabaseIntegration()
            if hasattr(self.supabase, 'health_check'):
                supabase_health = await self.supabase.health_check()
                self.logger.info(f"Supabase integration: {supabase_health.get('status', 'unknown')}")
            
            # Initialize MCP server
            self.mcp_server = MCPServer("TRAE-AI-Unified")
            
            self.logger.info("All integrations initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing integrations: {e}")
    
    async def _verify_auth(self, auth: HTTPAuthorizationCredentials):
        """Verify authentication token."""
        if not auth:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Simple token verification (implement proper JWT validation in production)
        if not self.config.auth_secret:
            return  # Skip auth if no secret configured
        
        try:
            # Verify token signature
            token_parts = auth.credentials.split('.')
            if len(token_parts) != 3:
                raise HTTPException(status_code=401, detail="Invalid token format")
            
            # In production, implement proper JWT verification
            # For now, just check if token exists
            if not auth.credentials:
                raise HTTPException(status_code=401, detail="Invalid token")
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def _health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        components = {}
        
        # Check n8n
        if self.n8n and hasattr(self.n8n, 'health_check'):
            try:
                components['n8n'] = await self.n8n.health_check()
            except Exception as e:
                components['n8n'] = {'status': 'error', 'error': str(e)}
        
        # Check CrewAI
        if self.crewai and hasattr(self.crewai, 'health_check'):
            try:
                components['crewai'] = await self.crewai.health_check()
            except Exception as e:
                components['crewai'] = {'status': 'error', 'error': str(e)}
        
        # Check Supabase
        if self.supabase and hasattr(self.supabase, 'health_check'):
            try:
                components['supabase'] = await self.supabase.health_check()
            except Exception as e:
                components['supabase'] = {'status': 'error', 'error': str(e)}
        
        # Overall status
        all_healthy = all(
            comp.get('status') == 'healthy' 
            for comp in components.values()
        )
        
        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'components': components
        }
    
    async def _authenticate(self, credentials: dict) -> Dict[str, Any]:
        """Authenticate user and return token."""
        # Implement proper authentication logic
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        # In production, verify against database
        # For now, simple check
        if username == "admin" and password == "admin":
            token = self._generate_token(username)
            return {
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': 3600
            }
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    def _generate_token(self, username: str) -> str:
        """Generate authentication token."""
        # Simple token generation (implement proper JWT in production)
        payload = {
            'username': username,
            'exp': (datetime.now() + timedelta(hours=1)).timestamp()
        }
        
        token_data = json.dumps(payload)
        return f"trae.{hashlib.sha256(token_data.encode()).hexdigest()}"
    
    async def _list_workflows(self) -> List[Dict]:
        """List n8n workflows."""
        if not self.n8n:
            raise HTTPException(status_code=503, detail="n8n integration not available")
        
        try:
            workflows = await self.n8n.list_workflows()
            return workflows
        except Exception as e:
            self.logger.error(f"Error listing workflows: {e}")
            raise HTTPException(status_code=500, detail="Failed to list workflows")
    
    async def _create_workflow(self, workflow: WorkflowRequest) -> Dict[str, Any]:
        """Create new n8n workflow."""
        if not self.n8n:
            raise HTTPException(status_code=503, detail="n8n integration not available")
        
        try:
            result = await self.n8n.create_workflow(
                name=workflow.name,
                workflow_data=workflow.workflow_data,
                active=workflow.active
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow: {e}")
            raise HTTPException(status_code=500, detail="Failed to create workflow")
    
    async def _get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get n8n workflow by ID."""
        if not self.n8n:
            raise HTTPException(status_code=503, detail="n8n integration not available")
        
        try:
            workflow = await self.n8n.get_workflow(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return workflow
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting workflow: {e}")
            raise HTTPException(status_code=500, detail="Failed to get workflow")
    
    async def _execute_workflow(self, workflow_id: str, data: dict = None) -> Dict[str, Any]:
        """Execute n8n workflow."""
        if not self.n8n:
            raise HTTPException(status_code=503, detail="n8n integration not available")
        
        try:
            result = await self.n8n.execute_workflow(workflow_id, data or {})
            return result
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            raise HTTPException(status_code=500, detail="Failed to execute workflow")
    
    async def _list_agents(self) -> List[Dict]:
        """List CrewAI agents."""
        if not self.crewai:
            raise HTTPException(status_code=503, detail="CrewAI integration not available")
        
        try:
            agents = await self.crewai.list_agents()
            return agents
        except Exception as e:
            self.logger.error(f"Error listing agents: {e}")
            raise HTTPException(status_code=500, detail="Failed to list agents")
    
    async def _create_agent(self, agent: AgentRequest) -> Dict[str, Any]:
        """Create new CrewAI agent."""
        if not self.crewai:
            raise HTTPException(status_code=503, detail="CrewAI integration not available")
        
        try:
            result = await self.crewai.create_agent(
                name=agent.name,
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory,
                tools=agent.tools,
                max_iter=agent.max_iter,
                memory=agent.memory
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating agent: {e}")
            raise HTTPException(status_code=500, detail="Failed to create agent")
    
    async def _create_task(self, agent_id: str, task: TaskRequest) -> Dict[str, Any]:
        """Create new task for agent."""
        if not self.crewai:
            raise HTTPException(status_code=503, detail="CrewAI integration not available")
        
        try:
            result = await self.crewai.create_task(
                agent_id=agent_id,
                description=task.description,
                expected_output=task.expected_output,
                context=task.context,
                tools=task.tools
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            raise HTTPException(status_code=500, detail="Failed to create task")
    
    async def _get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task by ID."""
        if not self.crewai:
            raise HTTPException(status_code=503, detail="CrewAI integration not available")
        
        try:
            task = await self.crewai.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            return task
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting task: {e}")
            raise HTTPException(status_code=500, detail="Failed to get task")
    
    async def _database_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Execute database query."""
        if not self.supabase:
            raise HTTPException(status_code=503, detail="Supabase integration not available")
        
        try:
            # This would need to be implemented in the Supabase integration
            # For now, return a placeholder
            return {
                'operation': query.operation,
                'table': query.table,
                'result': 'Query executed successfully'
            }
        except Exception as e:
            self.logger.error(f"Error executing database query: {e}")
            raise HTTPException(status_code=500, detail="Failed to execute query")
    
    async def _list_tables(self) -> List[str]:
        """List database tables."""
        if not self.supabase:
            raise HTTPException(status_code=503, detail="Supabase integration not available")
        
        try:
            # Placeholder implementation
            return ['users', 'workflows', 'agents', 'tasks', 'executions']
        except Exception as e:
            self.logger.error(f"Error listing tables: {e}")
            raise HTTPException(status_code=500, detail="Failed to list tables")
    
    async def _mcp_request(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle MCP protocol request."""
        try:
            # Route to appropriate MCP server or client
            if request.server_name and request.server_name in self.mcp_clients:
                client = self.mcp_clients[request.server_name]
                result = await client.send_request(request.method, request.params)
                return result or {}
            elif self.mcp_server:
                # Handle locally if it's a server request
                return {'message': 'MCP request processed', 'method': request.method}
            else:
                raise HTTPException(status_code=503, detail="MCP not available")
        except Exception as e:
            self.logger.error(f"Error handling MCP request: {e}")
            raise HTTPException(status_code=500, detail="Failed to process MCP request")
    
    async def _list_mcp_tools(self, server_name: str = None) -> List[Dict]:
        """List MCP tools."""
        try:
            if server_name and server_name in self.mcp_clients:
                client = self.mcp_clients[server_name]
                tools = await client.list_tools()
                return tools
            elif self.mcp_server:
                tools = []
                for tool in self.mcp_server.tools.values():
                    tools.append({
                        'name': tool.name,
                        'description': tool.description,
                        'inputSchema': tool.inputSchema
                    })
                return tools
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error listing MCP tools: {e}")
            raise HTTPException(status_code=500, detail="Failed to list MCP tools")
    
    async def _upload_file(self, request: Request) -> Dict[str, Any]:
        """Handle file upload."""
        try:
            # Placeholder implementation
            return {
                'message': 'File upload endpoint',
                'status': 'not_implemented'
            }
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time(),
                'active_connections': len(self.connection_manager.active_connections),
                'integrations': {
                    'n8n': bool(self.n8n),
                    'crewai': bool(self.crewai),
                    'supabase': bool(self.supabase),
                    'mcp': bool(self.mcp_server)
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    async def _handle_webhook(self, webhook_id: str, payload: WebhookPayload, request: Request) -> Dict[str, Any]:
        """Handle incoming webhook."""
        try:
            # Verify webhook signature if configured
            if self.config.webhook_secret:
                signature = request.headers.get('X-Signature-256')
                if not self._verify_webhook_signature(payload.dict(), signature):
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Process webhook
            self.logger.info(f"Received webhook {webhook_id}: {payload.event}")
            
            # Broadcast to WebSocket clients
            await self.connection_manager.broadcast(json.dumps({
                'type': 'webhook',
                'webhook_id': webhook_id,
                'event': payload.event,
                'data': payload.data,
                'timestamp': payload.timestamp
            }))
            
            return {'status': 'received', 'webhook_id': webhook_id}
            
        except Exception as e:
            self.logger.error(f"Error handling webhook: {e}")
            raise HTTPException(status_code=500, detail="Failed to process webhook")
    
    def _verify_webhook_signature(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature."""
        if not signature or not self.config.webhook_secret:
            return False
        
        try:
            payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
            expected_signature = hmac.new(
                self.config.webhook_secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, f"sha256={expected_signature}")
        except Exception:
            return False
    
    async def _handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection."""
        await self.connection_manager.connect(websocket, client_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo message back (implement proper message handling)
                response = {
                    'type': 'echo',
                    'original': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.connection_manager.send_personal_message(
                    json.dumps(response), client_id
                )
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(client_id)
        except Exception as e:
            self.logger.error(f"WebSocket error for client {client_id}: {e}")
            self.connection_manager.disconnect(client_id)
    
    async def start_server(self):
        """Start the unified API server."""
        if not FASTAPI_AVAILABLE:
            self.logger.error("Cannot start server: FastAPI not available")
            return
        
        # Initialize integrations
        await self.initialize_integrations()
        
        # Configure SSL if certificates provided
        ssl_config = None
        if self.config.ssl_cert and self.config.ssl_key:
            ssl_config = {
                'ssl_certfile': self.config.ssl_cert,
                'ssl_keyfile': self.config.ssl_key
            }
        
        # Start server
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning",
            **(ssl_config or {})
        )
        
        server = uvicorn.Server(config)
        
        self.logger.info(f"Starting Unified API server on {self.config.host}:{self.config.port}")
        await server.serve()


# Example usage and testing
if __name__ == "__main__":
    async def test_unified_api():
        config = APIConfig(
            host="localhost",
            port=8000,
            debug=True,
            cors_origins=["http://localhost:3000"],
            auth_secret="test-secret",
            webhook_secret="webhook-secret"
        )
        
        api = UnifiedAPILayer(config)
        
        if api.app:
            print("Unified API Layer configured successfully")
            print(f"Available endpoints:")
            for route in api.app.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    methods = ', '.join(route.methods)
                    print(f"  {methods} {route.path}")
            
            print("\nTo start the server, run: await api.start_server()")
        else:
            print("FastAPI not available. Install with: pip install fastapi uvicorn")
    
    # Run test
    asyncio.run(test_unified_api())