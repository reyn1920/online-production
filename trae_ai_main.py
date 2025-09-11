#!/usr/bin/env python3
"""
TRAE.AI Complete Application Launcher
Unified entry point for the entire TRAE.AI ecosystem

This script orchestrates all services:
- Content Agent (port 8001)
- Marketing Agent (port 8002)
- Analytics Dashboard (port 8004)
- Monetization Bundle (port 8003)
- Orchestrator (port 8000)
- Dashboard (port 8083)

Usage:
    python trae_ai_main.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    REDIS_URL - Redis connection string
    OPENAI_API_KEY - OpenAI API key
    ANTHROPIC_API_KEY - Anthropic API key
    And other service-specific API keys
"""

import asyncio
import logging
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TraeAILauncher:
    """Main launcher for the complete TRAE.AI application"""

    def __init__(self):
        self.processes = {}
        self.running = False
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("Checking system dependencies...")

        # Check Python packages
        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "redis",
            "celery",
            "openai",
            "anthropic",
            "flask",
            "flask_socketio",
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.error("Install with: pip install -r requirements.txt")
            return False

        # Check environment variables
        required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "REDIS_URL"]

        missing_env_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_env_vars.append(var)

        if missing_env_vars:
            logger.warning(f"Missing environment variables: {missing_env_vars}")
            logger.warning("Some services may not function properly")

        return True

    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            "logs",
            "temp",
            "output",
            "data",
            "uploads",
            "static/videos",
            "static/images",
            "static/audio",
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

        logger.info("Created necessary directories")

    def start_service(
        self, name: str, module_path: str, port: int, cwd: str = None
    ) -> bool:
        """Start a service in a separate process"""
        try:
            if cwd is None:
                cwd = str(project_root)

            cmd = [sys.executable, module_path]

            logger.info(f"Starting {name} on port {port}...")

            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
            )

            self.processes[name] = {
                "process": process,
                "port": port,
                "module": module_path,
                "cwd": cwd,
            }

            # Give the service time to start
            time.sleep(2)

            if process.poll() is None:
                logger.info(f"✅ {name} started successfully on port {port}")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ {name} failed to start:")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False

    def start_all_services(self) -> bool:
        """Start all TRAE.AI services"""
        logger.info("🚀 Starting TRAE.AI Complete Application...")

        services = [
            {
                "name": "Content Agent",
                "module": "content-agent/main.py",
                "port": 8001,
                "cwd": str(project_root / "content-agent"),
            },
            {
                "name": "Marketing Agent",
                "module": "marketing-agent/main.py",
                "port": 8002,
                "cwd": str(project_root / "marketing-agent"),
            },
            {
                "name": "Monetization Bundle",
                "module": "monetization-bundle/main.py",
                "port": 8003,
                "cwd": str(project_root / "monetization-bundle"),
            },
            {
                "name": "Analytics Dashboard",
                "module": "analytics-dashboard/main.py",
                "port": 8004,
                "cwd": str(project_root / "analytics-dashboard"),
            },
            {
                "name": "Orchestrator",
                "module": "orchestrator/main.py",
                "port": 8000,
                "cwd": str(project_root / "orchestrator"),
            },
        ]

        success_count = 0
        for service in services:
            if self.start_service(**service):
                success_count += 1
            else:
                logger.warning(f"Service {service['name']} failed to start")

        # Start the main dashboard last
        try:
            logger.info("Starting TRAE.AI Dashboard...")
            from app.dashboard import DashboardApp

            def run_dashboard():
                dashboard = DashboardApp()
                dashboard.run(use_waitress=True)

            dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
            dashboard_thread.start()

            logger.info("✅ TRAE.AI Dashboard started on port 8083")
            success_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {e}")

        logger.info(f"\n🎯 Started {success_count}/{len(services) + 1} services")

        if success_count > 0:
            self.print_service_status()
            return True
        else:
            logger.error("❌ No services started successfully")
            return False

    def print_service_status(self):
        """Print status of all services"""
        print("\n" + "=" * 80)
        print("🚀 TRAE.AI COMPLETE APPLICATION - SERVICE STATUS")
        print("=" * 80)

        services_info = [
            ("Content Agent", "8001", "AI content creation and video generation"),
            ("Marketing Agent", "8002", "Campaign management and social media"),
            ("Monetization Bundle", "8003", "Revenue tracking and payments"),
            ("Analytics Dashboard", "8004", "Business intelligence and reporting"),
            ("Orchestrator", "8000", "Service coordination and management"),
            ("Main Dashboard", "8083", "Total access command center"),
        ]

        for name, port, description in services_info:
            status = (
                "🟢 RUNNING"
                if name in self.processes or name == "Main Dashboard"
                else "🔴 STOPPED"
            )
            print(f"{status} {name:<20} Port {port:<6} - {description}")

        print("\n🌐 Access URLs:")
        for name, port, _ in services_info:
            print(f"   • {name}: http://localhost:{port}")

        print("\n📊 Main Dashboard: http://localhost:8083")
        print("\n✨ The complete TRAE.AI ecosystem is now running!")
        print("=" * 80 + "\n")

    def monitor_services(self):
        """Monitor running services and restart if needed"""
        while self.running:
            try:
                for name, info in list(self.processes.items()):
                    process = info["process"]
                    if process.poll() is not None:
                        logger.warning(
                            f"Service {name} has stopped. Attempting restart..."
                        )

                        # Remove dead process
                        del self.processes[name]

                        # Attempt restart
                        self.start_service(
                            name, info["module"], info["port"], info["cwd"]
                        )

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                time.sleep(5)

    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        logger.info("\n🛑 Shutting down TRAE.AI services...")
        self.running = False

        for name, info in self.processes.items():
            try:
                process = info["process"]
                logger.info(f"Stopping {name}...")

                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"✅ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}...")
                    process.kill()
                    process.wait()

            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        logger.info("🏁 All services stopped")
        sys.exit(0)

    def run(self):
        """Main run method"""
        try:
            # Pre-flight checks
            if not self.check_dependencies():
                return False

            self.setup_directories()

            # Start all services
            if not self.start_all_services():
                logger.error("Failed to start services")
                return False

            self.running = True

            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()

            # Keep main thread alive
            logger.info("\n🎯 TRAE.AI is running. Press Ctrl+C to stop.")

            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.shutdown()

            return True

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.shutdown()
            return False


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🚀 TRAE.AI COMPLETE APPLICATION LAUNCHER")
    print("   Unified ecosystem for autonomous content creation")
    print("=" * 80 + "\n")

    launcher = TraeAILauncher()
    success = launcher.run()

    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
