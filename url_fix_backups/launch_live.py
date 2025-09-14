#!/usr / bin / env python3
"""
TRAE.AI Master Orchestrator - Live Production Launch System

This is the master orchestrator that initializes and manages all TRAE.AI agents,
systems, and services in a coordinated, production - ready environment.

Features:
- Complete agent lifecycle management
- Real - time monitoring and health checks
- Graceful shutdown and error recovery
- Integration with unified dashboard
- Autonomous task distribution and execution
"""

import asyncio
import logging
import os
import queue
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Quiet chatty framework loggers if enabled
try:

    from backend.logging_tune import tune_chatty_loggers

    tune_chatty_loggers()
except Exception:
    pass

# Load environment variables from .env files
try:

    from dotenv import load_dotenv

    load_dotenv(".env.local")
    load_dotenv(".env")
except ImportError:
    # If python - dotenv is not available, continue without it
    pass

# Configure logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
)
logger = logging.getLogger("trae_ai.orchestrator")

# IDE Probe Filter to reduce log noise


class IDEProbeFilter(logging.Filter):


    def filter(self, record):
        # Suppress log lines for IDE webview probes

# Apply to werkzeug / flask request logger
logging.getLogger("werkzeug").addFilter(IDEProbeFilter())

# This global instance is the bridge between the orchestrator and dashboard
_global_orchestrator = None
_shutdown_event = threading.Event()


def get_orchestrator_instance():
    """Get the global orchestrator instance for dashboard integration."""
    return _global_orchestrator


def set_orchestrator_instance(orchestrator):
    """Set the global orchestrator instance."""
    global _global_orchestrator
    _global_orchestrator = orchestrator

# Import components after the bridge is defined
# Import components with individual error handling
DashboardApp = None
TaskQueueManager = None
SystemAgent = None
ContentEvolutionAgent = None
MarketingAgent = None
ResearchAgent = None
FinancialAgent = None
SelfRepairAgent = None
SecretStore = None
NewsMonitoringService = None
YouTubeEngagementAgent = None
ProgressiveSelfRepairAgent = None
ProactiveNicheDominationAgent = None
EvolutionAgent = None
BreakingNewsWatcher = None
CompetitorAnalyzer = None

# Deferred imports - these will be imported after migration


def _import_dashboard():
    global DashboardApp
    try:

        from app.dashboard import DashboardApp

        return DashboardApp
    except ImportError as e:
        logger.warning(f"DashboardApp not available: {e}")
        return None


def _import_task_queue():
    global TaskQueueManager
    try:

        from backend.task_queue_manager import TaskQueueManager

    except ImportError as e:
        logger.warning(f"TaskQueueManager not available: {e}")

# Import Phase 1 - 4 specialized agents
try:

    from backend.agents.base_agents import AgentCapability, AgentStatus
    from backend.agents.specialized_agents import (ContentAgent, MarketingAgent,

        ResearchAgent, SystemAgent)
except ImportError as e:
    logger.warning(f"Specialized agents not available: {e}")
    SystemAgent = None
    ResearchAgent = None
    ContentAgent = None
    MarketingAgent = None

# Import extracted agents
try:

    from backend.agents.financial_agent import FinancialAgent

except ImportError as e:
    logger.warning(f"FinancialAgent not available: {e}")
    FinancialAgent = None

try:

    from backend.agents.youtube_engagement_agent import YouTubeEngagementAgent

except ImportError as e:
    logger.warning(f"YouTubeEngagementAgent not available: {e}")
    YouTubeEngagementAgent = None

try:

    from backend.agents.self_repair_agent import ProgressiveSelfRepairAgent

except ImportError as e:
    logger.warning(f"ProgressiveSelfRepairAgent not available: {e}")
    ProgressiveSelfRepairAgent = None

try:

    from backend.agents.niche_domination_agent import ProactiveNicheDominationAgent

except ImportError as e:
    logger.warning(f"ProactiveNicheDominationAgent not available: {e}")
    ProactiveNicheDominationAgent = None

try:

    from backend.agents.evolution_agent import EvolutionAgent

except ImportError as e:
    logger.warning(f"EvolutionAgent not available: {e}")
    EvolutionAgent = None

try:

    from backend.agents.research_tools import BreakingNewsWatcher, CompetitorAnalyzer

except ImportError as e:
    logger.warning(f"Research tools not available: {e}")
    BreakingNewsWatcher = None
    CompetitorAnalyzer = None

# Import Phase 1 - 4 system components
try:

    from breaking_news_watcher import RSSIntelligenceEngine

except ImportError as e:
    logger.warning(f"RSS Intelligence Engine not available: {e}")
    RSSIntelligenceEngine = None

try:

    from backend.engines.hypocrisy_engine import HypocrisyEngine

except ImportError as e:
    logger.warning(f"Hypocrisy Engine not available: {e}")
    HypocrisyEngine = None

try:

    from backend.ecommerce_marketing_layer import EcommerceMarketingLayer

except ImportError as e:
    logger.warning(f"Ecommerce Marketing Layer not available: {e}")
    EcommerceMarketingLayer = None

try:

    from backend.integrations.research_validation_service import \\

        ResearchValidationService
except ImportError as e:
    logger.warning(f"Research Validation Service not available: {e}")
    ResearchValidationService = None

try:

    from backend.secret_store import SecretStore

except ImportError as e:
    logger.warning(f"SecretStore not available: {e}")

try:

    from utils.logging_config import setup_logging

except ImportError as e:
    logger.warning(f"Custom logging config not available: {e}")

try:

    from start_news_monitoring import NewsMonitoringService

except ImportError as e:
    logger.warning(f"NewsMonitoringService not available: {e}")

try:

    from backend.database_setup import run_database_migration, verify_database_schema

except ImportError as e:
    logger.warning(f"Database setup module not available: {e}")
    run_database_migration = None
    verify_database_schema = None


class AutonomousOrchestrator:
    """Master orchestrator for all TRAE.AI agents and systems."""


    def __init__(self, main_loop = None):
        """Initialize the master orchestrator with all agents and systems."""
        self.agent_states = {}
        self.agent_threads = {}
        self.agent_state_lock = threading.RLock()  # Use RLock for nested locking
        self.running = True
        self.start_time = datetime.now()
        self.health_check_interval = 30  # seconds
        self.news_monitoring_service = None
        self.shutdown_event = threading.Event()
        self.thread_pool = ThreadPoolExecutor(
            max_workers = 10, thread_name_prefix="TRAE - Agent"
        )
        self.main_loop = main_loop  # Store the main event loop for agent threads

        logger.info("🚀 Initializing TRAE.AI Master Orchestrator...")

        # Initialize core systems
        self._initialize_core_systems()

        # Initialize system components
        self._initialize_system_components()

        # Initialize all agents
        self._initialize_agents()

        # Initialize news monitoring service
        self._initialize_news_monitoring()

        # Start health monitoring
        self._start_health_monitor()

        logger.info("✅ Master Orchestrator initialization complete")


    def _initialize_core_systems(self):
        """Initialize core systems like task queue, secret store, etc."""
        try:
            # Initialize SecretStore
            if SecretStore:
                self.secret_store = SecretStore()
                logger.info("SecretStore initialized")
            else:
                self.secret_store = None
                logger.warning("SecretStore not available")

            # Initialize TaskQueueManager
            if TaskQueueManager:
                self.task_queue = TaskQueueManager()
                logger.info("TaskQueueManager initialized")
            else:
                self.task_queue = None
                logger.warning("TaskQueueManager not available")

        except Exception as e:
            logger.error(f"Error initializing core systems: {e}")
            self.secret_store = None
            self.task_queue = None


    def _initialize_system_components(self):
        """Initialize Phase 1 - 4 system components."""
        logger.info("Initializing system components...")

        # Initialize RSS Intelligence Engine
        if RSSIntelligenceEngine:
            try:
                self.rss_engine = RSSIntelligenceEngine()
                logger.info("✓ RSS Intelligence Engine initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize RSS Intelligence Engine: {e}")
                self.rss_engine = None

        # Initialize Hypocrisy Engine
        if HypocrisyEngine:
            try:
                self.hypocrisy_engine = HypocrisyEngine()
                logger.info("✓ Hypocrisy Engine initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Hypocrisy Engine: {e}")
                self.hypocrisy_engine = None

        # Initialize Ecommerce Marketing Layer
        if EcommerceMarketingLayer:
            try:
                self.ecommerce_layer = EcommerceMarketingLayer()
                logger.info("✓ Ecommerce Marketing Layer initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Ecommerce Marketing Layer: {e}")
                self.ecommerce_layer = None

        # Initialize Research Validation Service
        if ResearchValidationService:
            try:
                self.research_validation = ResearchValidationService()
                logger.info("✓ Research Validation Service initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Research Validation Service: {e}")
                self.research_validation = None


    def _initialize_agents(self):
        """Initialize all Phase 1 - 4 specialized agents."""
        self.agents = {}
        logger.info("Initializing agents...")

        # System Agent
        if SystemAgent:
            try:
                agent = SystemAgent(
                    agent_id="system_agent",
                        name="System Management Agent",
                        main_loop = self.main_loop,
                        )
                self.agents["SystemAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 1,
                            "description": "System monitoring and management",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("SystemAgent", "initialized")
                logger.info(
                    "✅ SystemAgent initialized: System monitoring and management"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize SystemAgent: {e}")
                self.update_agent_status("SystemAgent", "error", error = str(e))

        # Research Agent
        if ResearchAgent:
            try:
                agent = ResearchAgent(
                    agent_id="research_agent", name="Research & Intelligence Agent"
                )
                self.agents["ResearchAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 2,
                            "description": "Research and intelligence gathering",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("ResearchAgent", "initialized")
                logger.info(
                    "✅ ResearchAgent initialized: Research and intelligence gathering"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize ResearchAgent: {e}")
                self.update_agent_status("ResearchAgent", "error", error = str(e))

        # Content Agent
        if ContentAgent:
            try:
                agent = ContentAgent(
                    agent_id="content_agent", name="Content Creation Agent"
                )
                self.agents["ContentAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 3,
                            "description": "Content creation and evolution",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("ContentAgent", "initialized")
                logger.info(
                    "✅ ContentAgent initialized: Content creation and evolution"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize ContentAgent: {e}")
                self.update_agent_status("ContentAgent", "error", error = str(e))

        # Marketing Agent
        if MarketingAgent:
            try:
                agent = MarketingAgent(
                    agent_id="marketing_agent", name="Marketing & Promotion Agent"
                )
                self.agents["MarketingAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 4,
                            "description": "Marketing automation and strategy",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("MarketingAgent", "initialized")
                logger.info(
                    "✅ MarketingAgent initialized: Marketing automation and strategy"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize MarketingAgent: {e}")
                self.update_agent_status("MarketingAgent", "error", error = str(e))

        # Financial Agent
        if FinancialAgent:
            try:
                agent = FinancialAgent(
                    agent_id="financial_agent", name="Financial Management Agent"
                )
                self.agents["FinancialAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 5,
                            "description": "Financial analysis and trading automation",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("FinancialAgent", "initialized")
                logger.info(
                    "✅ FinancialAgent initialized: Financial analysis \
    and trading automation"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize FinancialAgent: {e}")
                self.update_agent_status("FinancialAgent", "error", error = str(e))

        # YouTube Engagement Agent
        if YouTubeEngagementAgent:
            try:
                agent = YouTubeEngagementAgent(db_path="data / youtube_engagement.sqlite")
                self.agents["YouTubeEngagementAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 6,
                            "description": "YouTube content engagement \
    and optimization",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("YouTubeEngagementAgent", "initialized")
                logger.info(
                    "✅ YouTubeEngagementAgent initialized: YouTube content engagement \
    and optimization"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize YouTubeEngagementAgent: {e}")
                self.update_agent_status(
                    "YouTubeEngagementAgent", "error", error = str(e)
                )

        # Progressive Self Repair Agent
        if ProgressiveSelfRepairAgent:
            try:
                agent = ProgressiveSelfRepairAgent(
                    config={
                        "agent_id": "progressive_self_repair_agent",
                            "name": "Self Repair Agent",
                            }
                )
                self.agents["ProgressiveSelfRepairAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 7,
                            "description": "System self - repair and optimization",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("ProgressiveSelfRepairAgent", "initialized")
                logger.info(
                    "✅ ProgressiveSelfRepairAgent initialized: System self - repair \
    and optimization"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize ProgressiveSelfRepairAgent: {e}")
                self.update_agent_status(
                    "ProgressiveSelfRepairAgent", "error", error = str(e)
                )

        # Proactive Niche Domination Agent
        if ProactiveNicheDominationAgent:
            try:
                agent = ProactiveNicheDominationAgent(
                    agent_id="proactive_niche_domination_agent",
                        name="Niche Domination Agent",
                        )
                self.agents["ProactiveNicheDominationAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 8,
                            "description": "Market niche identification and domination",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("ProactiveNicheDominationAgent", "initialized")
                logger.info(
                    "✅ ProactiveNicheDominationAgent initialized: Market niche identification \
    and domination"
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to initialize ProactiveNicheDominationAgent: {e}"
                )
                self.update_agent_status(
                    "ProactiveNicheDominationAgent", "error", error = str(e)
                )

        # Evolution Agent
        if EvolutionAgent:
            try:
                agent = EvolutionAgent(
                    agent_id="evolution_agent", name="Evolution Agent"
                )
                self.agents["EvolutionAgent"] = {
                    "instance": agent,
                        "config": {
                        "enabled": True,
                            "priority": 9,
                            "description": "Continuous system evolution and adaptation",
                            },
                        "status": "initialized",
                        "last_heartbeat": datetime.now(),
                        "task_count": 0,
                        "error_count": 0,
                        }
                self.update_agent_status("EvolutionAgent", "initialized")
                logger.info(
                    "✅ EvolutionAgent initialized: Continuous system evolution \
    and adaptation"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize EvolutionAgent: {e}")
                self.update_agent_status("EvolutionAgent", "error", error = str(e))

        logger.info(f"Initialized {len(self.agents)} available agent configurations")
        if len(self.agents) == 0:
            logger.warning("No agents available - running in minimal mode")


    def _initialize_news_monitoring(self):
        """Initialize the news monitoring service for Right Perspective content triggers."""
        if NewsMonitoringService:
            try:
                logger.info("📰 Initializing News Monitoring Service...")
                self.news_monitoring_service = NewsMonitoringService()
                logger.info(
                    "✅ News Monitoring Service initialized: Political RSS feed monitoring for Right Perspective"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize News Monitoring Service: {e}")
                self.news_monitoring_service = None
        else:
            logger.warning("⚠️  News Monitoring Service not available")


    def update_agent_status(
        self,
            agent_name: str,
            status: str,
            task_id: Optional[str] = None,
            error: Optional[str] = None,
            ):
        """Update agent status with thread safety."""
        with self.agent_state_lock:
            self.agent_states[agent_name] = {
                "status": status,
                    "task_id": task_id,
                    "error": error,
                    "timestamp": datetime.now(),
                    "uptime": (datetime.now() - self.start_time).total_seconds(),
                    }

            # Update agent heartbeat
            if agent_name in self.agents:
                self.agents[agent_name]["last_heartbeat"] = datetime.now()
                if status == "error":
                    self.agents[agent_name]["error_count"] += 1


    def get_agent_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current status of agents."""
        with self.agent_state_lock:
            if agent_name:
                return self.agent_states.get(agent_name, {})
            return dict(self.agent_states)


    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""

        import psutil

        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "uptime": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
                "uptime_seconds": uptime,
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(interval = 1),
                "disk_usage": psutil.disk_usage("/").percent,
                "active_agents": len(
                [
                    a
                    for a in self.agent_states.values()
                    if a.get("status") not in ["error", "stopped"]
                ]
            ),
                "total_agents": len(self.agents),
                "database_health": self._check_database_health(),
                "task_queue_size": self._get_task_queue_size(),
                "start_time": self.start_time.isoformat(),
                }


    def _check_database_health(self) -> bool:
        """Check database connectivity and health."""
        try:
            if self.task_queue and hasattr(self.task_queue, "db_manager"):
                # Perform a simple database query
                return self.task_queue.db_manager.test_connection()
            return True  # Assume healthy if no database
        except Exception:
            return False


    def _get_task_queue_size(self) -> int:
        """Get current task queue size."""
        try:
            if self.task_queue:
                return self.task_queue.get_queue_size()
            return 0
        except Exception:
            return 0


    async def _run_agent_loop(self, agent_name: str):
        """Main execution loop for an agent with proper shutdown handling."""
        logger.info(f"🔄 Starting agent loop: {agent_name}")
        agent_info = self.agents.get(agent_name)

        if not agent_info:
            logger.error(f"❌ Agent {agent_name} not found")
            return

        agent = agent_info["instance"]

        while self.running and not self.shutdown_event.is_set():
            try:
                # Check for shutdown every iteration
                if self.shutdown_event.wait(timeout = 0.1):
                    break

                with self.agent_state_lock:
                    self.update_agent_status(agent_name, "active")

                # Check for tasks in the queue
                if self.task_queue:
                    task = await self._get_next_task_for_agent(agent_name)
                    if task:
                        logger.info(
                            f"📋 {agent_name} processing task: {task.get('id', 'unknown')}"
                        )
                        with self.agent_state_lock:
                            self.update_agent_status(
                                agent_name, "processing", task_id = task.get("id")
                            )

                        # Process the task with timeout and defensive programming
                        try:
                            if hasattr(agent, "process_task") and callable(
                                getattr(agent, "process_task", None)
                            ):
                                await asyncio.wait_for(
                                    agent.process_task(task), timeout = 60.0
                                )
                            elif hasattr(agent, "execute") and callable(
                                getattr(agent, "execute", None)
                            ):
                                await asyncio.wait_for(
                                    agent.execute(task), timeout = 60.0
                                )
                            else:
                                logger.warning(
                                    f"⚠️  Agent {agent_name} has no callable process_task \
    or execute method"
                                )
                        except asyncio.TimeoutError:
                            logger.warning(f"⏰ Task timeout for agent {agent_name}")
                        except Exception as e:
                            logger.error(
                                f"❌ Task processing error for {agent_name}: {e}"
                            )

                        agent_info["task_count"] += 1
                        logger.info(
                            f"✅ {agent_name} completed task: {task.get('id', 'unknown')}"
                        )

                # Agent - specific autonomous operations with defensive programming
                if hasattr(agent, "autonomous_cycle") and callable(
                    getattr(agent, "autonomous_cycle", None)
                ):
                    try:
                        await asyncio.wait_for(agent.autonomous_cycle(), timeout = 30.0)
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"⏰ Autonomous cycle timeout for agent {agent_name}"
                        )
                    except Exception as e:
                        logger.error(f"❌ Autonomous cycle error for {agent_name}: {e}")

                with self.agent_state_lock:
                    self.update_agent_status(agent_name, "idle")

                # Use shutdown event for interruptible sleep
                if self.shutdown_event.wait(timeout = 10.0):
                    break

            except Exception as e:
                logger.error(f"❌ Error in {agent_name} loop: {e}")
                with self.agent_state_lock:
                    self.update_agent_status(agent_name, "error", error = str(e))

                # Wait before retrying, but allow interruption
                if self.shutdown_event.wait(timeout = 30.0):
                    break

        logger.info(f"🛑 Agent loop stopped: {agent_name}")


    async def _get_next_task_for_agent(
        self, agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get the next appropriate task for the specified agent."""
        if not self.task_queue:
            return None

        try:
            # Get tasks suitable for this agent type
            return await self.task_queue.get_task_for_agent(agent_name)
        except Exception as e:
            logger.error(f"Error getting task for {agent_name}: {e}")
            return None


    def _run_agent_thread(self, agent_name: str):
        """Run agent loop in a separate thread with proper error handling."""
        try:
            # Use the main event loop if available, otherwise create a new one
            if self.main_loop and not self.main_loop.is_closed():
                # Submit the coroutine to the main event loop from this thread
                future = asyncio.run_coroutine_threadsafe(
                    self._run_agent_loop(agent_name), self.main_loop
                )
                future.result()  # Wait for completion
            else:
                # Fallback: create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._run_agent_loop(agent_name))
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"❌ Agent {agent_name} thread crashed: {e}")
            with self.agent_state_lock:
                self.update_agent_status(agent_name, "error", error = str(e))


    def start_agent_threads(self):
        """Start threads for all enabled agents using thread pool."""
        logger.info("🧵 Starting agent threads...")

        futures = {}
        for agent_name, agent_info in self.agents.items():
            if agent_info["config"]["enabled"] and not self.shutdown_event.is_set():
                future = self.thread_pool.submit(self._run_agent_thread, agent_name)
                futures[agent_name] = future
                self.agent_threads[agent_name] = future
                self.update_agent_status(agent_name, "running")
                logger.info(f"✅ Started thread for {agent_name}")

        logger.info(f"🎯 Started {len(futures)} agent threads")
        return futures


    def _start_health_monitor(self):
        """Start the health monitoring thread."""


        def health_monitor():
            while self.running:
                try:
                    self._perform_health_checks()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
                    time.sleep(60)  # Wait longer on error

        health_thread = threading.Thread(
            target = health_monitor, name="HealthMonitor", daemon = True
        )
        health_thread.start()
        logger.info("💓 Health monitor started")


    def _perform_health_checks(self):
        """Perform comprehensive health checks."""
        current_time = datetime.now()

        # Check agent heartbeats with defensive programming
        try:
            for agent_name, agent_info in self.agents.items():
                try:
                    last_heartbeat = agent_info.get("last_heartbeat")
                    if last_heartbeat:
                        time_since_heartbeat = (
                            current_time - last_heartbeat
                        ).total_seconds()
                        if time_since_heartbeat > 120:  # 2 minutes
                            logger.warning(
                                f"⚠️  {agent_name} heartbeat timeout ({time_since_heartbeat:.1f}s)"
                            )
                            self.update_agent_status(agent_name, "timeout")
                except Exception as e:
                    logger.error(f"Error checking heartbeat for {agent_name}: {e}")
        except Exception as e:
            logger.error(f"Error during agent heartbeat checks: {e}")

        # Check system resources
        try:

            import psutil

            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 90:
                logger.warning(f"⚠️  High memory usage: {memory_usage:.1f}%")

            disk_usage = psutil.disk_usage("/").percent
            if disk_usage > 90:
                logger.warning(f"⚠️  High disk usage: {disk_usage:.1f}%")
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")


    def pause_agent(self, agent_name: str) -> bool:
        """Pause a specific agent."""
        if agent_name in self.agents:
            self.update_agent_status(agent_name, "paused")
            logger.info(f"⏸️  Paused agent: {agent_name}")
            return True
        return False


    def resume_agent(self, agent_name: str) -> bool:
        """Resume a paused agent."""
        if agent_name in self.agents:
            self.update_agent_status(agent_name, "active")
            logger.info(f"▶️  Resumed agent: {agent_name}")
            return True
        return False


    def restart_agent(self, agent_name: str) -> bool:
        """Restart a specific agent."""
        if agent_name in self.agents:
            logger.info(f"🔄 Restarting agent: {agent_name}")
            # This would require more complex thread management
            # For now, just update status
            self.update_agent_status(agent_name, "restarting")
            return True
        return False


    def control_agent(self, agent_id: str, action: str) -> bool:
        """Control agent operations (pause / restart)."""
        try:
            if action == "pause":
                return self.pause_agent(agent_id)
            elif action == "restart":
                return self.restart_agent(agent_id)
            else:
                logger.error(f"Unknown action '{action}' for agent {agent_id}")
                return False
        except Exception as e:
            logger.error(
                f"Failed to control agent {agent_id} with action {action}: {e}"
            )
            return False


    def shutdown(self, timeout: int = 30):
        """Gracefully shutdown the orchestrator and all agents with timeout."""
        logger.info("🛑 Orchestrator shutdown initiated...")
        self.running = False
        self.shutdown_event.set()

        # Stop news monitoring service
        if self.news_monitoring_service:
            logger.info("📰 Stopping News Monitoring Service...")
            try:
                self.news_monitoring_service.stop()
                logger.info("✅ News Monitoring Service stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping News Monitoring Service: {e}")

        # Shutdown thread pool with timeout
        logger.info(f"⏳ Shutting down agent threads (timeout: {timeout}s)...")
        try:
            # Use shutdown without timeout for compatibility
            self.thread_pool.shutdown(wait = True)
            logger.info("✅ All agent threads stopped gracefully")
        except Exception as e:
            logger.warning(f"⚠️ Some agent threads may not have stopped cleanly: {e}")

        # Update all agent statuses
        with self.agent_state_lock:
            for agent_name in self.agents.keys():
                self.update_agent_status(agent_name, "stopped")

        logger.info("✅ Orchestrator shutdown complete")


def main():
    """Main entry point for TRAE.AI Master Orchestrator."""
    print("MAIN FUNCTION CALLED - DEBUG")
    logger.info("🚀 TRAE.AI LIVE PRODUCTION LAUNCH INITIATED")
    logger.info("=" * 60)

    # Run database migration FIRST, before any imports that might touch the database
    logger.info("🗄️ Running database migration...")
    try:

        from infra.migrations import migrate

        migrate()
        logger.info("✅ Database migration completed successfully")
    except ImportError as e:
        logger.warning(f"⚠️ Migration module not available: {e}")
    except Exception as e:
        logger.error(
            f"❌ Database migration failed: {e} - continuing with startup but some features may not work"
        )

    orchestrator = None
    dashboard_thread = None

    # Create and start event loop in a dedicated thread
    main_loop = asyncio.new_event_loop()


    def run_event_loop():
        """Run the event loop in a dedicated thread"""
        asyncio.set_event_loop(main_loop)
        try:
            main_loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")

    loop_thread = threading.Thread(
        target = run_event_loop, daemon = True, name="AsyncEventLoop"
    )
    loop_thread.start()

    # Wait for the loop to be properly running
    max_wait = 50  # 5 seconds max
    wait_count = 0
    while not main_loop.is_running() and wait_count < max_wait:
        time.sleep(0.1)
        wait_count += 1

    if main_loop.is_running():
        logger.info("✅ Event loop started successfully in dedicated thread")
    else:
        logger.error("❌ Failed to start event loop")
        return 1


    def graceful_shutdown(signum, frame):
        """Singleton signal handler for graceful shutdown."""
        if not _shutdown_event.is_set():
            signal_name = signal.Signals(signum).name
            logger.info(
                f"📡 Received {signal_name} signal, initiating graceful shutdown..."
            )
            _shutdown_event.set()

            # Add cleanup logic here
            if orchestrator:
                try:
                    orchestrator.shutdown()
                    logger.info("🛑 Orchestrator shutdown complete.")
                except Exception as e:
                    logger.error(f"Error during orchestrator shutdown: {e}")

            sys.exit(0)  # Force exit

    # Register signal handlers once
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    try:
        # Import dashboard and other components
        logger.info("📦 Importing dashboard and components...")
        DashboardApp = _import_dashboard()
        logger.info(f"Dashboard import result: {DashboardApp}")
        _import_task_queue()
        logger.info("✅ Component imports complete")

        # Validate environment
        logger.info("🔍 Validating environment and dependencies...")

        # Check for required environment variables
        required_env_vars = ["TRAE_MASTER_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return 1

        logger.info("✅ Environment validation complete")

        # Initialize orchestrator with main event loop
        logger.info("🎯 Initializing Master Orchestrator...")
        orchestrator = AutonomousOrchestrator(main_loop = main_loop)
        set_orchestrator_instance(orchestrator)
        logger.info("✅ Master Orchestrator initialized")

        # Initialize and start dashboard
        dashboard_future = None
        if DashboardApp:
            logger.info("🖥️  Starting unified dashboard...")
            try:
                # Try port 8080 first, fallback to 5000 if busy
                dashboard_port = int(
                    os.getenv("DASHBOARD_PORT") or os.getenv("PORT") or "8080"
                )
                logger.info(
                    f"[dashboard] attempting to bind to http://127.0.0.1:{dashboard_port}"
                )

                dashboard_app = DashboardApp(orchestrator = orchestrator)

                # Add debug routes for verification
                @dashboard_app.app.route("/_whoami")


                def _whoami():
                    return {"port": dashboard_port, "ok": True}

                @dashboard_app.app.route("/api / routes")


                def _routes():
                    return {
                        "count": len(dashboard_app.app.url_map._rules),
                            "routes": [
                            {"rule": r.rule, "methods": list(r.methods)}
                            for r in dashboard_app.app.url_map.iter_rules()
                        ],
                            }

                print(f"🚀 Starting dashboard on port {dashboard_port}")

                # Force consistent binding with CORS fix
                dashboard_future = orchestrator.thread_pool.submit(
                    lambda: dashboard_app.run(use_waitress = True)
                )
                logger.info(f"✅ Dashboard started on port {dashboard_port}")
            except OSError as e:
                # Handle port binding failures specifically
                if getattr(e, "errno", None) in (48, 98):  # EADDRINUSE mac / linux
                    logger.error(f"❌ Port {dashboard_port} is already in use")
                    # Try fallback port 5000
                    try:
                        fallback_port = 5000
                        logger.info(f"🔄 Trying fallback port {fallback_port}")
                        dashboard_future = orchestrator.thread_pool.submit(
                            lambda: dashboard_app.run(use_waitress = True)
                        )
                        logger.info(
                            f"✅ Dashboard started on fallback port {fallback_port}"
                        )
                    except Exception as fallback_e:
                        logger.error(
                            f"❌ Fallback port {fallback_port} also failed: {fallback_e}"
                        )

                        import traceback

                        logger.error(f"Full traceback: {traceback.format_exc()}")
                        logger.info("⚠️  Continuing without dashboard...")
                else:
                    logger.error(f"❌ Dashboard bind error: {e}")

                    import traceback

                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    logger.info("⚠️  Continuing without dashboard...")
            except Exception as e:
                logger.error(f"❌ Failed to start dashboard: {e}")

                import traceback

                logger.error(f"Full traceback: {traceback.format_exc()}")
                logger.info("⚠️  Continuing without dashboard...")
        else:
            logger.warning("⚠️  Dashboard not available, continuing without UI")

        # Start all agent threads
        logger.info("🤖 Starting all autonomous agents...")
        agent_futures = orchestrator.start_agent_threads()

        # Start news monitoring service
        news_future = None
        if orchestrator.news_monitoring_service:
            logger.info("📰 Starting News Monitoring Service...")
            try:
                news_future = orchestrator.thread_pool.submit(
                    lambda: asyncio.run(orchestrator.news_monitoring_service.start())
                )
                logger.info(
                    "✅ News Monitoring Service started - monitoring political RSS feeds"
                )
            except Exception as e:
                logger.error(f"❌ Failed to start News Monitoring Service: {e}")

        # Display system status
        logger.info("📊 System Status:")
        stats = orchestrator.get_system_stats()
        logger.info(
            f"   • Active Agents: {stats['active_agents']}/{stats['total_agents']}"
        )
        logger.info(f"   • Memory Usage: {stats['memory_usage']:.1f}%")
        logger.info(
            f"   • Database Health: {'✅' if stats['database_health'] else '❌'}"
        )
        logger.info(f"   • Task Queue Size: {stats['task_queue_size']}")

        logger.info("🎉 TRAE.AI Master Orchestrator is now LIVE!")
        logger.info("=" * 60)

        # Main execution loop with proper shutdown handling
        heartbeat_counter = 0
        while (
            orchestrator.running
            and not orchestrator.shutdown_event.is_set()
            and not _shutdown_event.is_set()
        ):
            # Check if any critical threads have died
            if agent_futures:
                for agent_name, future in list(agent_futures.items()):
                    if future.done():
                        try:
                            future.result()  # This will raise any exception
                        except Exception as e:
                            logger.error(f"❌ Agent {agent_name} died: {e}")
                        agent_futures.pop(agent_name, None)

            # Check dashboard health
            if dashboard_future and dashboard_future.done():
                try:
                    dashboard_future.result()
                except Exception as e:
                    logger.error(f"❌ Dashboard died: {e}")
                dashboard_future = None

            time.sleep(1)
            heartbeat_counter += 1

            # Log heartbeat every 5 minutes
            if heartbeat_counter % 300 == 0:
                stats = orchestrator.get_system_stats()
                logger.info(
                    f"💓 System heartbeat - Uptime: {stats['uptime']}, Active Agents: {stats['active_agents']}"
                )

        logger.info("🛑 Main execution loop terminated")
        return 0

    except KeyboardInterrupt:
        logger.info("\\n⚡ Keyboard interrupt detected")
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")

        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        # Ensure graceful shutdown
        if orchestrator:
            logger.info("🔄 Performing graceful shutdown...")
            orchestrator.shutdown()

        # Stop the event loop
        if main_loop and not main_loop.is_closed():
            logger.info("⏳ Stopping event loop...")
            main_loop.call_soon_threadsafe(main_loop.stop)

        # Wait for dashboard thread to finish
        if dashboard_thread and dashboard_thread.is_alive():
            logger.info("⏳ Waiting for dashboard to shutdown...")
            dashboard_thread.join(timeout = 5)

        logger.info("✅ TRAE.AI Master Orchestrator shutdown complete")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())