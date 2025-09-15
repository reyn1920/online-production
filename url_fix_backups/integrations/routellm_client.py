#!/usr / bin / env python3
""""""
RouteLL API Client for Trae AI Integration
Provides comprehensive API wrapper with credit monitoring and optimization
""""""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Iterator, List, Optional, Union

import requests


class RouteLL_Status(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    CREDITS_LOW = "credits_low"
    CREDITS_EXHAUSTED = "credits_exhausted"
    API_ERROR = "api_error"
    OFFLINE = "offline"


@dataclass
class CreditUsage:
    """Credit usage tracking data structure"""

    total_credits: int
    used_credits: int
    remaining_credits: int
    daily_usage: int
    hourly_usage: int
    last_updated: datetime
    warning_level: str = "normal"  # normal, warning, critical


@dataclass
class APIResponse:
    """Standardized API response structure"""

    success: bool
    data: Optional[Dict]
    error: Optional[str]
    credits_used: int
    response_time_ms: int
    model_used: str
    timestamp: datetime
    provider: str = "routellm"
    fallback_used: bool = False


class RouteLL_Client:
    """RouteLL API Client with advanced monitoring and optimization"""

    def __init__(self, config_path: str = None):
        """Initialize RouteLL client with configuration"""
        self.config = self._load_config(config_path)
        self.api_key = os.getenv(self.config["api_settings"]["api_key_env"])
        self.base_url = self.config["api_settings"]["base_url"]
        self.session = requests.Session()
        self.credit_usage = CreditUsage(
            total_credits=self.config["credit_system"]["monthly_credits"],
            used_credits=0,
            remaining_credits=self.config["credit_system"]["monthly_credits"],
            daily_usage=0,
            hourly_usage=0,
            last_updated=datetime.now(),
# BRACKET_SURGEON: disabled
#         )
        self.status = RouteLL_Status.ACTIVE
        self.logger = self._setup_logging()
        self._setup_session()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        if config_path is None:
            config_path = (
                "/Users / thomasbrianreynolds / online production / config / routellm_config.json"
# BRACKET_SURGEON: disabled
#             )

        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON in configuration file: {config_path}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("routellm_client")
        logger.setLevel(getattr(logging, self.config["logging"]["level"]))

        # Create file handler
        log_file = self.config["logging"]["log_file"]
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _setup_session(self):
        """Configure requests session with headers and timeouts"""
        if not self.api_key:
            raise ValueError(
                f"API key not found in environment variable: {self.config['api_settings']['api_key_env']}"
# BRACKET_SURGEON: disabled
#             )

        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content - Type": "application / json",
                "User - Agent": "Trae - AI - RouteLL - Client / 1.0.0",
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

        self.session.timeout = self.config["api_settings"]["timeout_seconds"]

    def check_credits(self) -> CreditUsage:
        """Check current credit usage and update internal tracking"""
        try:
            # In a real implementation, this would call the billing API
            # For now, we'll simulate credit tracking
            self.credit_usage.last_updated = datetime.now()

            # Calculate warning level
            usage_percentage = (
                self.credit_usage.used_credits / self.credit_usage.total_credits
# BRACKET_SURGEON: disabled
#             ) * 100

            if usage_percentage >= 95:
                self.credit_usage.warning_level = "critical"
                self.status = RouteLL_Status.CREDITS_EXHAUSTED
            elif usage_percentage >= 90:
                self.credit_usage.warning_level = "warning"
                self.status = RouteLL_Status.CREDITS_LOW
            else:
                self.credit_usage.warning_level = "normal"
                if self.status in [
                    RouteLL_Status.CREDITS_LOW,
                    RouteLL_Status.CREDITS_EXHAUSTED,
# BRACKET_SURGEON: disabled
#                 ]:
                    self.status = RouteLL_Status.ACTIVE

            self.logger.info(
                f"Credit check: {self.credit_usage.remaining_credits} remaining ({usage_percentage:.1f}% used)"
# BRACKET_SURGEON: disabled
#             )
            return self.credit_usage

        except Exception as e:
            self.logger.error(f"Failed to check credits: {str(e)}")
            return self.credit_usage

    def _estimate_credit_cost(self, messages: List[Dict], model: str = None) -> int:
        """Estimate credit cost for a request"""
        model = model or self.config["api_settings"]["default_model"]

        # Check if model is unlimited
        unlimited_models = self.config["credit_system"]["unlimited_models"]
        if any(unlimited_model.lower() in model.lower() for unlimited_model in unlimited_models):
            return 0

        # Estimate based on token count (rough approximation)
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough token estimation

        # High - cost models use more credits
        high_cost_models = self.config["credit_system"]["high_cost_models"]
        if any(high_cost_model.lower() in model.lower() for high_cost_model in high_cost_models):
            return max(10, estimated_tokens // 100)  # Higher cost for premium models

        return max(1, estimated_tokens // 200)  # Standard cost estimation

    def _can_make_request(self, estimated_cost: int) -> bool:
        """Check if we can make a request based on credits and rate limits"""
        if self.status == RouteLL_Status.CREDITS_EXHAUSTED:
            return False

        if self.credit_usage.remaining_credits < estimated_cost:
            self.status = RouteLL_Status.CREDITS_EXHAUSTED
            return False

        # Check daily and hourly limits
        daily_limit = self.config["monitoring"]["credit_tracking"]["daily_usage_limit"]
        hourly_limit = self.config["monitoring"]["credit_tracking"]["hourly_usage_limit"]

        if self.credit_usage.daily_usage + estimated_cost > daily_limit:
            self.logger.warning(
                f"Daily usage limit would be exceeded: {self.credit_usage.daily_usage + estimated_cost} > {daily_limit}"
# BRACKET_SURGEON: disabled
#             )
            return False

        if self.credit_usage.hourly_usage + estimated_cost > hourly_limit:
            self.logger.warning(
                f"Hourly usage limit would be exceeded: {self.credit_usage.hourly_usage + estimated_cost} > {hourly_limit}"
# BRACKET_SURGEON: disabled
#             )
            return False

        return True

    def _update_credit_usage(self, credits_used: int):
        """Update internal credit usage tracking"""
        self.credit_usage.used_credits += credits_used
        self.credit_usage.remaining_credits -= credits_used
        self.credit_usage.daily_usage += credits_used
        self.credit_usage.hourly_usage += credits_used
        self.credit_usage.last_updated = datetime.now()

    def chat_completion(
        self, messages: List[Dict], model: str = None, stream: bool = False, **kwargs
    ) -> Union[APIResponse, Iterator[APIResponse]]:
        """Create a chat completion with comprehensive monitoring"""

        model = model or self.config["api_settings"]["default_model"]
        estimated_cost = self._estimate_credit_cost(messages, model)

        # Check if we can make the request
        if not self._can_make_request(estimated_cost):
            error_msg = f"Cannot make request: {self.status.value}"
            self.logger.error(error_msg)
            return APIResponse(
                success=False,
                data=None,
                error=error_msg,
                credits_used=0,
                response_time_ms=0,
                model_used=model,
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )

        # Prepare request payload
        payload = {"model": model, "messages": messages, "stream": stream, **kwargs}

        # Apply default parameters
        default_params = self.config["model_configuration"][model]["default_parameters"]
        for key, value in default_params.items():
            if key not in payload:
                payload[key] = value

        start_time = time.time()

        try:
            url = f"{self.base_url}{self.config['api_settings']['chat_completions_endpoint']}"

            if stream:
                return self._handle_streaming_response(url, payload, estimated_cost, start_time)
            else:
                return self._handle_regular_response(url, payload, estimated_cost, start_time)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                credits_used=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                model_used=model,
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )

    def _handle_regular_response(
        self, url: str, payload: Dict, estimated_cost: int, start_time: float
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Handle non - streaming API response"""
        response = self.session.post(url, json=payload)
        response_time_ms = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            self._update_credit_usage(estimated_cost)
            self.logger.info(
                f"Successful request: {estimated_cost} credits used, {response_time_ms}ms"
# BRACKET_SURGEON: disabled
#             )

            return APIResponse(
                success=True,
                data=response.json(),
                error=None,
                credits_used=estimated_cost,
                response_time_ms=response_time_ms,
                model_used=payload["model"],
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )
        else:
            error_msg = f"API error {response.status_code}: {response.text}"
            self.logger.error(error_msg)

            return APIResponse(
                success=False,
                data=None,
                error=error_msg,
                credits_used=0,
                response_time_ms=response_time_ms,
                model_used=payload["model"],
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )

    def _handle_streaming_response(
        self, url: str, payload: Dict, estimated_cost: int, start_time: float
    ) -> Iterator[APIResponse]:
        """Handle streaming API response"""
        try:
            response = self.session.post(url, json=payload, stream=True)

            if response.status_code != 200:
                error_msg = f"API error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                yield APIResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    credits_used=0,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    model_used=payload["model"],
                    timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#                 )
                return

            # Update credits once for streaming request
            self._update_credit_usage(estimated_cost)
            credits_reported = False

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf - 8")
                    if line.startswith("data: "):
                        line = line[6:]
                        if line == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(line)
                            yield APIResponse(
                                success=True,
                                data=chunk_data,
                                error=None,
                                credits_used=(estimated_cost if not credits_reported else 0),
                                response_time_ms=int((time.time() - start_time) * 1000),
                                model_used=payload["model"],
                                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#                             )
                            credits_reported = True
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.logger.error(f"Streaming request failed: {str(e)}")
            yield APIResponse(
                success=False,
                data=None,
                error=str(e),
                credits_used=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                model_used=payload["model"],
                timestamp=datetime.now(),
# BRACKET_SURGEON: disabled
#             )

    def get_status(self) -> Dict:
        """Get current client status and metrics"""
        return {
            "status": self.status.value,
            "credit_usage": {
                "total_credits": self.credit_usage.total_credits,
                "used_credits": self.credit_usage.used_credits,
                "remaining_credits": self.credit_usage.remaining_credits,
                "daily_usage": self.credit_usage.daily_usage,
                "hourly_usage": self.credit_usage.hourly_usage,
                "warning_level": self.credit_usage.warning_level,
                "last_updated": self.credit_usage.last_updated.isoformat(),
# BRACKET_SURGEON: disabled
#             },
            "api_health": self._check_api_health(),
            "configuration": {
                "model": self.config["api_settings"]["default_model"],
                "base_url": self.base_url,
                "monitoring_enabled": self.config["monitoring"]["enabled"],
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

    def _check_api_health(self) -> Dict:
        """Check API health status"""
        try:
            # Simple health check - attempt a minimal request
            test_messages = [{"role": "user", "content": "test"}]
            estimated_cost = self._estimate_credit_cost(test_messages)

            if not self._can_make_request(estimated_cost):
                return {"status": "unavailable", "reason": "insufficient_credits"}

            # In a real implementation, you might have a dedicated health endpoint
            return {"status": "healthy", "last_check": datetime.now().isoformat()}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def optimize_for_credits(self) -> Dict:
        """Get optimization recommendations for credit usage"""
        recommendations = []

        if self.credit_usage.warning_level in ["warning", "critical"]:
            recommendations.append("Consider using unlimited models when possible")
            recommendations.append("Reduce max_tokens parameter for shorter responses")
            recommendations.append("Enable response caching to avoid duplicate requests")

        unlimited_models = self.config["credit_system"]["unlimited_models"]
        recommendations.append(f"Available unlimited models: {', '.join(unlimited_models)}")

        return {
            "current_usage_percentage": (
                self.credit_usage.used_credits / self.credit_usage.total_credits
# BRACKET_SURGEON: disabled
#             )
            * 100,
            "recommendations": recommendations,
            "unlimited_models": unlimited_models,
            "estimated_days_remaining": self._estimate_days_remaining(),
# BRACKET_SURGEON: disabled
#         }

    def _estimate_days_remaining(self) -> float:
        """Estimate days remaining based on current usage pattern"""
        if self.credit_usage.daily_usage == 0:
            return float("inf")

        return self.credit_usage.remaining_credits / self.credit_usage.daily_usage


# Example usage and testing
if __name__ == "__main__":
    # Initialize client
    client = RouteLL_Client()

    # Check status
    status = client.get_status()
    print(f"Client Status: {json.dumps(status, indent = 2)}")

    # Test chat completion
    messages = [{"role": "user", "content": "What is the meaning of life?"}]

    response = client.chat_completion(messages)
    print(f"Response: {response}")

    # Get optimization recommendations
    optimization = client.optimize_for_credits()
    print(f"Optimization: {json.dumps(optimization, indent = 2)}")