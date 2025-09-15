#!/usr / bin / env python3
""""""
TRAE AI Monitoring Dashboard
Provides a web - based dashboard for monitoring system health, performance, and errors.
""""""

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from flask import Flask, jsonify, render_template_string, request

except ImportError:
    print("Flask not installed. Install with: pip install flask")
    exit(1)

from error_tracker import ErrorTracker
from performance_monitor import PerformanceMonitor

app = Flask(__name__)
app.secret_key = os.environ.get("MONITORING_SECRET_KEY", os.urandom(24).hex())

# Initialize monitoring components
performance_monitor = PerformanceMonitor()
error_tracker = ErrorTracker()

# HTML Template for the dashboard
DASHBOARD_TEMPLATE = """"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > TRAE AI Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box - sizing: border - box;
# BRACKET_SURGEON: disabled
#         }

        body {
            font - family: -apple - system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans - serif;
            background: #0f1419;
            color: #e6e6e6;
            line - height: 1.6;
# BRACKET_SURGEON: disabled
#         }

        .header {
            background: linear - gradient(135deg, #1a1f2e 0%, #2d3748 100%);
            padding: 1rem 2rem;
            border - bottom: 2px solid #4a5568;
            box - shadow: 0 2px 10px rgba(0,0,0,0.3);
# BRACKET_SURGEON: disabled
#         }

        .header h1 {
            color: #00d4ff;
            font - size: 2rem;
            font - weight: 700;
            margin - bottom: 0.5rem;
# BRACKET_SURGEON: disabled
#         }

        .header .subtitle {
            color: #a0aec0;
            font - size: 1rem;
# BRACKET_SURGEON: disabled
#         }

        .container {
            max - width: 1400px;
            margin: 0 auto;
            padding: 2rem;
# BRACKET_SURGEON: disabled
#         }

        .grid {
            display: grid;
            grid - template - columns: repeat(auto - fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin - bottom: 2rem;
# BRACKET_SURGEON: disabled
#         }

        .card {
            background: #1a202c;
            border: 1px solid #2d3748;
            border - radius: 12px;
            padding: 1.5rem;
            box - shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box - shadow 0.2s;
# BRACKET_SURGEON: disabled
#         }

        .card:hover {
            transform: translateY(-2px);
            box - shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
# BRACKET_SURGEON: disabled
#         }

        .card h3 {
            color: #00d4ff;
            margin - bottom: 1rem;
            font - size: 1.25rem;
            display: flex;
            align - items: center;
            gap: 0.5rem;
# BRACKET_SURGEON: disabled
#         }

        .status - indicator {
            width: 12px;
            height: 12px;
            border - radius: 50%;
            display: inline - block;
# BRACKET_SURGEON: disabled
#         }

        .status - healthy { background: #48bb78; }
        .status - warning { background: #ed8936; }
        .status - critical { background: #f56565; }
        .status - unknown { background: #718096; }

        .metric {
            display: flex;
            justify - content: space - between;
            align - items: center;
            padding: 0.75rem 0;
            border - bottom: 1px solid #2d3748;
# BRACKET_SURGEON: disabled
#         }

        .metric:last - child {
            border - bottom: none;
# BRACKET_SURGEON: disabled
#         }

        .metric - label {
            color: #a0aec0;
            font - weight: 500;
# BRACKET_SURGEON: disabled
#         }

        .metric - value {
            color: #e6e6e6;
            font - weight: 600;
            font - size: 1.1rem;
# BRACKET_SURGEON: disabled
#         }

        .progress - bar {
            width: 100%;
            height: 8px;
            background: #2d3748;
            border - radius: 4px;
            overflow: hidden;
            margin - top: 0.5rem;
# BRACKET_SURGEON: disabled
#         }

        .progress - fill {
            height: 100%;
            transition: width 0.3s ease;
# BRACKET_SURGEON: disabled
#         }

        .progress - normal { background: #48bb78; }
        .progress - warning { background: #ed8936; }
        .progress - critical { background: #f56565; }

        .alert - item {
            background: #2d1b1b;
            border: 1px solid #f56565;
            border - radius: 8px;
            padding: 1rem;
            margin - bottom: 0.75rem;
# BRACKET_SURGEON: disabled
#         }

        .alert - item.warning {
            background: #2d2416;
            border - color: #ed8936;
# BRACKET_SURGEON: disabled
#         }

        .alert - timestamp {
            color: #a0aec0;
            font - size: 0.875rem;
            margin - bottom: 0.25rem;
# BRACKET_SURGEON: disabled
#         }

        .alert - message {
            color: #e6e6e6;
            font - weight: 500;
# BRACKET_SURGEON: disabled
#         }

        .refresh - btn {
            background: #00d4ff;
            color: #0f1419;
            border: none;
            padding: 0.75rem 1.5rem;
            border - radius: 8px;
            font - weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            margin - bottom: 1rem;
# BRACKET_SURGEON: disabled
#         }

        .refresh - btn:hover {
            background: #0099cc;
# BRACKET_SURGEON: disabled
#         }

        .timestamp {
            color: #718096;
            font - size: 0.875rem;
            text - align: center;
            margin - top: 2rem;
# BRACKET_SURGEON: disabled
#         }

        .error - list {
            max - height: 300px;
            overflow - y: auto;
# BRACKET_SURGEON: disabled
#         }

        .error - item {
            background: #2d1b1b;
            border - left: 4px solid #f56565;
            padding: 0.75rem;
            margin - bottom: 0.5rem;
            border - radius: 0 8px 8px 0;
# BRACKET_SURGEON: disabled
#         }

        .error - level {
            color: #f56565;
            font - weight: 600;
            font - size: 0.875rem;
# BRACKET_SURGEON: disabled
#         }

        .error - message {
            color: #e6e6e6;
            margin - top: 0.25rem;
# BRACKET_SURGEON: disabled
#         }

        @media (max - width: 768px) {
            .container {
                padding: 1rem;
# BRACKET_SURGEON: disabled
#             }

            .grid {
                grid - template - columns: 1fr;
# BRACKET_SURGEON: disabled
#             }

            .header {
                padding: 1rem;
# BRACKET_SURGEON: disabled
#             }

            .header h1 {
                font - size: 1.5rem;
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         }
    </style>
    <script>
        function refreshDashboard() {
            location.reload();
# BRACKET_SURGEON: disabled
#         }

        // Auto - refresh every 30 seconds
        setInterval(refreshDashboard, 30000);

        function getProgressBarClass(value, type) {
            if (type === 'cpu' || type === 'memory' || type === 'disk') {
                if (value >= 90) return 'progress - critical';
                if (value >= 75) return 'progress - warning';
                return 'progress - normal';
# BRACKET_SURGEON: disabled
#             }
            return 'progress - normal';
# BRACKET_SURGEON: disabled
#         }
    </script>
</head>
<body>
    <div class="header">
        <h1>🤖 TRAE AI Monitoring Dashboard</h1>
        <div class="subtitle">Real - time system health and performance monitoring</div>
    </div>

    <div class="container">
        <button class="refresh - btn" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>

        <div class="grid">
            <!-- System Health Card -->
            <div class="card">
                <h3>
                    <span class="status - indicator status-{{ health_status.status }}"></span>
                    System Health
                </h3>
                <div class="metric">
                    <span class="metric - label">Overall Status</span>
                    <span class="metric - value">{{ health_status.status|title }}</span>
                </div>
                <div class="metric">
                    <span class="metric - label">Uptime</span>
                    <span class="metric - value">{{ uptime_formatted }}</span>
                </div>
                <div class="metric">
                    <span class="metric - label">Active Agents</span>
                    <span class="metric - value">{{ health_status.application_metrics.active_agents }}</span>
                </div>
                <div class="metric">
                    <span class="metric - label">Dashboard Status</span>
                    <span class="metric - value">{{ health_status.application_metrics.dashboard_status|title }}</span>
                </div>
            </div>

            <!-- CPU & Memory Card -->
            <div class="card">
                <h3>💻 CPU & Memory</h3>
                <div class="metric">
                    <span class="metric - label">CPU Usage</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.system_metrics.cpu_percent) }}%</span>
                </div>
                <div class="progress - bar">
                    <div class="progress - fill progress-{{ 'critical' if health_status.system_metrics.cpu_percent >= 90 else 'warning' if health_status.system_metrics.cpu_percent >= 75 else 'normal' }}"
                         style="width: {{ health_status.system_metrics.cpu_percent }}%"></div>
                </div>

                <div class="metric">
                    <span class="metric - label">Memory Usage</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.system_metrics.memory_percent) }}%</span>
                </div>
                <div class="progress - bar">
                    <div class="progress - fill progress-{{ 'critical' if health_status.system_metrics.memory_percent >= 90 else 'warning' if health_status.system_metrics.memory_percent >= 75 else 'normal' }}"
                         style="width: {{ health_status.system_metrics.memory_percent }}%"></div>
                </div>

                <div class="metric">
                    <span class="metric - label">Available Memory</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.system_metrics.memory_available_mb / 1024) }} GB</span>
                </div>
            </div>

            <!-- Storage & Network Card -->
            <div class="card">
                <h3>💾 Storage & Network</h3>
                <div class="metric">
                    <span class="metric - label">Disk Usage</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.system_metrics.disk_usage_percent) }}%</span>
                </div>
                <div class="progress - bar">
                    <div class="progress - fill progress-{{ 'critical' if health_status.system_metrics.disk_usage_percent >= 90 else 'warning' if health_status.system_metrics.disk_usage_percent >= 75 else 'normal' }}"
                         style="width: {{ health_status.system_metrics.disk_usage_percent }}%"></div>
                </div>

                <div class="metric">
                    <span class="metric - label">Free Space</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.system_metrics.disk_free_gb) }} GB</span>
                </div>

                <div class="metric">
                    <span class="metric - label">Network Sent</span>
                    <span class="metric - value">{{ format_bytes(health_status.system_metrics.network_bytes_sent) }}</span>
                </div>

                <div class="metric">
                    <span class="metric - label">Network Received</span>
                    <span class="metric - value">{{ format_bytes(health_status.system_metrics.network_bytes_recv) }}</span>
                </div>
            </div>

            <!-- Performance Metrics Card -->
            <div class="card">
                <h3>📊 Performance</h3>
                <div class="metric">
                    <span class="metric - label">Response Time</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.application_metrics.response_time_ms) }} ms</span>
                </div>

                <div class="metric">
                    <span class="metric - label">Process Count</span>
                    <span class="metric - value">{{ health_status.system_metrics.process_count }}</span>
                </div>

                <div class="metric">
                    <span class="metric - label">Load Average</span>
                    <span class="metric - value">{{ "%.2f"|format(health_status.system_metrics.load_average[0]) }}</span>
                </div>

                <div class="metric">
                    <span class="metric - label">App Memory</span>
                    <span class="metric - value">{{ "%.1f"|format(health_status.application_metrics.memory_usage_mb) }} MB</span>
                </div>
            </div>
        </div>

        <!-- Alerts Section -->
        {% if health_status.alerts %}
        <div class="card">
            <h3>🚨 Active Alerts</h3>
            {% for alert in health_status.alerts %}
            <div class="alert - item {{ alert.severity }}">
                <div class="alert - timestamp">{{ alert.get('timestamp', 'Unknown time') }}</div>
                <div class="alert - message">{{ alert.message }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Recent Errors Section -->
        {% if error_summary.recent_alerts %}
        <div class="card">
            <h3>⚠️ Recent Error Alerts</h3>
            <div class="error - list">
                {% for alert in error_summary.recent_alerts[:5] %}
                <div class="error - item">
                    <div class="error - level">{{ alert.severity|upper }}</div>
                    <div class="error - message">{{ alert.message }}</div>
                    <div class="alert - timestamp">{{ alert.timestamp }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Error Statistics -->
        <div class="card">
            <h3>📈 Error Statistics (24h)</h3>
            <div class="metric">
                <span class="metric - label">Total Errors</span>
                <span class="metric - value">{{ error_summary.total_errors }}</span>
            </div>

            {% for level, count in error_summary.errors_by_level.items() %}
            <div class="metric">
                <span class="metric - label">{{ level|title }} Errors</span>
                <span class="metric - value">{{ count }}</span>
            </div>
            {% endfor %}
        </div>

        <div class="timestamp">
            Last updated: {{ current_time }}
        </div>
    </div>
</body>
</html>
""""""


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_uptime(seconds: float) -> str:
    """Format uptime seconds into human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


@app.route("/")
def dashboard():
    """Main dashboard route."""
    try:
        # Get health status
        health_status = performance_monitor.get_health_status()

        # Get error summary
        error_summary = error_tracker.get_error_summary(24)

        # Format uptime
        uptime_formatted = format_uptime(health_status.get("uptime_seconds", 0))

        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return render_template_string(
            DASHBOARD_TEMPLATE,
            health_status=health_status,
            error_summary=error_summary,
            uptime_formatted=uptime_formatted,
            current_time=current_time,
            format_bytes=format_bytes,
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Dashboard error",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


@app.route("/api / health")
def api_health():
    """Health check API endpoint."""
    try:
        health_status = performance_monitor.get_health_status()
        return jsonify(health_status)
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


@app.route("/api / errors")
def api_errors():
    """Error summary API endpoint."""
    try:
        hours = request.args.get("hours", 24, type=int)
        error_summary = error_tracker.get_error_summary(hours)
        return jsonify(error_summary)
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Failed to get error summary",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


@app.route("/api / metrics")
def api_metrics():
    """Combined metrics API endpoint."""
    try:
        health_status = performance_monitor.get_health_status()
        error_summary = error_tracker.get_error_summary(24)

        return jsonify(
            {
                "health": health_status,
                "errors": error_summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Failed to get metrics",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


@app.route("/api / alerts")
def api_alerts():
    """Active alerts API endpoint."""
    try:
        # Get recent alerts from error tracker
        with sqlite3.connect(error_tracker.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """"""
                SELECT rule_name, severity, message, timestamp
                FROM alert_history
                WHERE timestamp >= datetime('now', '-1 hour')
                AND acknowledged = FALSE
                ORDER BY timestamp DESC
            """"""
# BRACKET_SURGEON: disabled
#             )

            alerts = [
                {
                    "rule_name": row[0],
                    "severity": row[1],
                    "message": row[2],
                    "timestamp": row[3],
# BRACKET_SURGEON: disabled
#                 }
                for row in cursor.fetchall()
# BRACKET_SURGEON: disabled
#             ]

        return jsonify(
            {
                "alerts": alerts,
                "count": len(alerts),
                "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Failed to get alerts",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


def main():
    """Main function to run the monitoring dashboard."""

    import sys

    # Configuration
    host = os.environ.get("MONITORING_HOST", "127.0.0.1")
    port = int(os.environ.get("MONITORING_PORT", 5001))
    debug = os.environ.get("MONITORING_DEBUG", "false").lower() == "true"

    print(f"🚀 Starting TRAE AI Monitoring Dashboard")
    print(f"📊 Dashboard URL: http://{host}:{port}")
    print(f"🔗 Health API: http://{host}:{port}/api / health")
    print(f"⚠️  Errors API: http://{host}:{port}/api / errors")
    print(f"📈 Metrics API: http://{host}:{port}/api / metrics")
    print(f"🚨 Alerts API: http://{host}:{port}/api / alerts")
    print("")
    print("Press Ctrl + C to stop the dashboard")

    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("\\n👋 Monitoring dashboard stopped")
    except Exception as e:
        print(f"❌ Failed to start monitoring dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()