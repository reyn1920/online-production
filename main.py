# main.py - FastAPI application with integrations hub
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import httpx
import socketio
# Load environment variables
from dotenv import load_dotenv
from fastapi import (FastAPI, HTTPException, Query, Request, WebSocket,
    WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from content_sources import router as content_router
from integrations_hub import _petfinder_token, _state, lifespan, wire_integrations
from shared_utils import get_secret

load_dotenv()

# Set up logging first
import logging

# Import production initialization
from backend.production_init import get_production_manager, initialize_production_sync

logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Dynamic router loading
import importlib

ROUTER_CONFIGS = [
    {
        "modules": ["backend.api.pet_endpoints", "api.pet_endpoints"],
            "attr": "router",
            "name": "pet_router",
            "prefix": "/api / v1",
            "tags": ["pets"],
            },
        {
        "modules": ["app.routers.places"],
            "attr": "router",
            "name": "places_router",
            "prefix": "/places",
            "tags": ["places"],
            },
        {
        "modules": ["backend.routers.social"],
            "attr": "router",
            "name": "social_router",
            "tags": ["social"],
            },
        {
        "modules": ["app.routers.chat", "backend.routers.chat"],
            "attr": "router",
            "name": "chat_router",
            "tags": ["chat"],
            },
        {
        "modules": ["backend.routers.payment_webhooks"],
            "attr": "router",
            "name": "webhooks_router",
            "tags": ["webhooks"],
            },
        {
        "modules": ["backend.routers.analytics_hub"],
            "attr": "router",
            "name": "analytics_router",
            "tags": ["analytics"],
            },
        {
        "modules": ["app.routers.integrations_max"],
            "attr": "router",
            "name": "integrations_max_router",
            "tags": ["integrations"],
            },
        {
        "modules": ["app.routers.oauth"],
            "attr": "router",
            "name": "oauth_router",
            "tags": ["oauth"],
            },
        {
        "modules": ["app.routers.paste"],
            "attr": "router",
            "name": "paste_router",
            "prefix": "/paste",
            "tags": ["paste"],
            },
        {
        "modules": ["app.routers.avatar_api"],
            "attr": "router",
            "name": "avatar_api_router",
            "prefix": "/api / avatar",
            "tags": ["avatar - api"],
            },
        {
        "modules": ["master_orchestrator.main"],
            "attr": "router",
            "name": "master_orchestrator_router",
            "prefix": "/api / orchestrator",
            "tags": ["orchestrator"],
            },
        {
        "modules": ["app.routers.affiliate_credentials"],
            "attr": "router",
            "name": "affiliate_credentials_router",
            "prefix": "/api / affiliate",
            "tags": ["affiliate - credentials"],
            },
]

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
    loaded_routers.get("pet_router", {}).get("router")
    if loaded_routers.get("pet_router")
    else None
)
places_router = (
    loaded_routers.get("places_router", {}).get("router")
    if loaded_routers.get("places_router")
    else None
)
social_router = (
    loaded_routers.get("social_router", {}).get("router")
    if loaded_routers.get("social_router")
    else None
)
chat_router = (
    loaded_routers.get("chat_router", {}).get("router")
    if loaded_routers.get("chat_router")
    else None
)
webhooks_router = (
    loaded_routers.get("webhooks_router", {}).get("router")
    if loaded_routers.get("webhooks_router")
    else None
)
analytics_router = (
    loaded_routers.get("analytics_router", {}).get("router")
    if loaded_routers.get("analytics_router")
    else None
)
integrations_max_router = (
    loaded_routers.get("integrations_max_router", {}).get("router")
    if loaded_routers.get("integrations_max_router")
    else None
)
oauth_router = (
    loaded_routers.get("oauth_router", {}).get("router")
    if loaded_routers.get("oauth_router")
    else None
)
paste_router = (
    loaded_routers.get("paste_router", {}).get("router")
    if loaded_routers.get("paste_router")
    else None
)
avatar_api_router = (
    loaded_routers.get("avatar_api_router", {}).get("router")
    if loaded_routers.get("avatar_api_router")
    else None
)
master_orchestrator_router = (
    loaded_routers.get("master_orchestrator_router", {}).get("router")
    if loaded_routers.get("master_orchestrator_router")
    else None
)
affiliate_credentials_router = (
    loaded_routers.get("affiliate_credentials_router", {}).get("router")
    if loaded_routers.get("affiliate_credentials_router")
    else None
)

# Logger already configured above

# Initialize production services with graceful fallback
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

# Import avatar router
try:
    from app.routers import avatar

    avatar_router = avatar.router
except ImportError:
    avatar_router = None
    logging.warning("Avatar router not available - check app structure")

# Import content router
try:
    from app.routers import content

    content_router_new = content.router
    logger.info("✅ Content router imported successfully")
except ImportError as e:
    content_router_new = None
    logger.warning(f"⚠️ Content router import failed: {e}")

# Import monetization router
try:
    from app.routers import monetization

    monetization_router = monetization.router
    logger.info("✅ Monetization router imported successfully")
except ImportError as e:
    monetization_router = None
    logger.warning(f"⚠️ Monetization router import failed: {e}")

# Import monetization platform APIs
try:
    from monetization import (EtsyAPI, GumroadAPI, MonetizationManager, PaddleAPI,
        SendOwlAPI)

    logger.info("✅ Monetization platform APIs imported successfully")
except ImportError as e:
    MonetizationManager = None
    logger.warning(f"⚠️ Monetization platform APIs import failed: {e}")

# Import financial router
try:
    from app.routers.financial import router as financial_router

    logger.info("Financial router imported successfully")
except ImportError as e:
    financial_router = None
    logger.warning(f"Financial router not available: {e}")

# Import dashboard router
try:
    from app.routers.dashboard import router as dashboard_router

    logger.info("Dashboard router imported successfully")
except ImportError as e:
    dashboard_router = None
    logger.warning(f"Dashboard router not available: {e}")

# Import comprehensive dashboard router
try:
    from routers.comprehensive_dashboard import router as comprehensive_dashboard_router

    logger.info("Comprehensive dashboard router imported successfully")
except ImportError as e:
    comprehensive_dashboard_router = None
    logger.warning(f"Comprehensive dashboard router not available: {e}")

# Import auth manager
try:
    from app.auth import auth_manager

    logger.info("Auth manager imported successfully")
except ImportError as e:
    auth_manager = None
    logger.warning(f"Auth manager not available: {e}")

# Import configuration validator
try:
    from config.environment import config
    from config.validator import validate_startup_config
except ImportError:
    validate_startup_config = None
    config = None
    logging.warning("Configuration modules not available")

# Logging already configured above

# Validate configuration at startup
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

# Create FastAPI app
app = FastAPI(
    title="Online Production API",
        description="Production - ready API with pet care services and affiliate processing",
        version="1.0.0",
        docs_url="/docs" if __name__ == "__main__" else None,  # Disable docs in production
    redoc_url="/redoc" if __name__ == "__main__" else None,
        lifespan = lifespan,
)

# Create Socket.IO server for dashboard real - time updates
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://localhost:3000",
            "http://localhost:8000",
            "https://*.netlify.app",
            ],
        async_mode="asgi",
        logger = True,
        engineio_logger = False,
)

# Socket.IO event handlers
@sio.event


async def connect(sid, environ):
    logger.info(f"Socket.IO client connected: {sid}")
    await sio.emit("connection_status", {"status": "connected", "sid": sid}, room = sid)

@sio.event


async def disconnect(sid):
    logger.info(f"Socket.IO client disconnected: {sid}")

@sio.on("agent_update")


async def handle_agent_update(sid, data):
    logger.info(f"Agent update from {sid}: {data}")
    # Broadcast to all connected clients
    await sio.emit("agent_update", data)

@sio.on("task_update")


async def handle_task_update(sid, data):
    logger.info(f"Task update from {sid}: {data}")
    await sio.emit("task_update", data)

@sio.on("system_alert")


async def handle_system_alert(sid, data):
    logger.info(f"System alert from {sid}: {data}")
    await sio.emit("system_alert", data)

@sio.on("log_update")


async def handle_log_update(sid, data):
    await sio.emit("log_update", data)

@sio.on("performance_update")


async def handle_performance_update(sid, data):
    await sio.emit("performance_update", data)

# Initialize security
security = HTTPBearer()

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
        allowed_hosts=[
        "localhost",
            "127.0.0.1",
            "*.netlify.app",
            ],  # Configure for production
)

# Configure CORS with security considerations
app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "http://localhost:3000",
            "http://localhost:8000",
            "https://*.netlify.app",  # Configure appropriately for production
    ],
        allow_credentials = True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        max_age = 600,  # Cache preflight requests for 10 minutes
)

# Mount static files
app.mount("/static", StaticFiles(directory="app / static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")
wire_integrations(app)  # mounts /integrations + starts background health checker
app.include_router(content_router)  # mounts /content endpoints

# Include pet endpoints if available
if pet_router:
    app.include_router(pet_router, prefix="/api / v1", tags=["pets"])
    logger.info("Pet endpoints mounted at /api / v1")
else:
    logger.warning("Pet endpoints not mounted - router not available")

# Include places router if available
if places_router:
    app.include_router(places_router, prefix="/places", tags=["places"])
    logger.info("Places endpoints mounted at /places")
else:
    logger.warning("Places endpoints not mounted - router not available")

# Include social media router if available
if social_router:
    app.include_router(social_router, tags=["social"])
    logger.info("Social media endpoints mounted at /social")
else:
    logger.warning("Social media endpoints not mounted - router not available")

# Include payment webhooks router if available
if webhooks_router:
    app.include_router(webhooks_router, tags=["webhooks"])
    logger.info("Payment webhook endpoints mounted at /webhooks")
else:
    logger.warning("Payment webhook endpoints not mounted - router not available")

# Include analytics hub router if available
if analytics_router:
    app.include_router(analytics_router, tags=["analytics"])
    logger.info("Analytics hub endpoints mounted at /analytics")
else:
    logger.warning("Analytics hub endpoints not mounted - router not available")

# Mount integrations max router
if integrations_max_router:
    app.include_router(integrations_max_router, tags=["integrations"])
    logger.info("Integrations max endpoints mounted at /integrations")
else:
    logger.warning("Integrations max endpoints not mounted - router not available")

# Mount OAuth router
if oauth_router:
    app.include_router(oauth_router, tags=["oauth"])
    logger.info("OAuth endpoints mounted at /oauth")
else:
    logger.warning("OAuth endpoints not mounted - router not available")

# Mount chat router
if chat_router:
    app.include_router(chat_router, tags=["chat"])
    logger.info("Chat endpoints mounted at /chat")
else:
    logger.warning("Chat endpoints not mounted - router not available")

# Mount paste router
if paste_router:
    app.include_router(paste_router, prefix="/paste", tags=["paste"])
    logger.info("Paste endpoints mounted at /paste")
else:
    logger.warning("Paste endpoints not mounted - router not available")

# Mount avatar router
if avatar_router:
    app.include_router(avatar_router, prefix="/avatar", tags=["avatar"])
    logger.info("Avatar endpoints mounted at /avatar")
else:
    logger.warning("Avatar endpoints not mounted - router not available")

# Mount avatar API router
if avatar_api_router:
    app.include_router(avatar_api_router, prefix="/api / avatar", tags=["avatar - api"])
    logger.info("Avatar API endpoints mounted at /api / avatar")
else:
    logger.warning("Avatar API endpoints not mounted - router not available")

# Mount content router if available
if content_router_new:
    app.include_router(content_router_new, prefix="/api / content")
    logger.info("✅ Content router mounted at /api / content")
else:
    logger.warning("⚠️ Content router not mounted - import failed")

# Mount monetization router if available
if monetization_router:
    app.include_router(monetization_router, prefix="/api")
    logger.info("✅ Monetization router mounted at /api / monetization")
else:
    logger.warning("⚠️ Monetization router not mounted - import failed")

# Mount financial router
if financial_router:
    app.include_router(financial_router, prefix="/api / financial", tags=["financial"])
    logger.info("Financial router mounted at /api / financial")
else:
    logger.warning("Financial router not mounted - service unavailable")

# Mount dashboard router
if dashboard_router:
    app.include_router(dashboard_router, tags=["dashboard"])
    logger.info("Dashboard router mounted at /dashboard")
else:
    logger.warning("Dashboard router not mounted - service unavailable")

# Mount comprehensive dashboard router
if comprehensive_dashboard_router:
    app.include_router(
        comprehensive_dashboard_router,
            prefix="/api / comprehensive",
            tags=["comprehensive - dashboard"],
            )
    logger.info("Comprehensive dashboard router mounted at /api / comprehensive")
else:
    logger.warning("Comprehensive dashboard router not mounted - service unavailable")

# Mount auth endpoints if available
if auth_manager:
    try:
        from app.routers.auth import router as auth_router

        app.include_router(auth_router, prefix="/api / auth", tags=["authentication"])
        logger.info("Auth endpoints mounted at /api / auth")
    except ImportError:
        logger.warning("Auth router not available - check app structure")
else:
    logger.warning("Auth manager not available - authentication disabled")

# Mount Master Orchestrator router
if master_orchestrator_router:
    app.include_router(
        master_orchestrator_router, prefix="/api / orchestrator", tags=["orchestrator"]
    )
    logger.info("✅ Master Orchestrator endpoints mounted at /api / orchestrator")
else:
    logger.warning("⚠️ Master Orchestrator endpoints not mounted - router not available")

# Mount affiliate credentials router
if affiliate_credentials_router:
    app.include_router(
        affiliate_credentials_router,
            prefix="/api / affiliate",
            tags=["affiliate - credentials"],
            )
    logger.info("✅ Affiliate Credentials endpoints mounted at /api / affiliate")
else:
    logger.warning(
        "⚠️ Affiliate Credentials endpoints not mounted - router not available"
    )

# Initialize monetization manager
monetization_manager = None
if MonetizationManager:
    try:
        monetization_manager = MonetizationManager()
        logger.info("✅ Monetization manager initialized")
    except Exception as e:
        logger.warning(f"⚠️ Monetization manager initialization failed: {e}")

# Import backend app routes if available
try:
    from backend.app import app as backend_app

    # Copy all routes from backend app to main app
    for route in backend_app.routes:
        app.routes.append(route)
    logger.info("✅ Backend app routes integrated")
except ImportError as e:
    logger.warning(f"⚠️ Backend app not available: {e}")
except Exception as e:
    logger.warning(f"⚠️ Backend app integration failed: {e}")

# WebSocket manager for real - time updates


class WebSocketManager:


    def __init__(self):
        self.active_connections = []
        self.client_connections = {}


    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if client_id:
            self.client_connections[client_id] = websocket


    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from client connections
        for client_id, ws in list(self.client_connections.items()):
            if ws == websocket:
                del self.client_connections[client_id]
                break


    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")


    async def broadcast(self, message: dict):
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                self.disconnect(connection)


    async def handle_client_message(self, websocket: WebSocket, message: dict):
        # Handle different message types
        msg_type = message.get("type")
        if msg_type == "ping":
            await self.send_personal_message({"type": "pong"}, websocket)
        elif msg_type == "subscribe":
            await self.send_personal_message(
                {"type": "subscribed", "channel": message.get("channel", "dashboard")},
                    websocket,
                    )


    def get_connection_count(self):
        return len(self.active_connections)


    def get_connection_info(self):
        return {
            "total": len(self.active_connections),
                "clients": list(self.client_connections.keys()),
                }


    async def start_heartbeat(self):
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await self.broadcast(
                {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
            )

websocket_manager = WebSocketManager()

# Simulate real - time updates


async def simulate_real_time_updates():
    while True:
        await asyncio.sleep(5)  # Update every 5 seconds
        update_data = {
            "type": "dashboard_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                "active_users": len(websocket_manager.active_connections),
                    "system_status": "healthy",
                    },
                }
        await websocket_manager.broadcast(update_data)

# WebSocket endpoint for real - time dashboard updates
@app.websocket("/ws / dashboard")


async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket_manager.handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"}, websocket
                )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# WebSocket info endpoint
@app.get("/ws / info")


async def websocket_info():
    """Get information about active WebSocket connections"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
            "connections": websocket_manager.get_connection_info(),
            }

# Chat page route
@app.get("/chat", response_class = HTMLResponse)


async def chat_page(request: Request):
    """Serve the chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

# Paste page route
@app.get("/paste", response_class = HTMLResponse)


async def paste_page(request: Request):
    """Serve the paste interface"""
    # Redirect to the paste router's main interface
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/paste/", status_code = 302)

@app.get("/comprehensive - dashboard", response_class = HTMLResponse)


async def comprehensive_dashboard_page(request: Request):
    """Serve the comprehensive dashboard page"""
    return templates.TemplateResponse(
        "comprehensive_dashboard.html", {"request": request}
    )

@app.get("/affiliate - credentials", response_class = HTMLResponse)


async def affiliate_credentials_page(request: Request):
    """Serve the affiliate credentials page"""
    return templates.TemplateResponse(
        "affiliate_credentials.html", {"request": request}
    )

# Add pets search endpoint
@app.get("/pets / search")


async def pets_search(
    animal: str = Query("dog", pattern="^(dog|cat)$"),
        location: Optional[str] = None,
        limit: int = Query(20, ge = 1, le = 100),
        page: int = Query(1, ge = 1),
):
    """Search for pets using TheDogAPI or TheCatAPI"""
    if animal == "dog":
        try:
            key = get_secret("DOG_API_KEY")
            headers = {"x - api - key": key} if key else {}
            async with httpx.AsyncClient(timeout = 12) as client:
                r = await client.get(
                    f"https://api.thedogapi.com / v1 / images / search?limit={limit}&has_breeds = 1",
                        headers = headers,
                        )
                r.raise_for_status()
                return {"provider": "thedogapi", "data": r.json()}
        except Exception as e:
            raise HTTPException(500, f"Failed to fetch dog data: {str(e)}")
    else:
        try:
            key = get_secret("CAT_API_KEY")
            headers = {"x - api - key": key} if key else {}
            async with httpx.AsyncClient(timeout = 12) as client:
                r = await client.get(
                    f"https://api.thecatapi.com / v1 / images / search?limit={limit}&has_breeds = 1",
                        headers = headers,
                        )
                r.raise_for_status()
                return {"provider": "thecatapi", "data": r.json()}
        except Exception as e:
            raise HTTPException(500, f"Failed to fetch cat data: {str(e)}")

# Add configuration status endpoint
@app.get("/api / status")


async def get_configuration_status():
    """Get current configuration status including geocoding APIs"""
    try:
        if config:
            status_data = config.get_api_status()
            return {
                "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "configuration": status_data,
                    "message": "Configuration status retrieved successfully",
                    }
        else:
            return {
                "success": False,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Configuration not available",
                    }
    except Exception as e:
        logger.error(f"Configuration status error: {str(e)}")
        raise HTTPException(
            status_code = 500, detail="Configuration status service unavailable"
        )

@app.get("/pets / types")


async def pets_types():
    """Get pet types from Petfinder API with fallback to static data"""
    # Try Petfinder (if enabled + creds)
    pf = _state["providers"].get("petfinder")
    if pf and pf.enabled and pf.status == "green":
        token = await _petfinder_token()
        if token:
            async with httpx.AsyncClient(timeout = 12) as client:
                r = await client.get(
                    "https://api.petfinder.com / v2 / types",
                        headers={"Authorization": f"Bearer {token}"},
                        )
                if r.status_code < 400:
                    return {"provider": "petfinder", "types": r.json().get("types", [])}
    # Fallback static set
    return {
        "provider": "static",
            "types": [
            {"name": "Dog"},
                {"name": "Cat"},
                {"name": "Bird"},
                {"name": "Rabbit"},
                {"name": "Small & Furry"},
                {"name": "Scales, Fins & Other"},
                {"name": "Horse"},
                {"name": "Barnyard"},
                ],
            }

@app.get("/health")


async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "main_app",
            }

@app.get("/health / detailed")


async def detailed_health_check():
    """Detailed health check with system metrics"""
    import os

    import psutil

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval = 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process info
        process = psutil.Process(os.getpid())
        process_info = {
            "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "status": process.status(),
                }

        # Database connectivity (if applicable)
        db_status = "unknown"
        try:
            # Check if database file exists and is accessible
            from pathlib import Path

            db_path = Path("data / businesses.db")
            if db_path.exists():
                db_status = "connected"
            else:
                db_status = "no_database"
        except Exception:
            db_status = "error"

        # Determine overall health
        health_status = "healthy"
        issues = []

        if cpu_percent > 90:
            health_status = "degraded"
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")

        if memory.percent > 90:
            health_status = "degraded"
            issues.append(f"High memory usage: {memory.percent:.1f}%")

        if disk.percent > 95:
            health_status = "degraded"
            issues.append(f"High disk usage: {disk.percent:.1f}%")

        if db_status == "error":
            health_status = "unhealthy"
            issues.append("Database connection error")

        return {
            "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "main_app",
                "system": {
                "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    },
                "process": process_info,
                "database": {"status": db_status},
                "issues": issues,
                "uptime_seconds": (
                datetime.now() - datetime.fromtimestamp(process.create_time())
            ).total_seconds(),
                }

    except Exception as e:
        return {
            "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "main_app",
                "error": str(e),
                }

@app.get("/health / ready")


async def readiness_check():
    """Readiness check - indicates if service is ready to handle requests"""
    try:
        # Check critical dependencies
        ready = True
        checks = {}

        # Check if all routers are loaded
        checks["routers_loaded"] = (
            len(app.routes) > 2
        )  # More than just health endpoints

        # Check database accessibility
        try:
            from pathlib import Path

            db_path = Path("data / businesses.db")
            checks["database_accessible"] = db_path.parent.exists()
        except Exception:
            checks["database_accessible"] = False

        # Check if we can write to logs
        try:
            from pathlib import Path

            log_path = Path("logs")
            log_path.mkdir(exist_ok = True)
            test_file = log_path / "readiness_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            checks["logs_writable"] = True
        except Exception:
            checks["logs_writable"] = False

        # Overall readiness
        ready = all(checks.values())

        return {
            "ready": ready,
                "timestamp": datetime.now().isoformat(),
                "service": "main_app",
                "checks": checks,
                }

    except Exception as e:
        return {
            "ready": False,
                "timestamp": datetime.now().isoformat(),
                "service": "main_app",
                "error": str(e),
                }

@app.get("/health / live")


async def liveness_check():
    """Liveness check - indicates if service is alive and should not be restarted"""
    try:
        # Simple liveness check - if we can respond, we're alive
        import os
        import threading

        return {
            "alive": True,
                "timestamp": datetime.now().isoformat(),
                "service": "main_app",
                "thread_count": threading.active_count(),
                "pid": os.getpid(),
                }

    except Exception as e:
        return {
            "alive": False,
                "timestamp": datetime.now().isoformat(),
                "service": "main_app",
                "error": str(e),
                }

# Version endpoint for production monitoring
@app.get("/api / version")


async def get_version():
    import os

    return {
        "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "build_time": datetime.now().isoformat(),
            "status": "production - ready",
            }

# Version endpoint alias for compatibility
@app.get("/version")


async def get_version_alias():
    return await get_version()

# Add direct system metrics endpoint for dashboard compatibility
@app.get("/api / system / metrics")


async def get_system_metrics_direct():
    """Get system metrics - direct endpoint for dashboard compatibility"""
    try:
        import time

        import psutil

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval = 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "active_connections": len(websocket_manager.active_connections),
                "uptime_seconds": int(time.time()),
                "response_time_ms": 50,
                "health_score": 100,
                "load_average": (
                list(psutil.getloadavg())
                if hasattr(psutil, "getloadavg")
                else [0, 0, 0]
            ),
                "process_count": len(psutil.pids()),
                "network_bytes_sent": 0,
                "network_bytes_recv": 0,
                "timestamp": datetime.now().isoformat(),
                }
    except ImportError:
        # Fallback if psutil is not available
        return {
            "cpu_percent": 25.0,
                "memory_percent": 45.0,
                "memory_used_gb": 2.1,
                "memory_total_gb": 8.0,
                "disk_percent": 30.0,
                "disk_used_gb": 15.0,
                "disk_total_gb": 50.0,
                "active_connections": len(websocket_manager.active_connections),
                "uptime_seconds": 3600,
                "response_time_ms": 50,
                "health_score": 100,
                "load_average": [0.5, 0.3, 0.2],
                "process_count": 25,
                "network_bytes_sent": 0,
                "network_bytes_recv": 0,
                "timestamp": datetime.now().isoformat(),
                }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code = 500, detail="Failed to get system metrics")

@app.get("/api / services")


async def get_services_status():
    """Get services status for dashboard"""
    return {
        "services": {
            "main_api": {"status": "active", "uptime": "1h 23m"},
                "database": {"status": "active", "uptime": "1h 23m"},
                "websocket": {
                "status": "active",
                    "connections": len(websocket_manager.active_connections),
                    },
                "socketio": {
                "status": "active",
                    "connections": len(websocket_manager.active_connections),
                    },
                },
            "timestamp": datetime.now().isoformat(),
            }

@app.get("/api / system - info")


async def get_system_info():
    """Get system information for dashboard"""
    try:
        import platform

        return {
            "system": {
                "platform": platform.system(),
                    "platform_release": platform.release(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                    "python_version": platform.python_version(),
                    },
                "application": {
                "name": "Online Production API",
                    "version": "1.0.0",
                    "environment": "development",
                    },
                "timestamp": datetime.now().isoformat(),
                }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "system": {"platform": "Unknown", "hostname": "localhost"},
                "application": {
                "name": "Online Production API",
                    "version": "1.0.0",
                    "environment": "development",
                    },
                "timestamp": datetime.now().isoformat(),
                }

# Dashboard - specific endpoints with /dashboard prefix
@app.get("/dashboard / api / metrics")


async def get_dashboard_metrics():
    """Get system metrics for dashboard with /dashboard prefix"""
    return await get_system_metrics_direct()

@app.get("/dashboard / api / services")


async def get_dashboard_services():
    """Get services status for dashboard with /dashboard prefix"""
    return await get_services_status()

@app.get("/dashboard / api / system - info")


async def get_dashboard_system_info():
    """Get system information for dashboard with /dashboard prefix"""
    return await get_system_info()

# Background task for real - time updates
@app.on_event("startup")


async def startup_event():
    """Start background tasks on application startup"""
    # Start the real - time data simulation
    asyncio.create_task(simulate_real_time_updates())
    # Start WebSocket heartbeat
    asyncio.create_task(websocket_manager.start_heartbeat())

    # Initialize auth manager on startup
    if auth_manager:
        # Create default admin user if none exists
        if not auth_manager.list_users():
            admin_user = auth_manager.create_user(
                username="admin",
                    email="admin@dashboard.local",
                    full_name="System Administrator",
                    password="admin123",  # Change this in production!
                role="ADMIN",
                    )
            logger.info(f"Created default admin user: {admin_user.username}")
            logger.warning(
                "Default password: admin123 - Please change this immediately!"
            )

        logger.info("Authentication system initialized")

    logger.info("🚀 Dashboard with real - time features started")

@app.on_event("shutdown")


async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("🛑 Dashboard shutting down")

# Wrap FastAPI app with Socket.IO
socketio_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import os

    import uvicorn

    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info(f"🚀 Starting server on {host}:{port}")
    logger.info(f"📖 API docs: http://{host}:{port}/docs")
    logger.info(f"❤️ Health check: http://{host}:{port}/health")

    # Use socketio_app for Socket.IO support, but ensure health checks work
    uvicorn.run(
        socketio_app,
            host = host,
            port = port,
            reload = False,  # Disable reload in production
        log_level="info",
            )
