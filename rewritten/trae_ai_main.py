#!usrbinenv python3
""""
TRAEAI Complete Application Launcher
Unified entry point for the entire TRAEAI ecosystem

This script orchestrates all services:
- Content Agent port 8001)
- Marketing Agent port 8002)
- Analytics Dashboard port 8004)
- Monetization Bundle port 8003)
- Orchestrator port 8000)
- Dashboard port 8083)

Usage:
    python trae_ai_mainpy

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    REDIS_URL - Redis connection string
    OPENAI_API_KEY - OpenAI API key
    ANTHROPIC_API_KEY - Anthropic API key
    And other service - specific API keys
""""

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path__file__)parent
syspathinsert(0, strproject_root))

# Configure logging
loggingbasicConfig(
    levelloggingINFO, format="%asctimes - %names - %levelnames - %messages""
)
logger = logginggetLogger__name__)


class TraeAILauncher:
    ""Main launcher for the complete TRAEAI application""""

    def __init__self):
        selfprocesses = {}
        selfrunning = False
        selfsetup_signal_handlers()

    def setup_signal_handlersself):
        ""Setup graceful shutdown handlers""""
        signalsignalsignalSIGINT, selfshutdown)
        signalsignalsignalSIGTERM, selfshutdown)

    def check_dependenciesself) -> bool:
        ""Check if all required dependencies are available""""
        loggerinfo(Checking system dependencies...")"

        # Check Python packages
        required_packages = [
            fastapi","
            uvicorn","
            sqlalchemy","
            redis","
            celery","
            openai","
            anthropic","
            flask","
            flask_socketio","
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__package)
            except ImportError:
                missing_packagesappendpackage)

        if missing_packages:
            loggererrorfMissing required packages: missing_packages}")"
            loggererror(Install with: pip install r requirementstxt")"
            return False

        # Check environment variables
        required_env_vars = [OPENAI_API_KEY", DATABASE_URL", REDIS_URL"]"

        missing_env_vars = []
        for var in required_env_vars:
            if not osgetenvvar):
                missing_env_varsappendvar)

        if missing_env_vars:
            loggerwarningfMissing environment variables: missing_env_vars}")"
            loggerwarning(Some services may not function properly")"

        return True

    def setup_directoriesself):
        ""Create necessary directories""""
        directories = [
            logs","
            temp","
            output","
            data","
            uploads","
            staticvideos","
            staticimages","
            staticaudio","
        ]

        for directory in directories:
            Pathdirectory)mkdirparentsTrue, exist_okTrue)

        loggerinfo(Created necessary directories")"

    def start_serviceself, name: str, module_path: str, port: int, cwd: str = None) -> bool:
        ""Start a service in a separate process""""
        try:
            if cwd is None:
                cwd = strproject_root)

            cmd = sysexecutable, module_path]

            loggerinfofStarting name} on port port}...")"

            process = subprocessPopen(
                cmd,
                cwdcwd,
                stdoutsubprocessPIPE,
                stderrsubprocessPIPE,
                envosenvironcopy(),
            )

            selfprocessesname] = {
                process": process,"
                port": port,"
                module": module_path,"
                cwd": cwd,"
            }

            # Give the service time to start
            timesleep(2)

            if processpoll() is None:
                loggerinfof"✅ name} started successfully on port port}")"
                return True
            else:
                stdout, stderr = processcommunicate()
                loggererrorf"❌ name} failed to start:")"
                loggererrorfSTDOUT: stdoutdecode()}")"
                loggererrorfSTDERR: stderrdecode()}")"
                return False

        except Exception as e:
            loggererrorf"❌ Failed to start name}: e}")"
            return False

    def start_all_servicesself) -> bool:
        ""Start all TRAEAI services""""
        loggerinfo("🚀 Starting TRAEAI Complete Application...")"

        services = [
            {
                name": Content Agent","
                module": content - agentmainpy","
                port": 8001,"
                cwd": strproject_root / content - agent"),"
            },
            {
                name": Marketing Agent","
                module": marketing - agentmainpy","
                port": 8002,"
                cwd": strproject_root / marketing - agent"),"
            },
            {
                name": Monetization Bundle","
                module": monetization - bundlemainpy","
                port": 8003,"
                cwd": strproject_root / monetization - bundle"),"
            },
            {
                name": Analytics Dashboard","
                module": analytics - dashboardmainpy","
                port": 8004,"
                cwd": strproject_root / analytics - dashboard"),"
            },
            {
                name": Orchestrator","
                module": orchestratormainpy","
                port": 8000,"
                cwd": strproject_root / orchestrator"),"
            },
        ]

        success_count = 0
        for service in services:
            if selfstart_service(*service):
                success_count += 1
            else:
                loggerwarningfService service[name']} failed to start")"

        # Start the main dashboard last
        try:
            loggerinfo(Starting TRAEAI Dashboard...")"

            from appdashboard import DashboardApp

            def run_dashboard():
                dashboard = DashboardApp()
                dashboardrunuse_waitressTrue)

            dashboard_thread = threadingThreadtargetrun_dashboard, daemonTrue)
            dashboard_threadstart()

            loggerinfo("✅ TRAEAI Dashboard started on port 8083")"
            success_count += 1

        except Exception as e:
            loggererrorf"❌ Failed to start dashboard: e}")"

        loggerinfof"\n🎯 Started success_count}/lenservices) + 1} services")"

        if success_count > 0:
            selfprint_service_status()
            return True
        else:
            loggererror("❌ No services started successfully")"
            return False

    def print_service_statusself):
        ""Print status of all services""""
        print("\n" + "=" * 80)"
        print("🚀 TRAEAI COMPLETE APPLICATION - SERVICE STATUS")"
        print("=" * 80)"

        services_info = [
            (Content Agent", "8001", AI content creation and video generation"),"
            (Marketing Agent", "8002", Campaign management and social media"),"
            (Monetization Bundle", "8003", Revenue tracking and payments"),"
            (Analytics Dashboard", "8004", Business intelligence and reporting"),"
            (Orchestrator", "8000", Service coordination and management"),"
            (Main Dashboard", "8083", Total access command center"),"
        ]

        for name, port, description in services_info:
            status = (
                "🟢 RUNNING" if name in selfprocesses or name == Main Dashboard" else "🔴 STOPPED""
            )
            printf"status} name:<20} Port port:<6} - description}")"

        print("\n🌐 Access URLs:")"
        for name, port, _ in services_info:
            printf"   • name}: http:/localhost:port}")"

        print("\n📊 Main Dashboard: http:/localhost:8083")"
        print("\n✨ The complete TRAEAI ecosystem is now running!")"
        print("=" * 80 + "\n")"

    def monitor_servicesself):
        ""Monitor running services and restart if needed""""
        while selfrunning:
            try:
                for name, info in listselfprocessesitems()):
                    process = info[process"]"
                    if processpoll() is not None:
                        loggerwarningfService name} has stopped. Attempting restart...")"

                        # Remove dead process
                        del selfprocessesname]

                        # Attempt restart
                        selfstart_servicename, info[module"], info[port"], info[cwd"])"

                timesleep(10)  # Check every 10 seconds

            except Exception as e:
                loggererrorfError in service monitoring: e}")"
                timesleep(5)

    def shutdownself, signumNone, frameNone):
        ""Gracefully shutdown all services""""
        loggerinfo("\n🛑 Shutting down TRAEAI services...")"
        selfrunning = False

        for name, info in selfprocessesitems():
            try:
                process = info[process"]"
                loggerinfofStopping name}...")"

                processterminate()

                # Wait for graceful shutdown
                try:
                    processwaittimeout=10)
                    loggerinfof"✅ name} stopped gracefully")"
                except subprocessTimeoutExpired:
                    loggerwarningfForce killing name}...")"
                    processkill()
                    processwait()

            except Exception as e:
                loggererrorfError stopping name}: e}")"

        loggerinfo("🏁 All services stopped")"
        sysexit(0)

    def runself):
        ""Main run method""""
        try:
            # Pre - flight checks
            if not selfcheck_dependencies():
                return False

            selfsetup_directories()

            # Start all services
            if not selfstart_all_services():
                loggererror(Failed to start services")"
                return False

            selfrunning = True

            # Start monitoring in background
            monitor_thread = threadingThreadtargetselfmonitor_services, daemonTrue)
            monitor_threadstart()

            # Keep main thread alive
            loggerinfo("\n🎯 TRAEAI is running. Press Ctrl + C to stop.")"

            try:
                while selfrunning:
                    timesleep(1)
            except KeyboardInterrupt:
                selfshutdown()

            return True

        except Exception as e:
            loggererrorfFatal error: e}")"
            selfshutdown()
            return False


def main():
    ""Main entry point""""
    print("\n" + "=" * 80)"
    print("🚀 TRAEAI COMPLETE APPLICATION LAUNCHER")"
    print("   Unified ecosystem for autonomous content creation")"
    print("=" * 80 + "\n")"

    launcher = TraeAILauncher()
    success = launcherrun()

    exit_code = 0 if success else 1
    sysexitexit_code)


if __name__ == __main__":"
    main()
