#!/usr / bin / env python3
"""
Process Watchdog - Advanced process monitoring and management
Integrates with startup_system.py to provide comprehensive process oversight
"""

import asyncio
import json
import logging
import queue
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a monitored process"""

    pid: int
    name: str
    cmdline: List[str]
    start_time: datetime
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = "running"
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    stuck_since: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)


@dataclass
class WatchdogRule:
    """Rule for process monitoring"""

    name: str
    process_pattern: str
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 80.0
    max_response_time: float = 30.0
    stuck_threshold: int = 300  # seconds
    restart_on_stuck: bool = True
    restart_command: Optional[List[str]] = None
    enabled: bool = True


class ProcessWatchdog:
    """Advanced process watchdog with self - healing capabilities"""

    def __init__(self):
        self.processes: Dict[int, ProcessInfo] = {}
        self.rules: Dict[str, WatchdogRule] = {}
        self.running = False
        self.alert_queue = queue.Queue()
        self.stats_history: List[Dict] = []
        self.max_history = 1000

        # Performance thresholds
        self.cpu_spike_threshold = 95.0
        self.memory_leak_threshold = 85.0
        self.response_timeout = 30.0

        # Initialize default rules
        self._initialize_default_rules()

        # Create monitoring directory
        Path("logs / watchdog").mkdir(parents=True, exist_ok=True)

    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""
        self.add_rule(
            WatchdogRule(
                name="python_processes",
                process_pattern="python",
                max_cpu_percent=85.0,
                max_memory_percent=75.0,
                stuck_threshold=180,
                restart_on_stuck=True,
            )
        )

        self.add_rule(
            WatchdogRule(
                name="node_processes",
                process_pattern="node",
                max_cpu_percent=80.0,
                max_memory_percent=70.0,
                stuck_threshold=240,
            )
        )

        self.add_rule(
            WatchdogRule(
                name="uvicorn_server",
                process_pattern="uvicorn",
                max_cpu_percent=90.0,
                max_memory_percent=80.0,
                stuck_threshold=120,
                restart_on_stuck=True,
                restart_command=["python3", "main.py"],
            )
        )

    def add_rule(self, rule: WatchdogRule):
        """Add a monitoring rule"""
        self.rules[rule.name] = rule
        logger.info(f"📋 Added watchdog rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove a monitoring rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"🗑️ Removed watchdog rule: {rule_name}")

    def scan_processes(self) -> Dict[int, ProcessInfo]:
        """Scan and update process information"""
        current_processes = {}

        try:
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cmdline",
                    "create_time",
                    "cpu_percent",
                    "memory_percent",
                    "status",
                ]
            ):
                try:
                    info = proc.info
                    if not info["cmdline"]:
                        continue

                    pid = info["pid"]

                    # Check if this process matches any of our rules
                    matching_rules = self._get_matching_rules(info["name"], info["cmdline"])
                    if not matching_rules:
                        continue

                    # Create or update process info
                    if pid in self.processes:
                        process_info = self.processes[pid]
                        process_info.cpu_percent = info["cpu_percent"] or 0.0
                        process_info.memory_percent = info["memory_percent"] or 0.0
                        process_info.status = info["status"]
                    else:
                        process_info = ProcessInfo(
                            pid=pid,
                            name=info["name"],
                            cmdline=info["cmdline"],
                            start_time=datetime.fromtimestamp(info["create_time"]),
                            cpu_percent=info["cpu_percent"] or 0.0,
                            memory_percent=info["memory_percent"] or 0.0,
                            status=info["status"],
                        )

                    current_processes[pid] = process_info

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:
            logger.error(f"Error scanning processes: {e}")

        # Update our process list
        self.processes = current_processes
        return current_processes

    def _get_matching_rules(self, process_name: str, cmdline: List[str]) -> List[WatchdogRule]:
        """Get rules that match a process"""
        matching = []
        cmdline_str = " ".join(cmdline).lower()

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if (
                rule.process_pattern.lower() in process_name.lower()
                or rule.process_pattern.lower() in cmdline_str
            ):
                matching.append(rule)

        return matching

    def detect_stuck_processes(self) -> List[ProcessInfo]:
        """Detect processes that appear to be stuck"""
        stuck_processes = []
        current_time = datetime.now()

        for process in self.processes.values():
            matching_rules = self._get_matching_rules(process.name, process.cmdline)
            if not matching_rules:
                continue

            # Check for various stuck conditions
            is_stuck = False
            stuck_reason = ""

            # High CPU usage for extended period
            if process.cpu_percent > self.cpu_spike_threshold:
                if not process.stuck_since:
                    process.stuck_since = current_time
                elif (current_time - process.stuck_since).seconds > 60:
                    is_stuck = True
                    stuck_reason = f"High CPU usage: {process.cpu_percent:.1f}%"

            # High memory usage
            elif process.memory_percent > self.memory_leak_threshold:
                if not process.stuck_since:
                    process.stuck_since = current_time
                elif (current_time - process.stuck_since).seconds > 120:
                    is_stuck = True
                    stuck_reason = f"High memory usage: {process.memory_percent:.1f}%"

            # Process in uninterruptible sleep for too long
            elif process.status in ["disk - sleep", "uninterruptible"]:
                if not process.stuck_since:
                    process.stuck_since = current_time
                elif (current_time - process.stuck_since).seconds > 180:
                    is_stuck = True
                    stuck_reason = f"Uninterruptible state: {process.status}"

            else:
                # Reset stuck timer if process is behaving normally
                process.stuck_since = None

            if is_stuck:
                logger.warning(
                    f"🔒 Stuck process detected: PID {process.pid} ({process.name}) - {stuck_reason}"
                )
                stuck_processes.append(process)

        return stuck_processes

    def detect_resource_issues(self) -> Dict[str, List[ProcessInfo]]:
        """Detect processes with resource issues"""
        issues = {"high_cpu": [], "high_memory": [], "zombie": [], "unresponsive": []}

        for process in self.processes.values():
            matching_rules = self._get_matching_rules(process.name, process.cmdline)
            if not matching_rules:
                continue

            # Apply the most restrictive rule
            min_cpu_threshold = min(rule.max_cpu_percent for rule in matching_rules)
            min_memory_threshold = min(rule.max_memory_percent for rule in matching_rules)

            if process.cpu_percent > min_cpu_threshold:
                issues["high_cpu"].append(process)

            if process.memory_percent > min_memory_threshold:
                issues["high_memory"].append(process)

            if process.status == "zombie":
                issues["zombie"].append(process)

        return issues

    async def restart_process(self, process: ProcessInfo, rule: WatchdogRule) -> bool:
        """Restart a stuck or problematic process"""
        try:
            logger.info(f"🔄 Attempting to restart process: PID {process.pid} ({process.name})")

            # Kill the existing process
            try:
                proc = psutil.Process(process.pid)
                proc.terminate()

                # Wait for graceful termination
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    logger.warning(f"Process {process.pid} didn't terminate gracefully, killing...")
                    proc.kill()
                    proc.wait(timeout=5)

                logger.info(f"✅ Process {process.pid} terminated")

            except psutil.NoSuchProcess:
                logger.info(f"Process {process.pid} already terminated")

            # Restart if we have a restart command
            if rule.restart_command:
                logger.info(f"🚀 Restarting with command: {' '.join(rule.restart_command)}")

                # Start new process
                new_process = await asyncio.create_subprocess_exec(
                    *rule.restart_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                # Update restart count
                process.restart_count += 1
                process.last_restart = datetime.now()

                # Give it time to start
                await asyncio.sleep(3)

                if new_process.returncode is None:
                    logger.info(f"✅ Process restarted successfully")
                    self.alert_queue.put(
                        f"Process {process.name} (PID {process.pid}) restarted successfully"
                    )
                    return True
                else:
                    logger.error(
                        f"❌ Process restart failed with exit code: {new_process.returncode}"
                    )
                    return False
            else:
                logger.warning(f"No restart command configured for rule: {rule.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to restart process {process.pid}: {e}")
            return False

    async def monitoring_cycle(self):
        """Single monitoring cycle"""
        try:
            # Scan current processes
            processes = self.scan_processes()

            # Detect stuck processes
            stuck_processes = self.detect_stuck_processes()

            # Detect resource issues
            resource_issues = self.detect_resource_issues()

            # Handle stuck processes
            for process in stuck_processes:
                matching_rules = self._get_matching_rules(process.name, process.cmdline)
                for rule in matching_rules:
                    if rule.restart_on_stuck and rule.restart_command:
                        success = await self.restart_process(process, rule)
                        if success:
                            break

            # Log resource issues
            for issue_type, issue_processes in resource_issues.items():
                if issue_processes:
                    logger.warning(
                        f"⚠️ {issue_type.replace('_', ' ').title()} issues detected in {len(issue_processes)} processes"
                    )

            # Store statistics
            stats = {
                "timestamp": datetime.now().isoformat(),
                "total_processes": len(processes),
                "stuck_processes": len(stuck_processes),
                "resource_issues": {k: len(v) for k, v in resource_issues.items()},
                "system_cpu": psutil.cpu_percent(),
                "system_memory": psutil.virtual_memory().percent,
            }

            self.stats_history.append(stats)
            if len(self.stats_history) > self.max_history:
                self.stats_history.pop(0)

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info("🔍 Starting process watchdog monitoring")

        while self.running:
            try:
                await self.monitoring_cycle()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("🛑 Stopping process watchdog monitoring")

    def get_status(self) -> Dict:
        """Get current watchdog status"""
        return {
            "running": self.running,
            "monitored_processes": len(self.processes),
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "recent_stats": self.stats_history[-10:] if self.stats_history else [],
            "processes": {
                pid: {
                    "name": proc.name,
                    "cpu_percent": proc.cpu_percent,
                    "memory_percent": proc.memory_percent,
                    "status": proc.status,
                    "restart_count": proc.restart_count,
                    "stuck_since": (proc.stuck_since.isoformat() if proc.stuck_since else None),
                }
                for pid, proc in self.processes.items()
            },
        }


# Global watchdog instance
watchdog = ProcessWatchdog()


async def main():
    """Main entry point for standalone watchdog"""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        watchdog.stop_monitoring()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await watchdog.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        watchdog.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
