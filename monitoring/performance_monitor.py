#!/usr/bin/env python3
"""
TRAE AI Performance Monitor
Tracks system performance, resource usage, and application health metrics.
"""

import os
import sys
import time
import json
import psutil
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger('trae_ai.performance')

@dataclass
class SystemMetrics:
    """System performance metrics data structure."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: List[float]
    uptime_seconds: float

@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics."""
    timestamp: str
    active_agents: int
    dashboard_status: str
    database_connections: int
    response_time_ms: float
    error_count: int
    warning_count: int
    memory_usage_mb: float
    cpu_usage_percent: float

class PerformanceMonitor:
    """Main performance monitoring class."""
    
    def __init__(self, db_path: str = "monitoring/performance_metrics.db"):
        self.db_path = db_path
        self.start_time = time.time()
        self._ensure_db_directory()
        self._init_database()
        
    def _ensure_db_directory(self):
        """Ensure the monitoring directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
    def _init_database(self):
        """Initialize the performance metrics database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # System metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        memory_used_mb REAL,
                        memory_available_mb REAL,
                        disk_usage_percent REAL,
                        disk_free_gb REAL,
                        network_bytes_sent INTEGER,
                        network_bytes_recv INTEGER,
                        process_count INTEGER,
                        load_average TEXT,
                        uptime_seconds REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Application metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS application_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        active_agents INTEGER,
                        dashboard_status TEXT,
                        database_connections INTEGER,
                        response_time_ms REAL,
                        error_count INTEGER,
                        warning_count INTEGER,
                        memory_usage_mb REAL,
                        cpu_usage_percent REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        metric_name TEXT,
                        metric_value REAL,
                        threshold REAL,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Performance monitoring database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize performance database: {e}")
            raise
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_avg = list(os.getloadavg())
            except (OSError, AttributeError):
                load_avg = [0.0, 0.0, 0.0]  # Windows fallback
            
            # Uptime
            uptime = time.time() - self.start_time
            
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                load_average=load_avg,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific performance metrics."""
        try:
            # Get current process info
            current_process = psutil.Process()
            
            # Check if dashboard is running (simplified check)
            dashboard_status = "unknown"
            try:
                # This would need to be adapted based on actual dashboard implementation
                import requests
                response = requests.get("http://localhost:5000/health", timeout=2)
                dashboard_status = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                dashboard_status = "offline"
            
            # Database connections (simplified)
            db_connections = 1  # This would need actual implementation
            
            # Response time (mock - would need actual implementation)
            response_time = 50.0  # milliseconds
            
            # Error and warning counts (would need log parsing)
            error_count = 0
            warning_count = 0
            
            return ApplicationMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                active_agents=13,  # Based on the system description
                dashboard_status=dashboard_status,
                database_connections=db_connections,
                response_time_ms=response_time,
                error_count=error_count,
                warning_count=warning_count,
                memory_usage_mb=current_process.memory_info().rss / (1024 * 1024),
                cpu_usage_percent=current_process.cpu_percent()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            raise
    
    def store_metrics(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Store metrics in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store system metrics
                cursor.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, memory_used_mb,
                        memory_available_mb, disk_usage_percent, disk_free_gb,
                        network_bytes_sent, network_bytes_recv, process_count,
                        load_average, uptime_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    system_metrics.timestamp,
                    system_metrics.cpu_percent,
                    system_metrics.memory_percent,
                    system_metrics.memory_used_mb,
                    system_metrics.memory_available_mb,
                    system_metrics.disk_usage_percent,
                    system_metrics.disk_free_gb,
                    system_metrics.network_bytes_sent,
                    system_metrics.network_bytes_recv,
                    system_metrics.process_count,
                    json.dumps(system_metrics.load_average),
                    system_metrics.uptime_seconds
                ))
                
                # Store application metrics
                cursor.execute("""
                    INSERT INTO application_metrics (
                        timestamp, active_agents, dashboard_status, database_connections,
                        response_time_ms, error_count, warning_count,
                        memory_usage_mb, cpu_usage_percent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_metrics.timestamp,
                    app_metrics.active_agents,
                    app_metrics.dashboard_status,
                    app_metrics.database_connections,
                    app_metrics.response_time_ms,
                    app_metrics.error_count,
                    app_metrics.warning_count,
                    app_metrics.memory_usage_mb,
                    app_metrics.cpu_usage_percent
                ))
                
                conn.commit()
                logger.debug("Metrics stored successfully")
                
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            raise
    
    def check_thresholds(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        # CPU threshold
        if system_metrics.cpu_percent > 80:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning' if system_metrics.cpu_percent < 90 else 'critical',
                'message': f'High CPU usage: {system_metrics.cpu_percent:.1f}%',
                'metric_name': 'cpu_percent',
                'metric_value': system_metrics.cpu_percent,
                'threshold': 80
            })
        
        # Memory threshold
        if system_metrics.memory_percent > 85:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning' if system_metrics.memory_percent < 95 else 'critical',
                'message': f'High memory usage: {system_metrics.memory_percent:.1f}%',
                'metric_name': 'memory_percent',
                'metric_value': system_metrics.memory_percent,
                'threshold': 85
            })
        
        # Disk threshold
        if system_metrics.disk_usage_percent > 90:
            alerts.append({
                'type': 'disk_full',
                'severity': 'critical',
                'message': f'Disk usage critical: {system_metrics.disk_usage_percent:.1f}%',
                'metric_name': 'disk_usage_percent',
                'metric_value': system_metrics.disk_usage_percent,
                'threshold': 90
            })
        
        # Dashboard status
        if app_metrics.dashboard_status != 'healthy':
            alerts.append({
                'type': 'dashboard_unhealthy',
                'severity': 'critical',
                'message': f'Dashboard status: {app_metrics.dashboard_status}',
                'metric_name': 'dashboard_status',
                'metric_value': 0,
                'threshold': 1
            })
        
        # Store alerts
        if alerts:
            self._store_alerts(alerts)
        
        return alerts
    
    def _store_alerts(self, alerts: List[Dict]):
        """Store performance alerts in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for alert in alerts:
                    cursor.execute("""
                        INSERT INTO performance_alerts (
                            timestamp, alert_type, severity, message,
                            metric_name, metric_value, threshold
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.now(timezone.utc).isoformat(),
                        alert['type'],
                        alert['severity'],
                        alert['message'],
                        alert['metric_name'],
                        alert['metric_value'],
                        alert['threshold']
                    ))
                
                conn.commit()
                logger.warning(f"Stored {len(alerts)} performance alerts")
                
        except Exception as e:
            logger.error(f"Failed to store alerts: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        try:
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()
            alerts = self.check_thresholds(system_metrics, app_metrics)
            
            # Determine overall health
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            warning_alerts = [a for a in alerts if a['severity'] == 'warning']
            
            if critical_alerts:
                overall_status = 'critical'
            elif warning_alerts:
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
            
            return {
                'status': overall_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_metrics': asdict(system_metrics),
                'application_metrics': asdict(app_metrics),
                'alerts': alerts,
                'uptime_seconds': system_metrics.uptime_seconds
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle."""
        try:
            logger.info("Starting monitoring cycle")
            
            # Collect metrics
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()
            
            # Store metrics
            self.store_metrics(system_metrics, app_metrics)
            
            # Check thresholds and generate alerts
            alerts = self.check_thresholds(system_metrics, app_metrics)
            
            # Log summary
            logger.info(
                f"Monitoring cycle complete - "
                f"CPU: {system_metrics.cpu_percent:.1f}%, "
                f"Memory: {system_metrics.memory_percent:.1f}%, "
                f"Disk: {system_metrics.disk_usage_percent:.1f}%, "
                f"Alerts: {len(alerts)}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return False

def main():
    """Main monitoring function."""
    monitor = PerformanceMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--health':
        # Return health status and exit
        health = monitor.get_health_status()
        print(json.dumps(health, indent=2))
        return
    
    # Run continuous monitoring
    logger.info("Starting TRAE AI Performance Monitor")
    
    try:
        while True:
            monitor.run_monitoring_cycle()
            time.sleep(60)  # Monitor every minute
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()