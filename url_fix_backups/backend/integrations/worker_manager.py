#!/usr / bin / env python3
"""
Distributed Worker Manager

This module provides utilities for managing Celery workers across different machines
in the distributed processing system. It handles worker lifecycle, monitoring,
and cross - platform deployment.

Features:
- Worker startup and shutdown management
- Health monitoring and heartbeat tracking
- Cross - platform worker deployment
- Load balancing and resource optimization
- Automatic worker recovery and failover

Author: AI Assistant
Date: 2024
"""

import json
import logging
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import distributed processing components

from distributed_processing import DistributedProcessingSystem, WorkerCapabilities

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class WorkerProcess:
    """Worker process information."""

    worker_id: str
    process_id: int
    command: List[str]
    started_at: datetime
    status: str  # 'starting', 'running', 'stopping', 'stopped', 'failed'
    queue_names: List[str]
    concurrency: int
    last_heartbeat: Optional[datetime] = None
    restart_count: int = 0
    max_restarts: int = 3


class WorkerManager:
    """Manages Celery workers across the distributed system."""


    def __init__(self, dps: DistributedProcessingSystem):
        """
        Initialize the worker manager.

        Args:
            dps: Distributed processing system instance
        """
        self.dps = dps
        self.workers: Dict[str, WorkerProcess] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()

        # Get machine capabilities
        self.machine_capabilities = self.dps.get_worker_capabilities()

        # Platform - specific settings
        self.platform = platform.system().lower()
        self.python_executable = sys.executable

        logging.getLogger(__name__).info(f"Worker Manager initialized for {self.platform} platform")


    def start_worker(self, queue_names: List[str], concurrency: int = None) -> str:
        """Start a new Celery worker.

        Args:
            queue_names: List of queue names for this worker
            concurrency: Number of concurrent processes (auto - detect if None)

        Returns:
            Worker ID
        """
        if concurrency is None:
            concurrency = min(
                self.machine_capabilities.cpu_cores,
                    self.machine_capabilities.max_concurrent_tasks,
                    )

        worker_id = f"worker_{self.platform}_{int(time.time())}"

        # Build Celery worker command
            command = self._build_worker_command(worker_id, queue_names, concurrency)

        try:
            # Start the worker process
            logging.getLogger(__name__).info(f"Starting worker {worker_id} with queues: {queue_names}")

            process = subprocess.Popen(
                command,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    text = True,
                    bufsize = 1,
                    universal_newlines = True,
                    )

            # Create worker process record
            worker_process = WorkerProcess(
                worker_id = worker_id,
                    process_id = process.pid,
                    command = command,
                    started_at = datetime.now(),
                    status="starting",
                    queue_names = queue_names,
                    concurrency = concurrency,
                    )

            self.workers[worker_id] = worker_process

            # Start monitoring if not already running
            if not self.monitoring_thread or not self.monitoring_thread.is_alive():
                self.start_monitoring()

            logging.getLogger(__name__).info(f"Worker {worker_id} started with PID {process.pid}")
        except Exception as e:
            pass
        return worker_id

        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to start worker {worker_id}: {e}")
            raise


    def _build_worker_command(:
        self, worker_id: str, queue_names: List[str], concurrency: int
    ) -> List[str]:
        """Build Celery worker command.

        Args:
            worker_id: Unique worker identifier
            queue_names: List of queues to consume from
            concurrency: Number of concurrent processes

        Returns:
            Command as list of strings
        """
        command = [
            self.python_executable,
                "-m",
                "celery",
                "-A",
                "distributed_processing",
                "worker",
                "--hostname",
                f"{worker_id}@%h",
                "--queues",
                ",".join(queue_names),
                "--concurrency",
                str(concurrency),
                "--loglevel",
                "info",
                "--without - gossip",
                "--without - mingle",
                "--without - heartbeat",
                ]

        # Platform - specific optimizations
        if self.platform == "darwin":  # macOS
            command.extend(["--pool", "prefork"])
        elif self.platform == "win32":  # Windows
            command.extend(["--pool", "solo"])  # Windows doesn't support prefork well
        else:  # Linux
            command.extend(["--pool", "prefork"])

        return command


    def stop_worker(self, worker_id: str, timeout: int = 30) -> bool:
        """Stop a specific worker.

        Args:
            worker_id: ID of worker to stop
            timeout: Timeout in seconds for graceful shutdown

        Returns:
            True if worker stopped successfully
        """
        if worker_id not in self.workers:
            logging.getLogger(__name__).warning(f"Worker {worker_id} not found")
        return False

        worker = self.workers[worker_id]
        worker.status = "stopping"

        try:
            # Try graceful shutdown first
            if self.platform == "win32":
                # Windows
                subprocess.run(
                    ["taskkill", "/PID", str(worker.process_id), "/T"],
                        timeout = timeout,
                        check = False,
                        )
            else:
                # Unix - like systems
                os.kill(worker.process_id, signal.SIGTERM)

                # Wait for graceful shutdown
                for _ in range(timeout):
                    try:
                        os.kill(worker.process_id, 0)  # Check if process exists
                        time.sleep(1)
                    except OSError:
                        break  # Process has terminated
                else:
                    # Force kill if still running
                    os.kill(worker.process_id, signal.SIGKILL)

            worker.status = "stopped"
            logging.getLogger(__name__).info(f"Worker {worker_id} stopped")
        except Exception as e:
            pass
        return True

        except Exception as e:
            logging.getLogger(__name__).error(f"Error stopping worker {worker_id}: {e}")
            worker.status = "failed"
        return False


    def stop_all_workers(self, timeout: int = 30) -> Dict[str, bool]:
        """Stop all managed workers.

        Args:
            timeout: Timeout in seconds for each worker

        Returns:
            Dictionary mapping worker IDs to success status
        """
        results = {}

        for worker_id in list(self.workers.keys()):
            results[worker_id] = self.stop_worker(worker_id, timeout)

        # Stop monitoring
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.shutdown_event.set()
            self.monitoring_thread.join(timeout = 10)

        return results


    def restart_worker(self, worker_id: str) -> bool:
        """Restart a specific worker.

        Args:
            worker_id: ID of worker to restart

        Returns:
            True if restart successful
        """
        if worker_id not in self.workers:
            logging.getLogger(__name__).warning(f"Worker {worker_id} not found")
        return False

        worker = self.workers[worker_id]

        # Check restart limit
        if worker.restart_count >= worker.max_restarts:
            logging.getLogger(__name__).error(
                f"Worker {worker_id} exceeded max restarts ({worker.max_restarts})"
            )
            worker.status = "failed"
        return False

        # Stop the worker
        if not self.stop_worker(worker_id):
        return False

        # Wait a moment
        time.sleep(2)

        # Start new worker with same configuration
        try:
            new_worker_id = self.start_worker(worker.queue_names, worker.concurrency)

            # Update restart count
            if new_worker_id in self.workers:
                self.workers[new_worker_id].restart_count = worker.restart_count + 1

            # Remove old worker record
            del self.workers[worker_id]

            logging.getLogger(__name__).info(f"Worker {worker_id} restarted as {new_worker_id}")
        except Exception as e:
            pass
        return True

        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to restart worker {worker_id}: {e}")
        return False


    def start_monitoring(self):
        """Start worker monitoring thread."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.shutdown_event.clear()
        self.monitoring_thread = threading.Thread(
            target = self._monitor_workers, daemon = True
        )
        self.monitoring_thread.start()

        logging.getLogger(__name__).info("Worker monitoring started")


    def _monitor_workers(self):
        """Monitor worker health and restart failed workers."""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()

                for worker_id, worker in list(self.workers.items()):
                    # Check if process is still running
                    if not self._is_process_running(worker.process_id):
                        if worker.status in ["running", "starting"]:
                            logging.getLogger(__name__).warning(
                                f"Worker {worker_id} process died unexpectedly"
                            )
                            worker.status = "failed"

                            # Attempt restart if within limits
                            if worker.restart_count < worker.max_restarts:
                                logging.getLogger(__name__).info(f"Attempting to restart worker {worker_id}")
                                self.restart_worker(worker_id)
                            else:
                                logging.getLogger(__name__).error(
                                    f"Worker {worker_id} exceeded restart limit"
                                )

                    # Update worker status based on heartbeat
                    elif worker.status == "starting":
                        # Check if worker has been starting for too long
                        if current_time - worker.started_at > timedelta(minutes = 2):
                            worker.status = (
                                "running"  # Assume it's running if process exists
                            )

                    # Update heartbeat
                    worker.last_heartbeat = current_time

                # Sleep before next check
                self.shutdown_event.wait(30)  # Check every 30 seconds

            except Exception as e:
                logging.getLogger(__name__).error(f"Error in worker monitoring: {e}")
                self.shutdown_event.wait(60)  # Wait longer on error


    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running
        """
        try:
            if self.platform == "win32":
                # Windows
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"], capture_output = True, text = True
                )
        except Exception as e:
            pass
        return str(pid) in result.stdout
            else:
                # Unix - like systems
                os.kill(pid, 0)  # Send signal 0 to check if process exists
        return True
        except (OSError, subprocess.SubprocessError):
        return False


    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all managed workers.

        Returns:
            Worker status information
        """
        status = {
            "total_workers": len(self.workers),
            "running_workers": len(
                [w for w in self.workers.values() if w.status == "running"]
            ),
            "failed_workers": len(
                [w for w in self.workers.values() if w.status == "failed"]
            ),
            "workers": [],
        }

        for worker in self.workers.values():
            worker_info = {
            "worker_id": worker.worker_id,
            "process_id": worker.process_id,
            "status": worker.status,
            "queues": worker.queue_names,
            "concurrency": worker.concurrency,
            "started_at": worker.started_at.isoformat(),
            "restart_count": worker.restart_count,
            "last_heartbeat": (
                    worker.last_heartbeat.isoformat() if worker.last_heartbeat else None
                ),
        }
            status["workers"].append(worker_info)

        return status


    def auto_scale_workers(self, target_queues: Dict[str, int]) -> Dict[str, str]:
        """Automatically scale workers based on queue requirements.

        Args:
            target_queues: Dictionary mapping queue names to desired worker counts

        Returns:
            Dictionary with scaling actions taken
        """
        actions = {}

        # Count current workers per queue
        current_queues = {}
        for worker in self.workers.values():
            if worker.status == "running":
                for queue in worker.queue_names:
                    current_queues[queue] = current_queues.get(queue, 0) + 1

        # Scale up / down as needed
        for queue_name, target_count in target_queues.items():
            current_count = current_queues.get(queue_name, 0)

            if current_count < target_count:
                # Scale up
                needed = target_count - current_count
                for _ in range(needed):
                    try:
                        worker_id = self.start_worker([queue_name])
                        actions[f"scale_up_{queue_name}"] = (
                            f"Started worker {worker_id}"
                        )
                    except Exception as e:
                        actions[f"scale_up_error_{queue_name}"] = str(e)

            elif current_count > target_count:
                # Scale down
                excess = current_count - target_count
                workers_to_stop = []

                for worker in self.workers.values():
                    if (
                        worker.status == "running"
                        and queue_name in worker.queue_names
                        and len(workers_to_stop) < excess
                    ):
                        workers_to_stop.append(worker.worker_id)

                for worker_id in workers_to_stop:
                    if self.stop_worker(worker_id):
                        actions[f"scale_down_{queue_name}"] = (
                            f"Stopped worker {worker_id}"
                        )

        return actions

# CLI interface for worker management


def main():
    """Command - line interface for worker management."""

    import argparse

    parser = argparse.ArgumentParser(description="Distributed Worker Manager")
    parser.add_argument(
        "action",
            choices=["start", "stop", "restart", "status", "monitor"],
            help="Action to perform",
            )
    parser.add_argument("--worker - id", help="Specific worker ID (for stop / restart)")
    parser.add_argument(
        "--queues", nargs="+", default=["general"], help="Queue names for new workers"
    )
    parser.add_argument("--concurrency", type = int, help="Worker concurrency")
    parser.add_argument("--broker - url", help="Celery broker URL")

    args = parser.parse_args()

    # Initialize distributed processing system
    dps = DistributedProcessingSystem(broker_url = args.broker_url)
    manager = WorkerManager(dps)

    try:
        if args.action == "start":
            worker_id = manager.start_worker(args.queues, args.concurrency)
            print(f"Started worker: {worker_id}")

        elif args.action == "stop":
            if args.worker_id:
                success = manager.stop_worker(args.worker_id)
                print(
                    f"Stop worker {args.worker_id}: {'Success' if success else 'Failed'}"
                )
            else:
                results = manager.stop_all_workers()
                for worker_id, success in results.items():
                    print(
                        f"Stop worker {worker_id}: {'Success' if success else 'Failed'}"
                    )

        elif args.action == "restart":
            if not args.worker_id:
                print("Worker ID required for restart")
                return
            success = manager.restart_worker(args.worker_id)
            print(
                f"Restart worker {args.worker_id}: {'Success' if success else 'Failed'}"
            )

        elif args.action == "status":
            status = manager.get_worker_status()
            print(json.dumps(status, indent = 2))

        elif args.action == "monitor":
            print("Starting worker monitoring... (Press Ctrl + C to stop)")
            manager.start_monitoring()
            try:
                while True:
                    time.sleep(10)
                    status = manager.get_worker_status()
                    print(
                        f"Workers: {status['running_workers']}/{status['total_workers']} running"
                    )
            except KeyboardInterrupt:
                print("\\nStopping monitoring...")
                manager.stop_all_workers()

    except KeyboardInterrupt:
        print("\\nShutting down...")
        manager.stop_all_workers()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())