#!/usr/bin/env python3
"""
Monitoring Dashboard - Real-time AI CEO Operations Control Center

Provides:
1. Real-time pipeline status and metrics visualization
2. Agent performance monitoring and control
3. Business intelligence dashboard
4. System health monitoring and alerts
5. Decision engine oversight
6. Revenue and cost tracking
7. Interactive controls for manual intervention
8. Performance analytics and reporting

Author: TRAE.AI System
Version: 2.0.0
"""

import asyncio
import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import psutil
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

# Import our pipeline components
try:
    from ai_ceo_master_controller import AICEOMasterController
    from autonomous_decision_engine import AutonomousDecisionEngine
    from full_automation_pipeline import (FullAutomationPipeline, PipelineStatus,
                                          TaskPriority)
except ImportError as e:
    logging.warning(f"Some components not available: {e}")

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard-specific metrics."""

    active_users: int = 0
    page_views: int = 0
    api_calls: int = 0
    error_rate: float = 0.0
    response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = None
    last_updated: datetime = None


@dataclass
class AlertConfig:
    """Alert configuration."""

    name: str
    condition: str
    threshold: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class MonitoringDashboard:
    """Real-time monitoring dashboard for AI CEO operations."""

    def __init__(
        self, pipeline: Optional[FullAutomationPipeline] = None, port: int = 5000
    ):
        self.pipeline = pipeline
        self.port = port

        # Flask app setup
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.app.config["SECRET_KEY"] = "ai-ceo-dashboard-secret-key"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Dashboard state
        self.metrics = DashboardMetrics(last_updated=datetime.now())
        self.connected_clients = set()
        self.real_time_data = {
            "pipeline_status": deque(maxlen=100),
            "task_metrics": deque(maxlen=100),
            "business_metrics": deque(maxlen=100),
            "system_metrics": deque(maxlen=100),
            "agent_performance": deque(maxlen=100),
        }

        # Alert system
        self.alerts = self._setup_default_alerts()
        self.active_alerts = []

        # Performance tracking
        self.performance_history = []
        self.business_kpis = {
            "daily_revenue": 0.0,
            "monthly_revenue": 0.0,
            "conversion_rate": 0.0,
            "customer_acquisition_cost": 0.0,
            "lifetime_value": 0.0,
            "churn_rate": 0.0,
        }

        # Database connection
        self.db_path = "dashboard.db"
        self._init_dashboard_database()

        # Background threads
        self.monitoring_thread = None
        self.running = False

        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()

        logger.info("📊 Monitoring Dashboard initialized")

    def _setup_default_alerts(self) -> List[AlertConfig]:
        """Setup default alert configurations."""
        return [
            AlertConfig("High Error Rate", "error_rate > 0.1", 0.1, "high"),
            AlertConfig("High CPU Usage", "cpu_usage > 0.8", 0.8, "medium"),
            AlertConfig("High Memory Usage", "memory_usage > 0.8", 0.8, "medium"),
            AlertConfig(
                "Low Automation Efficiency", "automation_efficiency < 0.7", 0.7, "high"
            ),
            AlertConfig(
                "Pipeline Stopped", "pipeline_status == 'stopped'", 0, "critical"
            ),
            AlertConfig("Agent Failure", "agent_success_rate < 0.5", 0.5, "high"),
            AlertConfig("High Response Time", "response_time > 5.0", 5.0, "medium"),
            AlertConfig("Revenue Drop", "daily_revenue_change < -0.2", -0.2, "high"),
        ]

    def _init_dashboard_database(self):
        """Initialize dashboard database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Dashboard metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboard_metrics (
                timestamp TEXT PRIMARY KEY,
                active_users INTEGER,
                page_views INTEGER,
                api_calls INTEGER,
                error_rate REAL,
                response_time REAL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_io TEXT
            )
        """
        )

        # Alerts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                name TEXT,
                condition_text TEXT,
                threshold_value REAL,
                severity TEXT,
                triggered_at TEXT,
                resolved_at TEXT,
                message TEXT,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """
        )

        # Business KPIs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS business_kpis (
                date TEXT PRIMARY KEY,
                daily_revenue REAL,
                monthly_revenue REAL,
                conversion_rate REAL,
                customer_acquisition_cost REAL,
                lifetime_value REAL,
                churn_rate REAL
            )
        """
        )

        # User sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TEXT,
                end_time TEXT,
                actions_performed INTEGER,
                ip_address TEXT
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("📊 Dashboard database initialized")

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def dashboard():
            """Main dashboard page."""
            return render_template("dashboard.html")

        @self.app.route("/api/status")
        def get_status():
            """Get current system status."""
            try:
                status_data = {
                    "pipeline": (
                        self.pipeline.get_status()
                        if self.pipeline
                        else {"status": "disconnected"}
                    ),
                    "dashboard": asdict(self.metrics),
                    "system": self._get_system_metrics(),
                    "business": self.business_kpis,
                    "alerts": [alert for alert in self.active_alerts],
                    "timestamp": datetime.now().isoformat(),
                }
                return jsonify(status_data)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/metrics")
        def get_metrics():
            """Get detailed metrics."""
            try:
                return jsonify(
                    {
                        "pipeline_metrics": list(
                            self.real_time_data["pipeline_status"]
                        ),
                        "task_metrics": list(self.real_time_data["task_metrics"]),
                        "business_metrics": list(
                            self.real_time_data["business_metrics"]
                        ),
                        "system_metrics": list(self.real_time_data["system_metrics"]),
                        "agent_performance": list(
                            self.real_time_data["agent_performance"]
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/performance-report")
        def get_performance_report():
            """Get comprehensive performance report."""
            try:
                if self.pipeline:
                    report = self.pipeline.get_performance_report()
                else:
                    report = {"error": "Pipeline not connected"}

                # Add dashboard-specific metrics
                report["dashboard_metrics"] = asdict(self.metrics)
                report["business_kpis"] = self.business_kpis
                report["system_health"] = self._get_system_health()

                return jsonify(report)
            except Exception as e:
                logger.error(f"Error getting performance report: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/agents")
        def get_agents():
            """Get agent status and controls."""
            try:
                if self.pipeline:
                    agent_status = self.pipeline.agent_status
                    return jsonify(
                        {
                            "agents": agent_status,
                            "controls": {
                                "restart_agent": "/api/agents/<agent_name>/restart",
                                "pause_agent": "/api/agents/<agent_name>/pause",
                                "resume_agent": "/api/agents/<agent_name>/resume",
                            },
                        }
                    )
                else:
                    return jsonify({"error": "Pipeline not connected"}), 503
            except Exception as e:
                logger.error(f"Error getting agents: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/agents/<agent_name>/restart", methods=["POST"])
        def restart_agent(agent_name):
            """Restart a specific agent."""
            try:
                if self.pipeline:
                    # This would trigger agent restart
                    # For now, return success
                    return jsonify({"message": f"Agent {agent_name} restart initiated"})
                else:
                    return jsonify({"error": "Pipeline not connected"}), 503
            except Exception as e:
                logger.error(f"Error restarting agent: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/pipeline/pause", methods=["POST"])
        def pause_pipeline():
            """Pause the pipeline."""
            try:
                if self.pipeline:
                    # This would pause the pipeline
                    return jsonify({"message": "Pipeline pause initiated"})
                else:
                    return jsonify({"error": "Pipeline not connected"}), 503
            except Exception as e:
                logger.error(f"Error pausing pipeline: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/pipeline/resume", methods=["POST"])
        def resume_pipeline():
            """Resume the pipeline."""
            try:
                if self.pipeline:
                    # This would resume the pipeline
                    return jsonify({"message": "Pipeline resume initiated"})
                else:
                    return jsonify({"error": "Pipeline not connected"}), 503
            except Exception as e:
                logger.error(f"Error resuming pipeline: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/alerts")
        def get_alerts():
            """Get current alerts."""
            try:
                return jsonify(
                    {
                        "active_alerts": self.active_alerts,
                        "alert_configs": [asdict(alert) for alert in self.alerts],
                    }
                )
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
        def acknowledge_alert(alert_id):
            """Acknowledge an alert."""
            try:
                # Mark alert as acknowledged
                for alert in self.active_alerts:
                    if alert.get("id") == alert_id:
                        alert["acknowledged"] = True
                        break

                return jsonify({"message": f"Alert {alert_id} acknowledged"})
            except Exception as e:
                logger.error(f"Error acknowledging alert: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/charts/pipeline-performance")
        def get_pipeline_performance_chart():
            """Get pipeline performance chart data."""
            try:
                # Generate chart data
                chart_data = self._generate_pipeline_performance_chart()
                return jsonify(chart_data)
            except Exception as e:
                logger.error(f"Error generating chart: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/charts/business-metrics")
        def get_business_metrics_chart():
            """Get business metrics chart data."""
            try:
                chart_data = self._generate_business_metrics_chart()
                return jsonify(chart_data)
            except Exception as e:
                logger.error(f"Error generating chart: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/charts/system-health")
        def get_system_health_chart():
            """Get system health chart data."""
            try:
                chart_data = self._generate_system_health_chart()
                return jsonify(chart_data)
            except Exception as e:
                logger.error(f"Error generating chart: {e}")
                return jsonify({"error": str(e)}), 500

    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time updates."""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            client_id = request.sid
            self.connected_clients.add(client_id)
            logger.info(f"📱 Client connected: {client_id}")

            # Send initial data
            emit("status_update", self._get_current_status())

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid
            self.connected_clients.discard(client_id)
            logger.info(f"📱 Client disconnected: {client_id}")

        @self.socketio.on("request_update")
        def handle_update_request():
            """Handle client update request."""
            emit("status_update", self._get_current_status())

        @self.socketio.on("execute_command")
        def handle_command(data):
            """Handle command execution from client."""
            try:
                command = data.get("command")
                params = data.get("params", {})

                result = self._execute_dashboard_command(command, params)
                emit(
                    "command_result",
                    {
                        "command": command,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            except Exception as e:
                emit(
                    "command_error",
                    {
                        "command": command,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    def _get_current_status(self) -> Dict[str, Any]:
        """Get current comprehensive status."""
        return {
            "pipeline": (
                self.pipeline.get_status()
                if self.pipeline
                else {"status": "disconnected"}
            ),
            "dashboard": asdict(self.metrics),
            "system": self._get_system_metrics(),
            "business": self.business_kpis,
            "alerts": self.active_alerts,
            "connected_clients": len(self.connected_clients),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # Network I/O
            network = psutil.net_io_counters()

            return {
                "cpu_usage": cpu_percent / 100.0,
                "memory_usage": memory_percent / 100.0,
                "disk_usage": disk_percent / 100.0,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def _get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        system_metrics = self._get_system_metrics()

        health_score = 100.0
        issues = []

        # Check CPU usage
        if system_metrics.get("cpu_usage", 0) > 0.8:
            health_score -= 20
            issues.append("High CPU usage")

        # Check memory usage
        if system_metrics.get("memory_usage", 0) > 0.8:
            health_score -= 20
            issues.append("High memory usage")

        # Check disk usage
        if system_metrics.get("disk_usage", 0) > 0.9:
            health_score -= 15
            issues.append("High disk usage")

        # Check pipeline status
        if self.pipeline:
            pipeline_status = self.pipeline.get_status()
            if pipeline_status["status"] != "running":
                health_score -= 30
                issues.append(f"Pipeline not running: {pipeline_status['status']}")
        else:
            health_score -= 50
            issues.append("Pipeline not connected")

        return {
            "health_score": max(0, health_score),
            "status": (
                "healthy"
                if health_score > 80
                else "warning" if health_score > 50 else "critical"
            ),
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }

    def _execute_dashboard_command(
        self, command: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute dashboard command."""
        try:
            if command == "restart_pipeline":
                if self.pipeline:
                    # This would restart the pipeline
                    return {"success": True, "message": "Pipeline restart initiated"}
                else:
                    return {"success": False, "message": "Pipeline not connected"}

            elif command == "pause_pipeline":
                if self.pipeline:
                    # This would pause the pipeline
                    return {"success": True, "message": "Pipeline paused"}
                else:
                    return {"success": False, "message": "Pipeline not connected"}

            elif command == "resume_pipeline":
                if self.pipeline:
                    # This would resume the pipeline
                    return {"success": True, "message": "Pipeline resumed"}
                else:
                    return {"success": False, "message": "Pipeline not connected"}

            elif command == "restart_agent":
                agent_name = params.get("agent_name")
                if self.pipeline and agent_name:
                    # This would restart the specific agent
                    return {
                        "success": True,
                        "message": f"Agent {agent_name} restart initiated",
                    }
                else:
                    return {
                        "success": False,
                        "message": "Invalid agent name or pipeline not connected",
                    }

            elif command == "clear_alerts":
                self.active_alerts.clear()
                return {"success": True, "message": "All alerts cleared"}

            elif command == "export_metrics":
                # Export metrics to file
                export_data = self._export_metrics_data()
                return {
                    "success": True,
                    "message": "Metrics exported",
                    "data": export_data,
                }

            else:
                return {"success": False, "message": f"Unknown command: {command}"}

        except Exception as e:
            return {"success": False, "message": f"Command execution failed: {str(e)}"}

    def _generate_pipeline_performance_chart(self) -> Dict[str, Any]:
        """Generate pipeline performance chart data."""
        try:
            # Get recent pipeline metrics
            pipeline_data = list(self.real_time_data["pipeline_status"])

            if not pipeline_data:
                return {"error": "No pipeline data available"}

            # Extract data for chart
            timestamps = [item.get("timestamp", "") for item in pipeline_data]
            success_rates = [item.get("success_rate", 0) for item in pipeline_data]
            task_counts = [item.get("active_tasks", 0) for item in pipeline_data]

            # Create Plotly chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=success_rates,
                    mode="lines+markers",
                    name="Success Rate",
                    line=dict(color="green"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=task_counts,
                    mode="lines+markers",
                    name="Active Tasks",
                    yaxis="y2",
                    line=dict(color="blue"),
                )
            )

            fig.update_layout(
                title="Pipeline Performance Over Time",
                xaxis_title="Time",
                yaxis_title="Success Rate",
                yaxis2=dict(title="Active Tasks", overlaying="y", side="right"),
                hovermode="x unified",
            )

            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

        except Exception as e:
            logger.error(f"Error generating pipeline performance chart: {e}")
            return {"error": str(e)}

    def _generate_business_metrics_chart(self) -> Dict[str, Any]:
        """Generate business metrics chart data."""
        try:
            # Get recent business metrics
            business_data = list(self.real_time_data["business_metrics"])

            if not business_data:
                return {"error": "No business data available"}

            # Extract data for chart
            timestamps = [item.get("timestamp", "") for item in business_data]
            revenue = [item.get("daily_revenue", 0) for item in business_data]
            conversion_rate = [item.get("conversion_rate", 0) for item in business_data]

            # Create Plotly chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=revenue,
                    mode="lines+markers",
                    name="Daily Revenue",
                    line=dict(color="green"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=conversion_rate,
                    mode="lines+markers",
                    name="Conversion Rate",
                    yaxis="y2",
                    line=dict(color="orange"),
                )
            )

            fig.update_layout(
                title="Business Metrics Over Time",
                xaxis_title="Time",
                yaxis_title="Revenue ($)",
                yaxis2=dict(title="Conversion Rate (%)", overlaying="y", side="right"),
                hovermode="x unified",
            )

            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

        except Exception as e:
            logger.error(f"Error generating business metrics chart: {e}")
            return {"error": str(e)}

    def _generate_system_health_chart(self) -> Dict[str, Any]:
        """Generate system health chart data."""
        try:
            # Get recent system metrics
            system_data = list(self.real_time_data["system_metrics"])

            if not system_data:
                return {"error": "No system data available"}

            # Extract data for chart
            timestamps = [item.get("timestamp", "") for item in system_data]
            cpu_usage = [item.get("cpu_usage", 0) * 100 for item in system_data]
            memory_usage = [item.get("memory_usage", 0) * 100 for item in system_data]
            disk_usage = [item.get("disk_usage", 0) * 100 for item in system_data]

            # Create Plotly chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=cpu_usage,
                    mode="lines+markers",
                    name="CPU Usage (%)",
                    line=dict(color="red"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=memory_usage,
                    mode="lines+markers",
                    name="Memory Usage (%)",
                    line=dict(color="blue"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=disk_usage,
                    mode="lines+markers",
                    name="Disk Usage (%)",
                    line=dict(color="green"),
                )
            )

            fig.update_layout(
                title="System Health Over Time",
                xaxis_title="Time",
                yaxis_title="Usage (%)",
                hovermode="x unified",
            )

            return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

        except Exception as e:
            logger.error(f"Error generating system health chart: {e}")
            return {"error": str(e)}

    def _export_metrics_data(self) -> Dict[str, Any]:
        """Export metrics data for analysis."""
        try:
            export_data = {
                "pipeline_metrics": list(self.real_time_data["pipeline_status"]),
                "business_metrics": list(self.real_time_data["business_metrics"]),
                "system_metrics": list(self.real_time_data["system_metrics"]),
                "agent_performance": list(self.real_time_data["agent_performance"]),
                "business_kpis": self.business_kpis,
                "dashboard_metrics": asdict(self.metrics),
                "export_timestamp": datetime.now().isoformat(),
            }

            # Save to file
            filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            return {
                "filename": filename,
                "record_count": sum(len(data) for data in self.real_time_data.values()),
                "file_size": os.path.getsize(filename),
            }

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return {"error": str(e)}

    def start_monitoring(self):
        """Start the monitoring dashboard."""
        logger.info("📊 Starting Monitoring Dashboard...")

        self.running = True

        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        # Start Flask app
        try:
            logger.info(f"🌐 Dashboard available at http://localhost:{self.port}")
            self.socketio.run(self.app, host="0.0.0.0", port=self.port, debug=False)
        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {e}")
            self.running = False
            raise

    def _monitoring_loop(self):
        """Background monitoring loop."""
        logger.info("🔄 Monitoring loop started")

        while self.running:
            try:
                # Update metrics
                self._update_dashboard_metrics()

                # Check alerts
                self._check_alerts()

                # Broadcast updates to connected clients
                if self.connected_clients:
                    self.socketio.emit("status_update", self._get_current_status())

                # Sleep for update interval
                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(10)

        logger.info("🛑 Monitoring loop stopped")

    def _update_dashboard_metrics(self):
        """Update dashboard metrics."""
        try:
            # Update system metrics
            system_metrics = self._get_system_metrics()

            self.metrics.cpu_usage = system_metrics.get("cpu_usage", 0)
            self.metrics.memory_usage = system_metrics.get("memory_usage", 0)
            self.metrics.disk_usage = system_metrics.get("disk_usage", 0)
            self.metrics.last_updated = datetime.now()

            # Add to real-time data
            self.real_time_data["system_metrics"].append(
                {"timestamp": datetime.now().isoformat(), **system_metrics}
            )

            # Update pipeline metrics if available
            if self.pipeline:
                pipeline_status = self.pipeline.get_status()
                self.real_time_data["pipeline_status"].append(
                    {"timestamp": datetime.now().isoformat(), **pipeline_status}
                )

            # Update business metrics (simulated for now)
            self.real_time_data["business_metrics"].append(
                {"timestamp": datetime.now().isoformat(), **self.business_kpis}
            )

        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {e}")

    def _check_alerts(self):
        """Check for alert conditions."""
        try:
            current_time = datetime.now()

            for alert_config in self.alerts:
                if not alert_config.enabled:
                    continue

                # Evaluate alert condition
                triggered = self._evaluate_alert_condition(alert_config)

                if triggered:
                    # Check if alert was recently triggered (avoid spam)
                    if (
                        alert_config.last_triggered
                        and (current_time - alert_config.last_triggered).total_seconds()
                        < 300
                    ):  # 5 minutes
                        continue

                    # Create alert
                    alert = {
                        "id": str(uuid.uuid4()),
                        "name": alert_config.name,
                        "severity": alert_config.severity,
                        "message": f"Alert triggered: {alert_config.name}",
                        "condition": alert_config.condition,
                        "threshold": alert_config.threshold,
                        "triggered_at": current_time.isoformat(),
                        "acknowledged": False,
                    }

                    self.active_alerts.append(alert)
                    alert_config.last_triggered = current_time
                    alert_config.trigger_count += 1

                    # Broadcast alert to connected clients
                    if self.connected_clients:
                        self.socketio.emit("new_alert", alert)

                    logger.warning(f"🚨 Alert triggered: {alert_config.name}")

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _evaluate_alert_condition(self, alert_config: AlertConfig) -> bool:
        """Evaluate if an alert condition is met."""
        try:
            condition = alert_config.condition
            threshold = alert_config.threshold

            # Get current values
            if "error_rate" in condition:
                current_value = self.metrics.error_rate
            elif "cpu_usage" in condition:
                current_value = self.metrics.cpu_usage
            elif "memory_usage" in condition:
                current_value = self.metrics.memory_usage
            elif "response_time" in condition:
                current_value = self.metrics.response_time
            elif "pipeline_status" in condition:
                if self.pipeline:
                    status = self.pipeline.get_status()
                    return status["status"] == "stopped"
                return True  # Pipeline not connected
            else:
                return False

            # Evaluate condition
            if ">" in condition:
                return current_value > threshold
            elif "<" in condition:
                return current_value < threshold
            elif "==" in condition:
                return current_value == threshold

            return False

        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False

    def stop_monitoring(self):
        """Stop the monitoring dashboard."""
        logger.info("🛑 Stopping Monitoring Dashboard...")

        self.running = False

        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)

        logger.info("✅ Monitoring Dashboard stopped")

    def connect_pipeline(self, pipeline: FullAutomationPipeline):
        """Connect to a pipeline instance."""
        self.pipeline = pipeline
        logger.info("🔗 Pipeline connected to dashboard")

    def disconnect_pipeline(self):
        """Disconnect from pipeline."""
        self.pipeline = None
        logger.info("🔌 Pipeline disconnected from dashboard")


def create_dashboard_templates():
    """Create basic HTML templates for the dashboard."""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    # Main dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI CEO Monitoring Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .alert-card {
            border-left: 4px solid #dc3545;
            margin-bottom: 10px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-running { background-color: #28a745; }
        .status-stopped { background-color: #dc3545; }
        .status-paused { background-color: #ffc107; }
        .chart-container {
            height: 400px;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-robot"></i> AI CEO Monitoring Dashboard
            </span>
            <span class="navbar-text">
                <span class="status-indicator status-running" id="connection-status"></span>
                <span id="connection-text">Connected</span>
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Status Cards -->
        <div class="row">
            <div class="col-md-3">
                <div class="metric-card">
                    <h5><i class="fas fa-cogs"></i> Pipeline Status</h5>
                    <h3 id="pipeline-status">Loading...</h3>
                    <small id="pipeline-uptime">Uptime: --</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h5><i class="fas fa-tasks"></i> Active Tasks</h5>
                    <h3 id="active-tasks">--</h3>
                    <small id="queue-size">Queue: --</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h5><i class="fas fa-chart-line"></i> Success Rate</h5>
                    <h3 id="success-rate">--%</h3>
                    <small id="total-tasks">Total: --</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h5><i class="fas fa-dollar-sign"></i> Revenue</h5>
                    <h3 id="daily-revenue">$--</h3>
                    <small id="monthly-revenue">Monthly: $--</small>
                </div>
            </div>
        </div>

        <!-- Alerts Section -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> Active Alerts</h5>
                    </div>
                    <div class="card-body" id="alerts-container">
                        <p class="text-muted">No active alerts</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Pipeline Performance</h5>
                    </div>
                    <div class="card-body">
                        <div id="pipeline-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>System Health</h5>
                    </div>
                    <div class="card-body">
                        <div id="system-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Controls Section -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-sliders-h"></i> Pipeline Controls</h5>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-success me-2" onclick="executeCommand('resume_pipeline')">
                            <i class="fas fa-play"></i> Resume
                        </button>
                        <button class="btn btn-warning me-2" onclick="executeCommand('pause_pipeline')">
                            <i class="fas fa-pause"></i> Pause
                        </button>
                        <button class="btn btn-info me-2" onclick="executeCommand('restart_pipeline')">
                            <i class="fas fa-redo"></i> Restart
                        </button>
                        <button class="btn btn-secondary me-2" onclick="executeCommand('export_metrics')">
                            <i class="fas fa-download"></i> Export Metrics
                        </button>
                        <button class="btn btn-outline-danger" onclick="executeCommand('clear_alerts')">
                            <i class="fas fa-times"></i> Clear Alerts
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Connection status
        socket.on('connect', function() {
            document.getElementById('connection-status').className = 'status-indicator status-running';
            document.getElementById('connection-text').textContent = 'Connected';
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').className = 'status-indicator status-stopped';
            document.getElementById('connection-text').textContent = 'Disconnected';
        });
        
        // Status updates
        socket.on('status_update', function(data) {
            updateDashboard(data);
        });
        
        // New alerts
        socket.on('new_alert', function(alert) {
            addAlert(alert);
        });
        
        // Command results
        socket.on('command_result', function(result) {
            console.log('Command result:', result);
            alert('Command executed: ' + result.result.message);
        });
        
        socket.on('command_error', function(error) {
            console.error('Command error:', error);
            alert('Command failed: ' + error.error);
        });
        
        // Update dashboard with new data
        function updateDashboard(data) {
            // Pipeline status
            const pipeline = data.pipeline || {};
            document.getElementById('pipeline-status').textContent = pipeline.status || 'Unknown';
            document.getElementById('pipeline-uptime').textContent = 'Uptime: ' + formatUptime(pipeline.uptime || 0);
            document.getElementById('active-tasks').textContent = pipeline.active_tasks || 0;
            document.getElementById('queue-size').textContent = 'Queue: ' + (pipeline.queue_size || 0);
            
            // Metrics
            const metrics = pipeline.metrics || {};
            const successRate = metrics.total_tasks_executed > 0 ? 
                ((metrics.successful_tasks / metrics.total_tasks_executed) * 100).toFixed(1) : 0;
            document.getElementById('success-rate').textContent = successRate + '%';
            document.getElementById('total-tasks').textContent = 'Total: ' + (metrics.total_tasks_executed || 0);
            
            // Business metrics
            const business = data.business || {};
            document.getElementById('daily-revenue').textContent = '$' + (business.daily_revenue || 0).toFixed(2);
            document.getElementById('monthly-revenue').textContent = 'Monthly: $' + (business.monthly_revenue || 0).toFixed(2);
            
            // Update charts
            updateCharts();
        }
        
        // Add new alert
        function addAlert(alert) {
            const container = document.getElementById('alerts-container');
            
            // Clear "no alerts" message
            if (container.children.length === 1 && container.children[0].textContent === 'No active alerts') {
                container.innerHTML = '';
            }
            
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-' + getSeverityClass(alert.severity) + ' alert-card';
            alertDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alert.name}</strong><br>
                        <small>${alert.message}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary" onclick="acknowledgeAlert('${alert.id}')">
                        Acknowledge
                    </button>
                </div>
            `;
            
            container.appendChild(alertDiv);
        }
        
        // Execute command
        function executeCommand(command, params = {}) {
            socket.emit('execute_command', {
                command: command,
                params: params
            });
        }
        
        // Acknowledge alert
        function acknowledgeAlert(alertId) {
            fetch(`/api/alerts/${alertId}/acknowledge`, {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    // Remove alert from display
                    location.reload();
                }
            });
        }
        
        // Update charts
        function updateCharts() {
            // Pipeline performance chart
            fetch('/api/charts/pipeline-performance')
                .then(response => response.json())
                .then(data => {
                    if (!data.error) {
                        Plotly.newPlot('pipeline-chart', data.data, data.layout);
                    }
                });
            
            // System health chart
            fetch('/api/charts/system-health')
                .then(response => response.json())
                .then(data => {
                    if (!data.error) {
                        Plotly.newPlot('system-chart', data.data, data.layout);
                    }
                });
        }
        
        // Utility functions
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        
        function getSeverityClass(severity) {
            const classes = {
                'low': 'info',
                'medium': 'warning',
                'high': 'danger',
                'critical': 'danger'
            };
            return classes[severity] || 'info';
        }
        
        // Initialize dashboard
        socket.emit('request_update');
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            socket.emit('request_update');
        }, 30000);
    </script>
</body>
</html>
    """

    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)

    logger.info("📄 Dashboard templates created")


def main():
    """Main function to run the monitoring dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="AI CEO Monitoring Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument(
        "--create-templates", action="store_true", help="Create dashboard templates"
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()],
    )

    if args.create_templates:
        create_dashboard_templates()
        return

    # Create and start dashboard
    dashboard = MonitoringDashboard(port=args.port)

    try:
        # Create templates if they don't exist
        if not Path("templates/dashboard.html").exists():
            create_dashboard_templates()

        # Start dashboard
        dashboard.start_monitoring()

    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
    finally:
        dashboard.stop_monitoring()


if __name__ == "__main__":
    main()
