#!/usr / bin / env python3
""""""
API Orchestrator - Intelligent API Management and Failover System

This module provides intelligent API selection, load balancing, and automatic failover
capabilities for the TRAE.AI system. It manages multiple API endpoints, monitors their
health, and automatically routes requests to the best available API.

Features:
- Automatic API health monitoring
- Intelligent failover based on response times and error rates
- Load balancing across multiple API endpoints
- Rate limit management and throttling
- Configurable failover policies
- Real - time API performance tracking
""""""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests


class APIStatus(Enum):
    """API status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FailoverStrategy(Enum):
    """Failover strategy enumeration"""

    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"
    PERFORMANCE_BASED = "performance_based"
    LEAST_LOADED = "least_loaded"

@dataclass


class APIEndpoint:
    """Represents an API endpoint with its configuration and status"""

    id: int
    api_name: str
    base_url: str
    authentication_type: str
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    status: str
    health_status: str
    allow_automatic_failover: bool
    failover_priority: int
    average_response_time: float = 0.0
    success_rate: float = 1.0
    current_usage_minute: int = 0
    current_usage_hour: int = 0
    last_health_check: Optional[datetime] = None
    configuration: Optional[Dict] = None

@dataclass


class APIRequest:
    """Represents an API request with metadata"""

    endpoint: str
    method: str
    headers: Optional[Dict] = None
    body: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    priority: str = "normal"

@dataclass


class APIResponse:
    """Represents an API response with performance metrics"""

    status_code: int
    headers: Dict
    body: str
    response_time_ms: int
    api_name: str
    success: bool
    error_message: Optional[str] = None


class APIOrchestrator:
    """"""
    Intelligent API orchestrator that manages multiple API endpoints,
        provides automatic failover, load balancing, and health monitoring.
    """"""


    def __init__(
        self,
            db_path: str = "right_perspective.db",
            health_check_interval: int = 300,
            failover_strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED,
# BRACKET_SURGEON: disabled
#             ):
        self.db_path = db_path
        self.health_check_interval = health_check_interval
        self.failover_strategy = failover_strategy
        self.logger = logging.getLogger(__name__)

        # API endpoint cache
        self.api_endpoints: Dict[str, APIEndpoint] = {}
        self.api_lock = threading.RLock()

        # Performance tracking
        self.performance_history: Dict[str, List[float]] = {}
        self.request_counts: Dict[str, int] = {}

        # Health monitoring
        self.health_monitor_running = False
        self.health_monitor_task = None

        # Thread pool for concurrent requests
        self.executor = ThreadPoolExecutor(max_workers = 10)

        # Initialize
        self._load_api_endpoints()
        self._start_health_monitoring()

        self.logger.info(
            f"API Orchestrator initialized with {len(self.api_endpoints)} endpoints"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )


    def _load_api_endpoints(self) -> None:
        """Load API endpoints from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """"""
                    SELECT id, api_name, base_url, authentication_type,
                        rate_limit_per_minute, rate_limit_per_hour, status,
                               health_status, allow_automatic_failover, failover_priority,
                               average_response_time, success_rate, current_usage_minute,
                               current_usage_hour, last_health_check, configuration
                    FROM api_registry
                    WHERE status = 'active'
                    ORDER BY failover_priority ASC
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                rows = cursor.fetchall()

                with self.api_lock:
                    self.api_endpoints.clear()

                    for row in rows:
                        endpoint = APIEndpoint(
                            id = row[0],
                                api_name = row[1],
                                base_url = row[2],
                                authentication_type = row[3],
                                rate_limit_per_minute = row[4] or 60,
                                rate_limit_per_hour = row[5] or 3600,
                                status = row[6],
                                health_status = row[7] or "unknown",
                                allow_automatic_failover = bool(row[8]),
                                failover_priority = row[9] or 1,
                                average_response_time = row[10] or 0.0,
                                success_rate = row[11] or 1.0,
                                current_usage_minute = row[12] or 0,
                                current_usage_hour = row[13] or 0,
                                last_health_check=(
                                datetime.fromisoformat(row[14]) if row[14] else None
# BRACKET_SURGEON: disabled
#                             ),
                                configuration = json.loads(row[15]) if row[15] else {},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )

                        self.api_endpoints[endpoint.api_name] = endpoint

                        # Initialize performance tracking
                        if endpoint.api_name not in self.performance_history:
                            self.performance_history[endpoint.api_name] = []
                        if endpoint.api_name not in self.request_counts:
                            self.request_counts[endpoint.api_name] = 0

                self.logger.info(f"Loaded {len(self.api_endpoints)} API endpoints")

        except Exception as e:
            self.logger.error(f"Failed to load API endpoints: {e}")
            raise


    def _start_health_monitoring(self) -> None:
        """Start background health monitoring"""
        if not self.health_monitor_running:
            self.health_monitor_running = True
            self.health_monitor_task = threading.Thread(
                target = self._health_monitor_loop, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.health_monitor_task.start()
            self.logger.info("Health monitoring started")


    def _health_monitor_loop(self) -> None:
        """Background health monitoring loop"""
        while self.health_monitor_running:
            try:
                self._check_all_endpoints_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait before retry


    def _check_all_endpoints_health(self) -> None:
        """Check health of all API endpoints"""
        with self.api_lock:
            endpoints = list(self.api_endpoints.values())

        for endpoint in endpoints:
            try:
                self._check_endpoint_health(endpoint)
            except Exception as e:
                self.logger.error(f"Health check failed for {endpoint.api_name}: {e}")


    def _check_endpoint_health(self, endpoint: APIEndpoint) -> None:
        """Check health of a specific endpoint"""
        health_url = (
            endpoint.configuration.get("health_check_url")
            if endpoint.configuration
            else None
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        if not health_url:
            health_url = f"{endpoint.base_url.rstrip('/')}/health"

        start_time = time.time()

        try:
            response = requests.get(health_url, timeout = 10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Determine health status
            if response.status_code == 200:
                if response_time < 1000:  # Less than 1 second
                    health_status = APIStatus.HEALTHY.value
                elif response_time < 5000:  # Less than 5 seconds
                    health_status = APIStatus.DEGRADED.value
                else:
                    health_status = APIStatus.UNHEALTHY.value
            else:
                health_status = APIStatus.UNHEALTHY.value

            # Update endpoint
            with self.api_lock:
                if endpoint.api_name in self.api_endpoints:
                    self.api_endpoints[endpoint.api_name].health_status = health_status
                    self.api_endpoints[endpoint.api_name].last_health_check = (
                        datetime.now()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    self.api_endpoints[endpoint.api_name].average_response_time = (
                        response_time
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Update database
            self._update_endpoint_health(
                endpoint.api_name, health_status, response_time
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            self.logger.debug(
                f"Health check for {endpoint.api_name}: {health_status} ({response_time:.0f}ms)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        except Exception as e:
            health_status = APIStatus.UNHEALTHY.value

            with self.api_lock:
                if endpoint.api_name in self.api_endpoints:
                    self.api_endpoints[endpoint.api_name].health_status = health_status
                    self.api_endpoints[endpoint.api_name].last_health_check = (
                        datetime.now()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            self._update_endpoint_health(endpoint.api_name, health_status, 0)
            self.logger.warning(f"Health check failed for {endpoint.api_name}: {e}")


    def _update_endpoint_health(
        self, api_name: str, health_status: str, response_time: float
# BRACKET_SURGEON: disabled
#     ) -> None:
        """Update endpoint health in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """"""
                    UPDATE api_registry
                    SET health_status = ?,
                        average_response_time = ?,
                            last_health_check = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                    WHERE api_name = ?
                ""","""
                    (health_status, response_time, api_name),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update endpoint health for {api_name}: {e}")


    def select_best_api(
        self, api_type: str = None, exclude_apis: List[str] = None
    ) -> Optional[APIEndpoint]:
        """Select the best available API endpoint based on the configured strategy"""
        exclude_apis = exclude_apis or []

        with self.api_lock:
            # Filter available endpoints
            available_endpoints = [
                endpoint
                for endpoint in self.api_endpoints.values()
                if (
                    endpoint.status == "active"
                    and endpoint.api_name not in exclude_apis
                    and endpoint.health_status in ["healthy", "degraded"]
                    and self._check_rate_limits(endpoint)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ]

            if not available_endpoints:
                self.logger.warning("No healthy API endpoints available")
                return None

            # Apply selection strategy
            if self.failover_strategy == FailoverStrategy.PRIORITY_BASED:
                return min(available_endpoints, key = lambda x: x.failover_priority)

            elif self.failover_strategy == FailoverStrategy.PERFORMANCE_BASED:
                return min(available_endpoints, key = lambda x: x.average_response_time)

            elif self.failover_strategy == FailoverStrategy.LEAST_LOADED:
                return min(available_endpoints, key = lambda x: x.current_usage_minute)

            elif self.failover_strategy == FailoverStrategy.ROUND_ROBIN:
                # Simple round - robin based on request count
                return min(
                    available_endpoints,
                        key = lambda x: self.request_counts.get(x.api_name, 0),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

            else:
                # Default to priority - based
                return min(available_endpoints, key = lambda x: x.failover_priority)


    def _check_rate_limits(self, endpoint: APIEndpoint) -> bool:
        """Check if endpoint is within rate limits"""
        now = datetime.now()

        # Check minute limit
        if endpoint.current_usage_minute >= endpoint.rate_limit_per_minute:
            return False

        # Check hour limit
        if endpoint.current_usage_hour >= endpoint.rate_limit_per_hour:
            return False

        return True


    async def make_request(
        self, request: APIRequest, api_name: str = None
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Make an API request with automatic failover"""
        excluded_apis = []
        max_retries = 3

        for attempt in range(max_retries):
            # Select API endpoint
            if api_name and attempt == 0:
                # Try specific API first
                endpoint = self.api_endpoints.get(api_name)
                if not endpoint or not endpoint.allow_automatic_failover:
                    excluded_apis.append(api_name)
                    endpoint = None
            else:
                endpoint = self.select_best_api(exclude_apis = excluded_apis)

            if not endpoint:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"No available API endpoint,"
    retrying in 5 seconds (attempt {attempt + 1}/{max_retries})""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    await asyncio.sleep(5)
                    continue
                else:
                    raise Exception(
                        "No healthy API endpoints available after all retries"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            try:
                # Make the request
                response = await self._execute_request(endpoint, request)

                # Update success metrics
                self._update_request_metrics(
                    endpoint.api_name, True, response.response_time_ms
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                return response

            except Exception as e:
                self.logger.warning(f"Request failed on {endpoint.api_name}: {e}")

                # Update failure metrics
                self._update_request_metrics(endpoint.api_name, False, 0)

                # Add to excluded list for next attempt
                excluded_apis.append(endpoint.api_name)

                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise Exception(
                        f"All API requests failed after {max_retries} attempts: {e}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def _execute_request(
        self, endpoint: APIEndpoint, request: APIRequest
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Execute the actual API request"""
        url = f"{endpoint.base_url.rstrip('/')}/{request.endpoint.lstrip('/')}"

        # Prepare headers
        headers = request.headers or {}

        # Add authentication if configured
        if endpoint.authentication_type == "api_key" and endpoint.configuration:
            api_key = endpoint.configuration.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        start_time = time.time()

        try:
            # Make the request
            if request.method.upper() == "GET":
                response = requests.get(url,
    headers = headers,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     timeout = request.timeout)
            elif request.method.upper() == "POST":
                response = requests.post(
                    url, headers = headers, data = request.body, timeout = request.timeout
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            elif request.method.upper() == "PUT":
                response = requests.put(
                    url, headers = headers, data = request.body, timeout = request.timeout
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            elif request.method.upper() == "DELETE":
                response = requests.delete(
                    url, headers = headers, timeout = request.timeout
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                raise ValueError(f"Unsupported HTTP method: {request.method}")

            response_time_ms = int((time.time() - start_time) * 1000)

            # Log the request
            self._log_api_request(endpoint, request, response, response_time_ms)

            return APIResponse(
                status_code = response.status_code,
                    headers = dict(response.headers),
                    body = response.text,
                    response_time_ms = response_time_ms,
                    api_name = endpoint.api_name,
                    success = 200 <= response.status_code < 300,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log the failed request
            self._log_api_request(endpoint, request, None, response_time_ms, str(e))

            raise Exception(f"Request to {endpoint.api_name} failed: {e}")


    def _update_request_metrics(
        self, api_name: str, success: bool, response_time_ms: int
# BRACKET_SURGEON: disabled
#     ) -> None:
        """Update request metrics for an API endpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Update usage counters
                cursor.execute(
                    """"""
                    UPDATE api_registry
                    SET current_usage_minute = current_usage_minute + 1,
                        current_usage_hour = current_usage_hour + 1,
                            total_requests = total_requests + 1,
                            total_errors = total_errors + ?,
                            updated_at = CURRENT_TIMESTAMP
                    WHERE api_name = ?
                ""","""
                    (0 if success else 1, api_name),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                # Calculate new success rate
                cursor.execute(
                    """"""
                    SELECT total_requests, total_errors
                    FROM api_registry
                    WHERE api_name = ?
                ""","""
                    (api_name,),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                row = cursor.fetchone()
                if row:
                    total_requests, total_errors = row
                    success_rate = (
                        (total_requests - total_errors) / total_requests
                        if total_requests > 0
                        else 1.0
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                    cursor.execute(
                        """"""
                        UPDATE api_registry
                        SET success_rate = ?
                        WHERE api_name = ?
                    ""","""
                        (success_rate, api_name),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

                conn.commit()

                # Update in - memory tracking
                with self.api_lock:
                    if api_name in self.request_counts:
                        self.request_counts[api_name] += 1

                    if api_name in self.performance_history:
                        self.performance_history[api_name].append(response_time_ms)
                        # Keep only last 100 measurements
                        if len(self.performance_history[api_name]) > 100:
                            self.performance_history[api_name] = (
                                self.performance_history[api_name][-100:]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

        except Exception as e:
            self.logger.error(f"Failed to update request metrics for {api_name}: {e}")


    def _log_api_request(
        self,
            endpoint: APIEndpoint,
            request: APIRequest,
            response: Optional[requests.Response],
            response_time_ms: int,
            error_message: str = None,
# BRACKET_SURGEON: disabled
#             ) -> None:
        """Log API request details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                request_id = f"{endpoint.api_name}_{int(time.time() * 1000)}"

                cursor.execute(
                    """"""
                    INSERT INTO api_request_logs (
                        api_id, request_id, endpoint, method, request_headers,
                            request_body, response_status, response_headers, response_body,
                            response_time_ms, error_message, timestamp
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ""","""
                    (
                        endpoint.id,
                            request_id,
                            request.endpoint,
                            request.method,
                            json.dumps(request.headers) if request.headers else None,
                            request.body,
                            response.status_code if response else None,
                            json.dumps(dict(response.headers)) if response else None,
                            response.text if response else None,
                            response_time_ms,
                            error_message,
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log API request: {e}")


    def get_api_status(self) -> Dict[str, Any]:
        """Get current status of all API endpoints"""
        with self.api_lock:
            status = {
                "total_endpoints": len(self.api_endpoints),
                    "healthy_endpoints": len(
                    [
                        e
                        for e in self.api_endpoints.values()
                        if e.health_status == "healthy"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]
# BRACKET_SURGEON: disabled
#                 ),
                    "degraded_endpoints": len(
                    [
                        e
                        for e in self.api_endpoints.values()
                        if e.health_status == "degraded"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]
# BRACKET_SURGEON: disabled
#                 ),
                    "unhealthy_endpoints": len(
                    [
                        e
                        for e in self.api_endpoints.values()
                        if e.health_status == "unhealthy"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]
# BRACKET_SURGEON: disabled
#                 ),
                    "endpoints": {},
# BRACKET_SURGEON: disabled
#                     }

            for name, endpoint in self.api_endpoints.items():
                status["endpoints"][name] = {
                    "status": endpoint.status,
                        "health_status": endpoint.health_status,
                        "success_rate": endpoint.success_rate,
                        "average_response_time": endpoint.average_response_time,
                        "current_usage_minute": endpoint.current_usage_minute,
                        "current_usage_hour": endpoint.current_usage_hour,
                        "allow_automatic_failover": endpoint.allow_automatic_failover,
                        "failover_priority": endpoint.failover_priority,
                        "last_health_check": (
                        endpoint.last_health_check.isoformat()
                        if endpoint.last_health_check
                        else None
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                         }

            return status


    def reload_endpoints(self) -> None:
        """Reload API endpoints from database"""
        self.logger.info("Reloading API endpoints from database")
        self._load_api_endpoints()


    def shutdown(self) -> None:
        """Shutdown the orchestrator"""
        self.logger.info("Shutting down API orchestrator")
        self.health_monitor_running = False

        if self.health_monitor_task and self.health_monitor_task.is_alive():
            self.health_monitor_task.join(timeout = 5)

        self.executor.shutdown(wait = True)
        self.logger.info("API orchestrator shutdown complete")

# Convenience functions for easy integration


def create_api_orchestrator(db_path: str = "right_perspective.db") -> APIOrchestrator:
    """Create and return a configured API orchestrator instance"""
    return APIOrchestrator(db_path = db_path)


async def make_api_request(
    endpoint: str,
        method: str = "GET",
        headers: Dict = None,
        body: str = None,
        api_name: str = None,
        orchestrator: APIOrchestrator = None,
# BRACKET_SURGEON: disabled
# ) -> APIResponse:
    """Convenience function to make an API request with automatic failover"""
    if orchestrator is None:
        orchestrator = create_api_orchestrator()

    request = APIRequest(endpoint = endpoint,
    method = method,
    headers = headers,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     body = body)

    return await orchestrator.make_request(request, api_name = api_name)