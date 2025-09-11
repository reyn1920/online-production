#!/usr/bin/env python3
"""
TRAE.AI System Monitor

Provides comprehensive monitoring and health checking for all integrated services,
including real-time metrics, performance tracking, and automated alerting.

Features:
- Real-time service health monitoring
- System resource tracking (CPU, memory, disk)
- Network connectivity checks
- Database health monitoring
- WebSocket connection tracking
- Performance metrics collection
- Automated alerting and notifications
- Web-based dashboard interface

Author: TRAE.AI Integration System
Version: 1.0.0
Date: 2024
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
import requests
import websocket
from flask import Flask, jsonify, render_template_string, request
from flask_socketio import SocketIO, emit

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@dataclass
class ServiceMetrics:
    """Metrics for a service"""

    name: str
    status: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    response_time_ms: float = 0.0
    uptime_seconds: int = 0
    error_count: int = 0
    request_count: int = 0
    last_check: Optional[datetime] = None
    health_score: float = 100.0


@dataclass
class SystemMetrics:
    """System-wide metrics"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: Tuple[float, float, float]


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    condition: str  # e.g., "cpu_percent > 80"
    severity: str  # low, medium, high, critical
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None


class SystemMonitor:
    """
    Comprehensive system monitoring and health checking
    """

    def __init__(self, config_file: str = "monitoring_config.json"):
        self.config_file = config_file
        self.logger = self._setup_logging()

        # Monitoring data
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, datetime] = {}

        # Configuration
        self.config = self._load_config()
        self.monitoring_interval = self.config.get("monitoring_interval", 30)
        self.services_to_monitor = self.config.get("services", {})

        # Database for metrics storage
        self.db_path = "monitoring/metrics.db"
        self._init_database()

        # Flask app for web dashboard
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = os.environ.get(
            "SYSTEM_MONITOR_SECRET_KEY", os.urandom(24).hex()
        )
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Setup routes
        self._setup_routes()

        # Monitoring thread control
        self.monitoring_active = False
        self.monitoring_thread = None

        # Load default alert rules
        self._setup_default_alert_rules()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        Path("logs").mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/system_monitor.log"),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "monitoring_interval": 30,
            "services": {
                "main_app": {
                    "url": "http://localhost:8000/health",
                    "port": 8000,
                    "critical": True,
                },
                "paste_app": {
                    "url": "http://localhost:3001",
                    "port": 3001,
                    "critical": False,
                },
                "demo_avatar": {
                    "url": "http://localhost:3002",
                    "port": 3002,
                    "critical": False,
                },
                "static_server": {
                    "url": "http://localhost:3000",
                    "port": 3000,
                    "critical": False,
                },
            },
            "alert_thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
                "response_time_ms": 5000,
            },
        }

        try:
            if Path(self.config_file).exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return default_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return default_config

    def _init_database(self):
        """Initialize metrics database"""
        Path("monitoring").mkdir(exist_ok=True)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS service_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    service_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_mb REAL,
                    response_time_ms REAL,
                    uptime_seconds INTEGER,
                    error_count INTEGER,
                    request_count INTEGER,
                    health_score REAL
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_recv INTEGER,
                    active_connections INTEGER,
                    load_avg_1m REAL,
                    load_avg_5m REAL,
                    load_avg_15m REAL
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME
                )
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("Metrics database initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        thresholds = self.config.get("alert_thresholds", {})

        self.alert_rules = [
            AlertRule(
                name="High CPU Usage",
                condition=f"cpu_percent > {thresholds.get('cpu_percent', 80)}",
                severity="high",
                cooldown_minutes=5,
            ),
            AlertRule(
                name="High Memory Usage",
                condition=f"memory_percent > {thresholds.get('memory_percent', 85)}",
                severity="high",
                cooldown_minutes=5,
            ),
            AlertRule(
                name="High Disk Usage",
                condition=f"disk_percent > {thresholds.get('disk_percent', 90)}",
                severity="critical",
                cooldown_minutes=10,
            ),
            AlertRule(
                name="Service Down",
                condition="service_status == 'down'",
                severity="critical",
                cooldown_minutes=1,
            ),
            AlertRule(
                name="Slow Response Time",
                condition=f"response_time_ms > {thresholds.get('response_time_ms', 5000)}",
                severity="medium",
                cooldown_minutes=3,
            ),
        ]

    def _setup_routes(self):
        """Setup Flask routes for web dashboard"""

        @self.app.route("/")
        def dashboard():
            return render_template_string(DASHBOARD_HTML)

        @self.app.route("/api/metrics")
        def get_metrics():
            return jsonify(
                {
                    "services": {
                        name: asdict(metrics)
                        for name, metrics in self.service_metrics.items()
                    },
                    "system": [
                        asdict(m) for m in list(self.system_metrics_history)[-10:]
                    ],
                    "alerts": self._get_active_alerts(),
                }
            )

        @self.app.route("/api/service/<service_name>/history")
        def get_service_history(service_name):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT timestamp, status, cpu_percent, memory_mb, response_time_ms, health_score
                    FROM service_metrics 
                    WHERE service_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """,
                    (service_name,),
                )

                rows = cursor.fetchall()
                conn.close()

                history = []
                for row in rows:
                    history.append(
                        {
                            "timestamp": row[0],
                            "status": row[1],
                            "cpu_percent": row[2],
                            "memory_mb": row[3],
                            "response_time_ms": row[4],
                            "health_score": row[5],
                        }
                    )

                return jsonify(history)

            except Exception as e:
                self.logger.error(f"Failed to get service history: {e}")
                return jsonify({"error": str(e)}), 500

        @self.socketio.on("connect")
        def handle_connect():
            self.logger.info("Client connected to monitoring dashboard")
            emit("status", {"message": "Connected to monitoring system"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.logger.info("Client disconnected from monitoring dashboard")

    def check_service_health(
        self, service_name: str, service_config: Dict[str, Any]
    ) -> ServiceMetrics:
        """Check health of a specific service"""
        metrics = ServiceMetrics(name=service_name, status="unknown")

        try:
            # Get process info if port is specified
            if "port" in service_config:
                port = service_config["port"]
                process = self._find_process_by_port(port)

                if process:
                    metrics.cpu_percent = process.cpu_percent()
                    metrics.memory_mb = process.memory_info().rss / 1024 / 1024
                    metrics.uptime_seconds = int(time.time() - process.create_time())
                    metrics.status = "running"
                else:
                    metrics.status = "down"

            # HTTP health check if URL is provided
            if "url" in service_config and metrics.status != "down":
                start_time = time.time()
                try:
                    response = requests.get(service_config["url"], timeout=10)
                    metrics.response_time_ms = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        metrics.status = "healthy"
                        metrics.health_score = 100.0
                    else:
                        metrics.status = "unhealthy"
                        metrics.health_score = 50.0
                        metrics.error_count += 1

                except requests.RequestException as e:
                    metrics.status = "unreachable"
                    metrics.response_time_ms = (time.time() - start_time) * 1000
                    metrics.health_score = 0.0
                    metrics.error_count += 1

            metrics.last_check = datetime.now()

        except Exception as e:
            self.logger.error(f"Error checking service {service_name}: {e}")
            metrics.status = "error"
            metrics.health_score = 0.0

        return metrics

    def _find_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """Find process listening on a specific port"""
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return psutil.Process(conn.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network
            net_io = psutil.net_io_counters()

            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                load_avg = (0.0, 0.0, 0.0)

            # Active connections
            active_connections = len(psutil.net_connections())

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                active_connections=active_connections,
                load_average=load_avg,
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                active_connections=0,
                load_average=(0.0, 0.0, 0.0),
            )

    def store_metrics(
        self, service_metrics: Dict[str, ServiceMetrics], system_metrics: SystemMetrics
    ):
        """Store metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Store service metrics
            for metrics in service_metrics.values():
                cursor.execute(
                    """
                    INSERT INTO service_metrics 
                    (service_name, status, cpu_percent, memory_mb, response_time_ms, 
                     uptime_seconds, error_count, request_count, health_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.name,
                        metrics.status,
                        metrics.cpu_percent,
                        metrics.memory_mb,
                        metrics.response_time_ms,
                        metrics.uptime_seconds,
                        metrics.error_count,
                        metrics.request_count,
                        metrics.health_score,
                    ),
                )

            # Store system metrics
            cursor.execute(
                """
                INSERT INTO system_metrics 
                (cpu_percent, memory_percent, disk_percent, network_bytes_sent, 
                 network_bytes_recv, active_connections, load_avg_1m, load_avg_5m, load_avg_15m)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    system_metrics.cpu_percent,
                    system_metrics.memory_percent,
                    system_metrics.disk_percent,
                    system_metrics.network_bytes_sent,
                    system_metrics.network_bytes_recv,
                    system_metrics.active_connections,
                    system_metrics.load_average[0],
                    system_metrics.load_average[1],
                    system_metrics.load_average[2],
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")

    def check_alerts(
        self, service_metrics: Dict[str, ServiceMetrics], system_metrics: SystemMetrics
    ):
        """Check alert conditions and trigger alerts"""
        current_time = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered and current_time - rule.last_triggered < timedelta(
                minutes=rule.cooldown_minutes
            ):
                continue

            # Evaluate condition
            alert_triggered = False
            alert_message = ""

            try:
                if "cpu_percent" in rule.condition:
                    if eval(
                        rule.condition.replace(
                            "cpu_percent", str(system_metrics.cpu_percent)
                        )
                    ):
                        alert_triggered = True
                        alert_message = (
                            f"System CPU usage is {system_metrics.cpu_percent:.1f}%"
                        )

                elif "memory_percent" in rule.condition:
                    if eval(
                        rule.condition.replace(
                            "memory_percent", str(system_metrics.memory_percent)
                        )
                    ):
                        alert_triggered = True
                        alert_message = f"System memory usage is {system_metrics.memory_percent:.1f}%"

                elif "disk_percent" in rule.condition:
                    if eval(
                        rule.condition.replace(
                            "disk_percent", str(system_metrics.disk_percent)
                        )
                    ):
                        alert_triggered = True
                        alert_message = (
                            f"System disk usage is {system_metrics.disk_percent:.1f}%"
                        )

                elif "service_status" in rule.condition:
                    for service_name, metrics in service_metrics.items():
                        if metrics.status in ["down", "unreachable", "error"]:
                            alert_triggered = True
                            alert_message = (
                                f"Service {service_name} is {metrics.status}"
                            )
                            break

                elif "response_time_ms" in rule.condition:
                    for service_name, metrics in service_metrics.items():
                        if eval(
                            rule.condition.replace(
                                "response_time_ms", str(metrics.response_time_ms)
                            )
                        ):
                            alert_triggered = True
                            alert_message = f"Service {service_name} response time is {metrics.response_time_ms:.0f}ms"
                            break

                if alert_triggered:
                    self._trigger_alert(rule, alert_message)
                    rule.last_triggered = current_time

            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.name}: {e}")

    def _trigger_alert(self, rule: AlertRule, message: str):
        """Trigger an alert"""
        alert_data = {
            "name": rule.name,
            "severity": rule.severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.warning(f"ALERT [{rule.severity.upper()}] {rule.name}: {message}")

        # Store alert in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts (alert_name, severity, message)
                VALUES (?, ?, ?)
            """,
                (rule.name, rule.severity, message),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")

        # Emit to connected clients
        try:
            self.socketio.emit("alert", alert_data)
        except Exception as e:
            self.logger.error(f"Failed to emit alert: {e}")

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT alert_name, severity, message, timestamp
                FROM alerts 
                WHERE resolved = FALSE 
                ORDER BY timestamp DESC 
                LIMIT 50
            """
            )

            rows = cursor.fetchall()
            conn.close()

            alerts = []
            for row in rows:
                alerts.append(
                    {
                        "name": row[0],
                        "severity": row[1],
                        "message": row[2],
                        "timestamp": row[3],
                    }
                )

            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []

    def monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")

        while self.monitoring_active:
            try:
                # Collect service metrics
                for service_name, service_config in self.services_to_monitor.items():
                    metrics = self.check_service_health(service_name, service_config)
                    self.service_metrics[service_name] = metrics

                # Collect system metrics
                system_metrics = self.collect_system_metrics()
                self.system_metrics_history.append(system_metrics)

                # Store metrics
                self.store_metrics(self.service_metrics, system_metrics)

                # Check alerts
                self.check_alerts(self.service_metrics, system_metrics)

                # Emit real-time data to connected clients
                try:
                    self.socketio.emit(
                        "metrics_update",
                        {
                            "services": {
                                name: asdict(metrics)
                                for name, metrics in self.service_metrics.items()
                            },
                            "system": asdict(system_metrics),
                        },
                    )
                except Exception as e:
                    self.logger.error(f"Failed to emit metrics update: {e}")

                # Wait for next iteration
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)

        self.logger.info("Monitoring loop stopped")

    def start_monitoring(self):
        """Start the monitoring system"""
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self.monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        self.logger.info("Monitoring system started")

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        self.logger.info("Monitoring system stopped")

    def run_dashboard(
        self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False
    ):
        """Run the web dashboard"""
        self.logger.info(f"Starting monitoring dashboard on {host}:{port}")
        self.start_monitoring()

        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            self.logger.info("Dashboard shutdown requested")
        finally:
            self.stop_monitoring()


# HTML template for the monitoring dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAE.AI System Monitor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #fff; }
        .header { background: #2d2d2d; padding: 1rem; border-bottom: 2px solid #4a9eff; }
        .header h1 { color: #4a9eff; }
        .container { padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { background: #2d2d2d; border-radius: 8px; padding: 1.5rem; border: 1px solid #444; }
        .card h3 { color: #4a9eff; margin-bottom: 1rem; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-healthy { background: #4caf50; }
        .status-warning { background: #ff9800; }
        .status-error { background: #f44336; }
        .status-unknown { background: #9e9e9e; }
        .metric { display: flex; justify-content: space-between; margin: 0.5rem 0; }
        .metric-value { font-weight: bold; }
        .alert { background: #d32f2f; border-radius: 4px; padding: 0.5rem; margin: 0.5rem 0; }
        .alert-medium { background: #f57c00; }
        .alert-low { background: #388e3c; }
        .chart-container { height: 200px; margin-top: 1rem; }
        .refresh-indicator { position: fixed; top: 20px; right: 20px; background: #4a9eff; padding: 0.5rem 1rem; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TRAE.AI System Monitor</h1>
        <div id="refresh-indicator" class="refresh-indicator" style="display: none;">Updating...</div>
    </div>
    
    <div class="container">
        <div class="grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div id="system-metrics">
                    <div class="metric">
                        <span>CPU Usage:</span>
                        <span class="metric-value" id="cpu-usage">--</span>
                    </div>
                    <div class="metric">
                        <span>Memory Usage:</span>
                        <span class="metric-value" id="memory-usage">--</span>
                    </div>
                    <div class="metric">
                        <span>Disk Usage:</span>
                        <span class="metric-value" id="disk-usage">--</span>
                    </div>
                    <div class="metric">
                        <span>Active Connections:</span>
                        <span class="metric-value" id="connections">--</span>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="system-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>🔧 Services Status</h3>
                <div id="services-list"></div>
            </div>
            
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts-list"></div>
            </div>
            
            <div class="card">
                <h3>📈 Performance Metrics</h3>
                <div class="chart-container">
                    <canvas id="performance-chart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let systemChart, performanceChart;
        
        // Initialize charts
        function initCharts() {
            const systemCtx = document.getElementById('system-chart').getContext('2d');
            systemChart = new Chart(systemCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#4a9eff',
                        tension: 0.1
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#ff9800',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    },
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    }
                }
            });
            
            const perfCtx = document.getElementById('performance-chart').getContext('2d');
            performanceChart = new Chart(perfCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        backgroundColor: '#4caf50'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    }
                }
            });
        }
        
        // Update system metrics display
        function updateSystemMetrics(system) {
            document.getElementById('cpu-usage').textContent = system.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory-usage').textContent = system.memory_percent.toFixed(1) + '%';
            document.getElementById('disk-usage').textContent = system.disk_percent.toFixed(1) + '%';
            document.getElementById('connections').textContent = system.active_connections;
            
            // Update system chart
            const now = new Date().toLocaleTimeString();
            systemChart.data.labels.push(now);
            systemChart.data.datasets[0].data.push(system.cpu_percent);
            systemChart.data.datasets[1].data.push(system.memory_percent);
            
            if (systemChart.data.labels.length > 20) {
                systemChart.data.labels.shift();
                systemChart.data.datasets[0].data.shift();
                systemChart.data.datasets[1].data.shift();
            }
            
            systemChart.update('none');
        }
        
        // Update services display
        function updateServices(services) {
            const servicesList = document.getElementById('services-list');
            servicesList.innerHTML = '';
            
            const responseData = [];
            const serviceNames = [];
            
            for (const [name, metrics] of Object.entries(services)) {
                const statusClass = {
                    'healthy': 'status-healthy',
                    'running': 'status-healthy',
                    'unhealthy': 'status-warning',
                    'down': 'status-error',
                    'unreachable': 'status-error',
                    'error': 'status-error'
                }[metrics.status] || 'status-unknown';
                
                const serviceDiv = document.createElement('div');
                serviceDiv.innerHTML = `
                    <div class="metric">
                        <span><span class="status-indicator ${statusClass}"></span>${name}</span>
                        <span class="metric-value">${metrics.status}</span>
                    </div>
                    <div style="font-size: 0.8em; color: #aaa; margin-left: 20px;">
                        CPU: ${metrics.cpu_percent.toFixed(1)}% | 
                        Memory: ${metrics.memory_mb.toFixed(0)}MB | 
                        Response: ${metrics.response_time_ms.toFixed(0)}ms
                    </div>
                `;
                servicesList.appendChild(serviceDiv);
                
                serviceNames.push(name);
                responseData.push(metrics.response_time_ms);
            }
            
            // Update performance chart
            performanceChart.data.labels = serviceNames;
            performanceChart.data.datasets[0].data = responseData;
            performanceChart.update('none');
        }
        
        // Update alerts display
        function updateAlerts(alerts) {
            const alertsList = document.getElementById('alerts-list');
            alertsList.innerHTML = '';
            
            if (alerts.length === 0) {
                alertsList.innerHTML = '<div style="color: #4caf50;">✅ No active alerts</div>';
                return;
            }
            
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.severity}`;
                alertDiv.innerHTML = `
                    <strong>${alert.name}</strong><br>
                    ${alert.message}<br>
                    <small>${new Date(alert.timestamp).toLocaleString()}</small>
                `;
                alertsList.appendChild(alertDiv);
            });
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to monitoring system');
        });
        
        socket.on('metrics_update', function(data) {
            document.getElementById('refresh-indicator').style.display = 'block';
            
            updateSystemMetrics(data.system);
            updateServices(data.services);
            
            setTimeout(() => {
                document.getElementById('refresh-indicator').style.display = 'none';
            }, 1000);
        });
        
        socket.on('alert', function(alert) {
            console.log('New alert:', alert);
            // Could add notification here
        });
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            
            // Load initial data
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.system.length > 0) {
                        updateSystemMetrics(data.system[data.system.length - 1]);
                    }
                    updateServices(data.services);
                    updateAlerts(data.alerts);
                })
                .catch(error => console.error('Error loading initial data:', error));
        });
    </script>
</body>
</html>
"""


def main():
    """Main entry point"""
    monitor = SystemMonitor()

    try:
        monitor.run_dashboard(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutdown requested")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
