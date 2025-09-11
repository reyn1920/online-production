#!/usr / bin / env python3
"""
News Monitoring Service Startup Script

This script starts the news - driven content trigger service that continuously
monitors political RSS feeds and automatically triggers Right Perspective video
content creation.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.logger import get_logger

from news_driven_content_trigger import NewsDrivenContentTrigger

logger = get_logger(__name__)


class NewsMonitoringService:
    """Service wrapper for news - driven content triggering."""


    def __init__(self):
        self.trigger_service = None
        self.running = False


    async def start(self):
        """Start the news monitoring service."""
        try:
            logger.info("Starting News Monitoring Service...")

            # Initialize the trigger service
            self.trigger_service = NewsDrivenContentTrigger()
            self.running = True

            logger.info("News Monitoring Service started successfully")
            logger.info("Monitoring political RSS feeds for content opportunities...")

            # Start continuous monitoring
            await self.trigger_service.run_continuous_monitoring()

        except Exception as e:
            logger.error(f"Error starting News Monitoring Service: {e}")
            sys.exit(1)


    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()


    def stop(self):
        """Stop the news monitoring service."""
        if self.running:
            logger.info("Stopping News Monitoring Service...")
            self.running = False
            if self.trigger_service:
                self.trigger_service.stop_monitoring()
            logger.info("News Monitoring Service stopped")


    async def status(self):
        """Get service status and recent activity."""
        if not self.trigger_service:
            return {"status": "not_running", "message": "Service not initialized"}

        try:
            pending_triggers = self.trigger_service.get_pending_triggers()

            return {
                "status": "running" if self.running else "stopped",
                    "pending_triggers": len(pending_triggers),
                    "recent_triggers": pending_triggers[:5],  # Show last 5 triggers
                "monitoring_interval": self.trigger_service.monitoring_interval,
                    "urgency_threshold": self.trigger_service.urgency_threshold,
                    }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"status": "error", "message": str(e)}


async def main():
    """Main entry point for the news monitoring service."""
    service = NewsMonitoringService()

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        service.stop()
        logger.info("News Monitoring Service shutdown complete")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level = logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
            logging.FileHandler("logs / news_monitoring.log"),
                logging.StreamHandler(sys.stdout),
                ],
            )

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok = True)

    logger.info("=" * 60)
    logger.info("NEWS MONITORING SERVICE - RIGHT PERSPECTIVE")
    logger.info("=" * 60)

    # Run the service
    asyncio.run(main())
