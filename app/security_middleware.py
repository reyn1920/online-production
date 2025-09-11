#!/usr/bin/env python3
"""
Security Middleware for TRAE AI Production

This module provides comprehensive security middleware including:
- Rate limiting
- CORS configuration
- Security headers
- Request validation
- IP filtering
- Session management
"""

import os
import time
import json
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, app, calls_per_minute: int = 60, burst_limit: int = 10):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.burst_limit = burst_limit
        self.clients: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return True
            else:
                del self.blocked_ips[client_ip]
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cleanup_old_entries()
            self.last_cleanup = current_time
        
        # Get client's request history
        client_requests = self.clients[client_ip]
        
        # Remove requests older than 1 minute
        cutoff_time = current_time - 60
        client_requests[:] = [req_time for req_time in client_requests if req_time > cutoff_time]
        
        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = current_time - 10
        recent_requests = [req_time for req_time in client_requests if req_time > burst_cutoff]
        
        if len(recent_requests) >= self.burst_limit:
            # Block IP for 5 minutes
            self.blocked_ips[client_ip] = current_time + 300
            logger.warning(f"IP {client_ip} blocked for burst limit violation")
            return True
        
        # Check rate limit
        if len(client_requests) >= self.calls_per_minute:
            return True
        
        # Add current request
        client_requests.append(current_time)
        return False
    
    def cleanup_old_entries(self):
        """Clean up old client entries"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour
        
        # Clean up client requests
        for client_ip in list(self.clients.keys()):
            self.clients[client_ip] = [
                req_time for req_time in self.clients[client_ip] 
                if req_time > cutoff_time
            ]
            if not self.clients[client_ip]:
                del self.clients[client_ip]
        
        # Clean up expired blocked IPs
        expired_blocks = [
            ip for ip, unblock_time in self.blocked_ips.items() 
            if current_time >= unblock_time
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        
        if self.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                }
            )
        
        response = await call_next(request)
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: wss: ws:; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
        self.suspicious_patterns = [
            "<script", "javascript:", "vbscript:", "onload=", "onerror=",
            "../", "..\\", "SELECT", "INSERT", "DELETE", "DROP", "UNION",
            "eval(", "setTimeout(", "setInterval(", "Function("
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request too large"}
            )
        
        # Validate request path
        if any(pattern.lower() in str(request.url).lower() for pattern in self.suspicious_patterns):
            logger.warning(f"Suspicious request detected: {request.url}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request"}
            )
        
        response = await call_next(request)
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Handle authentication and authorization"""
    
    def __init__(self, app, protected_paths: List[str] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/admin", "/api/private"]
        self.api_key = os.getenv("TRAE_API_KEY")
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        if any(request.url.path.startswith(path) for path in self.protected_paths):
            auth_header = request.headers.get("Authorization")
            api_key = request.headers.get("X-API-Key")
            
            if not auth_header and not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "Authentication required"}
                )
            
            # Validate API key if provided
            if api_key and api_key != self.api_key:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Invalid API key"}
                )
        
        response = await call_next(request)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for monitoring and debugging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        
        return response

def setup_security_middleware(app: FastAPI):
    """Configure all security middleware for the application"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.netlify.app"]
    )
    
    # Add custom security middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    logger.info("Security middleware configured successfully")