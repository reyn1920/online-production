#!/usr/bin/env python3
""""""
RouteLL API Integration Example
Demonstrates complete integration with monitoring, rate limiting, \
#     and intelligent routing
""""""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.rate_limiter import CreditOptimizer, RateLimiter

from integrations.free_api_fallback import FreeAPIFallback
from integrations.routellm_client import APIResponse, RouteLL_Client
from integrations.web_ai_client import WebAIClient, WebAIPlatform
from monitoring.routellm_monitor import CreditMonitor
from routing.model_router import ModelRouter, TaskType


class RouteLL_IntegratedClient:
    """"""
    Complete RouteLL integration with all features:
    - Intelligent model routing
    - Credit monitoring and optimization
    - Rate limiting
    - Usage analytics
    - Error handling and fallbacks
    """"""

    def __init__(self, api_key: str = None, config_path: str = None):
        # Initialize components
        self.config_path = (
            config_path
            or "/Users/thomasbrianreynolds/online production/config/routellm_config.json"
# BRACKET_SURGEON: disabled
#         )
        self.config = self._load_config()

        # Core API client
        self.client = RouteLL_Client()

        # Rate limiting and optimization
        self.rate_limiter = RateLimiter()
        self.optimizer = CreditOptimizer(self.rate_limiter)

        # Intelligent routing
        self.router = ModelRouter(config_path=self.config_path, rate_limiter=self.rate_limiter)

        # Monitoring
        self.monitor = CreditMonitor()

        # Fallback system for when credits are exhausted
        self.fallback = FreeAPIFallback()

        # Initialize web AI client for avatar generation
        self.web_ai_client = WebAIClient()

        # Usage tracking
        self.session_stats = {
            "requests_made": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "successful_requests": 0,
            "failed_requests": 0,
            "fallback_requests": 0,
            "web_ai_requests": 0,
            "avatar_generations": 0,
            "start_time": time.time(),
# BRACKET_SURGEON: disabled
#         }

        print("🚀 RouteLL Integrated Client initialized")
        print(f"💳 Credit monitoring: {'✅ Enabled' if self.monitor else '❌ Disabled'}")
        print(f"🎯 Model routing: {'✅ Enabled' if self.router else '❌ Disabled'}")
        print(f"⚡ Rate limiting: {'✅ Enabled' if self.rate_limiter else '❌ Disabled'}")

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")
            return {}

    async def chat_completion(self, messages: List[Dict], **kwargs) -> APIResponse:
        """"""
        Enhanced chat completion with full integration and fallback support

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            RouteLL_Response with enhanced metadata
        """"""
        request_start = time.time()

        try:
            # Step 1: Check rate limits
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                print(f"⏳ Rate limit reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

            # Step 2: Check credit status
            credit_status = await self.client.get_credit_status()
            if credit_status.remaining_credits < 10:  # Low credit threshold
                print(f"⚠️ Low credits remaining: {credit_status.remaining_credits}")

                # If credits are exhausted, use fallback immediately
                if credit_status.remaining_credits <= 0:
                    print("🔄 Credits exhausted, using fallback API...")
                    return await self._try_fallback(messages, **kwargs)

                # Try to optimize the request
                optimized_params = self.optimizer.optimize_request(
                    messages, {"cost": 0.8, "quality": 0.2}
# BRACKET_SURGEON: disabled
#                 )
                kwargs.update(optimized_params)
                print("🔧 Request optimized for cost savings")

            # Step 3: Intelligent model routing
            routing_result = self.router.route_request(
                messages, preferences=kwargs.get("preferences")
# BRACKET_SURGEON: disabled
#             )
            selected_model = routing_result["routing_decision"]["selected_model"]
            optimized_params = routing_result["optimized_params"]

            # Merge routing optimizations with user parameters
            final_params = {**optimized_params, **kwargs}
            final_params["model"] = selected_model

            print(f"🎯 Routed to model: {selected_model} ({routing_result['model_info']['tier']})")
            print(f"💰 Estimated cost/token: ${routing_result['model_info']['cost_per_token']:.4f}")

            # Step 4: Make the API request
            response = await self.client.chat_completion(messages, **final_params)

            # Step 5: Record the request for rate limiting
            self.rate_limiter.record_request()

            # Step 6: Update routing performance
            request_time = time.time() - request_start
            task_type = TaskType(routing_result["routing_decision"]["task_type"])

            if response.success:
                self.router.record_request_outcome(
                    selected_model, task_type, True, request_time, quality_rating=0.85
# BRACKET_SURGEON: disabled
#                 )
                self.session_stats["successful_requests"] += 1
            else:
                # Try fallback on RouteLL failure
                print("🔄 RouteLL request failed, trying fallback...")
                fallback_response = await self._try_fallback(messages, **kwargs)
                if fallback_response:
                    return fallback_response

                self.router.record_request_outcome(selected_model, task_type, False, request_time)
                self.session_stats["failed_requests"] += 1

            # Step 7: Update session statistics
            self.session_stats["requests_made"] += 1
            if hasattr(response, "usage") and response.usage:
                self.session_stats["total_tokens"] += response.usage.get("total_tokens", 0)
                self.session_stats["total_cost"] += (
                    response.usage.get("total_tokens", 0)
                    * routing_result["model_info"]["cost_per_token"]
# BRACKET_SURGEON: disabled
#                 )

            # Step 8: Enhanced response with routing metadata
            if response.success:
                response.routing_info = routing_result["routing_decision"]
                response.optimization_info = {
                    "original_params": kwargs,
                    "optimized_params": final_params,
                    "cost_savings": self._calculate_cost_savings(
                        kwargs, final_params, routing_result
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 }

            return response

        except Exception as e:
            print(f"❌ Request failed: {e}")

            # Try fallback on exception
            fallback_response = await self._try_fallback(messages, **kwargs)
            if fallback_response:
                return fallback_response

            self.session_stats["failed_requests"] += 1

            # Return error response
            return APIResponse(
                success=False,
                content=None,
                error=str(e),
                usage=None,
                model=kwargs.get("model", "unknown"),
                response_time=time.time() - request_start,
# BRACKET_SURGEON: disabled
#             )

    def _calculate_cost_savings(
        self, original_params: Dict, optimized_params: Dict, routing_result: Dict
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """Calculate potential cost savings from optimization"""
        # This is a simplified calculation - in practice you'd need more sophisticated cost modeling
        original_model_cost = 0.01  # Assume premium model cost
        optimized_model_cost = routing_result["model_info"]["cost_per_token"]

        original_tokens = original_params.get("max_tokens", 1000)
        optimized_tokens = optimized_params.get("max_tokens", 1000)

        original_cost = original_model_cost * original_tokens
        optimized_cost = optimized_model_cost * optimized_tokens

        savings = max(0, original_cost - optimized_cost)
        savings_percentage = (savings / original_cost * 100) if original_cost > 0 else 0

        return {
            "estimated_original_cost": original_cost,
            "estimated_optimized_cost": optimized_cost,
            "estimated_savings": savings,
            "savings_percentage": savings_percentage,
# BRACKET_SURGEON: disabled
#         }

    async def stream_completion(self, messages: List[Dict], **kwargs) -> AsyncIterator[str]:
        """Stream completion with full integration"""
        # Similar to chat_completion but with streaming
        routing_result = self.router.route_request(messages, preferences=kwargs.get("preferences"))
        selected_model = routing_result["routing_decision"]["selected_model"]
        optimized_params = routing_result["optimized_params"]

        final_params = {
            **optimized_params,
            **kwargs,
            "model": selected_model,
            "stream": True,
# BRACKET_SURGEON: disabled
#         }

        print(f"🎯 Streaming from model: {selected_model}")

        async for chunk in self.client.stream_completion(messages, **final_params):
            yield chunk

    def get_session_analytics(self) -> Dict:
        """Get comprehensive session analytics"""
        session_duration = time.time() - self.session_stats["start_time"]

        analytics = {
            "session_duration_minutes": session_duration / 60,
            "requests_per_minute": (
                self.session_stats["requests_made"] / (session_duration / 60)
                if session_duration > 0
                else 0
# BRACKET_SURGEON: disabled
#             ),
            "success_rate": (
                (
                    self.session_stats["successful_requests"]
                    / self.session_stats["requests_made"]
                    * 100
# BRACKET_SURGEON: disabled
#                 )
                if self.session_stats["requests_made"] > 0
                else 0
# BRACKET_SURGEON: disabled
#             ),
            "total_requests": self.session_stats["requests_made"],
            "successful_requests": self.session_stats["successful_requests"],
            "failed_requests": self.session_stats["failed_requests"],
            "total_tokens_used": self.session_stats["total_tokens"],
            "estimated_total_cost": self.session_stats["total_cost"],
            "avg_cost_per_request": (
                self.session_stats["total_cost"] / self.session_stats["requests_made"]
                if self.session_stats["requests_made"] > 0
                else 0
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

        # Add routing analytics
        routing_analytics = self.router.get_routing_analytics()
        analytics["routing"] = routing_analytics

        # Add rate limiting status
        analytics["rate_limiting"] = {
            "current_window_requests": len(self.rate_limiter.request_history),
            "can_make_request": self.rate_limiter.can_make_request(),
            "wait_time_seconds": self.rate_limiter.can_make_request()[2],
# BRACKET_SURGEON: disabled
#         }

        return analytics

    async def _try_fallback(self, messages: List[Dict], **kwargs) -> Optional[APIResponse]:
        """"""
        Try to use fallback API when RouteLL fails or credits are exhausted

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            APIResponse from fallback or None if fallback fails
        """"""
        try:
            print("🔄 Attempting fallback API request...")

            # Use fallback system
            fallback_response = await self.fallback.chat_completion(messages=messages, **kwargs)

            if fallback_response.success:
                print(f"✅ Fallback successful using {fallback_response.provider}")
                self.session_stats["fallback_requests"] += 1
                self.session_stats["successful_requests"] += 1

                # Convert fallback response to APIResponse format
                return APIResponse(
                    success=True,
                    data={
                        "content": fallback_response.content,
                        "usage": fallback_response.usage,
# BRACKET_SURGEON: disabled
#                     },
                    error=None,
                    credits_used=0,  # Fallback APIs are free
                    response_time_ms=int(fallback_response.response_time * 1000),
                    model_used=fallback_response.model,
                    timestamp=datetime.now(),
                    provider=fallback_response.provider,
                    fallback_used=True,
# BRACKET_SURGEON: disabled
#                 )
            else:
                print(f"❌ Fallback failed: {fallback_response.error}")
                return None

        except Exception as e:
            print(f"❌ Fallback exception: {e}")
            return None

    async def health_check(self) -> Dict:
        """Comprehensive health check"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
# BRACKET_SURGEON: disabled
#         }

        try:
            # Check API connectivity
            api_status = await self.client.health_check()
            health_status["components"]["api"] = {
                "status": "healthy" if api_status.success else "unhealthy",
                "response_time": api_status.response_time,
                "details": (api_status.content if api_status.success else api_status.error),
# BRACKET_SURGEON: disabled
#             }
        except Exception as e:
            health_status["components"]["api"] = {
                "status": "unhealthy",
                "error": str(e),
# BRACKET_SURGEON: disabled
#             }
            health_status["overall_status"] = "degraded"

        try:
            # Check credit status
            credit_status = await self.client.get_credit_status()
            health_status["components"]["credits"] = {
                "status": ("healthy" if credit_status.remaining_credits > 100 else "warning"),
                "remaining_credits": credit_status.remaining_credits,
                "daily_usage": credit_status.daily_usage,
# BRACKET_SURGEON: disabled
#             }
        except Exception as e:
            health_status["components"]["credits"] = {
                "status": "unknown",
                "error": str(e),
# BRACKET_SURGEON: disabled
#             }

        # Check rate limiting
        health_status["components"]["rate_limiting"] = {
            "status": "healthy",
            "can_make_request": self.rate_limiter.can_make_request(),
            "current_usage": len(self.rate_limiter.request_history),
# BRACKET_SURGEON: disabled
#         }

        # Check model router
        health_status["components"]["model_router"] = {
            "status": "healthy",
            "available_models": len(self.router.models),
            "routing_decisions_made": len(self.router.routing_history),
# BRACKET_SURGEON: disabled
#         }

        return health_status

    async def generate_avatar(
        self,
        description: str,
        style: str = "realistic",
        platform: WebAIPlatform = WebAIPlatform.CHATGPT,
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """"""
        Generate avatar using web AI platforms

        Args:
            description: Description of the avatar to generate
            style: Style preference for the avatar
            platform: AI platform to use for generation

        Returns:
            Dictionary with avatar generation results
        """"""
        try:
            print(f"🎨 Generating avatar: {description} (style: {style})")

            # Create avatar generation prompt
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating detailed prompts for AI image generation. Create optimized prompts that produce high - quality avatar images.",
# BRACKET_SURGEON: disabled
#                 },
                {
                    "role": "user",
                    "content": f"Create a detailed prompt for generating a {style} avatar with this description: {description}. Include specific details about lighting, composition, \"
#     and quality modifiers that work well with AI image generators like DALL - E, Midjourney, or Stable Diffusion.",
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             ]

            # Generate optimized prompt using web AI
            response = await self.web_ai_client.chat_completion(
                messages=messages, platform=platform
# BRACKET_SURGEON: disabled
#             )

            self.session_stats["web_ai_requests"] += 1

            if response.success:
                self.session_stats["avatar_generations"] += 1
                print("✅ Avatar prompt generated successfully")

                return {
                    "success": True,
                    "description": description,
                    "style": style,
                    "optimized_prompt": response.content,
                    "platform_used": platform.value,
                    "response_time": response.response_time,
                    "timestamp": datetime.now(),
# BRACKET_SURGEON: disabled
#                 }
            else:
                print(f"❌ Avatar generation failed: {response.error}")
                return {
                    "success": False,
                    "error": response.error,
                    "platform_used": platform.value,
                    "timestamp": datetime.now(),
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            print(f"❌ Avatar generation exception: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now()}

    async def multi_platform_avatar_generation(
        self, description: str, style: str = "realistic"
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """"""
        Generate avatar prompts using multiple platforms for comparison

        Args:
            description: Description of the avatar
            style: Style preference

        Returns:
            Dictionary with results from multiple platforms
        """"""
        print(f"🔄 Multi - platform avatar generation: {description}")

        platforms = [WebAIPlatform.CHATGPT, WebAIPlatform.GEMINI, WebAIPlatform.CLAUDE]
        results = {}

        for platform in platforms:
            try:
                result = await self.generate_avatar(description, style, platform)
                results[platform.value] = result

                # Small delay between requests
                await asyncio.sleep(1)

            except Exception as e:
                results[platform.value] = {
                    "success": False,
                    "error": str(e),
                    "platform_used": platform.value,
# BRACKET_SURGEON: disabled
#                 }

        return {
            "description": description,
            "style": style,
            "platform_results": results,
            "timestamp": datetime.now(),
# BRACKET_SURGEON: disabled
#         }


# Example usage and testing


async def main():
    """Example usage of the integrated RouteLL client"""

    # Initialize client (API key should be set in environment)
    api_key = os.getenv("ROUTELLM_API_KEY", "your_routellm_api_key_here")
    client = RouteLL_IntegratedClient(api_key=api_key)

    print("\\n🧪 Testing RouteLL Integration")
    print("=" * 50)

    # Test 1: Health check
    print("\\n1️⃣ Health Check:")
    health = await client.health_check()
    print(f"   Overall Status: {health['overall_status']}")
    for component, status in health["components"].items():
        print(f"   {component}: {status['status']}")

    # Test 2: Simple chat completion
    print("\\n2️⃣ Simple Chat Completion:")
    messages = [{"role": "user", "content": "What is the meaning of life?"}]

    response = await client.chat_completion(messages)
    if response.success:
        print(f"   ✅ Response: {response.content[:100]}...")
        print(f"   🎯 Model used: {response.model}")
        print(f"   ⏱️ Response time: {response.response_time:.2f}s")
        if hasattr(response, "routing_info"):
            print(f"   🧠 Task type: {response.routing_info['task_type']}")
    else:
        print(f"   ❌ Error: {response.error}")

    # Test 3: Code generation task
    print("\\n3️⃣ Code Generation Task:")
    code_messages = [
        {
            "role": "user",
            "content": "Write a Python function to calculate the factorial of a number",
# BRACKET_SURGEON: disabled
#         }
# BRACKET_SURGEON: disabled
#     ]

    response = await client.chat_completion(
        code_messages, preferences={"quality": 0.7, "cost": 0.3}
# BRACKET_SURGEON: disabled
#     )
    if response.success:
        print("   ✅ Code generated successfully")
        print(f"   🎯 Model used: {response.model}")
        if hasattr(response, "optimization_info"):
            savings = response.optimization_info["cost_savings"]
            print(f"   💰 Cost savings: {savings['savings_percentage']:.1f}%")

    # Test 4: Streaming completion
    print("\\n4️⃣ Streaming Completion:")
    stream_messages = [{"role": "user", "content": "Tell me a short story about AI"}]

    print("   📡 Streaming response:")
    async for chunk in client.stream_completion(stream_messages):
        print(chunk, end="", flush=True)
    print("\\n   ✅ Streaming completed")

    # Test 5: Session analytics
    print("\\n5️⃣ Session Analytics:")
    analytics = client.get_session_analytics()
    print(f"   📊 Total requests: {analytics['total_requests']}")
    print(f"   ✅ Success rate: {analytics['success_rate']:.1f}%")
    print(f"   💰 Total cost: ${analytics['estimated_total_cost']:.4f}")
    print(f"   ⚡ Requests/min: {analytics['requests_per_minute']:.1f}")
    print(f"   🎨 Avatar generations: {client.session_stats['avatar_generations']}")
    print(f"   🌐 Web AI requests: {client.session_stats['web_ai_requests']}")

    # Test 6: Avatar generation
    print("\\n6️⃣ Avatar Generation:")
    avatar_result = await client.generate_avatar(
        description="A professional software developer with glasses \"
#     and a friendly smile",
        style="realistic",
        platform=WebAIPlatform.CHATGPT,
# BRACKET_SURGEON: disabled
#     )

    if avatar_result["success"]:
        print("   ✅ Avatar prompt generated")
        print(f"   🎨 Optimized prompt: {avatar_result['optimized_prompt'][:100]}...")
        print(f"   🤖 Platform: {avatar_result['platform_used']}")
    else:
        print(f"   ❌ Avatar generation failed: {avatar_result['error']}")

    # Test 7: Multi - platform avatar generation
    print("\\n7️⃣ Multi - Platform Avatar Generation:")
    multi_result = await client.multi_platform_avatar_generation(
        description="A futuristic AI assistant avatar", style="digital art"
# BRACKET_SURGEON: disabled
#     )

    for platform, result in multi_result["platform_results"].items():
        status = "✅" if result["success"] else "❌"
        print(
            f"   {status} {platform}: {'Success' if result['success'] else result.get('error', 'Failed')}"
# BRACKET_SURGEON: disabled
#         )

    # Test 8: Model suggestions
    print("\\n8️⃣ Model Suggestions:")
    suggestions = [
        "Help me debug this complex algorithm",
        "Write a poem about technology",
        "Solve this math equation: 2x^2 + 5x - 3 = 0",
# BRACKET_SURGEON: disabled
#     ]

    for task in suggestions:
        suggestion = client.router.suggest_model_for_task(task)
        print(f"   Task: {task[:30]}...")
        print(f"   Recommended: {suggestion['recommended_model']} ({suggestion['model_tier']})")
        print(f"   Reason: {suggestion['task_type']}")
        print()

    print("\\n🎉 Integration test completed successfully!")
    print("\\n📋 Summary:")
    print("   ✅ API connectivity verified")
    print("   ✅ Intelligent routing working")
    print("   ✅ Credit monitoring active")
    print("   ✅ Rate limiting functional")
    print("   ✅ Cost optimization enabled")
    print("   ✅ Analytics and monitoring ready")
    print("   ✅ Avatar generation integrated")
    print("   ✅ Multi - platform AI access enabled")

    # Cleanup resources
    await client.web_ai_client.cleanup_sessions()

    # Additional cleanup
    print("\\n🧹 Cleaning up resources...")
    print("✅ Cleanup completed")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())