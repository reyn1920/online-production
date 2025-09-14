#!/usr/bin/env python3
"""
Zero - Cost Monitoring Stack

Implements comprehensive monitoring and analytics using:
- Prometheus metrics collection
- Grafana dashboards for visualization
- Custom metrics for web scraping and API discovery
- Performance tracking and alerting
- Resource usage monitoring
- Health checks and uptime monitoring
"""

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
import yaml

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
        push_to_gateway,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    logging.warning("Prometheus client not available. Metrics collection will be limited.")
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Summary = Info = None
    CollectorRegistry = generate_latest = CONTENT_TYPE_LATEST = None
    start_http_server = push_to_gateway = None

try:
    import requests

except ImportError:
    requests = None


class MetricType(Enum):
    """Types of metrics to collect"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricDefinition:
    """Definition of a custom metric"""

    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    unit: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    metric_name: str
    condition: str  # e.g., "> 0.8", "< 100"
    severity: AlertSeverity
    description: str
    duration: int = 300  # Seconds
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for monitoring stack"""

    prometheus_port: int = 8000
    metrics_path: str = "/metrics"
    scrape_interval: int = 15  # Seconds
    retention_days: int = 15
    enable_push_gateway: bool = False
    push_gateway_url: Optional[str] = None
    grafana_config: Dict[str, Any] = field(default_factory=dict)
    alert_rules: List[AlertRule] = field(default_factory=list)
    custom_metrics: List[MetricDefinition] = field(default_factory=list)
    enable_system_metrics: bool = True
    enable_application_metrics: bool = True
    log_level: str = "INFO"


class MetricsCollector:
    """Collects and manages Prometheus metrics"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self.metrics: Dict[str, Any] = {}
        self.custom_metrics: Dict[str, Any] = {}
        self.is_running = False
        self.collection_thread = None

        if PROMETHEUS_AVAILABLE:
            self._initialize_default_metrics()
            self._initialize_custom_metrics()

    def _initialize_default_metrics(self):
        """Initialize default system and application metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        # System metrics
        if self.config.enable_system_metrics:
            self.metrics.update(
                {
                    "system_cpu_usage": Gauge(
                        "system_cpu_usage_percent",
                        "System CPU usage percentage",
                        registry=self.registry,
                    ),
                    "system_memory_usage": Gauge(
                        "system_memory_usage_bytes",
                        "System memory usage in bytes",
                        ["type"],
                        registry=self.registry,
                    ),
                    "system_disk_usage": Gauge(
                        "system_disk_usage_bytes",
                        "System disk usage in bytes",
                        ["device", "type"],
                        registry=self.registry,
                    ),
                    "system_network_io": Counter(
                        "system_network_io_bytes_total",
                        "System network I/O in bytes",
                        ["direction"],
                        registry=self.registry,
                    ),
                    "system_uptime": Gauge(
                        "system_uptime_seconds",
                        "System uptime in seconds",
                        registry=self.registry,
                    ),
                }
            )

        # Application metrics
        if self.config.enable_application_metrics:
            self.metrics.update(
                {
                    "scraping_requests_total": Counter(
                        "scraping_requests_total",
                        "Total number of scraping requests",
                        ["method", "status", "source"],
                        registry=self.registry,
                    ),
                    "scraping_duration": Histogram(
                        "scraping_duration_seconds",
                        "Time spent on scraping requests",
                        ["method", "source"],
                        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
                        registry=self.registry,
                    ),
                    "api_discovery_total": Counter(
                        "api_discovery_total",
                        "Total number of APIs discovered",
                        ["source", "category", "status"],
                        registry=self.registry,
                    ),
                    "api_validation_duration": Histogram(
                        "api_validation_duration_seconds",
                        "Time spent validating APIs",
                        ["source"],
                        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
                        registry=self.registry,
                    ),
                    "cache_operations": Counter(
                        "cache_operations_total",
                        "Total cache operations",
                        ["operation", "result"],
                        registry=self.registry,
                    ),
                    "active_connections": Gauge(
                        "active_connections",
                        "Number of active connections",
                        ["type"],
                        registry=self.registry,
                    ),
                    "error_rate": Counter(
                        "errors_total",
                        "Total number of errors",
                        ["component", "error_type"],
                        registry=self.registry,
                    ),
                    "queue_size": Gauge(
                        "queue_size",
                        "Size of processing queues",
                        ["queue_name"],
                        registry=self.registry,
                    ),
                }
            )

    def _initialize_custom_metrics(self):
        """Initialize custom metrics from configuration"""
        if not PROMETHEUS_AVAILABLE:
            return

        for metric_def in self.config.custom_metrics:
            try:
                if metric_def.metric_type == MetricType.COUNTER:
                    metric = Counter(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        registry=self.registry,
                    )
                elif metric_def.metric_type == MetricType.GAUGE:
                    metric = Gauge(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        registry=self.registry,
                    )
                elif metric_def.metric_type == MetricType.HISTOGRAM:
                    metric = Histogram(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        buckets=metric_def.buckets,
                        registry=self.registry,
                    )
                elif metric_def.metric_type == MetricType.SUMMARY:
                    metric = Summary(
                        metric_def.name,
                        metric_def.description,
                        metric_def.labels,
                        registry=self.registry,
                    )
                elif metric_def.metric_type == MetricType.INFO:
                    metric = Info(metric_def.name, metric_def.description, registry=self.registry)
                else:
                    continue

                self.custom_metrics[metric_def.name] = metric

            except Exception as e:
                self.logger.error(f"Failed to initialize custom metric {metric_def.name}: {e}")

    def record_scraping_request(self, method: str, status: str, source: str, duration: float):
        """Record a scraping request metric"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["scraping_requests_total"].labels(
                method=method, status=status, source=source
            ).inc()

            self.metrics["scraping_duration"].labels(method=method, source=source).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to record scraping metrics: {e}")

    def record_api_discovery(self, source: str, category: str, status: str, count: int = 1):
        """Record API discovery metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["api_discovery_total"].labels(
                source=source, category=category, status=status
            ).inc(count)
        except Exception as e:
            self.logger.error(f"Failed to record API discovery metrics: {e}")

    def record_api_validation(self, source: str, duration: float):
        """Record API validation metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["api_validation_duration"].labels(source=source).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to record API validation metrics: {e}")

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["cache_operations"].labels(operation=operation, result=result).inc()
        except Exception as e:
            self.logger.error(f"Failed to record cache metrics: {e}")

    def record_error(self, component: str, error_type: str):
        """Record error metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["error_rate"].labels(component=component, error_type=error_type).inc()
        except Exception as e:
            self.logger.error(f"Failed to record error metrics: {e}")

    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["queue_size"].labels(queue_name=queue_name).set(size)
        except Exception as e:
            self.logger.error(f"Failed to update queue size metrics: {e}")

    def update_active_connections(self, connection_type: str, count: int):
        """Update active connections metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics["active_connections"].labels(type=connection_type).set(count)
        except Exception as e:
            self.logger.error(f"Failed to update connection metrics: {e}")

    def collect_system_metrics(self):
        """Collect system - level metrics"""
        if not PROMETHEUS_AVAILABLE or not self.config.enable_system_metrics:
            return

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics["system_cpu_usage"].set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics["system_memory_usage"].labels(type="used").set(memory.used)
            self.metrics["system_memory_usage"].labels(type="available").set(memory.available)
            self.metrics["system_memory_usage"].labels(type="total").set(memory.total)

            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    device = partition.device.replace("/", "_")
                    self.metrics["system_disk_usage"].labels(device=device, type="used").set(
                        usage.used
                    )
                    self.metrics["system_disk_usage"].labels(device=device, type="free").set(
                        usage.free
                    )
                    self.metrics["system_disk_usage"].labels(device=device, type="total").set(
                        usage.total
                    )
                except (PermissionError, FileNotFoundError):
                    continue

            # Network I/O
            network = psutil.net_io_counters()
            self.metrics["system_network_io"].labels(
                direction="sent"
            )._value._value = network.bytes_sent
            self.metrics["system_network_io"].labels(
                direction="recv"
            )._value._value = network.bytes_recv

            # System uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            self.metrics["system_uptime"].set(uptime)

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    def start_collection(self):
        """Start metrics collection in background thread"""
        if self.is_running:
            return

        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        self.logger.info("Started metrics collection")

    def stop_collection(self):
        """Stop metrics collection"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        self.logger.info("Stopped metrics collection")

    def _collection_loop(self):
        """Background loop for collecting metrics"""
        while self.is_running:
            try:
                self.collect_system_metrics()
                time.sleep(self.config.scrape_interval)
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(5)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus not available\\n"

        return generate_latest(self.registry)


class AlertManager:
    """Manages alerts based on metric thresholds"""

    def __init__(self, config: MonitoringConfig, metrics_collector: MetricsCollector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        self.alert_states: Dict[str, Dict] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.is_running = False
        self.alert_thread = None

    def start_monitoring(self):
        """Start alert monitoring"""
        if self.is_running or not self.config.alert_rules:
            return

        self.is_running = True
        self.alert_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.alert_thread.start()
        self.logger.info("Started alert monitoring")

    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_running = False
        if self.alert_thread:
            self.alert_thread.join(timeout=5)
        self.logger.info("Stopped alert monitoring")

    def _monitoring_loop(self):
        """Background loop for monitoring alerts"""
        while self.is_running:
            try:
                self._check_alert_rules()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in alert monitoring loop: {e}")
                time.sleep(5)

    def _check_alert_rules(self):
        """Check all alert rules"""
        for rule in self.config.alert_rules:
            try:
                self._evaluate_alert_rule(rule)
            except Exception as e:
                self.logger.error(f"Failed to evaluate alert rule {rule.name}: {e}")

    def _evaluate_alert_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        # This is a simplified implementation
        # In practice, you'd need to query the actual metric values

        metric_name = rule.metric_name
        condition = rule.condition

        # Get current metric value (simplified)
        current_value = self._get_metric_value(metric_name)
        if current_value is None:
            return

        # Evaluate condition
        is_alerting = self._evaluate_condition(current_value, condition)

        # Update alert state
        alert_key = f"{rule.name}_{metric_name}"
        current_time = datetime.now()

        if alert_key not in self.alert_states:
            self.alert_states[alert_key] = {
                "is_firing": False,
                "started_at": None,
                "last_evaluation": current_time,
            }

        alert_state = self.alert_states[alert_key]

        if is_alerting and not alert_state["is_firing"]:
            # Alert started
            alert_state["is_firing"] = True
            alert_state["started_at"] = current_time

            # Check if duration threshold is met
            if rule.duration == 0:
                self._fire_alert(rule, current_value)

        elif is_alerting and alert_state["is_firing"]:
            # Alert continuing
            duration = (current_time - alert_state["started_at"]).total_seconds()
            if duration >= rule.duration:
                self._fire_alert(rule, current_value)

        elif not is_alerting and alert_state["is_firing"]:
            # Alert resolved
            alert_state["is_firing"] = False
            alert_state["started_at"] = None
            self._resolve_alert(rule, current_value)

        alert_state["last_evaluation"] = current_time

    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value of a metric (simplified implementation)"""
        # This would need to be implemented based on your metric storage
        # For now, return a dummy value
        return 0.5

    def _evaluate_condition(self, value: float, condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            # Format: "> 0.8", "< 100", "== 0", etc.
            if condition.startswith(">"):
                threshold = float(condition[1:].strip())
                return value > threshold
            elif condition.startswith("<"):
                threshold = float(condition[1:].strip())
                return value < threshold
            elif condition.startswith("=="):
                threshold = float(condition[2:].strip())
                return value == threshold
            elif condition.startswith("!="):
                threshold = float(condition[2:].strip())
                return value != threshold
            else:
                return False
        except (ValueError, IndexError):
            return False

    def _fire_alert(self, rule: AlertRule, value: float):
        """Fire an alert"""
        alert = {
            "rule_name": rule.name,
            "metric_name": rule.metric_name,
            "severity": rule.severity.value,
            "description": rule.description,
            "current_value": value,
            "condition": rule.condition,
            "timestamp": datetime.now(),
            "labels": rule.labels,
            "status": "firing",
        }

        self.alert_history.append(alert)

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(rule.severity, logging.WARNING)

        self.logger.log(
            log_level,
            f"ALERT FIRING: {rule.name} - {rule.description} (value: {value}, condition: {rule.condition})",
        )

        # Send alert notification (implement as needed)
        self._send_alert_notification(alert)

    def _resolve_alert(self, rule: AlertRule, value: float):
        """Resolve an alert"""
        alert = {
            "rule_name": rule.name,
            "metric_name": rule.metric_name,
            "severity": rule.severity.value,
            "description": rule.description,
            "current_value": value,
            "condition": rule.condition,
            "timestamp": datetime.now(),
            "labels": rule.labels,
            "status": "resolved",
        }

        self.alert_history.append(alert)

        self.logger.info(f"ALERT RESOLVED: {rule.name} - {rule.description} (value: {value})")

    def _send_alert_notification(self, alert: Dict):
        """Send alert notification (implement based on your needs)"""
        # This could send emails, Slack messages, webhooks, etc.
        try:
            # Log the alert for now - can be extended to send actual notifications
            severity = alert.get("severity", "unknown")
            message = alert.get("message", "No message")
            metric_name = alert.get("metric_name", "unknown")

            log_message = f"ALERT [{severity.upper()}] {metric_name}: {message}"

            if severity in ["critical", "error"]:
                logging.error(log_message)
            elif severity == "warning":
                logging.warning(log_message)
            else:
                logging.info(log_message)

            # Future implementations could add:
            # - Email notifications via SMTP
            # - Slack webhook notifications
            # - Discord webhook notifications
            # - Custom webhook endpoints
            # - SMS notifications via Twilio

        except Exception as e:
            logging.error(f"Failed to send alert notification: {e}")

    def get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts"""
        active_alerts = []
        for alert in self.alert_history:
            if alert["status"] == "firing":
                # Check if this alert is still active
                is_still_active = any(state["is_firing"] for state in self.alert_states.values())
                if is_still_active:
                    active_alerts.append(alert)

        return active_alerts


class GrafanaDashboardGenerator:
    """Generates Grafana dashboard configurations"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_system_dashboard(self) -> Dict:
        """Generate system monitoring dashboard"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "System Monitoring",
                "tags": ["system", "monitoring"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "CPU Usage",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "system_cpu_usage_percent",
                                "legendFormat": "CPU %",
                            }
                        ],
                        "fieldConfig": {"defaults": {"unit": "percent", "min": 0, "max": 100}},
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "Memory Usage",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "system_memory_usage_bytes{type='used'}",
                                "legendFormat": "Used",
                            },
                            {
                                "expr": "system_memory_usage_bytes{type='available'}",
                                "legendFormat": "Available",
                            },
                        ],
                        "fieldConfig": {"defaults": {"unit": "bytes"}},
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "Network I/O",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(system_network_io_bytes_total[5m])",
                                "legendFormat": "{{direction}}",
                            }
                        ],
                        "fieldConfig": {"defaults": {"unit": "Bps"}},
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                    },
                ],
                "time": {"from": "now - 1h", "to": "now"},
                "refresh": "5s",
            }
        }

        return dashboard

    def generate_application_dashboard(self) -> Dict:
        """Generate application monitoring dashboard"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Application Monitoring",
                "tags": ["application", "scraping", "api"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Scraping Requests Rate",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(scraping_requests_total[5m])",
                                "legendFormat": "{{method}} - {{status}}",
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    },
                    {
                        "id": 2,
                        "title": "Scraping Duration",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(scraping_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile",
                            },
                            {
                                "expr": "histogram_quantile(0.50, rate(scraping_duration_seconds_bucket[5m]))",
                                "legendFormat": "50th percentile",
                            },
                        ],
                        "fieldConfig": {"defaults": {"unit": "s"}},
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    },
                    {
                        "id": 3,
                        "title": "API Discovery Rate",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(api_discovery_total[5m])",
                                "legendFormat": "{{source}} - {{category}}",
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    },
                    {
                        "id": 4,
                        "title": "Error Rate",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(errors_total[5m])",
                                "legendFormat": "{{component}} - {{error_type}}",
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    },
                    {
                        "id": 5,
                        "title": "Cache Hit Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "rate(cache_operations_total{result='hit'}[5m])/rate(cache_operations_total[5m]) * 100",
                                "legendFormat": "Hit Rate %",
                            }
                        ],
                        "fieldConfig": {"defaults": {"unit": "percent", "min": 0, "max": 100}},
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                    },
                ],
                "time": {"from": "now - 1h", "to": "now"},
                "refresh": "5s",
            }
        }

        return dashboard

    def save_dashboard(self, dashboard: Dict, filename: str):
        """Save dashboard configuration to file"""
        try:
            with open(filename, "w") as f:
                json.dump(dashboard, f, indent=2)
            self.logger.info(f"Saved dashboard to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save dashboard: {e}")


class ZeroCostMonitoringStack:
    """Main monitoring stack orchestrator"""

    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.metrics_collector = MetricsCollector(self.config)
        self.alert_manager = AlertManager(self.config, self.metrics_collector)
        self.dashboard_generator = GrafanaDashboardGenerator(self.config)

        # HTTP server for metrics endpoint
        self.metrics_server = None
        self.is_running = False

    def start(self):
        """Start the monitoring stack"""
        if self.is_running:
            return

        try:
            # Start metrics collection
            self.metrics_collector.start_collection()

            # Start alert monitoring
            self.alert_manager.start_monitoring()

            # Start metrics HTTP server
            if PROMETHEUS_AVAILABLE:
                self._start_metrics_server()

            # Generate dashboards
            self._generate_dashboards()

            self.is_running = True
            self.logger.info("Zero - cost monitoring stack started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start monitoring stack: {e}")
            self.stop()

    def stop(self):
        """Stop the monitoring stack"""
        if not self.is_running:
            return

        try:
            # Stop components
            self.metrics_collector.stop_collection()
            self.alert_manager.stop_monitoring()

            # Stop metrics server
            if self.metrics_server:
                # Note: prometheus_client doesn't provide a clean way to stop the server
                # The server will be stopped when the process exits
                self.logger.info("Metrics server will stop when process exits")
                self.metrics_server = None

            self.is_running = False
            self.logger.info("Zero - cost monitoring stack stopped")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring stack: {e}")

    def _start_metrics_server(self):
        """Start HTTP server for metrics endpoint"""
        try:
            start_http_server(self.config.prometheus_port, registry=self.metrics_collector.registry)
            self.logger.info(f"Metrics server started on port {self.config.prometheus_port}")
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {e}")

    def _generate_dashboards(self):
        """Generate Grafana dashboards"""
        try:
            # Generate system dashboard
            system_dashboard = self.dashboard_generator.generate_system_dashboard()
            self.dashboard_generator.save_dashboard(
                system_dashboard, "grafana_system_dashboard.json"
            )

            # Generate application dashboard
            app_dashboard = self.dashboard_generator.generate_application_dashboard()
            self.dashboard_generator.save_dashboard(
                app_dashboard, "grafana_application_dashboard.json"
            )

            self.logger.info("Generated Grafana dashboards")

        except Exception as e:
            self.logger.error(f"Failed to generate dashboards: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the monitoring stack"""
        return {
            "is_running": self.is_running,
            "metrics_collector_running": self.metrics_collector.is_running,
            "alert_manager_running": self.alert_manager.is_running,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "metrics_port": self.config.prometheus_port,
            "uptime": time.time() - getattr(self, "_start_time", time.time()),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not PROMETHEUS_AVAILABLE:
            return {"error": "Prometheus not available"}

        try:
            metrics_text = self.metrics_collector.get_metrics()
            metric_count = len(
                [line for line in metrics_text.split("\\n") if line and not line.startswith("#")]
            )
            return {
                "total_metrics": metric_count,
                "system_metrics_enabled": self.config.enable_system_metrics,
                "application_metrics_enabled": self.config.enable_application_metrics,
                "custom_metrics_count": len(self.metrics_collector.custom_metrics),
                "scrape_interval": self.config.scrape_interval,
            }
        except Exception as e:
            return {"error": str(e)}


# Configuration helper functions


def create_default_config() -> MonitoringConfig:
    """Create default monitoring configuration"""
    alert_rules = [
        AlertRule(
            name="high_cpu_usage",
            metric_name="system_cpu_usage_percent",
            condition="> 80",
            severity=AlertSeverity.WARNING,
            description="CPU usage is above 80%",
            duration=300,
        ),
        AlertRule(
            name="high_error_rate",
            metric_name="errors_total",
            condition="> 10",
            severity=AlertSeverity.ERROR,
            description="Error rate is too high",
            duration=60,
        ),
        AlertRule(
            name="low_cache_hit_rate",
            metric_name="cache_hit_rate",
            condition="< 50",
            severity=AlertSeverity.WARNING,
            description="Cache hit rate is below 50%",
            duration=600,
        ),
    ]

    custom_metrics = [
        MetricDefinition(
            name="business_metric_revenue",
            metric_type=MetricType.GAUGE,
            description="Business revenue metric",
            labels=["source", "currency"],
            unit="currency",
        ),
        MetricDefinition(
            name="user_activity_events",
            metric_type=MetricType.COUNTER,
            description="User activity events",
            labels=["event_type", "user_segment"],
        ),
    ]

    return MonitoringConfig(
        prometheus_port=8000,
        scrape_interval=15,
        retention_days=15,
        alert_rules=alert_rules,
        custom_metrics=custom_metrics,
        enable_system_metrics=True,
        enable_application_metrics=True,
    )


def save_config(config: MonitoringConfig, filename: str = "monitoring_config.yaml"):
    """Save monitoring configuration to YAML file"""
    config_dict = {
        "prometheus_port": config.prometheus_port,
        "scrape_interval": config.scrape_interval,
        "retention_days": config.retention_days,
        "enable_push_gateway": config.enable_push_gateway,
        "push_gateway_url": config.push_gateway_url,
        "enable_system_metrics": config.enable_system_metrics,
        "enable_application_metrics": config.enable_application_metrics,
        "log_level": config.log_level,
        "alert_rules": [
            {
                "name": rule.name,
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "severity": rule.severity.value,
                "description": rule.description,
                "duration": rule.duration,
                "labels": rule.labels,
            }
            for rule in config.alert_rules
        ],
        "custom_metrics": [
            {
                "name": metric.name,
                "metric_type": metric.metric_type.value,
                "description": metric.description,
                "labels": metric.labels,
                "buckets": metric.buckets,
                "unit": metric.unit,
            }
            for metric in config.custom_metrics
        ],
    }

    with open(filename, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)


# Example usage
if __name__ == "__main__":
    # Create and save default configuration
    config = create_default_config()
    save_config(config)

    # Initialize and start monitoring stack
    monitoring_stack = ZeroCostMonitoringStack(config)

    try:
        monitoring_stack.start()

        # Simulate some metrics
        for i in range(10):
            monitoring_stack.metrics_collector.record_scraping_request(
                method="requests", status="success", source="publicapis", duration=1.5
            )

            monitoring_stack.metrics_collector.record_api_discovery(
                source="publicapis", category="weather", status="validated", count=5
            )

            time.sleep(2)

        # Print health status
        health = monitoring_stack.get_health_status()
        print(f"\\nMonitoring Stack Health: {json.dumps(health, indent = 2)}")

        # Print metrics summary
        summary = monitoring_stack.get_metrics_summary()
        print(f"\\nMetrics Summary: {json.dumps(summary, indent = 2)}")

        # Keep running for a while
        print(f"\\nMonitoring stack running on http://localhost:{config.prometheus_port}/metrics")
        print("Press Ctrl + C to stop...")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\\nStopping monitoring stack...")
    finally:
        monitoring_stack.stop()
