#!/usr/bin/env python3
"""
Avatar Generation Service
Provides comprehensive avatar generation capabilities using web AI platforms
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.mcp_client import MCPClient
from integrations.puppeteer_service import PuppeteerService
from integrations.web_ai_client import WebAIClient, WebAIPlatform


class AvatarStyle(Enum):
    """Supported avatar styles"""

    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    ARTISTIC = "artistic"
    MINIMALIST = "minimalist"
    CYBERPUNK = "cyberpunk"
    FANTASY = "fantasy"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FUTURISTIC = "futuristic"


class AvatarQuality(Enum):
    """Avatar quality levels"""

    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"


@dataclass
class AvatarRequest:
    """Avatar generation request"""

    description: str
    style: AvatarStyle = AvatarStyle.REALISTIC
    quality: AvatarQuality = AvatarQuality.STANDARD
    platform: Optional[WebAIPlatform] = None
    custom_modifiers: List[str] = None
    use_multi_platform: bool = False
    max_prompt_length: int = 500


@dataclass
class AvatarResult:
    """Avatar generation result"""

    success: bool
    request: AvatarRequest
    optimized_prompt: Optional[str] = None
    alternative_prompts: List[str] = None
    platform_used: Optional[str] = None
    platforms_compared: List[str] = None
    generation_time: float = 0.0
    quality_score: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class AvatarGenerationService:
    """Comprehensive avatar generation service"""

    def __init__(self, config_path: str = None):
        """Initialize avatar generation service"""
        self.web_ai_client = WebAIClient(config_path)
        self.puppeteer_service = PuppeteerService()
        self.mcp_client = MCPClient()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Load configuration
        self.config = self._load_config(config_path)

        # Generation statistics
        self.stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "platform_usage": {},
            "style_usage": {},
            "quality_usage": {},
            "average_generation_time": 0.0,
            "service_start_time": datetime.now(),
        }

        # Quality modifiers for different quality levels
        self.quality_modifiers = {
            AvatarQuality.DRAFT: ["simple", "basic"],
            AvatarQuality.STANDARD: ["detailed", "good quality"],
            AvatarQuality.HIGH: [
                "high quality",
                "detailed",
                "professional",
                "sharp focus",
            ],
            AvatarQuality.PREMIUM: [
                "ultra high quality",
                "8k resolution",
                "masterpiece",
                "professional photography",
                "studio lighting",
                "sharp focus",
                "highly detailed",
                "photorealistic",
            ],
        }

        # Style-specific modifiers
        self.style_modifiers = {
            AvatarStyle.REALISTIC: [
                "photorealistic",
                "natural lighting",
                "human features",
            ],
            AvatarStyle.CARTOON: ["cartoon style", "animated", "colorful", "stylized"],
            AvatarStyle.ANIME: ["anime style", "manga", "cel shading", "large eyes"],
            AvatarStyle.ARTISTIC: ["artistic", "painterly", "expressive", "creative"],
            AvatarStyle.MINIMALIST: [
                "minimalist",
                "simple",
                "clean lines",
                "geometric",
            ],
            AvatarStyle.CYBERPUNK: [
                "cyberpunk",
                "neon",
                "futuristic",
                "tech",
                "digital",
            ],
            AvatarStyle.FANTASY: ["fantasy", "magical", "ethereal", "mystical"],
            AvatarStyle.PROFESSIONAL: [
                "professional",
                "business",
                "formal",
                "corporate",
            ],
            AvatarStyle.CASUAL: ["casual", "relaxed", "friendly", "approachable"],
            AvatarStyle.FUTURISTIC: [
                "futuristic",
                "sci-fi",
                "advanced",
                "technological",
            ],
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_config(self, config_path: str = None) -> Dict:
        """Load service configuration"""
        default_config = {
            "max_concurrent_generations": 3,
            "default_platform": WebAIPlatform.CHATGPT,
            "enable_multi_platform_comparison": True,
            "quality_validation_enabled": True,
            "prompt_optimization_enabled": True,
            "cache_enabled": True,
            "cache_duration_minutes": 60,
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    if "avatar_generation" in config_data:
                        default_config.update(config_data["avatar_generation"])
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")

        return default_config

    async def generate_avatar(self, request: AvatarRequest) -> AvatarResult:
        """
        Generate avatar based on request

        Args:
            request: Avatar generation request

        Returns:
            Avatar generation result
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            self.logger.info(f"Starting avatar generation: {request.description}")

            # Update usage statistics
            self._update_usage_stats(request)

            if request.use_multi_platform:
                result = await self._generate_multi_platform_avatar(request)
            else:
                result = await self._generate_single_platform_avatar(request)

            # Calculate generation time
            result.generation_time = time.time() - start_time

            # Update statistics
            if result.success:
                self.stats["successful_generations"] += 1
                self._update_average_generation_time(result.generation_time)
            else:
                self.stats["failed_generations"] += 1

            self.logger.info(f"Avatar generation completed: {result.success}")
            return result

        except Exception as e:
            self.logger.error(f"Avatar generation failed: {e}")
            self.stats["failed_generations"] += 1

            return AvatarResult(
                success=False,
                request=request,
                error=str(e),
                generation_time=time.time() - start_time,
            )

    async def _generate_single_platform_avatar(
        self, request: AvatarRequest
    ) -> AvatarResult:
        """Generate avatar using single platform"""
        platform = request.platform or self.config["default_platform"]

        # Build optimized prompt
        optimized_prompt = self._build_optimized_prompt(request)

        # Create messages for AI
        messages = [
            {
                "role": "system",
                "content": "You are an expert at creating detailed prompts for AI image generation. Create optimized prompts that produce high-quality avatar images.",
            },
            {
                "role": "user",
                "content": f"Create a detailed prompt for generating an avatar with these specifications: {optimized_prompt}. Make it suitable for AI image generators like DALL-E, Midjourney, or Stable Diffusion.",
            },
        ]

        # Generate using web AI
        response = await self.web_ai_client.chat_completion(
            messages=messages, platform=platform
        )

        if response.success:
            # Validate and optimize the generated prompt
            final_prompt = self._validate_and_optimize_prompt(
                response.content, request.max_prompt_length
            )

            return AvatarResult(
                success=True,
                request=request,
                optimized_prompt=final_prompt,
                platform_used=platform.value,
                metadata={
                    "original_response": response.content,
                    "response_time": response.response_time,
                },
            )
        else:
            return AvatarResult(
                success=False,
                request=request,
                error=response.error,
                platform_used=platform.value,
            )

    async def _generate_multi_platform_avatar(
        self, request: AvatarRequest
    ) -> AvatarResult:
        """Generate avatar using multiple platforms for comparison"""
        platforms = [WebAIPlatform.CHATGPT, WebAIPlatform.GEMINI, WebAIPlatform.CLAUDE]
        results = {}

        # Generate prompts from multiple platforms
        for platform in platforms:
            try:
                platform_request = AvatarRequest(
                    description=request.description,
                    style=request.style,
                    quality=request.quality,
                    platform=platform,
                    custom_modifiers=request.custom_modifiers,
                    max_prompt_length=request.max_prompt_length,
                )

                result = await self._generate_single_platform_avatar(platform_request)
                results[platform.value] = result

                # Small delay between requests
                await asyncio.sleep(0.5)

            except Exception as e:
                self.logger.warning(f"Platform {platform.value} failed: {e}")
                results[platform.value] = AvatarResult(
                    success=False,
                    request=platform_request,
                    error=str(e),
                    platform_used=platform.value,
                )

        # Select best result and compile alternatives
        best_result = self._select_best_result(results)
        alternative_prompts = [
            result.optimized_prompt
            for result in results.values()
            if result.success and result != best_result
        ]

        if best_result:
            best_result.alternative_prompts = alternative_prompts
            best_result.platforms_compared = list(results.keys())
            best_result.metadata["multi_platform_results"] = {
                platform: {"success": result.success, "error": result.error}
                for platform, result in results.items()
            }

        return best_result or AvatarResult(
            success=False,
            request=request,
            error="All platforms failed",
            platforms_compared=list(results.keys()),
        )

    def _build_optimized_prompt(self, request: AvatarRequest) -> str:
        """Build optimized prompt from request"""
        components = [request.description]

        # Add style modifiers
        if request.style in self.style_modifiers:
            components.extend(self.style_modifiers[request.style])

        # Add quality modifiers
        if request.quality in self.quality_modifiers:
            components.extend(self.quality_modifiers[request.quality])

        # Add custom modifiers
        if request.custom_modifiers:
            components.extend(request.custom_modifiers)

        return ", ".join(components)

    def _validate_and_optimize_prompt(self, prompt: str, max_length: int) -> str:
        """Validate and optimize generated prompt"""
        # Remove excessive whitespace
        prompt = " ".join(prompt.split())

        # Truncate if too long
        if len(prompt) > max_length:
            prompt = prompt[:max_length].rsplit(" ", 1)[0] + "..."

        return prompt

    def _select_best_result(self, results: Dict) -> Optional[AvatarResult]:
        """Select best result from multiple platform results"""
        successful_results = [result for result in results.values() if result.success]

        if not successful_results:
            return None

        # Simple selection: prefer ChatGPT, then Gemini, then Claude
        platform_priority = ["chatgpt", "gemini", "claude"]

        for platform in platform_priority:
            for result in successful_results:
                if result.platform_used == platform:
                    return result

        # Fallback to first successful result
        return successful_results[0]

    def _update_usage_stats(self, request: AvatarRequest):
        """Update usage statistics"""
        # Update style usage
        style_name = request.style.value
        if style_name not in self.stats["style_usage"]:
            self.stats["style_usage"][style_name] = 0
        self.stats["style_usage"][style_name] += 1

        # Update quality usage
        quality_name = request.quality.value
        if quality_name not in self.stats["quality_usage"]:
            self.stats["quality_usage"][quality_name] = 0
        self.stats["quality_usage"][quality_name] += 1

    def _update_average_generation_time(self, generation_time: float):
        """Update average generation time"""
        current_avg = self.stats["average_generation_time"]
        successful_count = self.stats["successful_generations"]

        if successful_count == 1:
            self.stats["average_generation_time"] = generation_time
        else:
            self.stats["average_generation_time"] = (
                current_avg * (successful_count - 1) + generation_time
            ) / successful_count

    async def get_service_analytics(self) -> Dict:
        """Get comprehensive service analytics"""
        service_uptime = (
            datetime.now() - self.stats["service_start_time"]
        ).total_seconds()

        analytics = {
            "service_uptime_seconds": service_uptime,
            "total_requests": self.stats["total_requests"],
            "successful_generations": self.stats["successful_generations"],
            "failed_generations": self.stats["failed_generations"],
            "success_rate": (
                self.stats["successful_generations"]
                / max(self.stats["total_requests"], 1)
            )
            * 100,
            "average_generation_time": self.stats["average_generation_time"],
            "requests_per_hour": (
                self.stats["total_requests"] / max(service_uptime / 3600, 1)
            ),
            "style_usage": self.stats["style_usage"],
            "quality_usage": self.stats["quality_usage"],
            "platform_usage": self.stats["platform_usage"],
        }

        # Add platform health status
        platform_health = {}
        for platform in WebAIPlatform:
            try:
                # Quick health check (placeholder)
                platform_health[platform.value] = "healthy"
            except:
                platform_health[platform.value] = "error"

        analytics["platform_health"] = platform_health

        return analytics

    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Cleaning up avatar generation service...")

        try:
            await self.web_ai_client.cleanup_sessions()
            await self.puppeteer_service.cleanup_all_sessions()
            self.logger.info("Avatar generation service cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


async def main():
    """Demo function for avatar generation service"""
    print("🎨 Avatar Generation Service Demo")
    print("=" * 50)

    service = AvatarGenerationService()

    try:
        # Test 1: Simple avatar generation
        print("\n1️⃣ Simple Avatar Generation")
        request = AvatarRequest(
            description="A friendly software developer with glasses",
            style=AvatarStyle.PROFESSIONAL,
            quality=AvatarQuality.HIGH,
        )

        result = await service.generate_avatar(request)
        print(f"Success: {result.success}")
        if result.success:
            print(f"Prompt: {result.optimized_prompt[:100]}...")
            print(f"Platform: {result.platform_used}")
            print(f"Time: {result.generation_time:.2f}s")

        # Test 2: Multi-platform comparison
        print("\n2️⃣ Multi-Platform Comparison")
        multi_request = AvatarRequest(
            description="A futuristic AI assistant avatar",
            style=AvatarStyle.CYBERPUNK,
            quality=AvatarQuality.PREMIUM,
            use_multi_platform=True,
        )

        multi_result = await service.generate_avatar(multi_request)
        print(f"Success: {multi_result.success}")
        if multi_result.success:
            print(f"Best prompt: {multi_result.optimized_prompt[:100]}...")
            print(f"Platforms compared: {multi_result.platforms_compared}")
            print(f"Alternatives: {len(multi_result.alternative_prompts or [])}")

        # Test 3: Service analytics
        print("\n3️⃣ Service Analytics")
        analytics = await service.get_service_analytics()
        print(f"Total requests: {analytics['total_requests']}")
        print(f"Success rate: {analytics['success_rate']:.1f}%")
        print(f"Average time: {analytics['average_generation_time']:.2f}s")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

    finally:
        await service.cleanup()
        print("\n✅ Demo completed")


if __name__ == "__main__":
    asyncio.run(main())
