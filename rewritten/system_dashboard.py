#!/usr/bin/env python3
"""
TRAE.AI System Management Dashboard
Provides a web interface to monitor and control all system services.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

except ImportError:
    print("FastAPI not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "jinja2"])

    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates


class SystemMonitor:
    """System monitoring and management class"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.pid_file = self.project_root / "service.pid"
        self.log_file = self.project_root / "startup_system.log"
        self.service_log = self.project_root / "service.log"
        self.error_log = self.project_root / "service.error.log"

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # CPU and Memory info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network info
            network = psutil.net_io_counters()

            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            # Service status
            services = {
                "main_app": self.is_service_running("uvicorn")
                or self.is_service_running("main:app"),
                "ollama": self.is_service_running("ollama"),
                "chrome": self.is_service_running("chrome"),
                "dashboard": self.is_service_running("system_dashboard"),
            }

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "uptime": str(uptime).split(".")[0],
                "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                "services": services,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get TRAE.AI service status"""
        try:
            if not self.pid_file.exists():
                return {
                    "status": "stopped",
                    "pid": None,
                    "uptime": None,
                    "health": "unknown",
                }

            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Check if process is running
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    create_time = datetime.fromtimestamp(process.create_time())
                    uptime = datetime.now() - create_time

                    # Check health endpoint
                    health_status = self.check_health_endpoint()

                    return {
                        "status": "running",
                        "pid": pid,
                        "uptime": str(uptime).split(".")[0],
                        "health": health_status,
                        "cpu_percent": process.cpu_percent(),
                        "memory_percent": process.memory_percent(),
                        "memory_info": process.memory_info()._asdict(),
                        "num_threads": process.num_threads(),
                        "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                else:
                    return {
                        "status": "stopped",
                        "pid": None,
                        "uptime": None,
                        "health": "down",
                    }
            except psutil.NoSuchProcess:
                return {
                    "status": "stopped",
                    "pid": None,
                    "uptime": None,
                    "health": "down",
                }
        except Exception as e:
            return {"status": "error", "error": str(e), "health": "unknown"}

    def check_health_endpoint(self) -> str:
        """Check if the health endpoint is responding"""
        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                return "healthy"
            else:
                return "unhealthy"
        except Exception:
            return "unreachable"

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running by name"""
        try:
            for proc in psutil.process_iter(["name", "cmdline"]):
                try:
                    if service_name.lower() in proc.info["name"].lower():
                        return True
                    if proc.info["cmdline"]:
                        cmdline = " ".join(proc.info["cmdline"]).lower()
                        if service_name.lower() in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False

    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes related to the application"""
        processes = []
        keywords = ["python", "uvicorn", "fastapi", "node", "npm", "trae"]

        for proc in psutil.process_iter(
            ["pid", "name", "cmdline", "cpu_percent", "memory_percent"]
        ):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if any(keyword in cmdline.lower() for keyword in keywords):
                    processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": (cmdline[:100] + "..." if len(cmdline) > 100 else cmdline),
                            "cpu_percent": proc.info["cpu_percent"],
                            "memory_percent": proc.info["memory_percent"],
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def get_log_tail(self, log_file: Path, lines: int = 50) -> List[str]:
        """Get last N lines from log file"""
        try:
            if not log_file.exists():
                return []

            with open(log_file, "r") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [f"Error reading log: {str(e)}"]

    def execute_command(self, command: str, service: str = "main") -> Dict[str, Any]:
        """Execute system command safely"""
        try:
            if service == "main":
                allowed_commands = {
                    "start": "./start_app.sh start",
                    "stop": "./start_app.sh stop",
                    "restart": "./start_app.sh restart",
                    "status": "./start_app.sh status",
                    "install - service": "./start_app.sh install - service",
                    "uninstall - service": "./start_app.sh uninstall - service",
                }

                if command not in allowed_commands:
                    return {"error": "Command not allowed"}

                result = subprocess.run(
                    allowed_commands[command],
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            elif service == "ollama":
                if command == "start":
                    if not self.is_service_running("ollama"):
                        subprocess.Popen(
                            ["ollama", "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        return {
                            "success": True,
                            "stdout": "Ollama service started",
                            "stderr": "",
                        }
                    else:
                        return {
                            "success": True,
                            "stdout": "Ollama is already running",
                            "stderr": "",
                        }

                elif command == "stop":
                    subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
                    return {
                        "success": True,
                        "stdout": "Ollama service stopped",
                        "stderr": "",
                    }

                elif command == "restart":
                    subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
                    time.sleep(2)
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return {
                        "success": True,
                        "stdout": "Ollama service restarted",
                        "stderr": "",
                    }

            elif service == "chrome":
                if command == "start":
                    if not self.is_service_running("chrome"):
                        subprocess.Popen(["open", "-a", "Google Chrome"])
                        time.sleep(2)
                        # Open essential tabs
                        essential_sites = [
                            "http://localhost:8000",
                            "http://localhost:9000",
                            "https://github.com",
                            "https://netlify.com",
                            "https://openai.com",
                        ]
                        for site in essential_sites:
                            subprocess.Popen(["open", "-u", site])
                        return {
                            "success": True,
                            "stdout": "Chrome started with essential tabs",
                            "stderr": "",
                        }
                    else:
                        return {
                            "success": True,
                            "stdout": "Chrome is already running",
                            "stderr": "",
                        }

                elif command == "stop":
                    subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
                    return {"success": True, "stdout": "Chrome stopped", "stderr": ""}

            return {"error": "Invalid action or service"}

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}


# Initialize FastAPI app
app = FastAPI(title="TRAE.AI System Dashboard", version="1.0.0")
monitor = SystemMonitor()

# Create templates directory and HTML template
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create the dashboard HTML template
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title > TRAE.AI System Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font - awesome/6.0.0/css/all.min.css">
</head>
<body class="bg - gray - 100 min - h-screen" x - data="dashboard()">
    <div class="container mx - auto px - 4 py - 8">
        <!-- Header -->
        <div class="bg - white rounded - lg shadow - md p - 6 mb - 6">
            <div class="flex items - center justify - between">
                <div>
                    <h1 class="text - 3xl font - bold text - gray - 800">TRAE.AI System Dashboard</h1>
                    <p class="text - gray - 600 mt - 2">Monitor \
    and manage your TRAE.AI application</p>
                </div>
                <div class="flex space - x-2">
                    <button @click="refreshData()" class="bg - blue - 500 hover:bg - blue - 600 text - white px - 4 py - 2 rounded - lg">
                        <i class="fas fa - sync - alt mr - 2"></i> Refresh
                    </button>
                    <div class="text - sm text - gray - 500">
                        Last updated: <span x - text="lastUpdate"></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Service Status -->
        <div class="grid grid - cols - 1 md:grid - cols - 2 lg:grid - cols - 4 gap - 6 mb - 6">
            <div class="bg - white rounded - lg shadow - md p - 6">
                <div class="flex items - center justify - between">
                    <div>
                        <h3 class="text - lg font - semibold text - gray - 800">Service Status</h3>
                        <p class="text - 2xl font - bold" :class="serviceStatus.status === 'running' ? 'text - green - 600' : 'text - red - 600'" x - text="serviceStatus.status || 'Unknown'"></p>
                    </div>
                    <div class="text - 3xl" :class="serviceStatus.status === 'running' ? 'text - green - 500' : 'text - red - 500'">
                        <i class="fas fa - circle"></i>
                    </div>
                </div>
                <div class="mt - 4 space - y-2">
                    <button @click="executeCommand('start', 'main')" class="w - full bg - green - 500 hover:bg - green - 600 text - white px - 3 py - 1 rounded text - sm">
                        <i class="fas fa - play mr - 1"></i> Start
                    </button>
                    <button @click="executeCommand('stop', 'main')" class="w - full bg - red - 500 hover:bg - red - 600 text - white px - 3 py - 1 rounded text - sm">
                        <i class="fas fa - stop mr - 1"></i> Stop
                    </button>
                    <button @click="executeCommand('restart', 'main')" class="w - full bg - yellow - 500 hover:bg - yellow - 600 text - white px - 3 py - 1 rounded text - sm">
                        <i class="fas fa - redo mr - 1"></i> Restart
                    </button>
                    <div class="mt - 2 space - y-1">
                        <button @click="executeCommand('start', 'ollama')" class="w - full bg - purple - 500 hover:bg - purple - 600 text - white px - 2 py - 1 rounded text - xs">
                            <i class="fas fa - robot mr - 1"></i> Start Ollama
                        </button>
                        <button @click="executeCommand('start', 'chrome')" class="w - full bg - blue - 500 hover:bg - blue - 600 text - white px - 2 py - 1 rounded text - xs">
                            <i class="fab fa - chrome mr - 1"></i> Start Chrome
                        </button>
                    </div>
                </div>
            </div>

            <div class="bg - white rounded - lg shadow - md p - 6">
                <div class="flex items - center justify - between">
                    <div>
                        <h3 class="text - lg font - semibold text - gray - 800">CPU Usage</h3>
                        <p class="text - 2xl font - bold text - blue - 600" x - text="systemInfo.cpu?.percent?.toFixed(1) + '%' || 'N/A'"></p>
                    </div>
                    <div class="text - 3xl text - blue - 500">
                        <i class="fas fa - microchip"></i>
                    </div>
                </div>
            </div>

            <div class="bg - white rounded - lg shadow - md p - 6">
                <div class="flex items - center justify - between">
                    <div>
                        <h3 class="text - lg font - semibold text - gray - 800">Memory Usage</h3>
                        <p class="text - 2xl font - bold text - purple - 600" x - text="systemInfo.memory?.percent?.toFixed(1) + '%' || 'N/A'"></p>
                    </div>
                    <div class="text - 3xl text - purple - 500">
                        <i class="fas fa - memory"></i>
                    </div>
                </div>
            </div>

            <div class="bg - white rounded - lg shadow - md p - 6">
                <div class="flex items - center justify - between">
                    <div>
                        <h3 class="text - lg font - semibold text - gray - 800">Health Status</h3>
                        <p class="text - 2xl font - bold" :class="serviceStatus.health === 'healthy' ? 'text - green - 600' : 'text - red - 600'" x - text="serviceStatus.health || 'Unknown'"></p>
                    </div>
                    <div class="text - 3xl" :class="serviceStatus.health === 'healthy' ? 'text - green - 500' : 'text - red - 500'">
                        <i class="fas fa - heartbeat"></i>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detailed Information -->
        <div class="grid grid - cols - 1 lg:grid - cols - 2 gap - 6 mb - 6">
            <!-- Service Details -->
            <div class="bg - white rounded - lg shadow - md p - 6">
                <h3 class="text - xl font - semibold text - gray - 800 mb - 4">Service Details</h3>
                <div class="space - y - 3">
                    <div class="flex justify - between">
                        <span class="text - gray - 600">PID:</span>
                        <span class="font - mono" x - text="serviceStatus.pid || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Uptime:</span>
                        <span class="font - mono" x - text="serviceStatus.uptime || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">CPU %:</span>
                        <span class="font - mono" x - text="serviceStatus.cpu_percent?.toFixed(2) + '%' || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Memory %:</span>
                        <span class="font - mono" x - text="serviceStatus.memory_percent?.toFixed(2) + '%' || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Threads:</span>
                        <span class="font - mono" x - text="serviceStatus.num_threads || 'N/A'"></span>
                    </div>
                </div>

                <!-- Service Status Indicators -->
                <div class="mt - 4 pt - 4 border - t border - gray - 200">
                    <h4 class="text - sm font - medium text - gray - 700 mb - 2">Service Status</h4>
                    <div class="space - y - 2">
                        <div class="flex items - center justify - between">
                            <span class="text - sm text - gray - 600">Main App:</span>
                            <span class="flex items - center">
                                <div class="w - 2 h - 2 rounded - full mr - 2" :class="systemInfo.services?.main_app ? 'bg - green - 400' : 'bg - red - 400'"></div>
                                <span class="text - sm" x - text="systemInfo.services?.main_app ? 'Running' : 'Stopped'"></span>
                            </span>
                        </div>
                        <div class="flex items - center justify - between">
                            <span class="text - sm text - gray - 600">Ollama:</span>
                            <span class="flex items - center">
                                <div class="w - 2 h - 2 rounded - full mr - 2" :class="systemInfo.services?.ollama ? 'bg - green - 400' : 'bg - red - 400'"></div>
                                <span class="text - sm" x - text="systemInfo.services?.ollama ? 'Running' : 'Stopped'"></span>
                            </span>
                        </div>
                        <div class="flex items - center justify - between">
                            <span class="text - sm text - gray - 600">Chrome:</span>
                            <span class="flex items - center">
                                <div class="w - 2 h - 2 rounded - full mr - 2" :class="systemInfo.services?.chrome ? 'bg - green - 400' : 'bg - red - 400'"></div>
                                <span class="text - sm" x - text="systemInfo.services?.chrome ? 'Running' : 'Stopped'"></span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Information -->
            <div class="bg - white rounded - lg shadow - md p - 6">
                <h3 class="text - xl font - semibold text - gray - 800 mb - 4">System Information</h3>
                <div class="space - y - 3">
                    <div class="flex justify - between">
                        <span class="text - gray - 600">CPU Cores:</span>
                        <span class="font - mono" x - text="systemInfo.cpu?.count || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Total Memory:</span>
                        <span class="font - mono" x - text="formatBytes(systemInfo.memory?.total) || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Available Memory:</span>
                        <span class="font - mono" x - text="formatBytes(systemInfo.memory?.available) || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">Disk Usage:</span>
                        <span class="font - mono" x - text="systemInfo.disk?.percent?.toFixed(1) + '%' || 'N/A'"></span>
                    </div>
                    <div class="flex justify - between">
                        <span class="text - gray - 600">System Uptime:</span>
                        <span class="font - mono" x - text="systemInfo.uptime || 'N/A'"></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Running Processes -->
        <div class="bg - white rounded - lg shadow - md p - 6 mb - 6">
            <h3 class="text - xl font - semibold text - gray - 800 mb - 4">Related Processes</h3>
            <div class="overflow - x - auto">
                <table class="min - w - full table - auto">
                    <thead>
                        <tr class="bg - gray - 50">
                            <th class="px - 4 py - 2 text - left text - sm font - medium text - gray - 700">PID</th>
                            <th class="px - 4 py - 2 text - left text - sm font - medium text - gray - 700">Name</th>
                            <th class="px - 4 py - 2 text - left text - sm font - medium text - gray - 700">Command</th>
                            <th class="px - 4 py - 2 text - left text - sm font - medium text - gray - 700">CPU %</th>
                            <th class="px - 4 py - 2 text - left text - sm font - medium text - gray - 700">Memory %</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template x - for="process in processes" :key="process.pid">
                            <tr class="border - t">
                                <td class="px - 4 py - 2 text - sm font - mono" x - text="process.pid"></td>
                                <td class="px - 4 py - 2 text - sm" x - text="process.name"></td>
                                <td class="px - 4 py - 2 text - sm font - mono text - gray - 600" x - text="process.cmdline"></td>
                                <td class="px - 4 py - 2 text - sm" x - text="process.cpu_percent?.toFixed(1) + '%'"></td>
                                <td class="px - 4 py - 2 text - sm" x - text="process.memory_percent?.toFixed(1) + '%'"></td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Logs -->
        <div class="bg - white rounded - lg shadow - md p - 6">
            <div class="flex items - center justify - between mb - 4">
                <h3 class="text - xl font - semibold text - gray - 800">Recent Logs</h3>
                <div class="space - x - 2">
                    <button @click="currentLogType = 'system'" :class="currentLogType === 'system' ? 'bg - blue - 500 text - white' : 'bg - gray - 200 text - gray - 700'" class="px - 3 py - 1 rounded text - sm">
                        System
                    </button>
                    <button @click="currentLogType = 'service'" :class="currentLogType === 'service' ? 'bg - blue - 500 text - white' : 'bg - gray - 200 text - gray - 700'" class="px - 3 py - 1 rounded text - sm">
                        Service
                    </button>
                    <button @click="currentLogType = 'error'" :class="currentLogType === 'error' ? 'bg - blue - 500 text - white' : 'bg - gray - 200 text - gray - 700'" class="px - 3 py - 1 rounded text - sm">
                        Errors
                    </button>
                </div>
            </div>
            <div class="bg - gray - 900 text - green - 400 p - 4 rounded - lg font - mono text - sm max - h - 96 overflow - y - auto">
                <template x - for="line in logs[currentLogType] || []" :key="$index">
                    <div x - text="line.trim()"></div>
                </template>
            </div>
        </div>
    </div>

    <script>
        function dashboard() {
            return {
                systemInfo: {},
                    serviceStatus: {},
                    processes: [],
                    logs: {
                    system: [],
                        service: [],
                        error: []
                },
                    currentLogType: 'system',
                    lastUpdate: '',

                init() {
                    this.refreshData();
                    setInterval(() => this.refreshData(),
    5000);//Auto - refresh every 5 seconds
                },

                async refreshData() {
                    try {
                        const [systemResponse,
    serviceResponse,
    processesResponse,
    logsResponse] = await Promise.all([
                            fetch("/api/system'),
                                fetch("/api/service'),
                                fetch("/api/processes'),
                                fetch("/api/logs')
                        ]);

                        this.systemInfo = await systemResponse.json();
                        this.serviceStatus = await serviceResponse.json();
                        this.processes = await processesResponse.json();
                        this.logs = await logsResponse.json();
                        this.lastUpdate = new Date().toLocaleTimeString();
                    } catch (error) {
                        console.error('Failed to refresh data:', error);
                    }
                },

                async executeCommand(command, service = 'main') {
                    try {
                        const response = await fetch("/api/command', {
                            method: 'POST',
                                headers: {
                                'Content - Type': 'application/json'
                            },
                                body: JSON.stringify({ command, service })
                        });

                        const result = await response.json();
                        if (result.success) {
                            alert(`${service} service ${command} executed successfully`);
                        } else {
                            alert(`${service} service ${command} failed: ` + (result.stderr || result.error));
                        }//Refresh data after command
                            setTimeout(() => this.refreshData(), 1000);
                    } catch (error) {
                        alert('Failed to execute command: ' + error.message);
                    }
                },

                formatBytes(bytes) {
                    if (!bytes) return 'N/A';
                    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
                    if (bytes === 0) return '0 Bytes';
                    const i = Math.floor(Math.log(bytes)/Math.log(1024));
                    return Math.round(bytes/Math.pow(1024,
    i) * 100)/100 + ' ' + sizes[i];
                }
            }
        }
    </script>
</body>
</html>
"""

# Write the HTML template
with open(templates_dir / "dashboard.html", "w") as f:
    f.write(dashboard_html)

templates = Jinja2Templates(directory=str(templates_dir))


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/system")
async def get_system_info():
    """Get system information"""
    return monitor.get_system_info()


@app.get("/api/service")
async def get_service_status():
    """Get service status"""
    return monitor.get_service_status()


@app.get("/api/processes")
async def get_processes():
    """Get running processes"""
    return monitor.get_running_processes()


@app.get("/api/logs")
async def get_logs():
    """Get log files"""
    return {
        "system": monitor.get_log_tail(monitor.log_file),
        "service": monitor.get_log_tail(monitor.service_log),
        "error": monitor.get_log_tail(monitor.error_log),
    }


@app.post("/api/command")
async def execute_command(request: Request):
    """Execute system command"""
    data = await request.json()
    command = data.get("command")
    service = data.get("service", "main")

    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    result = monitor.execute_command(command, service)
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TRAE.AI System Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto - reload")

    args = parser.parse_args()

    print(f"Starting TRAE.AI System Dashboard on http://{args.host}:{args.port}")
    print("Dashboard features:")
    print("  - Real - time system monitoring")
    print("  - Service control (start/stop/restart)")
    print("  - Process monitoring")
    print("  - Log viewing")
    print("  - Health checks")

    uvicorn.run("system_dashboard:app", host=args.host, port=args.port, reload=args.reload)
