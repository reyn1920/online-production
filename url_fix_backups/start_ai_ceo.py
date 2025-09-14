#!/usr / bin / env python3
"""
AI CEO Master Startup Script - Full Automation Launch

This script launches the complete AI CEO automation system with:
1. AI CEO Master Controller
2. Full Automation Pipeline
3. Autonomous Decision Engine
4. Self - Healing Protocols
5. Monitoring Dashboard
6. All AI Agents and Services

Author: TRAE.AI System
Version: 2.0.0
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import our AI CEO components
try:
    from ai_ceo_master_controller import AICEOMasterController
    from autonomous_decision_engine import AutonomousDecisionEngine
    from full_automation_pipeline import FullAutomationPipeline
    from monitoring_dashboard import MonitoringDashboard
    from self_healing_protocols import SelfHealingProtocols

except ImportError as e:
    print(f"❌ Error importing AI CEO components: {e}")
    print("Please ensure all AI CEO modules are in the current directory.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ai_ceo_system.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class AICEOSystemLauncher:
    """Master launcher for the complete AI CEO automation system."""

    def __init__(self):
        self.components = {}
        self.running = False
        self.startup_order = [
            "decision_engine",
            "pipeline",
            "healing_protocols",
            "master_controller",
            "monitoring_dashboard",
        ]
        self.shutdown_order = list(reversed(self.startup_order))

        # System configuration
        self.config = self._load_configuration()

        # Process management
        self.processes = {}
        self.threads = {}

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("🚀 AI CEO System Launcher initialized")

    def _load_configuration(self) -> Dict[str, Any]:
        """Load system configuration."""
        config_file = Path("ai_ceo_config.json")

        default_config = {
            "system": {
                "startup_timeout": 300,
                "health_check_interval": 30,
                "auto_restart": True,
                "max_restart_attempts": 3,
            },
            "components": {
                "decision_engine": {"enabled": True, "startup_delay": 0},
                "pipeline": {"enabled": True, "startup_delay": 5},
                "healing_protocols": {"enabled": True, "startup_delay": 10},
                "master_controller": {"enabled": True, "startup_delay": 15},
                "monitoring_dashboard": {
                    "enabled": True,
                    "startup_delay": 20,
                    "port": 5000,
                },
            },
            "agents": {
                "marketing_agent": True,
                "financial_agent": True,
                "monetization_agent": True,
                "stealth_automation_agent": True,
                "content_generation_agent": True,
            },
            "apis": {
                "youtube_api": True,
                "gmail_api": True,
                "social_media_apis": True,
                "payment_apis": True,
            },
            "monitoring": {
                "enable_real_time_alerts": True,
                "enable_performance_tracking": True,
                "enable_business_metrics": True,
                "dashboard_refresh_rate": 5,
            },
        }

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
                    logger.info(f"📋 Configuration loaded from {config_file}")
            except Exception as e:
                logger.warning(f"⚠️ Error loading config file: {e}. Using defaults.")
        else:
            # Save default configuration
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"📋 Default configuration saved to {config_file}")

        return default_config

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
        self.shutdown_system()

    def start_system(self, components: Optional[List[str]] = None):
        """Start the complete AI CEO system."""
        logger.info("🚀 Starting AI CEO Automation System...")
        logger.info("=" * 60)

        self.running = True
        startup_success = True

        # Determine which components to start
        components_to_start = components or self.startup_order

        try:
            # Pre - startup checks
            if not self._pre_startup_checks():
                logger.error("❌ Pre - startup checks failed")
                return False

            # Start components in order
            for component_name in components_to_start:
                if not self.config["components"].get(component_name, {}).get("enabled", True):
                    logger.info(f"⏭️ Skipping disabled component: {component_name}")
                    continue

                logger.info(f"🔄 Starting {component_name}...")

                # Apply startup delay
                startup_delay = (
                    self.config["components"].get(component_name, {}).get("startup_delay", 0)
                )
                if startup_delay > 0:
                    logger.info(f"⏳ Waiting {startup_delay}s before starting {component_name}")
                    time.sleep(startup_delay)

                # Start component
                success = self._start_component(component_name)

                if success:
                    logger.info(f"✅ {component_name} started successfully")
                else:
                    logger.error(f"❌ Failed to start {component_name}")
                    startup_success = False

                    if not self.config["system"].get("auto_restart", True):
                        break

            if startup_success:
                logger.info("=" * 60)
                logger.info("🎉 AI CEO System startup completed successfully!")
                logger.info("🤖 AI CEO is now fully operational and autonomous")
                logger.info("📊 Monitor system status at: http://localhost:5000")
                logger.info("=" * 60)

                # Start system monitoring
                self._start_system_monitoring()

                return True
            else:
                logger.error("❌ AI CEO System startup failed")
                self.shutdown_system()
                return False

        except Exception as e:
            logger.error(f"❌ Critical error during startup: {e}")
            logger.error(f"Stack trace: {e.__class__.__name__}: {e}")
            self.shutdown_system()
            return False

    def _pre_startup_checks(self) -> bool:
        """Perform pre - startup system checks."""
        logger.info("🔍 Performing pre - startup checks...")

        checks = [
            self._check_python_version,
            self._check_required_files,
            self._check_system_resources,
            self._check_network_connectivity,
            self._check_database_access,
        ]

        for check in checks:
            try:
                if not check():
                    return False
            except Exception as e:
                logger.error(f"❌ Pre - startup check failed: {e}")
                return False

        logger.info("✅ All pre - startup checks passed")
        return True

    def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            return False
        logger.info(f"✅ Python version: {sys.version.split()[0]}")
        return True

    def _check_required_files(self) -> bool:
        """Check for required system files."""
        required_files = [
            "ai_ceo_master_controller.py",
            "full_automation_pipeline.py",
            "autonomous_decision_engine.py",
            "self_healing_protocols.py",
            "monitoring_dashboard.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            logger.error(f"❌ Missing required files: {missing_files}")
            return False

        logger.info("✅ All required files present")
        return True

    def _check_system_resources(self) -> bool:
        """Check system resource availability."""
        try:
            import psutil

            # Check available memory (minimum 1GB)
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory < 1.0:
                logger.error(
                    f"❌ Insufficient memory: {available_memory:.1f}GB available (1GB required)"
                )
                return False

            # Check available disk space (minimum 1GB)
            available_disk = psutil.disk_usage(".").free / (1024**3)
            if available_disk < 1.0:
                logger.error(
                    f"❌ Insufficient disk space: {available_disk:.1f}GB available (1GB required)"
                )
                return False

            logger.info(
                f"✅ System resources: {available_memory:.1f}GB RAM, {available_disk:.1f}GB disk"
            )
            return True

        except ImportError:
            logger.warning("⚠️ psutil not available, skipping resource check")
            return True
        except Exception as e:
            logger.error(f"❌ Resource check failed: {e}")
            return False

    def _check_network_connectivity(self) -> bool:
        """Check network connectivity."""
        try:
            import socket

            socket.create_connection(("8.8.8.8", 53), timeout=5)
            logger.info("✅ Network connectivity available")
            return True
        except OSError:
            logger.warning("⚠️ Limited network connectivity (offline mode)")
            return True  # Allow offline operation

    def _check_database_access(self) -> bool:
        """Check database access."""
        try:
            import sqlite3

            # Test database creation
            test_db = "test_startup.db"
            conn = sqlite3.connect(test_db)
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            conn.close()

            # Clean up
            if Path(test_db).exists():
                Path(test_db).unlink()

            logger.info("✅ Database access available")
            return True

        except Exception as e:
            logger.error(f"❌ Database access check failed: {e}")
            return False

    def _start_component(self, component_name: str) -> bool:
        """Start a specific system component."""
        try:
            if component_name == "decision_engine":
                return self._start_decision_engine()
            elif component_name == "pipeline":
                return self._start_pipeline()
            elif component_name == "healing_protocols":
                return self._start_healing_protocols()
            elif component_name == "master_controller":
                return self._start_master_controller()
            elif component_name == "monitoring_dashboard":
                return self._start_monitoring_dashboard()
            else:
                logger.error(f"❌ Unknown component: {component_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error starting {component_name}: {e}")
            return False

    def _start_decision_engine(self) -> bool:
        """Start the autonomous decision engine."""
        try:
            decision_engine = AutonomousDecisionEngine()
            decision_engine.start_decision_engine()

            self.components["decision_engine"] = decision_engine
            logger.info("🧠 Autonomous Decision Engine started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start decision engine: {e}")
            return False

    def _start_pipeline(self) -> bool:
        """Start the full automation pipeline."""
        try:
            pipeline = FullAutomationPipeline()
            pipeline.start_pipeline()

            self.components["pipeline"] = pipeline
            logger.info("🔄 Full Automation Pipeline started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start pipeline: {e}")
            return False

    def _start_healing_protocols(self) -> bool:
        """Start the self - healing protocols."""
        try:
            # Connect to pipeline if available
            pipeline = self.components.get("pipeline")

            healing_protocols = SelfHealingProtocols(pipeline)
            healing_protocols.start_healing_protocols()

            self.components["healing_protocols"] = healing_protocols
            logger.info("🔧 Self - Healing Protocols started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start healing protocols: {e}")
            return False

    def _start_master_controller(self) -> bool:
        """Start the AI CEO master controller."""
        try:
            # Get references to other components
            pipeline = self.components.get("pipeline")
            decision_engine = self.components.get("decision_engine")
            healing_protocols = self.components.get("healing_protocols")

            master_controller = AICEOMasterController(
                pipeline=pipeline,
                decision_engine=decision_engine,
                healing_system=healing_protocols,
            )
            master_controller.start_ai_ceo()

            self.components["master_controller"] = master_controller
            logger.info("🤖 AI CEO Master Controller started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start master controller: {e}")
            return False

    def _start_monitoring_dashboard(self) -> bool:
        """Start the monitoring dashboard."""
        try:
            # Get references to other components
            pipeline = self.components.get("pipeline")
            master_controller = self.components.get("master_controller")
            healing_protocols = self.components.get("healing_protocols")

            dashboard = MonitoringDashboard(
                pipeline=pipeline,
                ai_ceo=master_controller,
                healing_system=healing_protocols,
            )

            # Start dashboard in separate thread
            dashboard_thread = threading.Thread(
                target=dashboard.run_dashboard,
                kwargs={
                    "host": "0.0.0.0",
                    "port": self.config["components"]["monitoring_dashboard"].get("port", 5000),
                },
                daemon=True,
            )
            dashboard_thread.start()

            self.components["monitoring_dashboard"] = dashboard
            self.threads["monitoring_dashboard"] = dashboard_thread

            logger.info("📊 Monitoring Dashboard started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start monitoring dashboard: {e}")
            return False

    def _start_system_monitoring(self):
        """Start system - wide monitoring."""
        logger.info("📊 Starting system monitoring...")

        # Start monitoring thread
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()
        self.threads["system_monitoring"] = monitoring_thread

    def _monitoring_loop(self):
        """Main system monitoring loop."""
        logger.info("🔄 System monitoring loop started")

        health_check_interval = self.config["system"].get("health_check_interval", 30)

        while self.running:
            try:
                # Check component health
                self._check_component_health()

                # Log system status
                self._log_system_status()

                # Sleep until next check
                time.sleep(health_check_interval)

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error

        logger.info("🛑 System monitoring loop stopped")

    def _check_component_health(self):
        """Check health of all components."""
        for component_name, component in self.components.items():
            try:
                if hasattr(component, "get_status"):
                    status = component.get_status()
                    if status.get("status") != "running":
                        logger.warning(
                            f"⚠️ Component {component_name} status: {status.get('status')}"
                        )

                        # Auto - restart if enabled
                        if self.config["system"].get("auto_restart", True):
                            logger.info(f"🔄 Auto - restarting {component_name}")
                            self._restart_component(component_name)

            except Exception as e:
                logger.error(f"❌ Error checking {component_name} health: {e}")

    def _restart_component(self, component_name: str):
        """Restart a specific component."""
        try:
            logger.info(f"🔄 Restarting {component_name}...")

            # Stop component
            component = self.components.get(component_name)
            if component and hasattr(component, "stop"):
                component.stop()

            # Wait a moment
            time.sleep(5)

            # Restart component
            success = self._start_component(component_name)

            if success:
                logger.info(f"✅ {component_name} restarted successfully")
            else:
                logger.error(f"❌ Failed to restart {component_name}")

        except Exception as e:
            logger.error(f"❌ Error restarting {component_name}: {e}")

    def _log_system_status(self):
        """Log current system status."""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "running_components": len(self.components),
                "system_health": (
                    "healthy"
                    if all(
                        comp.get_status().get("status") == "running"
                        for comp in self.components.values()
                        if hasattr(comp, "get_status")
                    )
                    else "degraded"
                ),
            }

            # Log to file periodically (every 10 minutes)
            if int(time.time()) % 600 == 0:
                logger.info(f"📊 System Status: {json.dumps(status)}")

        except Exception as e:
            logger.error(f"❌ Error logging system status: {e}")

    def shutdown_system(self):
        """Gracefully shutdown the AI CEO system."""
        logger.info("🛑 Shutting down AI CEO System...")

        self.running = False

        # Stop components in reverse order
        for component_name in self.shutdown_order:
            if component_name in self.components:
                try:
                    logger.info(f"🛑 Stopping {component_name}...")
                    component = self.components[component_name]

                    if hasattr(component, "stop"):
                        component.stop()
                    elif hasattr(component, "shutdown"):
                        component.shutdown()

                    logger.info(f"✅ {component_name} stopped")

                except Exception as e:
                    logger.error(f"❌ Error stopping {component_name}: {e}")

        # Wait for threads to finish
        for thread_name, thread in self.threads.items():
            try:
                logger.info(f"⏳ Waiting for {thread_name} thread...")
                thread.join(timeout=10)
            except Exception as e:
                logger.error(f"❌ Error joining {thread_name} thread: {e}")

        logger.info("✅ AI CEO System shutdown complete")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            component_status = {}

            for name, component in self.components.items():
                if hasattr(component, "get_status"):
                    component_status[name] = component.get_status()
                else:
                    component_status[name] = {"status": "running"}

            return {
                "system_running": self.running,
                "components": component_status,
                "startup_time": getattr(self, "startup_time", None),
                "configuration": self.config,
            }

        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            return {"error": str(e)}

    def run_interactive_mode(self):
        """Run in interactive mode with command interface."""
        logger.info("🎮 Starting interactive mode...")
        logger.info("Available commands: status, restart <component>, shutdown, help")

        while self.running:
            try:
                command = input("AI - CEO> ").strip().lower()

                if command == "status":
                    status = self.get_system_status()
                    print(json.dumps(status, indent=2, default=str))

                elif command.startswith("restart "):
                    component = command.split(" ", 1)[1]
                    if component in self.components:
                        self._restart_component(component)
                    else:
                        print(f"Unknown component: {component}")

                elif command == "shutdown":
                    break

                elif command == "help":
                    print("Available commands:")
                    print("  status - Show system status")
                    print("  restart <component> - Restart a component")
                    print("  shutdown - Shutdown system")
                    print("  help - Show this help")

                elif command == "":
                    continue

                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")

            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                logger.error(f"❌ Error in interactive mode: {e}")

        self.shutdown_system()


def main():
    """Main function to launch the AI CEO system."""
    parser = argparse.ArgumentParser(description="AI CEO Automation System Launcher")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--components", "-c", nargs="+", help="Specific components to start")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show system status and exit")

    args = parser.parse_args()

    # Create launcher
    launcher = AICEOSystemLauncher()

    try:
        if args.status:
            # Show status and exit
            status = launcher.get_system_status()
            print(json.dumps(status, indent=2, default=str))
            return

        # Start the system
        success = launcher.start_system(components=args.components)

        if not success:
            logger.error("❌ Failed to start AI CEO system")
            sys.exit(1)

        # Record startup time
        launcher.startup_time = datetime.now().isoformat()

        if args.interactive:
            # Run in interactive mode
            launcher.run_interactive_mode()
        else:
            # Run in daemon mode
            logger.info("🤖 AI CEO System running in daemon mode")
            logger.info("Press Ctrl + C to shutdown")

            try:
                while launcher.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Keyboard interrupt received")

    except Exception as e:
        logger.error(f"❌ Critical system error: {e}")
        logger.error(f"Stack trace: {e.__class__.__name__}: {e}")
        sys.exit(1)

    finally:
        launcher.shutdown_system()


if __name__ == "__main__":
    main()
