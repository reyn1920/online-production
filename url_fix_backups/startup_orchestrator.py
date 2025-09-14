#!/usr / bin / env python3
"""
TRAE.AI Startup Orchestrator

This module provides a comprehensive startup system that orchestrates all discovered
components and services in the correct order, ensuring proper initialization and
integration while following zero - cost and no - delete principles.

Orchestrated Services:
- Database initialization and schema setup
- Task queue system startup
- Specialized agents initialization
- Content generation pipeline
- Web servers (FastAPI, Flask, static)
- WebSocket connections
- Monitoring and diagnostics
- Authentication system

Author: TRAE.AI Integration System
Version: 1.0.0
Date: 2024
"""

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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import integration components
try:

    from master_integration import IntegrationConfig, get_master_integration
    from unified_api_router import UnifiedAPIRouter

except ImportError as e:
    logging.warning(f"Some integration components not available: {e}")

@dataclass


class ServiceConfig:
    """Configuration for a service"""

    name: str
    command: str
    port: Optional[int] = None
    directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory = dict)
    dependencies: List[str] = field(default_factory = list)
    health_check_url: Optional[str] = None
    startup_delay: int = 0
    critical: bool = True
    auto_restart: bool = True

@dataclass


class ServiceStatus:
    """Status of a service"""

    name: str
    status: str  # starting, running, stopped, failed
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    port: Optional[int] = None
    start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    restart_count: int = 0
    error_message: Optional[str] = None


class StartupOrchestrator:
    """
    Orchestrates the startup of all system components
    """


    def __init__(self, config_file: str = "integration_config.yaml"):
        self.config_file = config_file
        self.logger = self._setup_logging()
        self.services: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers = 10)

        # Load configuration
        self._load_configuration()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Integration components
        self.master_integration = None
        self.unified_router = None


    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok = True)

        logging.basicConfig(
            level = logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                logging.FileHandler("logs / startup_orchestrator.log"),
                    logging.StreamHandler(),
                    ],
                )
        return logging.getLogger(__name__)


    def _load_configuration(self):
        """Load configuration from YAML file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, "r") as f:
                    config = yaml.safe_load(f)
                self._parse_services_config(config)
            else:
                self.logger.warning(
                    f"Configuration file {self.config_file} not found, using defaults"
                )
                self._setup_default_services()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._setup_default_services()


    def _parse_services_config(self, config: Dict[str, Any]):
        """Parse services configuration from YAML"""
        server_config = config.get("server", {})
        services_config = server_config.get("services", {})

        # Parse each service
        for service_name, service_data in services_config.items():
            if service_name == "main_app":
                self.services["main_app"] = ServiceConfig(
                    name="main_app",
                        command = f"python -m uvicorn {service_data.get('module', 'unified_api_router:app')} --host 0.0.0.0 --port {service_data.get('port',
    8000)}",
                        port = service_data.get("port", 8000),
                        health_check_url = f"http://localhost:{service_data.get('port',
    8000)}/health",
                        critical = True,
                        )

            elif service_name == "paste_app":
                self.services["paste_app"] = ServiceConfig(
                    name="paste_app",
                        command="python paste_app.py",
                        port = service_data.get("port", 3001),
                        dependencies=["main_app"],
                        startup_delay = 2,
                        critical = False,
                        )

            elif service_name == "demo_avatar":
                self.services["demo_avatar"] = ServiceConfig(
                    name="demo_avatar",
                        command="python demo_realistic_avatar.py",
                        port = service_data.get("port", 3002),
                        dependencies=["main_app"],
                        startup_delay = 3,
                        critical = False,
                        )

            elif service_name == "static_server":
                self.services["static_server"] = ServiceConfig(
                    name="static_server",
                        command = f"python -m http.server {service_data.get('port',
    3000)}",
                        port = service_data.get("port", 3000),
                        startup_delay = 1,
                        critical = False,
                        )

        # Add additional discovered services
        self._add_discovered_services()


    def _setup_default_services(self):
        """Setup default services configuration"""
        self.services = {
            "main_app": ServiceConfig(
                name="main_app",
                    command="python -m uvicorn unified_api_router:app --host 0.0.0.0 --port 8000",
                    port = 8000,
                    health_check_url="http://localhost:8000 / health",
                    critical = True,
                    ),
                "paste_app": ServiceConfig(
                name="paste_app",
                    command="python paste_app.py",
                    port = 3001,
                    dependencies=["main_app"],
                    startup_delay = 2,
                    critical = False,
                    ),
                "demo_avatar": ServiceConfig(
                name="demo_avatar",
                    command="python demo_realistic_avatar.py",
                    port = 3002,
                    dependencies=["main_app"],
                    startup_delay = 3,
                    critical = False,
                    ),
                "static_server": ServiceConfig(
                name="static_server",
                    command="python -m http.server 3000",
                    port = 3000,
                    startup_delay = 1,
                    critical = False,
                    ),
                }

        self._add_discovered_services()


    def _add_discovered_services(self):
        """Add services discovered from the file system"""
        # Check for additional Python services
        python_services = [
            ("monitoring_service", "monitoring / performance_monitor.py"),
                ("analytics_service", "backend / analytics_agent.py"),
                ("content_scheduler", "backend / content_scheduler.py"),
                ]

        for service_name, script_path in python_services:
            if Path(script_path).exists() and service_name not in self.services:
                self.services[service_name] = ServiceConfig(
                    name = service_name,
                        command = f"python {script_path}",
                        dependencies=["main_app"],
                        startup_delay = 5,
                        critical = False,
                        auto_restart = True,
                        )


    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()


    async def initialize_integration_layer(self):
        """Initialize the master integration layer"""
        try:
            self.logger.info("Initializing master integration layer...")

            # Initialize master integration
            config = IntegrationConfig()
            self.master_integration = get_master_integration(config)

            success = await self.master_integration.initialize()
            if success:
                await self.master_integration.start_services()
                self.logger.info("Master integration layer initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize master integration layer")
                return False

        except Exception as e:
            self.logger.error(f"Integration layer initialization failed: {e}")
            return False


    def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False

        service = self.services[service_name]

        try:
            self.logger.info(f"Starting service: {service_name}")

            # Check dependencies
            for dep in service.dependencies:
                if (
                    dep not in self.service_status
                    or self.service_status[dep].status != "running"
                ):
                    self.logger.warning(
                        f"Dependency {dep} not running for service {service_name}"
                    )

            # Apply startup delay
            if service.startup_delay > 0:
                self.logger.info(
                    f"Applying startup delay of {service.startup_delay}s for {service_name}"
                )
                time.sleep(service.startup_delay)

            # Prepare environment
            env = os.environ.copy()
            env.update(service.environment)

            # Set working directory
            cwd = service.directory or os.getcwd()

            # Start the process
            process = subprocess.Popen(
                service.command.split(),
                    cwd = cwd,
                    env = env,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    text = True,
                    )

            # Update service status
            self.service_status[service_name] = ServiceStatus(
                name = service_name,
                    status="starting",
                    process = process,
                    pid = process.pid,
                    port = service.port,
                    start_time = datetime.now(),
                    )

            # Wait a moment to check if process started successfully
            time.sleep(1)

            if process.poll() is None:
                self.service_status[service_name].status = "running"
                self.logger.info(
                    f"Service {service_name} started successfully (PID: {process.pid})"
                )
                return True
            else:
                stdout, stderr = process.communicate()
                error_msg = (
                    f"Process exited immediately. STDOUT: {stdout}, STDERR: {stderr}"
                )
                self.service_status[service_name].status = "failed"
                self.service_status[service_name].error_message = error_msg
                self.logger.error(
                    f"Service {service_name} failed to start: {error_msg}"
                )
                return False

        except Exception as e:
            error_msg = f"Failed to start service {service_name}: {e}"
            self.logger.error(error_msg)

            if service_name in self.service_status:
                self.service_status[service_name].status = "failed"
                self.service_status[service_name].error_message = error_msg

            return False


    def stop_service(self, service_name: str) -> bool:
        """Stop a single service"""
        if service_name not in self.service_status:
            self.logger.warning(f"Service {service_name} not found in status")
            return True

        status = self.service_status[service_name]

        try:
            if status.process and status.process.poll() is None:
                self.logger.info(
                    f"Stopping service: {service_name} (PID: {status.pid})"
                )

                # Try graceful shutdown first
                status.process.terminate()

                # Wait for graceful shutdown
                try:
                    status.process.wait(timeout = 10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    self.logger.warning(f"Force killing service {service_name}")
                    status.process.kill()
                    status.process.wait()

                status.status = "stopped"
                self.logger.info(f"Service {service_name} stopped successfully")
                return True
            else:
                status.status = "stopped"
                return True

        except Exception as e:
            self.logger.error(f"Failed to stop service {service_name}: {e}")
            return False


    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get status of a service"""
        return self.service_status.get(service_name)


    def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        status_dict = {}

        for name, status in self.service_status.items():
            status_dict[name] = {
                "status": status.status,
                    "pid": status.pid,
                    "port": status.port,
                    "start_time": (
                    status.start_time.isoformat() if status.start_time else None
                ),
                    "restart_count": status.restart_count,
                    "error_message": status.error_message,
                    }

        return status_dict


    def health_check_service(self, service_name: str) -> bool:
        """Perform health check on a service"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]
        status = self.service_status.get(service_name)

        if not status or status.status != "running":
            return False

        # Check if process is still running
        if status.process and status.process.poll() is not None:
            status.status = "failed"
            return False

        # HTTP health check if URL is provided
        if service.health_check_url:
            try:

                import requests

                response = requests.get(service.health_check_url, timeout = 5)
                healthy = response.status_code == 200
                status.last_health_check = datetime.now()
                return healthy
            except Exception as e:
                self.logger.warning(f"Health check failed for {service_name}: {e}")
                return False

        return True


    def monitor_services(self):
        """Monitor services and restart if needed"""
        while not self.shutdown_event.is_set():
            try:
                for service_name, service in self.services.items():
                    if service_name in self.service_status:
                        status = self.service_status[service_name]

                        # Check if service is healthy
                        if (
                            status.status == "running"
                            and not self.health_check_service(service_name)
                        ):
                            self.logger.warning(
                                f"Service {service_name} failed health check"
                            )

                            if service.auto_restart and status.restart_count < 3:
                                self.logger.info(f"Restarting service {service_name}")
                                self.stop_service(service_name)
                                time.sleep(2)
                                if self.start_service(service_name):
                                    status.restart_count += 1
                                else:
                                    self.logger.error(
                                        f"Failed to restart service {service_name}"
                                    )

                # Wait before next check
                time.sleep(30)

            except Exception as e:
                self.logger.error(f"Error in service monitoring: {e}")
                time.sleep(10)


    async def start_all_services(self):
        """Start all services in dependency order"""
        self.logger.info("Starting all services...")

        # First, initialize the integration layer
        integration_success = await self.initialize_integration_layer()
        if not integration_success:
            self.logger.warning(
                "Integration layer failed to initialize, continuing with services..."
            )

        # Build dependency graph and start services in order
        started_services = set()
        remaining_services = set(self.services.keys())

        while remaining_services:
            # Find services with satisfied dependencies
            ready_services = []
            for service_name in remaining_services:
                service = self.services[service_name]
                if all(dep in started_services for dep in service.dependencies):
                    ready_services.append(service_name)

            if not ready_services:
                # No services ready, check for circular dependencies
                self.logger.warning(
                    f"Possible circular dependencies in: {remaining_services}"
                )
                # Start remaining services anyway
                ready_services = list(remaining_services)

            # Start ready services
            for service_name in ready_services:
                success = self.start_service(service_name)
                if success or not self.services[service_name].critical:
                    started_services.add(service_name)
                    remaining_services.remove(service_name)
                else:
                    self.logger.error(
                        f"Critical service {service_name} failed to start"
                    )
                    return False

        self.logger.info("All services started successfully")
        return True


    def stop_all_services(self):
        """Stop all services in reverse dependency order"""
        self.logger.info("Stopping all services...")

        # Stop services in reverse order
        service_names = list(self.services.keys())
        service_names.reverse()

        for service_name in service_names:
            self.stop_service(service_name)

        # Shutdown integration layer
        if self.master_integration:
            try:
                asyncio.create_task(self.master_integration.shutdown())
            except Exception as e:
                self.logger.error(f"Error shutting down integration layer: {e}")

        self.logger.info("All services stopped")


    def print_status_summary(self):
        """Print a summary of all service statuses"""
        print("\\n" + "=" * 60)
        print("TRAE.AI System Status Summary")
        print("=" * 60)

        for service_name, status in self.service_status.items():
            status_icon = {
                "running": "🟢",
                    "starting": "🟡",
                    "stopped": "🔴",
                    "failed": "❌",
                    }.get(status.status, "❓")

            port_info = f" (Port: {status.port})" if status.port else ""
            print(
                f"{status_icon} {service_name:<20} {status.status.upper():<10}{port_info}"
            )

            if status.error_message:
                print(f"   Error: {status.error_message}")

        print("\\n" + "=" * 60)
        print("Access Points:")
        print("Main Dashboard: http://localhost:8000")
        print("API Documentation: http://localhost:8000 / docs")
        print("Static Files: http://localhost:3000")
        print("Paste App: http://localhost:3001")
        print("Demo Avatar: http://localhost:3002")
        print("=" * 60 + "\\n")


    async def run(self):
        """Main run method"""
        try:
            self.logger.info("TRAE.AI Startup Orchestrator starting...")

            # Start all services
            success = await self.start_all_services()
            if not success:
                self.logger.error("Failed to start all services")
                return 1

            # Start monitoring in background
            monitor_thread = threading.Thread(target = self.monitor_services,
    daemon = True)
            monitor_thread.start()

            # Print status summary
            self.print_status_summary()

            self.logger.info("All systems operational. Press Ctrl + C to shutdown.")

            # Wait for shutdown signal
            while not self.shutdown_event.is_set():
                time.sleep(1)

            return 0

        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
            return 0
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            return 1
        finally:
            self.stop_all_services()
            self.executor.shutdown(wait = True)


async def main():
    """Main entry point"""
    orchestrator = StartupOrchestrator()
    return await orchestrator.run()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)