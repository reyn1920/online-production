#!/usr/bin/env python3
""""""
Simple Startup Runner - Alternative to complex startup_system.py
Provides basic server startup with monitoring integration
""""""

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SimpleRunner:
    """Simple server runner with basic monitoring"""

    def __init__(self):
        self.processes = {}
        self.running = True
        self.monitoring_thread = None

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        logger.info("🔍 Checking dependencies...")

        required_packages = ["fastapi", "uvicorn", "psutil"]
        missing = []

        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package} - OK")
            except ImportError:
                missing.append(package)
                logger.error(f"❌ {package} - MISSING")

        if missing:
            logger.error(f"Missing required packages: {', '.join(missing)}")
            logger.info("Install with: pip install " + " ".join(missing))
            return False

        return True

    def setup_directories(self):
        """Create necessary directories"""
        logger.info("📁 Setting up directories...")

        directories = ["logs", "data", "monitoring"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"✅ {directory}/directory ready")

    def set_environment(self):
        """Set up environment variables"""
        logger.info("🔧 Setting up environment...")

        defaults = {
            "ENVIRONMENT": "development",
            "DEBUG": "true",
            "HOST": "0.0.0.0",
            "PORT": "8000",
            "SECRET_KEY": "dev - secret - key - change - in - production",
# BRACKET_SURGEON: disabled
#         }

        for key, value in defaults.items():
            if key not in os.environ:
                os.environ[key] = value
                logger.info(f"✅ Set {key}={value}")
            else:
                logger.info(f"✅ Using existing {key}={os.environ[key]}")

    def start_main_server(self) -> bool:
        """Start the main FastAPI server"""
        logger.info("🚀 Starting main server...")

        try:
            # Import and start the server

            host = os.environ.get("HOST", "0.0.0.0")
            port = int(os.environ.get("PORT", 8000))

            logger.info(f"🌐 Server starting on http://{host}:{port}")
            logger.info(f"📚 API docs available at http://{host}:{port}/docs")
            logger.info(f"❤️ Health check at http://{host}:{port}/health")

            # Start server in a separate process
            server_process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    f"import uvicorn; from main import app; uvicorn.run(app, host='{host}', port={port}, reload=False, log_level='info')",
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )

            self.processes["main_server"] = server_process

            # Give server time to start
            time.sleep(3)

            # Check if server started successfully
            if server_process.poll() is None:
                logger.info("✅ Main server started successfully")
                return True
            else:
                logger.error("❌ Main server failed to start")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to start main server: {e}")
            return False

    def start_monitoring(self):
        """Start basic monitoring"""
        logger.info("👁️ Starting monitoring...")

        self.monitoring_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self.monitoring_thread.start()
        logger.info("✅ Monitoring started")

    def _monitor_processes(self):
        """Monitor running processes"""

        import psutil
        import requests

        while self.running:
            try:
                # Check main server process
                if "main_server" in self.processes:
                    process = self.processes["main_server"]

                    if process.poll() is not None:
                        logger.error("❌ Main server process died, attempting restart...")
                        self.start_main_server()
                    else:
                        # Check if server is responding
                        try:
                            response = requests.get("http://localhost:8000/health", timeout=5)
                            if response.status_code == 200:
                                logger.debug("✅ Main server health check passed")
                            else:
                                logger.warning(
                                    f"⚠️ Main server health check failed: {response.status_code}"
# BRACKET_SURGEON: disabled
#                                 )
                        except requests.exceptions.RequestException as e:
                            logger.warning(f"⚠️ Main server health check failed: {e}")

                # System resource check
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                if cpu_percent > 90:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}%")

                if memory.percent > 90:
                    logger.warning(f"⚠️ High memory usage: {memory.percent:.1f}%")

                # Wait before next check
                time.sleep(30)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)

    def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        logger.info("🎯 System ready - Press Ctrl + C to shutdown")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown all processes"""
        logger.info("🛑 Shutting down...")
        self.running = False

        # Stop all processes
        for name, process in self.processes.items():
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()

                # Wait for graceful termination
                try:
                    process.wait(timeout=10)
                    logger.info(f"✅ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}...")
                    process.kill()
                    process.wait()
                    logger.info(f"✅ {name} force stopped")

            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        logger.info("👋 Shutdown complete")

    def run(self):
        """Main run method"""
        logger.info("🚀 Simple Runner Starting...")

        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False

        # Setup environment
        self.setup_directories()
        self.set_environment()

        # Start main server
        if not self.start_main_server():
            logger.error("❌ Failed to start main server")
            return False

        # Start monitoring
        self.start_monitoring()

        # Wait for shutdown
        self.wait_for_shutdown()

        return True


def main():
    """Main entry point"""
    runner = SimpleRunner()

    try:
        success = runner.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()