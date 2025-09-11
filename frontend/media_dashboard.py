#!/usr / bin / env python3
"""
Media Dashboard - Real - time Media Processing Control Center

This module provides a comprehensive web - based dashboard for monitoring and controlling
all media processing operations, including real - time status updates, progress tracking,
and interactive workflow management.

Features:
- Real - time processing status monitoring
- Interactive workflow designer
- Batch operation management
- Performance analytics and metrics
- Live preview capabilities
- Resource usage monitoring
- Error tracking and debugging
- Export and sharing capabilities

Author: TRAE.AI Media System
Version: 2.0.0
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import plotly.graph_objs as go
import plotly.utils
# Web framework imports
from flask import Flask, jsonify, render_template, request, send_file, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class DashboardMetrics:
    """Dashboard performance metrics."""

    total_jobs: int = 0
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    queue_length: int = 0
    avg_processing_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0
    uptime: float = 0.0
    last_updated: datetime = None

@dataclass


class JobStatus:
    """Individual job status information."""

    job_id: str
    job_type: str
    status: str
    progress: float
    start_time: datetime
    estimated_completion: Optional[datetime]
    input_files: List[str]
    output_files: List[str]
    error_message: Optional[str]
    metadata: Dict[str, Any]


class MediaDashboard:
    """Comprehensive media processing dashboard."""


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.app.config["SECRET_KEY"] = self.config.get(
            "secret_key", "media - dashboard - secret"
        )

        # Initialize extensions
        self.socketio = SocketIO(
            self.app, cors_allowed_origins="*", async_mode="threading"
        )
        CORS(self.app)

        # Dashboard state
        self.metrics = DashboardMetrics()
        self.active_jobs: Dict[str, JobStatus] = {}
        self.job_history: deque = deque(maxlen = 1000)
        self.connected_clients: Set[str] = set()
        self.workflow_templates: Dict[str, Any] = {}

        # Performance monitoring
        self.performance_history: deque = deque(maxlen = 100)
        self.start_time = datetime.now()

        # Initialize routes and socket handlers
        self._setup_routes()
        self._setup_socket_handlers()

        # Start background monitoring
        self._start_monitoring_thread()

        logger.info("Media Dashboard initialized")


    def _load_default_config(self) -> Dict[str, Any]:
        """Load default dashboard configuration."""
        return {
            "host": "0.0.0.0",
                "port": 8080,
                "debug": True,
                "secret_key": "media - dashboard - secret - key",
                "upload_folder": "./uploads",
                "max_file_size": 100 * 1024 * 1024,  # 100MB
            "allowed_extensions": {
                ".mp4",
                    ".avi",
                    ".mov",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".wav",
                    ".mp3",
                    },
                "monitoring_interval": 5,  # seconds
            "auto_cleanup_hours": 24,
                "enable_analytics": True,
                "theme": "dark",
                }


    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")


        def dashboard_home():
            """Main dashboard page."""
            return render_template(
                "dashboard.html", config = self.config, metrics = asdict(self.metrics)
            )

        @self.app.route("/api / status")


        def get_status():
            """Get current dashboard status."""
            return jsonify(
                {
                    "success": True,
                        "metrics": asdict(self.metrics),
                        "active_jobs": {
                        job_id: asdict(job) for job_id, job in self.active_jobs.items()
                    },
                        "uptime": (datetime.now() - self.start_time).total_seconds(),
                        }
            )

        @self.app.route("/api / jobs")


        def get_jobs():
            """Get all jobs with filtering."""
            status_filter = request.args.get("status")
            job_type_filter = request.args.get("type")
            limit = int(request.args.get("limit", 50))

            jobs = list(self.job_history)

            # Apply filters
            if status_filter:
                jobs = [job for job in jobs if job.get("status") == status_filter]
            if job_type_filter:
                jobs = [job for job in jobs if job.get("job_type") == job_type_filter]

            # Limit results
            jobs = jobs[-limit:]

            return jsonify({"success": True, "jobs": jobs, "total": len(jobs)})

        @self.app.route("/api / jobs/<job_id>")


        def get_job_details(job_id):
            """Get detailed information about a specific job."""
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return jsonify({"success": True, "job": asdict(job)})

            # Search in history
            for job in self.job_history:
                if job.get("job_id") == job_id:
                    return jsonify({"success": True, "job": job})

            return jsonify({"success": False, "error": "Job not found"}), 404

        @self.app.route("/api / jobs/<job_id>/cancel", methods=["POST"])


        def cancel_job(job_id):
            """Cancel a running job."""
            try:
                # Import workflow engine
                from backend.media.workflow_engine import get_workflow_engine

                engine = get_workflow_engine()
                success = await engine.cancel_execution(job_id)

                if success:
                    return jsonify(
                        {
                            "success": True,
                                "message": f"Job {job_id} cancelled successfully",
                                }
                    )
                else:
                    return (
                        jsonify(
                            {
                                "success": False,
                                    "error": "Job not found or cannot be cancelled",
                                    }
                        ),
                            400,
                            )

            except Exception as e:
                logger.error(f"Error cancelling job {job_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / workflows")


        def get_workflows():
            """Get available workflow templates."""
            try:
                from backend.media.workflow_engine import get_workflow_engine

                engine = get_workflow_engine()
                workflows = engine.get_available_workflows()

                return jsonify({"success": True, "workflows": workflows})

            except Exception as e:
                logger.error(f"Error getting workflows: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / workflows/<workflow_id>/execute", methods=["POST"])


        def execute_workflow(workflow_id):
            """Execute a workflow with provided input data."""
            try:
                input_data = request.get_json()

                from backend.media.workflow_engine import get_workflow_engine

                engine = get_workflow_engine()

                # Create and execute workflow
                execution_id = asyncio.run(
                    engine.create_workflow_execution(workflow_id, input_data)
                )

                # Start execution in background


                def run_workflow():
                    asyncio.run(engine.execute_workflow(execution_id))

                threading.Thread(target = run_workflow, daemon = True).start()

                return jsonify(
                    {
                        "success": True,
                            "execution_id": execution_id,
                            "message": "Workflow execution started",
                            }
                )

            except Exception as e:
                logger.error(f"Error executing workflow {workflow_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / upload", methods=["POST"])


        def upload_file():
            """Handle file uploads."""
            try:
                if "file" not in request.files:
                    return jsonify({"success": False, "error": "No file provided"}), 400

                file = request.files["file"]
                if file.filename == "":
                    return jsonify({"success": False, "error": "No file selected"}), 400

                # Validate file extension
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in self.config["allowed_extensions"]:
                    return (
                        jsonify(
                            {
                                "success": False,
                                    "error": f"File type {file_ext} not allowed",
                                    }
                        ),
                            400,
                            )

                # Save file
                filename = secure_filename(file.filename)
                upload_path = Path(self.config["upload_folder"]) / filename
                upload_path.parent.mkdir(parents = True, exist_ok = True)

                file.save(str(upload_path))

                return jsonify(
                    {
                        "success": True,
                            "filename": filename,
                            "path": str(upload_path),
                            "size": upload_path.stat().st_size,
                            }
                )

            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / analytics")


        def get_analytics():
            """Get performance analytics data."""
            try:
                # Generate analytics charts
                charts = self._generate_analytics_charts()

                return jsonify(
                    {
                        "success": True,
                            "charts": charts,
                            "summary": {
                            "total_jobs_today": self._count_jobs_today(),
                                "avg_processing_time": self.metrics.avg_processing_time,
                                "success_rate": self._calculate_success_rate(),
                                "peak_usage_time": self._get_peak_usage_time(),
                                },
                            }
                )

            except Exception as e:
                logger.error(f"Error generating analytics: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / system / health")


        def system_health():
            """Get system health information."""
            try:
                import psutil

                health_data = {
                    "cpu_percent": psutil.cpu_percent(interval = 1),
                        "memory_percent": psutil.virtual_memory().percent,
                        "disk_percent": psutil.disk_usage("/").percent,
                        "network_io": dict(psutil.net_io_counters()._asdict()),
                        "process_count": len(psutil.pids()),
                        "uptime": (datetime.now() - self.start_time).total_seconds(),
                        "load_average": (
                        os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
                    ),
                        }

                return jsonify(
                    {
                        "success": True,
                            "health": health_data,
                            "status": (
                            "healthy" if health_data["cpu_percent"] < 80 else "warning"
                        ),
                            }
                )

            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return jsonify({"success": False, "error": str(e)}), 500


    def _setup_socket_handlers(self):
        """Setup WebSocket event handlers."""

        @self.socketio.on("connect")


        def handle_connect():
            """Handle client connection."""
            client_id = request.sid
            self.connected_clients.add(client_id)

            # Send initial data
            emit(
                "dashboard_update",
                    {
                    "metrics": asdict(self.metrics),
                        "active_jobs": {
                        job_id: asdict(job) for job_id, job in self.active_jobs.items()
                    },
                        },
                    )

            logger.info(f"Client {client_id} connected")

        @self.socketio.on("disconnect")


        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid
            self.connected_clients.discard(client_id)
            logger.info(f"Client {client_id} disconnected")

        @self.socketio.on("subscribe_job")


        def handle_subscribe_job(data):
            """Subscribe to job updates."""
            job_id = data.get("job_id")
            if job_id:
                join_room(f"job_{job_id}")
                emit("subscribed", {"job_id": job_id})

        @self.socketio.on("unsubscribe_job")


        def handle_unsubscribe_job(data):
            """Unsubscribe from job updates."""
            job_id = data.get("job_id")
            if job_id:
                leave_room(f"job_{job_id}")
                emit("unsubscribed", {"job_id": job_id})

        @self.socketio.on("request_preview")


        def handle_preview_request(data):
            """Handle preview generation request."""
            try:
                job_id = data.get("job_id")
                preview_type = data.get("type", "thumbnail")

                # Generate preview (implementation depends on media type)
                preview_data = self._generate_preview(job_id, preview_type)

                emit(
                    "preview_ready",
                        {
                        "job_id": job_id,
                            "preview_type": preview_type,
                            "preview_data": preview_data,
                            },
                        )

            except Exception as e:
                emit("preview_error", {"job_id": job_id, "error": str(e)})


    def _start_monitoring_thread(self):
        """Start background monitoring thread."""


        def monitor_loop():
            while True:
                try:
                    self._update_metrics()
                    self._broadcast_updates()
                    time.sleep(self.config["monitoring_interval"])
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(5)

        monitoring_thread = threading.Thread(target = monitor_loop, daemon = True)
        monitoring_thread.start()
        logger.info("Monitoring thread started")


    def _update_metrics(self):
        """Update dashboard metrics."""
        try:
            import psutil

            # Update system metrics
            self.metrics.cpu_usage = psutil.cpu_percent(interval = None)
            self.metrics.memory_usage = psutil.virtual_memory().percent
            self.metrics.disk_usage = psutil.disk_usage("/").percent

            # Update job metrics
            self.metrics.active_jobs = len(self.active_jobs)
            self.metrics.total_jobs = len(self.job_history) + self.metrics.active_jobs

            # Calculate averages
            if self.job_history:
                processing_times = [
                    job.get("processing_time", 0)
                    for job in self.job_history
                    if job.get("processing_time")
                ]
                if processing_times:
                    self.metrics.avg_processing_time = sum(processing_times) / len(
                        processing_times
                    )

            self.metrics.uptime = (datetime.now() - self.start_time).total_seconds()
            self.metrics.last_updated = datetime.now()

            # Store performance history
            self.performance_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                        "cpu_usage": self.metrics.cpu_usage,
                        "memory_usage": self.metrics.memory_usage,
                        "active_jobs": self.metrics.active_jobs,
                        }
            )

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")


    def _broadcast_updates(self):
        """Broadcast updates to connected clients."""
        if self.connected_clients:
            update_data = {
                "metrics": asdict(self.metrics),
                    "active_jobs": {
                    job_id: asdict(job) for job_id, job in self.active_jobs.items()
                },
                    "timestamp": datetime.now().isoformat(),
                    }

            self.socketio.emit("dashboard_update", update_data)


    def _generate_analytics_charts(self) -> Dict[str, Any]:
        """Generate analytics charts data."""
        charts = {}

        # Performance over time chart
        if self.performance_history:
            timestamps = [entry["timestamp"] for entry in self.performance_history]
            cpu_data = [entry["cpu_usage"] for entry in self.performance_history]
            memory_data = [entry["memory_usage"] for entry in self.performance_history]

            performance_chart = {
                "data": [
                    {
                        "x": timestamps,
                            "y": cpu_data,
                            "type": "scatter",
                            "mode": "lines",
                            "name": "CPU Usage %",
                            "line": {"color": "#ff6b6b"},
                            },
                        {
                        "x": timestamps,
                            "y": memory_data,
                            "type": "scatter",
                            "mode": "lines",
                            "name": "Memory Usage %",
                            "line": {"color": "#4ecdc4"},
                            },
                        ],
                    "layout": {
                    "title": "System Performance Over Time",
                        "xaxis": {"title": "Time"},
                        "yaxis": {"title": "Usage %"},
                        "template": (
                        "plotly_dark"
                        if self.config["theme"] == "dark"
                        else "plotly_white"
                    ),
                        },
                    }
            charts["performance"] = performance_chart

        # Job status distribution
        if self.job_history:
            status_counts = defaultdict(int)
            for job in self.job_history:
                status_counts[job.get("status", "unknown")] += 1

            status_chart = {
                "data": [
                    {
                        "labels": list(status_counts.keys()),
                            "values": list(status_counts.values()),
                            "type": "pie",
                            "marker": {
                            "colors": [
                                "#ff6b6b",
                                    "#4ecdc4",
                                    "#45b7d1",
                                    "#96ceb4",
                                    "#feca57",
                                    ]
                        },
                            }
                ],
                    "layout": {
                    "title": "Job Status Distribution",
                        "template": (
                        "plotly_dark"
                        if self.config["theme"] == "dark"
                        else "plotly_white"
                    ),
                        },
                    }
            charts["job_status"] = status_chart

        return charts


    def _count_jobs_today(self) -> int:
        """Count jobs processed today."""
        today = datetime.now().date()
        count = 0

        for job in self.job_history:
            job_date = datetime.fromisoformat(job.get("start_time", "")).date()
            if job_date == today:
                count += 1

        return count


    def _calculate_success_rate(self) -> float:
        """Calculate job success rate."""
        if not self.job_history:
            return 0.0

        successful_jobs = sum(
            1 for job in self.job_history if job.get("status") == "completed"
        )
        return (successful_jobs / len(self.job_history)) * 100


    def _get_peak_usage_time(self) -> str:
        """Get peak usage time of day."""
        if not self.performance_history:
            return "N / A"

        # Find hour with highest average CPU usage
        hourly_usage = defaultdict(list)

        for entry in self.performance_history:
            hour = datetime.fromisoformat(entry["timestamp"]).hour
            hourly_usage[hour].append(entry["cpu_usage"])

        if not hourly_usage:
            return "N / A"

        peak_hour = max(
            hourly_usage.keys(),
                key = lambda h: sum(hourly_usage[h]) / len(hourly_usage[h]),
                )

        return f"{peak_hour:02d}:00"


    def _generate_preview(self, job_id: str, preview_type: str) -> Dict[str, Any]:
        """Generate preview for a job."""
        # This would integrate with the actual media processing to generate previews
        # For now, return placeholder data
        return {
            "type": preview_type,
                "url": f"/api / preview/{job_id}/{preview_type}",
                "generated_at": datetime.now().isoformat(),
                }


    def update_job_status(
        self,
            job_id: str,
            status: str,
            progress: float = None,
            metadata: Dict[str, Any] = None,
            ):
        """Update job status and broadcast to clients."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = status

            if progress is not None:
                job.progress = progress

            if metadata:
                job.metadata.update(metadata)

            # Broadcast job update
            self.socketio.emit(
                "job_update",
                    {
                    "job_id": job_id,
                        "status": status,
                        "progress": progress,
                        "metadata": metadata,
                        },
                    room = f"job_{job_id}",
                    )

            # Move to history if completed or failed
            if status in ["completed", "failed", "cancelled"]:
                job.end_time = datetime.now()
                self.job_history.append(asdict(job))
                del self.active_jobs[job_id]


    def add_job(
        self,
            job_id: str,
            job_type: str,
            input_files: List[str],
            metadata: Dict[str, Any] = None,
            ) -> JobStatus:
        """Add a new job to tracking."""
        job = JobStatus(
            job_id = job_id,
                job_type = job_type,
                status="pending",
                progress = 0.0,
                start_time = datetime.now(),
                estimated_completion = None,
                input_files = input_files,
                output_files=[],
                error_message = None,
                metadata = metadata or {},
                )

        self.active_jobs[job_id] = job

        # Broadcast new job
        self.socketio.emit("new_job", asdict(job))

        return job


    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Run the dashboard server."""
        host = host or self.config["host"]
        port = port or self.config["port"]
        debug = debug if debug is not None else self.config["debug"]

        logger.info(f"Starting Media Dashboard on {host}:{port}")

        self.socketio.run(
            self.app, host = host, port = port, debug = debug, allow_unsafe_werkzeug = True
        )

# Global dashboard instance
_dashboard_instance = None


def get_media_dashboard(config: Optional[Dict[str, Any]] = None) -> MediaDashboard:
    """Get or create the global media dashboard instance."""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = MediaDashboard(config)
    return _dashboard_instance

# Dashboard HTML Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > Media Processing Dashboard</title>
    <script src="https://cdn.socket.io / 4.0.0 / socket.io.min.js"></script>
    <script src="https://cdn.plot.ly / plotly - latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com / ajax / libs / font - awesome / 6.0.0 / css / all.min.css" rel="stylesheet">
    <style>
        .dashboard - card {
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            border - radius: 12px;
            padding: 1.5rem;
            color: white;
            box - shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .metric - card {
            background: rgba(255,255,255,0.1);
            backdrop - filter: blur(10px);
            border - radius: 8px;
            padding: 1rem;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .job - card {
            background: white;
            border - radius: 8px;
            padding: 1rem;
            box - shadow: 0 2px 8px rgba(0,0,0,0.1);
            border - left: 4px solid #4ecdc4;
        }
        .progress - bar {
            background: linear - gradient(90deg, #4ecdc4, #44a08d);
            height: 6px;
            border - radius: 3px;
            transition: width 0.3s ease;
        }
        .status - badge {
            padding: 0.25rem 0.75rem;
            border - radius: 12px;
            font - size: 0.75rem;
            font - weight: 600;
        }
        .status - running { background: #fef3c7; color: #92400e; }
        .status - completed { background: #d1fae5; color: #065f46; }
        .status - failed { background: #fee2e2; color: #991b1b; }
        .status - pending { background: #e0e7ff; color: #3730a3; }
    </style>
</head>
<body class="bg - gray - 100 min - h-screen">
    <!-- Header -->
    <header class="bg - white shadow - sm border - b">
        <div class="max - w-7xl mx - auto px - 4 sm:px - 6 lg:px - 8">
            <div class="flex justify - between items - center py - 4">
                <div class="flex items - center">
                    <i class="fas fa - video text - 2xl text - blue - 600 mr - 3"></i>
                    <h1 class="text - 2xl font - bold text - gray - 900">Media Processing Dashboard</h1>
                </div>
                <div class="flex items - center space - x-4">
                    <div class="flex items - center text - sm text - gray - 500">
                        <div class="w - 2 h - 2 bg - green - 500 rounded - full mr - 2 animate - pulse"></div>
                        <span id="connection - status">Connected</span>
                    </div>
                    <button id="refresh - btn" class="bg - blue - 600 text - white px - 4 py - 2 rounded - lg hover:bg - blue - 700 transition - colors">
                        <i class="fas fa - sync - alt mr - 2"></i > Refresh
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max - w-7xl mx - auto px - 4 sm:px - 6 lg:px - 8 py - 8">
        <!-- Metrics Overview -->
        <div class="grid grid - cols - 1 md:grid - cols - 2 lg:grid - cols - 4 gap - 6 mb - 8">
            <div class="dashboard - card">
                <div class="flex items - center justify - between">
                    <div>
                        <p class="text - sm opacity - 80">Active Jobs</p>
                        <p class="text - 3xl font - bold" id="active - jobs">0</p>
                    </div>
                    <i class="fas fa - play - circle text - 3xl opacity - 60"></i>
                </div>
            </div>

            <div class="dashboard - card">
                <div class="flex items - center justify - between">
                    <div>
                        <p class="text - sm opacity - 80">Completed Today</p>
                        <p class="text - 3xl font - bold" id="completed - jobs">0</p>
                    </div>
                    <i class="fas fa - check - circle text - 3xl opacity - 60"></i>
                </div>
            </div>

            <div class="dashboard - card">
                <div class="flex items - center justify - between">
                    <div>
                        <p class="text - sm opacity - 80">CPU Usage</p>
                        <p class="text - 3xl font - bold" id="cpu - usage">0%</p>
                    </div>
                    <i class="fas fa - microchip text - 3xl opacity - 60"></i>
                </div>
            </div>

            <div class="dashboard - card">
                <div class="flex items - center justify - between">
                    <div>
                        <p class="text - sm opacity - 80">Memory Usage</p>
                        <p class="text - 3xl font - bold" id="memory - usage">0%</p>
                    </div>
                    <i class="fas fa - memory text - 3xl opacity - 60"></i>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid - cols - 1 lg:grid - cols - 2 gap - 6 mb - 8">
            <div class="bg - white rounded - lg shadow p - 6">
                <h3 class="text - lg font - semibold mb - 4">System Performance</h3>
                <div id="performance - chart" style="height: 300px;"></div>
            </div>

            <div class="bg - white rounded - lg shadow p - 6">
                <h3 class="text - lg font - semibold mb - 4">Job Status Distribution</h3>
                <div id="status - chart" style="height: 300px;"></div>
            </div>
        </div>

        <!-- Active Jobs -->
        <div class="bg - white rounded - lg shadow">
            <div class="px - 6 py - 4 border - b border - gray - 200">
                <h3 class="text - lg font - semibold">Active Jobs</h3>
            </div>
            <div class="p - 6">
                <div id="active - jobs - list" class="space - y-4">
                    <div class="text - center text - gray - 500 py - 8">
                        <i class="fas fa - tasks text - 4xl mb - 4"></i>
                        <p > No active jobs</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Job History -->
        <div class="bg - white rounded - lg shadow mt - 6">
            <div class="px - 6 py - 4 border - b border - gray - 200">
                <h3 class="text - lg font - semibold">Recent Jobs</h3>
            </div>
            <div class="p - 6">
                <div id="job - history - list" class="space - y-4">
                    <!-- Job history will be populated here -->
                </div>
            </div>
        </div>
    </main>

    <script>
        // Initialize Socket.IO connection
        const socket = io();

        // Dashboard state
        let dashboardData = {
            metrics: {},
                activeJobs: {},
                jobHistory: []
        };

        // Socket event handlers
        socket.on('connect', function() {
            document.getElementById('connection - status').textContent = 'Connected';
            console.log('Connected to dashboard');
        });

        socket.on('disconnect', function() {
            document.getElementById('connection - status').textContent = 'Disconnected';
            console.log('Disconnected from dashboard');
        });

        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
        });

        socket.on('job_update', function(data) {
            updateJobStatus(data);
        });

        socket.on('new_job', function(job) {
            addNewJob(job);
        });

        // Update dashboard with new data
        function updateDashboard(data) {
            dashboardData = data;

            // Update metrics
            document.getElementById('active - jobs').textContent = data.metrics.active_jobs || 0;
            document.getElementById('completed - jobs').textContent = data.metrics.completed_jobs || 0;
            document.getElementById('cpu - usage').textContent = (data.metrics.cpu_usage || 0).toFixed(1) + '%';
            document.getElementById('memory - usage').textContent = (data.metrics.memory_usage || 0).toFixed(1) + '%';

            // Update active jobs list
            updateActiveJobsList(data.active_jobs);

            // Update charts
            updateCharts();
        }

        // Update active jobs list
        function updateActiveJobsList(activeJobs) {
            const container = document.getElementById('active - jobs - list');

            if (Object.keys(activeJobs).length === 0) {
                container.innerHTML = `
                    <div class="text - center text - gray - 500 py - 8">
                        <i class="fas fa - tasks text - 4xl mb - 4"></i>
                        <p > No active jobs</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = Object.values(activeJobs).map(job => `
                <div class="job - card">
                    <div class="flex items - center justify - between mb - 3">
                        <div>
                            <h4 class="font - semibold text - gray - 900">${job.job_type}</h4>
                            <p class="text - sm text - gray - 600">${job.job_id}</p>
                        </div>
                        <span class="status - badge status-${job.status}">${job.status}</span>
                    </div>

                    <div class="mb - 3">
                        <div class="flex justify - between text - sm text - gray - 600 mb - 1">
                            <span > Progress</span>
                            <span>${job.progress.toFixed(1)}%</span>
                        </div>
                        <div class="w - full bg - gray - 200 rounded - full h - 2">
                            <div class="progress - bar" style="width: ${job.progress}%"></div>
                        </div>
                    </div>

                    <div class="flex justify - between items - center text - sm text - gray - 600">
                        <span > Started: ${new Date(job.start_time).toLocaleTimeString()}</span>
                        <button onclick="cancelJob('${job.job_id}')" class="text - red - 600 hover:text - red - 800">
                            <i class="fas fa - times"></i> Cancel
                        </button>
                    </div>
                </div>
            `).join('');
        }

        // Update job status
        function updateJobStatus(data) {
            if (dashboardData.activeJobs[data.job_id]) {
                dashboardData.activeJobs[data.job_id].status = data.status;
                dashboardData.activeJobs[data.job_id].progress = data.progress || 0;
                updateActiveJobsList(dashboardData.activeJobs);
            }
        }

        // Add new job
        function addNewJob(job) {
            dashboardData.activeJobs[job.job_id] = job;
            updateActiveJobsList(dashboardData.activeJobs);
        }

        // Cancel job
        function cancelJob(jobId) {
            if (confirm('Are you sure you want to cancel this job?')) {
                fetch(`/api / jobs/${jobId}/cancel`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Job cancelled successfully');
                    } else {
                        alert('Failed to cancel job: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error cancelling job:', error);
                    alert('Error cancelling job');
                });
            }
        }

        // Update charts
        function updateCharts() {
            // Fetch analytics data
            fetch('/api / analytics')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.charts) {
                        if (data.charts.performance) {
                            Plotly.newPlot('performance - chart',
                                data.charts.performance.data,
                                    data.charts.performance.layout,
                                    {responsive: true}
                            );
                        }

                        if (data.charts.job_status) {
                            Plotly.newPlot('status - chart',
                                data.charts.job_status.data,
                                    data.charts.job_status.layout,
                                    {responsive: true}
                            );
                        }
                    }
                })
                .catch(error => console.error('Error fetching analytics:', error));
        }

        // Refresh button handler
        document.getElementById('refresh - btn').addEventListener('click', function() {
            location.reload();
        });

        // Initialize dashboard
        fetch('/api / status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateDashboard(data);
                }
            })
            .catch(error => console.error('Error fetching initial data:', error));
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Create templates directory and save template
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok = True)

    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(DASHBOARD_TEMPLATE)

    # Run dashboard
    dashboard = get_media_dashboard()
    dashboard.run()
