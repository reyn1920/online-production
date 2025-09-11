#!/usr/bin/env python3
"""
RouteLL Usage Dashboard
Web-based dashboard for monitoring RouteLL API usage, credits, and performance
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.routellm_client import RouteLL_Client
from monitoring.routellm_monitor import CreditMonitor

app = Flask(__name__)
app.secret_key = os.environ.get("ROUTELLM_SECRET_KEY", os.urandom(24).hex())

# Initialize components
monitor = CreditMonitor()
client = RouteLL_Client()


@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template("dashboard.html")


@app.route("/api/status")
def api_status():
    """Get current API status and usage"""
    try:
        client_status = client.get_status()
        usage_summary = monitor.get_usage_summary(days=1)
        recent_alerts = monitor.get_recent_alerts(hours=24)

        return jsonify(
            {
                "success": True,
                "data": {
                    "client_status": client_status,
                    "usage_summary": usage_summary,
                    "recent_alerts": recent_alerts,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/usage/<int:days>")
def usage_data(days):
    """Get usage data for specified number of days"""
    try:
        if days > 90:  # Limit to 90 days
            days = 90

        usage_summary = monitor.get_usage_summary(days=days)
        return jsonify({"success": True, "data": usage_summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts/<int:hours>")
def alerts_data(hours):
    """Get alerts for specified number of hours"""
    try:
        if hours > 720:  # Limit to 30 days
            hours = 720

        alerts = monitor.get_recent_alerts(hours=hours)
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/optimization")
def optimization_recommendations():
    """Get optimization recommendations"""
    try:
        recommendations = client.optimize_for_credits()
        return jsonify({"success": True, "data": recommendations})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test_request", methods=["POST"])
def test_request():
    """Test API request endpoint"""
    try:
        data = request.get_json()
        message = data.get("message", "Hello, this is a test message.")
        model = data.get("model", "route-llm")

        messages = [{"role": "user", "content": message}]

        response = client.chat_completion(messages, model=model)

        return jsonify(
            {
                "success": True,
                "data": {
                    "response": (
                        response.__dict__
                        if hasattr(response, "__dict__")
                        else str(response)
                    ),
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/models")
def available_models():
    """Get available models information"""
    try:
        config_path = (
            "/Users/thomasbrianreynolds/online production/config/routellm_config.json"
        )
        with open(config_path, "r") as f:
            config = json.load(f)

        unlimited_models = config["credit_system"]["unlimited_models"]
        premium_models = config["credit_system"]["high_cost_models"]

        return jsonify(
            {
                "success": True,
                "data": {
                    "unlimited_models": unlimited_models,
                    "premium_models": premium_models,
                    "default_model": config["api_settings"]["default_model"],
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Create templates directory and HTML template
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # Create the dashboard HTML template
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RouteLL API Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #718096;
            font-size: 0.9rem;
        }
        
        .metric-value {
            font-weight: bold;
            color: #2d3748;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-active { background-color: #48bb78; }
        .status-warning { background-color: #ed8936; }
        .status-error { background-color: #f56565; }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background-color: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78 0%, #ed8936 70%, #f56565 90%);
            transition: width 0.3s ease;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .alerts-container {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .alert-item {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-info {
            background-color: #ebf8ff;
            border-left-color: #3182ce;
        }
        
        .alert-warning {
            background-color: #fffbeb;
            border-left-color: #ed8936;
        }
        
        .alert-critical {
            background-color: #fed7d7;
            border-left-color: #f56565;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .test-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #4a5568;
            font-weight: 500;
        }
        
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .response-container {
            background-color: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RouteLL API Dashboard</h1>
            <p>Monitor your AI API usage, credits, and performance in real-time</p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 Current Status</h3>
                <div id="status-content">
                    <div class="loading"></div> Loading status...
                </div>
            </div>
            
            <div class="card">
                <h3>💳 Credit Usage</h3>
                <div id="credit-content">
                    <div class="loading"></div> Loading credits...
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Usage Trends</h3>
                <div class="chart-container">
                    <canvas id="usageChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>🚨 Recent Alerts</h3>
                <div id="alerts-content" class="alerts-container">
                    <div class="loading"></div> Loading alerts...
                </div>
            </div>
        </div>
        
        <div class="test-section">
            <h3>🧪 Test API Request</h3>
            <div class="form-group">
                <label for="test-message">Message:</label>
                <textarea id="test-message" rows="3" placeholder="Enter your test message here...">What is the meaning of life?</textarea>
            </div>
            <div class="form-group">
                <label for="test-model">Model:</label>
                <select id="test-model">
                    <option value="route-llm">route-llm (Default)</option>
                </select>
            </div>
            <button class="btn" onclick="testAPI()">Send Test Request</button>
            <div id="test-response" class="response-container" style="display: none;"></div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshDashboard()" title="Refresh Dashboard">
        🔄
    </button>
    
    <script>
        let usageChart;
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error);
                }
                return data.data;
            } catch (error) {
                console.error('Fetch error:', error);
                return null;
            }
        }
        
        async function updateStatus() {
            const data = await fetchData('/api/status');
            const container = document.getElementById('status-content');
            
            if (!data) {
                container.innerHTML = '<div style="color: #f56565;">❌ Failed to load status</div>';
                return;
            }
            
            const status = data.client_status.status;
            const statusColor = status === 'active' ? 'status-active' : 
                               status.includes('warning') ? 'status-warning' : 'status-error';
            
            container.innerHTML = `
                <div class="metric">
                    <span class="metric-label">
                        <span class="status-indicator ${statusColor}"></span>API Status
                    </span>
                    <span class="metric-value">${status.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Model</span>
                    <span class="metric-value">${data.client_status.configuration.model}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Monitoring</span>
                    <span class="metric-value">${data.client_status.configuration.monitoring_enabled ? '✅ Enabled' : '❌ Disabled'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Updated</span>
                    <span class="metric-value">${new Date(data.timestamp).toLocaleTimeString()}</span>
                </div>
            `;
        }
        
        async function updateCredits() {
            const data = await fetchData('/api/status');
            const container = document.getElementById('credit-content');
            
            if (!data) {
                container.innerHTML = '<div style="color: #f56565;">❌ Failed to load credits</div>';
                return;
            }
            
            const usage = data.client_status.credit_usage;
            const usagePercent = (usage.used_credits / usage.total_credits) * 100;
            
            container.innerHTML = `
                <div class="metric">
                    <span class="metric-label">Monthly Usage</span>
                    <span class="metric-value">${usage.used_credits.toLocaleString()} / ${usage.total_credits.toLocaleString()}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${usagePercent}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Remaining</span>
                    <span class="metric-value">${usage.remaining_credits.toLocaleString()} credits</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Daily Usage</span>
                    <span class="metric-value">${usage.daily_usage.toLocaleString()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Warning Level</span>
                    <span class="metric-value" style="color: ${usage.warning_level === 'critical' ? '#f56565' : usage.warning_level === 'warning' ? '#ed8936' : '#48bb78'}">
                        ${usage.warning_level.toUpperCase()}
                    </span>
                </div>
            `;
        }
        
        async function updateChart() {
            const data = await fetchData('/api/usage/7');
            
            if (!data || !data.daily_breakdown) {
                return;
            }
            
            const ctx = document.getElementById('usageChart').getContext('2d');
            
            if (usageChart) {
                usageChart.destroy();
            }
            
            const labels = data.daily_breakdown.map(d => new Date(d.date).toLocaleDateString());
            const credits = data.daily_breakdown.map(d => d.credits);
            const requests = data.daily_breakdown.map(d => d.requests);
            
            usageChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Credits Used',
                        data: credits,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    }, {
                        label: 'Requests',
                        data: requests,
                        borderColor: '#ed8936',
                        backgroundColor: 'rgba(237, 137, 54, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Credits'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Requests'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        }
        
        async function updateAlerts() {
            const data = await fetchData('/api/alerts/24');
            const container = document.getElementById('alerts-content');
            
            if (!data) {
                container.innerHTML = '<div style="color: #f56565;">❌ Failed to load alerts</div>';
                return;
            }
            
            if (data.length === 0) {
                container.innerHTML = '<div style="color: #48bb78;">✅ No recent alerts</div>';
                return;
            }
            
            container.innerHTML = data.map(alert => `
                <div class="alert-item alert-${alert.level}">
                    <strong>${alert.title}</strong><br>
                    <small>${new Date(alert.timestamp).toLocaleString()}</small><br>
                    ${alert.message}
                </div>
            `).join('');
        }
        
        async function loadModels() {
            const data = await fetchData('/api/models');
            const select = document.getElementById('test-model');
            
            if (!data) return;
            
            select.innerHTML = `
                <option value="${data.default_model}">${data.default_model} (Default)</option>
                ${data.unlimited_models.map(model => 
                    `<option value="${model}">${model} (Unlimited)</option>`
                ).join('')}
                ${data.premium_models.map(model => 
                    `<option value="${model}">${model} (Premium)</option>`
                ).join('')}
            `;
        }
        
        async function testAPI() {
            const message = document.getElementById('test-message').value;
            const model = document.getElementById('test-model').value;
            const responseContainer = document.getElementById('test-response');
            
            responseContainer.style.display = 'block';
            responseContainer.innerHTML = '<div class="loading"></div> Sending request...';
            
            try {
                const response = await fetch('/api/test_request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message, model })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    responseContainer.innerHTML = `
                        <strong>✅ Success!</strong><br><br>
                        <strong>Response:</strong><br>
                        ${JSON.stringify(data.data, null, 2)}
                    `;
                } else {
                    responseContainer.innerHTML = `
                        <strong>❌ Error:</strong><br>
                        ${data.error}
                    `;
                }
            } catch (error) {
                responseContainer.innerHTML = `
                    <strong>❌ Request Failed:</strong><br>
                    ${error.message}
                `;
            }
        }
        
        async function refreshDashboard() {
            await Promise.all([
                updateStatus(),
                updateCredits(),
                updateChart(),
                updateAlerts()
            ]);
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', async function() {
            await loadModels();
            await refreshDashboard();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshDashboard, 30000);
        });
    </script>
</body>
</html>
    """

    with open(os.path.join(templates_dir, "dashboard.html"), "w") as f:
        f.write(dashboard_html)

    print("🚀 Starting RouteLL Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Auto-refresh enabled every 30 seconds")
    print("\n💡 Features:")
    print("   - Real-time credit monitoring")
    print("   - Usage analytics and trends")
    print("   - Alert management")
    print("   - API testing interface")
    print("   - Model optimization recommendations")

    # Start monitoring in background
    monitor.start_monitoring()

    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
    finally:
        monitor.stop_monitoring()
