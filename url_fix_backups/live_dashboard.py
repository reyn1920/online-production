import os
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse


class LiveDashboard:
    """Live Dashboard FastAPI Application with automatic port detection"""

    def __init__(self):
        self.app = FastAPI(
            title="Live Dashboard",
            description="Real - time monitoring and control dashboard",
            version="1.0.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard page"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title > Live Dashboard</title>
                <meta charset="utf - 8">
                <meta name="viewport" content="width = device - width, initial - scale = 1">
                <style>
                    body {
                        font - family: -apple - system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans - serif;
                        margin: 0;
                        padding: 20px;
                        background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min - height: 100vh;
                    }
                    .container {
                        max - width: 1200px;
                        margin: 0 auto;
                    }
                    .header {
                        text - align: center;
                        margin - bottom: 40px;
                    }
                    .header h1 {
                        font - size: 3rem;
                        margin: 0;
                        text - shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    .status - grid {
                        display: grid;
                        grid - template - columns: repeat(auto - fit,
    minmax(300px,
    1fr));
                        gap: 20px;
                        margin - bottom: 40px;
                    }
                    .status - card {
                        background: rgba(255,255,255,0.1);
                        backdrop - filter: blur(10px);
                        border - radius: 15px;
                        padding: 25px;
                        border: 1px solid rgba(255,255,255,0.2);
                    }
                    .status - card h3 {
                        margin: 0 0 15px 0;
                        font - size: 1.2rem;
                    }
                    .status - indicator {
                        display: inline - block;
                        width: 12px;
                        height: 12px;
                        border - radius: 50%;
                        background: #4CAF50;
                        margin - right: 8px;
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    .metric {
                        display: flex;
                        justify - content: space - between;
                        margin: 10px 0;
                        padding: 8px 0;
                        border - bottom: 1px solid rgba(255,255,255,0.1);
                    }
                    .metric:last - child {
                        border - bottom: none;
                    }
                    .refresh - btn {
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.3);
                        color: white;
                        padding: 12px 24px;
                        border - radius: 8px;
                        cursor: pointer;
                        font - size: 1rem;
                        transition: all 0.3s ease;
                    }
                    .refresh - btn:hover {
                        background: rgba(255,255,255,0.3);
                        transform: translateY(-2px);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 Live Dashboard</h1>
                        <p > Real - time system monitoring and control</p>
                        <button class="refresh - btn" onclick="location.reload()">🔄 Refresh</button>
                    </div>

                    <div class="status - grid">
                        <div class="status - card">
                            <h3><span class="status - indicator"></span > System Status</h3>
                            <div class="metric">
                                <span > Status:</span>
                                <span>🟢 Online</span>
                            </div>
                            <div class="metric">
                                <span > Uptime:</span>
                                <span id="uptime">Loading...</span>
                            </div>
                            <div class="metric">
                                <span > Port:</span>
                                <span > Auto - detected</span>
                            </div>
                        </div>

                        <div class="status - card">
                            <h3><span class="status - indicator"></span > Performance</h3>
                            <div class="metric">
                                <span > Response Time:</span>
                                <span>< 100ms</span>
                            </div>
                            <div class="metric">
                                <span > Memory Usage:</span>
                                <span > Normal</span>
                            </div>
                            <div class="metric">
                                <span > CPU Usage:</span>
                                <span > Low</span>
                            </div>
                        </div>

                        <div class="status - card">
                            <h3><span class="status - indicator"></span > API Endpoints</h3>
                            <div class="metric">
                                <span > Health Check:</span>
                                <span><a href="/health" style="color: #4CAF50;">/health</a></span>
                            </div>
                            <div class="metric">
                                <span > Status API:</span>
                                <span><a href="/api / status" style="color: #4CAF50;">/api / status</a></span>
                            </div>
                            <div class="metric">
                                <span > Metrics API:</span>
                                <span><a href="/api / metrics" style="color: #4CAF50;">/api / metrics</a></span>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    // Update uptime
                    function updateUptime() {
                        fetch('/api / status')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('uptime').textContent = data.uptime || 'Unknown';
                            })
                            .catch(error => {
                                document.getElementById('uptime').textContent = 'Error loading';
                            });
                    }

                    // Update uptime on load and every 30 seconds
                    updateUptime();
                    setInterval(updateUptime, 30000);
                </script>
            </body>
            </html>
            """

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "Live Dashboard",
                "version": "1.0.0",
            }

        @self.app.get("/api / status")
        async def get_status():
            """Get system status"""
            uptime = datetime.now() - datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return {
                "status": "online",
                "uptime": str(uptime).split(".")[0],  # Remove microseconds
                "timestamp": datetime.now().isoformat(),
                "port_detection": "automatic",
                "environment": os.getenv("ENVIRONMENT", "development"),
            }

        @self.app.get("/api / metrics")
        async def get_metrics():
            """Get system metrics"""
            return {
                "cpu_usage": "low",
                "memory_usage": "normal",
                "response_time": "< 100ms",
                "active_connections": 1,
                "requests_per_minute": 0,
                "timestamp": datetime.now().isoformat(),
            }


if __name__ == "__main__":
    import os
    import socket

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

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
    print(f"Dashboard starting on http://{host}:{port}")
    uvicorn.run(LiveDashboard().app, host=host, port=port, reload=False, log_level="info")
