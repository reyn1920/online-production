"""Request Timeout Middleware for Production

Provides request-level timeout protection to prevent hanging requests
and ensure responsive behavior in production environments.
"""

import asyncio
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts and prevent hanging requests"""
    
    def __init__(
        self,
        app,
        default_timeout: float = 30.0,
        api_timeout: float = 60.0,
        static_timeout: float = 10.0,
        health_timeout: float = 5.0
    ):
        super().__init__(app)
        self.default_timeout = default_timeout
        self.api_timeout = api_timeout
        self.static_timeout = static_timeout
        self.health_timeout = health_timeout
        
    def _get_timeout_for_path(self, path: str) -> float:
        """Determine appropriate timeout based on request path"""
        if path.startswith('/api/'):
            return self.api_timeout
        elif path.startswith('/static/') or path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            return self.static_timeout
        elif path in ['/health', '/api/health', '/status']:
            return self.health_timeout
        else:
            return self.default_timeout
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with timeout protection"""
        start_time = time.time()
        path = request.url.path
        timeout = self._get_timeout_for_path(path)
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            
            # Add timing headers
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Timeout-Used"] = f"{timeout}"
            
            return response
            
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            
            logger.warning(
                f"Request timeout after {process_time:.3f}s (limit: {timeout}s): {request.method} {path}",
                extra={
                    "method": request.method,
                    "path": path,
                    "timeout": timeout,
                    "process_time": process_time,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request Timeout",
                    "message": f"Request exceeded {timeout}s timeout limit",
                    "timeout": timeout,
                    "path": path
                },
                headers={
                    "X-Process-Time": f"{process_time:.3f}",
                    "X-Timeout-Used": f"{timeout}",
                    "Retry-After": "5"
                }
            )
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            logger.error(
                f"Unexpected error in timeout middleware: {exc}",
                extra={
                    "method": request.method,
                    "path": path,
                    "process_time": process_time,
                    "error": str(exc)
                }
            )
            
            # Re-raise the exception to be handled by other middleware
            raise


class AdaptiveTimeoutMiddleware(BaseHTTPMiddleware):
    """Advanced timeout middleware with adaptive timeouts based on endpoint performance"""
    
    def __init__(
        self,
        app,
        base_timeout: float = 30.0,
        max_timeout: float = 120.0,
        min_timeout: float = 5.0,
        adaptation_factor: float = 1.5
    ):
        super().__init__(app)
        self.base_timeout = base_timeout
        self.max_timeout = max_timeout
        self.min_timeout = min_timeout
        self.adaptation_factor = adaptation_factor
        
        # Track endpoint performance
        self.endpoint_stats = {}
        
    def _get_adaptive_timeout(self, path: str) -> float:
        """Calculate adaptive timeout based on historical performance"""
        if path not in self.endpoint_stats:
            return self.base_timeout
            
        stats = self.endpoint_stats[path]
        avg_time = stats.get('avg_time', self.base_timeout)
        
        # Adaptive timeout = average time * adaptation factor
        adaptive_timeout = avg_time * self.adaptation_factor
        
        # Clamp to min/max bounds
        return max(self.min_timeout, min(adaptive_timeout, self.max_timeout))
    
    def _update_stats(self, path: str, process_time: float):
        """Update endpoint performance statistics"""
        if path not in self.endpoint_stats:
            self.endpoint_stats[path] = {
                'count': 0,
                'total_time': 0.0,
                'avg_time': 0.0
            }
        
        stats = self.endpoint_stats[path]
        stats['count'] += 1
        stats['total_time'] += process_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        # Keep only recent data (sliding window)
        if stats['count'] > 100:
            stats['count'] = 50
            stats['total_time'] = stats['avg_time'] * 50
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with adaptive timeout"""
        start_time = time.time()
        path = request.url.path
        timeout = self._get_adaptive_timeout(path)
        
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            
            process_time = time.time() - start_time
            self._update_stats(path, process_time)
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Adaptive-Timeout"] = f"{timeout:.1f}"
            
            return response
            
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            
            logger.warning(
                f"Adaptive timeout exceeded: {request.method} {path} ({process_time:.3f}s/{timeout:.1f}s)",
                extra={
                    "method": request.method,
                    "path": path,
                    "timeout": timeout,
                    "process_time": process_time
                }
            )
            
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request Timeout",
                    "message": f"Request exceeded adaptive timeout of {timeout:.1f}s",
                    "timeout": timeout,
                    "path": path
                },
                headers={
                    "X-Process-Time": f"{process_time:.3f}",
                    "X-Adaptive-Timeout": f"{timeout:.1f}",
                    "Retry-After": "10"
                }
            )
            
        except Exception as exc:
            logger.error(f"Error in adaptive timeout middleware: {exc}")
            raise