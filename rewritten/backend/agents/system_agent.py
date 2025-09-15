#!/usr/bin/env python3
""""""
TRAE.AI System Agent - The Chief Engineer

The "industrial immune system" that runs Autonomous Diagnosis and Repair (ADR)
protocol and watchdog "heartbeat" system to ensure all other agents are always
online and healthy. Implements aggressive technical debt management.
""""""

import json
import logging
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from .base_agents import BaseAgent

# Import dashboard action decorator
try:

    import sys

    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    from app.actions import dashboard_action

except ImportError:
    # Fallback decorator if dashboard not available


    def dashboard_action(doc = None, method="POST", public = True):


        def decorator(func):
            func._dash_action = True
            func._dash_doc = doc
            func._dash_method = method
            func._dash_public = public
        return func

        return decorator

@dataclass


class SystemHealth:
    """System health metrics"""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    agent_status: Dict[str, bool]
    service_status: Dict[str, bool]
    error_count: int
    uptime_seconds: int


    def overall_health_score(self) -> float:
        """Calculate overall system health score (0 - 1)"""
        # Weight factors
        cpu_score = max(0, 1 - (self.cpu_usage/100))
        memory_score = max(0, 1 - (self.memory_usage/100))
        disk_score = max(0, 1 - (self.disk_usage/100))

        # Agent health
        agent_health = sum(self.agent_status.values())/max(1, len(self.agent_status))

        # Service health
        service_health = sum(self.service_status.values())/max(
            1, len(self.service_status)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Error penalty
        error_penalty = max(0, 1 - (self.error_count/100))

        return (
            cpu_score * 0.2
            + memory_score * 0.2
            + disk_score * 0.1
            + agent_health * 0.25
            + service_health * 0.15
            + error_penalty * 0.1
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

@dataclass


class DiagnosticResult:
    """Result of system diagnostic"""

    component: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    suggested_action: Optional[str]
    confidence: float
    timestamp: datetime

@dataclass


class RepairAction:
    """Automated repair action"""

    action_id: str
    component: str
    action_type: str
    description: str
    command: Optional[str]
    success: bool
    timestamp: datetime
    execution_time: float


class SystemAgent(BaseAgent):
    """The Chief Engineer - Autonomous system management and repair"""


    def __init__(
        self,
        db_path: str = "data/right_perspective.db",
        agent_id: str = "SystemAgent",
        name: str = "System Management Agent",
        main_loop = None,
# BRACKET_SURGEON: disabled
#     ):
        super().__init__(agent_id)
        self.name = name
        self.db_path = db_path
        self.main_loop = main_loop  # Reference to main event loop
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_database()

        # System monitoring parameters
        self.heartbeat_interval = 30  # seconds
        self.health_check_interval = 60  # seconds
        self.critical_threshold = 0.3  # Health score below this triggers emergency
        self.warning_threshold = 0.6  # Health score below this triggers warning

        # Watchdog system parameters
        self.watchdog_enabled = os.getenv("WATCHDOG_ENABLED", "true").lower() == "true"
        self.watchdog_threshold = int(
            os.getenv("WATCHDOG_THRESHOLD_SECONDS", "300")
# BRACKET_SURGEON: disabled
#         )  # 5 minutes default
        self.watchdog_check_interval = int(
            os.getenv("WATCHDOG_CHECK_INTERVAL", "60")
# BRACKET_SURGEON: disabled
#         )  # 1 minute default
        self.last_system_activity = datetime.now()
        self.watchdog_alerts_sent = 0
        self.max_watchdog_alerts = int(os.getenv("MAX_WATCHDOG_ALERTS", "3"))

        # Agent registry
        self.registered_agents = {}
        self.agent_heartbeats = {}

        # Service registry
        self.registered_services = {}

        # Monitoring threads
        self.monitoring_active = False
        self.heartbeat_thread = None
        self.health_thread = None
        self.watchdog_thread = None

        # Repair queue
        self.repair_queue = queue.Queue()
        self.repair_thread = None

        # System start time
        self.start_time = datetime.now()


    def initialize_database(self):
        """Initialize system monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        cpu_usage REAL NOT NULL,
                        memory_usage REAL NOT NULL,
                        disk_usage REAL NOT NULL,
                        agent_status TEXT NOT NULL,
                        service_status TEXT NOT NULL,
                        error_count INTEGER NOT NULL,
                        uptime_seconds INTEGER NOT NULL,
                        health_score REAL NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS diagnostic_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT NOT NULL,
                        suggested_action TEXT,
                        confidence REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS repair_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_id TEXT NOT NULL,
                        component TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        command TEXT,
                        success BOOLEAN NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        execution_time REAL NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS agent_registry (
                    agent_name TEXT PRIMARY KEY,
                        agent_class TEXT NOT NULL,
                        last_heartbeat TIMESTAMP,
                        status TEXT NOT NULL,
                        registered_at TIMESTAMP NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    # Back - compat: expose both names so any caller works


    def _health_summary(self, report: dict) -> str:
        """"""
        Create a short, readable summary of a health report.
        Expected shape:
          {"healthy": int, "unhealthy": int, "notes": [str, ...]}
        """"""
        try:
            healthy = int(report.get("healthy", 0))
            unhealthy = int(report.get("unhealthy", 0))
            notes = report.get("notes") or []
            if not isinstance(notes, (list, tuple)):  # be forgiving
                notes = [str(notes)]
            note_str = (
                ("; ".join(map(str, notes)))[:200] if notes else "All checks passed."
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        except Exception as e:
            # Never fail formatting; degrade gracefully
            return f"health summary unavailable ({type(e).__name__}: {e})"
        return f"{healthy} healthy, {unhealthy} unhealthy — {note_str}"

    # Optional convenience alias used by older callers


    def health_summary(self, report: dict) -> str:
        return self._health_summary(report)


    def start_monitoring(self):
        """Start autonomous monitoring system"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Start heartbeat monitoring
        self.heartbeat_thread = threading.Thread(
            target = self._heartbeat_monitor, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        self.heartbeat_thread.start()

        # Start health monitoring
        self.health_thread = threading.Thread(target=self._health_monitor,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                              daemon=True)
        self.health_thread.start()

        # Start repair processor
        self.repair_thread = threading.Thread(
            target=self._repair_processor, daemon=True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        self.repair_thread.start()

        # Start watchdog monitor if enabled
        if self.watchdog_enabled:
            self.watchdog_thread = threading.Thread(
                target = self._watchdog_monitor, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.watchdog_thread.start()
            self.logger.info(
                f"Watchdog system enabled (threshold: {self.watchdog_threshold}s)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        self.logger.info("System monitoring started")


    def stop_monitoring(self):
        """Stop monitoring system"""
        self.monitoring_active = False

        # Wait for threads to finish
        if hasattr(self, "health_thread") and self.health_thread.is_alive():
            self.health_thread.join(timeout = 5)

        if hasattr(self, "repair_thread") and self.repair_thread.is_alive():
            self.repair_thread.join(timeout = 5)

        if (
            hasattr(self, "watchdog_thread")
            and self.watchdog_thread
            and self.watchdog_thread.is_alive()
# BRACKET_SURGEON: disabled
#         ):
            self.watchdog_thread.join(timeout = 5)

        self.logger.info("System monitoring stopped")


    def register_agent(self, agent_name: str, agent_class: str):
        """Register agent for monitoring"""
        self.registered_agents[agent_name] = agent_class
        self.agent_heartbeats[agent_name] = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT OR REPLACE INTO agent_registry
                (agent_name, agent_class, last_heartbeat, status, registered_at)
                VALUES (?, ?, ?, ?, ?)
            ""","""
                (
                    agent_name,
                        agent_class,
                        datetime.now().isoformat(),
                        "active",
                        datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        self.logger.info(f"Registered agent: {agent_name} ({agent_class})")


    def agent_heartbeat(self, agent_name: str):
        """Record agent heartbeat"""
        if agent_name in self.registered_agents:
            self.agent_heartbeats[agent_name] = datetime.now()

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """"""
                    UPDATE agent_registry
                    SET last_heartbeat = ?, status = 'active'
                    WHERE agent_name = ?
                ""","""
                    (datetime.now().isoformat(), agent_name),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

            # Update system activity on agent heartbeat
            if self.watchdog_enabled:
                self.update_system_activity()


    def register_service(self, service_name: str, check_command: str):
        """Register service for monitoring"""
        self.registered_services[service_name] = check_command
        self.logger.info(f"Registered service: {service_name}")

    @dashboard_action(
        "Get System Health", "Retrieve current system health metrics and status"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )


    def get_system_health(self) -> SystemHealth:
        """Get current system health metrics"""
        # System metrics
        cpu_usage = psutil.cpu_percent(interval = 1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Agent status
        agent_status = {}
        current_time = datetime.now()

        for agent_name, last_heartbeat in self.agent_heartbeats.items():
            time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
            agent_status[agent_name] = time_since_heartbeat < (
                self.heartbeat_interval * 2
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Service status
        service_status = {}
        for service_name, check_command in self.registered_services.items():
            try:
                result = subprocess.run(
                    check_command, shell = True, capture_output = True, timeout = 10
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                service_status[service_name] = result.returncode == 0
            except Exception:
                service_status[service_name] = False

        # Error count (from recent logs)
        error_count = self._count_recent_errors()

        # Uptime
        uptime_seconds = int((current_time - self.start_time).total_seconds())

        return SystemHealth(
            timestamp = current_time,
                cpu_usage = cpu_usage,
                memory_usage = memory.percent,
                disk_usage = disk.percent,
                agent_status = agent_status,
                service_status = service_status,
                error_count = error_count,
                uptime_seconds = uptime_seconds,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

    @dashboard_action(
        "Run System Diagnostics", "Perform comprehensive system health diagnostics"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )


    def run_diagnostics(self) -> List[DiagnosticResult]:
        """Run comprehensive system diagnostics"""
        results = []
        health = self.get_system_health()

        # CPU diagnostics
        if health.cpu_usage > 90:
            results.append(
                DiagnosticResult(
                    component="CPU",
                        status="critical",
                        message = f"CPU usage at {health.cpu_usage:.1f}%",
                        suggested_action="restart_high_cpu_processes",
                        confidence = 0.9,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        elif health.cpu_usage > 70:
            results.append(
                DiagnosticResult(
                    component="CPU",
                        status="warning",
                        message = f"CPU usage at {health.cpu_usage:.1f}%",
                        suggested_action="monitor_cpu_usage",
                        confidence = 0.8,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Memory diagnostics
        if health.memory_usage > 90:
            results.append(
                DiagnosticResult(
                    component="Memory",
                        status="critical",
                        message = f"Memory usage at {health.memory_usage:.1f}%",
                        suggested_action="clear_memory_cache",
                        confidence = 0.9,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Agent diagnostics
        for agent_name, is_healthy in health.agent_status.items():
            if not is_healthy:
                results.append(
                    DiagnosticResult(
                        component = f"Agent_{agent_name}",
                            status="critical",
                            message = f"Agent {agent_name} not responding",
                            suggested_action="restart_agent",
                            confidence = 0.95,
                            timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        # Service diagnostics
        for service_name, is_healthy in health.service_status.items():
            if not is_healthy:
                results.append(
                    DiagnosticResult(
                        component = f"Service_{service_name}",
                            status="critical",
                            message = f"Service {service_name} is down",
                            suggested_action="restart_service",
                            confidence = 0.9,
                            timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        # Disk space diagnostics
        if health.disk_usage > 90:
            results.append(
                DiagnosticResult(
                    component="Disk",
                        status="critical",
                        message = f"Disk usage at {health.disk_usage:.1f}%",
                        suggested_action="cleanup_disk_space",
                        confidence = 0.9,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Save diagnostic results
        self._save_diagnostic_results(results)

        return results


    def execute_repair(self, diagnostic: DiagnosticResult) -> RepairAction:
        """Execute automated repair action"""
        action_id = (
            f"repair_{datetime.now().strftime('%Y % m%d_ % H%M % S')}_{diagnostic.component}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        start_time = time.time()

        repair_action = RepairAction(
            action_id = action_id,
                component = diagnostic.component,
                action_type = diagnostic.suggested_action or "unknown",
                description = f"Automated repair for {diagnostic.component}: {diagnostic.message}",
                command = None,
                success = False,
                timestamp = datetime.now(),
                execution_time = 0,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        try:
            success = False

            if diagnostic.suggested_action == "restart_agent":
                agent_name = diagnostic.component.replace("Agent_", "")
                success = self._restart_agent(agent_name)
                repair_action.command = f"restart_agent({agent_name})"

            elif diagnostic.suggested_action == "restart_service":
                service_name = diagnostic.component.replace("Service_", "")
                success = self._restart_service(service_name)
                repair_action.command = f"restart_service({service_name})"

            elif diagnostic.suggested_action == "clear_memory_cache":
                success = self._clear_memory_cache()
                repair_action.command = "clear_memory_cache"

            elif diagnostic.suggested_action == "cleanup_disk_space":
                success = self._cleanup_disk_space()
                repair_action.command = "cleanup_disk_space"

            elif diagnostic.suggested_action == "restart_high_cpu_processes":
                success = self._restart_high_cpu_processes()
                repair_action.command = "restart_high_cpu_processes"

            elif diagnostic.suggested_action == "investigate_system_stall":
                success = self._investigate_system_stall()
                repair_action.command = "investigate_system_stall"

            repair_action.success = success
            repair_action.execution_time = time.time() - start_time

            self.logger.info(
                f"Repair action {action_id}: {'SUCCESS' if success else 'FAILED'}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        except Exception as e:
            repair_action.success = False
            repair_action.execution_time = time.time() - start_time
            self.logger.error(f"Repair action {action_id} failed: {e}")

        # Save repair action
        self._save_repair_action(repair_action)

        return repair_action


    def _heartbeat_monitor(self):
        """Monitor agent heartbeats using main event loop"""

        import asyncio

        while self.monitoring_active:
            try:
                if self.main_loop and not self.main_loop.is_closed():
                    # Use main event loop via run_coroutine_threadsafe
                    future = asyncio.run_coroutine_threadsafe(
                        self._heartbeat_monitor_async_single(), self.main_loop
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    future.result(timeout = 30)  # Wait for completion with timeout
                else:
                    # Fallback to synchronous monitoring if no main loop
                    self._heartbeat_monitor_sync()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Heartbeat monitoring loop error: {e}")
                time.sleep(self.heartbeat_interval)


    async def _heartbeat_monitor_async_single(self):
        """Single async heartbeat check iteration"""
        try:
            current_time = datetime.now()

            for agent_name, last_heartbeat in self.agent_heartbeats.items():
                time_since_heartbeat = (current_time - last_heartbeat).total_seconds()

                if time_since_heartbeat > (self.heartbeat_interval * 3):
                    self.logger.warning(
                        f"Agent {agent_name} missed heartbeat ({time_since_heartbeat:.1f}s)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                    # Queue repair action
                    diagnostic = DiagnosticResult(
                        component = f"Agent_{agent_name}",
                            status="critical",
                            message = f"Agent {agent_name} missed heartbeat",
                            suggested_action="restart_agent",
                            confidence = 0.9,
                            timestamp = current_time,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                    self.repair_queue.put(diagnostic)

        except Exception as e:
            self.logger.error(f"Heartbeat check error: {e}")


    def _heartbeat_monitor_sync(self):
        """Synchronous heartbeat monitoring fallback"""
        try:
            current_time = datetime.now()

            for agent_name, last_heartbeat in self.agent_heartbeats.items():
                time_since_heartbeat = (current_time - last_heartbeat).total_seconds()

                if time_since_heartbeat > (self.heartbeat_interval * 3):
                    self.logger.warning(
                        f"Agent {agent_name} missed heartbeat ({time_since_heartbeat:.1f}s)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                    # Queue repair action
                    diagnostic = DiagnosticResult(
                        component = f"Agent_{agent_name}",
                            status="critical",
                            message = f"Agent {agent_name} missed heartbeat",
                            suggested_action="restart_agent",
                            confidence = 0.9,
                            timestamp = current_time,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                    self.repair_queue.put(diagnostic)

        except Exception as e:
            self.logger.error(f"Heartbeat check error: {e}")


    async def _heartbeat_monitor_async(self):
        """Async heartbeat monitoring loop (legacy method)"""
        while self.monitoring_active:
            try:
                await self._heartbeat_monitor_async_single()
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Heartbeat monitoring loop error: {e}")
                await asyncio.sleep(self.heartbeat_interval)


    def _health_monitor(self):
        """Monitor overall system health using main event loop"""

        import asyncio

        while self.monitoring_active:
            try:
                if self.main_loop and not self.main_loop.is_closed():
                    # Use main event loop via run_coroutine_threadsafe
                    future = asyncio.run_coroutine_threadsafe(
                        self._health_monitor_async_single(), self.main_loop
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    future.result(timeout = 30)  # Wait for completion with timeout
                else:
                    # Fallback to synchronous monitoring if no main loop
                    self._health_monitor_sync()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
                time.sleep(self.health_check_interval)


    async def _health_monitor_async_single(self):
        """Single async health check iteration"""
        try:
            health = self.get_system_health()
            health_score = health.overall_health_score()

            # Store health data
            self._store_health_data(health)

            # Check for critical issues
            if health_score < self.critical_threshold:
                diagnostic = DiagnosticResult(
                    component="System",
                        status="critical",
                        message = f"Critical system health: {health_score:.2f}",
                        suggested_action="immediate_intervention",
                        confidence = 0.95,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                self.repair_queue.put(diagnostic)

            elif health_score < self.warning_threshold:
                diagnostic = DiagnosticResult(
                    component="System",
                        status="warning",
                        message = f"System health degraded: {health_score:.2f}",
                        suggested_action="monitor_closely",
                        confidence = 0.8,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                self.repair_queue.put(diagnostic)

        except Exception as e:
            self.logger.error(f"Health check error: {e}")


    def _health_monitor_sync(self):
        """Synchronous health monitoring fallback"""
        try:
            health = self.get_system_health()
            health_score = health.overall_health_score()

            # Store health data
            self._store_health_data(health)

            # Check for critical issues
            if health_score < self.critical_threshold:
                diagnostic = DiagnosticResult(
                    component="System",
                        status="critical",
                        message = f"Critical system health: {health_score:.2f}",
                        suggested_action="immediate_intervention",
                        confidence = 0.95,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                self.repair_queue.put(diagnostic)

            elif health_score < self.warning_threshold:
                diagnostic = DiagnosticResult(
                    component="System",
                        status="warning",
                        message = f"System health degraded: {health_score:.2f}",
                        suggested_action="monitor_closely",
                        confidence = 0.8,
                        timestamp = datetime.now(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                self.repair_queue.put(diagnostic)

        except Exception as e:
            self.logger.error(f"Health check error: {e}")


    async def _health_monitor_async(self):
        """Async health monitoring loop (legacy method)"""
        while self.monitoring_active:
            try:
                await self._health_monitor_async_single()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(self.health_check_interval)

                # Save health metrics
                self._save_health_metrics(health)

                # Check for critical issues
                if health_score < self.critical_threshold:
                    self.logger.critical(f"System health critical: {health_score:.2f}")
                    diagnostics = self.run_diagnostics()

                    # Queue critical repairs
                    for diagnostic in diagnostics:
                        if diagnostic.status == "critical":
                            self.repair_queue.put(diagnostic)

                elif health_score < self.warning_threshold:
                    self.logger.warning(f"System health warning: {health_score:.2f}")

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(self.health_check_interval)


    def _repair_processor(self):
        """Process repair queue"""
        while self.monitoring_active:
            try:
                # Get repair task with timeout
                diagnostic = self.repair_queue.get(timeout = 10)

                # Execute repair
                repair_result = self.execute_repair(diagnostic)

                if repair_result.success:
                    self.logger.info(f"Successful repair: {repair_result.description}")
                else:
                    self.logger.error(f"Failed repair: {repair_result.description}")

                self.repair_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Repair processor error: {e}")


    def _restart_agent(self, agent_name: str) -> bool:
        """Restart a specific agent"""
        try:
            # This would integrate with the actual agent management system
            self.logger.info(f"Restarting agent: {agent_name}")
            # Placeholder for actual restart logic
        except Exception as e:
            self.logger.error(f"Failed to restart agent {agent_name}: {e}")
            return False


    def _restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            # Use launchctl for macOS services
            if sys.platform == "darwin":
                subprocess.run(
                    ["launchctl", "kickstart", "-k", f"gui/501/{service_name}"],
                        check = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
            else:
                subprocess.run(["systemctl", "restart", service_name], check = True)

            self.logger.info(f"Restarted service: {service_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {e}")
            return False


    def _clear_memory_cache(self) -> bool:
        """Clear system memory cache"""
        try:
            if sys.platform == "darwin":
                subprocess.run(["sudo", "purge"], check = True)
            else:
                subprocess.run(["sync"], check = True)
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("3")

            self.logger.info("Cleared memory cache")
        except Exception as e:
            self.logger.error(f"Failed to clear memory cache: {e}")
            return False


    def _cleanup_disk_space(self) -> bool:
        """Clean up disk space"""
        try:
            # Clean temporary files
            temp_dirs = ["/tmp", "/var/tmp"]
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    subprocess.run(
                        ["find", temp_dir, "-type", "f", "-atime", "+7", "-delete"],
                            check = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

            # Clean logs older than 30 days
            log_dirs = ["/var/log", "./logs"]
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    subprocess.run(
                        ["find", log_dir, "-name", "*.log", "-mtime", "+30", "-delete"],
                            check = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

            self.logger.info("Cleaned up disk space")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup disk space: {e}")
            return False


    def _restart_high_cpu_processes(self) -> bool:
        """Restart processes using high CPU"""
        try:
            # Find high CPU processes
            high_cpu_processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
                if proc.info["cpu_percent"] > 80:
                    high_cpu_processes.append(proc)

            # Restart manageable processes
            for proc in high_cpu_processes:
                if proc.info["name"] in ["python", "python3"]:
                    proc.terminate()
                    proc.wait(timeout = 10)

            self.logger.info(f"Restarted {len(high_cpu_processes)} high CPU processes")
        except Exception as e:
            self.logger.error(f"Failed to restart high CPU processes: {e}")
            return False


    def _count_recent_errors(self, hours: int = 1) -> int:
        """Count recent errors from logs"""
        try:
            # Count errors from the last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            error_count = 0

            # Check system logs for errors
            try:
                # On macOS/Linux, check system logs
                result = subprocess.run(
                    ['grep', '-c', 'ERROR', '/var/log/system.log'],
                    capture_output=True, text=True, timeout=5
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                if result.returncode == 0:
                    error_count += int(result.stdout.strip())
            except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                pass

            # Check application logs if they exist
            log_dir = Path('logs')
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    try:
                        with open(log_file, 'r') as f:
                            for line in f:
                                if 'ERROR' in line:
                                    error_count += 1
                    except Exception:
                        continue

            return error_count
        except Exception as e:
            self.logger.error(f"Error counting recent errors: {e}")
            return 0


    def _investigate_system_stall(self) -> bool:
        """Investigate system stall and gather diagnostic information"""
        try:
            self.logger.warning(
                "Investigating system stall - gathering diagnostic information"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Get current system metrics
            health = self.get_system_health()

            # Log detailed system state
            self.logger.info(
                f"System Health Score: {health.overall_health_score():.2f}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.logger.info(f"CPU Usage: {health.cpu_usage:.1f}%")
            self.logger.info(f"Memory Usage: {health.memory_usage:.1f}%")
            self.logger.info(
                f"Active Agents: {sum(health.agent_status.values())}/{len(health.agent_status)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.logger.info(
                f"Active Services: {sum(health.service_status.values())}/{len(health.service_status)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Check for stuck processes
            stuck_processes = []
            for proc in psutil.process_iter(["pid", "name", "status", "cpu_times"]):
                try:
                    if (
                        proc.info["status"] == "zombie"
                        or proc.info["cpu_times"].user > 3600
# BRACKET_SURGEON: disabled
#                     ):  # 1 hour CPU time
                        stuck_processes.append(
                            f"{proc.info['name']} (PID: {proc.info['pid']})"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if stuck_processes:
                self.logger.warning(
                    f"Potentially stuck processes: {', '.join(stuck_processes)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Reset watchdog activity to prevent immediate re - triggering
            self.update_system_activity()

        except Exception as e:
            pass
            return True
        except Exception as e:
            self.logger.error(f"Failed to investigate system stall: {e}")
            return False


    def _save_health_metrics(self, health: SystemHealth):
        """Save health metrics to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT INTO system_health
                (timestamp, cpu_usage, memory_usage, disk_usage,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     agent_status, service_status, error_count, uptime_seconds, health_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    health.timestamp.isoformat(),
                        health.cpu_usage,
                        health.memory_usage,
                        health.disk_usage,
                        json.dumps(health.agent_status),
                        json.dumps(health.service_status),
                        health.error_count,
                        health.uptime_seconds,
                        health.overall_health_score(),
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def _save_diagnostic_results(self, results: List[DiagnosticResult]):
        """Save diagnostic results to database"""
        with sqlite3.connect(self.db_path) as conn:
            for result in results:
                conn.execute(
                    """"""
                    INSERT INTO diagnostic_results
                    (component,
    status,
    message,
    suggested_action,
    confidence,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        result.component,
                            result.status,
                            result.message,
                            result.suggested_action,
                            result.confidence,
                            result.timestamp.isoformat(),
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )


    def _save_repair_action(self, action: RepairAction):
        """Save repair action to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """"""
                INSERT INTO repair_actions
                (action_id, component, action_type, description, command,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     success, timestamp, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    action.action_id,
                        action.component,
                        action.action_type,
                        action.description,
                        action.command,
                        action.success,
                        action.timestamp.isoformat(),
                        action.execution_time,
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def update_system_activity(self):
        """Update last system activity timestamp - call this on any significant system activity"""
        self.last_system_activity = datetime.now()
        if self.watchdog_alerts_sent > 0:
            self.logger.info(
                "System activity detected, resetting watchdog alert counter"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.watchdog_alerts_sent = 0


    def _watchdog_monitor(self):
        """Monitor system cadence and alert when stalled beyond threshold"""
        self.logger.info(
            f"Watchdog monitor started (threshold: {self.watchdog_threshold}s, "
            f"check interval: {self.watchdog_check_interval}s)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        while self.monitoring_active:
            try:
                current_time = datetime.now()
                time_since_activity = (
                    current_time - self.last_system_activity
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ).total_seconds()

                if time_since_activity > self.watchdog_threshold:
                    if self.watchdog_alerts_sent < self.max_watchdog_alerts:
                        self.watchdog_alerts_sent += 1

                        # Create diagnostic for system stall
                        diagnostic = DiagnosticResult(
                            component="SystemCadence",
                                status="critical",
                                message = f"System cadence stalled for {time_since_activity:.1f}s (threshold: {self.watchdog_threshold}s)",
                                suggested_action="investigate_system_stall",
                                confidence = 0.95,
                                timestamp = current_time,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )

                        # Queue for repair/investigation
                        self.repair_queue.put(diagnostic)

                        # Log critical alert
                        self.logger.critical(
                            f"WATCHDOG ALERT #{self.watchdog_alerts_sent}: System cadence stalled for {time_since_activity:.1f}s ""
                            f"(threshold: {self.watchdog_threshold}s). Last activity: {self.last_system_activity}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                        # Save to database
                        self._save_diagnostic_result(diagnostic)

                    elif self.watchdog_alerts_sent == self.max_watchdog_alerts:
                        self.logger.warning(
                            f"Watchdog alert limit reached ({self.max_watchdog_alerts}). Suppressing further alerts until activity resumes."
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        self.watchdog_alerts_sent += (
                            1  # Increment to prevent repeated warnings
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                time.sleep(self.watchdog_check_interval)

            except Exception as e:
                self.logger.error(f"Watchdog monitor error: {e}")
                time.sleep(self.watchdog_check_interval)


    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system management task"""
        # Update system activity on task execution
        if self.watchdog_enabled:
            self.update_system_activity()

        task_type = task_data.get("type")

        if task_type == "get_health":
            health = self.get_system_health()
        return {
            "success": True,
            "health": asdict(health),
            "health_score": health.overall_health_score(),
# BRACKET_SURGEON: disabled
#         }

        elif task_type == "run_diagnostics":
            results = self.run_diagnostics()
            return {"success": True, "diagnostics": [asdict(r) for r in results]}

        elif task_type == "start_monitoring":
            self.start_monitoring()
            return {"success": True}

        elif task_type == "stop_monitoring":
            self.stop_monitoring()
            return {"success": True}

        return {"success": False, "error": f"Unknown task type: {task_type}"}

    @dashboard_action(doc="Run immediate health checks (sync)")


    def run_health_checks(self):
        """Run immediate synchronous health checks"""
        try:
            health = self.get_system_health()
        except Exception as e:
            pass
        return {
            "ok": True,
            "health_score": health.overall_health_score(),
            "cpu_usage": health.cpu_usage,
            "memory_usage": health.memory_usage,
            "disk_usage": health.disk_usage,
            "timestamp": health.timestamp.isoformat(),
# BRACKET_SURGEON: disabled
#         }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @dashboard_action(doc="Get current system snapshot", method="GET", public = False)


    def status(self):
        """Get current system status snapshot"""
        try:
            health = self.get_system_health()
            return {
                "timestamp": time.time(),
                "health": asdict(health),
                "monitoring_active": self.monitoring_active,
                "registered_agents": list(self.registered_agents.keys()),
                "registered_services": list(self.registered_services.keys()),
# BRACKET_SURGEON: disabled
#             }
        except Exception as e:
            return {"timestamp": time.time(), "error": str(e)}

    @dashboard_action(doc="Force watchdog investigation")


    def investigate_system_stall(self):
        """Force a watchdog investigation for system stalls"""
        try:
            if not self.watchdog_enabled:
                return {"queued": False, "error": "Watchdog not enabled"}

            # Trigger immediate watchdog check
            self._investigate_stall()
            return {"queued": True, "message": "Watchdog investigation triggered"}
        except Exception as e:
            return {"queued": False, "error": str(e)}

    @property


    def capabilities(self) -> List["AgentCapability"]:
        """Return system agent capabilities"""

        from .base_agents import AgentCapability

        return [
            AgentCapability.SYSTEM_MONITORING,
                AgentCapability.AUTONOMOUS_REPAIR,
                AgentCapability.HEALTH_DIAGNOSTICS,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    async def _execute_with_monitoring(
        self, task: Dict[str, Any], context
    ) -> Dict[str, Any]:
        """Execute task with system monitoring"""
        try:
            result = await self.process_task(task)
            return {
                "success": True,
                "result": result,
                "monitoring": "System health monitored during execution",
# BRACKET_SURGEON: disabled
#             }
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {"success": False, "error": str(e)}


    async def _rephrase_task(self, task: Dict[str, Any], context) -> str:
        """Rephrase system task for clarity"""
        task_type = task.get("type", "unknown")
        return f"System operation: {task_type} - {task.get('description', 'No description')}"


    async def _validate_rephrase_accuracy(
        self, original_task: Dict[str, Any], rephrased: str, context
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Validate rephrased task accuracy"""
        return True

# Test code removed to prevent duplicate SystemAgent instances
# The SystemAgent should only be instantiated by the orchestrator