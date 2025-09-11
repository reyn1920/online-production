import asyncio
import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    """Represents an API endpoint with its configuration and status"""

    id: int
    api_name: str
    base_url: str
    api_version: Optional[str]
    capability: str
    authentication_type: str
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    rate_limit_per_day: Optional[int]
    current_usage_minute: int
    current_usage_hour: int
    current_usage_day: int
    last_reset_minute: Optional[str]
    last_reset_hour: Optional[str]
    last_reset_day: Optional[str]
    status: str
    health_check_url: Optional[str]
    last_health_check: Optional[str]
    health_status: str
    average_response_time: Optional[float]
    success_rate: Optional[float]
    total_requests: int
    total_errors: int
    allow_automatic_failover: bool
    failover_priority: int
    priority: int
    configuration: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]

    def is_available(self) -> bool:
        """Check if API is available for use"""
        if self.status != "active":
            return False
        if (
            self.rate_limit_per_day
            and self.current_usage_day >= self.rate_limit_per_day
        ):
            return False
        if self.health_status == APIHealthStatus.UNHEALTHY.value:
            return False
        return True

    def get_load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)"""
        if not self.rate_limit_per_day:
            return 0.0
        return min(1.0, self.current_usage_day / self.rate_limit_per_day)


@dataclass
class OrchestrationRequest:
    """Represents a request to be orchestrated across APIs"""

    request_id: str
    capability: str
    payload: Dict[str, Any]
    timeout_seconds: int = 30
    max_retries: int = 3
    prefer_free: bool = True


@dataclass
class OrchestrationResult:
    """Result of an orchestrated API request"""

    request_id: str
    status: RequestStatus
    response_data: Optional[Dict[str, Any]]
    api_used: Optional[APIEndpoint]
    total_attempts: int
    total_time_ms: int
    error_message: Optional[str]
    fallback_apis_tried: List[str]


class EnhancedAPIOrchestrator:
    """Enhanced API orchestrator with intelligent failover and load balancing"""

    def __init__(self, db_path: str = "intelligence.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Create orchestration log table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_orchestration_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    capability_requested TEXT NOT NULL,
                    successful_api_id INTEGER,
                    failed_api_ids TEXT,
                    total_attempts INTEGER NOT NULL,
                    total_response_time_ms INTEGER NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create API usage tracking table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_id INTEGER NOT NULL,
                    request_id TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    response_time_ms INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_only TEXT NOT NULL
                )
            """
            )

            conn.commit()

    async def get_available_apis(
        self, capability: str, prefer_free: bool = True
    ) -> List[APIEndpoint]:
        """Get available APIs for a capability, sorted by priority and load"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, api_name, base_url, api_version, capability, authentication_type,
                       rate_limit_per_minute, rate_limit_per_hour, rate_limit_per_day,
                       current_usage_minute, current_usage_hour, current_usage_day,
                       last_reset_minute, last_reset_hour, last_reset_day,
                       status, health_check_url, last_health_check, health_status,
                       average_response_time, success_rate, total_requests, total_errors,
                       allow_automatic_failover, failover_priority, priority,
                       configuration, created_at, updated_at, created_by
                FROM api_registry 
                WHERE capability = ? AND status = 'active'
                ORDER BY priority ASC, current_usage_day ASC
            """,
                (capability,),
            )

            apis = []
            for row in cursor.fetchall():
                # Create APIEndpoint with explicit field mapping
                api = APIEndpoint(
                    id=row[0],
                    api_name=row[1],
                    base_url=row[2],
                    api_version=row[3],
                    capability=row[4],
                    authentication_type=row[5],
                    rate_limit_per_minute=row[6],
                    rate_limit_per_hour=row[7],
                    rate_limit_per_day=row[8],
                    current_usage_minute=row[9] or 0,
                    current_usage_hour=row[10] or 0,
                    current_usage_day=row[11] or 0,
                    last_reset_minute=row[12],
                    last_reset_hour=row[13],
                    last_reset_day=row[14],
                    status=row[15],
                    health_check_url=row[16],
                    last_health_check=row[17],
                    health_status=row[18],
                    average_response_time=row[19] or 0.0,
                    success_rate=row[20] or 100.0,
                    total_requests=row[21] or 0,
                    total_errors=row[22] or 0,
                    allow_automatic_failover=row[23] if row[23] is not None else True,
                    failover_priority=row[24] or 1,
                    priority=row[25] or 5,
                    configuration=row[26],
                    created_at=row[27],
                    updated_at=row[28],
                    created_by=row[29],
                )
                if api.is_available():
                    apis.append(api)

            # Sort by preference (free first if preferred) and load factor
            if prefer_free:
                apis.sort(
                    key=lambda x: (
                        x.rate_limit_per_day is not None,
                        x.get_load_factor(),
                        x.priority,
                    )
                )
            else:
                apis.sort(key=lambda x: (x.get_load_factor(), x.priority))

            return apis

    async def make_api_request(
        self, api: APIEndpoint, payload: Dict[str, Any], timeout: int = 30
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Make a request to a specific API endpoint"""
        start_time = time.time()

        try:
            # For avatar generation engines, we need to handle them specially
            if api.capability == "avatar-generation":
                return await self._make_avatar_request(api, payload, timeout)

            # Get API key if required
            api_key = None
            if api.authentication_type != "none":
                api_key = self._get_api_key(f"{api.api_name.upper()}_API_KEY")
                if not api_key and api.authentication_type != "none":
                    return False, None, f"API key not found for {api.api_name}"

            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                if api.authentication_type == "bearer_token":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif api.authentication_type == "api_key":
                    headers["X-API-Key"] = api_key
                elif api.authentication_type == "basic_auth":
                    headers["Authorization"] = f"Basic {api_key}"

            # Make the request
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.post(
                    api.base_url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return True, result, None
                    elif response.status == 429:
                        return False, None, "Rate limited"
                    else:
                        error_text = await response.text()
                        return False, None, f"HTTP {response.status}: {error_text}"

        except asyncio.TimeoutError:
            return False, None, "Request timeout"
        except Exception as e:
            return False, None, str(e)

    async def _make_avatar_request(
        self, api: APIEndpoint, payload: Dict[str, Any], timeout: int = 30
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Handle avatar generation requests with engine-specific logic"""
        try:
            # Import avatar engine services
            from backend.services.avatar_engines import AvatarRequest, engine_manager

            # Parse configuration
            config = {}
            if api.configuration:
                config = json.loads(api.configuration)

            # Get the appropriate engine
            engine = await engine_manager.get_engine(api.api_name)
            if not engine:
                return False, None, f"Avatar engine {api.api_name} not found"

            # Check engine health
            if not await engine.health_check():
                return False, None, f"Avatar engine {api.api_name} is not responding"

            # Create avatar request
            avatar_request = AvatarRequest(
                text=payload.get("text", ""),
                voice_settings=payload.get("voice_settings", {}),
                video_settings=payload.get("video_settings", {}),
                source_image=payload.get("source_image"),
            )

            # Generate avatar using the engine
            response = await engine.generate_avatar(avatar_request)

            if response.success:
                result = {
                    "status": "success",
                    "engine_used": response.engine_used,
                    "video_path": response.video_path,
                    "duration": response.duration,
                    "processing_time": response.processing_time,
                    "quality": config.get("quality", "medium"),
                    "message": f"Avatar generated successfully using {api.api_name}",
                }
                return True, result, None
            else:
                return (
                    False,
                    None,
                    response.error_message
                    or f"Avatar generation failed using {api.api_name}",
                )

        except Exception as e:
            return False, None, f"Avatar generation failed: {str(e)}"

    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Retrieve API key from environment or secure storage"""
        import os

        return os.getenv(key_name)

    async def orchestrate_request(
        self, request: OrchestrationRequest
    ) -> OrchestrationResult:
        """Main orchestration method with intelligent API selection and failover"""
        start_time = time.time()
        failed_apis = []

        # Get available APIs for this capability, sorted by priority
        available_apis = await self.get_available_apis(
            request.capability, request.prefer_free
        )

        if not available_apis:
            return OrchestrationResult(
                request_id=request.request_id,
                status=RequestStatus.FAILED,
                response_data=None,
                api_used=None,
                total_attempts=0,
                total_time_ms=int((time.time() - start_time) * 1000),
                error_message=f"No available APIs for capability: {request.capability}",
                fallback_apis_tried=[],
            )

        failover_triggered = False

        # Log the orchestration attempt
        logger.info(
            f"Starting orchestration for capability '{request.capability}' with {len(available_apis)} available APIs"
        )

        # Try each API in order of priority (automatic failover)
        for attempt, api in enumerate(available_apis[: request.max_retries], 1):
            # Log which API we're trying
            if attempt > 1:
                failover_triggered = True
                logger.info(
                    f"Failover triggered: Attempting API '{api.api_name}' (priority {api.priority}) - Attempt {attempt}"
                )
            else:
                logger.info(
                    f"Primary attempt: Using API '{api.api_name}' (priority {api.priority})"
                )

            success, response_data, error_message = await self.make_api_request(
                api, request.payload, request.timeout_seconds
            )

            # Log the attempt
            await self._log_api_usage(
                api.api_name,
                request.request_id,
                request.capability,
                int((time.time() - start_time) * 1000),
                success,
                error_message,
            )

            if success:
                # Success! Log and return
                total_time_ms = int((time.time() - start_time) * 1000)
                await self._log_orchestration_result(
                    request.request_id,
                    request.capability,
                    api.api_name,
                    failed_apis,
                    attempt,
                    total_time_ms,
                    None,
                )

                # Add orchestration metadata to response
                if isinstance(response_data, dict):
                    response_data["_orchestration"] = {
                        "api_used": api.api_name,
                        "priority": api.priority,
                        "attempts_made": attempt,
                        "failover_triggered": failover_triggered,
                        "response_time_ms": round(total_time_ms, 2),
                    }

                logger.info(
                    f"Request {request.request_id} completed successfully using {api.api_name} after {attempt} attempts"
                )

                return OrchestrationResult(
                    request_id=request.request_id,
                    status=RequestStatus.SUCCESS,
                    response_data=response_data,
                    api_used=api,
                    total_attempts=attempt,
                    total_time_ms=total_time_ms,
                    error_message=None,
                    fallback_apis_tried=failed_apis,
                )
            else:
                # Failed, add to failed list and continue
                failed_apis.append(api.api_name)
                logger.warning(f"API {api.api_name} failed: {error_message}")

                # If this was a rate limit error, skip to next API immediately
                if "Rate limited" in str(error_message):
                    logger.info(f"Rate limit hit for {api.api_name}, trying next API")
                    continue

                # For avatar generation, if primary engine fails, immediately try fallback
                if request.capability == "avatar-generation" and api.priority == 1:
                    logger.warning(
                        f"Primary avatar engine {api.api_name} failed, triggering immediate failover"
                    )
                    continue

        # All APIs failed
        total_time_ms = int((time.time() - start_time) * 1000)
        final_error = (
            f"All {len(failed_apis)} APIs failed for capability {request.capability}"
        )

        logger.error(
            f"All APIs failed for request {request.request_id}. Last error: {final_error}"
        )

        await self._log_orchestration_result(
            request.request_id,
            request.capability,
            None,
            failed_apis,
            len(failed_apis),
            total_time_ms,
            final_error,
        )

        return OrchestrationResult(
            request_id=request.request_id,
            status=RequestStatus.FAILED,
            response_data=None,
            api_used=None,
            total_attempts=len(failed_apis),
            total_time_ms=total_time_ms,
            error_message=final_error,
            fallback_apis_tried=failed_apis,
        )

    async def _log_api_usage(
        self,
        api_name: str,
        request_id: str,
        capability: str,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
    ):
        """Log individual API usage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO api_usage_tracking 
                (api_name, usage_count, last_used, response_time_avg)
                VALUES (
                    ?, 
                    COALESCE((SELECT usage_count FROM api_usage_tracking WHERE api_name = ?), 0) + 1,
                    CURRENT_TIMESTAMP,
                    ?
                )
            """,
                (api_name, api_name, response_time_ms),
            )
            conn.commit()

    async def _log_orchestration_result(
        self,
        request_id: str,
        capability: str,
        successful_api_name: Optional[str],
        failed_api_names: List[str],
        total_attempts: int,
        total_time_ms: int,
        error_message: Optional[str],
    ):
        """Log orchestration result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_orchestration_log 
                (request_id, capability_requested, successful_api_id, failed_api_ids, 
                 total_attempts, total_response_time_ms, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    capability,
                    successful_api_name,
                    ",".join(failed_api_names) if failed_api_names else None,
                    total_attempts,
                    total_time_ms,
                    error_message,
                ),
            )
            conn.commit()

    async def _update_api_usage(
        self, api_name: str, response_time: float, success: bool
    ):
        """Update API usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Update usage tracking table
            conn.execute(
                """
                INSERT OR REPLACE INTO api_usage_tracking 
                (api_name, usage_count, last_used, response_time_avg)
                VALUES (
                    ?, 
                    COALESCE((SELECT usage_count FROM api_usage_tracking WHERE api_name = ?), 0) + 1,
                    CURRENT_TIMESTAMP,
                    ?
                )
            """,
                (api_name, api_name, response_time),
            )

            # Update current usage count in api_registry
            conn.execute(
                """
                UPDATE api_registry 
                SET current_usage_day = COALESCE(current_usage_day, 0) + 1,
                    total_requests = COALESCE(total_requests, 0) + 1,
                    total_errors = COALESCE(total_errors, 0) + ?,
                    average_response_time = CASE 
                        WHEN average_response_time IS NULL THEN ?
                        ELSE (COALESCE(average_response_time, 0) + ?) / 2
                    END,
                    success_rate = CASE 
                        WHEN total_requests > 0 THEN ((total_requests - total_errors) * 100.0) / total_requests
                        ELSE 100.0
                    END
                WHERE api_name = ?
            """,
                (0 if success else 1, response_time, response_time, api_name),
            )

            conn.commit()

    def update_api_usage(self, api_id: int):
        """Update daily usage count for an API"""
        with sqlite3.connect(self.db_path) as conn:
            today = datetime.now().strftime("%Y-%m-%d")

            # Get today's usage count
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM api_usage_tracking 
                WHERE api_id = ? AND date_only = ?
            """,
                (api_id, today),
            )

            daily_count = cursor.fetchone()[0]

            # Update the API registry
            conn.execute(
                """
                UPDATE api_registry 
                SET current_usage_day = ?, total_requests = total_requests + 1
                WHERE id = ?
            """,
                (daily_count, api_id),
            )

            conn.commit()

    async def _update_api_health_status(self, api_id: int, is_healthy: bool):
        """Update API health status based on recent performance"""
        with sqlite3.connect(self.db_path) as conn:
            health_status = (
                APIHealthStatus.HEALTHY.value
                if is_healthy
                else APIHealthStatus.DEGRADED.value
            )
            conn.execute(
                """
                UPDATE api_registry 
                SET health_status = ?, 
                    last_health_check = ?
                WHERE id = ?
            """,
                (health_status, datetime.now().isoformat(), api_id),
            )
            conn.commit()

    def get_apis_by_capability(self, capability: str) -> List[APIEndpoint]:
        """Get APIs filtered by capability, ordered by priority and usage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT api_name, base_url, api_version, status, capability, priority,
                       rate_limit_per_day, current_usage_day, health_status,
                       authentication_type, configuration,
                       total_requests, total_errors, average_response_time, success_rate,
                       last_health_check, created_at, updated_at
                FROM api_registry 
                WHERE capability = ? AND status = 'active'
                ORDER BY priority ASC, current_usage_day ASC
            """,
                (capability,),
            )

            apis = []
            for row in cursor.fetchall():
                config = json.loads(row[10]) if row[10] else {}
                # Create APIEndpoint with all required fields from database
                api = APIEndpoint(
                    id=0,  # Will be set properly when needed
                    api_name=row[0],
                    base_url=row[1],
                    api_version=row[2],
                    capability=row[4],
                    authentication_type=row[9],
                    rate_limit_per_minute=None,
                    rate_limit_per_hour=None,
                    rate_limit_per_day=row[6],
                    current_usage_minute=0,
                    current_usage_hour=0,
                    current_usage_day=row[7] or 0,
                    last_reset_minute=None,
                    last_reset_hour=None,
                    last_reset_day=None,
                    status=row[3],
                    health_check_url=None,
                    last_health_check=row[15],
                    health_status=row[8],
                    average_response_time=row[13] or 0.0,
                    success_rate=row[14] or 100.0,
                    total_requests=row[11] or 0,
                    total_errors=row[12] or 0,
                    allow_automatic_failover=True,
                    failover_priority=row[5],
                    priority=row[5],
                    configuration=row[10],
                    created_at=row[16],
                    updated_at=row[17],
                    created_by=None,
                )
                apis.append(api)

            return apis

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
                    ar.api_name,
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
                "capability_stats": capability_stats,
                "api_performance": api_performance,
                "analysis_period_days": days,
            }

    async def request_avatar_generation(
        self,
        text: str,
        voice_settings: Optional[Dict] = None,
        video_settings: Optional[Dict] = None,
    ) -> OrchestrationResult:
        """Convenience method for avatar generation requests with intelligent engine selection"""
        payload = {
            "text": text,
            "voice_settings": voice_settings
            or {"voice_type": "default", "speed": 1.0, "pitch": 1.0},
            "video_settings": video_settings
            or {"resolution": "1080p", "fps": 30, "duration": "auto"},
            "timestamp": datetime.now().isoformat(),
            "request_type": "avatar_generation",
        }

        request = OrchestrationRequest(
            request_id=f"avatar_{uuid.uuid4().hex[:8]}",
            capability="avatar-generation",
            payload=payload,
            timeout_seconds=120,  # Avatar generation can take longer
            max_retries=2,  # Try both engines if needed
        )

        logger.info(f"Initiating avatar generation request: {request.request_id}")
        return await self.orchestrate_request(request)


# Example usage
async def example_usage():
    """Example of how to use the Enhanced API Orchestrator"""
    orchestrator = EnhancedAPIOrchestrator()

    # Example avatar generation request
    result = await orchestrator.request_avatar_generation(
        text="Hello! Welcome to our AI-powered avatar system.",
        voice_settings={"voice_type": "professional", "speed": 1.1},
        video_settings={"resolution": "1080p", "fps": 30},
    )

    print(f"Avatar Generation - Status: {result.status}")
    if result.api_used:
        print(f"Engine Used: {result.api_used.api_name}")
    print(f"Response Time: {result.total_time_ms}ms")
    print(f"Attempts: {result.total_attempts}")

    if result.status == RequestStatus.SUCCESS:
        print(f"Video URL: {result.response_data.get('video_url')}")
        print(f"Engine Type: {result.response_data.get('engine_type')}")
        orchestration_info = result.response_data.get("_orchestration", {})
        if orchestration_info.get("failover_triggered"):
            print("⚠️  Failover was triggered during generation")
    else:
        print(f"Error: {result.error_message}")

    # Create a text generation request
    request = OrchestrationRequest(
        request_id=str(uuid.uuid4()),
        capability="text-generation",
        payload={
            "prompt": "Write a short story about AI",
            "max_tokens": 500,
            "temperature": 0.7,
        },
        timeout_seconds=30,
        max_retries=3,
        prefer_free=True,
    )

    # Execute the request
    result = await orchestrator.orchestrate_request(request)

    if result.status == RequestStatus.SUCCESS:
        print(
            f"Success! Used {result.api_used.api_name} in {result.total_attempts} attempts"
        )
        print(f"Response time: {result.total_time_ms}ms")
        print(f"Response: {result.response_data}")
    else:
        print(f"Failed after {result.total_attempts} attempts: {result.error_message}")
        print(f"Tried APIs: {result.fallback_apis_tried}")

    # Get analytics
    analytics = orchestrator.get_orchestration_analytics(days=7)
    print(f"Analytics: {analytics}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
