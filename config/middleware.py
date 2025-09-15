"""Production middleware configuration for FastAPI application."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from time import monotonic
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.security import security_config

# Rate limiting storage
rate_limit_storage = defaultdict(lambda: deque())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in security_config.security_headers.items():
            if value:  # Only add non-empty headers
                response.headers[header] = value
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID and processing time to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Track processing time
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{int(process_time * 1000)}ms"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with per-IP tracking."""
    
    def __init__(self, app: FastAPI, requests_per_minute: int | None = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or security_config.rate_limit_rpm
        self.exempt_paths = {
            "/health",
            "/metrics",
            "/api/version",
            "/api/system/status"
        }
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = monotonic()
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - 60
        client_requests = rate_limit_storage[client_ip]
        while client_requests and client_requests[0] < cutoff_time:
            client_requests.popleft()
        
        # Check rate limit
        if len(client_requests) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute",
                    "request_id": getattr(request.state, "request_id", None)
                },
                headers={"Retry-After": "60"}
            )
        
        # Add current request timestamp
        client_requests.append(current_time)
        
        return await call_next(request)


class NoCacheAPIMiddleware(BaseHTTPMiddleware):
    """Add no-cache headers to API endpoints."""
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        
        # Add no-cache headers to API endpoints
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    
    # Validate security configuration
    if not security_config.validate():
        raise RuntimeError("Security configuration validation failed")
    
    # 1. GZip compression (should be first for response compression)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 2. Trusted host middleware (security)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=security_config.trusted_hosts
    )
    
    # 3. CORS middleware (must be after TrustedHost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.allowed_origins,
        allow_credentials=security_config.allow_credentials,
        allow_methods=security_config.allowed_methods,
        allow_headers=security_config.allowed_headers,
        max_age=600  # Cache preflight requests for 10 minutes
    )
    
    # 4. Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 5. Request ID middleware
    app.add_middleware(RequestIDMiddleware)
    
    # 6. Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=security_config.rate_limit_rpm)
    
    # 7. No-cache API middleware (should be last)
    app.add_middleware(NoCacheAPIMiddleware)
    
    print(f"✅ Middleware configured for {security_config.environment} environment")
    print(f"📡 CORS origins: {security_config.allowed_origins}")
    print(f"🛡️ Trusted hosts: {security_config.trusted_hosts}")
    print(f"⚡ Rate limit: {security_config.rate_limit_rpm} requests/minute")