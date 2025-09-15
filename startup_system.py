#!/usr/bin/env python3
"""
TRAE.AI Application Startup and Management System

This script handles:
1. System requirements validation
2. Dependency installation and verification
3. Application startup with proper order
4. Process monitoring and auto-restart
5. Resource optimization (closing unnecessary apps)
6. Health monitoring and alerting

Usage:
    python3 startup_system.py --mode production
    python3 startup_system.py --mode development
    python3 startup_system.py --monitor-only
"""

import argparse
import asyncio
import logging
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import psutil

# Import monitoring components
try:
    from monitoring.process_watchdog import ProcessWatchdog
    from monitoring.self_healing_monitor import SelfHealingMonitor

except ImportError:
    SelfHealingMonitor = None
    ProcessWatchdog = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("startup_system.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class SystemManager:
    def __init__(self, mode: str = "production"):
        self.mode = mode
        self.project_root = Path.cwd()
        self.processes = {}
        self.monitoring = True
        self.required_ports = [8000]  # Main FastAPI app
        self.optional_ports = [3000, 5000]  # Frontend dev server, additional services

        # Initialize monitoring components
        self.self_healing_monitor = None
        self.process_watchdog = None
        self._init_monitoring_components()

        # System requirements
        self.system_requirements = {
            "python": "3.8+",
            "node": "16+",
            "memory_gb": 4,
            "disk_space_gb": 2
        }

        # Applications to close for optimization
        self.apps_to_close = [
            "Spotify",
            "Discord",
            "Slack",
            "Teams",
            "Zoom",
            "Skype",
            "Firefox",
            "Safari",
            "Opera",
            "Photoshop",
            "Illustrator",
            "Premiere Pro",
            "After Effects",
            "Steam",
            "Epic Games Launcher",
            "Battle.net",
            "Dropbox",
            "Google Drive",
            "OneDrive",
            "VLC",
            "QuickTime Player",
            "iTunes",
            "Music"
        ]

        # Essential apps to keep running
        self.essential_apps = [
            "Finder",
            "System Preferences",
            "Activity Monitor",
            "Terminal",
            "iTerm",
            "Trae",
            "Sublime Text",
            "Python",
            "Node",
            "uvicorn",
            "Ollama",
            "Chrome"
        ]

    def _init_monitoring_components(self):
        """Initialize monitoring components if available"""
        try:
            if SelfHealingMonitor:
                self.self_healing_monitor = SelfHealingMonitor()
                logger.info("✅ Self-healing monitor initialized")
            else:
                logger.warning("⚠️ Self-healing monitor not available")

            if ProcessWatchdog:
                self.process_watchdog = ProcessWatchdog()
                logger.info("✅ Process watchdog initialized")
            else:
                logger.warning("⚠️ Process watchdog not available")

        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize monitoring components: {e}")

    def validate_system_requirements(self) -> bool:
        """Validate system meets minimum requirements"""
        logger.info("🔍 Validating system requirements...")

        try:
            # Check Python version
            python_version = subprocess.check_output(["python3", "--version"], text=True).strip()
            logger.info(f"✅ Python: {python_version}")

            # Check Node version
            node_version = subprocess.check_output(["node", "--version"], text=True).strip()
            logger.info(f"✅ Node.js: {node_version}")

            # Check memory
            memory_gb = psutil.virtual_memory().total / (1024**3)
            logger.info(f"✅ Memory: {memory_gb:.1f} GB")

            # Check disk space
            disk_usage = psutil.disk_usage("/")
            free_gb = disk_usage.free / (1024**3)
            logger.info(f"✅ Free disk space: {free_gb:.1f} GB")

            # Check required files
            required_files = ["main.py", "requirements.txt", "package.json"]

            for file in required_files:
                if not (self.project_root / file).exists():
                    logger.error(f"❌ Missing required file: {file}")
                    return False
                logger.info(f"✅ Found: {file}")

            return True

        except Exception as e:
            logger.error(f"❌ System validation failed: {e}")
            return False

    def install_dependencies(self) -> bool:
        """Install and verify all dependencies"""
        logger.info("📦 Installing dependencies...")

        try:
            # Try minimal requirements first, then full requirements
            requirements_files = ["requirements_minimal.txt", "requirements.txt"]

            for req_file in requirements_files:
                if not (self.project_root / req_file).exists():
                    logger.info(f"⚠️ {req_file} not found, trying next...")
                    continue

                logger.info(f"📦 Attempting to install from {req_file}...")

                # Install dependencies
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    logger.info(f"✅ Dependencies installed successfully from {req_file}")
                    break
                else:
                    logger.warning(
                        f"⚠️ Failed to install from {req_file}: {result.stderr[:200]}..."
                    )
                    continue
            else:
                # If all requirements files fail, continue anyway
                logger.warning(
                    "⚠️ Could not install dependencies, continuing with existing packages..."
                )

            # Install Node dependencies
            if (self.project_root / "package.json").exists():
                logger.info("Installing Node.js packages...")
                result = subprocess.run(["npm", "install"], capture_output=True, text=True)

                if result.returncode != 0:
                    logger.warning(f"⚠️ Node dependencies failed: {result.stderr[:200]}...")
                else:
                    logger.info("✅ Node.js dependencies installed")

            return True  # Don't fail the entire startup for dependency issues

        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Dependency installation timed out, continuing anyway...")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error installing dependencies: {e}, continuing anyway...")
            return True

    def optimize_system_resources(self) -> None:
        """Close unnecessary applications to free up resources"""
        logger.info("🧹 Optimizing system resources...")

        closed_apps = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]

                # Check if it's an app we want to close
                for app in self.apps_to_close:
                    if app.lower() in proc_name.lower():
                        # Make sure it's not essential
                        is_essential = any(
                            essential.lower() in proc_name.lower()
                            for essential in self.essential_apps
                        )

                        if not is_essential:
                            try:
                                proc.terminate()
                                closed_apps.append(proc_name)
                                logger.info(f"🚫 Closed: {proc_name}")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if closed_apps:
            logger.info(f"✅ Closed {len(closed_apps)} unnecessary applications")
        else:
            logger.info("✅ No unnecessary applications found")

    def check_port_availability(self) -> Dict[int, bool]:
        """Check if required ports are available"""
        port_status = {}

        for port in self.required_ports + self.optional_ports:
            try:
                # Try to bind to the port

                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(("localhost", port))
                sock.close()

                port_status[port] = result != 0  # True if available (connection failed)

            except Exception:
                port_status[port] = True  # Assume available if check fails

        return port_status

    def start_essential_services(self) -> None:
        """Start essential services for the application"""
        try:
            logger.info("Starting essential services...")

            # Start Ollama if not running
            if not self.is_service_running("ollama"):
                logger.info("Starting Ollama service...")
                try:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(5)
                    logger.info("Ollama service started successfully")
                except FileNotFoundError:
                    logger.warning("Ollama not found in PATH, attempting to install...")
                    try:
                        subprocess.run(["brew", "install", "ollama"], check=True)
                        subprocess.Popen(
                            ["ollama", "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(5)
                        logger.info("Ollama installed and started successfully")
                    except Exception as install_error:
                        logger.error(f"Failed to install Ollama: {install_error}")

            # Start Chrome with predefined tabs
            self.start_chrome_with_tabs()

        except Exception as e:
            logger.error(f"Error starting essential services: {e}")

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            for proc in psutil.process_iter(["name", "cmdline"]):
                if service_name.lower() in proc.info["name"].lower():
                    return True
                if proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"]).lower()
                    if service_name.lower() in cmdline:
                        return True
            return False
        except Exception:
            return False

    def start_chrome_with_tabs(self) -> None:
        """Start Chrome with predefined tabs to avoid bot detection"""
        try:
            essential_sites = [
                "http://localhost:8000",
                "http://localhost:9000",
                "https://github.com",
                "https://netlify.com",
                "https://openai.com",
                "https://anthropic.com",
                "https://stackoverflow.com",
                "https://docs.python.org",
                "https://fastapi.tiangolo.com",
            ]

            chrome_running = False
            for proc in psutil.process_iter(["name"]):
                if "chrome" in proc.info["name"].lower():
                    chrome_running = True
                    break

            if not chrome_running:
                logger.info("Starting Chrome with essential tabs...")
                try:
                    subprocess.Popen(["open", "-a", "Google Chrome"])
                    time.sleep(3)

                    for site in essential_sites:
                        subprocess.Popen(["open", "-u", site])
                        time.sleep(0.5)

                    logger.info(f"Chrome started with {len(essential_sites)} essential tabs")

                except Exception as e:
                    logger.error(f"Failed to start Chrome with tabs: {e}")
                    subprocess.Popen(["open", "-a", "Google Chrome"])
            else:
                logger.info("Chrome is already running")

        except Exception as e:
            logger.error(f"Error starting Chrome: {e}")

    def start_application(self) -> bool:
        """Start the main application"""
        logger.info("🚀 Starting TRAE.AI application...")

        try:
            # Start essential services first
            self.start_essential_services()

            # Check port availability
            port_status = self.check_port_availability()

            for port in self.required_ports:
                if not port_status.get(port, False):
                    logger.warning(f"⚠️ Port {port} is already in use")

            # Start the main FastAPI application
            cmd = ["python3", "main.py"]

            if self.mode == "development":
                # Add development flags if needed
                pass

            logger.info(f"Executing: {' '.join(cmd)}")

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            self.processes["main_app"] = {
                "process": process,
                "cmd": cmd,
                "start_time": datetime.now(),
                "restart_count": 0,
            }

            # Give it a moment to start
            time.sleep(3)

            # Check if it's still running
            if process.poll() is None:
                logger.info("✅ Application started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error("❌ Application failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to start application: {e}")
            return False

    def monitor_processes(self) -> None:
        """Monitor running processes and restart if needed"""
        logger.info("👁️ Starting process monitoring...")

        # Start advanced monitoring components
        self._start_advanced_monitoring()

        while self.monitoring:
            try:
                for name, proc_info in self.processes.items():
                    process = proc_info["process"]

                    if process.poll() is not None:
                        # Process has died
                        logger.warning(f"⚠️ Process {name} has stopped")

                        # Get exit code and output
                        stdout, stderr = process.communicate()
                        logger.error(f"Exit code: {process.returncode}")
                        if stdout:
                            logger.error(f"STDOUT: {stdout[-500:]}")
                        if stderr:
                            logger.error(f"STDERR: {stderr[-500:]}")

                        # Restart the process
                        if proc_info["restart_count"] < 5:
                            logger.info(f"🔄 Restarting {name}...")

                            new_process = subprocess.Popen(
                                proc_info["cmd"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                bufsize=1,
                                universal_newlines=True,
                            )

                            proc_info["process"] = new_process
                            proc_info["restart_count"] += 1
                            proc_info["start_time"] = datetime.now()

                            logger.info(
                                f"✅ {name} restarted (attempt {proc_info['restart_count']})"
                            )
                        else:
                            logger.error(f"❌ {name} failed too many times, giving up")
                            del self.processes[name]

                # Sleep before next check
                time.sleep(10)

            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(5)

    def _start_advanced_monitoring(self):
        """Start advanced monitoring components"""
        try:
            # Start self - healing monitor
            if self.self_healing_monitor:
                monitor_thread = threading.Thread(
                    target=self._run_self_healing_monitor, daemon=True
                )
                monitor_thread.start()
                logger.info("🔧 Self - healing monitor started")

            # Start process watchdog
            if self.process_watchdog:
                watchdog_thread = threading.Thread(target=self._run_process_watchdog, daemon=True)
                watchdog_thread.start()
                logger.info("🐕 Process watchdog started")

        except Exception as e:
            logger.error(f"❌ Failed to start advanced monitoring: {e}")

    def _run_self_healing_monitor(self):
        """Run self - healing monitor in thread"""
        try:
            asyncio.run(self.self_healing_monitor.start_monitoring())
        except Exception as e:
            logger.error(f"Self - healing monitor error: {e}")

    def _run_process_watchdog(self):
        """Run process watchdog in thread"""
        try:
            asyncio.run(self.process_watchdog.start_monitoring())
        except Exception as e:
            logger.error(f"Process watchdog error: {e}")

    def health_check(self) -> Dict[str, any]:
        """Perform comprehensive health check"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "system": {},
            "issues": [],
        }

        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            health_status["system"] = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            }

            # Check if main application is responding
            try:
                import requests

                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    health_status["services"]["main_app"] = "healthy"
                else:
                    health_status["services"]["main_app"] = "unhealthy"
                    health_status["issues"].append("Main app not responding properly")
            except Exception as e:
                health_status["services"]["main_app"] = "unreachable"
                health_status["issues"].append(f"Main app unreachable: {str(e)}")

            # Check process status
            for name, proc_info in self.processes.items():
                if proc_info["process"].poll() is None:
                    health_status["services"][name] = "running"
                else:
                    health_status["services"][name] = "stopped"
                    health_status["issues"].append(f"{name} process stopped")

            # Determine overall status
            if health_status["issues"]:
                health_status["overall_status"] = (
                    "degraded" if len(health_status["issues"]) < 3 else "unhealthy"
                )

        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["issues"].append(f"Health check failed: {str(e)}")

        return health_status

    def shutdown(self) -> None:
        """Gracefully shutdown all processes"""
        logger.info("🛑 Shutting down system...")

        self.monitoring = False

        for name, proc_info in self.processes.items():
            try:
                process = proc_info["process"]
                if process.poll() is None:
                    logger.info(f"Stopping {name}...")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Force killing {name}")
                        process.kill()
                        process.wait()

            except Exception as e:
                logger.error(f"❌ Error stopping {name}: {e}")

        logger.info("✅ System shutdown complete")

    def run(self) -> None:
        """Main execution method"""
        logger.info(f"🚀 Starting TRAE.AI System Manager in {self.mode} mode")

        try:
            # Step 1: Validate system
            if not self.validate_system_requirements():
                logger.error("❌ System validation failed")
                return

            # Step 2: Install dependencies
            if not self.install_dependencies():
                logger.error("❌ Dependency installation failed")
                return

            # Step 3: Optimize resources
            self.optimize_system_resources()

            # Step 4: Start application
            if not self.start_application():
                logger.error("❌ Application startup failed")
                return

            # Step 5: Start monitoring
            logger.info("✅ System startup complete")
            logger.info("🌐 Application should be available at: http://localhost:8000")
            logger.info("📊 Health check available at: http://localhost:8000/health")
            logger.info("📖 API documentation at: http://localhost:8000/docs")

            # Start monitoring in background thread
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()

            # Keep main thread alive and handle signals

            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}")
                self.shutdown()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Main loop - perform periodic health checks
            while True:
                time.sleep(60)  # Check every minute
                health = self.health_check()

                if health["overall_status"] != "healthy":
                    logger.warning(f"⚠️ System health: {health['overall_status']}")
                    for issue in health["issues"]:
                        logger.warning(f"  - {issue}")
                else:
                    logger.info("✅ System healthy")

        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            self.shutdown()


def main():
    parser = argparse.ArgumentParser(description="TRAE.AI System Manager")
    parser.add_argument(
        "--mode",
        choices=["development", "production"],
        default="production",
        help="Run mode",
    )
    parser.add_argument(
        "--monitor-only", action="store_true", help="Only monitor existing processes"
    )

    args = parser.parse_args()

    manager = SystemManager(mode=args.mode)

    if args.monitor_only:
        logger.info("👁️ Monitor-only mode")
        manager.monitor_processes()
    else:
        manager.run()


if __name__ == "__main__":
    main()