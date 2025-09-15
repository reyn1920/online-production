# main.py - FastAPI application with integrations hub

import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
import socketio

# Load environment variables
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
# BRACKET_SURGEON: disabled
# )
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from content_sources import router as content_router
from integrations_hub import _petfinder_token, lifespan, wire_integrations

load_dotenv()

# Set up logging first

# Import production initialization
from backend.production_init import get_production_manager, initialize_production_sync

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# BRACKET_SURGEON: disabled
# )
logger = logging.getLogger(__name__)

# Dynamic router loading
import importlib

ROUTER_CONFIGS = [
    {
        "modules": ["backend.api.pet_endpoints", "api.pet_endpoints"],
        "attr": "router",
        "name": "pet_router",
        "prefix": "/api/v1",
        "tags": ["pets"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.places"],
        "attr": "router",
        "name": "places_router",
        "prefix": "/places",
        "tags": ["places"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["backend.routers.social"],
        "attr": "router",
        "name": "social_router",
        "tags": ["social"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.chat", "backend.routers.chat"],
        "attr": "router",
        "name": "chat_router",
        "tags": ["chat"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["backend.routers.payment_webhooks"],
        "attr": "router",
        "name": "webhooks_router",
        "tags": ["webhooks"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["backend.routers.analytics_hub"],
        "attr": "router",
        "name": "analytics_router",
        "tags": ["analytics"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.integrations_max"],
        "attr": "router",
        "name": "integrations_max_router",
        "tags": ["integrations"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.oauth"],
        "attr": "router",
        "name": "oauth_router",
        "tags": ["oauth"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.paste"],
        "attr": "router",
        "name": "paste_router",
        "prefix": "/paste",
        "tags": ["paste"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.avatar_api"],
        "attr": "router",
        "name": "avatar_api_router",
        "prefix": "/api/avatar",
        "tags": ["avatar-api"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["master_orchestrator.main"],
        "attr": "router",
        "name": "master_orchestrator_router",
        "prefix": "/api/orchestrator",
        "tags": ["orchestrator"],
# BRACKET_SURGEON: disabled
#     },
    {
        "modules": ["app.routers.affiliate_credentials"],
        "attr": "router",
        "name": "affiliate_credentials_router",
        "prefix": "/api/affiliate",
        "tags": ["affiliate-credentials"],
# BRACKET_SURGEON: disabled
#     },
# BRACKET_SURGEON: disabled
# ]

# Load routers dynamically
loaded_routers = {}
for config in ROUTER_CONFIGS:
    router_loaded = False
    for module_name in config["modules"]:
        try:
            module = importlib.import_module(module_name)
            router = getattr(module, config["attr"])
            loaded_routers[config["name"]] = {"router": router, "config": config}
            router_loaded = True
            break
        except ImportError:
            continue

    if not router_loaded:
        loaded_routers[config["name"]] = None
        logger.warning(f"⚠️ {config['name']} not available")

# Extract individual routers for backward compatibility
pet_router = (
    loaded_routers.get("pet_router", {}).get("router") if loaded_routers.get("pet_router") else None
# BRACKET_SURGEON: disabled
# )
places_router = (
    loaded_routers.get("places_router", {}).get("router")
    if loaded_routers.get("places_router")
    else None
# BRACKET_SURGEON: disabled
# )
social_router = (
    loaded_routers.get("social_router", {}).get("router")
    if loaded_routers.get("social_router")
    else None
# BRACKET_SURGEON: disabled
# )
chat_router = (
    loaded_routers.get("chat_router", {}).get("router")
    if loaded_routers.get("chat_router")
    else None
# BRACKET_SURGEON: disabled
# )
webhooks_router = (
    loaded_routers.get("webhooks_router", {}).get("router")
    if loaded_routers.get("webhooks_router")
    else None
# BRACKET_SURGEON: disabled
# )
analytics_router = (
    loaded_routers.get("analytics_router", {}).get("router")
    if loaded_routers.get("analytics_router")
    else None
# BRACKET_SURGEON: disabled
# )
integrations_max_router = (
    loaded_routers.get("integrations_max_router", {}).get("router")
    if loaded_routers.get("integrations_max_router")
    else None
# BRACKET_SURGEON: disabled
# )
oauth_router = (
    loaded_routers.get("oauth_router", {}).get("router")
    if loaded_routers.get("oauth_router")
    else None
# BRACKET_SURGEON: disabled
# )
paste_router = (
    loaded_routers.get("paste_router", {}).get("router")
    if loaded_routers.get("paste_router")
    else None
# BRACKET_SURGEON: disabled
# )
avatar_api_router = (
    loaded_routers.get("avatar_api_router", {}).get("router")
    if loaded_routers.get("avatar_api_router")
    else None
# BRACKET_SURGEON: disabled
# )
master_orchestrator_router = (
    loaded_routers.get("master_orchestrator_router", {}).get("router")
    if loaded_routers.get("master_orchestrator_router")
    else None
# BRACKET_SURGEON: disabled
# )
affiliate_credentials_router = (
    loaded_routers.get("affiliate_credentials_router", {}).get("router")
    if loaded_routers.get("affiliate_credentials_router")
    else None
# BRACKET_SURGEON: disabled
# )

# Production initialization
try:
    logger.info("🔧 Attempting full production initialization...")
    production_manager = initialize_production_sync()
    logger.info("🚀 Production services initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Production initialization had issues: {e}")
    logger.info("🔄 Continuing with minimal production manager...")
    try:
        production_manager = get_production_manager()
        logger.info("✅ Minimal production manager ready")
    except Exception as fallback_error:
        logger.error(f"❌ Even minimal initialization failed: {fallback_error}")
        production_manager = None

# Avatar router import
try:
    from app.routers import avatar

    avatar_router = avatar.router
except ImportError:
    avatar_router = None
    logging.warning("Avatar router not available - check app structure")

# Content router import
try:
    from app.routers import content

    content_router_new = content.router
    logger.info("✅ Content router imported successfully")
except ImportError as e:
    content_router_new = None
    logger.warning(f"⚠️ Content router import failed: {e}")

# Monetization router import
try:
    from app.routers import monetization

    monetization_router = monetization.router
    logger.info("✅ Monetization router imported successfully")
except ImportError as e:
    monetization_router = None
    logger.warning(f"⚠️ Monetization router import failed: {e}")

# Monetization platform APIs import
try:
    from monetization import (
        EtsyAPI,
        GumroadAPI,
        MonetizationManager,
        PaddleAPI,
        SendOwlAPI,
# BRACKET_SURGEON: disabled
#     )

    logger.info("✅ Monetization platform APIs imported successfully")
except ImportError as e:
    MonetizationManager = None
    logger.warning(f"⚠️ Monetization platform APIs import failed: {e}")

# Financial router import
try:
    from app.routers.financial import router as financial_router

    logger.info("Financial router imported successfully")
except ImportError as e:
    financial_router = None
    logger.warning(f"Financial router not available: {e}")

# Dashboard router import
try:
    from app.routers.dashboard import router as dashboard_router

    logger.info("Dashboard router imported successfully")
except ImportError as e:
    dashboard_router = None
    logger.warning(f"Dashboard router not available: {e}")

# Comprehensive dashboard router import
try:
    from routers.comprehensive_dashboard import router as comprehensive_dashboard_router

    logger.info("Comprehensive dashboard router imported successfully")
except ImportError as e:
    comprehensive_dashboard_router = None
    logger.warning(f"Comprehensive dashboard router not available: {e}")

# Auth manager import
try:
    from app.auth import auth_manager

    logger.info("Auth manager imported successfully")
except ImportError as e:
    auth_manager = None
    logger.warning(f"Auth manager not available: {e}")

# Configuration import
try:
    from config.environment import config
    from config.validator import validate_startup_config
except ImportError:
    validate_startup_config = None
    config = None
    logging.warning("Configuration modules not available")

# Configuration validation
if validate_startup_config:
    logger.info("Validating application configuration...")
    config_valid = validate_startup_config()
    if not config_valid:
        logger.error("❌ Configuration validation failed - check logs above")
        logger.error("Application startup aborted due to configuration errors")
        exit(1)
    logger.info("✅ Configuration validation passed")
else:
    logger.warning("Configuration validator not available - skipping validation")

# FastAPI app initialization
app = FastAPI(
    title="Online Production API",
    description="Production-ready API with pet care services and affiliate processing",
    version="1.0.0",
    docs_url="/docs" if __name__ == "__main__" else None,  # Disable docs in production
    redoc_url="/redoc" if __name__ == "__main__" else None,
    lifespan=lifespan,
# BRACKET_SURGEON: disabled
# )

# Socket.IO server initialization
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app",
# BRACKET_SURGEON: disabled
#     ],
    async_mode="asgi",
    logger=True,
    engineio_logger=False,
# BRACKET_SURGEON: disabled
# )


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client {sid} connected")


@sio.event
async def disconnect(sid):
    logger.info(f"Client {sid} disconnected")


@sio.on("agent_update")
async def handle_agent_update(sid, data):
    logger.info(f"Agent update from {sid}: {data}")
    await sio.emit("agent_status", data, room=sid)


@sio.on("task_update")
async def handle_task_update(sid, data):
    logger.info(f"Task update from {sid}: {data}")
    await sio.emit("task_status", data)


@sio.on("system_alert")
async def handle_system_alert(sid, data):
    logger.warning(f"System alert from {sid}: {data}")
    await sio.emit("alert", data)


@sio.on("log_update")
async def handle_log_update(sid, data):
    await sio.emit("log_entry", data)


@sio.on("performance_update")
async def handle_performance_update(sid, data):
    await sio.emit("performance_metrics", data)


# Security
security = HTTPBearer()

# Middleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.netlify.app",
# BRACKET_SURGEON: disabled
#     ],  # Configure for production
# BRACKET_SURGEON: disabled
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app",  # Configure appropriately for production
# BRACKET_SURGEON: disabled
#     ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
# BRACKET_SURGEON: disabled
# )

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")
wire_integrations(app)  # mounts/integrations + starts background health checker
app.include_router(content_router)  # mounts/content endpoints

# Router mounting
if pet_router:
    app.include_router(pet_router, prefix="/api/v1", tags=["pets"])
    logger.info("Pet endpoints mounted at /api/v1")
else:
    logger.warning("Pet endpoints not mounted - router not available")

if places_router:
    app.include_router(places_router, prefix="/places", tags=["places"])
    logger.info("Places endpoints mounted at /places")
else:
    logger.warning("Places endpoints not mounted - router not available")

if social_router:
    app.include_router(social_router, tags=["social"])
    logger.info("Social media endpoints mounted at /social")
else:
    logger.warning("Social media endpoints not mounted - router not available")

if webhooks_router:
    app.include_router(webhooks_router, tags=["webhooks"])
    logger.info("Payment webhook endpoints mounted at /webhooks")
else:
    logger.warning("Payment webhook endpoints not mounted - router not available")

if analytics_router:
    app.include_router(analytics_router, tags=["analytics"])
    logger.info("Analytics hub endpoints mounted at /analytics")
else:
    logger.warning("Analytics hub endpoints not mounted - router not available")

if integrations_max_router:
    app.include_router(integrations_max_router, tags=["integrations"])
    logger.info("Integrations max endpoints mounted at /integrations")
else:
    logger.warning("Integrations max endpoints not mounted - router not available")

if oauth_router:
    app.include_router(oauth_router, tags=["oauth"])
    logger.info("OAuth endpoints mounted at /oauth")
else:
    logger.warning("OAuth endpoints not mounted - router not available")

if chat_router:
    app.include_router(chat_router, tags=["chat"])
    logger.info("Chat endpoints mounted at /chat")
else:
    logger.warning("Chat endpoints not mounted - router not available")

if paste_router:
    app.include_router(paste_router, prefix="/paste", tags=["paste"])
    logger.info("Paste endpoints mounted at /paste")
else:
    logger.warning("Paste endpoints not mounted - router not available")

if avatar_router:
    app.include_router(avatar_router, prefix="/avatar", tags=["avatar"])
    logger.info("Avatar endpoints mounted at /avatar")
else:
    logger.warning("Avatar endpoints not mounted - router not available")

if avatar_api_router:
    app.include_router(avatar_api_router, prefix="/api/avatar", tags=["avatar-api"])
    logger.info("Avatar API endpoints mounted at /api/avatar")
else:
    logger.warning("Avatar API endpoints not mounted - router not available")

if content_router_new:
    app.include_router(content_router_new, prefix="/api/content")
    logger.info("✅ Content router mounted at /api/content")
else:
    logger.warning("⚠️ Content router not mounted - import failed")

if monetization_router:
    app.include_router(monetization_router, prefix="/api")
    logger.info("✅ Monetization router mounted at /api/monetization")
else:
    logger.warning("⚠️ Monetization router not mounted - import failed")

if financial_router:
    app.include_router(financial_router, prefix="/api/financial", tags=["financial"])
    logger.info("Financial router mounted at /api/financial")
else:
    logger.warning("Financial router not mounted - service unavailable")

if dashboard_router:
    app.include_router(dashboard_router, tags=["dashboard"])
    logger.info("Dashboard router mounted at /dashboard")
else:
    logger.warning("Dashboard router not mounted - service unavailable")

if comprehensive_dashboard_router:
    app.include_router(
        comprehensive_dashboard_router,
        prefix="/api/comprehensive",
        tags=["comprehensive-dashboard"],
# BRACKET_SURGEON: disabled
#     )
    logger.info("Comprehensive dashboard router mounted at /api/comprehensive")
else:
    logger.warning("Comprehensive dashboard router not mounted - service unavailable")

if True:  # Always try to mount auth
    try:
        from app.routers.auth import router as auth_router

        app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
        logger.info("Auth endpoints mounted at /api/auth")
    except ImportError:
        logger.warning("Auth router not available - check app structure")
else:
    logger.warning("Auth manager not available - authentication disabled")

if master_orchestrator_router:
    app.include_router(
        master_orchestrator_router, prefix="/api/orchestrator", tags=["orchestrator"]
# BRACKET_SURGEON: disabled
#     )
    logger.info("✅ Master Orchestrator endpoints mounted at /api/orchestrator")
else:
    logger.warning("⚠️ Master Orchestrator endpoints not mounted - router not available")

if affiliate_credentials_router:
    app.include_router(
        affiliate_credentials_router,
        prefix="/api/affiliate",
        tags=["affiliate-credentials"],
# BRACKET_SURGEON: disabled
#     )
    logger.info("✅ Affiliate Credentials endpoints mounted at /api/affiliate")
else:
    logger.warning("⚠️ Affiliate Credentials endpoints not mounted - router not available")

# Monetization manager initialization
monetization_manager = None
if MonetizationManager:
    try:
        monetization_manager = MonetizationManager()
        logger.info("✅ Monetization manager initialized")
    except Exception as e:
        logger.warning(f"⚠️ Monetization manager initialization failed: {e}")

# Backend app integration
try:
    from backend.app import app as backend_app

    for route in backend_app.routes:
        app.routes.append(route)
    logger.info("✅ Backend app routes integrated")
except ImportError as e:
    logger.warning(f"⚠️ Backend app not available: {e}")
except Exception as e:
    logger.warning(f"⚠️ Backend app integration failed: {e}")


# WebSocket Manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.client_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if client_id:
            self.client_connections[client_id] = websocket
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from client connections if exists
        client_to_remove = None
        for client_id, ws in self.client_connections.items():
            if ws == websocket:
                client_to_remove = client_id
                break
        if client_to_remove:
            del self.client_connections[client_to_remove]

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def handle_client_message(self, websocket: WebSocket, message: dict):
        message_type = message.get("type")

        if message_type == "ping":
            await self.send_personal_message({"type": "pong"}, websocket)
        elif message_type == "subscribe":
            # Handle subscription logic
            await self.send_personal_message(
                {"type": "subscription_confirmed", "channel": message.get("channel")},
                websocket,
# BRACKET_SURGEON: disabled
#             )
        else:
            # Echo back for now
            await self.send_personal_message(message, websocket)

    def get_connection_count(self):
        return len(self.active_connections)

    def get_connection_info(self):
        return {
            "total_connections": len(self.active_connections),
            "client_connections": len(self.client_connections),
# BRACKET_SURGEON: disabled
#         }

    async def start_heartbeat(self):
        while True:
            await asyncio.sleep(30)
            await self.broadcast({"type": "heartbeat", "timestamp": datetime.now().isoformat()})


websocket_manager = WebSocketManager()


# Real-time updates simulation
async def simulate_real_time_updates():
    while True:
        await asyncio.sleep(5)
        await websocket_manager.broadcast(
            {
                "type": "system_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": websocket_manager.get_connection_count(),
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )


# WebSocket endpoints
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            await websocket_manager.handle_client_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@app.get("/ws/info")
async def websocket_info():
    return {
        "websocket_endpoint": "/ws/dashboard",
        "connection_info": websocket_manager.get_connection_info(),
# BRACKET_SURGEON: disabled
#     }


# HTML page endpoints
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request, "title": "Chat Interface"})


@app.get("/paste", response_class=HTMLResponse)
async def paste_page(request: Request):
    return templates.TemplateResponse(
        "paste.html",
        {
            "request": request,
            "title": "Paste Service",
            "description": "Secure text sharing service",
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )


@app.get("/comprehensive-dashboard", response_class=HTMLResponse)
async def comprehensive_dashboard_page(request: Request):
    return templates.TemplateResponse("comprehensive_dashboard.html", {"request": request})


@app.get("/affiliate-credentials", response_class=HTMLResponse)
async def affiliate_credentials_page(request: Request):
    return templates.TemplateResponse(
        "affiliate_credentials.html",
        {"request": request, "title": "Affiliate Credentials Management"},
# BRACKET_SURGEON: disabled
#     )


# API endpoints
@app.get("/pets/search")
async def pets_search(
    animal: str = Query("dog", pattern="^(dog|cat)$"),
    location: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
# BRACKET_SURGEON: disabled
# ):
    """Search for pets using Petfinder API"""
    try:
        if not _petfinder_token:
            raise HTTPException(status_code=503, detail="Petfinder service unavailable")

        params = {"type": animal, "limit": limit, "page": page}

        if location:
            params["location"] = location

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.petfinder.com/v2/animals",
                headers={"Authorization": f"Bearer {_petfinder_token}"},
                params=params,
# BRACKET_SURGEON: disabled
#             )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/status")
async def get_configuration_status():
    """Get the current configuration and service status"""
    return {
        "status": "operational",
        "services": {
            "petfinder": bool(_petfinder_token),
            "database": True,  # Add actual database check
            "websocket": True,
# BRACKET_SURGEON: disabled
#         },
        "configuration": {
            "environment": "production" if production_manager else "development",
            "routers_loaded": len([r for r in loaded_routers.values() if r is not None]),
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     }


@app.get("/pets/types")
async def pets_types():
    """Get available pet types from Petfinder API"""
    try:
        if not _petfinder_token:
            raise HTTPException(status_code=503, detail="Petfinder service unavailable")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.petfinder.com/v2/types",
                headers={"Authorization": f"Bearer {_petfinder_token}"},
# BRACKET_SURGEON: disabled
#             )
            response.raise_for_status()
            data = response.json()

            # Extract just the type names for easier consumption
            types = [pet_type["name"] for pet_type in data.get("types", [])]

            return {"types": types, "count": len(types), "full_data": data}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pet types: {str(e)}")


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "online-production-api",
# BRACKET_SURGEON: disabled
#     }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    import os

    services = {
        "petfinder_api": bool(_petfinder_token),
        "production_manager": production_manager is not None,
        "websocket_manager": True,
        "database": True,  # Add actual database health check
# BRACKET_SURGEON: disabled
#     }

    router_status = {}
    for name, router_info in loaded_routers.items():
        router_status[name] = router_info is not None

    system_info = {
        "python_version": os.sys.version,
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "host": os.environ.get("HOST", "localhost"),
        "port": os.environ.get("PORT", "8000"),
# BRACKET_SURGEON: disabled
#     }

    all_healthy = all(services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "routers": router_status,
        "system": system_info,
        "websocket_connections": websocket_manager.get_connection_count(),
# BRACKET_SURGEON: disabled
#     }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    critical_services = {
        "app_initialized": True,
        "routers_loaded": any(loaded_routers.values()),
        "middleware_configured": True,
# BRACKET_SURGEON: disabled
#     }

    # Check if critical dependencies are available
    try:
        # Test database connection if available
        if production_manager:
            # Add actual database readiness check here
            pass

        # Test external API connectivity
        if _petfinder_token:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.petfinder.com/v2/types",
                    headers={"Authorization": f"Bearer {_petfinder_token}"},
# BRACKET_SURGEON: disabled
#                 )
                critical_services["petfinder_api"] = response.status_code == 200
        else:
            critical_services["petfinder_api"] = False

    except Exception as e:
        logger.warning(f"Readiness check failed for external services: {e}")
        critical_services["external_apis"] = False

    is_ready = all(critical_services.values())

    return {
        "ready": is_ready,
        "timestamp": datetime.now().isoformat(),
        "checks": critical_services,
# BRACKET_SURGEON: disabled
#     }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    try:
        # Basic application liveness checks
        checks = {
            "app_responsive": True,
            "memory_usage": "ok",  # Add actual memory check
            "websocket_manager": websocket_manager is not None,
# BRACKET_SURGEON: disabled
#         }

        return {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
# BRACKET_SURGEON: disabled
#         }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            "alive": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
# BRACKET_SURGEON: disabled
#         }


@app.get("/api/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "build": "production",
        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


@app.get("/version")
async def get_version_alias():
    """Alias for version endpoint"""
    return await get_version()


@app.get("/api/system/metrics")
async def get_system_metrics_direct():
    """Get system metrics directly"""
    import psutil
    import os

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Application metrics
        process = psutil.Process(os.getpid())
        app_memory = process.memory_info()

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
# BRACKET_SURGEON: disabled
#             },
            "application": {
                "memory_rss": app_memory.rss,
                "memory_vms": app_memory.vms,
                "websocket_connections": websocket_manager.get_connection_count(),
                "active_routers": len([r for r in loaded_routers.values() if r is not None]),
# BRACKET_SURGEON: disabled
#             },
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    except ImportError:
        return {
            "error": "psutil not available",
            "basic_metrics": {
                "websocket_connections": websocket_manager.get_connection_count(),
                "active_routers": len([r for r in loaded_routers.values() if r is not None]),
# BRACKET_SURGEON: disabled
#             },
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }
    except Exception as e:
        return {
            "error": f"Metrics collection failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }


@app.get("/api/services")
async def get_services_status():
    """Get status of all services"""
    services = {
        "petfinder": bool(_petfinder_token),
        "production_manager": production_manager is not None,
        "websocket_manager": True,
        "monetization_manager": monetization_manager is not None,
# BRACKET_SURGEON: disabled
#     }

    routers = {name: info is not None for name, info in loaded_routers.items()}

    return {
        "services": services,
        "routers": routers,
        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


@app.get("/api/system-info")
async def get_system_info():
    """Get system information"""
    import os
    import platform

    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
# BRACKET_SURGEON: disabled
#         },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
# BRACKET_SURGEON: disabled
#         },
        "environment": {
            "host": os.environ.get("HOST", "localhost"),
            "port": os.environ.get("PORT", "8000"),
            "environment": os.environ.get("ENVIRONMENT", "development"),
# BRACKET_SURGEON: disabled
#         },
        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


@app.get("/dashboard/api/metrics")
async def get_dashboard_metrics():
    """Dashboard-specific metrics endpoint"""
    return await get_system_metrics_direct()


@app.get("/dashboard/api/services")
async def get_dashboard_services():
    """Dashboard-specific services endpoint"""
    return await get_services_status()


@app.get("/dashboard/api/system-info")
async def get_dashboard_system_info():
    """Dashboard-specific system info endpoint"""
    return await get_system_info()


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info("🚀 Application startup initiated")

    # Start background tasks
    asyncio.create_task(simulate_real_time_updates())
    asyncio.create_task(websocket_manager.start_heartbeat())

    # Log configuration status
    logger.info(f"📊 Loaded routers: {len([r for r in loaded_routers.values() if r is not None])}")
    logger.info("🔌 WebSocket manager initialized")
    logger.info(f"🏭 Production manager: {'✅' if production_manager else '❌'}")
    logger.info(f"🐾 Petfinder API: {'✅' if _petfinder_token else '❌'}")

    if monetization_manager:
        logger.info("💰 Monetization manager: ✅")
    else:
        logger.info("💰 Monetization manager: ❌")

    logger.info("✅ Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("🛑 Application shutdown initiated")
    # Add cleanup logic here if needed
    logger.info("✅ Application shutdown completed")


# Socket.IO ASGI app
socketio_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import os
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info(f"🚀 Starting server on {host}:{port}")
    logger.info(f"📖 API docs: http://{host}:{port}/docs")
    logger.info(f"❤️ Health check: http://{host}:{port}/health")

    uvicorn.run(
        socketio_app,
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        log_level="info",
# BRACKET_SURGEON: disabled
#     )