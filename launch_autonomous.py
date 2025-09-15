#!/usr/bin/env python3
""""""
TRAE.AI Autonomous System Launcher

The main entry point for the fully autonomous TRAE.AI system.
This script is designed to be managed by launchd for bulletproof persistence
and self - healing capabilities on macOS.

Key Features:
- Initializes all autonomous agents
- Sets up the task queue system
- Implements system health monitoring
- Provides graceful shutdown handling
- Integrates with the Total Access dashboard
- Implements the closed - loop feedback system
""""""

import json
import logging
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.agents.content_agent import ContentAgent
from backend.agents.marketing_agent import MarketingAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.system_agent import SystemAgent
from backend.core.secret_store import SecretStore

# Import TRAE.AI components

from backend.core.task_queue import TaskPriority, TaskQueue


class AutonomousSystemLauncher:
    """Main launcher for the TRAE.AI autonomous system"""

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        # System components
        self.task_queue = None
        self.agents = {}
        self.agent_workers = {}
        self.secret_store = None

        # System state
        self.running = False
        self.shutdown_event = threading.Event()

        # Health monitoring
        self.health_monitor_thread = None
        self.last_health_check = datetime.now()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.logger.info("TRAE.AI Autonomous System Launcher initialized")

    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(logs_dir / "autonomous_system.log"),
                logging.StreamHandler(sys.stdout),
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         )

        # Set specific log levels for components
        logging.getLogger("TaskQueue").setLevel(logging.INFO)
        logging.getLogger("PlannerAgent").setLevel(logging.INFO)
        logging.getLogger("SystemAgent").setLevel(logging.INFO)
        logging.getLogger("ResearchAgent").setLevel(logging.INFO)
        logging.getLogger("MarketingAgent").setLevel(logging.INFO)
        logging.getLogger("ContentAgent").setLevel(logging.INFO)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()

    def initialize_system(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing TRAE.AI Autonomous System...")

            # Initialize secret store
            self.logger.info("Initializing SecretStore...")
            self.secret_store = SecretStore()

            # Initialize task queue
            self.logger.info("Initializing TaskQueue...")
            self.task_queue = TaskQueue()
            self.task_queue.start()

            # Initialize agents
            self.initialize_agents()

            # Register agents with task queue
            self.register_agents_with_queue()

            # Setup initial tasks
            self.setup_initial_tasks()

            # Start health monitoring
            self.start_health_monitoring()

            self.logger.info("TRAE.AI Autonomous System fully initialized and operational")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            return False

    def initialize_agents(self):
        """Initialize all autonomous agents"""
        try:
            # Initialize System Agent first (it monitors others)
            self.logger.info("Initializing SystemAgent...")
            self.agents["system"] = SystemAgent()

            # Initialize Planner Agent (the strategist)
            self.logger.info("Initializing PlannerAgent...")
            self.agents["planner"] = PlannerAgent()

            # Initialize Research Agent (intelligence gathering)
            self.logger.info("Initializing ResearchAgent...")
            self.agents["research"] = ResearchAgent()

            # Initialize Marketing Agent (growth engine)
            self.logger.info("Initializing MarketingAgent...")
            self.agents["marketing"] = MarketingAgent()

            # Initialize Content Agent (creative engine)
            self.logger.info("Initializing ContentAgent...")
            self.agents["content"] = ContentAgent()

            self.logger.info(f"Initialized {len(self.agents)} autonomous agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise

    def register_agents_with_queue(self):
        """Register all agents with the task queue"""
        try:
            # Register System Agent - MAXED OUT
            worker_id = self.task_queue.register_agent(
                agent_type="SystemAgent",
                agent_instance=self.agents["system"],
                capabilities=["system_health", "diagnostics", "repair", "monitoring"],
                max_concurrent_tasks=8,
# BRACKET_SURGEON: disabled
#             )
            self.agent_workers["system"] = worker_id

            # Register Planner Agent - MAXED OUT
            worker_id = self.task_queue.register_agent(
                agent_type="PlannerAgent",
                agent_instance=self.agents["planner"],
                capabilities=[
                    "strategy",
                    "planning",
                    "optimization",
                    "feedback_processing",
# BRACKET_SURGEON: disabled
#                 ],
                max_concurrent_tasks=4,
# BRACKET_SURGEON: disabled
#             )
            self.agent_workers["planner"] = worker_id

            # Register Research Agent - MAXED OUT
            worker_id = self.task_queue.register_agent(
                agent_type="ResearchAgent",
                agent_instance=self.agents["research"],
                capabilities=[
                    "trend_analysis",
                    "api_discovery",
                    "hypocrisy_detection",
                    "market_intelligence",
# BRACKET_SURGEON: disabled
#                 ],
                max_concurrent_tasks=12,
# BRACKET_SURGEON: disabled
#             )
            self.agent_workers["research"] = worker_id

            # Register Marketing Agent - MAXED OUT
            worker_id = self.task_queue.register_agent(
                agent_type="MarketingAgent",
                agent_instance=self.agents["marketing"],
                capabilities=[
                    "campaign_management",
                    "seo_optimization",
                    "affiliate_monitoring",
                    "content_promotion",
# BRACKET_SURGEON: disabled
#                 ],
                max_concurrent_tasks=8,
# BRACKET_SURGEON: disabled
#             )
            self.agent_workers["marketing"] = worker_id

            # Register Content Agent - MAXED OUT
            worker_id = self.task_queue.register_agent(
                agent_type="ContentAgent",
                agent_instance=self.agents["content"],
                capabilities=[
                    "video_creation",
                    "voice_synthesis",
                    "avatar_generation",
                    "graphics_creation",
# BRACKET_SURGEON: disabled
#                 ],
                max_concurrent_tasks=4,  # Resource - intensive tasks but maxed out
# BRACKET_SURGEON: disabled
#             )
            self.agent_workers["content"] = worker_id

            self.logger.info(f"Registered {len(self.agent_workers)} agent workers with task queue")

        except Exception as e:
            self.logger.error(f"Failed to register agents with queue: {e}")
            raise

    def setup_initial_tasks(self):
        """Setup initial autonomous tasks"""
        try:
            # System health check task (recurring)
            self.task_queue.submit_task(
                task_type="system_health_check",
                agent_type="SystemAgent",
                payload={"check_type": "full_system_scan"},
                priority=TaskPriority.HIGH,
                metadata={"recurring": True, "interval": 300},  # Every 5 minutes
# BRACKET_SURGEON: disabled
#             )

            # Initial strategy planning task
            self.task_queue.submit_task(
                task_type="create_initial_strategy",
                agent_type="PlannerAgent",
                payload={"strategy_type": "bootstrap_autonomous_operation"},
                priority=TaskPriority.URGENT,
                metadata={"bootstrap": True},
# BRACKET_SURGEON: disabled
#             )

            # Market research initialization
            self.task_queue.submit_task(
                task_type="initialize_market_research",
                agent_type="ResearchAgent",
                payload={"research_scope": "ai_automation_trends"},
                priority=TaskPriority.HIGH,
                metadata={"initialization": True},
# BRACKET_SURGEON: disabled
#             )

            # Marketing system initialization
            self.task_queue.submit_task(
                task_type="initialize_marketing_system",
                agent_type="MarketingAgent",
                payload={"setup_type": "autonomous_marketing_layer"},
                priority=TaskPriority.HIGH,
                metadata={"initialization": True},
# BRACKET_SURGEON: disabled
#             )

            # Content pipeline initialization
            self.task_queue.submit_task(
                task_type="initialize_content_pipeline",
                agent_type="ContentAgent",
                payload={"pipeline_type": "api_first_automation"},
                priority=TaskPriority.MEDIUM,
                metadata={"initialization": True},
# BRACKET_SURGEON: disabled
#             )

            self.logger.info("Initial autonomous tasks scheduled")

        except Exception as e:
            self.logger.error(f"Failed to setup initial tasks: {e}")
            raise

    def start_health_monitoring(self):
        """Start system health monitoring thread"""
        self.health_monitor_thread = threading.Thread(target=self.health_monitor_loop, daemon=True)
        self.health_monitor_thread.start()
        self.logger.info("Health monitoring started")

    def health_monitor_loop(self):
        """Main health monitoring loop"""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Check system health
                self.perform_health_check()

                # Check agent status
                self.check_agent_health()

                # Check task queue health
                self.check_task_queue_health()

                # Update last health check time
                self.last_health_check = datetime.now()

                # Wait before next check
                self.shutdown_event.wait(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                self.shutdown_event.wait(60)

    def perform_health_check(self):
        """Perform comprehensive system health check"""
        try:
            # Check critical directories
            critical_paths = [
                project_root / "data",
                project_root / "backend",
                project_root / "logs",
# BRACKET_SURGEON: disabled
#             ]

            for path in critical_paths:
                if not path.exists():
                    self.logger.error(f"Critical path missing: {path}")
                    path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Recreated critical path: {path}")

            # Check database connectivity
            if self.task_queue:
                metrics = self.task_queue.get_queue_metrics()
                if (
                    metrics.total_tasks == 0
                    and (datetime.now() - self.last_health_check).seconds > 3600
# BRACKET_SURGEON: disabled
#                 ):
                    self.logger.warning("No tasks processed in over an hour")

            # Log health status
            self.logger.debug("System health check completed successfully")

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    def check_agent_health(self):
        """Check health of all agents"""
        try:
            if not self.task_queue:
                return

            agent_status = self.task_queue.get_agent_status()

            for worker_id, status in agent_status.items():
                last_heartbeat = datetime.fromisoformat(status["last_heartbeat"])
                time_since_heartbeat = (datetime.now() - last_heartbeat).seconds

                if time_since_heartbeat > 300:  # 5 minutes
                    self.logger.warning(
                        f"Agent {worker_id} hasn't sent heartbeat in {time_since_heartbeat}s"'
# BRACKET_SURGEON: disabled
#                     )

                if status["status"] == "offline":
                    self.logger.error(f"Agent {worker_id} is offline")

        except Exception as e:
            self.logger.error(f"Agent health check failed: {e}")

    def check_task_queue_health(self):
        """Check task queue health"""
        try:
            if not self.task_queue:
                return

            metrics = self.task_queue.get_queue_metrics()

            # Check for excessive failed tasks
            if metrics.total_tasks > 0:
                failure_rate = (
                    metrics.failed_tasks + metrics.dead_letter_tasks
# BRACKET_SURGEON: disabled
#                 ) / metrics.total_tasks
                if failure_rate > 0.1:  # More than 10% failure rate
                    self.logger.warning(f"High task failure rate: {failure_rate:.2%}")

            # Check for stuck tasks
            if metrics.running_tasks > 10:
                self.logger.warning(f"High number of running tasks: {metrics.running_tasks}")

            # Log queue metrics
            self.logger.debug(
                f"Queue metrics: {metrics.pending_tasks} pending, "
                f"{metrics.running_tasks} running, {metrics.completed_tasks} completed"
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            self.logger.error(f"Task queue health check failed: {e}")

    def run(self):
        """Main run loop for the autonomous system"""
        try:
            # Initialize system
            if not self.initialize_system():
                self.logger.error("Failed to initialize system, exiting")
                return False

            self.running = True
            self.logger.info("TRAE.AI Autonomous System is now running")

            # Log system startup metrics
            self.log_startup_metrics()

            # Main event loop
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Check if we need to schedule recurring tasks
                    self.schedule_recurring_tasks()

                    # Process any system - level events
                    self.process_system_events()

                    # Brief sleep to prevent busy waiting
                    self.shutdown_event.wait(10)

                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.logger.error(f"Main loop error: {e}")
                    self.shutdown_event.wait(30)

            return True

        except Exception as e:
            self.logger.error(f"Fatal error in main run loop: {e}")
            return False
        finally:
            self.shutdown()

    def schedule_recurring_tasks(self):
        """Schedule recurring system tasks"""
        try:
            current_time = datetime.now()

            # Schedule hourly strategy review
            if current_time.minute == 0:  # Top of the hour
                self.task_queue.submit_task(
                    task_type="strategy_review",
                    agent_type="PlannerAgent",
                    payload={"review_type": "hourly_optimization"},
                    priority=TaskPriority.MEDIUM,
                    metadata={"recurring": True, "interval": 3600},
# BRACKET_SURGEON: disabled
#                 )

            # Schedule daily market research
            if current_time.hour == 6 and current_time.minute == 0:  # 6 AM daily
                self.task_queue.submit_task(
                    task_type="daily_market_research",
                    agent_type="ResearchAgent",
                    payload={"research_type": "comprehensive_market_scan"},
                    priority=TaskPriority.HIGH,
                    metadata={"recurring": True, "interval": 86400},
# BRACKET_SURGEON: disabled
#                 )

            # Schedule marketing optimization
            if current_time.hour == 9 and current_time.minute == 0:  # 9 AM daily
                self.task_queue.submit_task(
                    task_type="marketing_optimization",
                    agent_type="MarketingAgent",
                    payload={"optimization_type": "daily_campaign_review"},
                    priority=TaskPriority.MEDIUM,
                    metadata={"recurring": True, "interval": 86400},
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            self.logger.error(f"Failed to schedule recurring tasks: {e}")

    def process_system_events(self):
        """Process system - level events and notifications"""
        try:
            # Check for critical system alerts
            if self.task_queue:
                metrics = self.task_queue.get_queue_metrics()

                # Alert on high failure rate
                if metrics.total_tasks > 100 and metrics.success_rate < 90:
                    self.logger.warning(
                        f"System performance degraded: {metrics.success_rate:.1f}% success rate"
# BRACKET_SURGEON: disabled
#                     )

                    # Submit diagnostic task
                    self.task_queue.submit_task(
                        task_type="system_diagnostics",
                        agent_type="SystemAgent",
                        payload={"diagnostic_type": "performance_degradation"},
                        priority=TaskPriority.URGENT,
# BRACKET_SURGEON: disabled
#                     )

        except Exception as e:
            self.logger.error(f"Failed to process system events: {e}")

    def log_startup_metrics(self):
        """Log system startup metrics"""
        try:
            startup_info = {
                "timestamp": datetime.now().isoformat(),
                "agents_initialized": len(self.agents),
                "workers_registered": len(self.agent_workers),
                "system_mode": "autonomous",
                "python_version": sys.version,
                "working_directory": str(project_root),
# BRACKET_SURGEON: disabled
#             }

            self.logger.info(f"System startup metrics: {json.dumps(startup_info, indent = 2)}")

        except Exception as e:
            self.logger.error(f"Failed to log startup metrics: {e}")

    def shutdown(self):
        """Graceful system shutdown"""
        if not self.running:
            return

        self.logger.info("Initiating graceful shutdown...")
        self.running = False
        self.shutdown_event.set()

        try:
            # Stop task queue
            if self.task_queue:
                self.logger.info("Stopping task queue...")
                self.task_queue.stop()

            # Shutdown agents
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, "shutdown"):
                        self.logger.info(f"Shutting down {agent_name} agent...")
                        agent.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down {agent_name} agent: {e}")

            # Wait for health monitor to stop
            if self.health_monitor_thread and self.health_monitor_thread.is_alive():
                self.health_monitor_thread.join(timeout=5)

            self.logger.info("TRAE.AI Autonomous System shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    launcher = AutonomousSystemLauncher()

    try:
        success = launcher.run()
        exit_code = 0 if success else 1
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()