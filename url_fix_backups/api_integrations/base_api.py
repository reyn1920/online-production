import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors"""

    pass


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded"""


    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after

@dataclass


class RateLimitConfig:
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


class RateLimiter:
    """Token bucket rate limiter for API calls"""


    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_limit
        self.last_refill = time.time()
        self.hourly_count = 0
        self.daily_count = 0
        self.hour_start = datetime.now().replace(minute = 0,
    second = 0,
    microsecond = 0)
        self.day_start = datetime.now().replace(
            hour = 0, minute = 0, second = 0, microsecond = 0
        )


    async def acquire(self) -> bool:
        """Acquire a token for API call"""
        now = time.time()
        current_time = datetime.now()

        # Reset hourly counter
        if current_time >= self.hour_start + timedelta(hours = 1):
            self.hourly_count = 0
            self.hour_start = current_time.replace(minute = 0,
    second = 0,
    microsecond = 0)

        # Reset daily counter
        if current_time >= self.day_start + timedelta(days = 1):
            self.daily_count = 0
            self.day_start = current_time.replace(
                hour = 0, minute = 0, second = 0, microsecond = 0
            )

        # Check daily and hourly limits
        if self.daily_count >= self.config.requests_per_day:
            raise RateLimitError("Daily rate limit exceeded", retry_after = 86400)

        if self.hourly_count >= self.config.requests_per_hour:
            raise RateLimitError("Hourly rate limit exceeded", retry_after = 3600)

        # Refill tokens based on time passed
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * (self.config.requests_per_minute / 60.0)
        self.tokens = min(self.config.burst_limit, self.tokens + tokens_to_add)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            self.hourly_count += 1
            self.daily_count += 1
            return True

        # Calculate wait time
        wait_time = (1 - self.tokens) * (60.0 / self.config.requests_per_minute)
        raise RateLimitError(
            f"Rate limit exceeded, wait {wait_time:.2f} seconds",
                retry_after = int(wait_time))


class BaseAPI(ABC):
    """Base class for all API integrations"""


    def __init__(self, rate_limit_config: Optional[RateLimitConfig] = None):
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_headers = {
            "User - Agent": "NicheDiscoveryEngine / 1.0 (Educational Research)"
        }


    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers = self.base_headers)
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


    async def _make_request(
        self,
            method: str,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            max_retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retry logic"""

        if not self.session:
            raise APIError("Session not initialized. Use async context manager.")

        # Apply rate limiting
        await self.rate_limiter.acquire()

        request_headers = self.base_headers.copy()
        if headers:
            request_headers.update(headers)

        for attempt in range(max_retries + 1):
            try:
                async with self.session.request(
                    method = method,
                        url = url,
                        params = params,
                        json = data,
                        headers = request_headers) as response:

                    # Handle rate limiting from server
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry - After", 60))
                        if attempt < max_retries:
                            logger.warning(
                                f"Rate limited by server, waiting {retry_after}s"
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise RateLimitError(
                                "Server rate limit exceeded", retry_after
                            )

                    # Handle other HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise APIError(f"HTTP {response.status}: {error_text}")

                    return await response.json()

            except aiohttp.ClientError as e:
                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise APIError(f"Request failed after {max_retries} retries: {e}")

        raise APIError("Unexpected error in request handling")

    @abstractmethod


    async def health_check(self) -> bool:
        """Check if the API is accessible"""
        pass

    @abstractmethod


    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota / rate limit status"""
        pass


class APIManager:
    """Manager for coordinating multiple API integrations"""


    def __init__(self):
        self.apis: Dict[str, BaseAPI] = {}
        self.health_status: Dict[str, bool] = {}


    def register_api(self, name: str, api: BaseAPI):
        """Register an API integration"""
        self.apis[name] = api
        self.health_status[name] = False


    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered APIs"""
        results = {}

        for name, api in self.apis.items():
            try:
                async with api:
                    results[name] = await api.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False

        self.health_status = results
        return results


    async def get_all_quota_status(self) -> Dict[str, Dict[str, Any]]:
        """Get quota status for all APIs"""
        results = {}

        for name, api in self.apis.items():
            try:
                async with api:
                    results[name] = await api.get_quota_status()
            except Exception as e:
                logger.error(f"Quota check failed for {name}: {e}")
                results[name] = {"error": str(e)}

        return results


    def get_healthy_apis(self) -> List[str]:
        """Get list of currently healthy APIs"""
        return [name for name, status in self.health_status.items() if status]


    def get_api(self, name: str) -> Optional[BaseAPI]:
        """Get API instance by name"""
        return self.apis.get(name)