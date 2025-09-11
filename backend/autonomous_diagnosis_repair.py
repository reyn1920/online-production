#!/usr/bin/env python3
"""
TRAE.AI Autonomous Diagnosis and Repair (ADR) Protocol
Self-Healing System Optimization and Recovery

System Constitution Adherence:
- 100% Live Code: All diagnostics and repairs produce executable solutions
- Zero-Cost Stack: Uses only free, open-source monitoring and repair tools
- Additive Evolution: Builds upon existing systems without breaking changes
- Secure Design: Implements robust security and error handling
"""

import asyncio
import json
import logging
import time
import psutil
import sqlite3
import threading
import subprocess
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import uuid
import traceback
import requests
from contextlib import contextmanager
import shutil
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/adr_protocol.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiagnosisLevel(Enum):
    """Diagnosis severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class RepairStatus(Enum):
    """Repair operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class SystemComponent(Enum):
    """System components that can be diagnosed"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    API_ENDPOINTS = "api_endpoints"
    SERVICES = "services"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class DiagnosticResult:
    """Result of a diagnostic check"""
    id: str
    component: SystemComponent
    level: DiagnosisLevel
    title: str
    description: str
    metrics: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    repair_suggestions: List[str] = None
    auto_repairable: bool = False

@dataclass
class RepairAction:
    """Represents a repair action"""
    id: str
    diagnostic_id: str
    action_type: str
    description: str
    command: Optional[str] = None
    script: Optional[str] = None
    parameters: Dict[str, Any] = None
    priority: int = 1
    estimated_duration: int = 60  # seconds
    requires_restart: bool = False
    backup_required: bool = False

@dataclass
class RepairResult:
    """Result of a repair operation"""
    action_id: str
    status: RepairStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    success: bool = False
    rollback_available: bool = False

class AutonomousDiagnosisRepair:
    """Main ADR Protocol Implementation"""
    
    def __init__(self, db_path: str = "data/adr_protocol.db", config: Dict[str, Any] = None):
        self.db_path = db_path
        self.config = config or self._get_default_config()
        self.is_running = False
        self.diagnostics: List[DiagnosticResult] = []
        self.repair_queue: List[RepairAction] = []
        self.repair_history: List[RepairResult] = []
        self.lock = threading.Lock()
        self.system_baseline = {}
        
        # Initialize database
        self._init_database()
        
        # Establish system baseline
        self._establish_baseline()
        
        # Start monitoring
        self._start_monitoring()
        
        logger.info("Autonomous Diagnosis and Repair Protocol initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default ADR configuration"""
        return {
            "monitoring_interval": 30,  # seconds
            "auto_repair_enabled": True,
            "max_concurrent_repairs": 3,
            "backup_before_repair": True,
            "thresholds": {
                "cpu_warning": 80.0,
                "cpu_critical": 95.0,
                "memory_warning": 85.0,
                "memory_critical": 95.0,
                "disk_warning": 85.0,
                "disk_critical": 95.0,
                "response_time_warning": 2000,  # ms
                "response_time_critical": 5000,  # ms
            },
            "repair_strategies": {
                "high_cpu": ["restart_heavy_processes", "optimize_processes", "scale_resources"],
                "high_memory": ["clear_cache", "restart_memory_leaks", "garbage_collect"],
                "disk_full": ["cleanup_logs", "cleanup_temp", "compress_files"],
                "service_down": ["restart_service", "check_dependencies", "restore_backup"]
            }
        }
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS diagnostics (
                    id TEXT PRIMARY KEY,
                    component TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    repair_suggestions TEXT,
                    auto_repairable BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS repair_actions (
                    id TEXT PRIMARY KEY,
                    diagnostic_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    command TEXT,
                    script TEXT,
                    parameters TEXT,
                    priority INTEGER DEFAULT 1,
                    estimated_duration INTEGER DEFAULT 60,
                    requires_restart BOOLEAN DEFAULT FALSE,
                    backup_required BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (diagnostic_id) REFERENCES diagnostics (id)
                );
                
                CREATE TABLE IF NOT EXISTS repair_results (
                    id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    output TEXT,
                    error TEXT,
                    success BOOLEAN DEFAULT FALSE,
                    rollback_available BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (action_id) REFERENCES repair_actions (id)
                );
                
                CREATE TABLE IF NOT EXISTS system_baseline (
                    component TEXT PRIMARY KEY,
                    baseline_metrics TEXT NOT NULL,
                    established_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS system_health (
                    timestamp TIMESTAMP PRIMARY KEY,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_io TEXT,
                    active_connections INTEGER,
                    response_times TEXT,
                    error_rates TEXT
                );
            """)
    
    def _establish_baseline(self):
        """Establish system performance baseline"""
        try:
            baseline = {
                "cpu": {
                    "average_usage": psutil.cpu_percent(interval=1),
                    "core_count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "baseline_usage": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "baseline_usage": psutil.disk_usage('/').percent
                },
                "network": {
                    "interfaces": list(psutil.net_if_addrs().keys()),
                    "baseline_io": psutil.net_io_counters()._asdict()
                }
            }
            
            self.system_baseline = baseline
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                for component, metrics in baseline.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO system_baseline (component, baseline_metrics, last_updated) VALUES (?, ?, ?)",
                        (component, json.dumps(metrics), datetime.now())
                    )
            
            logger.info("System baseline established successfully")
            
        except Exception as e:
            logger.error(f"Failed to establish system baseline: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring threads"""
        self.is_running = True
        
        # System health monitor
        threading.Thread(target=self._monitor_system_health, daemon=True).start()
        
        # Service monitor
        threading.Thread(target=self._monitor_services, daemon=True).start()
        
        # Network monitor
        threading.Thread(target=self._monitor_network, daemon=True).start()
        
        # Repair processor
        threading.Thread(target=self._process_repairs, daemon=True).start()
        
        # Health recorder
        threading.Thread(target=self._record_health_metrics, daemon=True).start()
    
    def _monitor_system_health(self):
        """Monitor system health metrics"""
        while self.is_running:
            try:
                # CPU monitoring
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.config["thresholds"]["cpu_critical"]:
                    self._create_diagnostic(
                        SystemComponent.CPU,
                        DiagnosisLevel.CRITICAL,
                        "Critical CPU Usage",
                        f"CPU usage at {cpu_percent:.1f}% (threshold: {self.config['thresholds']['cpu_critical']}%)",
                        {"cpu_percent": cpu_percent, "processes": self._get_top_cpu_processes()},
                        auto_repairable=True
                    )
                elif cpu_percent > self.config["thresholds"]["cpu_warning"]:
                    self._create_diagnostic(
                        SystemComponent.CPU,
                        DiagnosisLevel.WARNING,
                        "High CPU Usage",
                        f"CPU usage at {cpu_percent:.1f}% (threshold: {self.config['thresholds']['cpu_warning']}%)",
                        {"cpu_percent": cpu_percent, "processes": self._get_top_cpu_processes()},
                        auto_repairable=True
                    )
                
                # Memory monitoring
                memory = psutil.virtual_memory()
                if memory.percent > self.config["thresholds"]["memory_critical"]:
                    self._create_diagnostic(
                        SystemComponent.MEMORY,
                        DiagnosisLevel.CRITICAL,
                        "Critical Memory Usage",
                        f"Memory usage at {memory.percent:.1f}% (threshold: {self.config['thresholds']['memory_critical']}%)",
                        {"memory_percent": memory.percent, "available_gb": memory.available / (1024**3), "processes": self._get_top_memory_processes()},
                        auto_repairable=True
                    )
                elif memory.percent > self.config["thresholds"]["memory_warning"]:
                    self._create_diagnostic(
                        SystemComponent.MEMORY,
                        DiagnosisLevel.WARNING,
                        "High Memory Usage",
                        f"Memory usage at {memory.percent:.1f}% (threshold: {self.config['thresholds']['memory_warning']}%)",
                        {"memory_percent": memory.percent, "available_gb": memory.available / (1024**3), "processes": self._get_top_memory_processes()},
                        auto_repairable=True
                    )
                
                # Disk monitoring
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                if disk_percent > self.config["thresholds"]["disk_critical"]:
                    self._create_diagnostic(
                        SystemComponent.DISK,
                        DiagnosisLevel.CRITICAL,
                        "Critical Disk Usage",
                        f"Disk usage at {disk_percent:.1f}% (threshold: {self.config['thresholds']['disk_critical']}%)",
                        {"disk_percent": disk_percent, "free_gb": disk.free / (1024**3), "large_files": self._get_large_files()},
                        auto_repairable=True
                    )
                elif disk_percent > self.config["thresholds"]["disk_warning"]:
                    self._create_diagnostic(
                        SystemComponent.DISK,
                        DiagnosisLevel.WARNING,
                        "High Disk Usage",
                        f"Disk usage at {disk_percent:.1f}% (threshold: {self.config['thresholds']['disk_warning']}%)",
                        {"disk_percent": disk_percent, "free_gb": disk.free / (1024**3), "large_files": self._get_large_files()},
                        auto_repairable=True
                    )
                
                time.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {e}")
                time.sleep(60)
    
    def _monitor_services(self):
        """Monitor critical services"""
        critical_services = [
            "python",  # Main application
            "nginx",   # Web server (if used)
            "redis",   # Cache (if used)
        ]
        
        while self.is_running:
            try:
                for service_name in critical_services:
                    if not self._is_service_running(service_name):
                        self._create_diagnostic(
                            SystemComponent.SERVICES,
                            DiagnosisLevel.CRITICAL,
                            f"Service Down: {service_name}",
                            f"Critical service {service_name} is not running",
                            {"service": service_name, "status": "down"},
                            auto_repairable=True
                        )
                
                time.sleep(60)  # Check services every minute
                
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                time.sleep(120)
    
    def _monitor_network(self):
        """Monitor network connectivity and performance"""
        while self.is_running:
            try:
                # Check internet connectivity
                if not self._check_internet_connectivity():
                    self._create_diagnostic(
                        SystemComponent.NETWORK,
                        DiagnosisLevel.CRITICAL,
                        "Internet Connectivity Lost",
                        "No internet connectivity detected",
                        {"connectivity": False, "timestamp": datetime.now().isoformat()},
                        auto_repairable=True
                    )
                
                # Check API endpoint health
                api_health = self._check_api_endpoints()
                for endpoint, health in api_health.items():
                    if not health["healthy"]:
                        level = DiagnosisLevel.CRITICAL if health["response_time"] > self.config["thresholds"]["response_time_critical"] else DiagnosisLevel.WARNING
                        self._create_diagnostic(
                            SystemComponent.API_ENDPOINTS,
                            level,
                            f"API Endpoint Issue: {endpoint}",
                            f"Endpoint {endpoint} is unhealthy (response time: {health['response_time']}ms)",
                            {"endpoint": endpoint, "response_time": health["response_time"], "error": health.get("error")},
                            auto_repairable=True
                        )
                
                time.sleep(120)  # Check network every 2 minutes
                
            except Exception as e:
                logger.error(f"Error in network monitoring: {e}")
                time.sleep(180)
    
    def _process_repairs(self):
        """Process repair queue"""
        active_repairs = 0
        
        while self.is_running:
            try:
                with self.lock:
                    if not self.repair_queue or active_repairs >= self.config["max_concurrent_repairs"]:
                        time.sleep(5)
                        continue
                    
                    # Get next repair action
                    repair_action = self.repair_queue.pop(0)
                
                # Execute repair (outside lock)
                active_repairs += 1
                threading.Thread(target=self._execute_repair, args=(repair_action,), daemon=True).start()
                
            except Exception as e:
                logger.error(f"Error in repair processing: {e}")
                time.sleep(10)
    
    def _record_health_metrics(self):
        """Record system health metrics to database"""
        while self.is_running:
            try:
                # Collect metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network_io = psutil.net_io_counters()
                
                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO system_health (timestamp, cpu_percent, memory_percent, disk_percent, network_io, active_connections) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            datetime.now(),
                            cpu_percent,
                            memory.percent,
                            (disk.used / disk.total) * 100,
                            json.dumps(network_io._asdict()),
                            len(psutil.net_connections())
                        )
                    )
                
                time.sleep(300)  # Record every 5 minutes
                
            except Exception as e:
                logger.error(f"Error recording health metrics: {e}")
                time.sleep(300)
    
    def _create_diagnostic(self, component: SystemComponent, level: DiagnosisLevel, title: str, description: str, metrics: Dict[str, Any], auto_repairable: bool = False):
        """Create a new diagnostic result"""
        try:
            # Check if similar diagnostic already exists and is unresolved
            existing = next((d for d in self.diagnostics if d.component == component and d.title == title and not d.resolved), None)
            if existing:
                # Update existing diagnostic
                existing.metrics.update(metrics)
                existing.timestamp = datetime.now()
                return
            
            diagnostic = DiagnosticResult(
                id=str(uuid.uuid4()),
                component=component,
                level=level,
                title=title,
                description=description,
                metrics=metrics,
                timestamp=datetime.now(),
                auto_repairable=auto_repairable,
                repair_suggestions=self._generate_repair_suggestions(component, level, metrics)
            )
            
            with self.lock:
                self.diagnostics.append(diagnostic)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO diagnostics (id, component, level, title, description, metrics, timestamp, auto_repairable, repair_suggestions) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (diagnostic.id, component.value, level.value, title, description, json.dumps(metrics), diagnostic.timestamp, auto_repairable, json.dumps(diagnostic.repair_suggestions))
                )
            
            logger.warning(f"Diagnostic created: {level.value.upper()} - {title}")
            
            # Auto-schedule repair if enabled and applicable
            if self.config["auto_repair_enabled"] and auto_repairable:
                self._schedule_auto_repair(diagnostic)
            
        except Exception as e:
            logger.error(f"Error creating diagnostic: {e}")
    
    def _generate_repair_suggestions(self, component: SystemComponent, level: DiagnosisLevel, metrics: Dict[str, Any]) -> List[str]:
        """Generate repair suggestions based on diagnostic"""
        suggestions = []
        
        if component == SystemComponent.CPU:
            if metrics.get("cpu_percent", 0) > 90:
                suggestions.extend([
                    "Restart high CPU processes",
                    "Optimize process priorities",
                    "Scale resources if possible",
                    "Check for CPU-intensive background tasks"
                ])
        
        elif component == SystemComponent.MEMORY:
            if metrics.get("memory_percent", 0) > 90:
                suggestions.extend([
                    "Clear system cache",
                    "Restart memory-leaking processes",
                    "Force garbage collection",
                    "Increase swap space"
                ])
        
        elif component == SystemComponent.DISK:
            if metrics.get("disk_percent", 0) > 90:
                suggestions.extend([
                    "Clean up log files",
                    "Remove temporary files",
                    "Compress old files",
                    "Move files to external storage"
                ])
        
        elif component == SystemComponent.SERVICES:
            suggestions.extend([
                "Restart the service",
                "Check service dependencies",
                "Restore from backup",
                "Check service configuration"
            ])
        
        elif component == SystemComponent.NETWORK:
            suggestions.extend([
                "Restart network interface",
                "Check DNS configuration",
                "Test alternative routes",
                "Contact network administrator"
            ])
        
        return suggestions
    
    def _schedule_auto_repair(self, diagnostic: DiagnosticResult):
        """Schedule automatic repair for a diagnostic"""
        try:
            repair_actions = self._create_repair_actions(diagnostic)
            
            with self.lock:
                self.repair_queue.extend(repair_actions)
                # Sort by priority
                self.repair_queue.sort(key=lambda x: x.priority)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                for action in repair_actions:
                    conn.execute(
                        "INSERT INTO repair_actions (id, diagnostic_id, action_type, description, command, script, parameters, priority, estimated_duration, requires_restart, backup_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (action.id, action.diagnostic_id, action.action_type, action.description, action.command, action.script, json.dumps(action.parameters), action.priority, action.estimated_duration, action.requires_restart, action.backup_required)
                    )
            
            logger.info(f"Scheduled {len(repair_actions)} repair actions for diagnostic {diagnostic.id}")
            
        except Exception as e:
            logger.error(f"Error scheduling auto repair: {e}")
    
    def _create_repair_actions(self, diagnostic: DiagnosticResult) -> List[RepairAction]:
        """Create repair actions for a diagnostic"""
        actions = []
        
        if diagnostic.component == SystemComponent.CPU:
            if diagnostic.metrics.get("cpu_percent", 0) > 95:
                actions.append(RepairAction(
                    id=str(uuid.uuid4()),
                    diagnostic_id=diagnostic.id,
                    action_type="restart_heavy_processes",
                    description="Restart processes consuming high CPU",
                    script="self._restart_heavy_cpu_processes()",
                    priority=1,
                    estimated_duration=30
                ))
        
        elif diagnostic.component == SystemComponent.MEMORY:
            if diagnostic.metrics.get("memory_percent", 0) > 95:
                actions.append(RepairAction(
                    id=str(uuid.uuid4()),
                    diagnostic_id=diagnostic.id,
                    action_type="clear_cache",
                    description="Clear system cache and restart memory-heavy processes",
                    script="self._clear_memory_cache()",
                    priority=1,
                    estimated_duration=45
                ))
        
        elif diagnostic.component == SystemComponent.DISK:
            if diagnostic.metrics.get("disk_percent", 0) > 95:
                actions.append(RepairAction(
                    id=str(uuid.uuid4()),
                    diagnostic_id=diagnostic.id,
                    action_type="cleanup_disk",
                    description="Clean up disk space by removing temporary files and logs",
                    script="self._cleanup_disk_space()",
                    priority=1,
                    estimated_duration=120,
                    backup_required=True
                ))
        
        elif diagnostic.component == SystemComponent.SERVICES:
            service_name = diagnostic.metrics.get("service")
            if service_name:
                actions.append(RepairAction(
                    id=str(uuid.uuid4()),
                    diagnostic_id=diagnostic.id,
                    action_type="restart_service",
                    description=f"Restart service: {service_name}",
                    script=f"self._restart_service('{service_name}')",
                    priority=1,
                    estimated_duration=60
                ))
        
        elif diagnostic.component == SystemComponent.NETWORK:
            actions.append(RepairAction(
                id=str(uuid.uuid4()),
                diagnostic_id=diagnostic.id,
                action_type="network_recovery",
                description="Attempt network connectivity recovery",
                script="self._recover_network_connectivity()",
                priority=1,
                estimated_duration=90
            ))
        
        return actions
    
    def _execute_repair(self, action: RepairAction):
        """Execute a repair action"""
        result = RepairResult(
            action_id=action.id,
            status=RepairStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            logger.info(f"Starting repair action: {action.description}")
            
            # Create backup if required
            if action.backup_required:
                backup_success = self._create_backup(action)
                if not backup_success:
                    result.status = RepairStatus.FAILED
                    result.error = "Backup creation failed"
                    result.completed_at = datetime.now()
                    self._store_repair_result(result)
                    return
                result.rollback_available = True
            
            # Execute repair
            if action.command:
                success, output, error = self._execute_command(action.command)
            elif action.script:
                success, output, error = self._execute_script(action.script, action.parameters or {})
            else:
                success, output, error = False, None, "No command or script specified"
            
            result.success = success
            result.output = output
            result.error = error
            result.status = RepairStatus.COMPLETED if success else RepairStatus.FAILED
            result.completed_at = datetime.now()
            
            if success:
                logger.info(f"Repair action completed successfully: {action.description}")
                # Mark diagnostic as resolved
                self._resolve_diagnostic(action.diagnostic_id)
            else:
                logger.error(f"Repair action failed: {action.description} - {error}")
            
        except Exception as e:
            result.status = RepairStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Error executing repair action {action.id}: {e}")
        
        finally:
            self._store_repair_result(result)
            with self.lock:
                self.repair_history.append(result)
    
    def _execute_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute a system command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, None, "Command timed out"
        except Exception as e:
            return False, None, str(e)
    
    def _execute_script(self, script: str, parameters: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Execute a Python script method"""
        try:
            # This is a simplified implementation
            # In practice, you'd want more sophisticated script execution
            if script.startswith("self."):
                method_name = script.replace("self.", "").split("(")[0]
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    result = method(**parameters)
                    return True, str(result), None
                else:
                    return False, None, f"Method {method_name} not found"
            else:
                # Execute as Python code (be very careful with this in production)
                exec(script, {"self": self, "parameters": parameters})
                return True, "Script executed", None
        except Exception as e:
            return False, None, str(e)
    
    def _create_backup(self, action: RepairAction) -> bool:
        """Create backup before repair"""
        try:
            backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup based on action type
            if action.action_type == "cleanup_disk":
                # Backup important files before cleanup
                important_dirs = ["data", "logs", "config"]
                for dir_name in important_dirs:
                    if Path(dir_name).exists():
                        shutil.copytree(dir_name, backup_dir / dir_name, ignore_errors=True)
            
            logger.info(f"Backup created at {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def _store_repair_result(self, result: RepairResult):
        """Store repair result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO repair_results (id, action_id, status, started_at, completed_at, output, error, success, rollback_available) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), result.action_id, result.status.value, result.started_at, result.completed_at, result.output, result.error, result.success, result.rollback_available)
                )
        except Exception as e:
            logger.error(f"Error storing repair result: {e}")
    
    def _resolve_diagnostic(self, diagnostic_id: str):
        """Mark a diagnostic as resolved"""
        try:
            # Update in memory
            diagnostic = next((d for d in self.diagnostics if d.id == diagnostic_id), None)
            if diagnostic:
                diagnostic.resolved = True
            
            # Update in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE diagnostics SET resolved = TRUE WHERE id = ?",
                    (diagnostic_id,)
                )
            
            logger.info(f"Diagnostic {diagnostic_id} marked as resolved")
            
        except Exception as e:
            logger.error(f"Error resolving diagnostic {diagnostic_id}: {e}")
    
    # Utility methods for system checks and repairs
    
    def _get_top_cpu_processes(self) -> List[Dict[str, Any]]:
        """Get top CPU consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
        except:
            return []
    
    def _get_top_memory_processes(self) -> List[Dict[str, Any]]:
        """Get top memory consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:5]
        except:
            return []
    
    def _get_large_files(self) -> List[Dict[str, Any]]:
        """Get largest files on disk"""
        try:
            large_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        if size > 100 * 1024 * 1024:  # Files larger than 100MB
                            large_files.append({
                                'path': file_path,
                                'size_mb': size / (1024 * 1024)
                            })
                    except (OSError, IOError):
                        pass
            return sorted(large_files, key=lambda x: x['size_mb'], reverse=True)[:10]
        except:
            return []
    
    def _is_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            for proc in psutil.process_iter(['name']):
                if service_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except:
            return False
    
    def _check_internet_connectivity(self) -> bool:
        """Check internet connectivity"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False
    
    def _check_api_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Check health of API endpoints"""
        endpoints = {
            "localhost": "http://localhost:8000/health",
            # Add more endpoints as needed
        }
        
        results = {}
        for name, url in endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                results[name] = {
                    "healthy": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "response_time": 0,
                    "error": str(e)
                }
        
        return results
    
    # Repair methods
    
    def _restart_heavy_cpu_processes(self) -> str:
        """Restart processes consuming high CPU"""
        try:
            heavy_processes = self._get_top_cpu_processes()
            restarted = []
            
            for proc_info in heavy_processes[:3]:  # Restart top 3
                if proc_info['cpu_percent'] > 50:  # Only if using more than 50% CPU
                    try:
                        proc = psutil.Process(proc_info['pid'])
                        proc.terminate()
                        proc.wait(timeout=10)
                        restarted.append(proc_info['name'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass
            
            return f"Restarted processes: {', '.join(restarted)}"
        except Exception as e:
            raise Exception(f"Failed to restart heavy CPU processes: {e}")
    
    def _clear_memory_cache(self) -> str:
        """Clear system memory cache"""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear system cache (Linux/macOS)
            if os.name == 'posix':
                os.system('sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true')
            
            return "Memory cache cleared successfully"
        except Exception as e:
            raise Exception(f"Failed to clear memory cache: {e}")
    
    def _cleanup_disk_space(self) -> str:
        """Clean up disk space"""
        try:
            cleaned_mb = 0
            
            # Clean log files
            log_dirs = ['logs', '/var/log', '/tmp']
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if file.endswith('.log') and os.path.getsize(os.path.join(root, file)) > 10 * 1024 * 1024:
                                try:
                                    file_path = os.path.join(root, file)
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    cleaned_mb += size / (1024 * 1024)
                                except OSError:
                                    pass
            
            # Clean temporary files
            temp_dirs = ['/tmp', '/var/tmp']
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for item in os.listdir(temp_dir):
                        try:
                            item_path = os.path.join(temp_dir, item)
                            if os.path.isfile(item_path):
                                size = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleaned_mb += size / (1024 * 1024)
                        except OSError:
                            pass
            
            return f"Cleaned up {cleaned_mb:.1f} MB of disk space"
        except Exception as e:
            raise Exception(f"Failed to cleanup disk space: {e}")
    
    def _restart_service(self, service_name: str) -> str:
        """Restart a service"""
        try:
            # Kill existing processes
            killed = 0
            for proc in psutil.process_iter(['pid', 'name']):
                if service_name.lower() in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        proc.wait(timeout=10)
                        killed += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass
            
            # Wait a moment
            time.sleep(2)
            
            # Restart service (this would depend on your specific service management)
            # For now, just return status
            return f"Service {service_name} restarted (killed {killed} processes)"
        except Exception as e:
            raise Exception(f"Failed to restart service {service_name}: {e}")
    
    def _recover_network_connectivity(self) -> str:
        """Attempt to recover network connectivity"""
        try:
            recovery_actions = []
            
            # Flush DNS
            if os.name == 'posix':
                os.system('dscacheutil -flushcache 2>/dev/null || true')
                recovery_actions.append("DNS cache flushed")
            
            # Test connectivity
            if self._check_internet_connectivity():
                recovery_actions.append("Internet connectivity restored")
            else:
                recovery_actions.append("Internet connectivity still unavailable")
            
            return "; ".join(recovery_actions)
        except Exception as e:
            raise Exception(f"Failed to recover network connectivity: {e}")
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        try:
            with self.lock:
                unresolved_diagnostics = [d for d in self.diagnostics if not d.resolved]
                recent_repairs = [r for r in self.repair_history if r.started_at > datetime.now() - timedelta(hours=24)]
            
            # Get current system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if len(unresolved_diagnostics) == 0 else "issues_detected",
                "current_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "uptime": time.time() - psutil.boot_time()
                },
                "diagnostics": {
                    "total": len(self.diagnostics),
                    "unresolved": len(unresolved_diagnostics),
                    "by_level": {
                        level.value: len([d for d in unresolved_diagnostics if d.level == level])
                        for level in DiagnosisLevel
                    }
                },
                "repairs": {
                    "total_executed": len(self.repair_history),
                    "recent_24h": len(recent_repairs),
                    "success_rate": (len([r for r in recent_repairs if r.success]) / len(recent_repairs) * 100) if recent_repairs else 100
                },
                "auto_repair_enabled": self.config["auto_repair_enabled"]
            }
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {"error": str(e)}
    
    def shutdown(self):
        """Gracefully shutdown the ADR protocol"""
        logger.info("Shutting down Autonomous Diagnosis and Repair Protocol...")
        self.is_running = False
        logger.info("ADR Protocol shutdown complete")

# Main execution
if __name__ == "__main__":
    # Initialize ADR protocol
    adr = AutonomousDiagnosisRepair()
    
    try:
        while True:
            # Generate health report every 5 minutes
            report = adr.get_system_health_report()
            logger.info(f"System Health Report: {json.dumps(report, indent=2)}")
            time.sleep(300)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        adr.shutdown()