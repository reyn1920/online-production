#!/usr/bin/env python3
""""""



Monitoring Orchestrator - Unified Monitoring System Manager
Coordinates all monitoring components and provides centralized control

""""""


import json
import logging
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import all monitoring components

from alert_manager import AlertCategory, AlertSeverity, alert_manager
from audit_logger import audit_logger
from compliance_monitor import compliance_monitor
from content_validator import content_validator
from health_monitor import health_monitor
from timeout_manager import timeout_manager
from webhook_security import webhook_security

from monitoring_dashboard import start_dashboard, stop_dashboard


class ServiceStatus(Enum):
    
Service status enumeration
"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """Service information"""

    name: str
    status: ServiceStatus
    start_time: Optional[datetime] = None
    error_message: Optional[str] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    pid: Optional[int] = None
    thread: Optional[threading.Thread] = None


class MonitoringOrchestrator:
    """Orchestrates all monitoring services"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "monitoring_config.yaml"
         )
        self.services: Dict[str, ServiceInfo] = {}
        self.running = False
        self.shutdown_event = threading.Event()

        # Setup logging
        self.logger = logging.getLogger("monitoring_orchestrator")
        self.logger.setLevel(logging.INFO)

        # Load configuration
        self.config = self._load_config()

        # Initialize services registry
        self._initialize_services()

        # Setup signal handlers
        self._setup_signal_handlers()

        # Health check interval
        self.health_check_interval = self.config.get("health_check_interval", 30)

        # Auto - restart configuration
        self.auto_restart = self.config.get("auto_restart", True)
        self.max_restart_attempts = self.config.get("max_restart_attempts", 3)

        # Performance monitoring
        self.performance_metrics = {
            "start_time": None,
            "total_restarts": 0,
            "total_errors": 0,
            "services_started": 0,
            "last_health_check": None,
         }

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "services": {
                "alert_manager": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "health_monitor": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "compliance_monitor": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "dashboard": {
                    "enabled": True,
                    "auto_start": True,
                    "host": "0.0.0.0",
                    "port": 8080,
                    "debug": False,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "timeout_manager": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "webhook_security": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
                "content_validator": {
                    "enabled": True,
                    "auto_start": True,
                    "health_check": True,
                    "restart_on_failure": True,
                 },
             },
            "health_check_interval": 30,
            "auto_restart": True,
            "max_restart_attempts": 3,
            "startup_delay": 2,
            "shutdown_timeout": 30,
         }

        try:
            if os.path.exists(self.config_path):
                import yaml

                with open(self.config_path, "r") as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            else:
                self.logger.info(f"Config file not found at {self.config_path}, using defaults")
        except Exception as e:
            self.logger.warning(f"Error loading config: {str(e)}, using defaults")

        return default_config

    def _initialize_services(self):
        """Initialize service registry"""
        service_configs = self.config.get("services", {})

        for service_name, service_config in service_configs.items():
            if service_config.get("enabled", True):
                self.services[service_name] = ServiceInfo(
                    name=service_name, status=ServiceStatus.STOPPED
                 )

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Unknown service: {service_name}")
            return False

        service = self.services[service_name]

        if service.status == ServiceStatus.RUNNING:
            self.logger.info(f"Service {service_name} is already running")
            return True

        self.logger.info(f"Starting service: {service_name}")
        service.status = ServiceStatus.STARTING

        try:
            if service_name == "alert_manager":
                self._start_alert_manager(service)
            elif service_name == "health_monitor":
                self._start_health_monitor(service)
            elif service_name == "compliance_monitor":
                self._start_compliance_monitor(service)
            elif service_name == "dashboard":
                self._start_dashboard(service)
            elif service_name == "timeout_manager":
                self._start_timeout_manager(service)
            elif service_name == "webhook_security":
                self._start_webhook_security(service)
            elif service_name == "content_validator":
                self._start_content_validator(service)
            else:
                raise ValueError(f"Unknown service: {service_name}")

            service.status = ServiceStatus.RUNNING
            service.start_time = datetime.now()
            service.error_message = None
            self.performance_metrics["services_started"] += 1

            # Log audit event
            audit_logger.log_system_event(
                event_type="service_started",
                severity="info",
                additional_data={
                    "service_name": service_name,
                    "start_time": service.start_time.isoformat(),
                 },
             )

            self.logger.info(f"Service {service_name} started successfully")
            return True

        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error_message = str(e)
            self.performance_metrics["total_errors"] += 1

            self.logger.error(f"Failed to start service {service_name}: {str(e)}")

            # Log audit event
            audit_logger.log_system_event(
                event_type="service_start_failed",
                severity="error",
                additional_data={"service_name": service_name, "error": str(e)},
             )

            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Unknown service: {service_name}")
            return False

        service = self.services[service_name]

        if service.status == ServiceStatus.STOPPED:
            self.logger.info(f"Service {service_name} is already stopped")
            return True

        self.logger.info(f"Stopping service: {service_name}")
        service.status = ServiceStatus.STOPPING

        try:
            if service_name == "dashboard":
                stop_dashboard()
            elif service_name == "alert_manager":
                alert_manager.stop()
            elif service_name == "health_monitor":
                health_monitor.stop()
            elif service_name == "compliance_monitor":
                compliance_monitor.stop()
            elif service_name == "timeout_manager":
                timeout_manager.stop()
            elif service_name == "webhook_security":
                webhook_security.stop()
            elif service_name == "content_validator":
                content_validator.stop()

            # Stop service thread if exists
            if service.thread and service.thread.is_alive():
                service.thread.join(timeout=5)

            service.status = ServiceStatus.STOPPED
            service.start_time = None
            service.error_message = None
            service.thread = None

            # Log audit event
            audit_logger.log_system_event(
                event_type="service_stopped",
                severity="info",
                additional_data={"service_name": service_name},
             )

            self.logger.info(f"Service {service_name} stopped successfully")
            return True

        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error_message = str(e)

            self.logger.error(f"Failed to stop service {service_name}: {str(e)}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        self.logger.info(f"Restarting service: {service_name}")

        if service_name in self.services:
            self.services[service_name].restart_count += 1
            self.performance_metrics["total_restarts"] += 1

        # Stop the service first
        if not self.stop_service(service_name):
            self.logger.error(f"Failed to stop service {service_name} for restart")
            return False

        # Wait a moment before restarting
        time.sleep(self.config.get("startup_delay", 2))

        # Start the service
        return self.start_service(service_name)

    def _start_alert_manager(self, service: ServiceInfo):
        """Start alert manager service"""

        def run_alert_manager():
            try:
                alert_manager.start()
            except Exception as e:
                self.logger.error(f"Alert manager error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_alert_manager, daemon=True)
        service.thread.start()

    def _start_health_monitor(self, service: ServiceInfo):
        """Start health monitor service"""

        def run_health_monitor():
            try:
                health_monitor.start_monitoring()
            except Exception as e:
                self.logger.error(f"Health monitor error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_health_monitor, daemon=True)
        service.thread.start()

    def _start_compliance_monitor(self, service: ServiceInfo):
        """Start compliance monitor service"""

        def run_compliance_monitor():
            try:
                compliance_monitor.start_monitoring()
            except Exception as e:
                self.logger.error(f"Compliance monitor error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_compliance_monitor, daemon=True)
        service.thread.start()

    def _start_dashboard(self, service: ServiceInfo):
        """Start dashboard service"""
        dashboard_config = self.config["services"]["dashboard"]

        def run_dashboard():
            try:
                start_dashboard(
                    host=dashboard_config.get("host", "0.0.0.0"),
                    port=dashboard_config.get("port", 8080),
                    debug=dashboard_config.get("debug", False),
                 )
            except Exception as e:
                self.logger.error(f"Dashboard error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_dashboard, daemon=True)
        service.thread.start()

    def _start_timeout_manager(self, service: ServiceInfo):
        """Start timeout manager service"""

        def run_timeout_manager():
            try:
                timeout_manager.start()
            except Exception as e:
                self.logger.error(f"Timeout manager error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_timeout_manager, daemon=True)
        service.thread.start()

    def _start_webhook_security(self, service: ServiceInfo):
        """Start webhook security service"""

        def run_webhook_security():
            try:
                webhook_security.start()
            except Exception as e:
                self.logger.error(f"Webhook security error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_webhook_security, daemon=True)
        service.thread.start()

    def _start_content_validator(self, service: ServiceInfo):
        """Start content validator service"""

        def run_content_validator():
            try:
                content_validator.start()
            except Exception as e:
                self.logger.error(f"Content validator error: {str(e)}")
                service.status = ServiceStatus.ERROR
                service.error_message = str(e)

        service.thread = threading.Thread(target=run_content_validator, daemon=True)
        service.thread.start()

    def start_all(self) -> bool:
        """Start all enabled services"""
        self.logger.info("Starting all monitoring services")
        self.running = True
        self.performance_metrics["start_time"] = datetime.now()

        # Log audit event
        audit_logger.log_system_event(
            event_type="monitoring_system_started",
            severity="info",
            additional_data={
                "services": list(self.services.keys()),
                "start_time": self.performance_metrics["start_time"].isoformat(),
             },
         )

        success = True
        service_configs = self.config.get("services", {})

        for service_name in self.services.keys():
            service_config = service_configs.get(service_name, {})

            if service_config.get("auto_start", True):
                if not self.start_service(service_name):
                    success = False

                # Add startup delay between services
                time.sleep(self.config.get("startup_delay", 2))

        if success:
            self.logger.info("All monitoring services started successfully")

            # Start health check loop
            self._start_health_check_loop()
        else:
            self.logger.error("Some services failed to start")

        return success

    def stop_all(self) -> bool:
        """Stop all services"""
        self.logger.info("Stopping all monitoring services")
        self.running = False
        self.shutdown_event.set()

        # Log audit event
        audit_logger.log_system_event(
            event_type="monitoring_system_stopped",
            severity="info",
            additional_data={"services": list(self.services.keys())},
         )

        success = True

        # Stop services in reverse order
        for service_name in reversed(list(self.services.keys())):
            if not self.stop_service(service_name):
                success = False

        if success:
            self.logger.info("All monitoring services stopped successfully")
        else:
            self.logger.error("Some services failed to stop cleanly")

        return success

    def _start_health_check_loop(self):
        """Start health check loop"""

        def health_check_loop():
            while self.running and not self.shutdown_event.is_set():
                try:
                    self._perform_health_checks()
                    self.performance_metrics["last_health_check"] = datetime.now()

                    # Wait for next health check
                    if self.shutdown_event.wait(self.health_check_interval):
                        break

                except Exception as e:
                    self.logger.error(f"Error in health check loop: {str(e)}")
                    time.sleep(5)

        health_thread = threading.Thread(target=health_check_loop, daemon=True)
        health_thread.start()

    def _perform_health_checks(self):
        """
Perform health checks on all services

        
"""
        for service_name, service in self.services.items():
        """"""
            if service.status == ServiceStatus.RUNNING:
                try:
        """

        for service_name, service in self.services.items():
        

                    health_status = self._check_service_health(service_name)
                    service.health_status = health_status
                   
""""""

                    service.last_health_check = datetime.now()
                   

                    
                   
"""
                    # Handle unhealthy services
                   """

                    
                   

                    service.last_health_check = datetime.now()
                   
""""""
                    if health_status == "unhealthy" and self.auto_restart:
                        if service.restart_count < self.max_restart_attempts:
                            self.logger.warning(
                                f"Service {service_name} is unhealthy, attempting restart"
                             )
                            self.restart_service(service_name)
                        else:
                            self.logger.error(
                                f"Service {service_name} exceeded max restart attempts"
                             )

                            # Create alert for failed service

                            from alert_manager import create_custom_alert

                            create_custom_alert(
                                title=f"Service {service_name} Failed",
                                description=f"Service {service_name} has exceeded maximum restart attempts and is no longer being restarted",
                                severity=AlertSeverity.CRITICAL,
                                category=AlertCategory.SYSTEM,
                             )

                except Exception as e:
                    self.logger.error(f"Error checking health of {service_name}: {str(e)}")
                    service.health_status = "error"

    def _check_service_health(self, service_name: str) -> str:
        """
Check health of a specific service

        
"""
        try:
        """"""
            if service_name == "alert_manager":
        """

        try:
        

       
""""""
                return "healthy" if alert_manager.is_running() else "unhealthy"
            elif service_name == "health_monitor":
                return "healthy" if health_monitor.is_monitoring_active() else "unhealthy"
            elif service_name == "compliance_monitor":
                return "healthy" if compliance_monitor.is_monitoring_active() else "unhealthy"
            elif service_name == "dashboard":
                # Check if dashboard is responding

                import requests

                try:
                    dashboard_config = self.config["services"]["dashboard"]
                    host = dashboard_config.get("host", "0.0.0.0")
                    port = dashboard_config.get("port", 8080)

                    # Use localhost if host is 0.0.0.0
                    check_host = "localhost" if host == "0.0.0.0" else host

                    response = requests.get(f"http://{check_host}:{port}/api/health", timeout=5)
                    return "healthy" if response.status_code == 200 else "unhealthy"
                except Exception:
                    return "unhealthy"
            elif service_name == "timeout_manager":
                return "healthy" if timeout_manager.is_active() else "unhealthy"
            elif service_name == "webhook_security":
                return "healthy" if webhook_security.is_active() else "unhealthy"
            elif service_name == "content_validator":
                return "healthy" if content_validator.is_active() else "unhealthy"
            else:
                return "unknown"
        except Exception as e:
            self.logger.error(f"Error checking {service_name} health: {str(e)}")
            return "error"

    def get_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            "orchestrator": {
                "running": self.running,
                "start_time": (
                    self.performance_metrics["start_time"].isoformat()
                    if self.performance_metrics["start_time"]
                    else None
                 ),
                "performance_metrics": self.performance_metrics.copy(),
             },
            "services": {},
         }

        for service_name, service in self.services.items():
            status["services"][service_name] = {
                "name": service.name,
                "status": service.status.value,
                "start_time": (service.start_time.isoformat() if service.start_time else None),
                "error_message": service.error_message,
                "restart_count": service.restart_count,
                "last_health_check": (
                    service.last_health_check.isoformat() if service.last_health_check else None
                 ),
                "health_status": service.health_status,
                "pid": service.pid,
             }

        return status

    def get_service_logs(self, service_name: str, lines: int = 100) -> List[str]:
        """
Get logs for a specific service

        # This would typically read from log files
       
""""""

        # For now, return a placeholder
       

        
       
"""
        return [f"Log entry for {service_name} - {i}" for i in range(lines)]
       """

        
       

        # For now, return a placeholder
       
""""""

    def shutdown(self):
        """
        Graceful shutdown
        """
        self.logger.info("Initiating graceful shutdown")

        # Stop all services
        self.stop_all()

        # Wait for shutdown
        time.sleep(2)

        self.logger.info("Monitoring orchestrator shutdown complete")

    def run(self):
        """Run the orchestrator"""
        self.logger.info("Starting monitoring orchestrator")

        try:
            # Start all services
            if not self.start_all():
                self.logger.error("Failed to start all services")
                return False

            # Keep running until shutdown
            while self.running and not self.shutdown_event.is_set():
                time.sleep(1)

            return True

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in orchestrator: {str(e)}")
        finally:
            self.shutdown()

        return False


# Global orchestrator instance
orchestrator = None


def start_monitoring_system(
    config_path: Optional[str] = None,
# ) -> MonitoringOrchestrator:
    """
Start the complete monitoring system

   
""""""

    global orchestrator
   

    
   
"""
    if orchestrator is None:
        orchestrator = MonitoringOrchestrator(config_path=config_path)

    return orchestrator


def stop_monitoring_system():
    """
Stop the complete monitoring system

   
""""""

    global orchestrator
   

    
   
"""
    if orchestrator:
        orchestrator.shutdown()
        orchestrator = None


def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring system status"""

    if orchestrator:
        return orchestrator.get_status()
    else:
        return {"error": "Monitoring system not running"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitoring System Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--service", help="Start specific service only")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--restart", help="Restart specific service")

    args = parser.parse_args()

    if args.status:
        status = get_monitoring_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    orchestrator = start_monitoring_system(config_path=args.config)

    if args.stop:
        orchestrator.stop_all()
        sys.exit(0)

    if args.service:
        if orchestrator.start_service(args.service):
            print(f"Service {args.service} started successfully")
        else:
            print(f"Failed to start service {args.service}")
            sys.exit(1)
    elif args.restart:
        if orchestrator.restart_service(args.restart):
            print(f"Service {args.restart} restarted successfully")
        else:
            print(f"Failed to restart service {args.restart}")
            sys.exit(1)
    else:
        # Run the complete system
        if orchestrator.run():
            print("Monitoring system started successfully")
        else:
            print("Monitoring system failed to start")
            sys.exit(1)