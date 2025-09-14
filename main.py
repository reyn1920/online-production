# main.py - FastAPI application with integrations hub

import asyncio
import logging
import os
import uuid
import time
import shutil
from datetime import datetime
from typing import Optional
from collections import defaultdict, deque
from time import monotonic

import httpx
import socketio

# Load environment variables
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import traceback
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = None

from content_sources import router as content_router
from integrations_hub import _petfinder_token, lifespan, wire_integrations

load_dotenv()

# Set up logging first

# Import production initialization
from backend.production_init import get_production_manager, initialize_production_sync

# Import timeout middleware
try:
    from backend.middleware.timeout_middleware import TimeoutMiddleware
except ImportError:
    TimeoutMiddleware = None
    logger.warning("⚠️ Timeout middleware not available")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import security middleware
try:
    from security_middleware import (
        setup_security_middleware,
        RateLimitMiddleware,
        AuthenticationMiddleware,
        RequestValidationMiddleware
    )
    security_middleware_available = True
    logger.info("✅ Security middleware loaded successfully")
except ImportError as e:
    security_middleware_available = False
    logger.warning(f"⚠️ Security middleware not available: {e}")

# Rate limiting storage
rate_limit_storage = defaultdict(lambda: deque())

# Security and Production Middleware
class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        
    async def dispatch(self, request: StarletteRequest, call_next):
        # Add request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        current_time = monotonic()
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - 60
        while rate_limit_storage[client_ip] and rate_limit_storage[client_ip][0] < cutoff_time:
            rate_limit_storage[client_ip].popleft()
        
        # Check rate limit
        if len(rate_limit_storage[client_ip]) >= self.max_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests_per_minute} requests per minute",
                    "request_id": request_id
                },
                headers={"Retry-After": "60"}
            )
        
        # Add current request timestamp
        rate_limit_storage[client_ip].append(current_time)
        
        # Security headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

# Production Error Handling Middleware
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        if PROMETHEUS_AVAILABLE:
            self.request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
            self.request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
        
    async def dispatch(self, request: StarletteRequest, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'request_count'):
                self.request_count.labels(method=method, endpoint=path, status=response.status_code).inc()
                self.request_duration.observe(process_time)
            
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"Unhandled exception in {request.method} {request.url}: {exc}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "process_time": process_time,
                    "traceback": traceback.format_exc(),
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
            
            # Prometheus error metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'request_count'):
                self.request_count.labels(method=method, endpoint=path, status=500).inc()
                self.request_duration.observe(process_time)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )

# Dynamic router loading
import importlib

ROUTER_CONFIGS = [
    {
        "modules": ["backend.api.pet_endpoints", "api.pet_endpoints"],
        "attr": "router",
        "name": "pet_router",
        "prefix": "/api/v1",
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
        "prefix": "/api/avatar",
        "tags": ["avatar-api"],
    },
    {
        "modules": ["master_orchestrator.main"],
        "attr": "router",
        "name": "master_orchestrator_router",
        "prefix": "/api/orchestrator",
        "tags": ["orchestrator"],
    },
    {
        "modules": ["app.routers.affiliate_credentials"],
        "attr": "router",
        "name": "affiliate_credentials_router",
        "prefix": "/api/affiliate",
        "tags": ["affiliate-credentials"],
    },
    {
        "modules": ["routers.health_router"],
        "attr": "router",
        "name": "health_router",
        "tags": ["health"],
    },
    {
        "modules": ["routers.policy_router"],
        "attr": "router",
        "name": "policy_router",
        "tags": ["policy"],
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
    loaded_routers.get("pet_router", {}).get("router") if loaded_routers.get("pet_router") else None
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
health_router = (
    loaded_routers.get("health_router", {}).get("router")
    if loaded_routers.get("health_router")
    else None
)
policy_router = (
    loaded_routers.get("policy_router", {}).get("router")
    if loaded_routers.get("policy_router")
    else None
)

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
    # from app.routers import monetization  # Temporarily disabled due to syntax errors

    # monetization_router = monetization.router
    # logger.info("✅ Monetization router imported successfully")
    monetization_router = None
    logger.warning("⚠️ Monetization router temporarily disabled due to syntax errors")
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
    )

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

# OpenAPI tags for better documentation
openapi_tags = [
    {"name": "Meta", "description": "Version & system status"},
    {"name": "Dashboard", "description": "UI analytics & status surfaces"},
    {"name": "Health", "description": "Health check endpoints"},
    {"name": "Webhooks", "description": "Webhook endpoints"},
    {"name": "RSS", "description": "RSS feed management"},
]

# FastAPI app initialization with production settings
app = FastAPI(
    title="TRAE AI Production API",
    description="Production-ready API with pet care services and affiliate processing",
    version="1.0.0",
    servers=[{"url": "/"}],
    contact={"name": "TRAE Ops", "email": "ops@yourdomain.com"},
    license_info={"name": "Proprietary"},
    openapi_tags=openapi_tags,
    docs_url="/docs" if __name__ == "__main__" else None,  # Disable docs in production
    redoc_url="/redoc" if __name__ == "__main__" else None,
    lifespan=lifespan,
)

# Track application start time for uptime metrics
import time
start_time = time.time()

# Socket.IO server initialization
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app",
    ],
    async_mode="asgi",
    logger=True,
    engineio_logger=False,
)


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
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.netlify.app",
    ],  # Configure for production
)

@app.middleware("http")
async def no_cache_meta(request, call_next):
    """Add no-cache headers to API endpoints"""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response

# Add timeout middleware
if TimeoutMiddleware:
    app.add_middleware(TimeoutMiddleware)
    logger.info("✅ Timeout middleware configured successfully")
else:
    logger.warning("⚠️ Timeout middleware not available - requests may hang")

# Security middleware setup
if security_middleware_available:
    try:
        setup_security_middleware(app)
        logger.info("✅ Security middleware configured successfully")
    except Exception as e:
        logger.error(f"❌ Failed to setup security middleware: {e}")

# Production-ready middleware stack from paste_content.txt

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://app.yourdomain.com,https://yourdomain.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request ID Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        dur_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Process-Time"] = f"{dur_ms}ms"
        return response

app.add_middleware(RequestIDMiddleware)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        h = resp.headers
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Referrer-Policy"] = "same-origin"
        h["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return resp

app.add_middleware(SecurityHeadersMiddleware)

# No Cache API Middleware
class NoCacheAPIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        if request.url.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

app.add_middleware(NoCacheAPIMiddleware)

# Rate Limiting Middleware
BUCKET = defaultdict(lambda: deque())
LIMIT = int(os.getenv("RATE_LIMIT_RPM", "120"))  # per minute

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if path.startswith(("/api/version", "/api/system/status", "/metrics", "/health")):
        return await call_next(request)
    ip = request.client.host
    now = monotonic()
    q = BUCKET[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= LIMIT:
        return JSONResponse({"code": "RATE_LIMIT", "message": "Too many requests"}, status_code=429)
    q.append(now)
    return await call_next(request)

# Prometheus metrics middleware
if PROMETHEUS_AVAILABLE:
    REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "path"])
    
    @app.middleware("http")
    async def prom_mw(request: Request, call_next):
        path = request.url.path
        method = request.method
        with LATENCY.labels(method, path).time():
            resp = await call_next(request)
        REQUESTS.labels(method, path, str(resp.status_code)).inc()
        return resp

# Uniform error envelope
@app.exception_handler(RequestValidationError)
async def validation_handler(_, exc: RequestValidationError):
    return JSONResponse(
        {"code": "VALIDATION_ERROR", "message": "Invalid request", "details": exc.errors()},
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
    )

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    rid = request.headers.get("X-Request-ID", "")
    return JSONResponse(
        {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "request_id": rid},
        status_code=500,
    )

# Configure CORS with tighter security for production
production_domains = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Legacy CORS middleware (keeping for compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=production_domains,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add security and error handling middleware
app.add_middleware(SecurityMiddleware, max_requests_per_minute=100)
app.add_middleware(ErrorHandlingMiddleware)

# Uniform error envelope handlers
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
    )

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "")
    logger.error(f"Unhandled exception {request_id}: {exc}", exc_info=True)
    return JSONResponse(
        {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": request_id
        },
        status_code=500,
    )

# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        f"HTTP {exc.status_code} error in {request.method} {request.url}: {exc.detail}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code
        }
    )
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Validation error in {request.method} {request.url}: {exc.errors()}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "validation_errors": exc.errors()
        }
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.errors()
        }
    )

# Static files - mount assets directory with name="static" for url_for compatibility
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
DIST_DIR = Path(__file__).parent / "frontend" / "dist"

# Mount frontend assets first (higher priority)
# Mount frontend assets at /assets (but not the SPA fallback yet)
if DIST_DIR.exists():
    frontend_assets_dir = DIST_DIR / "assets"
    if frontend_assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_assets_dir)), name="frontend_assets")

# Mount legacy assets at /assets with name="static" for url_for('static', ...) compatibility
if ASSETS_DIR.exists():
    app.mount("/legacy-assets", StaticFiles(directory=str(ASSETS_DIR)), name="static")

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
    )
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
    )
    logger.info("✅ Master Orchestrator endpoints mounted at /api/orchestrator")
else:
    logger.warning("⚠️ Master Orchestrator endpoints not mounted - router not available")

if affiliate_credentials_router:
    app.include_router(
        affiliate_credentials_router,
        prefix="/api/affiliate",
        tags=["affiliate-credentials"],
    )
    logger.info("✅ Affiliate Credentials endpoints mounted at /api/affiliate")
else:
    logger.warning("⚠️ Affiliate Credentials endpoints not mounted - router not available")

if health_router:
    app.include_router(health_router, tags=["health"])
    logger.info("✅ Health router mounted at /api/health and /dashboard/api/health")
else:
    logger.warning("⚠️ Health router not mounted - router not available")

if policy_router:
    app.include_router(policy_router, tags=["policy"])
    logger.info("✅ Policy router mounted at /api/policy")
else:
    logger.warning("⚠️ Policy router not mounted - router not available")

# Import and register meta router
try:
    from routers.meta import meta
    app.include_router(meta)
    logger.info("✅ Meta router mounted - /api/version, /api/system/status, /api/services, /ws/info")
except ImportError as e:
    logger.warning(f"⚠️ Meta router not mounted - import failed: {e}")

# Import and register software status router
try:
    from routers.software_status import router as software_status_router
    app.include_router(software_status_router)
    logger.info("✅ Software status router mounted")
except ImportError as e:
    logger.warning(f"⚠️ Software status router not mounted - import failed: {e}")

# Import and register dashboard safe router
try:
    from routers.dashboard_safe import router as dashboard_safe_router
    app.include_router(dashboard_safe_router)
    logger.info("✅ Dashboard safe router mounted")
except ImportError as e:
    logger.warning(f"⚠️ Dashboard safe router not mounted - import failed: {e}")

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
            )
        else:
            # Echo back for now
            await self.send_personal_message(message, websocket)

    def get_connection_count(self):
        return len(self.active_connections)

    def get_connection_info(self):
        return {
            "total_connections": len(self.active_connections),
            "client_connections": len(self.client_connections),
        }

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
                },
            }
        )


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
    }


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
        },
    )


@app.get("/comprehensive-dashboard", response_class=HTMLResponse)
async def comprehensive_dashboard_page(request: Request):
    return templates.TemplateResponse("comprehensive_dashboard.html", {"request": request})


@app.get("/affiliate-credentials", response_class=HTMLResponse)
async def affiliate_credentials_page(request: Request):
    return templates.TemplateResponse(
        "affiliate_credentials.html",
        {"request": request, "title": "Affiliate Credentials Management"},
    )


# API endpoints
@app.get("/pets/search")
async def pets_search(
    animal: str = Query("dog", pattern="^(dog|cat)$"),
    location: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
):
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
            )
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
        },
        "configuration": {
            "environment": "production" if production_manager else "development",
            "routers_loaded": len([r for r in loaded_routers.values() if r is not None]),
        },
    }


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
            )
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
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status - soft checks to avoid cascading failures"""
    import os
    
    # Soft database connectivity test (non-blocking)
    database_healthy = "unknown"
    try:
        from backend.core.database import get_db_connection
        # Use a timeout to prevent hanging
        import asyncio
        async def check_db():
            with get_db_connection() as conn:
                if hasattr(conn, 'execute'):
                    conn.execute("SELECT 1")
                    return True
            return False
        
        database_healthy = await asyncio.wait_for(check_db(), timeout=2.0)
    except asyncio.TimeoutError:
        logger.warning("Database health check timed out")
        database_healthy = "timeout"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        database_healthy = False

    # Soft external API check
    petfinder_status = "unknown"
    if _petfinder_token:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    "https://api.petfinder.com/v2/types",
                    headers={"Authorization": f"Bearer {_petfinder_token}"},
                )
                petfinder_status = response.status_code == 200
        except Exception as e:
            logger.warning(f"Petfinder API health check failed: {e}")
            petfinder_status = False
    else:
        petfinder_status = False

    services = {
        "petfinder_api": petfinder_status,
        "production_manager": production_manager is not None,
        "websocket_manager": True,
        "database": database_healthy,
        "timeout_middleware": 'TimeoutMiddleware' in str(app.middleware_stack),
        "security_middleware": True,  # We know it's loaded
        "prometheus_metrics": PROMETHEUS_AVAILABLE,
    }

    router_status = {}
    for name, router_info in loaded_routers.items():
        router_status[name] = router_info is not None

    system_info = {
        "python_version": os.sys.version,
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "host": os.environ.get("HOST", "localhost"),
        "port": os.environ.get("PORT", "8000"),
    }

    # Only consider critical services for overall health
    critical_services = ["websocket_manager", "production_manager"]
    critical_healthy = all(services.get(service, False) for service in critical_services)

    return {
        "status": "healthy" if critical_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "routers": router_status,
        "system": system_info,
        "websocket_connections": websocket_manager.get_connection_count(),
        "rate_limiting": {
            "active_clients": len(rate_limit_storage),
            "max_requests_per_minute": 100
        }
    }


@app.get("/metrics")
async def get_metrics():
    """Production metrics endpoint for monitoring"""
    # Return Prometheus metrics if available
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    # Fallback to JSON metrics
    try:
        import psutil
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Non-blocking
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        uptime = time.time() - start_time if 'start_time' in globals() else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": disk.free // (1024 * 1024 * 1024),
            },
            "application": {
                "uptime_seconds": uptime,
                "websocket_connections": websocket_manager.get_connection_count(),
                "loaded_routers": len(loaded_routers),
                "active_services": sum(1 for service in [_petfinder_token, production_manager] if service),
                "rate_limit_clients": len(rate_limit_storage),
            },
            "environment": {
                "python_version": os.sys.version.split()[0],
                "environment": os.environ.get("ENVIRONMENT", "development"),
                "debug_mode": os.environ.get("DEBUG", "false").lower() == "true",
            }
        }
    except ImportError:
        return {
            "error": "psutil not available",
            "basic_metrics": {
                "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0,
                "websocket_connections": websocket_manager.get_connection_count(),
                "loaded_routers": len(loaded_routers),
                "rate_limit_clients": len(rate_limit_storage),
            },
            "timestamp": datetime.now().isoformat(),
        }


# RSS Watcher endpoint
@app.get("/api/rss/watch", tags=["RSS"])
async def rss_watch_status():
    """RSS watcher status - never fails"""
    try:
        # Check if RSS watcher is configured
        rss_urls = os.getenv("RSS_WATCH_URLS", "").split(",")
        rss_urls = [url.strip() for url in rss_urls if url.strip()]
        
        return {
            "available": len(rss_urls) > 0,
            "watched_feeds": len(rss_urls),
            "feeds": rss_urls[:5],  # Show first 5 for privacy
            "last_check": datetime.now().isoformat(),
            "status": "monitoring" if rss_urls else "not_configured"
        }
    except Exception as e:
        return {
            "available": False,
            "reason": f"error: {type(e).__name__}",
            "timestamp": datetime.now().isoformat()
        }


# Webhook system endpoints
@app.post("/api/webhooks/github", tags=["Webhooks"])
async def github_webhook(request: Request):
    """GitHub webhook handler - always returns 200"""
    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        
        # Log the webhook for monitoring
        logger.info(f"GitHub webhook received: {event_type}")
        
        return {
            "received": True,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "status": "processed"
        }
    except Exception as e:
        logger.error(f"GitHub webhook error: {e}")
        return {
            "received": True,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error_logged"
        }


@app.post("/api/webhooks/deploy", tags=["Webhooks"])
async def deploy_webhook(request: Request):
    """Deployment webhook handler"""
    try:
        payload = await request.json()
        deploy_id = payload.get("deployment_id", "unknown")
        
        logger.info(f"Deploy webhook received: {deploy_id}")
        
        return {
            "received": True,
            "deployment_id": deploy_id,
            "timestamp": datetime.now().isoformat(),
            "status": "acknowledged"
        }
    except Exception as e:
        logger.error(f"Deploy webhook error: {e}")
        return {
            "received": True,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error_logged"
        }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    critical_services = {
        "app_initialized": True,
        "routers_loaded": any(loaded_routers.values()),
        "middleware_configured": True,
    }

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
                )
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
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    try:
        # Basic application liveness checks
        checks = {
            "app_responsive": True,
            "memory_usage": "ok",  # Add actual memory check
            "websocket_manager": websocket_manager is not None,
        }

        return {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            "alive": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# /api/version endpoint is now handled by the meta router


@app.get("/version")
async def get_version_alias():
    """Smart 308 redirect to /api/version to avoid drift"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/version", status_code=308)


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
            },
            "application": {
                "memory_rss": app_memory.rss,
                "memory_vms": app_memory.vms,
                "websocket_connections": websocket_manager.get_connection_count(),
                "active_routers": len([r for r in loaded_routers.values() if r is not None]),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError:
        return {
            "error": "psutil not available",
            "basic_metrics": {
                "websocket_connections": websocket_manager.get_connection_count(),
                "active_routers": len([r for r in loaded_routers.values() if r is not None]),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "error": f"Metrics collection failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/services")
async def get_services_status():
    """Get status of all services"""
    services = {
        "petfinder": bool(_petfinder_token),
        "production_manager": production_manager is not None,
        "websocket_manager": True,
        "monetization_manager": monetization_manager is not None,
    }

    routers = {name: info is not None for name, info in loaded_routers.items()}

    return {
        "services": services,
        "routers": routers,
        "timestamp": datetime.now().isoformat(),
    }


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
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "environment": {
            "host": os.environ.get("HOST", "localhost"),
            "port": os.environ.get("PORT", "8000"),
            "environment": os.environ.get("ENVIRONMENT", "development"),
        },
        "timestamp": datetime.now().isoformat(),
    }


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


# Log startup information
def log_startup_info():
    """Log application startup information"""
    logger.info("🚀 Application startup initiated")
    logger.info(f"📊 Loaded routers: {len([r for r in loaded_routers.values() if r is not None])}")
    logger.info("🔌 WebSocket manager initialized")
    logger.info(f"🏭 Production manager: {'✅' if production_manager else '❌'}")
    logger.info(f"🐾 Petfinder API: {'✅' if _petfinder_token else '❌'}")
    
    if monetization_manager:
        logger.info("💰 Monetization manager: ✅")
    else:
        logger.info("💰 Monetization manager: ❌")
    
    logger.info("✅ Application startup completed")

# Call startup logging
log_startup_info()

# Mount SPA fallback for frontend routes (MUST be last to avoid intercepting API routes)
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="frontend")
    logger.info("✅ Frontend SPA fallback mounted at /")

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
    )
