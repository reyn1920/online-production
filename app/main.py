"""TRAE AI Production FastAPI Application"""

Enterprise-grade FastAPI application with:
- Structured logging
- Security middleware
- API versioning
- Health checks
- Error handling
- CORS configuration
""""""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logger import setup_logging
from app.api.v1.router import api_router
from app.utils.health import health_check
from app.middleware.strip_content_length import StripContentLengthMiddleware
from app.middleware.set_content_length import SetContentLengthMiddleware
from app.middleware.log_headers import LogHeadersMiddleware

# Initialize settings
settings = get_settings()

# Setup structured logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting TRAE AI Production Application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down TRAE AI Production Application")


# Create FastAPI application
app = FastAPI(
    title="TRAE AI Production API",
    description="Enterprise-grade AI-powered content creation and management platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
# BRACKET_SURGEON: disabled
# )

# Security middleware
if settings.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        [settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
# BRACKET_SURGEON: disabled
#     ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
# BRACKET_SURGEON: disabled
# )

# Log Headers middleware (logs HTTP headers for debugging)
app.add_middleware(LogHeadersMiddleware)

# Set Content-Length middleware (calculates and sets Content-Length headers)
app.add_middleware(SetContentLengthMiddleware)

# Strip Content-Length middleware (removes Content-Length headers for streaming)
app.add_middleware(StripContentLengthMiddleware)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()

    # Log request
    logger.info(
        "HTTP Request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        "HTTP Response",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.error(
        "HTTP Exception",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code,
            "detail": exc.detail,
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception",
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(
        "Validation Error",
        extra={
            "method": request.method,
            "url": str(request.url),
            "errors": exc.errors(),
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "type": "validation_error",
                "details": exc.errors(),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected Error",
        extra={
            "method": request.method,
            "url": str(request.url),
            "error_type": type(exc).__name__,
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error" if not settings.DEBUG else str(exc),
                "type": "internal_error",
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_endpoint():
    """Health check endpoint for load balancers and monitoring."""
    return await health_check()


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - indicates if service is ready to receive traffic."""
    try:
        # Check if all critical services are ready
        health_result = await health_check()

        # Service is ready if health check passes and all critical components are healthy
        is_ready = (
            health_result.get("status") == "healthy" and
            health_result.get("checks", {}).get("database", {}).get("status") == "healthy"
# BRACKET_SURGEON: disabled
#         )

        return {
            "ready": is_ready,
            "timestamp": health_result.get("timestamp"),
            "service": "trae-ai-production",
            "checks": health_result.get("checks", {})
# BRACKET_SURGEON: disabled
#         }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "timestamp": datetime.now().isoformat(),
            "service": "trae-ai-production",
            "error": str(e)
# BRACKET_SURGEON: disabled
#         }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check - indicates if service is alive and should not be restarted."""
    try:
        import os
        import threading
        from datetime import datetime

        # Simple liveness check - if we can respond, we're alive
        return {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "service": "trae-ai-production",
            "version": "1.0.0",
            "thread_count": threading.active_count(),
            "pid": os.getpid()
# BRACKET_SURGEON: disabled
#         }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            "alive": False,
            "timestamp": datetime.now().isoformat(),
            "service": "trae-ai-production",
            "error": str(e)
# BRACKET_SURGEON: disabled
#         }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "TRAE AI Production API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
# BRACKET_SURGEON: disabled
#     }


# Common browser requests to prevent 404 errors
@app.get("/favicon.ico", tags=["Static"])
async def favicon():
    """Favicon endpoint to prevent 404 errors."""
    return JSONResponse(status_code=204, content=None)


@app.get("/robots.txt", tags=["Static"])
async def robots_txt():
    """Robots.txt endpoint."""
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse("User-agent: *\nDisallow:")


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
# BRACKET_SURGEON: disabled
#     )