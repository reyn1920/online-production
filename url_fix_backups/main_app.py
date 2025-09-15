#!/usr / bin / env python3
""""""
Main Application - Integrated AI Platform
Combines RouteLL, free API fallback, web AI platforms, avatar generation,
and always - available ChatGPT, Gemini, and Abacus AI integration
""""""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core AI integration system

from core_ai_integration import (

    core_ai, ask_ai, ask_all_ai, ai_integrated, get_ai_context,
        AIPlatform, AIRequest, AIResponse
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )

from utils.credit_optimizer import CreditOptimizer
from utils.rate_limiter import RateLimiter

from integrations.free_api_fallback import FallbackProvider, FreeAPIFallback
from integrations.routellm_client import APIResponse, RouteLL_Client
from integrations.web_ai_client import WebAIClient, WebAIPlatform
from services.avatar_generation_service import (AvatarGenerationService, AvatarQuality,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     AvatarRequest, AvatarStyle)


class IntegratedAIPlatform:
    """Main integrated AI platform combining all services with always - available AI integration"""


    def __init__(self, config_path: str = None):
        """Initialize the integrated AI platform with core AI integration"""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Initialize core AI integration (ChatGPT, Gemini, Abacus AI)
        self.core_ai = core_ai
        self.logger.info("Core AI Integration (ChatGPT, Gemini, Abacus AI) initialized")

        # Initialize core services
        self.routell_client = RouteLL_Client()
        self.fallback_system = FreeAPIFallback()
        self.web_ai_client = WebAIClient(config_path)
        self.avatar_service = AvatarGenerationService(config_path)

        # Initialize utilities
        self.rate_limiter = RateLimiter()
        self.credit_optimizer = CreditOptimizer()

        # Enhanced platform statistics with AI integration
        self.platform_stats = {
            "total_requests": 0,
                "routell_requests": 0,
                "fallback_requests": 0,
                "web_ai_requests": 0,
                "avatar_generations": 0,
                "core_ai_requests": 0,
                "chatgpt_requests": 0,
                "gemini_requests": 0,
                "abacus_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "credits_used": 0.0,
                "credits_saved": 0.0,
                "session_start": datetime.now(),
# BRACKET_SURGEON: disabled
#                 }

        # Enhanced service health status with AI platforms
        self.service_health = {
            "routell": "unknown",
                "fallback": "unknown",
                "web_ai": "unknown",
                "avatar_service": "unknown",
                "chatgpt": "available",
                "gemini": "available",
                "abacus_ai": "available",
                "core_ai_integration": "active"
# BRACKET_SURGEON: disabled
#         }

        # Log AI platform URLs
        ai_status = self.core_ai.get_platform_status()
        for platform, info in ai_status.items():
            self.logger.info(f"{platform.upper()} available at: {info['url']}")

        self.logger.info("Integrated AI Platform with Core AI Integration initialized")

    @ai_integrated


    async def process_with_ai_enhancement(self,
    task: str,
    content: str,
    task_type: str = "general") -> Dict[str,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     Any]:
        """Process any task with AI enhancement from all three platforms"""
        self.logger.info(f"Processing task '{task}' with AI enhancement")

        # Get AI insights from all platforms
        ai_prompt = f"Task: {task}\\nContent: {content}\\nPlease provide analysis \"
#     and recommendations."
        ai_responses = await ask_all_ai(ai_prompt, task_type)

        # Update statistics
        self.platform_stats["core_ai_requests"] += len(ai_responses)
        for platform_name, response in ai_responses.items():
            if platform_name == "chatgpt":
                self.platform_stats["chatgpt_requests"] += 1
            elif platform_name == "gemini":
                self.platform_stats["gemini_requests"] += 1
            elif platform_name == "abacus":
                self.platform_stats["abacus_requests"] += 1

        return {
            "task": task,
                "original_content": content,
                "ai_insights": ai_responses,
                "enhanced_context": get_ai_context({"task": task, "content_length": len(content)}),
                "timestamp": datetime.now().isoformat()
# BRACKET_SURGEON: disabled
#         }


    async def get_ai_recommendation(self,
    query: str,
# BRACKET_SURGEON: disabled
#     platform: AIPlatform = AIPlatform.CHATGPT) -> AIResponse:
        """Get a recommendation from a specific AI platform"""
        self.logger.info(f"Getting AI recommendation from {platform.value}")
        response = await ask_ai(query, platform, "recommendation")

        # Update statistics
        self.platform_stats["core_ai_requests"] += 1
        if platform == AIPlatform.CHATGPT:
            self.platform_stats["chatgpt_requests"] += 1
        elif platform == AIPlatform.GEMINI:
            self.platform_stats["gemini_requests"] += 1
        elif platform == AIPlatform.ABACUS:
            self.platform_stats["abacus_requests"] += 1

        return response


    async def analyze_with_all_ai(self,
    content: str,
    analysis_type: str = "comprehensive") -> Dict[str,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     Any]:
        """Analyze content with all three AI platforms for comprehensive insights"""
        self.logger.info(f"Performing {analysis_type} analysis with all AI platforms")

        analysis_prompt = f"Please perform a {analysis_type} analysis of the following content:\\n\\n{content}"
        ai_responses = await ask_all_ai(analysis_prompt, "analysis")

        # Update statistics
        self.platform_stats["core_ai_requests"] += len(ai_responses)
        for platform_name in ai_responses.keys():
            if platform_name == "chatgpt":
                self.platform_stats["chatgpt_requests"] += 1
            elif platform_name == "gemini":
                self.platform_stats["gemini_requests"] += 1
            elif platform_name == "abacus":
                self.platform_stats["abacus_requests"] += 1

        # Create comprehensive analysis report
        analysis_report = {
            "analysis_type": analysis_type,
                "content_analyzed": content[:200] + "..." if len(content) > 200 else content,
                "ai_insights": ai_responses,
                "consensus_points": self._extract_consensus(ai_responses),
                "unique_insights": self._extract_unique_insights(ai_responses),
                "timestamp": datetime.now().isoformat(),
                "platforms_used": list(ai_responses.keys())
# BRACKET_SURGEON: disabled
#         }

        return analysis_report


    def _extract_consensus(self, ai_responses: Dict[str, AIResponse]) -> List[str]:
        """Extract consensus points from multiple AI responses"""
        # Simple consensus extraction (in production, this could use NLP)
        consensus_points = []

        # Look for common themes or keywords
        all_responses = [resp.content.lower() for resp in ai_responses.values() if resp.success]

        common_words = ["optimize", "improve", "enhance", "recommend", "suggest", "consider"]
        for word in common_words:
            if sum(1 for response in all_responses if word in response) >= 2:
                consensus_points.append(f"Multiple AI platforms suggest focusing on: {word}")

        return consensus_points[:5]  # Limit to top 5 consensus points


    def _extract_unique_insights(self,
    ai_responses: Dict[str,
    AIResponse]) -> Dict[str,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     str]:
        """Extract unique insights from each AI platform"""
        unique_insights = {}

        for platform, response in ai_responses.items():
            if response.success:
                # Extract first sentence as unique insight
                sentences = response.content.split('. ')
                if sentences:
                    unique_insights[platform] = sentences[0] + "."

        return unique_insights


    async def get_enhanced_platform_stats(self) -> Dict[str, Any]:
        """Get comprehensive platform statistics including AI integration"""
        base_stats = self.platform_stats.copy()
        ai_stats = self.core_ai.get_integration_stats()

        enhanced_stats = {
            **base_stats,
                "ai_integration_stats": ai_stats,
                "service_health": self.service_health,
                "ai_platform_status": self.core_ai.get_platform_status(),
                "uptime_seconds": (datetime.now() - base_stats["session_start"]).total_seconds()
# BRACKET_SURGEON: disabled
#         }

        return enhanced_stats


    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level = logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler("logs / main_app.log"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )


    async def initialize(self):
        """Initialize all services and perform health checks"""
        self.logger.info("Initializing integrated AI platform...")

        try:
            # Perform health checks
            await self._perform_health_checks()

            # Initialize rate limiting if available
            if hasattr(self.rate_limiter, "initialize"):
                await self.rate_limiter.initialize()

            self.logger.info("Platform initialization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Platform initialization failed: {e}")
            return False


    async def _perform_health_checks(self):
        """Perform health checks on all services"""
        self.logger.info("Performing health checks...")

        # RouteLL health check
        try:
            if hasattr(self.routell_client, "health_check"):
                routell_health = await self.routell_client.health_check()
                self.service_health["routell"] = (
                    "healthy" if routell_health.get("status") == "healthy" else "error"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                self.service_health["routell"] = "available"
        except Exception as e:
            self.logger.warning(f"RouteLL health check failed: {e}")
            self.service_health["routell"] = "error"

        # Fallback system health check
        try:
            if hasattr(self.fallback_system, "health_check"):
                fallback_health = await self.fallback_system.health_check()
                self.service_health["fallback"] = (
                    "healthy" if fallback_health.get("status") == "healthy" else "error"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                self.service_health["fallback"] = "available"
        except Exception as e:
            self.logger.warning(f"Fallback system health check failed: {e}")
            self.service_health["fallback"] = "error"

        # Web AI health check
        try:
            if hasattr(self.web_ai_client, "health_check"):
                web_ai_health = await self.web_ai_client.health_check()
                self.service_health["web_ai"] = (
                    "healthy" if web_ai_health.get("status") == "healthy" else "error"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                self.service_health["web_ai"] = "available"
        except Exception as e:
            self.logger.warning(f"Web AI health check failed: {e}")
            self.service_health["web_ai"] = "error"

        # Avatar service health check
        try:
            if hasattr(self.avatar_service, "health_check"):
                avatar_health = await self.avatar_service.health_check()
                self.service_health["avatar_service"] = (
                    "healthy" if avatar_health else "error"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                avatar_health = await self.avatar_service.get_service_analytics()
                self.service_health["avatar_service"] = (
                    "healthy" if avatar_health else "error"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
        except Exception as e:
            self.logger.warning(f"Avatar service health check failed: {e}")
            self.service_health["avatar_service"] = "error"

        self.logger.info(f"Health check results: {self.service_health}")


    async def chat_completion(
        self,
            messages: List[Dict],
            model: str = None,
            use_fallback: bool = True,
            use_web_ai: bool = False,
            web_platform: WebAIPlatform = None,
# BRACKET_SURGEON: disabled
#             ) -> APIResponse:
        """"""
        Intelligent chat completion with automatic fallback

        Args:
            messages: List of message dictionaries
            model: Preferred model to use
            use_fallback: Whether to use fallback if RouteLL fails
            use_web_ai: Whether to use web AI platforms
            web_platform: Specific web platform to use

        Returns:
            API response with completion
        """"""
        start_time = time.time()
        self.platform_stats["total_requests"] += 1

        try:
            # Rate limiting check if available
            if hasattr(self.rate_limiter, "can_proceed"):
                if not await self.rate_limiter.can_proceed():
                    return APIResponse(
                        success = False,
                    data={"error": "Rate limit exceeded"},
                    credits_used = 0.0,
                    model_used = model or "unknown",
                    timestamp = datetime.now().isoformat(),
                    error="Rate limit exceeded",
                    response_time_ms = int((time.time() - start_time) * 1000),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

            # Try web AI first if requested
            if use_web_ai:
                return await self._try_web_ai_completion(
                    messages, web_platform, start_time
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Try RouteLL first
            routell_response = await self._try_routell_completion(
                messages, model, start_time
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            if routell_response.success:
                return routell_response

            # Try fallback if RouteLL failed and fallback is enabled
            if use_fallback and self.service_health["fallback"] == "healthy":
                return await self._try_fallback_completion(messages, start_time)

            # If all else fails, try web AI as last resort
            if self.service_health["web_ai"] == "healthy":
                return await self._try_web_ai_completion(messages, None, start_time)

            # Complete failure
            self.platform_stats["failed_requests"] += 1
            return APIResponse(
                success = False,
                    data={"error": "All services unavailable"},
                    credits_used = 0.0,
                    model_used = model or "unknown",
                    timestamp = datetime.now().isoformat(),
                    error="All services unavailable",
                    response_time_ms = int((time.time() - start_time) * 1000),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            self.platform_stats["failed_requests"] += 1
            return APIResponse(
                success = False,
                    data={"error": str(e)},
                    credits_used = 0.0,
                    model_used = model or "unknown",
                    timestamp = datetime.now().isoformat(),
                    error = str(e),
                    response_time_ms = int((time.time() - start_time) * 1000),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def _try_routell_completion(
        self, messages: List[Dict], model: str, start_time: float
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Try RouteLL completion"""
        try:
            self.logger.info("Attempting RouteLL completion")
            response = await self.routell_client.chat_completion(messages, model)

            self.platform_stats["routell_requests"] += 1

            if response.success:
                self.platform_stats["successful_requests"] += 1
                self.platform_stats["credits_used"] += response.credits_used or 0
                self.logger.info(
                    f"RouteLL completion successful, credits used: {response.credits_used}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            return response

        except Exception as e:
            self.logger.warning(f"RouteLL completion failed: {e}")
            return APIResponse(
                success = False,
                    data={"error": f"RouteLL error: {str(e)}"},
                    credits_used = 0.0,
                    model_used = model or "unknown",
                    timestamp = datetime.now().isoformat(),
                    error = f"RouteLL error: {str(e)}",
                    response_time_ms = int((time.time() - start_time) * 1000),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def _try_fallback_completion(
        self, messages: List[Dict], start_time: float
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Try fallback completion"""
        try:
            self.logger.info("Attempting fallback completion")
            fallback_response = await self.fallback_system.chat_completion(messages)

            self.platform_stats["fallback_requests"] += 1

            if fallback_response.success:
                self.platform_stats["successful_requests"] += 1
                # Estimate credits saved by using fallback
                estimated_saved = 0.01  # Rough estimate
                self.platform_stats["credits_saved"] += estimated_saved

                self.logger.info(
                    f"Fallback completion successful with {fallback_response.provider}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                return APIResponse(
                    success = True,
                        data = fallback_response.content,
                        credits_used = 0,  # Free fallback
                        response_time_ms = int(fallback_response.response_time * 1000),
                        model_used = fallback_response.model or "fallback",
                        provider = fallback_response.provider,
                        fallback_used = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
            else:
                return APIResponse(
                    success = False,
                        data={"error": f"Fallback error: {fallback_response.error}"},
                        credits_used = 0.0,
                        model_used="fallback",
                        timestamp = datetime.now().isoformat(),
                        error = f"Fallback error: {fallback_response.error}",
                        response_time_ms = int((time.time() - start_time) * 1000),
                        fallback_used = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

        except Exception as e:
            self.logger.warning(f"Fallback completion failed: {e}")
            return APIResponse(
                success = False,
                    data={"error": f"Fallback error: {str(e)}"},
                    credits_used = 0.0,
                    model_used="fallback",
                    timestamp = datetime.now().isoformat(),
                    error = f"Fallback error: {str(e)}",
                    response_time_ms = int((time.time() - start_time) * 1000),
                    fallback_used = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def _try_web_ai_completion(
        self, messages: List[Dict], platform: WebAIPlatform, start_time: float
# BRACKET_SURGEON: disabled
#     ) -> APIResponse:
        """Try web AI completion"""
        try:
            platform = platform or WebAIPlatform.CHATGPT
            self.logger.info(f"Attempting web AI completion with {platform.value}")

            response = await self.web_ai_client.chat_completion(messages, platform)

            self.platform_stats["web_ai_requests"] += 1

            if response.success:
                self.platform_stats["successful_requests"] += 1
                # Estimate credits saved by using web AI
                estimated_saved = 0.005  # Rough estimate
                self.platform_stats["credits_saved"] += estimated_saved

                self.logger.info(f"Web AI completion successful with {platform.value}")

                return APIResponse(
                    success = True,
                        data = response.content,
                        credits_used = 0,  # Free web AI
                        response_time_ms = int(response.response_time * 1000),
                        model_used = f"web-{platform.value}",
                        provider = platform.value,
                        fallback_used = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
            else:
                return APIResponse(
                    success = False,
                        data={"error": f"Web AI error: {response.error}"},
                        credits_used = 0.0,
                        model_used = f"web-{platform.value}",
                        timestamp = datetime.now().isoformat(),
                        error = f"Web AI error: {response.error}",
                        response_time_ms = int((time.time() - start_time) * 1000),
                        provider = platform.value,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

        except Exception as e:
            self.logger.warning(f"Web AI completion failed: {e}")
            return APIResponse(
                success = False,
                    data={"error": f"Web AI error: {str(e)}"},
                    credits_used = 0.0,
                    model_used = f"web-{platform.value if platform else 'unknown'}",
                    timestamp = datetime.now().isoformat(),
                    error = f"Web AI error: {str(e)}",
                    response_time_ms = int((time.time() - start_time) * 1000),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    async def generate_avatar(
        self,
            description: str,
            style: AvatarStyle = AvatarStyle.REALISTIC,
            quality: AvatarQuality = AvatarQuality.STANDARD,
            use_multi_platform: bool = False,
# BRACKET_SURGEON: disabled
#             ) -> Dict:
        """"""
        Generate avatar using the avatar generation service

        Args:
            description: Description of the avatar
            style: Avatar style
            quality: Avatar quality level
            use_multi_platform: Whether to use multiple platforms for comparison

        Returns:
            Avatar generation result
        """"""
        try:
            self.logger.info(f"Generating avatar: {description}")

            request = AvatarRequest(
                description = description,
                style = style,
                quality = quality,
                use_multi_platform = use_multi_platform,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            result = await self.avatar_service.generate_avatar(request)

            self.platform_stats["avatar_generations"] += 1

            if result.success:
                self.logger.info(f"Avatar generation successful")
            else:
                self.logger.warning(f"Avatar generation failed: {result.error}")

            return asdict(result)

        except Exception as e:
            self.logger.error(f"Avatar generation exception: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now()}


    async def get_platform_analytics(self) -> Dict:
        """Get comprehensive platform analytics"""
        session_duration = (
            datetime.now() - self.platform_stats["session_start"]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ).total_seconds()

        # Get service - specific analytics
        try:
            avatar_analytics = await self.avatar_service.get_service_analytics()
        except Exception:
            avatar_analytics = {}

        try:
            fallback_analytics = await self.fallback_system.get_analytics()
        except Exception:
            fallback_analytics = {}

        analytics = {
            "platform_overview": {
                "session_duration_seconds": session_duration,
                    "total_requests": self.platform_stats["total_requests"],
                    "successful_requests": self.platform_stats["successful_requests"],
                    "failed_requests": self.platform_stats["failed_requests"],
                    "success_rate": (
                    self.platform_stats["successful_requests"]/max(self.platform_stats["total_requests"],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     1)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                * 100,
                    "requests_per_minute": (
                    self.platform_stats["total_requests"]/max(session_duration / 60, 1)
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#                     },
                "service_usage": {
                "routell_requests": self.platform_stats["routell_requests"],
                    "fallback_requests": self.platform_stats["fallback_requests"],
                    "web_ai_requests": self.platform_stats["web_ai_requests"],
                    "avatar_generations": self.platform_stats["avatar_generations"],
# BRACKET_SURGEON: disabled
#                     },
                "cost_analysis": {
                "credits_used": self.platform_stats["credits_used"],
                    "credits_saved": self.platform_stats["credits_saved"],
                    "estimated_cost_usd": self.platform_stats["credits_used"]
                * 0.01,  # Rough estimate
                "estimated_savings_usd": self.platform_stats["credits_saved"] * 0.01,
# BRACKET_SURGEON: disabled
#                     },
                "service_health": self.service_health,
                "avatar_service_analytics": avatar_analytics,
                "fallback_analytics": fallback_analytics,
# BRACKET_SURGEON: disabled
#                 }

        return analytics


    async def cleanup(self):
        """Cleanup all services and resources"""
        self.logger.info("Cleaning up integrated AI platform...")

        try:
            # Cleanup all services if methods exist
            if hasattr(self.rate_limiter, "cleanup"):
                await self.rate_limiter.cleanup()
            if hasattr(self.web_ai_client, "cleanup_sessions"):
                await self.web_ai_client.cleanup_sessions()
            if hasattr(self.avatar_service, "cleanup"):
                await self.avatar_service.cleanup()

            # Log final statistics
            final_analytics = await self.get_platform_analytics()
            self.logger.info(
                f"Final platform analytics: {json.dumps(final_analytics,"
    indent = 2,
# BRACKET_SURGEON: disabled
#     default = str)}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            self.logger.info("Platform cleanup completed successfully")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


async def main():
    """Main application demo"""
    print("🚀 Integrated AI Platform Demo")
    print("=" * 60)

    # Initialize platform
    platform = IntegratedAIPlatform()

    try:
        # Initialize services
        print("\\n🔧 Initializing services...")
        init_success = await platform.initialize()

        if not init_success:
            print("❌ Platform initialization failed")
            return

        print("✅ Platform initialized successfully")

        # Test 1: Health checks
        print("\\n📊 Service Health Status:")
        for service, status in platform.service_health.items():
            status_icon = "✅" if status == "healthy" else "❌"
            print(f"   {status_icon} {service}: {status}")

        # Test 2: Chat completion with RouteLL
        print("\\n💬 Testing Chat Completion (RouteLL):")
        messages = [
            {
                "role": "user",
                    "content": "Hello! Can you help me with a coding question?",
# BRACKET_SURGEON: disabled
#                     }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        response = await platform.chat_completion(messages, use_web_ai = False)
        print(f"   Success: {response.success}")
        print(f"   Provider: {response.provider}")
        print(f"   Credits used: {response.credits_used}")
        if response.success:
            print(f"   Response: {response.data[:100]}...")

        # Test 3: Chat completion with Web AI fallback
        print("\\n🌐 Testing Web AI Completion:")
        web_messages = [
            {
                "role": "user",
                    "content": "What are the best practices for avatar design?",
# BRACKET_SURGEON: disabled
#                     }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        web_response = await platform.chat_completion(
            web_messages, use_web_ai = True, web_platform = WebAIPlatform.CHATGPT
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        print(f"   Success: {web_response.success}")
        print(f"   Provider: {web_response.provider}")
        if web_response.success:
            print(f"   Response: {web_response.data[:100]}...")

        # Test 4: Avatar generation
        print("\\n🎨 Testing Avatar Generation:")
        avatar_result = await platform.generate_avatar(
            description="A professional software engineer with a friendly demeanor",
            style = AvatarStyle.PROFESSIONAL,
            quality = AvatarQuality.HIGH,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        print(f"   Success: {avatar_result['success']}")
        if avatar_result["success"]:
            print(f"   Platform used: {avatar_result.get('platform_used')}")
            print(f"   Generation time: {avatar_result.get('generation_time', 0):.2f}s")
            print(f"   Prompt: {avatar_result.get('optimized_prompt', '')[:100]}...")

        # Test 5: Multi - platform avatar generation
        print("\\n🔄 Testing Multi - Platform Avatar Generation:")
        multi_avatar_result = await platform.generate_avatar(
            description="A futuristic AI assistant with glowing blue eyes",
            style = AvatarStyle.CYBERPUNK,
            quality = AvatarQuality.PREMIUM,
            use_multi_platform = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        print(f"   Success: {multi_avatar_result['success']}")
        if multi_avatar_result["success"]:
            platforms_compared = multi_avatar_result.get("platforms_compared", [])
            alternatives = multi_avatar_result.get("alternative_prompts", [])
            print(f"   Platforms compared: {len(platforms_compared)}")
            print(f"   Alternative prompts: {len(alternatives)}")

        # Test 6: Platform analytics
        print("\\n📈 Platform Analytics:")
        analytics = await platform.get_platform_analytics()

        overview = analytics["platform_overview"]
        usage = analytics["service_usage"]
        costs = analytics["cost_analysis"]

        print(f"   Total requests: {overview['total_requests']}")
        print(f"   Success rate: {overview['success_rate']:.1f}%")
        print(f"   RouteLL requests: {usage['routell_requests']}")
        print(f"   Fallback requests: {usage['fallback_requests']}")
        print(f"   Web AI requests: {usage['web_ai_requests']}")
        print(f"   Avatar generations: {usage['avatar_generations']}")
        print(f"   Credits used: {costs['credits_used']:.4f}")
        print(f"   Credits saved: {costs['credits_saved']:.4f}")
        print(f"   Estimated cost: ${costs['estimated_cost_usd']:.4f}")
        print(f"   Estimated savings: ${costs['estimated_savings_usd']:.4f}")

        print("\\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

    finally:
        # Cleanup
        await platform.cleanup()
        print("\\n🧹 Platform cleanup completed")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok = True)

    # Run the main application
    asyncio.run(main())