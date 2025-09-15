"""Request Timeout Middleware for Production

Provides request-level timeout protection to prevent hanging requests
and ensure responsive behavior in production environments.
"""

import asyncio
import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to handle request timeouts"""
    
    def __init__(self, app, timeout: float = 30.0):
        super().__init__(app)
        self.timeout = timeout
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request with timeout protection"""
        try:
            # Apply timeout to the request
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout after {self.timeout}s for {request.url}")
            return Response(
                content="Request timeout",
                status_code=408,
                headers={"Content-Type": "text/plain"}
            )
        except Exception as e:
            logger.error(f"Error in timeout middleware: {e}")
            return Response(
                content="Internal server error",
                status_code=500,
                headers={"Content-Type": "text/plain"}
            )