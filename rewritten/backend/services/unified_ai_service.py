#!/usr/bin/env python3
""""""
Unified AI Service Layer
Integrates ChatGPT, Gemini, and Abacus.AI with free APIs and cross-version compatibility
""""""

import os
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime
import hashlib
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIServiceType(Enum):
    """Enumeration of available AI services"""

    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    ABACUS = "abacus"
    HUGGINGFACE = "huggingface"
    OPENAI_FREE = "openai_free"
    GOOGLE_FREE = "google_free"


class RequestType(Enum):
    """Types of AI requests"""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CONTENT_CREATION = "content_creation"
    MULTIMODAL_ANALYSIS = "multimodal_analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"


@dataclass
class RateLimit:
    """Rate limiting configuration"""

    requests_per_minute: int
    requests_per_day: int
    requests_per_month: int = 0
    current_minute_count: int = 0
    current_day_count: int = 0
    current_month_count: int = 0
    last_reset_minute: datetime = field(default_factory=datetime.now):
    last_reset_day: datetime = field(default_factory=datetime.now)
    last_reset_month: datetime = field(default_factory=datetime.now)


@dataclass
class AIRequest:
    """AI service request structure"""

    request_type: RequestType
    data: Dict[str, Any]
    preferred_service: Optional[AIServiceType] = None
    priority: int = 1
    timeout: int = 30
    retry_count: int = 3
    cache_key: Optional[str] = None


@dataclass
class AIResponse:
    """AI service response structure"""

    success: bool
    data: Any
    service_used: AIServiceType
    response_time: float
    tokens_used: int = 0
    cost: float = 0.0
    error_message: Optional[str] = None
    cached: bool = False


class RateLimitManager:
    """Manages rate limits for all AI services"""

    def __init__(self):
        self.limits = {
            AIServiceType.OPENAI_FREE: RateLimit(
                requests_per_minute=3, requests_per_day=200, requests_per_month=1000
# BRACKET_SURGEON: disabled
#             ),
            AIServiceType.GOOGLE_FREE: RateLimit(
                requests_per_minute=15, requests_per_day=1500, requests_per_month=10000
# BRACKET_SURGEON: disabled
#             ),
            AIServiceType.HUGGINGFACE: RateLimit(
                requests_per_minute=30,
                requests_per_day=10000,
                requests_per_month=100000,
# BRACKET_SURGEON: disabled
#             ),
            AIServiceType.CHATGPT: RateLimit(
                requests_per_minute=60,
                requests_per_day=10000,
                requests_per_month=100000,
# BRACKET_SURGEON: disabled
#             ),
            AIServiceType.GEMINI: RateLimit(
                requests_per_minute=60,
                requests_per_day=10000,
                requests_per_month=100000,
# BRACKET_SURGEON: disabled
#             ),
            AIServiceType.ABACUS: RateLimit(
                requests_per_minute=100,
                requests_per_day=50000,
                requests_per_month=500000,
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }
        self.request_queues = {service: deque() for service in AIServiceType}

    async def check_rate_limit(self, service: AIServiceType) -> bool:
        """Check if request is within rate limits"""
        limit = self.limits.get(service)
        if not limit:
            return True

        now = datetime.now()

        # Reset counters if time periods have passed
        if (now - limit.last_reset_minute).total_seconds() >= 60:
            limit.current_minute_count = 0
            limit.last_reset_minute = now

        if (now - limit.last_reset_day).total_seconds() >= 86400:
            limit.current_day_count = 0
            limit.last_reset_day = now

        if (now - limit.last_reset_month).total_seconds() >= 2592000:  # 30 days
            limit.current_month_count = 0
            limit.last_reset_month = now

        # Check limits
        if limit.current_minute_count >= limit.requests_per_minute:
            return False
        if limit.current_day_count >= limit.requests_per_day:
            return False
        if limit.requests_per_month > 0 and limit.current_month_count >= limit.requests_per_month:
            return False

        return True

    async def increment_usage(self, service: AIServiceType):
        """Increment usage counters"""
        limit = self.limits.get(service)
        if limit:
            limit.current_minute_count += 1
            limit.current_day_count += 1
            limit.current_month_count += 1

    async def queue_request(self, service: AIServiceType, request: AIRequest) -> bool:
        """Queue request if rate limited"""
        if await self.check_rate_limit(service):
            return True

        self.request_queues[service].append(request)
        logger.info(f"Request queued for {service.value} due to rate limiting")
        return False


class CacheManager:
    """Manages caching for AI responses"""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _generate_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request"""
        if request.cache_key:
            return request.cache_key

        content = json.dumps(
            {"type": request.request_type.value, "data": request.data}, sort_keys=True
# BRACKET_SURGEON: disabled
#         )
        return hashlib.md5(content.encode()).hexdigest()

    async def get(self, request: AIRequest) -> Optional[AIResponse]:
        """Get cached response"""
        key = self._generate_cache_key(request)

        if key in self.cache:
            cached_time, response = self.cache[key]
            if time.time() - cached_time < self.ttl_seconds:
                self.access_times[key] = time.time()
                response.cached = True
                return response
            else:
                # Expired
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

        return None

    async def set(self, request: AIRequest, response: AIResponse):
        """Cache response"""
        if not response.success:
            return  # Don't cache failed responses

        key = self._generate_cache_key(request)
        current_time = time.time()

        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[lru_key]
            del self.access_times[lru_key]

        self.cache[key] = (current_time, response)
        self.access_times[key] = current_time


class ChatGPTIntegration:
    """ChatGPT API integration"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def generate_content(self, prompt: str, model: str = "gpt-3.5-turbo") -> AIResponse:
        """Generate content using ChatGPT"""
        start_time = time.time()

        try:
            session = await self._get_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
# BRACKET_SURGEON: disabled
#             }

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7,
# BRACKET_SURGEON: disabled
#             }

            async with session.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
# BRACKET_SURGEON: disabled
#             ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)

                    return AIResponse(
                        success=True,
                        data=content,
                        service_used=AIServiceType.CHATGPT,
                        response_time=time.time() - start_time,
                        tokens_used=tokens_used,
# BRACKET_SURGEON: disabled
#                     )
                else:
                    error_data = await response.text()
                    return AIResponse(
                        success=False,
                        data=None,
                        service_used=AIServiceType.CHATGPT,
                        response_time=time.time() - start_time,
                        error_message=f"HTTP {response.status}: {error_data}",
# BRACKET_SURGEON: disabled
#                     )

        except Exception as e:
            return AIResponse(
                success=False,
                data=None,
                service_used=AIServiceType.CHATGPT,
                response_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    async def code_review(self, code_snippet: str) -> AIResponse:
        """Review code using ChatGPT"""
        prompt = (
            f"Please review this code and provide suggestions for improvement:\n\n{code_snippet}"
# BRACKET_SURGEON: disabled
#         )
        return await self.generate_content(prompt)

    async def close(self):
        if self.session:
            await self.session.close()


class GeminiIntegration:
    """Google Gemini API integration"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def multimodal_analysis(self, content_type: str, data: Any) -> AIResponse:
        """Perform multimodal analysis using Gemini"""
        start_time = time.time()

        try:
            session = await self._get_session()

            payload = {"contents": [{"parts": [{"text": f"Analyze this {content_type}: {data}"}]}]}

            url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]

                    return AIResponse(
                        success=True,
                        data=content,
                        service_used=AIServiceType.GEMINI,
                        response_time=time.time() - start_time,
# BRACKET_SURGEON: disabled
#                     )
                else:
                    error_data = await response.text()
                    return AIResponse(
                        success=False,
                        data=None,
                        service_used=AIServiceType.GEMINI,
                        response_time=time.time() - start_time,
                        error_message=f"HTTP {response.status}: {error_data}",
# BRACKET_SURGEON: disabled
#                     )

        except Exception as e:
            return AIResponse(
                success=False,
                data=None,
                service_used=AIServiceType.GEMINI,
                response_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    async def advanced_reasoning(self, query: str) -> AIResponse:
        """Perform advanced reasoning using Gemini"""
        return await self.multimodal_analysis("reasoning task", query)

    async def close(self):
        if self.session:
            await self.session.close()


class AbacusAIIntegration:
    """Abacus.AI platform integration"""

    def __init__(self):
        self.api_key = os.getenv("ABACUS_AI_API_KEY")
        self.app_id = "1024a18ebe"
        self.base_url = "https://api.abacus.ai"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def enterprise_ai_service(self, service_type: str, data: Any) -> AIResponse:
        """Use enterprise AI service"""
        start_time = time.time()

        try:
            session = await self._get_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
# BRACKET_SURGEON: disabled
#             }

            payload = {
                "app_id": self.app_id,
                "service_type": service_type,
                "data": data,
# BRACKET_SURGEON: disabled
#             }

            async with session.post(
                f"{self.base_url}/v1/inference", headers=headers, json=payload
# BRACKET_SURGEON: disabled
#             ) as response:
                if response.status == 200:
                    result = await response.json()

                    return AIResponse(
                        success=True,
                        data=result,
                        service_used=AIServiceType.ABACUS,
                        response_time=time.time() - start_time,
# BRACKET_SURGEON: disabled
#                     )
                else:
                    error_data = await response.text()
                    return AIResponse(
                        success=False,
                        data=None,
                        service_used=AIServiceType.ABACUS,
                        response_time=time.time() - start_time,
                        error_message=f"HTTP {response.status}: {error_data}",
# BRACKET_SURGEON: disabled
#                     )

        except Exception as e:
            return AIResponse(
                success=False,
                data=None,
                service_used=AIServiceType.ABACUS,
                response_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    async def custom_model_inference(self, model_id: str, input_data: Any) -> AIResponse:
        """Run inference on custom model"""
        return await self.enterprise_ai_service(f"custom_model_{model_id}", input_data)

    async def close(self):
        if self.session:
            await self.session.close()


class HuggingFaceIntegration:
    """Hugging Face API integration"""

    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = "https://api-inference.huggingface.co/models"
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def inference(self, model_name: str, inputs: Any) -> AIResponse:
        """Run inference on Hugging Face model"""
        start_time = time.time()

        try:
            session = await self._get_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
# BRACKET_SURGEON: disabled
#             }

            async with session.post(
                f"{self.base_url}/{model_name}",
                headers=headers,
                json={"inputs": inputs},
# BRACKET_SURGEON: disabled
#             ) as response:
                if response.status == 200:
                    result = await response.json()

                    return AIResponse(
                        success=True,
                        data=result,
                        service_used=AIServiceType.HUGGINGFACE,
                        response_time=time.time() - start_time,
# BRACKET_SURGEON: disabled
#                     )
                else:
                    error_data = await response.text()
                    return AIResponse(
                        success=False,
                        data=None,
                        service_used=AIServiceType.HUGGINGFACE,
                        response_time=time.time() - start_time,
                        error_message=f"HTTP {response.status}: {error_data}",
# BRACKET_SURGEON: disabled
#                     )

        except Exception as e:
            return AIResponse(
                success=False,
                data=None,
                service_used=AIServiceType.HUGGINGFACE,
                response_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    async def close(self):
        if self.session:
            await self.session.close()


class AIServiceMonitor:
    """Monitor AI service performance and usage"""

    def __init__(self):
        self.metrics = {
            "response_times": defaultdict(list),
            "success_rates": defaultdict(list),
            "error_rates": defaultdict(list),
            "quota_usage": defaultdict(int),
            "total_requests": defaultdict(int),
            "total_tokens": defaultdict(int),
            "total_cost": defaultdict(float),
# BRACKET_SURGEON: disabled
#         }

    async def track_request(
        self, service: AIServiceType, request_type: RequestType, response: AIResponse
# BRACKET_SURGEON: disabled
#     ):
        """Track service performance metrics"""
        service_key = service.value

        self.metrics["response_times"][service_key].append(response.response_time)
        self.metrics["success_rates"][service_key].append(1 if response.success else 0)
        self.metrics["error_rates"][service_key].append(0 if response.success else 1)
        self.metrics["total_requests"][service_key] += 1
        self.metrics["total_tokens"][service_key] += response.tokens_used
        self.metrics["total_cost"][service_key] += response.cost

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {}

        for service in self.metrics["response_times"].keys():
            response_times = self.metrics["response_times"][service]
            success_rates = self.metrics["success_rates"][service]

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                success_rate = sum(success_rates) / len(success_rates) * 100

                report[service] = {
                    "avg_response_time": avg_response_time,
                    "success_rate": success_rate,
                    "total_requests": self.metrics["total_requests"][service],
                    "total_tokens": self.metrics["total_tokens"][service],
                    "total_cost": self.metrics["total_cost"][service],
# BRACKET_SURGEON: disabled
#                 }

        return report


class UnifiedAIService:
    """Unified interface for all AI services"""

    def __init__(self):
        self.chatgpt = ChatGPTIntegration()
        self.gemini = GeminiIntegration()
        self.abacus = AbacusAIIntegration()
        self.huggingface = HuggingFaceIntegration()
        self.rate_limiter = RateLimitManager()
        self.cache = CacheManager()
        self.monitor = AIServiceMonitor()

        # Service capability mapping
        self.service_capabilities = {
            RequestType.TEXT_GENERATION: [
                AIServiceType.CHATGPT,
                AIServiceType.GEMINI,
                AIServiceType.HUGGINGFACE,
# BRACKET_SURGEON: disabled
#             ],
            RequestType.CODE_GENERATION: [AIServiceType.CHATGPT, AIServiceType.GEMINI],
            RequestType.CODE_REVIEW: [AIServiceType.CHATGPT, AIServiceType.GEMINI],
            RequestType.CONTENT_CREATION: [AIServiceType.CHATGPT, AIServiceType.GEMINI],
            RequestType.MULTIMODAL_ANALYSIS: [AIServiceType.GEMINI],
            RequestType.TRANSLATION: [
                AIServiceType.CHATGPT,
                AIServiceType.GEMINI,
                AIServiceType.HUGGINGFACE,
# BRACKET_SURGEON: disabled
#             ],
            RequestType.SUMMARIZATION: [
                AIServiceType.CHATGPT,
                AIServiceType.GEMINI,
                AIServiceType.HUGGINGFACE,
# BRACKET_SURGEON: disabled
#             ],
            RequestType.QUESTION_ANSWERING: [
                AIServiceType.CHATGPT,
                AIServiceType.GEMINI,
                AIServiceType.ABACUS,
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         }

    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process AI request with intelligent service selection"""
        # Check cache first
        cached_response = await self.cache.get(request)
        if cached_response:
            logger.info(f"Cache hit for request type: {request.request_type.value}")
            return cached_response

        # Determine best service
        if request.preferred_service:
            services_to_try = [request.preferred_service]
        else:
            services_to_try = await self._get_best_available_services(request.request_type)

        # Try services in order of preference
        for service in services_to_try:
            # Check rate limits
            if not await self.rate_limiter.check_rate_limit(service):
                logger.warning(f"Rate limit exceeded for {service.value}, trying next service")
                continue

            # Process request
            response = await self._process_with_service(service, request)

            # Track metrics
            await self.monitor.track_request(service, request.request_type, response)

            if response.success:
                # Increment usage and cache response
                await self.rate_limiter.increment_usage(service)
                await self.cache.set(request, response)
                return response
            else:
                logger.warning(f"Request failed with {service.value}: {response.error_message}")

        # All services failed
        return AIResponse(
            success=False,
            data=None,
            service_used=(services_to_try[0] if services_to_try else AIServiceType.CHATGPT),
            response_time=0,
            error_message="All available services failed or rate limited",
# BRACKET_SURGEON: disabled
#         )

    async def _get_best_available_services(self, request_type: RequestType) -> List[AIServiceType]:
        """Get best available services for request type"""
        capable_services = self.service_capabilities.get(request_type, [])

        # Sort by preference (free services first, then paid)
        free_services = [s for s in capable_services if "free" in s.value.lower()]
        paid_services = [s for s in capable_services if "free" not in s.value.lower()]

        return free_services + paid_services

    async def _process_with_service(self, service: AIServiceType, request: AIRequest) -> AIResponse:
        """Process request with specific service"""
        try:
            if service == AIServiceType.CHATGPT:
                if request.request_type == RequestType.TEXT_GENERATION:
                    return await self.chatgpt.generate_content(request.data.get("prompt", ""))
                elif request.request_type == RequestType.CODE_REVIEW:
                    return await self.chatgpt.code_review(request.data.get("code", ""))
                else:
                    return await self.chatgpt.generate_content(request.data.get("prompt", ""))

            elif service == AIServiceType.GEMINI:
                if request.request_type == RequestType.MULTIMODAL_ANALYSIS:
                    return await self.gemini.multimodal_analysis(
                        request.data.get("content_type", "text"),
                        request.data.get("data", ""),
# BRACKET_SURGEON: disabled
#                     )
                else:
                    return await self.gemini.advanced_reasoning(request.data.get("query", ""))

            elif service == AIServiceType.ABACUS:
                return await self.abacus.enterprise_ai_service(
                    request.request_type.value, request.data
# BRACKET_SURGEON: disabled
#                 )

            elif service == AIServiceType.HUGGINGFACE:
                model_name = request.data.get("model", "gpt2")
                inputs = request.data.get("inputs", "")
                return await self.huggingface.inference(model_name, inputs)

            else:
                return AIResponse(
                    success=False,
                    data=None,
                    service_used=service,
                    response_time=0,
                    error_message=f"Service {service.value} not implemented",
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            return AIResponse(
                success=False,
                data=None,
                service_used=service,
                response_time=0,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all services"""
        return await self.monitor.generate_performance_report()

    async def close(self):
        """Close all service connections"""
        await self.chatgpt.close()
        await self.gemini.close()
        await self.abacus.close()
        await self.huggingface.close()


# Convenience functions for common use cases
async def generate_text(prompt: str, preferred_service: Optional[AIServiceType] = None) -> str:
    """Generate text using the best available service"""
    service = UnifiedAIService()
    try:
        request = AIRequest(
            request_type=RequestType.TEXT_GENERATION,
            data={"prompt": prompt},
            preferred_service=preferred_service,
# BRACKET_SURGEON: disabled
#         )
        response = await service.process_request(request)
        return response.data if response.success else f"Error: {response.error_message}"
    finally:
        await service.close()


async def review_code(code: str, preferred_service: Optional[AIServiceType] = None) -> str:
    """Review code using the best available service"""
    service = UnifiedAIService()
    try:
        request = AIRequest(
            request_type=RequestType.CODE_REVIEW,
            data={"code": code},
            preferred_service=preferred_service,
# BRACKET_SURGEON: disabled
#         )
        response = await service.process_request(request)
        return response.data if response.success else f"Error: {response.error_message}"
    finally:
        await service.close()


async def analyze_multimodal(
    content_type: str, data: Any, preferred_service: Optional[AIServiceType] = None
# BRACKET_SURGEON: disabled
# ) -> str:
    """Analyze multimodal content using the best available service"""
    service = UnifiedAIService()
    try:
        request = AIRequest(
            request_type=RequestType.MULTIMODAL_ANALYSIS,
            data={"content_type": content_type, "data": data},
            preferred_service=preferred_service or AIServiceType.GEMINI,
# BRACKET_SURGEON: disabled
#         )
        response = await service.process_request(request)
        return response.data if response.success else f"Error: {response.error_message}"
    finally:
        await service.close()


if __name__ == "__main__":
    # Example usage
    async def main():
        service = UnifiedAIService()

        try:
            # Test text generation
            request = AIRequest(
                request_type=RequestType.TEXT_GENERATION,
                data={"prompt": "Write a short story about AI"},
# BRACKET_SURGEON: disabled
#             )
            response = await service.process_request(request)
            print(f"Response: {response.data}")
            print(f"Service used: {response.service_used.value}")
            print(f"Response time: {response.response_time:.2f}s")

            # Get performance metrics
            metrics = await service.get_performance_metrics()
            print(f"Performance metrics: {metrics}")

        finally:
            await service.close()

    asyncio.run(main())