#!/usr / bin / env python3
""""""
Production Initialization Module for TRAE.AI
Initializes all production services and agents
""""""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load production environment
load_dotenv(".env.production")

logger = logging.getLogger(__name__)


class ProductionManager:
    """Manages all production services and agents"""


    def __init__(self):
        self.services = {}
        self.agents = {}
        self.initialized = False
        self.startup_time = None


    async def initialize_all_services(self):
        """Initialize all production services"""
        logger.info("🚀 Starting TRAE.AI Production Services...")
        self.startup_time = datetime.now()

        try:
            # Initialize Content Agent
            logger.info("Initializing Content Agent...")
            await self._initialize_content_agent()

            # Initialize Specialized Agents
            logger.info("Initializing Specialized Agents...")
            await self._initialize_specialized_agents()

            # Initialize Avatar Services
            logger.info("Initializing Avatar Services...")
            await self._initialize_avatar_services()

            # Initialize TTS Engine
            logger.info("Initializing TTS Engine...")
            await self._initialize_tts_engine()

            # Initialize Video Generation
            logger.info("Initializing Video Generation...")
            await self._initialize_video_generation()

            # Initialize Revenue Tracking
            logger.info("Initializing Revenue Tracking...")
            await self._initialize_revenue_tracking()

            # Initialize Monitoring
            logger.info("Initializing Monitoring...")
            await self._initialize_monitoring()

            self.initialized = True
            logger.info("✅ All production services initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize production services: {e}")

            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise


    async def _initialize_content_agent(self):
        """Initialize the main content agent"""
        try:

            from content_agent.main import ContentAgent, ContentConfig

            config = ContentConfig()
            content_agent = ContentAgent(config)

            # Start the content agent server in background
            self.services["content_agent"] = content_agent
            logger.info("✅ Content Agent initialized")

        except Exception as e:
            logger.warning(f"⚠️ Content Agent initialization failed: {e}")
            self.services["content_agent"] = None


    async def _initialize_specialized_agents(self):
        """Initialize specialized agents"""
        try:

            from backend.agents.specialized_agents import \\

                ContentAgent as SpecializedContentAgent

            from backend.agents.specialized_agents import (FinancialAgent,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ResearchAgent, SystemAgent)

            # Initialize ContentAgent
            if os.getenv("CONTENT_AGENT_ENABLED", "true").lower() == "true":
                content_agent = SpecializedContentAgent()
                self.agents["content_agent"] = content_agent
                logger.info("✅ Specialized Content Agent initialized")

            # Initialize SystemAgent
            if os.getenv("SYSTEM_AGENT_ENABLED", "true").lower() == "true":
                system_agent = SystemAgent()
                self.agents["system_agent"] = system_agent
                logger.info("✅ System Agent initialized")

            # Initialize ResearchAgent
            if os.getenv("RESEARCH_AGENT_ENABLED", "true").lower() == "true":
                research_agent = ResearchAgent()
                self.agents["research_agent"] = research_agent
                logger.info("✅ Research Agent initialized")

            # Initialize FinancialAgent
            if os.getenv("FINANCIAL_AGENT_ENABLED", "true").lower() == "true":
                financial_agent = FinancialAgent()
                self.agents["financial_agent"] = financial_agent
                logger.info("✅ Financial Agent initialized")

            # Initialize Twitter Agents
            await self._initialize_twitter_agents()

        except Exception as e:
            logger.warning(f"⚠️ Specialized agents initialization failed: {e}")


    async def _initialize_twitter_agents(self):
        """Initialize Twitter - related agents"""
        try:
            # Initialize Twitter Integration
            if os.getenv("TWITTER_INTEGRATION_ENABLED", "true").lower() == "true":

                from backend.integrations.twitter_integration import TwitterIntegration

                twitter_integration = TwitterIntegration()

                # Test connection
                if twitter_integration.test_connection():
                    self.services["twitter_integration"] = twitter_integration
                    logger.info("✅ Twitter Integration initialized and connected")

                    # Initialize Twitter Engagement Agent
                    if (
                        os.getenv("TWITTER_ENGAGEMENT_ENABLED", "true").lower()
                        == "true"
# BRACKET_SURGEON: disabled
#                     ):

                        from backend.agents.twitter_engagement_agent import \\

                            TwitterEngagementAgent

                        engagement_agent = TwitterEngagementAgent()
                        self.agents["twitter_engagement"] = engagement_agent
                        logger.info("✅ Twitter Engagement Agent initialized")

                    # Initialize Twitter Promotion Agent
                    if os.getenv("TWITTER_PROMOTION_ENABLED", "true").lower() == "true":

                        from backend.agents.twitter_promotion_agent import \\

                            TwitterPromotionAgent

                        promotion_agent = TwitterPromotionAgent()
                        self.agents["twitter_promotion"] = promotion_agent
                        logger.info("✅ Twitter Promotion Agent initialized")
                else:
                    logger.warning(
                        "⚠️ Twitter Integration connection failed - agents not initialized"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        except Exception as e:
            logger.warning(f"⚠️ Twitter agents initialization failed: {e}")


    async def _initialize_avatar_services(self):
        """Initialize avatar generation services"""
        try:

            from backend.services.avatar_engines import AvatarEngineManager

            avatar_manager = AvatarEngineManager()
            await avatar_manager.initialize_all_engines()

            self.services["avatar_manager"] = avatar_manager
            logger.info("✅ Avatar services initialized")

        except Exception as e:
            logger.warning(f"⚠️ Avatar services initialization failed: {e}")
            self.services["avatar_manager"] = None


    async def _initialize_tts_engine(self):
        """Initialize TTS engine"""
        try:

            from backend.tts_engine import TTSEngine

            tts_engine = TTSEngine()
            self.services["tts_engine"] = tts_engine
            logger.info("✅ TTS Engine initialized")

        except Exception as e:
            logger.warning(f"⚠️ TTS Engine initialization failed: {e}")
            self.services["tts_engine"] = None


    async def _initialize_video_generation(self):
        """Initialize video generation services"""
        try:
            if os.getenv("VIDEO_GENERATION_ENABLED", "true").lower() == "true":

                from backend.content.ai_video_editor import AIVideoEditor
                    from backend.content.blender_compositor import BlenderCompositor

                video_editor = AIVideoEditor()
                blender_compositor = BlenderCompositor()

                self.services["video_editor"] = video_editor
                    self.services["blender_compositor"] = blender_compositor
                    logger.info("✅ Video generation services initialized")

        except Exception as e:
            logger.warning(f"⚠️ Video generation initialization failed: {e}")


    async def _initialize_revenue_tracking(self):
        """Initialize revenue tracking services"""
        try:
            if os.getenv("REVENUE_TRACKING_ENABLED", "true").lower() == "true":

                from revenue_tracker.main import RevenueTracker

                revenue_tracker = RevenueTracker()
                self.services["revenue_tracker"] = revenue_tracker
                logger.info("✅ Revenue tracking initialized")

        except Exception as e:
            logger.warning(f"⚠️ Revenue tracking initialization failed: {e}")


    async def _initialize_monitoring(self):
        """Initialize monitoring services"""
        try:
            if os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true":

                from backend.health_monitor import HealthMonitor

                health_monitor = HealthMonitor()
                self.services["health_monitor"] = health_monitor
                    logger.info("✅ Monitoring services initialized")

        except Exception as e:
            logger.warning(f"⚠️ Monitoring initialization failed: {e}")


    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.services.get(service_name)


    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get an agent by name"""
        return self.agents.get(agent_name)


    def get_status(self) -> Dict[str, Any]:
        """Get production status"""
        return {
            "initialized": self.initialized,
                "startup_time": (
                self.startup_time.isoformat() if self.startup_time else None
# BRACKET_SURGEON: disabled
#             ),
                "services": {
                name: service is not None for name, service in self.services.items()
# BRACKET_SURGEON: disabled
#             },
                "agents": {name: agent is not None for name,
    agent in self.agents.items()},
                "environment": os.getenv("ENVIRONMENT", "development"),
                "autonomous_mode": os.getenv("AUTONOMOUS_MODE", "false").lower() == "true",
# BRACKET_SURGEON: disabled
#                 }

# Global production manager instance
production_manager = ProductionManager()


async def initialize_production():
    """Initialize production services"""
    await production_manager.initialize_all_services()
    return production_manager


def initialize_production_sync():
    """Synchronous wrapper for production initialization"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, just return the manager
            logger.warning("Event loop already running, skipping async initialization")
            return production_manager
        else:
            return loop.run_until_complete(initialize_production())
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(initialize_production())


def get_production_manager() -> ProductionManager:
    """Get the global production manager"""
    return production_manager

if __name__ == "__main__":
    # For testing
    asyncio.run(initialize_production())