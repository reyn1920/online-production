#!/usr/bin/env python3
"""
TRAEAI Live System Launcher

This script launches the complete TRAEAI autonomous system including:
- Autonomous orchestrator with all agents
- Web dashboard for monitoring and control
- All backend services and integrations

Usage:
    python start_live_system.py

Author: TRAEAI Development Team
Version: 2.0.0 (Live Production)
"""

import asyncio
import os
import signal
import sys
import threading

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger
from launch_live import AutonomousOrchestrator, set_orchestrator_instance
from simple_dashboard import SimpleDashboard

# Initialize logger
logger = get_logger(__name__)


class LiveSystemLauncher:
    """Unified launcher for the complete TRAEAI live system."""

    def __init__(self):
        self.orchestrator = None
        self.dashboard_app = None
        self.dashboard_thread = None
        self.orchestrator_task = None
        self.shutdown_event = threading.Event()

    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_dashboard(self):
        """Start the dashboard in a separate thread."""

        def run_dashboard():
            try:
                self.dashboard_app = SimpleDashboard(
                    host="0.0.0.0", port=8082  # Use different port to avoid conflicts
                )

                logger.info("Starting TRAEAI Dashboard on http://0.0.0.0:8082")
                self.dashboard_app.run()

            except Exception as e:
                logger.error(f"Dashboard failed to start: {e}")
                self.shutdown_event.set()

        self.dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        self.dashboard_thread.start()

    async def start_orchestrator(self):
        """Start the autonomous orchestrator."""
        try:
            logger.info("Initializing TRAEAI Autonomous Orchestrator...")
            self.orchestrator = AutonomousOrchestrator()

            # Set global orchestrator instance for other modules
            set_orchestrator_instance(self.orchestrator)

            logger.info("Starting autonomous operations...")
            await self.orchestrator.start_autonomous_operations()

        except Exception as e:
            logger.error(f"Orchestrator failed to start: {e}")
            self.shutdown_event.set()

    async def monitor_system(self):
        """Monitor system health and handle shutdown."""
        while not self.shutdown_event.is_set():
            try:
                # Check if dashboard thread is still alive
                if self.dashboard_thread and not self.dashboard_thread.is_alive():
                    logger.error("Dashboard thread died, initiating shutdown")
                    self.shutdown_event.set()
                    break

                # Sleep for a short interval
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Gracefully shutdown all components."""
        logger.info("Shutting down TRAEAI Live System...")

        # Shutdown orchestrator
        if self.orchestrator:
            try:
                await self.orchestrator.shutdown()
                logger.info("Orchestrator shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down orchestrator: {e}")

        # Shutdown dashboard
        if self.dashboard_app:
            try:
                # Dashboard shutdown is handled by the thread termination
                logger.info("Dashboard shutdown initiated")
            except Exception as e:
                logger.error(f"Error shutting down dashboard: {e}")

        logger.info("TRAEAI Live System shutdown complete")

    async def run(self):
        """Main run loop for the live system."""
        try:
            logger.info("=" * 60)
            logger.info("TRAEAI LIVE SYSTEM STARTING")
            logger.info("=" * 60)

            # Setup signal handlers for graceful shutdown
            self.setup_signal_handlers()

            # Start dashboard service
            logger.info("Starting dashboard service...")
            self.start_dashboard()

            # Give dashboard time to start
            await asyncio.sleep(3)

            # Start orchestrator
            logger.info("Starting autonomous orchestrator...")

            # Create tasks for orchestrator and monitoring
            orchestrator_task = asyncio.create_task(self.start_orchestrator())
            monitor_task = asyncio.create_task(self.monitor_system())

            # Wait for monitoring to complete (shutdown signal)
            await monitor_task

            # Cancel orchestrator task if still running
            if not orchestrator_task.done():
                orchestrator_task.cancel()
                try:
                    await orchestrator_task
                except asyncio.CancelledError:
                    pass

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.shutdown()


def main():
    """Main entry point."""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Error: Python 3.8 or higher is required")
            sys.exit(1)

        # Create and run the launcher
        launcher = LiveSystemLauncher()

        # Run the async main loop
        asyncio.run(launcher.run())

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
