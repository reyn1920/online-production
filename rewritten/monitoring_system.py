#!/usr/bin/env python3
""""""
Comprehensive Monitoring System for TRAE.AI Production
Detects stuck processes, initialization loops, and connection failures
""""""

import asyncio
import json
import logging
import subprocess
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List

import httpx
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("monitoring.log"), logging.StreamHandler()],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )
logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Monitors system processes for stuck or looping behavior"""

    def __init__(self):
        self.process_history = defaultdict(deque)
        self.restart_counts = defaultdict(int)
        self.last_check = time.time()
        self.loop_detection_window = 300  # 5 minutes
        self.max_restarts_per_hour = 5

    def detect_initialization_loop(
        self, process_name: str, log_patterns: List[str]
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Detect if a process is stuck in an initialization loop"""
        try:
            # Check for repeated initialization messages in logs
            current_time = time.time()

            # Look for processes with the given name
            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    if process_name in " ".join(proc.info["cmdline"] or []):
                        # Check if process has been restarting frequently
                        create_time = proc.info["create_time"]

                        # Add to history
                        self.process_history[process_name].append(create_time)

                        # Keep only recent entries
                        cutoff_time = current_time - self.loop_detection_window
                        while (
                            self.process_history[process_name]
                            and self.process_history[process_name][0] < cutoff_time
# BRACKET_SURGEON: disabled
#                         ):
                            self.process_history[process_name].popleft()

                        # Check for loop pattern (multiple restarts in short time)
                        if len(self.process_history[process_name]) >= 3:
                            logger.warning(
                                f"🔄 Initialization loop detected for {process_name}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            logger.warning(
                                f"Process restarted {len(self.process_history[process_name])} times in {self.loop_detection_window}s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Error detecting initialization loop: {e}")

        return False

    def kill_stuck_process(self, process_name: str) -> bool:
        """Kill a stuck process"""
        try:
            killed = False
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if process_name in " ".join(proc.info["cmdline"] or []):
                        logger.info(
                            f"🔪 Killing stuck process: {process_name} (PID: {proc.info['pid']})"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        proc.kill()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return killed
        except Exception as e:
            logger.error(f"Error killing stuck process: {e}")
            return False


class ServiceHealthMonitor:
    """Monitors service health and availability"""

    def __init__(self):
        self.services = {
            "main_api": {"url": "http://localhost:8000/health", "timeout": 5},
            "minimal_server": {"url": "http://localhost:8000/health", "timeout": 3},
# BRACKET_SURGEON: disabled
#         }
        self.health_history = defaultdict(list)

    async def check_service_health(
        self, service_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check health of a specific service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(config["url"], timeout=config["timeout"])
                healthy = response.status_code == 200

                result = {
                    "service": service_name,
                    "healthy": healthy,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

                if healthy:
                    try:
                        result["data"] = response.json()
                    except Exception:
                        result["data"] = response.text[:200]

                return result

        except httpx.RequestError as e:
            return {
                "service": service_name,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all monitored services"""
        results = {}

        for service_name, config in self.services.items():
            result = await self.check_service_health(service_name, config)
            results[service_name] = result

            # Store in history
            self.health_history[service_name].append(result)

            # Keep only last 100 checks
            if len(self.health_history[service_name]) > 100:
                self.health_history[service_name] = self.health_history[service_name][
                    -100:
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        return results


class SelfHealingSystem:
    """Implements self - healing mechanisms"""

    def __init__(self):
        self.process_monitor = ProcessMonitor()
        self.health_monitor = ServiceHealthMonitor()
        self.healing_actions = {
            "restart_minimal_server": self._restart_minimal_server,
            "kill_stuck_main_server": self._kill_stuck_main_server,
            "start_emergency_server": self._start_emergency_server,
# BRACKET_SURGEON: disabled
#         }
        self.last_healing_action = {}
        self.healing_cooldown = 60  # 1 minute between healing actions

    def _restart_minimal_server(self) -> bool:
        """Restart the minimal server"""
        try:
            logger.info("🔄 Restarting minimal server...")

            # Kill existing minimal server
            subprocess.run(["pkill", "-f", "minimal_server.py"], check=False)
            time.sleep(2)

            # Start new minimal server
            subprocess.Popen(
                ["python3", "minimal_server.py"],
                cwd="/Users/thomasbrianreynolds/online production",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            logger.info("✅ Minimal server restart initiated")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to restart minimal server: {e}")
            return False

    def _kill_stuck_main_server(self) -> bool:
        """Kill stuck main server processes"""
        try:
            logger.info("🔪 Killing stuck main server processes...")

            # Kill main.py processes
            subprocess.run(["pkill", "-f", "main.py"], check=False)
            subprocess.run(["pkill", "-f", "run_simple.py"], check=False)

            logger.info("✅ Stuck processes killed")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to kill stuck processes: {e}")
            return False

    def _start_emergency_server(self) -> bool:
        """Start emergency minimal server"""
        try:
            logger.info("🚨 Starting emergency server...")

            subprocess.Popen(
                ["python3", "minimal_server.py"],
                cwd="/Users/thomasbrianreynolds/online production",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            logger.info("✅ Emergency server started")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start emergency server: {e}")
            return False

    async def perform_healing_check(self) -> Dict[str, Any]:
        """Perform comprehensive healing check"""
        current_time = time.time()
        healing_report = {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": [],
            "issues_detected": [],
            "service_status": {},
# BRACKET_SURGEON: disabled
#         }

        # Check service health
        service_results = await self.health_monitor.check_all_services()
        healing_report["service_status"] = service_results

        # Check for initialization loops
        if self.process_monitor.detect_initialization_loop(
            "main.py", ["Agent", "initialized"]
# BRACKET_SURGEON: disabled
#         ):
            healing_report["issues_detected"].append("initialization_loop_main_py")

            # Apply healing if cooldown has passed
            if (
                current_time - self.last_healing_action.get("kill_stuck_main_server", 0)
                > self.healing_cooldown
# BRACKET_SURGEON: disabled
#             ):

                if self._kill_stuck_main_server():
                    healing_report["actions_taken"].append("killed_stuck_main_server")
                    self.last_healing_action["kill_stuck_main_server"] = current_time

        # Check if no services are healthy
        all_unhealthy = all(
            not result.get("healthy", False) for result in service_results.values()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if all_unhealthy:
            healing_report["issues_detected"].append("all_services_unhealthy")

            # Start emergency server if cooldown has passed
            if (
                current_time - self.last_healing_action.get("start_emergency_server", 0)
                > self.healing_cooldown
# BRACKET_SURGEON: disabled
#             ):

                if self._start_emergency_server():
                    healing_report["actions_taken"].append("started_emergency_server")
                    self.last_healing_action["start_emergency_server"] = current_time

        return healing_report


class MonitoringSystem:
    """Main monitoring system coordinator"""

    def __init__(self):
        self.self_healing = SelfHealingSystem()
        self.running = False
        self.check_interval = 30  # 30 seconds

    async def start_monitoring(self):
        """Start the monitoring loop"""
        logger.info("🔍 Starting comprehensive monitoring system...")
        self.running = True

        while self.running:
            try:
                # Perform healing check
                report = await self.self_healing.perform_healing_check()

                # Log significant events
                if report["issues_detected"] or report["actions_taken"]:
                    logger.info(
                        f"📊 Monitoring Report: {json.dumps(report,"
# BRACKET_SURGEON: disabled
#     indent = 2)}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                # Save report to file
                with open("monitoring_reports.jsonl", "a") as f:
                    f.write(json.dumps(report) + "\\n")

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        logger.info("🛑 Stopping monitoring system...")
        self.running = False


async def main():
    """Main monitoring function"""
    monitoring = MonitoringSystem()

    try:
        await monitoring.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    finally:
        monitoring.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())