#!/usr/bin/env python3
"""
Self-Healing Monitoring System
Detects stuck processes and automatically restarts failed services
"""

import asyncio
import logging
import time
import psutil
import httpx
import subprocess
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a monitored service"""
    name: str
    health_url: str
    process_name: str
    restart_command: List[str]
    max_failures: int = 3
    check_interval: int = 30
    timeout: int = 10
    failure_count: int = field(default=0)
    last_check: Optional[datetime] = field(default=None)
    last_failure: Optional[datetime] = field(default=None)
    status: str = field(default="unknown")

class SelfHealingMonitor:
    """Self-healing monitoring system for critical services"""
    
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.running = False
        self.alert_callbacks: List[Callable] = []
        self.restart_cooldown = 60  # seconds between restart attempts
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize default services
        self._initialize_default_services()
    
    def _initialize_default_services(self):
        """Initialize monitoring for default services"""
        self.add_service(ServiceConfig(
            name="main_app",
            health_url="http://localhost:8000/health",
            process_name="python3",
            restart_command=["python3", "main.py"]
        ))
        
        self.add_service(ServiceConfig(
            name="startup_system",
            health_url="http://localhost:8000/api/status",
            process_name="python3",
            restart_command=["python3", "startup_system.py", "--mode", "development"]
        ))
    
    def add_service(self, service: ServiceConfig):
        """Add a service to monitor"""
        self.services[service.name] = service
        logger.info(f"📊 Added service to monitor: {service.name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_service_health(self, service: ServiceConfig) -> bool:
        """Check if a service is healthy via HTTP health check"""
        try:
            async with httpx.AsyncClient(timeout=service.timeout) as client:
                response = await client.get(service.health_url)
                if response.status_code == 200:
                    service.status = "healthy"
                    service.failure_count = 0
                    return True
                else:
                    service.status = f"unhealthy_http_{response.status_code}"
                    return False
        except Exception as e:
            service.status = f"unreachable: {str(e)[:50]}"
            return False
    
    def check_process_running(self, service: ServiceConfig) -> bool:
        """Check if the service process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if service.process_name in proc.info['name']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # Check if this is our specific service
                    if any(cmd_part in cmdline for cmd_part in service.restart_command):
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking process for {service.name}: {e}")
            return False
    
    async def restart_service(self, service: ServiceConfig) -> bool:
        """Restart a failed service"""
        try:
            # Kill existing processes first
            await self._kill_service_processes(service)
            
            # Wait a moment for cleanup
            await asyncio.sleep(2)
            
            # Start the service
            logger.info(f"🔄 Restarting service: {service.name}")
            process = await asyncio.create_subprocess_exec(
                *service.restart_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Give it time to start
            await asyncio.sleep(5)
            
            # Check if it started successfully
            if process.returncode is None:  # Still running
                logger.info(f"✅ Service {service.name} restarted successfully")
                service.failure_count = 0
                await self._send_alert(f"Service {service.name} restarted successfully")
                return True
            else:
                logger.error(f"❌ Service {service.name} failed to start (exit code: {process.returncode})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to restart service {service.name}: {e}")
            return False
    
    async def _kill_service_processes(self, service: ServiceConfig):
        """Kill existing service processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if service.process_name in proc.info['name']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(cmd_part in cmdline for cmd_part in service.restart_command):
                        logger.info(f"🔪 Killing process {proc.info['pid']} for {service.name}")
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
        except Exception as e:
            logger.error(f"Error killing processes for {service.name}: {e}")
    
    async def _send_alert(self, message: str):
        """Send alert to all registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    async def monitor_service(self, service: ServiceConfig):
        """Monitor a single service"""
        service.last_check = datetime.now()
        
        # Check if process is running
        process_running = self.check_process_running(service)
        
        # Check health endpoint
        health_ok = await self.check_service_health(service)
        
        if not process_running or not health_ok:
            service.failure_count += 1
            service.last_failure = datetime.now()
            
            logger.warning(
                f"⚠️ Service {service.name} unhealthy: "
                f"process_running={process_running}, health_ok={health_ok}, "
                f"failures={service.failure_count}/{service.max_failures}"
            )
            
            # Check if we should restart
            if service.failure_count >= service.max_failures:
                # Check cooldown period
                if (service.last_failure and 
                    datetime.now() - service.last_failure < timedelta(seconds=self.restart_cooldown)):
                    logger.info(f"⏳ Service {service.name} in restart cooldown")
                    return
                
                await self._send_alert(
                    f"Service {service.name} failed {service.failure_count} times, attempting restart"
                )
                
                success = await self.restart_service(service)
                if success:
                    service.failure_count = 0
                else:
                    await self._send_alert(
                        f"CRITICAL: Failed to restart service {service.name}"
                    )
        else:
            if service.failure_count > 0:
                logger.info(f"✅ Service {service.name} recovered")
                service.failure_count = 0
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🔍 Starting self-healing monitoring loop")
        
        while self.running:
            try:
                # Monitor all services
                tasks = []
                for service in self.services.values():
                    if (not service.last_check or 
                        datetime.now() - service.last_check >= timedelta(seconds=service.check_interval)):
                        tasks.append(self.monitor_service(service))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def start(self):
        """Start the monitoring system"""
        if self.running:
            logger.warning("Monitoring system already running")
            return
        
        self.running = True
        logger.info("🚀 Starting self-healing monitoring system")
        
        # Start monitoring loop
        await self.monitoring_loop()
    
    async def stop(self):
        """Stop the monitoring system"""
        logger.info("🛑 Stopping self-healing monitoring system")
        self.running = False
    
    def get_status(self) -> Dict:
        """Get current status of all monitored services"""
        return {
            "monitoring_active": self.running,
            "services": {
                name: {
                    "status": service.status,
                    "failure_count": service.failure_count,
                    "last_check": service.last_check.isoformat() if service.last_check else None,
                    "last_failure": service.last_failure.isoformat() if service.last_failure else None
                }
                for name, service in self.services.items()
            }
        }

# Global monitor instance
monitor = SelfHealingMonitor()

async def main():
    """Main entry point for standalone monitoring"""
    # Add console alert callback
    def console_alert(message: str):
        print(f"🚨 ALERT: {message}")
    
    monitor.add_alert_callback(console_alert)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())