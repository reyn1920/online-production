#!/usr/bin/env python3
"""
Local Development Server Launcher

Usage:
    python3 tools/start_local.py paste      # Launch paste application
    python3 tools/start_local.py dashboard  # Launch dashboard application
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutting down server...")
    sys.exit(0)


def launch_paste_app():
    """Launch the paste application"""
    print("🚀 Starting Paste Application...")
    print("📋 Available at: http://127.0.0.1:8000 (or next available port)")
    print("💡 Press Ctrl+C to stop\n")

    # Change to project root directory
    os.chdir(project_root)

    # Launch paste app
    try:
        subprocess.run([sys.executable, "paste_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching paste app: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Paste app stopped by user")


def launch_dashboard():
    """Launch the dashboard application"""
    print("🚀 Starting Dashboard Application...")
    print("📊 Available at: http://127.0.0.1:8080 (or next available port)")
    print("💡 Press Ctrl+C to stop\n")

    # Change to project root directory
    os.chdir(project_root)

    # Launch dashboard
    try:
        subprocess.run([sys.executable, "app/dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")


def launch_live_dashboard():
    """Launch the live dashboard application"""
    print("🚀 Starting Live Dashboard Application...")
    print("📊 Available at: http://127.0.0.1:8001 (or next available port)")
    print("💡 Press Ctrl+C to stop\n")

    # Change to project root directory
    os.chdir(project_root)

    # Launch live dashboard
    try:
        subprocess.run([sys.executable, "live_dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching live dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Live dashboard stopped by user")


def show_help():
    """Show usage information"""
    print(
        """
🔧 Local Development Server Launcher

Usage:
    python3 tools/start_local.py <service>

Available services:
    paste         Launch paste application (http://127.0.0.1:8000)
    dashboard     Launch main dashboard (http://127.0.0.1:8080)
    live          Launch live dashboard (http://127.0.0.1:8001)
    
Examples:
    python3 tools/start_local.py paste
    python3 tools/start_local.py dashboard
    python3 tools/start_local.py live

💡 All applications use automatic port detection to avoid conflicts.
💡 Press Ctrl+C to stop any running service.
    """
    )


def main():
    """Main entry point"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments
    if len(sys.argv) != 2:
        show_help()
        sys.exit(1)

    service = sys.argv[1].lower()

    # Route to appropriate launcher
    if service == "paste":
        launch_paste_app()
    elif service == "dashboard":
        launch_dashboard()
    elif service == "live":
        launch_live_dashboard()
    elif service in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"❌ Unknown service: {service}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
