#!/usr / bin / env python3
"""
Performance Monitor - Real - time performance tracking and automatic scaling

This module provides comprehensive performance monitoring for the automated model
generation system, including real - time metrics collection, performance analysis,
and automatic scaling based on demand patterns.

Features:
- Real - time performance metrics collection
- Resource utilization monitoring
- Request throughput and latency tracking
- Automatic scaling recommendations
- Performance alerting and notifications
- Historical performance analysis
- Bottleneck detection and optimization
- Load prediction and capacity planning
"""

import asyncio
import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""

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


class ScalingAction(Enum):
    """Scaling actions"""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    OPTIMIZE = "optimize"

@dataclass


class PerformanceMetric:
    """Performance metric data structure"""

    name: str
    metric_type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory = dict)
    metadata: Dict[str, Any] = field(default_factory = dict)

@dataclass


class PerformanceAlert:
    """Performance alert data structure"""

    alert_id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    threshold: float
    current_value: float
    timestamp: float
    resolved: bool = False
    resolution_time: Optional[float] = None

@dataclass


class ScalingRecommendation:
    """Scaling recommendation data structure"""

    recommendation_id: str
    action: ScalingAction
    resource_type: str
    current_capacity: int
    recommended_capacity: int
    confidence: float
    reasoning: str
    estimated_impact: Dict[str, float]
    timestamp: float

@dataclass


class PerformanceReport:
    """Performance analysis report"""

    report_id: str
    start_time: float
    end_time: float
    metrics_summary: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[ScalingRecommendation]
    alerts: List[PerformanceAlert]
    overall_health_score: float
    trends: Dict[str, Any]


class MetricsCollector:
    """Collects and aggregates performance metrics"""


    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen = 1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen = 100))
        self.lock = threading.Lock()


    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self.lock:
            self.metrics[metric.name].append(metric)

            if metric.metric_type == MetricType.COUNTER:
                self.counters[metric.name] += metric.value
            elif metric.metric_type == MetricType.GAUGE:
                self.gauges[metric.name] = metric.value
            elif metric.metric_type == MetricType.HISTOGRAM:
                self.histograms[metric.name].append(metric.value)
                # Keep only last 1000 values
                if len(self.histograms[metric.name]) > 1000:
                    self.histograms[metric.name] = self.histograms[metric.name][-1000:]
            elif metric.metric_type == MetricType.TIMER:
                self.timers[metric.name].append(metric.value)


    def get_metric_stats(
        self, metric_name: str, time_window: int = 300
    ) -> Dict[str, Any]:
        """Get statistics for a metric within time window (seconds)"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - time_window

            # Filter metrics within time window
            recent_metrics = [
                m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {}

            values = [m.value for m in recent_metrics]

            return {
                "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "p95": self._percentile(values, 0.95),
                    "p99": self._percentile(values, 0.99),
                    "rate_per_second": len(values) / time_window,
                    }


    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


class ResourceMonitor:
    """Monitors system resource utilization"""


    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
            self.monitoring = False
        self.monitor_thread = None


    def start_monitoring(self, interval: float = 5.0):
        """Start resource monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target = self._monitor_loop, args=(interval,), daemon = True
        )
        self.monitor_thread.start()
        logger.info("Resource monitoring started")


    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout = 5)
        logger.info("Resource monitoring stopped")


    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(interval)


    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        timestamp = time.time()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval = 1)
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.cpu.usage_percent",
                    metric_type = MetricType.GAUGE,
                    value = cpu_percent,
                    timestamp = timestamp,
                    )
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.memory.usage_percent",
                    metric_type = MetricType.GAUGE,
                    value = memory.percent,
                    timestamp = timestamp,
                    )
        )

        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.memory.available_gb",
                    metric_type = MetricType.GAUGE,
                    value = memory.available / (1024**3),
                    timestamp = timestamp,
                    )
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.disk.usage_percent",
                    metric_type = MetricType.GAUGE,
                    value=(disk.used / disk.total) * 100,
                    timestamp = timestamp,
                    )
        )

        # Network metrics
        network = psutil.net_io_counters()
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.network.bytes_sent",
                    metric_type = MetricType.COUNTER,
                    value = network.bytes_sent,
                    timestamp = timestamp,
                    )
        )

        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="system.network.bytes_recv",
                    metric_type = MetricType.COUNTER,
                    value = network.bytes_recv,
                    timestamp = timestamp,
                    )
        )


class AlertManager:
    """Manages performance alerts and notifications"""


    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
            self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        self.notification_callbacks: List[Callable] = []


    def add_alert_rule(
        self,
            metric_name: str,
            threshold: float,
            severity: AlertSeverity,
            condition: str = "greater_than",
            time_window: int = 300,
            min_samples: int = 3,
            ):
        """Add an alert rule"""
        self.alert_rules[metric_name] = {
            "threshold": threshold,
                "severity": severity,
                "condition": condition,
                "time_window": time_window,
                "min_samples": min_samples,
                }


    def add_notification_callback(self, callback: Callable):
        """Add notification callback"""
        self.notification_callbacks.append(callback)


    def check_alerts(self):
        """Check all alert rules"""
        for metric_name, rule in self.alert_rules.items():
            try:
                self._check_metric_alert(metric_name, rule)
            except Exception as e:
                logger.error(f"Error checking alert for {metric_name}: {e}")


    def _check_metric_alert(self, metric_name: str, rule: Dict[str, Any]):
        """Check alert for specific metric"""
        stats = self.metrics_collector.get_metric_stats(
            metric_name, rule["time_window"]
        )

        if not stats or stats["count"] < rule["min_samples"]:
            return

        current_value = stats["mean"]
        threshold = rule["threshold"]
        condition = rule["condition"]

        # Check condition
        alert_triggered = False
        if condition == "greater_than" and current_value > threshold:
            alert_triggered = True
        elif condition == "less_than" and current_value < threshold:
            alert_triggered = True
        elif condition == "equals" and abs(current_value - threshold) < 0.001:
            alert_triggered = True

        alert_id = f"{metric_name}_{condition}_{threshold}"

        if alert_triggered:
            if alert_id not in self.active_alerts:
                # Create new alert
                alert = PerformanceAlert(
                    alert_id = alert_id,
                        metric_name = metric_name,
                        severity = rule["severity"],
                        message = f"{metric_name} {condition} {threshold} (current: {current_value:.2f})",
                        threshold = threshold,
                        current_value = current_value,
                        timestamp = time.time(),
                        )

                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                self._send_notification(alert)
        else:
            # Resolve alert if it exists
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_time = time.time()
                del self.active_alerts[alert_id]
                self._send_notification(alert)


    def _send_notification(self, alert: PerformanceAlert):
        """Send alert notification"""
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")


class AutoScaler:
    """Automatic scaling based on performance metrics"""


    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
            self.scaling_rules: Dict[str, Dict[str, Any]] = {}
        self.scaling_history: List[ScalingRecommendation] = []
        self.last_scaling_time: Dict[str, float] = {}
        self.min_scaling_interval = 300  # 5 minutes


    def add_scaling_rule(
        self,
            resource_type: str,
            scale_up_threshold: float,
            scale_down_threshold: float,
            metric_name: str,
            min_capacity: int = 1,
            max_capacity: int = 10,
            scaling_factor: float = 1.5,
            ):
        """Add auto - scaling rule"""
        self.scaling_rules[resource_type] = {
            "scale_up_threshold": scale_up_threshold,
                "scale_down_threshold": scale_down_threshold,
                "metric_name": metric_name,
                "min_capacity": min_capacity,
                "max_capacity": max_capacity,
                "scaling_factor": scaling_factor,
                }


    def evaluate_scaling(
        self, current_capacities: Dict[str, int]
    ) -> List[ScalingRecommendation]:
        """Evaluate scaling recommendations"""
        recommendations = []

        for resource_type, rule in self.scaling_rules.items():
            try:
                recommendation = self._evaluate_resource_scaling(
                    resource_type, rule, current_capacities.get(resource_type, 1)
                )
                if recommendation:
                    recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Error evaluating scaling for {resource_type}: {e}")

        return recommendations


    def _evaluate_resource_scaling(
        self, resource_type: str, rule: Dict[str, Any], current_capacity: int
    ) -> Optional[ScalingRecommendation]:
        """Evaluate scaling for specific resource"""
        # Check if enough time has passed since last scaling
        last_scaling = self.last_scaling_time.get(resource_type, 0)
        if time.time() - last_scaling < self.min_scaling_interval:
            return None

        # Get metric statistics
        stats = self.metrics_collector.get_metric_stats(rule["metric_name"])
        if not stats:
            return None

        current_value = stats["mean"]
        scale_up_threshold = rule["scale_up_threshold"]
        scale_down_threshold = rule["scale_down_threshold"]

        action = ScalingAction.MAINTAIN
        recommended_capacity = current_capacity
        confidence = 0.0
        reasoning = ""

        if (
            current_value > scale_up_threshold
            and current_capacity < rule["max_capacity"]
        ):
            # Scale up
            action = ScalingAction.SCALE_UP
            recommended_capacity = min(
                int(current_capacity * rule["scaling_factor"]), rule["max_capacity"]
            )
            confidence = min(
                (current_value - scale_up_threshold) / scale_up_threshold, 1.0
            )
            reasoning = f"Metric {rule['metric_name']} ({current_value:.2f}) exceeds scale - up threshold ({scale_up_threshold})"

        elif (
            current_value < scale_down_threshold
            and current_capacity > rule["min_capacity"]
        ):
            # Scale down
            action = ScalingAction.SCALE_DOWN
            recommended_capacity = max(
                int(current_capacity / rule["scaling_factor"]), rule["min_capacity"]
            )
            confidence = min(
                (scale_down_threshold - current_value) / scale_down_threshold, 1.0
            )
            reasoning = f"Metric {rule['metric_name']} ({current_value:.2f}) below scale - down threshold ({scale_down_threshold})"

        if action != ScalingAction.MAINTAIN:
            recommendation = ScalingRecommendation(
                recommendation_id = f"{resource_type}_{int(time.time())}",
                    action = action,
                    resource_type = resource_type,
                    current_capacity = current_capacity,
                    recommended_capacity = recommended_capacity,
                    confidence = confidence,
                    reasoning = reasoning,
                    estimated_impact = self._estimate_scaling_impact(
                    current_capacity, recommended_capacity, stats
                ),
                    timestamp = time.time(),
                    )

            self.scaling_history.append(recommendation)
            self.last_scaling_time[resource_type] = time.time()

            return recommendation

        return None


    def _estimate_scaling_impact(
        self, current_capacity: int, recommended_capacity: int, stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """Estimate impact of scaling action"""
        capacity_ratio = recommended_capacity / current_capacity

        return {
            "throughput_change_percent": (capacity_ratio - 1) * 100,
                "latency_change_percent": (1 / capacity_ratio - 1) * 100,
                "cost_change_percent": (capacity_ratio - 1) * 100,
                "reliability_improvement": min(capacity_ratio * 0.1, 0.5),
                }


class PerformanceMonitor:
    """Main performance monitoring system"""


    def __init__(self, db_path: str = "performance_monitor.db"):
        self.db_path = db_path
        self.metrics_collector = MetricsCollector()
        self.resource_monitor = ResourceMonitor(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.auto_scaler = AutoScaler(self.metrics_collector)
        self.monitoring_active = False
        self.monitor_thread = None

        # Initialize database
        self._init_database()

        # Setup default alert rules
        self._setup_default_alerts()

        # Setup default scaling rules
        self._setup_default_scaling()


    def _init_database(self):
        """Initialize performance monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp REAL NOT NULL,
                        tags TEXT,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Performance alerts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE NOT NULL,
                        metric_name TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        threshold REAL NOT NULL,
                        current_value REAL NOT NULL,
                        timestamp REAL NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution_time REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Scaling recommendations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scaling_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recommendation_id TEXT UNIQUE NOT NULL,
                        action TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        current_capacity INTEGER NOT NULL,
                        recommended_capacity INTEGER NOT NULL,
                        confidence REAL NOT NULL,
                        reasoning TEXT NOT NULL,
                        estimated_impact TEXT,
                        timestamp REAL NOT NULL,
                        applied BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Performance reports table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT UNIQUE NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        metrics_summary TEXT,
                        bottlenecks TEXT,
                        recommendations TEXT,
                        alerts TEXT,
                        overall_health_score REAL,
                        trends TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON performance_metrics(name, timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_scaling_timestamp ON scaling_recommendations(timestamp)"
            )

            conn.commit()


    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # CPU usage alerts
        self.alert_manager.add_alert_rule(
            "system.cpu.usage_percent", 80.0, AlertSeverity.WARNING
        )
        self.alert_manager.add_alert_rule(
            "system.cpu.usage_percent", 95.0, AlertSeverity.CRITICAL
        )

        # Memory usage alerts
        self.alert_manager.add_alert_rule(
            "system.memory.usage_percent", 85.0, AlertSeverity.WARNING
        )
        self.alert_manager.add_alert_rule(
            "system.memory.usage_percent", 95.0, AlertSeverity.CRITICAL
        )

        # Model generation latency alerts
        self.alert_manager.add_alert_rule(
            "model.generation.latency_ms", 30000.0, AlertSeverity.WARNING
        )
        self.alert_manager.add_alert_rule(
            "model.generation.latency_ms", 60000.0, AlertSeverity.CRITICAL
        )

        # Error rate alerts
        self.alert_manager.add_alert_rule(
            "model.generation.error_rate", 0.05, AlertSeverity.WARNING
        )
        self.alert_manager.add_alert_rule(
            "model.generation.error_rate", 0.10, AlertSeverity.CRITICAL
        )


    def _setup_default_scaling(self):
        """Setup default scaling rules"""
        # Model generation workers scaling
        self.auto_scaler.add_scaling_rule(
            resource_type="model_workers",
                scale_up_threshold = 0.8,  # 80% CPU usage
            scale_down_threshold = 0.3,  # 30% CPU usage
            metric_name="system.cpu.usage_percent",
                min_capacity = 1,
                max_capacity = 8,
                scaling_factor = 1.5,
                )

        # API server scaling
        self.auto_scaler.add_scaling_rule(
            resource_type="api_servers",
                scale_up_threshold = 100.0,  # 100 requests per second
            scale_down_threshold = 20.0,  # 20 requests per second
            metric_name="api.requests_per_second",
                min_capacity = 1,
                max_capacity = 5,
                scaling_factor = 2.0,
                )


    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        # Start main monitoring loop
        self.monitor_thread = threading.Thread(
            target = self._monitoring_loop, daemon = True
        )
        self.monitor_thread.start()

        logger.info("Performance monitoring started")


    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False

        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()

        # Wait for monitoring thread
        if self.monitor_thread:
            self.monitor_thread.join(timeout = 10)

        logger.info("Performance monitoring stopped")


    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Check alerts
                self.alert_manager.check_alerts()

                # Store metrics to database
                self._store_metrics_batch()

                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)


    def record_model_generation_metric(
        self, generation_time_ms: float, success: bool, model_type: str
    ):
        """Record model generation performance metric"""
        timestamp = time.time()

        # Record generation time
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="model.generation.latency_ms",
                    metric_type = MetricType.TIMER,
                    value = generation_time_ms,
                    timestamp = timestamp,
                    tags={"model_type": model_type, "success": str(success)},
                    )
        )

        # Record success / failure
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="model.generation.total",
                    metric_type = MetricType.COUNTER,
                    value = 1,
                    timestamp = timestamp,
                    tags={"model_type": model_type},
                    )
        )

        if not success:
            self.metrics_collector.record_metric(
                PerformanceMetric(
                    name="model.generation.errors",
                        metric_type = MetricType.COUNTER,
                        value = 1,
                        timestamp = timestamp,
                        tags={"model_type": model_type},
                        )
            )


    def record_api_request_metric(
        self, endpoint: str, response_time_ms: float, status_code: int
    ):
        """Record API request performance metric"""
        timestamp = time.time()

        # Record request count
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="api.requests_total",
                    metric_type = MetricType.COUNTER,
                    value = 1,
                    timestamp = timestamp,
                    tags={"endpoint": endpoint, "status_code": str(status_code)},
                    )
        )

        # Record response time
        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="api.response_time_ms",
                    metric_type = MetricType.TIMER,
                    value = response_time_ms,
                    timestamp = timestamp,
                    tags={"endpoint": endpoint},
                    )
        )

        # Calculate requests per second
        recent_requests = len(
            [
                m
                for m in self.metrics_collector.metrics["api.requests_total"]
                if m.timestamp >= timestamp - 60  # Last minute
            ]
        )

        self.metrics_collector.record_metric(
            PerformanceMetric(
                name="api.requests_per_second",
                    metric_type = MetricType.GAUGE,
                    value = recent_requests / 60.0,
                    timestamp = timestamp,
                    )
        )


    def get_scaling_recommendations(
        self, current_capacities: Dict[str, int]
    ) -> List[ScalingRecommendation]:
        """Get current scaling recommendations"""
        return self.auto_scaler.evaluate_scaling(current_capacities)


    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get currently active alerts"""
        return list(self.alert_manager.active_alerts.values())


    def generate_performance_report(
        self, start_time: float, end_time: float
    ) -> PerformanceReport:
        """Generate comprehensive performance report"""
        report_id = f"perf_report_{int(time.time())}"

        # Collect metrics summary
        metrics_summary = self._generate_metrics_summary(start_time, end_time)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(start_time, end_time)

        # Get recommendations
        current_capacities = {"model_workers": 2, "api_servers": 1}  # Default values
        recommendations = self.get_scaling_recommendations(current_capacities)

        # Get alerts in time range
        alerts = [
            alert
            for alert in self.alert_manager.alert_history
            if start_time <= alert.timestamp <= end_time
        ]

        # Calculate overall health score
        health_score = self._calculate_health_score(metrics_summary, alerts)

        # Analyze trends
        trends = self._analyze_trends(start_time, end_time)

        report = PerformanceReport(
            report_id = report_id,
                start_time = start_time,
                end_time = end_time,
                metrics_summary = metrics_summary,
                bottlenecks = bottlenecks,
                recommendations = recommendations,
                alerts = alerts,
                overall_health_score = health_score,
                trends = trends,
                )

        # Store report in database
        self._store_performance_report(report)

        return report


    def _generate_metrics_summary(
        self, start_time: float, end_time: float
    ) -> Dict[str, Any]:
        """Generate metrics summary for time period"""
        summary = {}

        key_metrics = [
            "system.cpu.usage_percent",
                "system.memory.usage_percent",
                "model.generation.latency_ms",
                "api.response_time_ms",
                "api.requests_per_second",
                ]

        for metric_name in key_metrics:
            stats = self.metrics_collector.get_metric_stats(
                metric_name, int(end_time - start_time)
            )
            if stats:
                summary[metric_name] = stats

        return summary


    def _identify_bottlenecks(
        self, start_time: float, end_time: float
    ) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Check CPU bottleneck
        cpu_stats = self.metrics_collector.get_metric_stats(
            "system.cpu.usage_percent", int(end_time - start_time)
        )
        if cpu_stats and cpu_stats["mean"] > 80:
            bottlenecks.append(
                {
                    "type": "cpu",
                        "severity": "high" if cpu_stats["mean"] > 90 else "medium",
                        "description": f"High CPU usage: {cpu_stats['mean']:.1f}% average",
                        "recommendation": "Consider scaling up compute resources",
                        }
            )

        # Check memory bottleneck
        memory_stats = self.metrics_collector.get_metric_stats(
            "system.memory.usage_percent", int(end_time - start_time)
        )
        if memory_stats and memory_stats["mean"] > 85:
            bottlenecks.append(
                {
                    "type": "memory",
                        "severity": "high" if memory_stats["mean"] > 95 else "medium",
                        "description": f"High memory usage: {memory_stats['mean']:.1f}% average",
                        "recommendation": "Consider increasing memory allocation",
                        }
            )

        # Check latency bottleneck
        latency_stats = self.metrics_collector.get_metric_stats(
            "model.generation.latency_ms", int(end_time - start_time)
        )
        if latency_stats and latency_stats["p95"] > 30000:  # 30 seconds
            bottlenecks.append(
                {
                    "type": "latency",
                        "severity": "high" if latency_stats["p95"] > 60000 else "medium",
                        "description": f"High generation latency: {latency_stats['p95']:.0f}ms P95",
                        "recommendation": "Optimize model generation pipeline",
                        }
            )

        return bottlenecks


    def _calculate_health_score(
        self, metrics_summary: Dict[str, Any], alerts: List[PerformanceAlert]
    ) -> float:
        """Calculate overall system health score (0 - 100)"""
        score = 100.0

        # Deduct points for high resource usage
        if "system.cpu.usage_percent" in metrics_summary:
            cpu_usage = metrics_summary["system.cpu.usage_percent"].get("mean", 0)
            if cpu_usage > 80:
                score -= (cpu_usage - 80) * 2

        if "system.memory.usage_percent" in metrics_summary:
            memory_usage = metrics_summary["system.memory.usage_percent"].get("mean", 0)
            if memory_usage > 85:
                score -= (memory_usage - 85) * 3

        # Deduct points for high latency
        if "model.generation.latency_ms" in metrics_summary:
            latency_p95 = metrics_summary["model.generation.latency_ms"].get("p95", 0)
            if latency_p95 > 30000:
                score -= min((latency_p95 - 30000) / 1000, 30)

        # Deduct points for alerts
        for alert in alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                score -= 15
            elif alert.severity == AlertSeverity.WARNING:
                score -= 5
            elif alert.severity == AlertSeverity.EMERGENCY:
                score -= 25

        return max(score, 0.0)


    def _analyze_trends(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """Analyze performance trends"""
        # This is a simplified trend analysis
        # In a real implementation, you'd use more sophisticated time series analysis

        trends = {
            "cpu_trend": "stable",
                "memory_trend": "stable",
                "latency_trend": "stable",
                "throughput_trend": "stable",
                }

        # For now, return stable trends
        # TODO: Implement proper trend analysis using time series data

        return trends


    def _store_metrics_batch(self):
        """Store metrics batch to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Store recent metrics (last 5 minutes)
                current_time = time.time()
                cutoff_time = current_time - 300

                for metric_name, metric_deque in self.metrics_collector.metrics.items():
                    recent_metrics = [
                        m for m in metric_deque if m.timestamp >= cutoff_time
                    ]

                    for metric in recent_metrics:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO performance_metrics (
                                name, metric_type, value, timestamp, tags, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                metric.name,
                                    metric.metric_type.value,
                                    metric.value,
                                    metric.timestamp,
                                    json.dumps(metric.tags),
                                    json.dumps(metric.metadata),
                                    ),
                                )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing metrics batch: {e}")


    def _store_performance_report(self, report: PerformanceReport):
        """Store performance report in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO performance_reports (
                        report_id, start_time, end_time, metrics_summary,
                            bottlenecks, recommendations, alerts, overall_health_score, trends
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        report.report_id,
                            report.start_time,
                            report.end_time,
                            json.dumps(report.metrics_summary),
                            json.dumps(
                            [
                                {
                                    "type": b["type"],
                                        "severity": b["severity"],
                                        "description": b["description"],
                                        "recommendation": b["recommendation"],
                                        }
                                for b in report.bottlenecks
                            ]
                        ),
                            json.dumps(
                            [
                                {
                                    "recommendation_id": r.recommendation_id,
                                        "action": r.action.value,
                                        "resource_type": r.resource_type,
                                        "current_capacity": r.current_capacity,
                                        "recommended_capacity": r.recommended_capacity,
                                        "confidence": r.confidence,
                                        "reasoning": r.reasoning,
                                        }
                                for r in report.recommendations
                            ]
                        ),
                            json.dumps(
                            [
                                {
                                    "alert_id": a.alert_id,
                                        "metric_name": a.metric_name,
                                        "severity": a.severity.value,
                                        "message": a.message,
                                        "timestamp": a.timestamp,
                                        }
                                for a in report.alerts
                            ]
                        ),
                            report.overall_health_score,
                            json.dumps(report.trends),
                            ),
                        )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing performance report: {e}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience functions


def start_performance_monitoring():
    """Start performance monitoring"""
    performance_monitor.start_monitoring()


def stop_performance_monitoring():
    """Stop performance monitoring"""
    performance_monitor.stop_monitoring()


def record_model_generation(
    generation_time_ms: float, success: bool, model_type: str = "default"
):
    """Record model generation performance"""
    performance_monitor.record_model_generation_metric(
        generation_time_ms, success, model_type
    )


def record_api_request(endpoint: str, response_time_ms: float, status_code: int):
    """Record API request performance"""
    performance_monitor.record_api_request_metric(
        endpoint, response_time_ms, status_code
    )


def get_current_performance_status() -> Dict[str, Any]:
    """Get current performance status"""
    return {
        "active_alerts": len(performance_monitor.get_active_alerts()),
            "cpu_usage": performance_monitor.metrics_collector.get_metric_stats(
            "system.cpu.usage_percent"
        ),
            "memory_usage": performance_monitor.metrics_collector.get_metric_stats(
            "system.memory.usage_percent"
        ),
            "generation_latency": performance_monitor.metrics_collector.get_metric_stats(
            "model.generation.latency_ms"
        ),
            }

if __name__ == "__main__":
    # Example usage


    def alert_callback(alert: PerformanceAlert):
        print(f"ALERT: {alert.message} (Severity: {alert.severity.value})")

    # Setup monitoring
    performance_monitor.alert_manager.add_notification_callback(alert_callback)

    # Start monitoring
    start_performance_monitoring()

    try:
        # Simulate some activity
        for i in range(10):
            # Simulate model generation
            import random

            generation_time = random.uniform(1000, 5000)  # 1 - 5 seconds
            success = random.random() > 0.1  # 90% success rate
            record_model_generation(generation_time, success, "avatar_video")

            # Simulate API requests
            response_time = random.uniform(50, 500)  # 50 - 500ms
            status_code = 200 if random.random() > 0.05 else 500
            record_api_request("/api / generate", response_time, status_code)

            time.sleep(2)

        # Generate performance report
        end_time = time.time()
        start_time = end_time - 300  # Last 5 minutes

        report = performance_monitor.generate_performance_report(start_time, end_time)
        print(f"\nPerformance Report: {report.report_id}")
        print(f"Health Score: {report.overall_health_score:.1f}/100")
        print(f"Active Alerts: {len(report.alerts)}")
        print(f"Bottlenecks: {len(report.bottlenecks)}")
        print(f"Scaling Recommendations: {len(report.recommendations)}")

        # Get current status
        status = get_current_performance_status()
        print(f"\nCurrent Status: {status}")

    finally:
        stop_performance_monitoring()
