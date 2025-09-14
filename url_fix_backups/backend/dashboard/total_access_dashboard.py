#!/usr / bin / env python3
"""
TRAE.AI Total Access Dashboard - Explainable AI Telemetry & System Transparency

A comprehensive, real - time dashboard providing complete visibility into the
autonomous TRAE.AI system. Designed with explainability and transparency
as core principles, allowing users to understand and trust AI decisions.

Key Features:
- Real - time system health monitoring
- Agent performance analytics
- Task queue visualization
- Decision tree explanations
- Performance metrics and KPIs
- Autonomous system controls
- Alert and notification system
- Historical trend analysis
"""

import json
import logging
import os
import socket
import sqlite3
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import plotly.graph_objs as go
import plotly.utils
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from backend.core.secret_store import SecretStore

# Import TRAE.AI components

from backend.core.task_queue import TaskMetrics, TaskQueue


@dataclass
class SystemHealth:
    """System health status"""

    overall_status: str  # 'healthy', 'warning', 'critical'
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_status: str
    database_status: str
    agent_count: int
    active_agents: int
    last_updated: datetime


@dataclass
class AgentMetrics:
    """Agent performance metrics"""

    agent_id: str
    agent_type: str
    status: str
    tasks_completed: int
    success_rate: float
    average_execution_time: float
    current_load: int
    max_load: int
    last_heartbeat: datetime
    capabilities: List[str]
    recent_decisions: List[Dict[str, Any]]


@dataclass
class DecisionExplanation:
    """AI decision explanation"""

    decision_id: str
    agent_type: str
    decision_type: str
    input_data: Dict[str, Any]
    reasoning_steps: List[str]
    confidence_score: float
    alternative_options: List[Dict[str, Any]]
    outcome: str
    timestamp: datetime


class TotalAccessDashboard:
    """Main dashboard application"""

    def __init__(self, port: int = 8082, debug: bool = False):
        self.port = port
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)

        # Flask app setup
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.app.config["SECRET_KEY"] = os.environ.get(
            "TOTAL_ACCESS_SECRET_KEY", os.urandom(24).hex()
        )
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Database connection
        self.db_path = "data / right_perspective.db"

        # System components
        self.task_queue = None
        self.secret_store = None

        # Dashboard state
        self.connected_clients = set()
        self.last_metrics_update = datetime.now()
        self.metrics_cache = {}

        # Background threads
        self.metrics_thread = None
        self.running = False

        # Setup routes
        self.setup_routes()
        self.setup_websocket_handlers()

        self.logger.info("Total Access Dashboard initialized")

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            """Main dashboard page"""
            return render_template("dashboard.html")

        @self.app.route("/api / system / health")
        def get_system_health():
            """Get current system health status"""
            try:
                health = self.get_system_health()
                return jsonify(asdict(health))
            except Exception as e:
                self.logger.error(f"Error getting system health: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / agents / status")
        def get_agents_status():
            """Get status of all agents"""
            try:
                agents = self.get_agent_metrics()
                return jsonify([asdict(agent) for agent in agents])
            except Exception as e:
                self.logger.error(f"Error getting agent status: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / tasks / metrics")
        def get_task_metrics():
            """Get task queue metrics"""
            try:
                if self.task_queue:
                    metrics = self.task_queue.get_queue_metrics()
                    return jsonify(asdict(metrics))
                return jsonify({"error": "Task queue not available"}), 503
            except Exception as e:
                self.logger.error(f"Error getting task metrics: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / tasks / history")
        def get_task_history():
            """Get task execution history"""
            try:
                limit = request.args.get("limit", 100, type=int)
                history = self.get_task_history(limit)
                return jsonify(history)
            except Exception as e:
                self.logger.error(f"Error getting task history: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / decisions / explanations")
        def get_decision_explanations():
            """Get AI decision explanations"""
            try:
                limit = request.args.get("limit", 50, type=int)
                explanations = self.get_decision_explanations(limit)
                return jsonify([asdict(exp) for exp in explanations])
            except Exception as e:
                self.logger.error(f"Error getting decision explanations: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / analytics / performance")
        def get_performance_analytics():
            """Get performance analytics data"""
            try:
                days = request.args.get("days", 7, type=int)
                analytics = self.get_performance_analytics(days)
                return jsonify(analytics)
            except Exception as e:
                self.logger.error(f"Error getting performance analytics: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / system / control", methods=["POST"])
        def system_control():
            """System control endpoint"""
            try:
                action = request.json.get("action")
                if action == "pause_agent":
                    agent_id = request.json.get("agent_id")
                    result = self.pause_agent(agent_id)
                elif action == "resume_agent":
                    agent_id = request.json.get("agent_id")
                    result = self.resume_agent(agent_id)
                elif action == "cancel_task":
                    task_id = request.json.get("task_id")
                    result = self.cancel_task(task_id)
                else:
                    return jsonify({"error": "Unknown action"}), 400

                return jsonify({"success": result})
            except Exception as e:
                self.logger.error(f"Error in system control: {e}")
                return jsonify({"error": str(e)}), 500

    def setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection"""
            self.connected_clients.add(request.sid)
            self.logger.info(f"Client connected: {request.sid}")

            # Send initial data
            emit("system_health", self.get_cached_system_health())
            emit("agent_metrics", self.get_cached_agent_metrics())

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection"""
            self.connected_clients.discard(request.sid)
            self.logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on("subscribe_to_updates")
        def handle_subscribe(data):
            """Handle subscription to real - time updates"""
            update_type = data.get("type", "all")
            self.logger.info(f"Client {request.sid} subscribed to {update_type} updates")

    def start(self):
        """Start the dashboard server"""
        try:
            self.running = True

            # Initialize connections
            self.initialize_connections()

            # Start background metrics thread
            self.start_metrics_thread()

            self.logger.info(f"Starting Total Access Dashboard on port {self.port}")

            # Run the Flask - SocketIO server
            self.socketio.run(
                self.app,
                host="0.0.0.0",
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True,
            )

        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            raise

    def stop(self):
        """Stop the dashboard server"""
        self.running = False
        self.logger.info("Total Access Dashboard stopped")

    def initialize_connections(self):
        """Initialize connections to system components"""
        try:
            # Initialize task queue connection
            self.task_queue = TaskQueue(self.db_path)

            # Initialize secret store
            self.secret_store = SecretStore()

            self.logger.info("Dashboard connections initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize connections: {e}")
            raise

    def start_metrics_thread(self):
        """Start background metrics collection thread"""
        self.metrics_thread = threading.Thread(target=self.metrics_collection_loop, daemon=True)
        self.metrics_thread.start()
        self.logger.info("Metrics collection thread started")

    def metrics_collection_loop(self):
        """Background loop for collecting and broadcasting metrics"""
        while self.running:
            try:
                # Collect current metrics
                system_health = self.get_system_health()
                agent_metrics = self.get_agent_metrics()

                # Cache metrics
                self.metrics_cache = {
                    "system_health": asdict(system_health),
                    "agent_metrics": [asdict(agent) for agent in agent_metrics],
                    "last_updated": datetime.now().isoformat(),
                }

                # Broadcast to connected clients
                if self.connected_clients:
                    self.socketio.emit("system_health", asdict(system_health))
                    self.socketio.emit("agent_metrics", [asdict(agent) for agent in agent_metrics])

                # Update timestamp
                self.last_metrics_update = datetime.now()

                # Wait before next collection
                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                time.sleep(10)

    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        try:
            # Get basic system metrics

            import psutil

            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Check database status
            database_status = "healthy"
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("SELECT 1").fetchone()
            except Exception:
                database_status = "error"

            # Get agent information
            agent_count = 0
            active_agents = 0

            if self.task_queue:
                agent_status = self.task_queue.get_agent_status()
                agent_count = len(agent_status)
                active_agents = sum(
                    1 for status in agent_status.values() if status["status"] in ["active", "busy"]
                )

            # Determine overall status
            overall_status = "healthy"
            if cpu_usage > 90 or memory.percent > 90 or disk.percent > 90:
                overall_status = "warning"
            if database_status == "error" or active_agents == 0:
                overall_status = "critical"

            return SystemHealth(
                overall_status=overall_status,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_status="connected",
                database_status=database_status,
                agent_count=agent_count,
                active_agents=active_agents,
                last_updated=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return SystemHealth(
                overall_status="error",
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                network_status="unknown",
                database_status="error",
                agent_count=0,
                active_agents=0,
                last_updated=datetime.now(),
            )

    def get_agent_metrics(self) -> List[AgentMetrics]:
        """Get metrics for all agents"""
        metrics = []

        try:
            if not self.task_queue:
                return metrics

            agent_status = self.task_queue.get_agent_status()

            for worker_id, status in agent_status.items():
                # Calculate success rate
                success_rate = self.calculate_agent_success_rate(worker_id)

                # Get average execution time
                avg_execution_time = self.get_agent_avg_execution_time(worker_id)

                # Get recent decisions
                recent_decisions = self.get_agent_recent_decisions(worker_id)

                metrics.append(
                    AgentMetrics(
                        agent_id=worker_id,
                        agent_type=status["agent_type"],
                        status=status["status"],
                        tasks_completed=status["tasks_completed"],
                        success_rate=success_rate,
                        average_execution_time=avg_execution_time,
                        current_load=status["current_load"],
                        max_load=status["max_concurrent_tasks"],
                        last_heartbeat=datetime.fromisoformat(status["last_heartbeat"]),
                        capabilities=status["capabilities"],
                        recent_decisions=recent_decisions,
                    )
                )

        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}")

        return metrics

    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT task_id, task_type, agent_type, status, priority,
                        created_at, started_at, completed_at, error_message
                    FROM tasks
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error getting task history: {e}")
            return []

    def get_decision_explanations(self, limit: int = 50) -> List[DecisionExplanation]:
        """Get AI decision explanations"""
        explanations = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM decision_explanations
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                for row in cursor.fetchall():
                    explanations.append(
                        DecisionExplanation(
                            decision_id=row[0],
                            agent_type=row[1],
                            decision_type=row[2],
                            input_data=json.loads(row[3]),
                            reasoning_steps=json.loads(row[4]),
                            confidence_score=row[5],
                            alternative_options=json.loads(row[6]),
                            outcome=row[7],
                            timestamp=datetime.fromisoformat(row[8]),
                        )
                    )

        except Exception as e:
            self.logger.error(f"Error getting decision explanations: {e}")

        return explanations

    def get_performance_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance analytics for the specified number of days"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                # Task completion trends
                cursor = conn.execute(
                    """
                    SELECT DATE(completed_at) as date, COUNT(*) as completed_tasks
                    FROM tasks
                    WHERE completed_at >= ? AND status = 'completed'
                    GROUP BY DATE(completed_at)
                    ORDER BY date
                """,
                    (start_date.isoformat(),),
                )

                completion_trends = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]

                # Agent performance
                cursor = conn.execute(
                    """
                    SELECT agent_type, COUNT(*) as total_tasks,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                    FROM tasks
                    WHERE created_at >= ?
                    GROUP BY agent_type
                """,
                    (start_date.isoformat(),),
                )

                agent_performance = []
                for row in cursor.fetchall():
                    agent_type, total, completed = row
                    success_rate = (completed / total * 100) if total > 0 else 0
                    agent_performance.append(
                        {
                            "agent_type": agent_type,
                            "total_tasks": total,
                            "completed_tasks": completed,
                            "success_rate": success_rate,
                        }
                    )

                # System health trends
                cursor = conn.execute(
                    """
                    SELECT DATE(timestamp) as date,
                        AVG(CAST(details AS REAL)) as avg_cpu_usage
                    FROM system_metrics
                    WHERE timestamp >= ? AND metric_name = 'cpu_usage'
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """,
                    (start_date.isoformat(),),
                )

                health_trends = [{"date": row[0], "cpu_usage": row[1]} for row in cursor.fetchall()]

                return {
                    "completion_trends": completion_trends,
                    "agent_performance": agent_performance,
                    "health_trends": health_trends,
                    "period_days": days,
                    "generated_at": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Error getting performance analytics: {e}")
            return {"error": str(e)}

    def calculate_agent_success_rate(self, worker_id: str) -> float:
        """Calculate success rate for an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as total,
                        SUM(CASE WHEN action = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM task_execution_log
                    WHERE worker_id = ? AND timestamp >= ?
                """,
                    (worker_id, (datetime.now() - timedelta(days=7)).isoformat()),
                )

                row = cursor.fetchone()
                if row and row[0] > 0:
                    return (row[1] / row[0]) * 100

        except Exception as e:
            self.logger.error(f"Error calculating success rate for {worker_id}: {e}")

        return 0.0

    def get_agent_avg_execution_time(self, worker_id: str) -> float:
        """Get average execution time for an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT AVG(CAST(JSON_EXTRACT(details, '$.execution_time') AS REAL))
                    FROM task_execution_log
                    WHERE worker_id = ? AND action = 'completed'
                      AND timestamp >= ?
                """,
                    (worker_id, (datetime.now() - timedelta(days=7)).isoformat()),
                )

                row = cursor.fetchone()
                return row[0] if row and row[0] else 0.0

        except Exception as e:
            self.logger.error(f"Error getting avg execution time for {worker_id}: {e}")

        return 0.0

    def get_agent_recent_decisions(self, worker_id: str) -> List[Dict[str, Any]]:
        """Get recent decisions made by an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT decision_type, confidence_score, outcome, timestamp
                    FROM decision_explanations
                    WHERE agent_type = (SELECT agent_type FROM agent_workers WHERE worker_id = ?)
                    ORDER BY timestamp DESC
                    LIMIT 5
                """,
                    (worker_id,),
                )

                return [
                    {
                        "decision_type": row[0],
                        "confidence_score": row[1],
                        "outcome": row[2],
                        "timestamp": row[3],
                    }
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            self.logger.error(f"Error getting recent decisions for {worker_id}: {e}")

        return []

    def get_cached_system_health(self) -> Dict[str, Any]:
        """Get cached system health data"""
        return self.metrics_cache.get("system_health", {})

    def get_cached_agent_metrics(self) -> List[Dict[str, Any]]:
        """Get cached agent metrics data"""
        return self.metrics_cache.get("agent_metrics", [])

    def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        try:
            # Implementation would depend on agent architecture
            self.logger.info(f"Pausing agent: {agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error pausing agent {agent_id}: {e}")
            return False

    def resume_agent(self, agent_id: str) -> bool:
        """Resume an agent"""
        try:
            # Implementation would depend on agent architecture
            self.logger.info(f"Resuming agent: {agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error resuming agent {agent_id}: {e}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        try:
            if self.task_queue:
                return self.task_queue.cancel_task(task_id)
            return False
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {e}")
            return False


def create_dashboard_templates():
    """Create dashboard HTML templates"""
    templates_dir = Path("backend / dashboard / templates")
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Main dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > TRAE.AI Total Access Dashboard</title>
    <script src="https://cdn.socket.io / 4.0.0 / socket.io.min.js"></script>
    <script src="https://cdn.plot.ly / plotly - latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net / npm / tailwindcss@2.2.19 / dist / tailwind.min.css" rel="stylesheet">
    <style>
        .status - healthy { @apply bg - green - 100 text - green - 800; }
        .status - warning { @apply bg - yellow - 100 text - yellow - 800; }
        .status - critical { @apply bg - red - 100 text - red - 800; }
        .agent - card { @apply bg - white rounded - lg shadow - md p - 6 mb - 4; }
        .metric - card { @apply bg - white rounded - lg shadow - md p - 4; }
    </style>
</head>
<body class="bg - gray - 100">
    <div class="container mx - auto px - 4 py - 8">
        <header class="mb - 8">
            <h1 class="text - 4xl font - bold text - gray - 800 mb - 2">TRAE.AI Total Access Dashboard</h1>
            <p class="text - gray - 600">Real - time system monitoring \
    and explainable AI telemetry</p>
        </header>

        <!-- System Health Overview -->
        <div class="grid grid - cols - 1 md:grid - cols - 4 gap - 6 mb - 8">
            <div class="metric - card">
                <h3 class="text - lg font - semibold mb - 2">System Status</h3>
                <div id="system - status" class="px - 3 py - 1 rounded - full text - sm font - medium">Loading...</div>
            </div>
            <div class="metric - card">
                <h3 class="text - lg font - semibold mb - 2">CPU Usage</h3>
                <div id="cpu - usage" class="text - 2xl font - bold text - blue - 600">--%</div>
            </div>
            <div class="metric - card">
                <h3 class="text - lg font - semibold mb - 2">Memory Usage</h3>
                <div id="memory - usage" class="text - 2xl font - bold text - green - 600">--%</div>
            </div>
            <div class="metric - card">
                <h3 class="text - lg font - semibold mb - 2">Active Agents</h3>
                <div id="active - agents" class="text - 2xl font - bold text - purple - 600">--</div>
            </div>
        </div>

        <!-- Agent Status Grid -->
        <div class="mb - 8">
            <h2 class="text - 2xl font - bold text - gray - 800 mb - 4">Agent Status</h2>
            <div id="agents - grid" class="grid grid - cols - 1 md:grid - cols - 2 lg:grid - cols - 3 gap - 6">
                <!-- Agent cards will be populated here -->
            </div>
        </div>

        <!-- Task Queue Metrics -->
        <div class="mb - 8">
            <h2 class="text - 2xl font - bold text - gray - 800 mb - 4">Task Queue Metrics</h2>
            <div class="grid grid - cols - 1 md:grid - cols - 4 gap - 6">
                <div class="metric - card">
                    <h3 class="text - lg font - semibold mb - 2">Pending Tasks</h3>
                    <div id="pending - tasks" class="text - 2xl font - bold text - orange - 600">--</div>
                </div>
                <div class="metric - card">
                    <h3 class="text - lg font - semibold mb - 2">Running Tasks</h3>
                    <div id="running - tasks" class="text - 2xl font - bold text - blue - 600">--</div>
                </div>
                <div class="metric - card">
                    <h3 class="text - lg font - semibold mb - 2">Completed Tasks</h3>
                    <div id="completed - tasks" class="text - 2xl font - bold text - green - 600">--</div>
                </div>
                <div class="metric - card">
                    <h3 class="text - lg font - semibold mb - 2">Success Rate</h3>
                    <div id="success - rate" class="text - 2xl font - bold text - purple - 600">--%</div>
                </div>
            </div>
        </div>

        <!-- Performance Charts -->
        <div class="mb - 8">
            <h2 class="text - 2xl font - bold text - gray - 800 mb - 4">Performance Analytics</h2>
            <div class="grid grid - cols - 1 lg:grid - cols - 2 gap - 6">
                <div class="bg - white rounded - lg shadow - md p - 6">
                    <h3 class="text - lg font - semibold mb - 4">Task Completion Trends</h3>
                    <div id="completion - chart" style="height: 300px;"></div>
                </div>
                <div class="bg - white rounded - lg shadow - md p - 6">
                    <h3 class="text - lg font - semibold mb - 4">Agent Performance</h3>
                    <div id="performance - chart" style="height: 300px;"></div>
                </div>
            </div>
        </div>

        <!-- Recent Decisions -->
        <div class="mb - 8">
            <h2 class="text - 2xl font - bold text - gray - 800 mb - 4">Recent AI Decisions</h2>
            <div class="bg - white rounded - lg shadow - md">
                <div id="decisions - list" class="p - 6">
                    <!-- Decision explanations will be populated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();

        // Handle system health updates
        socket.on('system_health', function(data) {
            updateSystemHealth(data);
        });

        // Handle agent metrics updates
        socket.on('agent_metrics', function(data) {
            updateAgentMetrics(data);
        });

        function updateSystemHealth(health) {
            const statusElement = document.getElementById('system - status');
            statusElement.textContent = health.overall_status.toUpperCase();
            statusElement.className = `px - 3 py - 1 rounded - full text - sm font - medium status-${health.overall_status}`;

            document.getElementById('cpu - usage').textContent = `${health.cpu_usage.toFixed(1)}%`;
            document.getElementById('memory - usage').textContent = `${health.memory_usage.toFixed(1)}%`;
            document.getElementById('active - agents').textContent = health.active_agents;
        }

        function updateAgentMetrics(agents) {
            const grid = document.getElementById('agents - grid');
            grid.innerHTML = '';

            agents.forEach(agent => {
                const card = document.createElement('div');
                card.className = 'agent - card';
                card.innerHTML = `
                    <h3 class="text - lg font - semibold mb - 2">${agent.agent_type}</h3>
                    <div class="mb - 2">
                        <span class="px - 2 py - 1 rounded text - sm font - medium status-${agent.status === 'active' ? 'healthy' : 'warning'}">
                            ${agent.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="text - sm text - gray - 600">
                        <p > Tasks Completed: ${agent.tasks_completed}</p>
                        <p > Success Rate: ${agent.success_rate.toFixed(1)}%</p>
                        <p > Load: ${agent.current_load}/${agent.max_load}</p>
                        <p > Avg Execution: ${agent.average_execution_time.toFixed(2)}s</p>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // Load initial data
        fetch('/api / system / health')
            .then(response => response.json())
            .then(data => updateSystemHealth(data));

        fetch('/api / agents / status')
            .then(response => response.json())
            .then(data => updateAgentMetrics(data));

        // Load task metrics
        fetch('/api / tasks / metrics')
            .then(response => response.json())
            .then(data => {
                document.getElementById('pending - tasks').textContent = data.pending_tasks;
                document.getElementById('running - tasks').textContent = data.running_tasks;
                document.getElementById('completed - tasks').textContent = data.completed_tasks;
                document.getElementById('success - rate').textContent = `${data.success_rate.toFixed(1)}%`;
            });

        // Load performance analytics
        fetch('/api / analytics / performance')
            .then(response => response.json())
            .then(data => {
                // Create completion trends chart
                const completionData = [{
                    x: data.completion_trends.map(d => d.date),
                        y: data.completion_trends.map(d => d.count),
                        type: 'scatter',
                        mode: 'lines + markers',
                        name: 'Completed Tasks'
                }];

                Plotly.newPlot('completion - chart', completionData, {
                    title: 'Daily Task Completions',
                        xaxis: { title: 'Date' },
                        yaxis: { title: 'Tasks Completed' }
                });

                // Create agent performance chart
                const performanceData = [{
                    x: data.agent_performance.map(d => d.agent_type),
                        y: data.agent_performance.map(d => d.success_rate),
                        type: 'bar',
                        name: 'Success Rate %'
                }];

                Plotly.newPlot('performance - chart', performanceData, {
                    title: 'Agent Success Rates',
                        xaxis: { title: 'Agent Type' },
                        yaxis: { title: 'Success Rate (%)' }
                });
            });

        // Load recent decisions
        fetch('/api / decisions / explanations')
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById('decisions - list');
                list.innerHTML = '';

                data.slice(0, 10).forEach(decision => {
                    const item = document.createElement('div');
                    item.className = 'border - b border - gray - 200 py - 4';
                    item.innerHTML = `
                        <div class="flex justify - between items - start mb - 2">
                            <h4 class="font - semibold">${decision.decision_type}</h4>
                            <span class="text - sm text - gray - 500">${new Date(decision.timestamp).toLocaleString()}</span>
                        </div>
                        <p class="text - sm text - gray - 600 mb - 2">Agent: ${decision.agent_type}</p>
                        <p class="text - sm mb - 2">Confidence: ${(decision.confidence_score * 100).toFixed(1)}%</p>
                        <p class="text - sm text - gray - 700">Outcome: ${decision.outcome}</p>
                    `;
                    list.appendChild(item);
                });
            });
    </script>
</body>
</html>
    """

    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)


if __name__ == "__main__":
    # Create dashboard templates
    create_dashboard_templates()

    # Automatic port detection
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8082"))

    def first_free(start, max_tries=50):
        p = start
        for _ in range(max_tries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind((host, p))
                    return p
                except OSError:
                    p += 1
        raise RuntimeError("No free port found")

    port = first_free(port)
    print(f"Total Access Dashboard starting on http://{host}:{port}")

    # Start the dashboard with detected port
    dashboard = TotalAccessDashboard(port=port, debug=True)
    dashboard.start()
