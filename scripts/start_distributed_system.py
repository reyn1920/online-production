#!/usr/bin/env python3
"""
Distributed Processing System Startup Script

Orchestrates the startup of the distributed processing system across
multiple platforms (macOS, Windows, Linux) with automatic worker discovery
and configuration.
"""

import argparse
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from integrations.distributed_config import config
from integrations.distributed_processing import DistributedProcessingSystem
from integrations.worker_manager import WorkerManager

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.monitoring.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DistributedSystemOrchestrator:
    """Orchestrates the distributed processing system startup"""

    def __init__(self):
        self.worker_manager = WorkerManager()
        self.processing_system = DistributedProcessingSystem()
        self.running_processes = []
        self.shutdown_requested = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
        self.shutdown()

    def start_broker(self) -> bool:
        """Start message broker if needed"""
        logger.info("Checking message broker status...")

        if config.broker.type == "redis":
            return self._start_redis()
        elif config.broker.type == "rabbitmq":
            return self._start_rabbitmq()
        else:
            logger.warning(f"Unsupported broker type: {config.broker.type}")
            return False

    def _start_redis(self) -> bool:
        """Start Redis server if not running"""
        try:
            # Check if Redis is already running
            result = subprocess.run(
                ["redis-cli", "ping"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and "PONG" in result.stdout:
                logger.info("Redis is already running")
                return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try to start Redis
        logger.info("Starting Redis server...")

        system = platform.system().lower()

        if system == "darwin":
            # macOS - try Homebrew first
            redis_cmd = ["redis-server"]
            try:
                process = subprocess.Popen(
                    redis_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                self.running_processes.append(process)
                time.sleep(2)  # Give Redis time to start

                # Verify it started
                result = subprocess.run(
                    ["redis-cli", "ping"], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    logger.info("Redis started successfully")
                    return True

            except FileNotFoundError:
                logger.error("Redis not found. Install with: brew install redis")

        elif system == "windows":
            # Windows - assume Redis is installed or use Docker
            logger.info(
                "On Windows, please ensure Redis is running manually or use Docker"
            )
            return False

        elif system == "linux":
            # Linux - try systemctl or direct command
            try:
                subprocess.run(["sudo", "systemctl", "start", "redis"], check=True)
                logger.info("Redis started via systemctl")
                return True
            except subprocess.CalledProcessError:
                logger.warning("Could not start Redis via systemctl")

        return False

    def _start_rabbitmq(self) -> bool:
        """Start RabbitMQ server if not running"""
        logger.info("RabbitMQ support not implemented yet")
        return False

    def start_monitoring(self):
        """Start monitoring services"""
        if not config.monitoring.enable_prometheus:
            return

        logger.info("Starting monitoring services...")

        # Start Flower for Celery monitoring
        try:
            flower_cmd = [
                "celery",
                "flower",
                "--broker",
                config.broker.get_url(),
                "--port",
                "5555",
            ]

            process = subprocess.Popen(
                flower_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.running_processes.append(process)
            logger.info("Flower monitoring started on port 5555")

        except FileNotFoundError:
            logger.warning("Flower not found. Install with: pip install flower")

    def start_workers(self, worker_count: Optional[int] = None) -> bool:
        """Start Celery workers"""
        logger.info("Starting Celery workers...")

        worker_count = worker_count or config.worker.max_workers

        try:
            # Start workers using WorkerManager
            success = self.worker_manager.start_workers(
                count=worker_count,
                queues=config.worker.queues,
                capabilities=config.worker.capabilities,
            )

            if success:
                logger.info(f"Started {worker_count} workers successfully")
                return True
            else:
                logger.error("Failed to start workers")
                return False

        except Exception as e:
            logger.error(f"Error starting workers: {e}")
            return False

    def start_web_interface(self):
        """Start web interface for system management"""
        logger.info("Starting web interface...")

        # This would start a Flask/FastAPI web interface
        # For now, just log the intention
        logger.info("Web interface would be available at http://localhost:8080")

    def health_check(self) -> Dict[str, bool]:
        """Perform system health check"""
        health = {"broker": False, "workers": False, "monitoring": False}

        # Check broker
        try:
            if config.broker.type == "redis":
                result = subprocess.run(
                    ["redis-cli", "ping"], capture_output=True, text=True, timeout=5
                )
                health["broker"] = result.returncode == 0
        except BaseException:
            pass

        # Check workers
        worker_status = self.worker_manager.get_worker_status()
        health["workers"] = len(worker_status.get("active", [])) > 0

        # Check monitoring
        health["monitoring"] = config.monitoring.enable_prometheus

        return health

    def display_status(self):
        """Display system status"""
        print("\n" + "=" * 60)
        print("DISTRIBUTED PROCESSING SYSTEM STATUS")
        print("=" * 60)

        # System info
        print(f"Platform: {config.worker.platform}")
        print(f"Worker Name: {config.worker.name}")
        print(f"Capabilities: {', '.join(config.worker.capabilities)}")
        print(f"Max Workers: {config.worker.max_workers}")

        # Health check
        health = self.health_check()
        print("\nHealth Status:")
        for component, status in health.items():
            status_icon = "✅" if status else "❌"
            print(f"  {component.capitalize()}: {status_icon}")

        # Worker status
        worker_status = self.worker_manager.get_worker_status()
        print(f"\nActive Workers: {len(worker_status.get('active', []))}")
        print(f"Failed Workers: {len(worker_status.get('failed', []))}")

        # URLs
        print("\nAccess URLs:")
        print(f"  Flower Monitoring: http://localhost:5555")
        print(f"  System Dashboard: http://localhost:8080")
        print(
            f"  Prometheus Metrics: http://localhost:{config.monitoring.prometheus_port}"
        )

        print("=" * 60)

    def shutdown(self):
        """Shutdown the distributed system"""
        logger.info("Shutting down distributed processing system...")

        # Stop workers
        self.worker_manager.stop_all_workers()

        # Stop other processes
        for process in self.running_processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            except BaseException:
                pass

        logger.info("Shutdown complete")

    def run(self, args):
        """Main run method"""
        logger.info("Starting Distributed Processing System...")

        # Start broker if needed
        if args.start_broker:
            if not self.start_broker():
                logger.error("Failed to start message broker")
                if not args.force:
                    return False

        # Start monitoring
        if args.monitoring:
            self.start_monitoring()

        # Start workers
        if not self.start_workers(args.workers):
            logger.error("Failed to start workers")
            if not args.force:
                return False

        # Start web interface
        if args.web_interface:
            self.start_web_interface()

        # Display status
        self.display_status()

        if args.daemon:
            logger.info("Running in daemon mode. Press Ctrl+C to stop.")
            try:
                while not self.shutdown_requested:
                    time.sleep(10)
                    # Periodic health check
                    health = self.health_check()
                    if not any(health.values()):
                        logger.warning("System health check failed")
            except KeyboardInterrupt:
                pass
        else:
            logger.info("System started. Use --daemon to run continuously.")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Distributed Processing System Startup Script"
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        help="Number of workers to start (default: auto-detect)",
    )

    parser.add_argument(
        "--start-broker",
        "-b",
        action="store_true",
        help="Start message broker if not running",
    )

    parser.add_argument(
        "--monitoring", "-m", action="store_true", help="Start monitoring services"
    )

    parser.add_argument(
        "--web-interface", "-ui", action="store_true", help="Start web interface"
    )

    parser.add_argument(
        "--daemon", "-d", action="store_true", help="Run in daemon mode"
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Continue even if some components fail to start",
    )

    parser.add_argument("--config", "-c", help="Path to configuration file")

    parser.add_argument(
        "--status", "-s", action="store_true", help="Show system status and exit"
    )

    args = parser.parse_args()

    # Load custom config if provided
    if args.config:
        global config
        from integrations.distributed_config import DistributedConfig

        config = DistributedConfig(args.config)

    orchestrator = DistributedSystemOrchestrator()

    if args.status:
        orchestrator.display_status()
        return

    try:
        success = orchestrator.run(args)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    main()
