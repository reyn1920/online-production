#!/usr/bin/env python3
"""
Alert Manager - Comprehensive Monitoring and Alerting System
Implements real - time monitoring, alerting, and scaling rules for go - live compliance
"""

import asyncio
import hashlib
import json
import logging
import os
import smtplib
import ssl
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import psutil
from audit_logger import AuditLevel, audit_logger
from compliance_monitor import compliance_monitor
from health_monitor import HealthStatus, health_monitor
from timeout_manager import timeout_manager


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(Enum):
    """Alert categories"""

    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channels"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"
    TEAMS = "teams"

@dataclass


class AlertRule:
    """Alert rule definition"""

    rule_id: str
    name: str
    description: str
    category: AlertCategory
    severity: AlertSeverity
    condition: str  # Python expression to evaluate
    threshold: float
    duration_seconds: int  # How long condition must be true
    cooldown_seconds: int  # Minimum time between alerts
    enabled: bool
    notification_channels: List[NotificationChannel]
    escalation_rules: List[Dict[str, Any]]
    auto_resolve: bool
    tags: List[str]

@dataclass


class Alert:
    """Alert instance"""

    alert_id: str
    rule_id: str
    title: str
    description: str
    category: AlertCategory
    severity: AlertSeverity
    status: AlertStatus
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    acknowledged_at: Optional[str]
    acknowledged_by: Optional[str]
    current_value: float
    threshold: float
    metadata: Dict[str, Any]
    notification_history: List[Dict[str, Any]]
    escalation_level: int

@dataclass


class MetricPoint:
    """Time series metric point"""

    timestamp: float
    value: float
    labels: Dict[str, str]

@dataclass


class SystemMetrics:
    """System performance metrics"""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, float]
    process_count: int
    load_average: List[float]
    uptime_seconds: float
    timestamp: float

@dataclass


class ApplicationMetrics:
    """Application - specific metrics"""

    request_count: int
    error_count: int
    response_time_ms: float
    active_connections: int
    queue_size: int
    cache_hit_rate: float
    database_connections: int
    timestamp: float


class AlertManager:
    """Comprehensive monitoring and alerting system"""


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)

        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen = 10000)
        self.metrics_buffer = defaultdict(lambda: deque(maxlen = 1000))
        self.notification_channels = {}
        self.escalation_handlers = {}

        # Monitoring state
        self.monitoring_active = False
        self.last_metric_collection = 0
        self.alert_counters = defaultdict(int)
        self.suppressed_alerts = set()

        # Setup logging
        self.logger = logging.getLogger("alert_manager")
        self.logger.setLevel(logging.INFO)

        # Initialize default alert rules
        self._initialize_default_rules()

        # Setup notification channels
        self._setup_notification_channels()

        # Start monitoring thread
        self.monitoring_thread = None
        self._start_monitoring()


    def _load_default_config(self) -> Dict[str, Any]:
        """Load default alert manager configuration"""
        return {
            "metric_collection_interval": 30,  # seconds
            "alert_evaluation_interval": 10,  # seconds
            "max_alerts_per_rule_per_hour": 10,
                "default_cooldown_seconds": 300,  # 5 minutes
            "escalation_timeout_minutes": 15,
                "auto_resolve_timeout_minutes": 60,
                "notification_retry_attempts": 3,
                "notification_retry_delay": 30,
                "metrics_retention_hours": 24,
                "alert_history_retention_days": 30,
                "enable_system_monitoring": True,
                "enable_application_monitoring": True,
                "enable_security_monitoring": True,
                "enable_compliance_monitoring": True,
                "cpu_threshold_warning": 80.0,
                "cpu_threshold_critical": 95.0,
                "memory_threshold_warning": 85.0,
                "memory_threshold_critical": 95.0,
                "disk_threshold_warning": 80.0,
                "disk_threshold_critical": 90.0,
                "response_time_threshold_warning": 2000,  # ms
            "response_time_threshold_critical": 5000,  # ms
            "error_rate_threshold_warning": 5.0,  # %
            "error_rate_threshold_critical": 10.0,  # %
            "availability_threshold_warning": 99.0,  # %
            "availability_threshold_critical": 95.0,  # %
            "email_smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "email_smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "email_username": os.getenv("ALERT_EMAIL_USERNAME"),
                "email_password": os.getenv("ALERT_EMAIL_PASSWORD"),
                "email_from": os.getenv("ALERT_EMAIL_FROM"),
                "email_to": os.getenv("ALERT_EMAIL_TO", "").split(","),
                "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
                "webhook_endpoints": os.getenv("ALERT_WEBHOOK_ENDPOINTS", "").split(","),
                "enable_auto_scaling": True,
                "scaling_cpu_threshold": 70.0,
                "scaling_memory_threshold": 80.0,
                "scaling_cooldown_minutes": 10,
                }


    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""

        # System monitoring rules
        self.register_alert_rule(
            AlertRule(
                rule_id="high_cpu_usage",
                    name="High CPU Usage",
                    description="CPU usage is above threshold",
                    category = AlertCategory.SYSTEM,
                    severity = AlertSeverity.WARNING,
                    condition="cpu_percent > threshold",
                    threshold = self.config["cpu_threshold_warning"],
                    duration_seconds = 120,
                    cooldown_seconds = 300,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 15,
                            "severity": AlertSeverity.CRITICAL,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["system", "performance", "cpu"],
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="critical_cpu_usage",
                    name="Critical CPU Usage",
                    description="CPU usage is critically high",
                    category = AlertCategory.SYSTEM,
                    severity = AlertSeverity.CRITICAL,
                    condition="cpu_percent > threshold",
                    threshold = self.config["cpu_threshold_critical"],
                    duration_seconds = 60,
                    cooldown_seconds = 180,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 5,
                            "severity": AlertSeverity.EMERGENCY,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                NotificationChannel.SMS,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["system", "performance", "cpu", "critical"],
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="high_memory_usage",
                    name="High Memory Usage",
                    description="Memory usage is above threshold",
                    category = AlertCategory.SYSTEM,
                    severity = AlertSeverity.WARNING,
                    condition="memory_percent > threshold",
                    threshold = self.config["memory_threshold_warning"],
                    duration_seconds = 180,
                    cooldown_seconds = 300,
                    enabled = True,
                    notification_channels=[NotificationChannel.EMAIL],
                    escalation_rules=[],
                    auto_resolve = True,
                    tags=["system", "performance", "memory"],
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="disk_space_low",
                    name="Low Disk Space",
                    description="Disk space is running low",
                    category = AlertCategory.SYSTEM,
                    severity = AlertSeverity.WARNING,
                    condition="disk_percent > threshold",
                    threshold = self.config["disk_threshold_warning"],
                    duration_seconds = 300,
                    cooldown_seconds = 1800,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 30,
                            "severity": AlertSeverity.CRITICAL,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["system", "storage", "disk"],
                    )
        )

        # Application monitoring rules
        self.register_alert_rule(
            AlertRule(
                rule_id="high_response_time",
                    name="High Response Time",
                    description="Application response time is above threshold",
                    category = AlertCategory.PERFORMANCE,
                    severity = AlertSeverity.WARNING,
                    condition="response_time_ms > threshold",
                    threshold = self.config["response_time_threshold_warning"],
                    duration_seconds = 120,
                    cooldown_seconds = 300,
                    enabled = True,
                    notification_channels=[NotificationChannel.EMAIL],
                    escalation_rules=[],
                    auto_resolve = True,
                    tags=["application", "performance", "response_time"],
                    )
        )

        self.register_alert_rule(
            AlertRule(
                rule_id="high_error_rate",
                    name="High Error Rate",
                    description="Application error rate is above threshold",
                    category = AlertCategory.APPLICATION,
                    severity = AlertSeverity.ERROR,
                    condition="error_rate > threshold",
                    threshold = self.config["error_rate_threshold_warning"],
                    duration_seconds = 60,
                    cooldown_seconds = 180,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 10,
                            "severity": AlertSeverity.CRITICAL,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["application", "errors", "reliability"],
                    )
        )

        # Security monitoring rules
        self.register_alert_rule(
            AlertRule(
                rule_id="security_threat_detected",
                    name="Security Threat Detected",
                    description="Security monitoring detected a potential threat",
                    category = AlertCategory.SECURITY,
                    severity = AlertSeverity.CRITICAL,
                    condition="threat_level >= threshold",
                    threshold = 3.0,  # High threat level
                duration_seconds = 0,  # Immediate
                cooldown_seconds = 60,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 5,
                            "severity": AlertSeverity.EMERGENCY,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                NotificationChannel.SMS,
                                ],
                            }
                ],
                    auto_resolve = False,  # Manual resolution required
                tags=["security", "threat", "critical"],
                    )
        )

        # Compliance monitoring rules
        self.register_alert_rule(
            AlertRule(
                rule_id="compliance_violation",
                    name="Compliance Violation",
                    description="System is not compliant with required rules",
                    category = AlertCategory.COMPLIANCE,
                    severity = AlertSeverity.ERROR,
                    condition="compliance_score < threshold",
                    threshold = 95.0,  # 95% compliance required
                duration_seconds = 300,
                    cooldown_seconds = 600,
                    enabled = True,
                    notification_channels=[NotificationChannel.EMAIL],
                    escalation_rules=[
                    {
                        "after_minutes": 30,
                            "severity": AlertSeverity.CRITICAL,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["compliance", "governance", "audit"],
                    )
        )

        # Health check rules
        self.register_alert_rule(
            AlertRule(
                rule_id="service_unavailable",
                    name="Service Unavailable",
                    description="Critical service is unavailable",
                    category = AlertCategory.INFRASTRUCTURE,
                    severity = AlertSeverity.CRITICAL,
                    condition="availability < threshold",
                    threshold = self.config["availability_threshold_critical"],
                    duration_seconds = 30,
                    cooldown_seconds = 120,
                    enabled = True,
                    notification_channels=[
                    NotificationChannel.EMAIL,
                        NotificationChannel.SLACK,
                        ],
                    escalation_rules=[
                    {
                        "after_minutes": 2,
                            "severity": AlertSeverity.EMERGENCY,
                            "channels": [
                            NotificationChannel.EMAIL,
                                NotificationChannel.SLACK,
                                NotificationChannel.SMS,
                                ],
                            }
                ],
                    auto_resolve = True,
                    tags=["infrastructure", "availability", "critical"],
                    )
        )


    def _setup_notification_channels(self):
        """Setup notification channels"""

        # Email notification
        if self.config["email_username"] and self.config["email_password"]:
            self.notification_channels[NotificationChannel.EMAIL] = {
                "enabled": True,
                    "config": {
                    "smtp_server": self.config["email_smtp_server"],
                        "smtp_port": self.config["email_smtp_port"],
                        "username": self.config["email_username"],
                        "password": self.config["email_password"],
                        "from_email": self.config["email_from"],
                        "to_emails": self.config["email_to"],
                        },
                    }

        # Slack notification
        if self.config["slack_webhook_url"]:
            self.notification_channels[NotificationChannel.SLACK] = {
                "enabled": True,
                    "config": {"webhook_url": self.config["slack_webhook_url"]},
                    }

        # Discord notification
        if self.config["discord_webhook_url"]:
            self.notification_channels[NotificationChannel.DISCORD] = {
                "enabled": True,
                    "config": {"webhook_url": self.config["discord_webhook_url"]},
                    }

        # Webhook notifications
        if self.config["webhook_endpoints"]:
            self.notification_channels[NotificationChannel.WEBHOOK] = {
                "enabled": True,
                    "config": {
                    "endpoints": [
                        url.strip()
                        for url in self.config["webhook_endpoints"]
                        if url.strip()
                    ]
                },
                    }


    def register_alert_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Registered alert rule: {rule.rule_id}")


    def _start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target = self._monitoring_loop, daemon = True
            )
            self.monitoring_thread.start()
            self.logger.info("Alert monitoring started")


    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout = 5)
        self.logger.info("Alert monitoring stopped")


    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                if (
                    time.time() - self.last_metric_collection
                    >= self.config["metric_collection_interval"]
                ):
                    self._collect_metrics()
                    self.last_metric_collection = time.time()

                # Evaluate alert rules
                self._evaluate_alert_rules()

                # Process escalations
                self._process_escalations()

                # Auto - resolve alerts
                self._auto_resolve_alerts()

                # Cleanup old data
                self._cleanup_old_data()

                time.sleep(self.config["alert_evaluation_interval"])

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(10)  # Wait before retrying


    def _collect_metrics(self):
        """Collect system and application metrics"""
        try:
            current_time = time.time()

            # Collect system metrics
            if self.config["enable_system_monitoring"]:
                system_metrics = self._collect_system_metrics()
                self._store_metric(
                    "system.cpu_percent", system_metrics.cpu_percent, current_time
                )
                self._store_metric(
                    "system.memory_percent", system_metrics.memory_percent, current_time
                )
                self._store_metric(
                    "system.disk_percent", system_metrics.disk_percent, current_time
                )
                self._store_metric(
                    "system.process_count", system_metrics.process_count, current_time
                )
                self._store_metric(
                    "system.uptime_seconds", system_metrics.uptime_seconds, current_time
                )

                if system_metrics.load_average:
                    self._store_metric(
                        "system.load_average_1m",
                            system_metrics.load_average[0],
                            current_time,
                            )
                    if len(system_metrics.load_average) > 1:
                        self._store_metric(
                            "system.load_average_5m",
                                system_metrics.load_average[1],
                                current_time,
                                )
                    if len(system_metrics.load_average) > 2:
                        self._store_metric(
                            "system.load_average_15m",
                                system_metrics.load_average[2],
                                current_time,
                                )

            # Collect application metrics
            if self.config["enable_application_monitoring"]:
                app_metrics = self._collect_application_metrics()
                if app_metrics:
                    self._store_metric(
                        "app.request_count", app_metrics.request_count, current_time
                    )
                    self._store_metric(
                        "app.error_count", app_metrics.error_count, current_time
                    )
                    self._store_metric(
                        "app.response_time_ms",
                            app_metrics.response_time_ms,
                            current_time,
                            )
                    self._store_metric(
                        "app.active_connections",
                            app_metrics.active_connections,
                            current_time,
                            )
                    self._store_metric(
                        "app.queue_size", app_metrics.queue_size, current_time
                    )
                    self._store_metric(
                        "app.cache_hit_rate", app_metrics.cache_hit_rate, current_time
                    )
                    self._store_metric(
                        "app.database_connections",
                            app_metrics.database_connections,
                            current_time,
                            )

            # Collect health metrics
            health_status = health_monitor.get_system_health()
            self._store_metric(
                "health.overall_score", health_status.overall_health_score, current_time
            )
            self._store_metric(
                "health.availability",
                    100.0 if health_status.status == HealthStatus.HEALTHY else 0.0,
                    current_time,
                    )

            # Collect compliance metrics
            if self.config["enable_compliance_monitoring"]:
                compliance_report = compliance_monitor.get_compliance_report()
                self._store_metric(
                    "compliance.score",
                        compliance_report["overall_compliance_score"],
                        current_time,
                        )
                self._store_metric(
                    "compliance.violations",
                        len(compliance_report["violations"]),
                        current_time,
                        )

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")


    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval = 1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            network = psutil.net_io_counters()
            process_count = len(psutil.pids())

            # Get load average (Unix - like systems)
            load_average = []
            try:
                load_average = list(os.getloadavg())
            except (OSError, AttributeError):
                pass  # Not available on Windows

            # Get uptime
            uptime_seconds = time.time() - psutil.boot_time()

            return SystemMetrics(
                cpu_percent = cpu_percent,
                    memory_percent = memory.percent,
                    disk_percent = disk.percent,
                    network_io={
                    "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv,
                        },
                    process_count = process_count,
                    load_average = load_average,
                    uptime_seconds = uptime_seconds,
                    timestamp = time.time(),
                    )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            return SystemMetrics(
                cpu_percent = 0.0,
                    memory_percent = 0.0,
                    disk_percent = 0.0,
                    network_io={},
                    process_count = 0,
                    load_average=[],
                    uptime_seconds = 0.0,
                    timestamp = time.time(),
                    )


    def _collect_application_metrics(self) -> Optional[ApplicationMetrics]:
        """Collect application - specific metrics"""
        try:
            # This would typically integrate with your application's metrics endpoint
            # For now, return mock data or integrate with existing monitoring

            # Try to get metrics from health monitor
                health_status = health_monitor.get_system_health()

            return ApplicationMetrics(
                request_count = 0,  # Would come from web server metrics
                error_count = 0,  # Would come from error tracking
                response_time_ms = health_status.response_time_ms,
                    active_connections = 0,  # Would come from connection pool
                queue_size = 0,  # Would come from task queue
                cache_hit_rate = 0.0,  # Would come from cache metrics
                database_connections = 0,  # Would come from DB pool
                timestamp = time.time(),
                    )

        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {str(e)}")
            return None


    def _store_metric(self, metric_name: str, value: float, timestamp: float):
        """Store a metric point"""
        metric_point = MetricPoint(
            timestamp = timestamp, value = value, labels={"metric": metric_name}
        )

        self.metrics_buffer[metric_name].append(metric_point)

        # Cleanup old metrics
        cutoff_time = timestamp - (self.config["metrics_retention_hours"] * 3600)
        while (
            self.metrics_buffer[metric_name]
            and self.metrics_buffer[metric_name][0].timestamp < cutoff_time
        ):
            self.metrics_buffer[metric_name].popleft()


    def _evaluate_alert_rules(self):
        """Evaluate all alert rules against current metrics"""
        current_time = time.time()

        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            try:
                # Check if rule is in cooldown
                if self._is_rule_in_cooldown(rule_id, current_time):
                    continue

                # Evaluate rule condition
                should_alert = self._evaluate_rule_condition(rule, current_time)

                if should_alert:
                    # Check if alert already exists
                    existing_alert = self._get_active_alert(rule_id)

                    if not existing_alert:
                        # Create new alert
                        alert = self._create_alert(rule, current_time)
                        self.active_alerts[alert.alert_id] = alert
                        self._send_notifications(alert)

                        # Log alert creation
                        audit_logger.log_security_event(
                            event_type="alert_created",
                                severity = rule.severity.value,
                                additional_data={
                                "alert_id": alert.alert_id,
                                    "rule_id": rule_id,
                                    "category": rule.category.value,
                                    },
                                )
                else:
                    # Check if existing alert should be auto - resolved
                    existing_alert = self._get_active_alert(rule_id)
                    if existing_alert and rule.auto_resolve:
                        self._resolve_alert(existing_alert.alert_id, "auto_resolved")

            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule_id}: {str(e)}")


    def _evaluate_rule_condition(self, rule: AlertRule, current_time: float) -> bool:
        """Evaluate if a rule condition is met"""
        try:
            # Get relevant metrics for the rule
            context = self._build_evaluation_context(rule, current_time)

            # Evaluate the condition
            condition_code = rule.condition.replace("threshold", str(rule.threshold))

            # Create a safe evaluation environment
            safe_globals = {
                "__builtins__": {},
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "round": round,
                    "len": len,
                    }

            result = eval(condition_code, safe_globals, context)

            # Check duration requirement
            if rule.duration_seconds > 0:
                return self._check_condition_duration(rule, result, current_time)

            return bool(result)

        except Exception as e:
            self.logger.error(
                f"Error evaluating condition for rule {rule.rule_id}: {str(e)}"
            )
            return False


    def _build_evaluation_context(
        self, rule: AlertRule, current_time: float
    ) -> Dict[str, Any]:
        """Build context for rule evaluation"""
        context = {}

        # Add current metric values
        for metric_name, metric_buffer in self.metrics_buffer.items():
            if metric_buffer:
                latest_point = metric_buffer[-1]
                # Use metric name without prefix as variable name
                var_name = metric_name.split(".")[-1]
                context[var_name] = latest_point.value

        # Add calculated values
        if "system.cpu_percent" in self.metrics_buffer:
            context["cpu_percent"] = self._get_latest_metric_value("system.cpu_percent")

        if "system.memory_percent" in self.metrics_buffer:
            context["memory_percent"] = self._get_latest_metric_value(
                "system.memory_percent"
            )

        if "system.disk_percent" in self.metrics_buffer:
            context["disk_percent"] = self._get_latest_metric_value(
                "system.disk_percent"
            )

        if "app.response_time_ms" in self.metrics_buffer:
            context["response_time_ms"] = self._get_latest_metric_value(
                "app.response_time_ms"
            )

        if "health.availability" in self.metrics_buffer:
            context["availability"] = self._get_latest_metric_value(
                "health.availability"
            )

        if "compliance.score" in self.metrics_buffer:
            context["compliance_score"] = self._get_latest_metric_value(
                "compliance.score"
            )

        # Calculate error rate
        request_count = self._get_latest_metric_value("app.request_count", 0)
        error_count = self._get_latest_metric_value("app.error_count", 0)
        context["error_rate"] = (
            (error_count/request_count * 100) if request_count > 0 else 0
        )

        # Add threat level (would come from security monitoring)
        context["threat_level"] = 0  # Default to no threat

        return context


    def _get_latest_metric_value(self, metric_name: str, default: float = 0.0) -> float:
        """Get the latest value for a metric"""
        if metric_name in self.metrics_buffer and self.metrics_buffer[metric_name]:
            return self.metrics_buffer[metric_name][-1].value
        return default


    def _check_condition_duration(
        self, rule: AlertRule, condition_met: bool, current_time: float
    ) -> bool:
        """Check if condition has been met for required duration"""
        rule_state_key = f"condition_state_{rule.rule_id}"

        if not hasattr(self, "_rule_states"):
            self._rule_states = {}

        if condition_met:
            if rule_state_key not in self._rule_states:
                self._rule_states[rule_state_key] = current_time
                return False
            else:
                duration = current_time - self._rule_states[rule_state_key]
                return duration >= rule.duration_seconds
        else:
            # Condition not met, reset state
            if rule_state_key in self._rule_states:
                del self._rule_states[rule_state_key]
            return False


    def _is_rule_in_cooldown(self, rule_id: str, current_time: float) -> bool:
        """Check if rule is in cooldown period"""
        cooldown_key = f"cooldown_{rule_id}"

        if not hasattr(self, "_cooldown_states"):
            self._cooldown_states = {}

        if cooldown_key in self._cooldown_states:
            rule = self.alert_rules[rule_id]
            time_since_last_alert = current_time - self._cooldown_states[cooldown_key]
            return time_since_last_alert < rule.cooldown_seconds

        return False


    def _get_active_alert(self, rule_id: str) -> Optional[Alert]:
        """Get active alert for a rule"""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                return alert
        return None


    def _create_alert(self, rule: AlertRule, current_time: float) -> Alert:
        """Create a new alert"""
        alert_id = f"alert_{rule.rule_id}_{int(current_time)}"

        # Get current metric value for context
        context = self._build_evaluation_context(rule, current_time)
        current_value = context.get(rule.condition.split()[0], 0.0)

        alert = Alert(
            alert_id = alert_id,
                rule_id = rule.rule_id,
                title = rule.name,
                description = rule.description,
                category = rule.category,
                severity = rule.severity,
                status = AlertStatus.ACTIVE,
                created_at = datetime.fromtimestamp(current_time).isoformat(),
                updated_at = datetime.fromtimestamp(current_time).isoformat(),
                resolved_at = None,
                acknowledged_at = None,
                acknowledged_by = None,
                current_value = current_value,
                threshold = rule.threshold,
                metadata={
                "rule_tags": rule.tags,
                    "evaluation_context": context,
                    "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
                    },
                notification_history=[],
                escalation_level = 0,
                )

        # Update cooldown state
        if not hasattr(self, "_cooldown_states"):
            self._cooldown_states = {}
        self._cooldown_states[f"cooldown_{rule.rule_id}"] = current_time

        # Update alert counter
        self.alert_counters[rule.rule_id] += 1

        return alert


    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        rule = self.alert_rules[alert.rule_id]

        for channel in rule.notification_channels:
            try:
                if (
                    channel in self.notification_channels
                    and self.notification_channels[channel]["enabled"]
                ):
                    success = self._send_notification(channel, alert)

                    # Record notification attempt
                    notification_record = {
                        "channel": channel.value,
                            "timestamp": datetime.now().isoformat(),
                            "success": success,
                            "attempt": 1,
                            }

                    alert.notification_history.append(notification_record)

                    if not success:
                        # Retry logic could be implemented here
                        self.logger.warning(
                            f"Failed to send notification via {channel.value} for alert {alert.alert_id}"
                        )

            except Exception as e:
                self.logger.error(
                    f"Error sending notification via {channel.value}: {str(e)}"
                )


    def _send_notification(self, channel: NotificationChannel, alert: Alert) -> bool:
        """Send notification via specific channel"""
        try:
            if channel == NotificationChannel.EMAIL:
                return self._send_email_notification(alert)
            elif channel == NotificationChannel.SLACK:
                return self._send_slack_notification(alert)
            elif channel == NotificationChannel.DISCORD:
                return self._send_discord_notification(alert)
            elif channel == NotificationChannel.WEBHOOK:
                return self._send_webhook_notification(alert)
            else:
                self.logger.warning(
                    f"Unsupported notification channel: {channel.value}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error in {channel.value} notification: {str(e)}")
            return False


    def _send_email_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            config = self.notification_channels[NotificationChannel.EMAIL]["config"]

            # Create message
            msg = MIMEMultipart()
            msg["From"] = config["from_email"]
            msg["To"] = ", ".join(config["to_emails"])
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create email body
            body = f"""
Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Category: {alert.category.value}
Description: {alert.description}

Current Value: {alert.current_value}
Threshold: {alert.threshold}

Created: {alert.created_at}
Alert ID: {alert.alert_id}

Metadata:
{json.dumps(alert.metadata, indent = 2)}

---
This is an automated alert from the monitoring system.
"""

            msg.attach(MIMEText(body, "plain"))

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls(context = context)
                server.login(config["username"], config["password"])
                server.send_message(msg)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            return False


    def _send_slack_notification(self, alert: Alert) -> bool:
        """Send Slack notification"""
        try:
            config = self.notification_channels[NotificationChannel.SLACK]["config"]

            # Create Slack message
            color = {
                AlertSeverity.INFO: "good",
                    AlertSeverity.WARNING: "warning",
                    AlertSeverity.ERROR: "danger",
                    AlertSeverity.CRITICAL: "danger",
                    AlertSeverity.EMERGENCY: "danger",
                    }.get(alert.severity, "warning")

            payload = {
                "text": f"Alert: {alert.title}",
                    "attachments": [
                    {
                        "color": color,
                            "fields": [
                            {
                                "title": "Severity",
                                    "value": alert.severity.value.upper(),
                                    "short": True,
                                    },
                                {
                                "title": "Category",
                                    "value": alert.category.value,
                                    "short": True,
                                    },
                                {
                                "title": "Current Value",
                                    "value": str(alert.current_value),
                                    "short": True,
                                    },
                                {
                                "title": "Threshold",
                                    "value": str(alert.threshold),
                                    "short": True,
                                    },
                                {
                                "title": "Description",
                                    "value": alert.description,
                                    "short": False,
                                    },
                                {
                                "title": "Alert ID",
                                    "value": alert.alert_id,
                                    "short": False,
                                    },
                                ],
                            "ts": int(time.time()),
                            }
                ],
                    }

            # Send to Slack

            import requests

            response = requests.post(config["webhook_url"],
    json = payload,
    timeout = 10)
            response.raise_for_status()

            return True

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
            return False


    def _send_discord_notification(self, alert: Alert) -> bool:
        """Send Discord notification"""
        try:
            config = self.notification_channels[NotificationChannel.DISCORD]["config"]

            # Create Discord embed
            color = {
                AlertSeverity.INFO: 0x00FF00,  # Green
                AlertSeverity.WARNING: 0xFFFF00,  # Yellow
                AlertSeverity.ERROR: 0xFF8000,  # Orange
                AlertSeverity.CRITICAL: 0xFF0000,  # Red
                AlertSeverity.EMERGENCY: 0x800080,  # Purple
            }.get(alert.severity, 0xFFFF00)

            payload = {
                "embeds": [
                    {
                        "title": f"🚨 {alert.title}",
                            "description": alert.description,
                            "color": color,
                            "fields": [
                            {
                                "name": "Severity",
                                    "value": alert.severity.value.upper(),
                                    "inline": True,
                                    },
                                {
                                "name": "Category",
                                    "value": alert.category.value,
                                    "inline": True,
                                    },
                                {
                                "name": "Current Value",
                                    "value": str(alert.current_value),
                                    "inline": True,
                                    },
                                {
                                "name": "Threshold",
                                    "value": str(alert.threshold),
                                    "inline": True,
                                    },
                                {
                                "name": "Alert ID",
                                    "value": f"`{alert.alert_id}`",
                                    "inline": False,
                                    },
                                ],
                            "timestamp": alert.created_at,
                            "footer": {"text": "Monitoring System"},
                            }
                ]
            }

            # Send to Discord

            import requests

            response = requests.post(config["webhook_url"],
    json = payload,
    timeout = 10)
            response.raise_for_status()

            return True

        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {str(e)}")
            return False


    def _send_webhook_notification(self, alert: Alert) -> bool:
        """Send webhook notification"""
        try:
            config = self.notification_channels[NotificationChannel.WEBHOOK]["config"]

            # Create webhook payload
            payload = {
                "alert_id": alert.alert_id,
                    "rule_id": alert.rule_id,
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity.value,
                    "category": alert.category.value,
                    "status": alert.status.value,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "created_at": alert.created_at,
                    "metadata": alert.metadata,
                    }

            # Send to all webhook endpoints

            import requests

            success_count = 0

            for endpoint in config["endpoints"]:
                try:
                    response = requests.post(endpoint, json = payload, timeout = 10)
                    response.raise_for_status()
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send webhook to {endpoint}: {str(e)}")

            return success_count > 0

        except Exception as e:
            self.logger.error(f"Failed to send webhook notifications: {str(e)}")
            return False


    def _process_escalations(self):
        """Process alert escalations"""
        current_time = time.time()

        for alert in list(self.active_alerts.values()):
            if alert.status != AlertStatus.ACTIVE:
                continue

            rule = self.alert_rules.get(alert.rule_id)
            if not rule or not rule.escalation_rules:
                continue

            # Check if escalation is needed
            alert_age_minutes = (
                current_time - datetime.fromisoformat(alert.created_at).timestamp()
            )/60

            for escalation in rule.escalation_rules:
                if alert_age_minutes >= escalation[
                    "after_minutes"
                ] and alert.escalation_level < len(rule.escalation_rules):

                    # Escalate alert
                    alert.severity = AlertSeverity(escalation["severity"])
                    alert.escalation_level += 1
                    alert.updated_at = datetime.fromtimestamp(current_time).isoformat()

                    # Send escalation notifications
                    for channel_name in escalation["channels"]:
                        try:
                            channel = NotificationChannel(channel_name)
                            if channel in self.notification_channels:
                                self._send_notification(channel, alert)
                        except ValueError:
                            self.logger.warning(
                                f"Unknown notification channel in escalation: {channel_name}"
                            )

                    # Log escalation
                    audit_logger.log_security_event(
                        event_type="alert_escalated",
                            severity = alert.severity.value,
                            additional_data={
                            "alert_id": alert.alert_id,
                                "escalation_level": alert.escalation_level,
                                "new_severity": alert.severity.value,
                                },
                            )

                    break


    def _auto_resolve_alerts(self):
        """Auto - resolve alerts that meet resolution criteria"""
        current_time = time.time()

        for alert_id, alert in list(self.active_alerts.items()):
            if alert.status != AlertStatus.ACTIVE:
                continue

            rule = self.alert_rules.get(alert.rule_id)
            if not rule or not rule.auto_resolve:
                continue

            # Check if condition is no longer met
            condition_met = self._evaluate_rule_condition(rule, current_time)

            if not condition_met:
                # Check auto - resolve timeout
                alert_age_minutes = (
                    current_time - datetime.fromisoformat(alert.created_at).timestamp()
                )/60

                if alert_age_minutes >= self.config["auto_resolve_timeout_minutes"]:
                    self._resolve_alert(alert_id, "auto_resolved")


    def _resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now().isoformat()
            alert.updated_at = datetime.now().isoformat()

            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]

            # Log resolution
            audit_logger.log_security_event(
                event_type="alert_resolved",
                    severity="info",
                    additional_data={
                    "alert_id": alert_id,
                        "resolved_by": resolved_by,
                        "duration_minutes": (
                        datetime.fromisoformat(alert.resolved_at).timestamp()
                        - datetime.fromisoformat(alert.created_at).timestamp()
                    )/60,
                        },
                    )

            self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")


    def _cleanup_old_data(self):
        """Cleanup old alerts and metrics"""
        current_time = time.time()
        cutoff_time = current_time - (
            self.config["alert_history_retention_days"] * 24 * 3600
        )

        # Cleanup old alert history
        while (
            self.alert_history
            and datetime.fromisoformat(self.alert_history[0].created_at).timestamp()
            < cutoff_time
        ):
            self.alert_history.popleft()

        # Cleanup old metrics (already handled in _store_metric)
        self.logger.debug("Metric cleanup completed")


    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now().isoformat()
            alert.acknowledged_by = acknowledged_by
            alert.updated_at = datetime.now().isoformat()

            # Log acknowledgment
            audit_logger.log_security_event(
                event_type="alert_acknowledged",
                    severity="info",
                    additional_data={
                    "alert_id": alert_id,
                        "acknowledged_by": acknowledged_by,
                        },
                    )

            return True

        return False


    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())


    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]


    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        current_time = time.time()

        # Calculate uptime
        uptime_seconds = self._get_latest_metric_value("system.uptime_seconds", 0)

        # Get recent alerts
        recent_alerts = [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert.created_at).timestamp()
            > current_time - 24 * 3600
        ]

        # Calculate alert statistics
        alert_stats = {
            "total_alerts_24h": len(recent_alerts),
                "critical_alerts_24h": len(
                [a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]
            ),
                "active_alerts": len(self.active_alerts),
                "acknowledged_alerts": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if a.status == AlertStatus.ACKNOWLEDGED
                ]
            ),
                }

        # Get current system status
        system_status = {
            "cpu_percent": self._get_latest_metric_value("system.cpu_percent"),
                "memory_percent": self._get_latest_metric_value("system.memory_percent"),
                "disk_percent": self._get_latest_metric_value("system.disk_percent"),
                "uptime_hours": uptime_seconds/3600,
                "health_score": self._get_latest_metric_value("health.overall_score"),
                "compliance_score": self._get_latest_metric_value("compliance.score"),
                }

        return {
            "report_id": f"monitoring_{datetime.now().strftime('%Y % m%d_ % H%M % S')}",
                "timestamp": datetime.now().isoformat(),
                "monitoring_status": {
                "active": self.monitoring_active,
                    "uptime_hours": uptime_seconds/3600,
                    "last_metric_collection": datetime.fromtimestamp(
                    self.last_metric_collection
                ).isoformat(),
                    },
                "system_status": system_status,
                "alert_statistics": alert_stats,
                "active_alerts": [asdict(alert) for alert in self.active_alerts.values()],
                "notification_channels": {
                channel.value: config["enabled"]
                for channel, config in self.notification_channels.items()
            },
                "alert_rules": {
                "total_rules": len(self.alert_rules),
                    "enabled_rules": len(
                    [r for r in self.alert_rules.values() if r.enabled]
                ),
                    "rule_summary": {
                    rule_id: {
                        "name": rule.name,
                            "enabled": rule.enabled,
                            "severity": rule.severity.value,
                            "category": rule.category.value,
                            }
                    for rule_id, rule in self.alert_rules.items()
                },
                    },
                "performance_metrics": {
                "metrics_collected": len(self.metrics_buffer),
                    "total_metric_points": sum(
                    len(buffer) for buffer in self.metrics_buffer.values()
                ),
                    "avg_evaluation_time_ms": 0,  # Would need to track this
            },
                }

# Global alert manager instance
alert_manager = AlertManager()

# Convenience functions


def create_custom_alert(
    title: str,
        description: str,
        severity: AlertSeverity,
        category: AlertCategory = AlertCategory.APPLICATION,
) -> str:
    """Create a custom alert"""
    alert_id = f"custom_{int(time.time())}"

    alert = Alert(
        alert_id = alert_id,
            rule_id="custom",
            title = title,
            description = description,
            category = category,
            severity = severity,
            status = AlertStatus.ACTIVE,
            created_at = datetime.now().isoformat(),
            updated_at = datetime.now().isoformat(),
            resolved_at = None,
            acknowledged_at = None,
            acknowledged_by = None,
            current_value = 0.0,
            threshold = 0.0,
            metadata={"custom": True},
            notification_history=[],
            escalation_level = 0,
            )

    alert_manager.active_alerts[alert_id] = alert
    alert_manager._send_notifications(alert)

    return alert_id


def get_system_health_summary() -> Dict[str, Any]:
    """Get system health summary"""
    return {
        "cpu_percent": alert_manager._get_latest_metric_value("system.cpu_percent"),
            "memory_percent": alert_manager._get_latest_metric_value(
            "system.memory_percent"
        ),
            "disk_percent": alert_manager._get_latest_metric_value("system.disk_percent"),
            "health_score": alert_manager._get_latest_metric_value("health.overall_score"),
            "active_alerts": len(alert_manager.active_alerts),
            "monitoring_active": alert_manager.monitoring_active,
            }