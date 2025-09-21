#!/usr/bin/env python3
"""Simple server for testing dashboard functionality"""

from datetime import datetime
from typing import Any


# Mock classes for standalone operation
class MockFastAPI:
    def __init__(self, title: str = "Mock API", **kwargs):
        self.routes = []
        self.title = title

    def get(self, path: str, response_class=None, **kwargs):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func

        return decorator

    def post(self, path: str, **kwargs):
        def decorator(func):
            self.routes.append(("POST", path, func))
            return func

        return decorator


class MockHTMLResponse:
    def __init__(self, content: str, status_code: int = 200):
        self.content = content
        self.status_code = status_code


class MockJSONResponse:
    def __init__(self, content: dict[str, Any], status_code: int = 200):
        self.content = content
        self.status_code = status_code


# Use mock classes
FastAPI = MockFastAPI
HTMLResponse = MockHTMLResponse
JSONResponse = MockJSONResponse

app = FastAPI(title="Simple Dashboard Server")


# Mock data for dashboard
def get_system_metrics():
    return {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 34.1,
        "active_connections": 12,
        "uptime_seconds": 86400,
    }


def get_application_stats():
    return {
        "total_requests": 15420,
        "requests_per_minute": 45,
        "error_rate": 0.02,
        "avg_response_time": 120,
        "active_users": 234,
        "total_users": 1567,
    }


def get_revenue_data():
    return {
        "daily_revenue": 1250.75,
        "monthly_revenue": 28450.20,
        "total_revenue": 156789.45,
        "conversion_rate": 3.2,
        "active_subscriptions": 89,
        "churn_rate": 2.1,
    }


@app.get("/api/comprehensive/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview"""
    overview_data = {
        "timestamp": datetime.now().isoformat(),
        "system_metrics": get_system_metrics(),
        "application_stats": get_application_stats(),
        "revenue_data": get_revenue_data(),
        "status": "operational",
    }
    return JSONResponse(content=overview_data)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the comprehensive dashboard HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 Comprehensive Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: white;
                font-size: 2.5rem;
                margin-bottom: 2rem;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            }
            .card h2 {
                color: #2d3748;
                font-size: 1.3rem;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 15px 0;
                padding: 10px;
                background: rgba(247, 250, 252, 0.8);
                border-radius: 8px;
                transition: background 0.2s ease;
            }
            .metric:hover {
                background: rgba(237, 242, 247, 0.9);
            }
            .metric-label {
                font-weight: 500;
                color: #4a5568;
            }
            .metric-value {
                font-weight: bold;
                color: #2563eb;
                font-size: 1.1rem;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #10b981;
                border-radius: 50%;
                margin-left: 10px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .loading {
                text-align: center;
                color: #718096;
                font-style: italic;
            }
            .last-updated {
                text-align: center;
                color: #a0aec0;
                font-size: 0.9rem;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Comprehensive Dashboard <span class="status-indicator"></span></h1>
            <div class="dashboard">
                <div class="card">
                    <h2>📊 System Metrics</h2>
                    <div id="system-metrics" class="loading">Loading...</div>
                </div>
                <div class="card">
                    <h2>📈 Application Stats</h2>
                    <div id="app-stats" class="loading">Loading...</div>
                </div>
                <div class="card">
                    <h2>💰 Revenue Data</h2>
                    <div id="revenue-data" class="loading">Loading...</div>
                </div>
                <div class="card">
                    <h2>🎯 Performance</h2>
                    <div id="performance-data" class="loading">Loading...</div>
                </div>
            </div>
            <div class="last-updated" id="last-updated"></div>
        </div>
        
        <script>
            async function loadDashboardData() {
                try {
                    const response = await fetch('/api/comprehensive/dashboard/overview');
                    const data = await response.json();
                    
                    // Update system metrics
                    const systemMetrics = document.getElementById('system-metrics');
                    systemMetrics.innerHTML = `
                        <div class="metric">
                            <span class="metric-label">CPU Usage:</span>
                            <span class="metric-value">${data.system_metrics.cpu_usage}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory Usage:</span>
                            <span class="metric-value">${data.system_metrics.memory_usage}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Disk Usage:</span>
                            <span class="metric-value">${data.system_metrics.disk_usage}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Connections:</span>
                            <span class="metric-value">${data.system_metrics.active_connections}</span>
                        </div>
                    `;
                    
                    // Update app stats
                    const appStats = document.getElementById('app-stats');
                    appStats.innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Total Requests:</span>
                            <span class="metric-value">${data.application_stats.total_requests.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Requests/Min:</span>
                            <span class="metric-value">${data.application_stats.requests_per_minute}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Error Rate:</span>
                            <span class="metric-value">${(data.application_stats.error_rate * 100).toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Users:</span>
                            <span class="metric-value">${data.application_stats.active_users.toLocaleString()}</span>
                        </div>
                    `;
                    
                    // Update revenue data
                    const revenueData = document.getElementById('revenue-data');
                    revenueData.innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Daily Revenue:</span>
                            <span class="metric-value">$${data.revenue_data.daily_revenue.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Monthly Revenue:</span>
                            <span class="metric-value">$${data.revenue_data.monthly_revenue.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Conversion Rate:</span>
                            <span class="metric-value">${data.revenue_data.conversion_rate}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Subscriptions:</span>
                            <span class="metric-value">${data.revenue_data.active_subscriptions}</span>
                        </div>
                    `;
                    
                    // Update performance data
                    const performanceData = document.getElementById('performance-data');
                    performanceData.innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Avg Response Time:</span>
                            <span class="metric-value">${data.application_stats.avg_response_time}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Users:</span>
                            <span class="metric-value">${data.application_stats.total_users.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">System Status:</span>
                            <span class="metric-value" style="color: #10b981;">${data.status.toUpperCase()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Uptime:</span>
                            <span class="metric-value">${Math.floor(data.system_metrics.uptime_seconds / 3600)}h</span>
                        </div>
                    `;
                    
                    // Update last updated time
                    const lastUpdated = document.getElementById('last-updated');
                    lastUpdated.textContent = `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                    document.querySelectorAll('.loading').forEach(el => {
                        el.innerHTML = '<div style="color: #e53e3e;">❌ Error loading data</div>';
                    });
                }
            }
            
            // Load data on page load and refresh every 30 seconds
            loadDashboardData();
            setInterval(loadDashboardData, 30000);
            
            // Add some interactivity
            document.addEventListener('DOMContentLoaded', function() {
                console.log('🚀 Dashboard loaded successfully!');
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/")
async def root():
    return {"message": "Dashboard Server Running", "dashboard_url": "/dashboard"}


if __name__ == "__main__":
    # DEBUG_REMOVED: print("🚀 Starting Simple Dashboard Server...")
    # DEBUG_REMOVED: print("📊 Dashboard: http://localhost:8000/dashboard")
    # DEBUG_REMOVED: print("🔗 API: http://localhost:8000/api/comprehensive/dashboard/overview")
    # DEBUG_REMOVED: print("Note: This is a mock server for demonstration purposes.")
    print("Routes registered:", len(app.routes))
    # Mock server - would need actual web server implementation
    # uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
