#!/usr/bin/env python3
""""""
Monitoring Dashboard - Web Interface for System Monitoring
Provides real - time monitoring, alerting, and system status visualization
""""""

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

from alert_manager import AlertCategory, AlertSeverity, alert_manager
from audit_logger import audit_logger
from compliance_monitor import compliance_monitor
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from health_monitor import health_monitor


class MonitoringDashboard:
    """Web - based monitoring dashboard"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug

        # Initialize Flask app
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.app.config["SECRET_KEY"] = os.getenv(
            "DASHBOARD_SECRET_KEY", "monitoring - dashboard - secret"
# BRACKET_SURGEON: disabled
#         )

        # Enable CORS
        CORS(self.app)

        # Initialize SocketIO for real - time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Setup logging
        self.logger = logging.getLogger("monitoring_dashboard")
        self.logger.setLevel(logging.INFO)

        # Dashboard state
        self.connected_clients = set()
        self.last_broadcast = 0
        self.broadcast_interval = 5  # seconds

        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()

        # Start background tasks
        self._start_background_tasks()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def dashboard():
            """Main dashboard page"""
            return self._render_dashboard_template()

        @self.app.route("/api/health")
        def api_health():
            """Health check endpoint"""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        @self.app.route("/api/alerts")
        def api_alerts():
            """Get alerts"""
            status_filter = request.args.get("status", "active")
            limit = int(request.args.get("limit", 100))

            if status_filter == "active":
                alerts = alert_manager.get_active_alerts()
            elif status_filter == "history":
                alerts = alert_manager.get_alert_history(limit)
            else:
                alerts = alert_manager.get_active_alerts() + alert_manager.get_alert_history(limit)

            return jsonify(
                {
                    "alerts": [self._serialize_alert(alert) for alert in alerts],
                    "total": len(alerts),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        @self.app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
        def api_acknowledge_alert(alert_id):
            """Acknowledge an alert"""
            data = request.get_json() or {}
            acknowledged_by = data.get("acknowledged_by", "dashboard_user")

            success = alert_manager.acknowledge_alert(alert_id, acknowledged_by)

            return jsonify(
                {
                    "success": success,
                    "message": "Alert acknowledged" if success else "Alert not found",
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        @self.app.route("/api/metrics")
        def api_metrics():
            """Get system metrics"""
            metric_name = request.args.get("metric")
            duration_hours = int(request.args.get("duration", 1))

            if metric_name:
                metrics = self._get_metric_history(metric_name, duration_hours)
            else:
                metrics = self._get_all_current_metrics()

            return jsonify({"metrics": metrics, "timestamp": datetime.now().isoformat()})

        @self.app.route("/api/system - status")
        def api_system_status():
            """Get system status"""
            return jsonify(self._get_system_status())

        @self.app.route("/api/compliance")
        def api_compliance():
            """Get compliance status"""
            report = compliance_monitor.get_compliance_report()
            return jsonify({"compliance": report, "timestamp": datetime.now().isoformat()})

        @self.app.route("/api/monitoring - report")
        def api_monitoring_report():
            """Get comprehensive monitoring report"""
            report = alert_manager.get_monitoring_report()
            return jsonify(report)

        @self.app.route("/api/alert - rules")
        def api_alert_rules():
            """Get alert rules"""
            rules = []
            for rule_id, rule in alert_manager.alert_rules.items():
                rules.append(
                    {
                        "rule_id": rule_id,
                        "name": rule.name,
                        "description": rule.description,
                        "category": rule.category.value,
                        "severity": rule.severity.value,
                        "enabled": rule.enabled,
                        "threshold": rule.threshold,
                        "duration_seconds": rule.duration_seconds,
                        "cooldown_seconds": rule.cooldown_seconds,
                        "tags": rule.tags,
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 )

            return jsonify(
                {
                    "rules": rules,
                    "total": len(rules),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        @self.app.route("/api/create - test - alert", methods=["POST"])
        def api_create_test_alert():
            """Create a test alert for demonstration"""
            data = request.get_json() or {}

            from alert_manager import create_custom_alert

            alert_id = create_custom_alert(
                title=data.get("title", "Test Alert"),
                description=data.get(
                    "description", "This is a test alert created from the dashboard"
# BRACKET_SURGEON: disabled
#                 ),
                severity=AlertSeverity(data.get("severity", "warning")),
                category=AlertCategory(data.get("category", "application")),
# BRACKET_SURGEON: disabled
#             )

            return jsonify(
                {
                    "success": True,
                    "alert_id": alert_id,
                    "message": "Test alert created successfully",
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        @self.app.route("/api/export - data")
        def api_export_data():
            """Export monitoring data"""
            export_type = request.args.get("type", "json")

            data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_status": self._get_system_status(),
                "active_alerts": [
                    self._serialize_alert(alert) for alert in alert_manager.get_active_alerts()
# BRACKET_SURGEON: disabled
#                 ],
                "alert_history": [
                    self._serialize_alert(alert) for alert in alert_manager.get_alert_history(1000)
# BRACKET_SURGEON: disabled
#                 ],
                "compliance_report": compliance_monitor.get_compliance_report(),
                "monitoring_report": alert_manager.get_monitoring_report(),
# BRACKET_SURGEON: disabled
#             }

            if export_type == "json":
                response = Response(
                    json.dumps(data, indent=2),
                    mimetype="application/json",
                    headers={
                        "Content - Disposition": f'attachment; filename = monitoring_export_{datetime.now().strftime("%Y % m%d_ % H%M % S")}.json'
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 )
            else:
                # Could add CSV export here
                response = jsonify({"error": "Unsupported export type"})

            return response

    def _setup_socketio_events(self):
        """Setup SocketIO events for real - time updates"""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection"""
            self.connected_clients.add(request.sid)
            self.logger.info(f"Client connected: {request.sid}")

            # Send initial data
            emit("system_status", self._get_system_status())
            emit(
                "alerts_update",
                {
                    "active_alerts": [
                        self._serialize_alert(alert) for alert in alert_manager.get_active_alerts()
# BRACKET_SURGEON: disabled
#                     ],
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             )

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection"""
            self.connected_clients.discard(request.sid)
            self.logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on("subscribe_metrics")
        def handle_subscribe_metrics(data):
            """Handle metrics subscription"""
            metric_names = data.get("metrics", [])
            # Store subscription preferences per client
            # This could be expanded to send only requested metrics
            emit("metrics_update", self._get_all_current_metrics())

        @self.socketio.on("acknowledge_alert")
        def handle_acknowledge_alert(data):
            """Handle alert acknowledgment via WebSocket"""
            alert_id = data.get("alert_id")
            acknowledged_by = data.get("acknowledged_by", "dashboard_user")

            if alert_id:
                success = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
                emit(
                    "alert_acknowledged",
                    {
                        "alert_id": alert_id,
                        "success": success,
                        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 )

                # Broadcast update to all clients
                self._broadcast_alerts_update()

    def _start_background_tasks(self):
        """Start background tasks for real - time updates"""

        def broadcast_loop():
            """Background task to broadcast updates to connected clients"""
            while True:
                try:
                    if (
                        self.connected_clients
                        and time.time() - self.last_broadcast >= self.broadcast_interval
# BRACKET_SURGEON: disabled
#                     ):
                        self._broadcast_system_updates()
                        self.last_broadcast = time.time()

                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Error in broadcast loop: {str(e)}")
                    time.sleep(5)

        # Start broadcast thread
        broadcast_thread = threading.Thread(target=broadcast_loop, daemon=True)
        broadcast_thread.start()

    def _broadcast_system_updates(self):
        """Broadcast system updates to all connected clients"""
        if not self.connected_clients:
            return

        try:
            # Broadcast system status
            self.socketio.emit("system_status", self._get_system_status())

            # Broadcast metrics
            self.socketio.emit("metrics_update", self._get_all_current_metrics())

            # Broadcast alerts if there are changes
            self._broadcast_alerts_update()

        except Exception as e:
            self.logger.error(f"Error broadcasting updates: {str(e)}")

    def _broadcast_alerts_update(self):
        """Broadcast alerts update"""
        try:
            self.socketio.emit(
                "alerts_update",
                {
                    "active_alerts": [
                        self._serialize_alert(alert) for alert in alert_manager.get_active_alerts()
# BRACKET_SURGEON: disabled
#                     ],
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             )
        except Exception as e:
            self.logger.error(f"Error broadcasting alerts update: {str(e)}")

    def _render_dashboard_template(self) -> str:
        """Render dashboard HTML template"""
        # For now, return a simple HTML template
        # In a real implementation, you'd use Flask's render_template with proper templates
        return """"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > System Monitoring Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box - sizing: border - box; }
        body { font - family: -apple - system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans - serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem; text - align: center; }
        .container { max - width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid - template - columns: repeat(auto - fit,
    minmax(300px,
# BRACKET_SURGEON: disabled
#     1fr)); gap: 1.5rem; }
        .card { background: white; border - radius: 8px; padding: 1.5rem; box - shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { margin - bottom: 1rem; color: #2c3e50; }
        .metric { display: flex; justify - content: space - between; margin - bottom: 0.5rem; }
        .metric - value { font - weight: bold; }
        .alert { padding: 0.75rem; margin - bottom: 0.5rem; border - radius: 4px; }
        .alert - critical { background: #ffebee; border - left: 4px solid #f44336; }
        .alert - warning { background: #fff3e0; border - left: 4px solid #ff9800; }
        .alert - info { background: #e3f2fd; border - left: 4px solid #2196f3; }
        .status - indicator { display: inline - block; width: 12px; height: 12px; border - radius: 50%; margin - right: 8px; }
        .status - healthy { background: #4caf50; }
        .status - warning { background: #ff9800; }
        .status - critical { background: #f44336; }
        .btn { background: #3498db; color: white; border: none; padding: 0.5rem 1rem; border - radius: 4px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .chart - container { position: relative; height: 300px; margin - top: 1rem; }
        #connection - status { position: fixed; top: 10px; right: 10px; padding: 0.5rem; border - radius: 4px; color: white; }
        .connected { background: #4caf50; }
        .disconnected { background: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥️ System Monitoring Dashboard</h1>
        <p > Real - time monitoring and alerting system</p>
    </div>

    <div id="connection - status" class="disconnected">Disconnected</div>

    <div class="container">
        <div class="grid">
            <!-- System Status Card -->
            <div class="card">
                <h3>🔧 System Status</h3>
                <div id="system - status">
                    <div class="metric">
                        <span > Overall Health:</span>
                        <span class="metric - value" id="health - score">Loading...</span>
                    </div>
                    <div class="metric">
                        <span > CPU Usage:</span>
                        <span class="metric - value" id="cpu - usage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span > Memory Usage:</span>
                        <span class="metric - value" id="memory - usage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span > Disk Usage:</span>
                        <span class="metric - value" id="disk - usage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span > Uptime:</span>
                        <span class="metric - value" id="uptime">Loading...</span>
                    </div>
                </div>
            </div>

            <!-- Active Alerts Card -->
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="active - alerts">
                    <p > Loading alerts...</p>
                </div>
            </div>

            <!-- Compliance Status Card -->
            <div class="card">
                <h3>✅ Compliance Status</h3>
                <div id="compliance - status">
                    <div class="metric">
                        <span > Compliance Score:</span>
                        <span class="metric - value" id="compliance - score">Loading...</span>
                    </div>
                    <div class="metric">
                        <span > Active Violations:</span>
                        <span class="metric - value" id="compliance - violations">Loading...</span>
                    </div>
                </div>
            </div>

            <!-- Performance Metrics Card -->
            <div class="card">
                <h3>📊 Performance Metrics</h3>
                <div class="chart - container">
                    <canvas id="performance - chart"></canvas>
                </div>
            </div>

            <!-- Quick Actions Card -->
            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <button class="btn" onclick="createTestAlert()">Create Test Alert</button>
                <button class="btn" onclick="exportData()">Export Data</button>
                <button class="btn" onclick="refreshData()">Refresh Data</button>
            </div>

            <!-- Recent Activity Card -->
            <div class="card">
                <h3>📝 Recent Activity</h3>
                <div id="recent - activity">
                    <p > Loading activity...</p>
                </div>
            </div>
        </div>
    </div>

    <script>//Initialize Socket.IO connection
        const socket = io();
        let performanceChart = null;//Connection status
        socket.on('connect', function() {
            document.getElementById('connection - status').textContent = 'Connected';
            document.getElementById('connection - status').className = 'connected';
# BRACKET_SURGEON: disabled
#         });

        socket.on('disconnect', function() {
            document.getElementById('connection - status').textContent = 'Disconnected';
            document.getElementById('connection - status').className = 'disconnected';
# BRACKET_SURGEON: disabled
#         });//System status updates
        socket.on('system_status', function(data) {
            updateSystemStatus(data);
# BRACKET_SURGEON: disabled
#         });//Alerts updates
        socket.on('alerts_update', function(data) {
            updateActiveAlerts(data.active_alerts);
# BRACKET_SURGEON: disabled
#         });//Metrics updates
        socket.on('metrics_update', function(data) {
            updatePerformanceChart(data);
# BRACKET_SURGEON: disabled
#         });

        function updateSystemStatus(data) {
            document.getElementById('health - score').textContent = data.health_score ? data.health_score.toFixed(1) + '%' : 'N/A';
            document.getElementById('cpu - usage').textContent = data.cpu_percent ? data.cpu_percent.toFixed(1) + '%' : 'N/A';
            document.getElementById('memory - usage').textContent = data.memory_percent ? data.memory_percent.toFixed(1) + '%' : 'N/A';
            document.getElementById('disk - usage').textContent = data.disk_percent ? data.disk_percent.toFixed(1) + '%' : 'N/A';
            document.getElementById('uptime').textContent = data.uptime_hours ? formatUptime(data.uptime_hours) : 'N/A';//Update compliance
            document.getElementById('compliance - score').textContent = data.compliance_score ? data.compliance_score.toFixed(1) + '%' : 'N/A';
# BRACKET_SURGEON: disabled
#         }

        function updateActiveAlerts(alerts) {
            const container = document.getElementById('active - alerts');

            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p style="color: #4caf50;">✅ No active alerts</p>';
                return;
# BRACKET_SURGEON: disabled
#             }

            let html = '';
            alerts.forEach(alert => {
                const alertClass = `alert-${alert.severity}`;
                const statusIndicator = getStatusIndicator(alert.severity);

                html += `
                    <div class="alert ${alertClass}">
                        ${statusIndicator}
                        <strong>${alert.title}</strong><br>
                        <small>${alert.description}</small><br>
                        <small > Created: ${new Date(alert.created_at).toLocaleString()}</small>
                        ${alert.status === 'active' ? `<button class="btn" style="float: right; font - size: 12px; padding: 0.25rem 0.5rem;" onclick="acknowledgeAlert('${alert.alert_id}')">Acknowledge</button>` : ''}
                    </div>
                `;
# BRACKET_SURGEON: disabled
#             });

            container.innerHTML = html;
# BRACKET_SURGEON: disabled
#         }

        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performance - chart').getContext('2d');

            if (performanceChart) {
                performanceChart.destroy();
# BRACKET_SURGEON: disabled
#             }

            performanceChart = new Chart(ctx, {
                type: 'line',
                    data: {
                    labels: ['CPU', 'Memory', 'Disk', 'Health'],
                        datasets: [{
                        label: 'System Metrics (%)',
                            data: [
                            data.cpu_percent || 0,
                                data.memory_percent || 0,
                                data.disk_percent || 0,
                                data.health_score || 0
# BRACKET_SURGEON: disabled
#                         ],
                            borderColor: '#3498db','
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4
# BRACKET_SURGEON: disabled
#                     }]
# BRACKET_SURGEON: disabled
#                 },
                    options: {
                    responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                        y: {
                            beginAtZero: true,
                                max: 100
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             });
# BRACKET_SURGEON: disabled
#         }

        function getStatusIndicator(severity) {
            const statusClass = severity === 'critical' || severity === 'emergency' ? 'status - critical' :
                              severity === 'warning' ? 'status - warning' : 'status - healthy';
            return `<span class="status - indicator ${statusClass}"></span>`;
# BRACKET_SURGEON: disabled
#         }

        function formatUptime(hours) {
            const days = Math.floor(hours/24);
            const remainingHours = Math.floor(hours % 24);
            return `${days}d ${remainingHours}h`;
# BRACKET_SURGEON: disabled
#         }

        function acknowledgeAlert(alertId) {
            socket.emit('acknowledge_alert', {
                alert_id: alertId,
                    acknowledged_by: 'dashboard_user'
# BRACKET_SURGEON: disabled
#             });
# BRACKET_SURGEON: disabled
#         }

        function createTestAlert() {
            fetch("/api/create - test - alert', {
                method: 'POST',
                    headers: {
                    'Content - Type': 'application/json'
# BRACKET_SURGEON: disabled
#                 },
                    body: JSON.stringify({
                    title: 'Dashboard Test Alert',
                        description: 'This is a test alert created from the dashboard',
                        severity: 'warning',
                        category: 'application'
# BRACKET_SURGEON: disabled
#                 })
# BRACKET_SURGEON: disabled
#             })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Test alert created successfully!');
                } else {
                    alert('Failed to create test alert');
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             })
            .catch(error => {
                console.error('Error creating test alert:', error);
                alert('Error creating test alert');
# BRACKET_SURGEON: disabled
#             });
# BRACKET_SURGEON: disabled
#         }

        function exportData() {
            window.open('/api/export - data?type = json', '_blank');
# BRACKET_SURGEON: disabled
#         }

        function refreshData() {
            location.reload();
# BRACKET_SURGEON: disabled
#         }//Load initial compliance data
        fetch("/api/compliance')
            .then(response => response.json())
            .then(data => {
                if (data.compliance) {
                    document.getElementById('compliance - score').textContent = data.compliance.overall_compliance_score.toFixed(1) + '%';
                    document.getElementById('compliance - violations').textContent = data.compliance.violations.length;
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             })
            .catch(error => console.error('Error loading compliance data:', error));//Load recent activity
        fetch("/api/alerts?status = history&limit = 5')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('recent - activity');
                if (data.alerts && data.alerts.length > 0) {
                    let html = '';
                    data.alerts.slice(-5).forEach(alert => {
                        html += `
                            <div style="padding: 0.5rem 0; border - bottom: 1px solid #eee;">"
                                <strong>${alert.title}</strong><br>
                                <small>${alert.status} - ${new Date(alert.created_at).toLocaleString()}</small>
                            </div>
                        `;
# BRACKET_SURGEON: disabled
#                     });
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p > No recent activity</p>';
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             })
            .catch(error => {
                console.error('Error loading recent activity:', error);
                document.getElementById('recent - activity').innerHTML = '<p > Error loading activity</p>';
# BRACKET_SURGEON: disabled
#             });
    </script>
</body>
</html>
        """"""

    def _serialize_alert(self, alert) -> Dict[str, Any]:
        """Serialize alert object to dictionary"""
        return {
            "alert_id": alert.alert_id,
            "rule_id": alert.rule_id,
            "title": alert.title,
            "description": alert.description,
            "category": alert.category.value,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "resolved_at": alert.resolved_at,
            "acknowledged_at": alert.acknowledged_at,
            "acknowledged_by": alert.acknowledged_by,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "metadata": alert.metadata,
            "escalation_level": alert.escalation_level,
# BRACKET_SURGEON: disabled
#         }

    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""

        from alert_manager import get_system_health_summary

        health_summary = get_system_health_summary()
        health_status = health_monitor.get_system_health()

        return {
            "cpu_percent": health_summary.get("cpu_percent", 0),
            "memory_percent": health_summary.get("memory_percent", 0),
            "disk_percent": health_summary.get("disk_percent", 0),
            "health_score": health_summary.get("health_score", 0),
            "active_alerts": health_summary.get("active_alerts", 0),
            "monitoring_active": health_summary.get("monitoring_active", False),
            "uptime_hours": getattr(health_status, "uptime_hours", 0),
            "response_time_ms": getattr(health_status, "response_time_ms", 0),
            "compliance_score": alert_manager._get_latest_metric_value("compliance.score", 0),
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def _get_all_current_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        metrics = {}

        for metric_name, metric_buffer in alert_manager.metrics_buffer.items():
            if metric_buffer:
                latest_point = metric_buffer[-1]
                metrics[metric_name] = {
                    "value": latest_point.value,
                    "timestamp": latest_point.timestamp,
                    "labels": latest_point.labels,
# BRACKET_SURGEON: disabled
#                 }

        # Add calculated metrics
        metrics["cpu_percent"] = alert_manager._get_latest_metric_value("system.cpu_percent", 0)
        metrics["memory_percent"] = alert_manager._get_latest_metric_value(
            "system.memory_percent", 0
# BRACKET_SURGEON: disabled
#         )
        metrics["disk_percent"] = alert_manager._get_latest_metric_value("system.disk_percent", 0)
        metrics["health_score"] = alert_manager._get_latest_metric_value("health.overall_score", 0)

        return metrics

    def _get_metric_history(self, metric_name: str, duration_hours: int) -> List[Dict[str, Any]]:
        """Get metric history for specified duration"""
        if metric_name not in alert_manager.metrics_buffer:
            return []

        cutoff_time = time.time() - (duration_hours * 3600)
        history = []

        for point in alert_manager.metrics_buffer[metric_name]:
            if point.timestamp >= cutoff_time:
                history.append(
                    {
                        "timestamp": point.timestamp,
                        "value": point.value,
                        "labels": point.labels,
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 )

        return history

    def run(self):
        """Run the dashboard server"""
        self.logger.info(f"Starting monitoring dashboard on {self.host}:{self.port}")

        # Log audit event
        audit_logger.log_security_event(
            event_type="dashboard_started",
            severity="info",
            additional_data={"host": self.host, "port": self.port, "debug": self.debug},
# BRACKET_SURGEON: disabled
#         )

        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True,  # For development only
# BRACKET_SURGEON: disabled
#             )
        except Exception as e:
            self.logger.error(f"Error running dashboard: {str(e)}")
            raise

    def stop(self):
        """Stop the dashboard server"""
        self.logger.info("Stopping monitoring dashboard")

        # Log audit event
        audit_logger.log_security_event(
            event_type="dashboard_stopped", severity="info", additional_data={}
# BRACKET_SURGEON: disabled
#         )


# Global dashboard instance
dashboard = None


def start_dashboard(host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
    """Start the monitoring dashboard"""
    global dashboard

    if dashboard is None:
        dashboard = MonitoringDashboard(host=host, port=port, debug=debug)

    dashboard.run()


def stop_dashboard():
    """Stop the monitoring dashboard"""
    global dashboard

    if dashboard:
        dashboard.stop()
        dashboard = None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="System Monitoring Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    start_dashboard(host=args.host, port=args.port, debug=args.debug)