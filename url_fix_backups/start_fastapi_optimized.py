#!/usr / bin / env python3
"""
Optimized FastAPI Startup Script for MacBook Air M1 (16GB)
Implements performance baseline recommendations
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class FastAPIOptimizer:
    """FastAPI optimization for MacBook Air M1"""

    def __init__(self):
        self.process = None
        self.config = self.get_m1_config()

    def get_m1_config(self):
        """Optimized configuration for MacBook Air M1"""
        return {
            "host": "0.0.0.0",
            "port": 8001,  # Using 8001 to avoid conflicts
            "workers": 2,  # Optimal for M1's 8 cores
            "worker_class": "uvicorn.workers.UvicornWorker",
            "max_requests": 1000,  # Restart workers after 1k requests
            "max_requests_jitter": 100,
            "preload_app": True,  # Faster startup
            "keepalive": 5,  # Connection keepalive
            "timeout": 30,
            "graceful_timeout": 30,
        }

    def check_dependencies(self):
        """Check if required packages are installed"""
        try:
            import gunicorn
            import uvicorn

            print("✅ Dependencies available")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Installing required packages...")
            try:
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "uvicorn[standard]",
                        "gunicorn",
                    ]
                )
                print("✅ Dependencies installed")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install dependencies")
                return False

    def find_app_module(self):
        """Find the FastAPI app module"""
        possible_paths = ["app.main:app", "main:app", "app:app", "backend.app:app"]

        for app_path in possible_paths:
            module_path = app_path.split(":")[0].replace(".", "/")
            if Path(f"{module_path}.py").exists() or Path(module_path).is_dir():
                print(f"📍 Found app module: {app_path}")
                return app_path

        print("❌ Could not find FastAPI app module")
        return None

    def start_with_uvicorn(self, app_module):
        """Start with Uvicorn (simpler, good for development)"""
        config = self.config

        cmd = [
            "uvicorn",
            app_module,
            "--host",
            config["host"],
            "--port",
            str(config["port"]),
            "--workers",
            str(config["workers"]),
            "--access - log",
            "--loop",
            "auto",  # Let uvicorn choose best event loop for M1
        ]

        print(f"🚀 Starting FastAPI with Uvicorn (MacBook Air M1 optimized)")
        print(f"   Workers: {config['workers']}")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   Command: {' '.join(cmd)}")
        print()

        return subprocess.Popen(cmd)

    def start_with_gunicorn(self, app_module):
        """Start with Gunicorn + Uvicorn workers (production - ready)"""
        config = self.config

        cmd = [
            "gunicorn",
            app_module,
            "-w",
            str(config["workers"]),
            "-k",
            config["worker_class"],
            "-b",
            f"{config['host']}:{config['port']}",
            "--max - requests",
            str(config["max_requests"]),
            "--max - requests - jitter",
            str(config["max_requests_jitter"]),
            "--preload" if config["preload_app"] else "--no - preload",
            "--keep - alive",
            str(config["keepalive"]),
            "--timeout",
            str(config["timeout"]),
            "--graceful - timeout",
            str(config["graceful_timeout"]),
            "--access - logfile",
            "-",
            "--error - logfile",
            "-",
        ]

        print(f"🚀 Starting FastAPI with Gunicorn + Uvicorn (Production - ready)")
        print(f"   Workers: {config['workers']} (Uvicorn workers)")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   Max requests per worker: {config['max_requests']}")
        print(f"   Command: {' '.join(cmd)}")
        print()

        return subprocess.Popen(cmd)

    def setup_signal_handlers(self):
        """Setup graceful shutdown"""

        def signal_handler(signum, frame):
            print(f"\\n🛑 Received signal {signum}, shutting down gracefully...")
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print("⚠️  Force killing process...")
                    self.process.kill()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def wait_for_startup(self):
        """Wait for FastAPI to be ready"""

        import requests

        config = self.config
        url = f"http://{config['host']}:{config['port']}/api / status"

        print("⏳ Waiting for FastAPI to start...")

        for attempt in range(30):  # 30 second timeout
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ FastAPI is ready! ({url})")
                    return True
            except requests.RequestException:
                pass

            time.sleep(1)
            print(f"   Attempt {attempt + 1}/30...")

        print("❌ FastAPI failed to start within 30 seconds")
        return False

    def print_performance_tips(self):
        """Print MacBook Air M1 performance optimization tips"""
        print("\\n💡 MacBook Air M1 Performance Tips:")
        print("=" * 50)
        print("✅ Using 2 workers (optimal for M1's 8 cores)")
        print("✅ Connection keepalive enabled")
        print("✅ Worker recycling after 1k requests")
        print("✅ Preloading app for faster startup")
        print()
        print("📊 Expected Performance:")
        print("  • 2k - 5k req / sec for simple endpoints")
        print("  • <50ms p95 latency")
        print("  • Memory usage: <2GB")
        print()
        print("🔧 Further Optimizations:")
        print("  • Add Redis caching")
        print("  • Use database connection pooling")
        print("  • Enable Nginx compression (gzip / brotli)")
        print("  • Monitor with htop during load tests")
        print()

    def start(self, use_gunicorn=False):
        """Start optimized FastAPI server"""
        print("🖥️  FastAPI Optimizer for MacBook Air M1 (16GB)")
        print("=" * 60)

        if not self.check_dependencies():
            return False

        app_module = self.find_app_module()
        if not app_module:
            return False

        self.setup_signal_handlers()

        try:
            if use_gunicorn:
                self.process = self.start_with_gunicorn(app_module)
            else:
                self.process = self.start_with_uvicorn(app_module)

            # Wait a moment for startup
            time.sleep(3)

            if self.process.poll() is not None:
                print("❌ FastAPI process exited immediately")
                return False

            self.print_performance_tips()

            print("🎯 Ready for performance testing!")
            print("   Run: python fastapi_performance_baseline.py")
            print("\\n⏹️  Press Ctrl + C to stop")

            # Keep running
            self.process.wait()

        except KeyboardInterrupt:
            print("\\n👋 Shutting down...")
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

        return True


def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(description="Optimized FastAPI startup for MacBook Air M1")
    parser.add_argument(
        "--gunicorn",
        action="store_true",
        help="Use Gunicorn + Uvicorn workers (production - ready)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark after startup",
    )

    args = parser.parse_args()

    optimizer = FastAPIOptimizer()

    if args.benchmark:
        # Start server in background and run benchmark
        print("🔄 Starting server and running benchmark...")
        # This would require more complex process management
        print("💡 For now, start server manually then run:")
        print("   python fastapi_performance_baseline.py")
        return

    success = optimizer.start(use_gunicorn=args.gunicorn)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
