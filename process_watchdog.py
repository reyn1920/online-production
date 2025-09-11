#!/usr/bin/env python3
"""
Process Watchdog for TRAE.AI Production
Monitors critical services and restarts them if they become unresponsive
"""

import os
import sys
import time
import psutil
import logging
import subprocess
import threading
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a monitored service"""
    name: str
    command: List[str]
    working_dir: str
    health_check_url: Optional[str] = None
    health_check_timeout: int = 5
    restart_delay: int = 5
    max_restarts_per_hour: int = 10
    process_match_pattern: str = None
    critical: bool = True

class ProcessWatchdog:
    """Monitors and manages critical processes"""
    
    def __init__(self):
        self.services = self._load_service_configs()
        self.service_processes = {}  # service_name -> psutil.Process
        self.restart_history = {}   # service_name -> list of restart times
        self.running = False
        self.check_interval = 10    # Check every 10 seconds
        self.shutdown_event = threading.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_service_configs(self) -> Dict[str, ServiceConfig]:
        """Load service configurations"""
        base_dir = "/Users/thomasbrianreynolds/online production"
        
        return {
            'minimal_server': ServiceConfig(
                name='minimal_server',
                command=['python3', 'minimal_server.py'],
                working_dir=base_dir,
                health_check_url='http://localhost:8000/health',
                process_match_pattern='minimal_server.py',
                critical=True
            ),
            'monitoring_system': ServiceConfig(
                name='monitoring_system',
                command=['python3', 'monitoring_system.py'],
                working_dir=base_dir,
                process_match_pattern='monitoring_system.py',
                critical=False,
                max_restarts_per_hour=5
            )
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down watchdog...")
        self.shutdown_event.set()
        self.running = False
    
    def _find_process_by_pattern(self, pattern: str) -> Optional[psutil.Process]:
        """Find a process by command line pattern"""
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if pattern in cmdline:
                        return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error finding process by pattern '{pattern}': {e}")
        return None
    
    def _is_process_running(self, service_name: str) -> bool:
        """Check if a service process is running"""
        config = self.services[service_name]
        
        # Check if we have a tracked process
        if service_name in self.service_processes:
            proc = self.service_processes[service_name]
            try:
                if proc.is_running():
                    return True
                else:
                    # Process died, remove from tracking
                    del self.service_processes[service_name]
            except psutil.NoSuchProcess:
                del self.service_processes[service_name]
        
        # Look for process by pattern
        if config.process_match_pattern:
            proc = self._find_process_by_pattern(config.process_match_pattern)
            if proc:
                self.service_processes[service_name] = proc
                return True
        
        return False
    
    def _check_service_health(self, service_name: str) -> bool:
        """Check service health via HTTP endpoint"""
        config = self.services[service_name]
        
        if not config.health_check_url:
            # No health check URL, assume healthy if process is running
            return self._is_process_running(service_name)
        
        try:
            response = requests.get(
                config.health_check_url,
                timeout=config.health_check_timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _can_restart_service(self, service_name: str) -> bool:
        """Check if service can be restarted (not hitting rate limits)"""
        config = self.services[service_name]
        current_time = time.time()
        
        # Initialize restart history if needed
        if service_name not in self.restart_history:
            self.restart_history[service_name] = []
        
        # Clean old restart entries (older than 1 hour)
        cutoff_time = current_time - 3600  # 1 hour ago
        self.restart_history[service_name] = [
            restart_time for restart_time in self.restart_history[service_name]
            if restart_time > cutoff_time
        ]
        
        # Check if we're under the restart limit
        return len(self.restart_history[service_name]) < config.max_restarts_per_hour
    
    def _start_service(self, service_name: str) -> bool:
        """Start a service"""
        config = self.services[service_name]
        
        try:
            logger.info(f"🚀 Starting service: {service_name}")
            
            # Start the process
            proc = subprocess.Popen(
                config.command,
                cwd=config.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Convert to psutil process for better monitoring
            psutil_proc = psutil.Process(proc.pid)
            self.service_processes[service_name] = psutil_proc
            
            # Record restart time
            self.restart_history[service_name].append(time.time())
            
            logger.info(f"✅ Service {service_name} started with PID {proc.pid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start service {service_name}: {e}")
            return False
    
    def _stop_service(self, service_name: str) -> bool:
        """Stop a service gracefully"""
        try:
            if service_name in self.service_processes:
                proc = self.service_processes[service_name]
                logger.info(f"🛑 Stopping service: {service_name} (PID: {proc.pid})")
                
                # Try graceful shutdown first
                proc.terminate()
                
                # Wait for graceful shutdown
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"⚡ Force killing service: {service_name}")
                    proc.kill()
                    proc.wait(timeout=5)
                
                del self.service_processes[service_name]
                logger.info(f"✅ Service {service_name} stopped")
                return True
            
            # Also try to kill by pattern
            config = self.services[service_name]
            if config.process_match_pattern:
                proc = self._find_process_by_pattern(config.process_match_pattern)
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to stop service {service_name}: {e}")
            return False
    
    def _restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        config = self.services[service_name]
        
        logger.info(f"🔄 Restarting service: {service_name}")
        
        # Stop the service
        self._stop_service(service_name)
        
        # Wait for restart delay
        time.sleep(config.restart_delay)
        
        # Start the service
        return self._start_service(service_name)
    
    def _monitor_service(self, service_name: str) -> Dict[str, Any]:
        """Monitor a single service and take action if needed"""
        config = self.services[service_name]
        status = {
            'service': service_name,
            'timestamp': datetime.now().isoformat(),
            'running': False,
            'healthy': False,
            'action_taken': None,
            'restart_count_last_hour': 0
        }
        
        try:
            # Check if process is running
            status['running'] = self._is_process_running(service_name)
            
            # Check service health
            status['healthy'] = self._check_service_health(service_name)
            
            # Get restart count
            if service_name in self.restart_history:
                status['restart_count_last_hour'] = len(self.restart_history[service_name])
            
            # Determine if action is needed
            needs_restart = False
            
            if not status['running']:
                logger.warning(f"⚠️ Service {service_name} is not running")
                needs_restart = True
            elif not status['healthy']:
                logger.warning(f"⚠️ Service {service_name} is unhealthy")
                needs_restart = True
            
            # Take action if needed
            if needs_restart and config.critical:
                if self._can_restart_service(service_name):
                    if self._restart_service(service_name):
                        status['action_taken'] = 'restarted'
                        logger.info(f"✅ Service {service_name} restarted successfully")
                    else:
                        status['action_taken'] = 'restart_failed'
                        logger.error(f"❌ Failed to restart service {service_name}")
                else:
                    status['action_taken'] = 'restart_rate_limited'
                    logger.error(f"🚫 Service {service_name} restart rate limited")
            elif needs_restart:
                logger.info(f"ℹ️ Service {service_name} needs restart but is not critical")
                status['action_taken'] = 'restart_skipped_non_critical'
            
        except Exception as e:
            logger.error(f"❌ Error monitoring service {service_name}: {e}")
            status['error'] = str(e)
        
        return status
    
    def start_watchdog(self):
        """Start the watchdog monitoring loop"""
        logger.info("🐕 Starting Process Watchdog...")
        logger.info(f"Monitoring {len(self.services)} services: {list(self.services.keys())}")
        
        self.running = True
        
        # Start all critical services
        for service_name, config in self.services.items():
            if config.critical and not self._is_process_running(service_name):
                if self._can_restart_service(service_name):
                    self._start_service(service_name)
        
        # Main monitoring loop
        while self.running and not self.shutdown_event.is_set():
            try:
                monitoring_report = {
                    'timestamp': datetime.now().isoformat(),
                    'services': {}
                }
                
                # Monitor each service
                for service_name in self.services:
                    service_status = self._monitor_service(service_name)
                    monitoring_report['services'][service_name] = service_status
                
                # Log significant events
                actions_taken = [
                    f"{name}: {status['action_taken']}"
                    for name, status in monitoring_report['services'].items()
                    if status.get('action_taken') and status['action_taken'] != 'none'
                ]
                
                if actions_taken:
                    logger.info(f"📊 Watchdog actions: {', '.join(actions_taken)}")
                
                # Save monitoring report
                with open('watchdog_reports.jsonl', 'a') as f:
                    f.write(json.dumps(monitoring_report) + '\n')
                
                # Wait for next check
                self.shutdown_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Watchdog error: {e}")
                self.shutdown_event.wait(self.check_interval)
        
        logger.info("🛑 Process Watchdog stopped")
    
    def stop_watchdog(self):
        """Stop the watchdog and all monitored services"""
        logger.info("🛑 Stopping Process Watchdog...")
        self.running = False
        self.shutdown_event.set()
        
        # Stop all monitored services
        for service_name in self.services:
            self._stop_service(service_name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all services"""
        status = {
            'watchdog_running': self.running,
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for service_name in self.services:
            service_status = {
                'running': self._is_process_running(service_name),
                'healthy': self._check_service_health(service_name),
                'restart_count_last_hour': len(self.restart_history.get(service_name, []))
            }
            
            if service_name in self.service_processes:
                proc = self.service_processes[service_name]
                try:
                    service_status['pid'] = proc.pid
                    service_status['cpu_percent'] = proc.cpu_percent()
                    service_status['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            status['services'][service_name] = service_status
        
        return status

def main():
    """Main watchdog function"""
    watchdog = ProcessWatchdog()
    
    try:
        watchdog.start_watchdog()
    except KeyboardInterrupt:
        logger.info("🛑 Watchdog stopped by user")
    finally:
        watchdog.stop_watchdog()

if __name__ == "__main__":
    main()