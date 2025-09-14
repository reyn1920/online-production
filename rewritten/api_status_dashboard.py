#!/usr/bin/env python3
"""
API Status Dashboard
Real - time monitoring and management for 100+ APIs

Features:
- Live status monitoring
- Performance metrics
- Cost tracking
- Health alerts
- Interactive web interface
- API usage analytics

Usage:
    python api_status_dashboard.py
    Open http://localhost:8080 in browser
"""

import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class APIStatus:
    api_key: str
    api_name: str
    status: str  # 'active', 'inactive', 'error', 'unknown'
    last_check: str
    response_time: Optional[float]
    error_message: Optional[str]
    uptime_percentage: float
    daily_requests: int
    daily_cost: float
    rate_limit_remaining: Optional[int]
    health_score: int
    phase: int
    priority: str
    cost_tier: str


@dataclass
class SystemMetrics:
    total_apis: int
    active_apis: int
    inactive_apis: int
    error_apis: int
    avg_response_time: float
    total_daily_cost: float
    total_daily_requests: int
    overall_health_score: int
    last_updated: str


class APIStatusDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "api - dashboard - secret - key"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.api_statuses = {}
        self.system_metrics = SystemMetrics(
            total_apis=0,
            active_apis=0,
            inactive_apis=0,
            error_apis=0,
            avg_response_time=0.0,
            total_daily_cost=0.0,
            total_daily_requests=0,
            overall_health_score=0,
            last_updated=datetime.now().isoformat(),
        )

        self.monitoring_active = False
        self.update_interval = 30  # seconds

        # Import required modules
        try:
            from api_registration_automation import API_REGISTRY
            from api_testing_suite import APITester

            self.api_registry = API_REGISTRY
            self.tester = APITester()
        except ImportError as e:
            logger.error(f"Required modules not found: {e}")
            sys.exit(1)

        self.setup_routes()
        self.setup_socketio_events()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def dashboard():
            return render_template_string(self.get_dashboard_template())

        @self.app.route("/api/status")
        def api_status():
            return jsonify(
                {
                    "statuses": {k: asdict(v) for k, v in self.api_statuses.items()},
                    "metrics": asdict(self.system_metrics),
                }
            )

        @self.app.route("/api/test/<api_key>")
        def test_api(api_key):
            try:
                result = self.test_single_api(api_key)
                return jsonify({"success": True, "result": result})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

        @self.app.route("/api/toggle/<api_key>", methods=["POST"])
        def toggle_api(api_key):
            try:
                # Toggle API monitoring
                if api_key in self.api_statuses:
                    current_status = self.api_statuses[api_key].status
                    new_status = "inactive" if current_status == "active" else "active"
                    self.api_statuses[api_key].status = new_status
                    return jsonify({"success": True, "new_status": new_status})
                else:
                    return jsonify({"success": False, "error": "API not found"})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

        @self.app.route("/api/metrics")
        def get_metrics():
            return jsonify(asdict(self.system_metrics))

        @self.app.route("/api/export")
        def export_data():
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "api_statuses": {k: asdict(v) for k, v in self.api_statuses.items()},
                "system_metrics": asdict(self.system_metrics),
            }
            return jsonify(export_data)

    def setup_socketio_events(self):
        """Setup SocketIO events for real - time updates"""

        @self.socketio.on("connect")
        def handle_connect():
            logger.info("Client connected to dashboard")
            emit(
                "status_update",
                {
                    "statuses": {k: asdict(v) for k, v in self.api_statuses.items()},
                    "metrics": asdict(self.system_metrics),
                },
            )

        @self.socketio.on("disconnect")
        def handle_disconnect():
            logger.info("Client disconnected from dashboard")

        @self.socketio.on("request_update")
        def handle_request_update():
            emit(
                "status_update",
                {
                    "statuses": {k: asdict(v) for k, v in self.api_statuses.items()},
                    "metrics": asdict(self.system_metrics),
                },
            )

    def initialize_api_statuses(self):
        """Initialize API statuses from registry"""
        logger.info("Initializing API statuses...")

        for api_key, api_config in self.api_registry.items():
            self.api_statuses[api_key] = APIStatus(
                api_key=api_key,
                api_name=api_config["name"],
                status="unknown",
                last_check=datetime.now().isoformat(),
                response_time=None,
                error_message=None,
                uptime_percentage=0.0,
                daily_requests=0,
                daily_cost=0.0,
                rate_limit_remaining=None,
                health_score=0,
                phase=api_config["phase"],
                priority=api_config["priority"],
                cost_tier=api_config["cost"],
            )

        logger.info(f"Initialized {len(self.api_statuses)} API statuses")

    def test_single_api(self, api_key: str) -> Dict:
        """Test a single API and return detailed results"""
        if api_key not in self.api_statuses:
            raise ValueError(f"API {api_key} not found")

        api_status = self.api_statuses[api_key]
        start_time = time.time()

        try:
            # Use the API tester
            result = self.tester.run_specific_test(api_key)
            response_time = time.time() - start_time

            if result:
                api_status.status = "active" if result.status == "success" else "error"
                api_status.response_time = result.response_time or response_time
                api_status.error_message = result.error_message
                api_status.last_check = datetime.now().isoformat()

                # Calculate health score
                health_score = self.calculate_health_score(api_status)
                api_status.health_score = health_score

                return {
                    "status": result.status,
                    "response_time": api_status.response_time,
                    "error_message": api_status.error_message,
                    "health_score": health_score,
                }
            else:
                api_status.status = "error"
                api_status.error_message = "No test result returned"
                api_status.last_check = datetime.now().isoformat()
                return {"status": "error", "error_message": "No test result returned"}

        except Exception as e:
            api_status.status = "error"
            api_status.error_message = str(e)
            api_status.last_check = datetime.now().isoformat()
            return {"status": "error", "error_message": str(e)}

    def calculate_health_score(self, api_status: APIStatus) -> int:
        """Calculate health score for an API (0 - 100)"""
        score = 0

        # Base score for being active
        if api_status.status == "active":
            score += 40
        elif api_status.status == "inactive":
            score += 20

        # Response time score (0 - 30 points)
        if api_status.response_time:
            if api_status.response_time < 0.5:
                score += 30
            elif api_status.response_time < 1.0:
                score += 25
            elif api_status.response_time < 2.0:
                score += 20
            elif api_status.response_time < 5.0:
                score += 10

        # Error score (0 - 20 points)
        if not api_status.error_message:
            score += 20

        # Uptime score (0 - 10 points)
        if api_status.uptime_percentage >= 99:
            score += 10
        elif api_status.uptime_percentage >= 95:
            score += 8
        elif api_status.uptime_percentage >= 90:
            score += 5

        return min(score, 100)

    def update_all_statuses(self):
        """Update all API statuses"""
        logger.info("Updating all API statuses...")

        # Use thread pool for parallel testing
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for api_key in self.api_statuses.keys():
                future = executor.submit(self.test_single_api, api_key)
                futures[future] = api_key

            for future in futures:
                try:
                    result = future.result(timeout=30)
                    api_key = futures[future]
                    logger.debug(f"Updated {api_key}: {result['status']}")
                except Exception as e:
                    api_key = futures[future]
                    logger.error(f"Failed to update {api_key}: {str(e)}")

        # Update system metrics
        self.update_system_metrics()

        # Broadcast update to connected clients
        self.socketio.emit(
            "status_update",
            {
                "statuses": {k: asdict(v) for k, v in self.api_statuses.items()},
                "metrics": asdict(self.system_metrics),
            },
        )

        logger.info("Status update completed")

    def update_system_metrics(self):
        """Update overall system metrics"""
        total_apis = len(self.api_statuses)
        active_apis = sum(1 for s in self.api_statuses.values() if s.status == "active")
        inactive_apis = sum(1 for s in self.api_statuses.values() if s.status == "inactive")
        error_apis = sum(1 for s in self.api_statuses.values() if s.status == "error")

        # Calculate average response time
        response_times = [s.response_time for s in self.api_statuses.values() if s.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # Calculate total costs and requests
        total_daily_cost = sum(s.daily_cost for s in self.api_statuses.values())
        total_daily_requests = sum(s.daily_requests for s in self.api_statuses.values())

        # Calculate overall health score
        health_scores = [s.health_score for s in self.api_statuses.values()]
        overall_health_score = int(sum(health_scores) / len(health_scores)) if health_scores else 0

        self.system_metrics = SystemMetrics(
            total_apis=total_apis,
            active_apis=active_apis,
            inactive_apis=inactive_apis,
            error_apis=error_apis,
            avg_response_time=avg_response_time,
            total_daily_cost=total_daily_cost,
            total_daily_requests=total_daily_requests,
            overall_health_score=overall_health_score,
            last_updated=datetime.now().isoformat(),
        )

    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True

        def monitoring_loop():
            while self.monitoring_active:
                try:
                    self.update_all_statuses()
                    time.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Monitoring error: {str(e)}")
                    time.sleep(60)  # Wait before retrying

        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info(f"Monitoring started (interval: {self.update_interval}s)")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("Monitoring stopped")

    def get_dashboard_template(self) -> str:
        """Return HTML template for dashboard"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > API Status Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box - sizing: border - box;
        }

        body {
            font - family: 'Segoe UI', Tahoma, Geneva, Verdana, sans - serif;
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min - height: 100vh;
        }

        .container {
            max - width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text - align: center;
            margin - bottom: 30px;
            color: white;
        }

        .header h1 {
            font - size: 2.5em;
            margin - bottom: 10px;
            text - shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .metrics - grid {
            display: grid;
            grid - template - columns: repeat(auto - fit, minmax(250px, 1fr));
            gap: 20px;
            margin - bottom: 30px;
        }

        .metric - card {
            background: white;
            border - radius: 15px;
            padding: 25px;
            box - shadow: 0 8px 32px rgba(0,0,0,0.1);
            text - align: center;
            transition: transform 0.3s ease;
        }

        .metric - card:hover {
            transform: translateY(-5px);
        }

        .metric - value {
            font - size: 2.5em;
            font - weight: bold;
            margin - bottom: 10px;
        }

        .metric - label {
            color: #666;
            font - size: 1.1em;
        }

        .status - grid {
            display: grid;
            grid - template - columns: repeat(auto - fill, minmax(300px, 1fr));
            gap: 20px;
            margin - bottom: 30px;
        }

        .api - card {
            background: white;
            border - radius: 15px;
            padding: 20px;
            box - shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .api - card:hover {
            transform: translateY(-3px);
        }

        .api - header {
            display: flex;
            justify - content: space - between;
            align - items: center;
            margin - bottom: 15px;
        }

        .api - name {
            font - weight: bold;
            font - size: 1.2em;
        }

        .status - badge {
            padding: 5px 12px;
            border - radius: 20px;
            font - size: 0.9em;
            font - weight: bold;
            text - transform: uppercase;
        }

        .status - active {
            background: #d4edda;
            color: #155724;
        }

        .status - inactive {
            background: #f8d7da;
            color: #721c24;
        }

        .status - error {
            background: #f5c6cb;
            color: #721c24;
        }

        .status - unknown {
            background: #e2e3e5;
            color: #383d41;
        }

        .api - details {
            display: grid;
            grid - template - columns: 1fr 1fr;
            gap: 10px;
            font - size: 0.9em;
        }

        .detail - item {
            display: flex;
            justify - content: space - between;
        }

        .detail - label {
            color: #666;
        }

        .detail - value {
            font - weight: bold;
        }

        .controls {
            background: white;
            border - radius: 15px;
            padding: 25px;
            box - shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin - bottom: 30px;
        }

        .controls h3 {
            margin - bottom: 20px;
            color: #333;
        }

        .button - group {
            display: flex;
            gap: 15px;
            flex - wrap: wrap;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border - radius: 8px;
            cursor: pointer;
            font - weight: bold;
            transition: all 0.3s ease;
            text - decoration: none;
            display: inline - block;
        }

        .btn - primary {
            background: #007bff;
            color: white;
        }

        .btn - primary:hover {
            background: #0056b3;
        }

        .btn - success {
            background: #28a745;
            color: white;
        }

        .btn - success:hover {
            background: #1e7e34;
        }

        .btn - warning {
            background: #ffc107;
            color: #212529;
        }

        .btn - warning:hover {
            background: #e0a800;
        }

        .btn - danger {
            background: #dc3545;
            color: white;
        }

        .btn - danger:hover {
            background: #c82333;
        }

        .health - bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border - radius: 4px;
            overflow: hidden;
            margin - top: 10px;
        }

        .health - fill {
            height: 100%;
            transition: width 0.3s ease;
        }

        .health - excellent {
            background: #28a745;
        }

        .health - good {
            background: #ffc107;
        }

        .health - poor {
            background: #dc3545;
        }

        .last - updated {
            text - align: center;
            color: white;
            margin - top: 20px;
            font - style: italic;
        }

        .phase - badge {
            background: #6c757d;
            color: white;
            padding: 2px 8px;
            border - radius: 12px;
            font - size: 0.8em;
            margin - left: 10px;
        }

        .priority - high {
            background: #dc3545;
        }

        .priority - medium {
            background: #ffc107;
        }

        .priority - low {
            background: #28a745;
        }

        @media (max - width: 768px) {
            .metrics - grid {
                grid - template - columns: 1fr;
            }

            .status - grid {
                grid - template - columns: 1fr;
            }

            .button - group {
                flex - direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Status Dashboard</h1>
            <p > Real - time monitoring of 100+ APIs</p>
        </div>

        <div class="metrics - grid">
            <div class="metric - card">
                <div class="metric - value" id="total - apis">0</div>
                <div class="metric - label">Total APIs</div>
            </div>
            <div class="metric - card">
                <div class="metric - value" id="active - apis" style="color: #28a745;">0</div>
                <div class="metric - label">Active APIs</div>
            </div>
            <div class="metric - card">
                <div class="metric - value" id="error - apis" style="color: #dc3545;">0</div>
                <div class="metric - label">Error APIs</div>
            </div>
            <div class="metric - card">
                <div class="metric - value" id="avg - response - time">0ms</div>
                <div class="metric - label">Avg Response Time</div>
            </div>
            <div class="metric - card">
                <div class="metric - value" id="health - score" style="color: #007bff;">0%</div>
                <div class="metric - label">Overall Health</div>
            </div>
            <div class="metric - card">
                <div class="metric - value" id="daily - cost" style="color: #ffc107;">$0.00</div>
                <div class="metric - label">Daily Cost</div>
            </div>
        </div>

        <div class="controls">
            <h3>🎛️ Dashboard Controls</h3>
            <div class="button - group">
                <button class="btn btn - primary" onclick="refreshAll()">🔄 Refresh All</button>
                <button class="btn btn - success" onclick="testAll()">🧪 Test All APIs</button>
                <button class="btn btn - warning" onclick="exportData()">📊 Export Data</button>
                <button class="btn btn - danger" onclick="toggleMonitoring()">⏸️ Toggle Monitoring</button>
            </div>
        </div>

        <div class="status - grid" id="api - grid">
            <!-- API cards will be populated here -->
        </div>

        <div class="last - updated" id="last - updated">
            Last updated: Never
        </div>
    </div>

    <script>
        const socket = io();
        let monitoringActive = true;

        socket.on('connect', function() {
            console.log('Connected to dashboard');
        });

        socket.on('status_update', function(data) {
            updateDashboard(data);
        });

        function updateDashboard(data) {//Update metrics
            const metrics = data.metrics;
            document.getElementById('total - apis').textContent = metrics.total_apis;
            document.getElementById('active - apis').textContent = metrics.active_apis;
            document.getElementById('error - apis').textContent = metrics.error_apis;
            document.getElementById('avg - response - time').textContent =
                metrics.avg_response_time ? `${(metrics.avg_response_time * 1000).toFixed(0)}ms` : '0ms';
            document.getElementById('health - score').textContent = `${metrics.overall_health_score}%`;
            document.getElementById('daily - cost').textContent = `$${metrics.total_daily_cost.toFixed(2)}`;//Update API grid
            const grid = document.getElementById('api - grid');
            grid.innerHTML = '';

            Object.entries(data.statuses).forEach(([apiKey, status]) => {
                const card = createApiCard(apiKey, status);
                grid.appendChild(card);
            });//Update last updated time
            document.getElementById('last - updated').textContent =
                `Last updated: ${new Date(metrics.last_updated).toLocaleString()}`;
        }

        function createApiCard(apiKey, status) {
            const card = document.createElement('div');
            card.className = 'api - card';

            const healthClass = status.health_score >= 80 ? 'health - excellent' :
                              status.health_score >= 60 ? 'health - good' : 'health - poor';

            const priorityClass = `priority-${status.priority}`;

            card.innerHTML = `
                <div class="api - header">
                    <div>
                        <span class="api - name">${status.api_name}</span>
                        <span class="phase - badge">Phase ${status.phase}</span>
                        <span class="phase - badge ${priorityClass}">${status.priority.toUpperCase()}</span>
                    </div>
                    <span class="status - badge status-${status.status}">${status.status}</span>
                </div>
                <div class="api - details">
                    <div class="detail - item">
                        <span class="detail - label">Response Time:</span>
                        <span class="detail - value">${status.response_time ? `${(status.response_time * 1000).toFixed(0)}ms` : 'N/A'}</span>
                    </div>
                    <div class="detail - item">
                        <span class="detail - label">Health Score:</span>
                        <span class="detail - value">${status.health_score}%</span>
                    </div>
                    <div class="detail - item">
                        <span class="detail - label">Daily Requests:</span>
                        <span class="detail - value">${status.daily_requests}</span>
                    </div>
                    <div class="detail - item">
                        <span class="detail - label">Daily Cost:</span>
                        <span class="detail - value">$${status.daily_cost.toFixed(2)}</span>
                    </div>
                    <div class="detail - item">
                        <span class="detail - label">Last Check:</span>
                        <span class="detail - value">${new Date(status.last_check).toLocaleTimeString()}</span>
                    </div>
                    <div class="detail - item">
                        <span class="detail - label">Cost Tier:</span>
                        <span class="detail - value">${status.cost_tier}</span>
                    </div>
                </div>
                <div class="health - bar">
                    <div class="health - fill ${healthClass}" style="width: ${status.health_score}%"></div>
                </div>
                ${status.error_message ? `<div style="color: #dc3545; font - size: 0.9em; margin - top: 10px;">⚠️ ${status.error_message}</div>` : ''}
            `;//Add click handler for testing
            card.addEventListener('click', () => testApi(apiKey));
            card.style.cursor = 'pointer';

            return card;
        }

        function refreshAll() {
            socket.emit('request_update');
        }

        function testAll() {//This would trigger a full test of all APIs
            fetch("/api/test/all', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('✅ All APIs tested successfully');
                    } else {
                        alert('❌ Test failed: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Test error:', error);
                });
        }

        function testApi(apiKey) {
            fetch(`/api/test/${apiKey}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`✅ ${apiKey} test completed`);
                        refreshAll();
                    } else {
                        alert(`❌ ${apiKey} test failed: ${data.error}`);
                    }
                })
                .catch(error => {
                    console.error('Test error:', error);
                });
        }

        function exportData() {
            fetch("/api/export')
                .then(response => response.json())
                .then(data => {
                    const blob = new Blob([JSON.stringify(data,
    null,
    2)], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `api_status_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                })
                .catch(error => {
                    console.error('Export error:', error);
                });
        }

        function toggleMonitoring() {
            monitoringActive = !monitoringActive;
            const button = event.target;
            if (monitoringActive) {
                button.textContent = '⏸️ Pause Monitoring';
                button.className = 'btn btn - danger';
            } else {
                button.textContent = '▶️ Resume Monitoring';
                button.className = 'btn btn - success';
            }
        }//Auto - refresh every 30 seconds
        setInterval(() => {
            if (monitoringActive) {
                refreshAll();
            }
        }, 30000);//Initial load
        refreshAll();
    </script>
</body>
</html>
        """

    def run(self, host="localhost", port=8080, debug=False):
        """Run the dashboard server"""
        logger.info(f"Starting API Status Dashboard on http://{host}:{port}")

        # Initialize API statuses
        self.initialize_api_statuses()

        # Start monitoring
        self.start_monitoring()

        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        finally:
            self.stop_monitoring()


def main():
    """Main entry point"""
    try:
        dashboard = APIStatusDashboard()
        dashboard.run()
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
