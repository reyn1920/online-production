#!/usr/bin/env python3
"""
Enhanced API Orchestrator - Intelligent API Management System

This module implements the core intelligence for managing 100+ APIs with:
- Automatic failover when APIs fail
- Load balancing across similar APIs
- Health monitoring and priority-based selection
- Usage tracking and daily limit management
"""

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RequestStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass
class APIEndpoint:
    """Represents an API endpoint with all its metadata"""

    id: int
    service_name: str
    capability: str
    api_url: str
    api_key_name: Optional[str]
    priority: int
    daily_limit: Optional[int]
    is_active: bool
    health_status: str
    response_time_ms: int
    success_rate: float
    usage_count: int
    daily_usage_count: int
    rate_limit_per_hour: Optional[int]
    authentication_type: str
    supported_methods: str
    error_count: int
    last_error_message: Optional[str]

    def is_available(self) -> bool:
        """Check if API is available for use"""
        if not self.is_active:
            return False
        if self.health_status == APIHealthStatus.UNHEALTHY.value:
            return False
        if self.daily_limit and self.daily_usage_count >= self.daily_limit:
            return False
        return True

    def get_load_factor(self) -> float:
        """Calculate load factor for load balancing (lower is better)"""
        if not self.daily_limit:
            return self.daily_usage_count / 1000.0  # Arbitrary scaling
        return self.daily_usage_count / self.daily_limit


@dataclass
class OrchestrationRequest:
    """Represents a request to the orchestrator"""

    request_id: str
    capability: str
    payload: Dict[str, Any]
    timeout_seconds: int = 30
    max_retries: int = 3
    prefer_free: bool = True


@dataclass
class OrchestrationResult:
    """Result of an orchestration request"""

    request_id: str
    status: RequestStatus
    response_data: Optional[Dict[str, Any]]
    api_used: Optional[APIEndpoint]
    total_attempts: int
    total_time_ms: int
    error_message: Optional[str]
    fallback_apis_tried: List[int]


class EnhancedAPIOrchestrator:
    """Enhanced API Orchestrator with intelligent failover and load balancing"""

    def __init__(self, db_path: str = "right_perspective.db"):
        self.db_path = db_path
        self.session = None
        self._init_database()

    def _init_database(self):
        """Initialize database connection and ensure tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            # Tables should already exist from schema, but we can add indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_registry_capability 
                ON api_registry(capability, is_active, priority)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_registry_health 
                ON api_registry(health_status, last_health_check)
            """
            )
            conn.commit()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def get_apis_for_capability(
        self, capability: str, limit: int = 10
    ) -> List[APIEndpoint]:
        """Get available APIs for a specific capability, sorted by priority and load"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM api_registry 
                WHERE capability = ? AND is_active = 1 
                AND (health_status != 'unhealthy' OR health_status IS NULL)
                ORDER BY priority ASC, daily_usage_count ASC
                LIMIT ?
            """,
                (capability, limit),
            )

            apis = []
            for row in cursor.fetchall():
                api = APIEndpoint(**dict(row))
                if api.is_available():
                    apis.append(api)

            return apis

    def update_api_usage(
        self,
        api_id: int,
        success: bool,
        response_time_ms: int,
        error_message: str = None,
    ):
        """Update API usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now(timezone.utc).isoformat()

            if success:
                conn.execute(
                    """
                    UPDATE api_registry SET 
                        usage_count = usage_count + 1,
                        daily_usage_count = daily_usage_count + 1,
                        response_time_ms = ?,
                        success_rate = (success_rate * usage_count + 1.0) / (usage_count + 1),
                        last_used = ?,
                        updated_at = ?
                    WHERE id = ?
                """,
                    (response_time_ms, now, now, api_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE api_registry SET 
                        usage_count = usage_count + 1,
                        daily_usage_count = daily_usage_count + 1,
                        error_count = error_count + 1,
                        last_error_message = ?,
                        last_error_timestamp = ?,
                        success_rate = (success_rate * usage_count) / (usage_count + 1),
                        updated_at = ?
                    WHERE id = ?
                """,
                    (error_message, now, now, api_id),
                )

            conn.commit()

    def log_orchestration_attempt(
        self,
        request_id: str,
        capability: str,
        primary_api_id: int,
        fallback_apis: List[int],
        successful_api_id: int = None,
        total_attempts: int = 1,
        total_time_ms: int = 0,
        failure_reasons: List[str] = None,
    ):
        """Log orchestration attempt for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_orchestration_log 
                (request_id, capability_requested, primary_api_id, fallback_apis, 
                 successful_api_id, total_attempts, total_response_time_ms, failure_reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    capability,
                    primary_api_id,
                    json.dumps(fallback_apis),
                    successful_api_id,
                    total_attempts,
                    total_time_ms,
                    json.dumps(failure_reasons or []),
                ),
            )
            conn.commit()

    async def make_api_request(
        self, api: APIEndpoint, payload: Dict[str, Any], timeout: int = 30
    ) -> Tuple[bool, Optional[Dict], int, Optional[str]]:
        """Make a request to a specific API endpoint"""
        start_time = time.time()

        try:
            # Prepare headers
            headers = {"Content-Type": "application/json"}

            # Add authentication if required
            if api.api_key_name and api.authentication_type == "api_key":
                # In a real implementation, you'd retrieve the API key from secure storage
                # headers['Authorization'] = f'Bearer {get_secret(api.api_key_name)}'
                pass

            # Determine HTTP method
            method = "POST" if "POST" in api.supported_methods else "GET"

            # Make the request
            async with self.session.request(
                method=method,
                url=api.api_url,
                json=payload if method == "POST" else None,
                params=payload if method == "GET" else None,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)

                if response.status == 200:
                    data = await response.json()
                    return True, data, response_time_ms, None
                elif response.status == 429:
                    return False, None, response_time_ms, "Rate limited"
                else:
                    error_text = await response.text()
                    return (
                        False,
                        None,
                        response_time_ms,
                        f"HTTP {response.status}: {error_text}",
                    )

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return False, None, response_time_ms, "Request timeout"
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return False, None, response_time_ms, str(e)

    async def orchestrate_request(
        self, request: OrchestrationRequest
    ) -> OrchestrationResult:
        """Main orchestration method with intelligent failover and load balancing"""
        start_time = time.time()

        # Get available APIs for the requested capability
        available_apis = self.get_apis_for_capability(request.capability)

        if not available_apis:
            return OrchestrationResult(
                request_id=request.request_id,
                status=RequestStatus.FAILED,
                response_data=None,
                api_used=None,
                total_attempts=0,
                total_time_ms=0,
                error_message=f"No available APIs for capability: {request.capability}",
                fallback_apis_tried=[],
            )

        # Apply load balancing - sort by load factor
        if len(available_apis) > 1:
            available_apis.sort(key=lambda api: (api.priority, api.get_load_factor()))

        primary_api = available_apis[0]
        fallback_apis = available_apis[1 : request.max_retries]

        attempts = 0
        failure_reasons = []
        apis_tried = []

        # Try primary API first
        for api in [primary_api] + fallback_apis:
            attempts += 1
            apis_tried.append(api.id)

            logger.info(
                f"Attempting request {request.request_id} with {api.service_name} (attempt {attempts})"
            )

            success, response_data, response_time, error_msg = (
                await self.make_api_request(
                    api, request.payload, request.timeout_seconds
                )
            )

            # Update API statistics
            self.update_api_usage(api.id, success, response_time, error_msg)

            if success:
                total_time_ms = int((time.time() - start_time) * 1000)

                # Log successful orchestration
                self.log_orchestration_attempt(
                    request.request_id,
                    request.capability,
                    primary_api.id,
                    [a.id for a in fallback_apis],
                    api.id,
                    attempts,
                    total_time_ms,
                )

                return OrchestrationResult(
                    request_id=request.request_id,
                    status=RequestStatus.SUCCESS,
                    response_data=response_data,
                    api_used=api,
                    total_attempts=attempts,
                    total_time_ms=total_time_ms,
                    error_message=None,
                    fallback_apis_tried=apis_tried[:-1],  # Exclude the successful one
                )
            else:
                failure_reasons.append(f"{api.service_name}: {error_msg}")
                logger.warning(f"API {api.service_name} failed: {error_msg}")

        # All APIs failed
        total_time_ms = int((time.time() - start_time) * 1000)

        # Log failed orchestration
        self.log_orchestration_attempt(
            request.request_id,
            request.capability,
            primary_api.id,
            [a.id for a in fallback_apis],
            None,
            attempts,
            total_time_ms,
            failure_reasons,
        )

        return OrchestrationResult(
            request_id=request.request_id,
            status=RequestStatus.FAILED,
            response_data=None,
            api_used=None,
            total_attempts=attempts,
            total_time_ms=total_time_ms,
            error_message=f"All APIs failed. Reasons: {'; '.join(failure_reasons)}",
            fallback_apis_tried=apis_tried,
        )

    def reset_daily_usage_counts(self):
        """Reset daily usage counts - should be called daily"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE api_registry SET daily_usage_count = 0")
            conn.commit()
            logger.info("Daily usage counts reset")

    def get_orchestration_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get orchestration analytics for the past N days"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get request statistics
            cursor = conn.execute(
                """
                SELECT 
                    capability_requested,
                    COUNT(*) as total_requests,
                    AVG(total_attempts) as avg_attempts,
                    AVG(total_response_time_ms) as avg_response_time,
                    SUM(CASE WHEN successful_api_id IS NOT NULL THEN 1 ELSE 0 END) as successful_requests
                FROM api_orchestration_log 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY capability_requested
            """.format(
                    days
                )
            )

            capability_stats = {}
            for row in cursor.fetchall():
                stats = dict(row)
                stats["success_rate"] = (
                    stats["successful_requests"] / stats["total_requests"]
                    if stats["total_requests"] > 0
                    else 0
                )
                capability_stats[row["capability_requested"]] = stats

            # Get API performance
            cursor = conn.execute(
                """
                SELECT 
                    ar.service_name,
                    ar.capability,
                    COUNT(aol.id) as requests_handled,
                    AVG(aol.total_response_time_ms) as avg_response_time,
                    ar.success_rate,
                    ar.health_status
                FROM api_registry ar
                LEFT JOIN api_orchestration_log aol ON ar.id = aol.successful_api_id
                WHERE aol.created_at >= datetime('now', '-{} days') OR aol.created_at IS NULL
                GROUP BY ar.id
                ORDER BY requests_handled DESC
            """.format(
                    days
                )
            )

            api_performance = [dict(row) for row in cursor.fetchall()]

            return {
                "capability_statistics": capability_stats,
                "api_performance": api_performance,
                "analysis_period_days": days,
            }


# Example usage and testing
async def example_usage():
    """Example of how to use the Enhanced API Orchestrator"""
    async with EnhancedAPIOrchestrator() as orchestrator:
        # Create a sample request
        request = OrchestrationRequest(
            request_id=str(uuid.uuid4()),
            capability="text-generation",
            payload={"prompt": "Hello, world!", "max_tokens": 100},
            timeout_seconds=30,
            max_retries=3,
        )

        # Execute the request
        result = await orchestrator.orchestrate_request(request)

        print(f"Request {result.request_id}:")
        print(f"Status: {result.status.value}")
        print(
            f"API Used: {result.api_used.service_name if result.api_used else 'None'}"
        )
        print(f"Total Attempts: {result.total_attempts}")
        print(f"Total Time: {result.total_time_ms}ms")

        if result.error_message:
            print(f"Error: {result.error_message}")

        # Get analytics
        analytics = orchestrator.get_orchestration_analytics()
        print("\nOrchestration Analytics:")
        print(json.dumps(analytics, indent=2, default=str))


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
