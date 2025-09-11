#!/usr / bin / env python3
"""
Health Check and Monitoring System for ChatGPT Integration
Implements Rule 11: Health Check and Monitoring Requirements
"""

import asyncio
import json
import logging
import os
import socket
import sqlite3
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
import psutil
from audit_logger import AuditLevel, audit_logger
from timeout_manager import TimeoutType, timeout_manager


class HealthStatus(Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of metrics to collect"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass


class HealthCheckResult:
    """Result of a health check"""

    check_name: str
    status: HealthStatus
    message: str
    timestamp: str
    response_time_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None

@dataclass


class SystemMetric:
    """System metric data point"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: str
    tags: Dict[str, str]
    unit: str

@dataclass


class AlertRule:
    """Alert rule configuration"""

    rule_id: str
    metric_name: str
    condition: str  # e.g., ">", "<", "=="
    threshold: float
    severity: AlertSeverity
    description: str
    cooldown_minutes: int
    enabled: bool

@dataclass


class Alert:
    """Alert instance"""

    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    message: str
    timestamp: str
    resolved: bool
    resolved_timestamp: Optional[str] = None


class HealthMonitor:
    """Comprehensive health monitoring and alerting system"""


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)

        self.health_checks = {}
        self.metrics = []
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = []
        self.last_alert_times = {}

        # Setup logging
        self.logger = logging.getLogger("health_monitor")
        self.logger.setLevel(logging.INFO)

        # Initialize database
        self._init_database()

        # Register default health checks
        self._register_default_health_checks()

        # Register default alert rules
        self._register_default_alert_rules()

        # Start monitoring loop
        self.monitoring_active = False
        self.monitoring_task = None


    def _load_default_config(self) -> Dict[str, Any]:
        """Load default monitoring configuration"""
        return {
            "health_check_interval": 30,  # seconds
            "metric_collection_interval": 10,  # seconds
            "alert_check_interval": 15,  # seconds
            "database_path": "/tmp / trae_health_monitor.db",
                "max_metrics_history": 10000,
                "max_alert_history": 1000,
                "webhook_timeout": 10,  # seconds
            "default_cooldown": 5,  # minutes
            "chatgpt_api_url": os.getenv(
                "CHATGPT_API_URL", "https://api.openai.com / v1 / chat / completions"
            ),
                "system_endpoints": [
                "http://localhost:8000 / health",
                    "http://localhost:3000 / api / health",
                    ],
                "critical_processes": ["python", "node", "nginx"],
                "disk_usage_threshold": 85,  # percent
            "memory_usage_threshold": 90,  # percent
            "cpu_usage_threshold": 80,  # percent
            "response_time_threshold": 5000,  # milliseconds
            "error_rate_threshold": 5,  # percent
        }


    def _init_database(self):
        """Initialize SQLite database for metrics and alerts"""
        db_path = Path(self.config["database_path"])
        db_path.parent.mkdir(parents = True, exist_ok = True)

        self.db_connection = sqlite3.connect(
            str(db_path), check_same_thread = False, timeout = 30
        )
        self.db_lock = threading.Lock()

        # Create tables
        with self.db_lock:
            cursor = self.db_connection.cursor()

            # Health checks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        check_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        timestamp TEXT NOT NULL,
                        response_time_ms REAL,
                        details TEXT,
                        error TEXT
                )
            """
            )

            # Metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        tags TEXT,
                        unit TEXT
                )
            """
            )

            # Alerts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE NOT NULL,
                        rule_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        current_value REAL NOT NULL,
                        threshold REAL NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        resolved INTEGER DEFAULT 0,
                        resolved_timestamp TEXT
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_timestamp ON health_checks(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(name, timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)"
            )

            self.db_connection.commit()


    def _register_default_health_checks(self):
        """Register default health checks"""

        # System resource checks
        self.register_health_check("system_cpu", self._check_cpu_usage)
        self.register_health_check("system_memory", self._check_memory_usage)
        self.register_health_check("system_disk", self._check_disk_usage)

        # Process checks
        self.register_health_check("critical_processes", self._check_critical_processes)

        # Network connectivity
        self.register_health_check(
            "internet_connectivity", self._check_internet_connectivity
        )

        # ChatGPT API connectivity
        self.register_health_check("chatgpt_api", self._check_chatgpt_api)

        # Local endpoints
        for endpoint in self.config["system_endpoints"]:
            endpoint_name = f"endpoint_{urlparse(endpoint).port or 'default'}"
            self.register_health_check(
                endpoint_name, lambda url = endpoint: self._check_http_endpoint(url)
            )


    def _register_default_alert_rules(self):
        """Register default alert rules"""

        # System resource alerts
        self.register_alert_rule(
            AlertRule(
                rule_id="high_cpu_usage",
                    metric_name="system.cpu.usage_percent",
                    condition=">",
                    threshold = self.config["cpu_usage_threshold"],
                    severity = AlertSeverity.WARNING,
                    description="High CPU usage detected",
                    cooldown_minutes = 5,
                    enabled = True,
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="high_memory_usage",
                    metric_name="system.memory.usage_percent",
                    condition=">",
                    threshold = self.config["memory_usage_threshold"],
                    severity = AlertSeverity.CRITICAL,
                    description="High memory usage detected",
                    cooldown_minutes = 5,
                    enabled = True,
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="high_disk_usage",
                    metric_name="system.disk.usage_percent",
                    condition=">",
                    threshold = self.config["disk_usage_threshold"],
                    severity = AlertSeverity.WARNING,
                    description="High disk usage detected",
                    cooldown_minutes = 10,
                    enabled = True,
                    )
        )

        # API response time alerts
        self.register_alert_rule(
            AlertRule(
                rule_id="slow_api_response",
                    metric_name="api.response_time_ms",
                    condition=">",
                    threshold = self.config["response_time_threshold"],
                    severity = AlertSeverity.WARNING,
                    description="Slow API response time detected",
                    cooldown_minutes = 3,
                    enabled = True,
                    )
        )

        # Error rate alerts
        self.register_alert_rule(
            AlertRule(
                rule_id="high_error_rate",
                    metric_name="api.error_rate_percent",
                    condition=">",
                    threshold = self.config["error_rate_threshold"],
                    severity = AlertSeverity.CRITICAL,
                    description="High API error rate detected",
                    cooldown_minutes = 2,
                    enabled = True,
                    )
        )


    def register_health_check(
        self, name: str, check_function: Callable[[], Dict[str, Any]]
    ):
        """Register a health check function"""
        self.health_checks[name] = check_function
        self.logger.info(f"Registered health check: {name}")


    def register_alert_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Registered alert rule: {rule.rule_id}")


    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval = 1)

            # Record metric
            await self.record_metric(
                name="system.cpu.usage_percent",
                    value = cpu_percent,
                    metric_type = MetricType.GAUGE,
                    unit="percent",
                    )

            status = HealthStatus.HEALTHY
            if cpu_percent > self.config["cpu_usage_threshold"]:
                status = (
                    HealthStatus.CRITICAL if cpu_percent > 95 else HealthStatus.WARNING
                )

            return {
                "status": status,
                    "message": f"CPU usage: {cpu_percent:.1f}%",
                    "details": {
                    "cpu_percent": cpu_percent,
                        "cpu_count": psutil.cpu_count(),
                        "load_average": (
                        os.getloadavg() if hasattr(os, "getloadavg") else None
                    ),
                        },
                    }

        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                    "message": f"Failed to check CPU usage: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()

            # Record metrics
            await self.record_metric(
                name="system.memory.usage_percent",
                    value = memory.percent,
                    metric_type = MetricType.GAUGE,
                    unit="percent",
                    )

            await self.record_metric(
                name="system.memory.available_bytes",
                    value = memory.available,
                    metric_type = MetricType.GAUGE,
                    unit="bytes",
                    )

            status = HealthStatus.HEALTHY
            if memory.percent > self.config["memory_usage_threshold"]:
                status = (
                    HealthStatus.CRITICAL
                    if memory.percent > 95
                    else HealthStatus.WARNING
                )

            return {
                "status": status,
                    "message": f"Memory usage: {memory.percent:.1f}%",
                    "details": {
                    "total_bytes": memory.total,
                        "available_bytes": memory.available,
                        "used_bytes": memory.used,
                        "percent": memory.percent,
                        },
                    }

        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                    "message": f"Failed to check memory usage: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage"""
        try:
            disk = psutil.disk_usage("/")
            usage_percent = (disk.used / disk.total) * 100

            # Record metric
            await self.record_metric(
                name="system.disk.usage_percent",
                    value = usage_percent,
                    metric_type = MetricType.GAUGE,
                    unit="percent",
                    )

            status = HealthStatus.HEALTHY
            if usage_percent > self.config["disk_usage_threshold"]:
                status = (
                    HealthStatus.CRITICAL
                    if usage_percent > 95
                    else HealthStatus.WARNING
                )

            return {
                "status": status,
                    "message": f"Disk usage: {usage_percent:.1f}%",
                    "details": {
                    "total_bytes": disk.total,
                        "used_bytes": disk.used,
                        "free_bytes": disk.free,
                        "percent": usage_percent,
                        },
                    }

        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                    "message": f"Failed to check disk usage: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_critical_processes(self) -> Dict[str, Any]:
        """Check if critical processes are running"""
        try:
            running_processes = {p.name() for p in psutil.process_iter(["name"])}
            critical_processes = self.config["critical_processes"]

            missing_processes = []
            for process in critical_processes:
                if not any(
                    process in running_proc for running_proc in running_processes
                ):
                    missing_processes.append(process)

            status = (
                HealthStatus.HEALTHY if not missing_processes else HealthStatus.CRITICAL
            )

            return {
                "status": status,
                    "message": f"Critical processes check: {len(missing_processes)} missing",
                    "details": {
                    "critical_processes": critical_processes,
                        "missing_processes": missing_processes,
                        "running_processes": list(running_processes),
                        },
                    }

        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                    "message": f"Failed to check processes: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_internet_connectivity(self) -> Dict[str, Any]:
        """Check internet connectivity"""
        try:
            start_time = time.time()

            # Try to connect to a reliable external service
            async with timeout_manager.timeout_context(
                operation_type = TimeoutType.HEALTH_CHECK, custom_timeout = 5
            ):
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://8.8.8.8:53", timeout = 5) as response:
                        pass

            response_time = (time.time() - start_time) * 1000

            return {
                "status": HealthStatus.HEALTHY,
                    "message": f"Internet connectivity OK ({response_time:.0f}ms)",
                    "details": {
                    "response_time_ms": response_time,
                        "test_endpoint": "8.8.8.8:53",
                        },
                    }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                    "message": f"No internet connectivity: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_chatgpt_api(self) -> Dict[str, Any]:
        """Check ChatGPT API connectivity"""
        try:
            start_time = time.time()

            headers = {
                "Authorization": f'Bearer {os.getenv("OPENAI_API_KEY", "test_key")}',
                    "Content - Type": "application / json",
                    }

            # Simple API health check (without making actual requests)
            async with timeout_manager.timeout_context(
                operation_type = TimeoutType.API_CALL,
                    custom_timeout = self.config["webhook_timeout"],
                    ):
                async with aiohttp.ClientSession() as session:
                    # Just check if the endpoint is reachable
                    async with session.head(
                        self.config["chatgpt_api_url"], headers = headers
                    ) as response:
                        response_time = (time.time() - start_time) * 1000

                        # Record API response time metric
                        await self.record_metric(
                            name="api.response_time_ms",
                                value = response_time,
                                metric_type = MetricType.TIMER,
                                unit="milliseconds",
                                tags={"endpoint": "chatgpt_api"},
                                )

                        status = HealthStatus.HEALTHY
                        if response.status >= 500:
                            status = HealthStatus.CRITICAL
                        elif response.status >= 400:
                            status = HealthStatus.WARNING

                        return {
                            "status": status,
                                "message": f"ChatGPT API: HTTP {response.status} ({response_time:.0f}ms)",
                                "details": {
                                "status_code": response.status,
                                    "response_time_ms": response_time,
                                    "endpoint": self.config["chatgpt_api_url"],
                                    },
                                }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                    "message": f"ChatGPT API unreachable: {str(e)}",
                    "details": {},
                    "error": str(e),
                    }


    async def _check_http_endpoint(self, url: str) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        try:
            start_time = time.time()

            async with timeout_manager.timeout_context(
                operation_type = TimeoutType.HEALTH_CHECK,
                    custom_timeout = self.config["webhook_timeout"],
                    ):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000

                        status = HealthStatus.HEALTHY
                        if response.status >= 500:
                            status = HealthStatus.CRITICAL
                        elif response.status >= 400:
                            status = HealthStatus.WARNING

                        return {
                            "status": status,
                                "message": f"Endpoint {url}: HTTP {response.status} ({response_time:.0f}ms)",
                                "details": {
                                "url": url,
                                    "status_code": response.status,
                                    "response_time_ms": response_time,
                                    },
                                }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                    "message": f"Endpoint {url} unreachable: {str(e)}",
                    "details": {"url": url},
                    "error": str(e),
                    }


    async def run_health_check(self, check_name: str) -> HealthCheckResult:
        """Run a specific health check"""
        if check_name not in self.health_checks:
            raise ValueError(f"Unknown health check: {check_name}")

        start_time = time.time()

        try:
            check_function = self.health_checks[check_name]
            result = await check_function()

            response_time = (time.time() - start_time) * 1000

            health_result = HealthCheckResult(
                check_name = check_name,
                    status = result["status"],
                    message = result["message"],
                    timestamp = datetime.utcnow().isoformat(),
                    response_time_ms = response_time,
                    details = result.get("details", {}),
                    error = result.get("error"),
                    )

            # Store in database
            await self._store_health_check_result(health_result)

            return health_result

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            health_result = HealthCheckResult(
                check_name = check_name,
                    status = HealthStatus.UNKNOWN,
                    message = f"Health check failed: {str(e)}",
                    timestamp = datetime.utcnow().isoformat(),
                    response_time_ms = response_time,
                    details={},
                    error = str(e),
                    )

            await self._store_health_check_result(health_result)
            return health_result


    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = {}

        for check_name in self.health_checks:
            try:
                results[check_name] = await self.run_health_check(check_name)
            except Exception as e:
                self.logger.error(f"Error running health check {check_name}: {str(e)}")
                results[check_name] = HealthCheckResult(
                    check_name = check_name,
                        status = HealthStatus.UNKNOWN,
                        message = f"Check execution failed: {str(e)}",
                        timestamp = datetime.utcnow().isoformat(),
                        response_time_ms = 0,
                        details={},
                        error = str(e),
                        )

        return results


    async def record_metric(
        self,
            name: str,
            value: float,
            metric_type: MetricType,
            unit: str = "",
            tags: Optional[Dict[str, str]] = None,
            ) -> None:
        """Record a metric"""

        metric = SystemMetric(
            name = name,
                value = value,
                metric_type = metric_type,
                timestamp = datetime.utcnow().isoformat(),
                tags = tags or {},
                unit = unit,
                )

        self.metrics.append(metric)

        # Store in database
        await self._store_metric(metric)

        # Check alert rules
        await self._check_alert_rules(metric)

        # Cleanup old metrics
        if len(self.metrics) > self.config["max_metrics_history"]:
            self.metrics = self.metrics[-self.config["max_metrics_history"] :]


    async def _store_health_check_result(self, result: HealthCheckResult):
        """Store health check result in database"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO health_checks
                    (check_name, status, message, timestamp, response_time_ms, details, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.check_name,
                            result.status.value,
                            result.message,
                            result.timestamp,
                            result.response_time_ms,
                            json.dumps(result.details),
                            result.error,
                            ),
                        )
                self.db_connection.commit()
        except Exception as e:
            self.logger.error(f"Error storing health check result: {str(e)}")


    async def _store_metric(self, metric: SystemMetric):
        """Store metric in database"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO metrics
                    (name, value, metric_type, timestamp, tags, unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        metric.name,
                            metric.value,
                            metric.metric_type.value,
                            metric.timestamp,
                            json.dumps(metric.tags),
                            metric.unit,
                            ),
                        )
                self.db_connection.commit()
        except Exception as e:
            self.logger.error(f"Error storing metric: {str(e)}")


    async def _check_alert_rules(self, metric: SystemMetric):
        """Check if metric triggers any alert rules"""
        for rule in self.alert_rules.values():
            if not rule.enabled or rule.metric_name != metric.name:
                continue

            # Check cooldown
            if rule.rule_id in self.last_alert_times:
                last_alert = self.last_alert_times[rule.rule_id]
                cooldown_end = last_alert + timedelta(minutes = rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue

            # Evaluate condition
            triggered = False
            if rule.condition == ">" and metric.value > rule.threshold:
                triggered = True
            elif rule.condition == "<" and metric.value < rule.threshold:
                triggered = True
            elif rule.condition == "==" and metric.value == rule.threshold:
                triggered = True
            elif rule.condition == ">=" and metric.value >= rule.threshold:
                triggered = True
            elif rule.condition == "<=" and metric.value <= rule.threshold:
                triggered = True

            if triggered:
                await self._trigger_alert(rule, metric)


    async def _trigger_alert(self, rule: AlertRule, metric: SystemMetric):
        """Trigger an alert"""
        alert_id = f"{rule.rule_id}_{int(time.time())}"

        alert = Alert(
            alert_id = alert_id,
                rule_id = rule.rule_id,
                metric_name = metric.name,
                current_value = metric.value,
                threshold = rule.threshold,
                severity = rule.severity,
                message = f"{rule.description}: {metric.name} = {metric.value} {metric.unit} (threshold: {rule.threshold})",
                timestamp = datetime.utcnow().isoformat(),
                resolved = False,
                )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[rule.rule_id] = datetime.utcnow()

        # Store in database
        await self._store_alert(alert)

        # Log alert
        audit_logger.log_security_event(
            event_description = f"Alert triggered: {rule.rule_id}",
                severity=(
                AuditLevel.ERROR
                if rule.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
                else AuditLevel.WARNING
            ),
                additional_data={
                "alert_id": alert_id,
                    "rule_id": rule.rule_id,
                    "metric_name": metric.name,
                    "current_value": metric.value,
                    "threshold": rule.threshold,
                    "severity": rule.severity.value,
                    },
                )

        self.logger.warning(f"Alert triggered: {alert.message}")

        # Cleanup old alerts
        if len(self.alert_history) > self.config["max_alert_history"]:
            self.alert_history = self.alert_history[-self.config["max_alert_history"] :]


    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO alerts
                    (alert_id, rule_id, metric_name, current_value, threshold, severity, message, timestamp, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert.alert_id,
                            alert.rule_id,
                            alert.metric_name,
                            alert.current_value,
                            alert.threshold,
                            alert.severity.value,
                            alert.message,
                            alert.timestamp,
                            0 if not alert.resolved else 1,
                            ),
                        )
                self.db_connection.commit()
        except Exception as e:
            self.logger.error(f"Error storing alert: {str(e)}")


    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        self.logger.info("Health monitoring started")

        audit_logger.log_system_event(
            event_description="Health monitoring system started",
                additional_data={
                "health_checks": list(self.health_checks.keys()),
                    "alert_rules": list(self.alert_rules.keys()),
                    },
                )


    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health monitoring stopped")


    async def _monitoring_loop(self):
        """Main monitoring loop"""
        last_health_check = 0
        last_metric_collection = 0
        last_alert_check = 0

        while self.monitoring_active:
            try:
                current_time = time.time()

                # Run health checks
                if (
                    current_time - last_health_check
                    >= self.config["health_check_interval"]
                ):
                    await self.run_all_health_checks()
                    last_health_check = current_time

                # Collect system metrics
                if (
                    current_time - last_metric_collection
                    >= self.config["metric_collection_interval"]
                ):
                    await self._collect_system_metrics()
                    last_metric_collection = current_time

                # Check alerts
                if (
                    current_time - last_alert_check
                    >= self.config["alert_check_interval"]
                ):
                    await self._check_alert_resolution()
                    last_alert_check = current_time

                await asyncio.sleep(1)  # Small sleep to prevent busy waiting

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying


    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent()
            await self.record_metric(
                "system.cpu.usage_percent", cpu_percent, MetricType.GAUGE, "percent"
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            await self.record_metric(
                "system.memory.usage_percent",
                    memory.percent,
                    MetricType.GAUGE,
                    "percent",
                    )

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            await self.record_metric(
                "system.disk.usage_percent", disk_percent, MetricType.GAUGE, "percent"
            )

            # Network metrics
            network = psutil.net_io_counters()
            await self.record_metric(
                "system.network.bytes_sent",
                    network.bytes_sent,
                    MetricType.COUNTER,
                    "bytes",
                    )
            await self.record_metric(
                "system.network.bytes_recv",
                    network.bytes_recv,
                    MetricType.COUNTER,
                    "bytes",
                    )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")


    async def _check_alert_resolution(self):
        """Check if any active alerts should be resolved"""
        # This is a simplified implementation
        # In a real system, you'd check if the conditions that triggered the alert are no longer true
        pass


    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Get recent health check results
        recent_checks = {}
        for check_name in self.health_checks:
            # Get most recent result from database
            try:
                with self.db_lock:
                    cursor = self.db_connection.cursor()
                    cursor.execute(
                        """
                        SELECT status, message, timestamp, response_time_ms, details, error
                            FROM health_checks
                        WHERE check_name = ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """,
                        (check_name,),
                            )

                    result = cursor.fetchone()
                    if result:
                        recent_checks[check_name] = {
                            "status": result[0],
                                "message": result[1],
                                "timestamp": result[2],
                                "response_time_ms": result[3],
                                "details": json.loads(result[4]) if result[4] else {},
                                "error": result[5],
                                }
            except Exception as e:
                self.logger.error(
                    f"Error getting recent check for {check_name}: {str(e)}"
                )

        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        if any(
            check["status"] == HealthStatus.CRITICAL.value
            for check in recent_checks.values()
        ):
            overall_status = HealthStatus.CRITICAL
        elif any(
            check["status"] == HealthStatus.WARNING.value
            for check in recent_checks.values()
        ):
            overall_status = HealthStatus.WARNING
        elif any(
            check["status"] == HealthStatus.UNKNOWN.value
            for check in recent_checks.values()
        ):
            overall_status = HealthStatus.UNKNOWN

        return {
            "overall_status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "health_checks": recent_checks,
                "active_alerts": len(self.active_alerts),
                "monitoring_active": self.monitoring_active,
                "uptime_seconds": (
                time.time() - psutil.boot_time()
                if hasattr(psutil, "boot_time")
                else None
            ),
                }


    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""

        # Get recent metrics summary
        recent_metrics = {}
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()

                # Get latest value for each metric
                cursor.execute(
                    """
                    SELECT name, value, unit, timestamp
                    FROM metrics m1
                    WHERE timestamp = (
                        SELECT MAX(timestamp)
                        FROM metrics m2
                        WHERE m2.name = m1.name
                    )
                    ORDER BY name
                """
                )

                for row in cursor.fetchall():
                    recent_metrics[row[0]] = {
                        "value": row[1],
                            "unit": row[2],
                            "timestamp": row[3],
                            }
        except Exception as e:
            self.logger.error(f"Error getting recent metrics: {str(e)}")

        # Get alert summary
        alert_summary = {
            "active_alerts": len(self.active_alerts),
                "total_alerts_24h": len(
                [
                    alert
                    for alert in self.alert_history
                    if datetime.fromisoformat(alert.timestamp)
                    > datetime.utcnow() - timedelta(hours = 24)
                ]
            ),
                "critical_alerts_24h": len(
                [
                    alert
                    for alert in self.alert_history
                    if (
                        datetime.fromisoformat(alert.timestamp)
                        > datetime.utcnow() - timedelta(hours = 24)
                        and alert.severity
                        in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
                    )
                ]
            ),
                }

        return {
            "report_id": f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "system_status": self.get_system_status(),
                "recent_metrics": recent_metrics,
                "alert_summary": alert_summary,
                "monitoring_config": {
                "health_check_interval": self.config["health_check_interval"],
                    "metric_collection_interval": self.config["metric_collection_interval"],
                    "alert_check_interval": self.config["alert_check_interval"],
                    "registered_checks": list(self.health_checks.keys()),
                    "registered_rules": list(self.alert_rules.keys()),
                    },
                "compliance_status": {
                "rule_11_health_checks": len(self.health_checks) > 0,
                    "rule_11_monitoring_active": self.monitoring_active,
                    "rule_11_alerting_configured": len(self.alert_rules) > 0,
                    "rule_11_metrics_collection": len(recent_metrics) > 0,
                    },
                }

# Global health monitor instance
health_monitor = HealthMonitor()

# Convenience functions


async def start_health_monitoring():
    """Start health monitoring system"""
    await health_monitor.start_monitoring()


async def get_system_health():
    """Get current system health status"""
    return health_monitor.get_system_status()


async def record_api_metric(endpoint: str, response_time_ms: float, status_code: int):
    """Record API performance metric"""
    await health_monitor.record_metric(
        name="api.response_time_ms",
            value = response_time_ms,
            metric_type = MetricType.TIMER,
            unit="milliseconds",
            tags={"endpoint": endpoint, "status_code": str(status_code)},
            )

    # Calculate error rate
    error_rate = 100 if status_code >= 400 else 0
    await health_monitor.record_metric(
        name="api.error_rate_percent",
            value = error_rate,
            metric_type = MetricType.GAUGE,
            unit="percent",
            tags={"endpoint": endpoint},
            )
