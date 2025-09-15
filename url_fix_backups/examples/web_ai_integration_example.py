#!/usr / bin / env python3
""""""
Web AI Integration Example
Demonstrates how to use web AI platforms for avatar generation and chat completion
""""""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.mcp_client import MCPClient
from integrations.puppeteer_service import PuppeteerService
from integrations.web_ai_client import WebAIClient, WebAIPlatform


class WebAIIntegration:
    """Integrated web AI client for avatar generation and chat"""

    def __init__(self, config_path: str = None):
        """Initialize web AI integration"""
        self.web_ai_client = WebAIClient(config_path)
        self.puppeteer_service = PuppeteerService()
        self.mcp_client = MCPClient()
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "platform_usage": {},
            "session_start": datetime.now(),
# BRACKET_SURGEON: disabled
#         }

    async def generate_avatar_prompt(
        self,
        description: str,
        style: str = "realistic",
        platform: WebAIPlatform = WebAIPlatform.CHATGPT,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """"""
        Generate an optimized prompt for avatar creation

        Args:
            description: Basic description of the avatar
            style: Style preference (realistic, cartoon, artistic, etc.)
            platform: AI platform to use for prompt generation

        Returns:
            Optimized prompt for avatar generation
        """"""
        try:
            print(f"🎨 Generating avatar prompt using {platform.value}...")

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating detailed prompts for AI image generation. Create optimized prompts that produce high - quality avatar images.",
# BRACKET_SURGEON: disabled
#                 },
                {
                    "role": "user",
                    "content": f"Create a detailed prompt for generating a {style} avatar with this description: {description}. Include specific details about lighting, composition, \"
#     and quality modifiers that work well with AI image generators.",
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             ]

            response = await self.web_ai_client.chat_completion(
                messages=messages, platform=platform
# BRACKET_SURGEON: disabled
#             )

            self._update_stats(platform, response.success)

            if response.success:
                print(f"✅ Avatar prompt generated successfully")
                return response.content
            else:
                print(f"❌ Failed to generate avatar prompt: {response.error}")
                return f"A {style} avatar of {description}"

        except Exception as e:
            print(f"❌ Avatar prompt generation failed: {e}")
            self._update_stats(platform, False)
            return f"A {style} avatar of {description}"

    async def chat_with_platform(
        self, messages: List[Dict], platform: WebAIPlatform = WebAIPlatform.CHATGPT
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """"""
        Send chat completion request to specified platform

        Args:
            messages: List of message dictionaries
            platform: AI platform to use

        Returns:
            Response dictionary with success status and content
        """"""
        try:
            print(f"💬 Sending chat request to {platform.value}...")

            response = await self.web_ai_client.chat_completion(
                messages=messages, platform=platform
# BRACKET_SURGEON: disabled
#             )

            self._update_stats(platform, response.success)

            if response.success:
                print(f"✅ Chat response received from {platform.value}")
                return {
                    "success": True,
                    "content": response.content,
                    "platform": platform.value,
                    "response_time": response.response_time,
# BRACKET_SURGEON: disabled
#                 }
            else:
                print(f"❌ Chat request failed: {response.error}")
                return {
                    "success": False,
                    "error": response.error,
                    "platform": platform.value,
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            print(f"❌ Chat request exception: {e}")
            self._update_stats(platform, False)
            return {"success": False, "error": str(e), "platform": platform.value}

    async def multi_platform_comparison(
        self, prompt: str, platforms: List[WebAIPlatform] = None
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """"""
        Compare responses from multiple AI platforms

        Args:
            prompt: The prompt to send to all platforms
            platforms: List of platforms to test (default: ChatGPT, Gemini, Claude)

        Returns:
            Dictionary with responses from each platform
        """"""
        if platforms is None:
            platforms = [
                WebAIPlatform.CHATGPT,
                WebAIPlatform.GEMINI,
                WebAIPlatform.CLAUDE,
# BRACKET_SURGEON: disabled
#             ]

        print(f"🔄 Comparing responses across {len(platforms)} platforms...")

        messages = [{"role": "user", "content": prompt}]
        results = {}

        # Send requests to all platforms concurrently
        tasks = []
        for platform in platforms:
            task = self.chat_with_platform(messages, platform)
            tasks.append((platform, task))

        # Wait for all responses
        for platform, task in tasks:
            try:
                result = await task
                results[platform.value] = result
            except Exception as e:
                results[platform.value] = {
                    "success": False,
                    "error": str(e),
                    "platform": platform.value,
# BRACKET_SURGEON: disabled
#                 }

        return results

    async def generate_avatar_workflow(self, description: str, style: str = "realistic") -> Dict:
        """"""
        Complete avatar generation workflow

        Args:
            description: Description of the avatar to generate
            style: Style preference for the avatar

        Returns:
            Dictionary with workflow results
        """"""
        print(f"🎭 Starting avatar generation workflow...")

        workflow_results = {
            "description": description,
            "style": style,
            "steps": {},
            "final_prompt": None,
            "success": False,
# BRACKET_SURGEON: disabled
#         }

        try:
            # Step 1: Generate optimized prompt
            print("Step 1: Generating optimized prompt...")
            optimized_prompt = await self.generate_avatar_prompt(
                description, style, WebAIPlatform.CHATGPT
# BRACKET_SURGEON: disabled
#             )
            workflow_results["steps"]["prompt_generation"] = {
                "success": True,
                "prompt": optimized_prompt,
# BRACKET_SURGEON: disabled
#             }
            workflow_results["final_prompt"] = optimized_prompt

            # Step 2: Validate prompt with another platform
            print("Step 2: Validating prompt with Gemini...")
            validation_messages = [
                {
                    "role": "user",
                    "content": f"Rate this AI image generation prompt on a scale of 1 - 10 \"
#     and suggest improvements: {optimized_prompt}",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ]

            validation_response = await self.chat_with_platform(
                validation_messages, WebAIPlatform.GEMINI
# BRACKET_SURGEON: disabled
#             )

            workflow_results["steps"]["prompt_validation"] = validation_response

            # Step 3: Generate alternative prompts
            print("Step 3: Generating alternative prompts...")
            alternative_messages = [
                {
                    "role": "user",
                    "content": f"Create 2 alternative prompts for this avatar: {description} (style: {style}). Make them different but equally detailed.",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ]

            alternatives_response = await self.chat_with_platform(
                alternative_messages, WebAIPlatform.CLAUDE
# BRACKET_SURGEON: disabled
#             )

            workflow_results["steps"]["alternative_prompts"] = alternatives_response

            workflow_results["success"] = True
            print("✅ Avatar generation workflow completed successfully")

        except Exception as e:
            print(f"❌ Avatar workflow failed: {e}")
            workflow_results["error"] = str(e)

        return workflow_results

    def _update_stats(self, platform: WebAIPlatform, success: bool):
        """Update session statistics"""
        self.session_stats["total_requests"] += 1

        if success:
            self.session_stats["successful_requests"] += 1
        else:
            self.session_stats["failed_requests"] += 1

        platform_name = platform.value
        if platform_name not in self.session_stats["platform_usage"]:
            self.session_stats["platform_usage"][platform_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
# BRACKET_SURGEON: disabled
#             }

        self.session_stats["platform_usage"][platform_name]["requests"] += 1
        if success:
            self.session_stats["platform_usage"][platform_name]["successes"] += 1
        else:
            self.session_stats["platform_usage"][platform_name]["failures"] += 1

    async def get_session_analytics(self) -> Dict:
        """Get comprehensive session analytics"""
        session_duration = (datetime.now() - self.session_stats["session_start"]).total_seconds()

        analytics = {
            "session_duration_seconds": session_duration,
            "total_requests": self.session_stats["total_requests"],
            "success_rate": (
                self.session_stats["successful_requests"]
                / max(self.session_stats["total_requests"], 1)
# BRACKET_SURGEON: disabled
#             )
            * 100,
            "platform_usage": self.session_stats["platform_usage"],
            "requests_per_minute": (
                self.session_stats["total_requests"] / max(session_duration / 60, 1)
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

        # Add platform health checks
        health_checks = {}
        for platform in WebAIPlatform:
            try:
                # Quick health check (placeholder)
                health_checks[platform.value] = "healthy"
            except Exception:
                health_checks[platform.value] = "error"

        analytics["platform_health"] = health_checks

        return analytics

    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up web AI integration...")
        await self.puppeteer_service.cleanup_all_sessions()
        await self.web_ai_client.cleanup_sessions()


async def main():
    """Main demonstration function"""
    print("🚀 Web AI Integration Demo")
    print("=" * 50)

    # Initialize integration
    integration = WebAIIntegration()

    try:
        # Test 1: Health checks
        print("\\n📊 Health Checks")
        print("-" * 30)

        web_health = await integration.web_ai_client.health_check()
        print(f"Web AI Client: {json.dumps(web_health, indent = 2)}")

        puppeteer_health = await integration.puppeteer_service.health_check()
        print(f"Puppeteer Service: {json.dumps(puppeteer_health, indent = 2)}")

        mcp_health = await integration.mcp_client.health_check()
        print(f"MCP Client: {json.dumps(mcp_health, indent = 2)}")

        # Test 2: Simple chat completion
        print("\\n💬 Simple Chat Test")
        print("-" * 30)

        simple_messages = [{"role": "user", "content": "Hello! Can you help me create an avatar?"}]

        chat_result = await integration.chat_with_platform(simple_messages, WebAIPlatform.CHATGPT)
        print(f"Chat Result: {json.dumps(chat_result, indent = 2)}")

        # Test 3: Avatar generation workflow
        print("\\n🎭 Avatar Generation Workflow")
        print("-" * 30)

        avatar_result = await integration.generate_avatar_workflow(
            "A friendly robot with blue eyes and a warm smile", "cartoon"
# BRACKET_SURGEON: disabled
#         )
        print(f"Avatar Workflow: {json.dumps(avatar_result, indent = 2)}")

        # Test 4: Multi - platform comparison
        print("\\n🔄 Multi - Platform Comparison")
        print("-" * 30)

        comparison_result = await integration.multi_platform_comparison(
            "What makes a good avatar design?"
# BRACKET_SURGEON: disabled
#         )
        print(f"Platform Comparison: {json.dumps(comparison_result, indent = 2)}")

        # Test 5: Session analytics
        print("\\n📈 Session Analytics")
        print("-" * 30)

        analytics = await integration.get_session_analytics()
        print(f"Analytics: {json.dumps(analytics, indent = 2)}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

    finally:
        # Cleanup
        await integration.cleanup()
        print("\\n✅ Demo completed")


if __name__ == "__main__":
    asyncio.run(main())