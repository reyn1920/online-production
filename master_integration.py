#!/usr/bin/env python3
"""
TRAE.AI Master Integration System

This module provides a unified integration layer that connects all discovered components
of the online production system while following zero-cost and no-delete rules.

Components Integrated:
- Backend Architecture (agents, orchestrator, content-agent)
- Frontend Components (dashboard, chat, diagnostics)
- Data Storage (SQLite databases, content management)
- Task Queue Management
- Content Generation Pipeline
- Monitoring and Analytics
- Authentication and Security

Author: TRAE.AI Integration System
Version: 1.0.0
Date: 2024
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core components
try:
    from app.auth import AuthManager
    from app.bridge_to_system import SystemBridge
    from app.dashboard_integration import DashboardIntegration
    from app.websocket_manager import WebSocketManager
    from backend.api_orchestrator import APIOrchestrator
    from backend.content_agent import AutomatedStudio
    from backend.core.database import DatabaseManager, get_db_connection
    from backend.specialized_agents import ContentAgent, ResearchAgent, SystemAgent
    from backend.task_queue_manager import TaskPriority, TaskQueueManager, TaskType
    from monitoring.error_tracker import ErrorTracker
    from monitoring.performance_monitor import PerformanceMonitor
except ImportError as e:
    logging.warning(f"Some components not available: {e}")
    # Continue with available components


@dataclass
class IntegrationConfig:
    """Configuration for the master integration system"""

    # Database configuration
    master_db_path: str = "data/trae_master.db"
    content_db_path: str = "data/content_management.db"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Component enablement flags
    enable_dashboard: bool = True
    enable_agents: bool = True
    enable_content_generation: bool = True
    enable_monitoring: bool = True
    enable_websockets: bool = True
    enable_auth: bool = True

    # Content generation settings
    content_output_dir: str = "outputs"
    content_templates_dir: str = "content/templates"

    # Monitoring settings
    log_level: str = "INFO"
    metrics_enabled: bool = True

    # Zero-cost compliance
    use_local_models: bool = True
    avoid_paid_apis: bool = True


class MasterIntegration:
    """
    Master integration system that orchestrates all components
    """

    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        self.logger = self._setup_logging()

        # Component instances
        self.db_manager: Optional[DatabaseManager] = None
        self.task_queue: Optional[TaskQueueManager] = None
        self.system_agent: Optional[SystemAgent] = None
        self.research_agent: Optional[ResearchAgent] = None
        self.content_agent: Optional[ContentAgent] = None
        self.automated_studio: Optional[AutomatedStudio] = None
        self.api_orchestrator: Optional[APIOrchestrator] = None
        self.system_bridge: Optional[SystemBridge] = None
        self.dashboard: Optional[DashboardIntegration] = None
        self.websocket_manager: Optional[WebSocketManager] = None
        self.auth_manager: Optional[AuthManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.error_tracker: Optional[ErrorTracker] = None

        # Integration state
        self.is_initialized = False
        self.running_components: Dict[str, bool] = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/master_integration.log"),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    async def initialize(self) -> bool:
        """
        Initialize all system components
        """
        try:
            self.logger.info("Starting master integration initialization...")

            # Ensure required directories exist
            self._ensure_directories()

            # Initialize database layer
            await self._initialize_database()

            # Initialize task queue system
            await self._initialize_task_queue()

            # Initialize agents
            if self.config.enable_agents:
                await self._initialize_agents()

            # Initialize content generation
            if self.config.enable_content_generation:
                await self._initialize_content_system()

            # Initialize API orchestrator
            await self._initialize_api_orchestrator()

            # Initialize authentication
            if self.config.enable_auth:
                await self._initialize_auth()

            # Initialize monitoring
            if self.config.enable_monitoring:
                await self._initialize_monitoring()

            # Initialize web components
            if self.config.enable_dashboard:
                await self._initialize_web_components()

            # Initialize WebSocket manager
            if self.config.enable_websockets:
                await self._initialize_websockets()

            self.is_initialized = True
            self.logger.info("Master integration initialization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            "data",
            "logs",
            "outputs",
            "outputs/audio",
            "outputs/videos",
            "outputs/pdfs",
            "content",
            "content/templates",
            "content/scripts",
            "content/images",
            "static",
            "app/templates",
            "monitoring",
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    async def _initialize_database(self):
        """Initialize database management"""
        try:
            self.db_manager = DatabaseManager(self.config.master_db_path)
            self.running_components["database"] = True
            self.logger.info("Database manager initialized")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    async def _initialize_task_queue(self):
        """Initialize task queue management"""
        try:
            self.task_queue = TaskQueueManager(self.config.master_db_path)
            self.running_components["task_queue"] = True
            self.logger.info("Task queue manager initialized")
        except Exception as e:
            self.logger.error(f"Task queue initialization failed: {e}")
            raise

    async def _initialize_agents(self):
        """Initialize specialized agents"""
        try:
            # Initialize system agent
            self.system_agent = SystemAgent()

            # Initialize research agent
            self.research_agent = ResearchAgent()

            # Initialize content agent
            self.content_agent = ContentAgent()

            self.running_components["agents"] = True
            self.logger.info("Specialized agents initialized")
        except Exception as e:
            self.logger.error(f"Agents initialization failed: {e}")
            # Continue without agents if they fail

    async def _initialize_content_system(self):
        """Initialize content generation system"""
        try:
            self.automated_studio = AutomatedStudio()
            self.running_components["content_generation"] = True
            self.logger.info("Content generation system initialized")
        except Exception as e:
            self.logger.error(f"Content system initialization failed: {e}")
            # Continue without content generation if it fails

    async def _initialize_api_orchestrator(self):
        """Initialize API orchestration"""
        try:
            self.api_orchestrator = APIOrchestrator()
            self.running_components["api_orchestrator"] = True
            self.logger.info("API orchestrator initialized")
        except Exception as e:
            self.logger.error(f"API orchestrator initialization failed: {e}")
            # Continue without API orchestrator if it fails

    async def _initialize_auth(self):
        """Initialize authentication system"""
        try:
            self.auth_manager = AuthManager()
            self.running_components["auth"] = True
            self.logger.info("Authentication system initialized")
        except Exception as e:
            self.logger.error(f"Authentication initialization failed: {e}")
            # Continue without auth if it fails

    async def _initialize_monitoring(self):
        """Initialize monitoring systems"""
        try:
            self.performance_monitor = PerformanceMonitor()
            self.error_tracker = ErrorTracker()
            self.running_components["monitoring"] = True
            self.logger.info("Monitoring systems initialized")
        except Exception as e:
            self.logger.error(f"Monitoring initialization failed: {e}")
            # Continue without monitoring if it fails

    async def _initialize_web_components(self):
        """Initialize web dashboard and bridge"""
        try:
            self.system_bridge = SystemBridge()
            self.dashboard = DashboardIntegration()
            self.running_components["web_components"] = True
            self.logger.info("Web components initialized")
        except Exception as e:
            self.logger.error(f"Web components initialization failed: {e}")
            # Continue without web components if they fail

    async def _initialize_websockets(self):
        """Initialize WebSocket management"""
        try:
            self.websocket_manager = WebSocketManager()
            self.running_components["websockets"] = True
            self.logger.info("WebSocket manager initialized")
        except Exception as e:
            self.logger.error(f"WebSocket initialization failed: {e}")
            # Continue without WebSockets if they fail

    async def start_services(self):
        """Start all integrated services"""
        if not self.is_initialized:
            raise RuntimeError("System must be initialized before starting services")

        self.logger.info("Starting integrated services...")

        # Start task queue processing
        if self.task_queue and "task_queue" in self.running_components:
            # Task queue manager handles its own background processing
            pass

        # Start monitoring services
        if self.performance_monitor and "monitoring" in self.running_components:
            # Performance monitor runs in background
            pass

        # Start WebSocket manager
        if self.websocket_manager and "websockets" in self.running_components:
            # WebSocket manager integrates with web framework
            pass

        self.logger.info("All services started successfully")

    async def create_content_pipeline_task(
        self, content_type: str, parameters: Dict[str, Any]
    ) -> str:
        """Create a content generation pipeline task"""
        if not self.task_queue:
            raise RuntimeError("Task queue not initialized")

        task_id = await self.task_queue.add_task(
            task_type=TaskType.CONTENT,
            payload={
                "content_type": content_type,
                "parameters": parameters,
                "output_dir": self.config.content_output_dir,
            },
            priority=TaskPriority.MEDIUM,
        )

        self.logger.info(f"Created content pipeline task: {task_id}")
        return task_id

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "initialized": self.is_initialized,
            "components": self.running_components.copy(),
            "timestamp": datetime.now().isoformat(),
        }

        # Add component-specific status
        if self.task_queue:
            try:
                # Get task queue metrics if available
                status["task_queue_stats"] = {
                    "pending_tasks": len(await self.task_queue.get_pending_tasks()),
                    "total_tasks": "N/A",  # Would need additional method
                }
            except Exception as e:
                status["task_queue_stats"] = {"error": str(e)}

        if self.db_manager:
            try:
                # Test database connection
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    )
                    table_count = cursor.fetchone()[0]
                    status["database_stats"] = {"table_count": table_count}
            except Exception as e:
                status["database_stats"] = {"error": str(e)}

        return status

    async def shutdown(self):
        """Gracefully shutdown all components"""
        self.logger.info("Starting graceful shutdown...")

        # Shutdown components in reverse order
        if self.websocket_manager:
            try:
                # WebSocket manager cleanup if needed
                pass
            except Exception as e:
                self.logger.error(f"WebSocket manager shutdown error: {e}")

        if self.performance_monitor:
            try:
                # Performance monitor cleanup if needed
                pass
            except Exception as e:
                self.logger.error(f"Performance monitor shutdown error: {e}")

        if self.task_queue:
            try:
                # Task queue cleanup if needed
                pass
            except Exception as e:
                self.logger.error(f"Task queue shutdown error: {e}")

        self.logger.info("Graceful shutdown completed")


# Global integration instance
_master_integration: Optional[MasterIntegration] = None


def get_master_integration(
    config: Optional[IntegrationConfig] = None,
) -> MasterIntegration:
    """Get or create the master integration instance"""
    global _master_integration
    if _master_integration is None:
        _master_integration = MasterIntegration(config)
    return _master_integration


async def main():
    """Main entry point for the integrated system"""
    config = IntegrationConfig()
    integration = get_master_integration(config)

    try:
        # Initialize the system
        success = await integration.initialize()
        if not success:
            print("Failed to initialize the system")
            return 1

        # Start services
        await integration.start_services()

        # Print system status
        status = await integration.get_system_status()
        print("System Status:")
        print(json.dumps(status, indent=2))

        print("\nMaster integration system is running...")
        print("Press Ctrl+C to shutdown")

        # Keep the system running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutdown requested...")

    except Exception as e:
        print(f"System error: {e}")
        return 1
    finally:
        await integration.shutdown()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
