#!/usr/bin/env python3
"""
Full Automation Pipeline - Complete AI CEO Business Automation System

This pipeline orchestrates:
1. All AI agents (marketing, financial, monetization, stealth automation)
2. API discovery and management systems
3. Content generation and distribution
4. Revenue optimization and cost management
5. Market analysis and competitive intelligence
6. Customer acquisition and retention
7. Real-time decision making and execution
8. Performance monitoring and optimization

Author: TRAEAI System
Version: 2.0.0
"""

import asyncio
import json
import logging
import queue
import signal
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# Import our AI CEO components
try:
    from ai_ceo_master_controller import AICEOMasterController
    from api_manager import APIManager
    from automation_controller import AutomationController
    from autonomous_decision_engine import (
        AutonomousDecisionEngine,
        DecisionRecommendation,
    )
except ImportError as e:
    logging.warning(f"Some components not available: {e}")

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status."""
    
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"
    OPTIMIZING = "optimizing"


class TaskPriority(Enum):
    """Task priority levels."""
    
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class PipelineTask:
    """Represents a task in the automation pipeline."""
    
    id: str
    name: str
    description: str
    priority: TaskPriority
    agent_type: str
    function_name: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # seconds
    scheduled_time: Optional[datetime] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    
    total_tasks_executed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    revenue_generated: float = 0.0
    cost_saved: float = 0.0
    decisions_made: int = 0
    automation_efficiency: float = 0.0
    uptime_percentage: float = 100.0
    last_updated: datetime = None


class FullAutomationPipeline:
    """Complete AI CEO automation pipeline orchestrator."""
    
    def __init__(self, config_path: str = "pipeline_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Pipeline state
        self.status = PipelineStatus.INITIALIZING
        self.start_time = datetime.now()
        self.metrics = PipelineMetrics(last_updated=datetime.now())
        
        # Task management
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, PipelineTask] = {}
        self.completed_tasks: List[PipelineTask] = []
        self.task_history: List[PipelineTask] = []
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 10))
        self.running = False
        self.pipeline_thread = None
        
        # AI Components
        self.ai_ceo = None
        self.decision_engine = None
        self.automation_controller = None
        self.api_manager = None
        
        # Agent management
        self.agents = {}
        self.agent_status = {}
        
        # Performance tracking
        self.performance_history = []
        self.optimization_cycles = 0
        
        # Database
        self.db_path = "pipeline.db"
        self._init_database()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 Full Automation Pipeline initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {
                "max_workers": 10,
                "task_timeout": 300,
                "max_retries": 3,
                "optimization_interval": 3600,  # 1 hour
                "health_check_interval": 60,  # 1 minute
                "metrics_update_interval": 300,  # 5 minutes
                "auto_scaling": True,
                "performance_threshold": 0.8,
                "error_threshold": 0.1,
                "agent_configs": {
                    "marketing_agent": {
                        "enabled": True,
                        "schedule": "*/15 * * * *",  # Every 15 minutes
                        "priority": "high",
                    },
                    "financial_agent": {
                        "enabled": True,
                        "schedule": "0 */6 * * *",  # Every 6 hours
                        "priority": "high",
                    },
                    "monetization_agent": {
                        "enabled": True,
                        "schedule": "*/30 * * * *",  # Every 30 minutes
                        "priority": "medium",
                    },
                    "stealth_automation_agent": {
                        "enabled": True,
                        "schedule": "*/5 * * * *",  # Every 5 minutes
                        "priority": "critical",
                    },
                    "content_agent": {
                        "enabled": True,
                        "schedule": "0 */2 * * *",  # Every 2 hours
                        "priority": "medium",
                    },
                },
                "decision_engine": {
                    "enabled": True,
                    "analysis_interval": 1800,  # 30 minutes
                    "auto_execute_threshold": 0.9,
                },
                "api_discovery": {
                    "enabled": True,
                    "discovery_interval": 7200,  # 2 hours
                    "auto_integrate": True,
                },
                "monitoring": {
                    "enabled": True,
                    "alert_thresholds": {
                        "error_rate": 0.1,
                        "response_time": 5.0,
                        "cpu_usage": 0.8,
                        "memory_usage": 0.8,
                    },
                },
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2, default=str)
    
    def _init_database(self):
        """Initialize pipeline database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                priority INTEGER,
                agent_type TEXT,
                function_name TEXT,
                parameters TEXT,
                dependencies TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                timeout INTEGER DEFAULT 300,
                scheduled_time TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                error TEXT
            )
            """
        )
        
        # Metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_tasks_executed INTEGER,
                successful_tasks INTEGER,
                failed_tasks INTEGER,
                average_execution_time REAL,
                revenue_generated REAL,
                cost_saved REAL,
                decisions_made INTEGER,
                automation_efficiency REAL,
                uptime_percentage REAL
            )
            """
        )
        
        # Performance history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                execution_time REAL,
                success BOOLEAN,
                error_message TEXT
            )
            """
        )
        
        conn.commit()
        conn.close()
        logger.info("📊 Pipeline database initialized")
    
    async def initialize_components(self):
        """Initialize all AI components and agents."""
        logger.info("🔧 Initializing AI components...")
        
        try:
            # Initialize AI CEO Master Controller
            self.ai_ceo = AICEOMasterController()
            await self.ai_ceo.initialize()
            
            # Initialize Decision Engine
            self.decision_engine = AutonomousDecisionEngine()
            
            # Initialize Automation Controller
            self.automation_controller = AutomationController()
            
            # Initialize API Manager
            self.api_manager = APIManager()
            
            # Register all available agents
            await self._register_agents()
            
            # Setup scheduled tasks
            self._setup_scheduled_tasks()
            
            logger.info("✅ All AI components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            self.status = PipelineStatus.ERROR
            raise
    
    async def _register_agents(self):
        """Register all available AI agents."""
        agent_configs = self.config.get("agent_configs", {})
        
        for agent_name, config in agent_configs.items():
            if config.get("enabled", True):
                try:
                    # Dynamic import of agent module
                    agent_module = __import__(agent_name)
                    agent_class = getattr(agent_module, agent_name.title().replace("_", ""))
                    
                    self.agents[agent_name] = agent_class()
                    self.agent_status[agent_name] = {
                        "status": "ready",
                        "last_execution": None,
                        "success_rate": 1.0,
                        "total_executions": 0,
                        "average_response_time": 0.0,
                    }
                    
                    logger.info(f"📋 Registered agent: {agent_name}")
                    
                except ImportError:
                    logger.warning(f"⚠️ Agent {agent_name} not available")
                except Exception as e:
                    logger.error(f"❌ Failed to register agent {agent_name}: {e}")
    
    def _setup_scheduled_tasks(self):
        """Setup scheduled tasks for agents."""
        agent_configs = self.config.get("agent_configs", {})
        
        for agent_name, config in agent_configs.items():
            if config.get("enabled", True) and "schedule" in config:
                schedule_str = config["schedule"]
                priority = TaskPriority[config.get("priority", "medium").upper()]
                
                # Create scheduled task
                task = PipelineTask(
                    id=f"{agent_name}_scheduled_{uuid.uuid4().hex[:8]}",
                    name=f"Scheduled {agent_name} execution",
                    description=f"Automated execution of {agent_name}",
                    priority=priority,
                    agent_type=agent_name,
                    function_name="execute",
                    parameters={},
                    dependencies=[],
                    created_at=datetime.now(),
                )
                
                # Schedule recurring execution
                self._schedule_recurring_task(task, schedule_str)
    
    def _schedule_recurring_task(self, task: PipelineTask, schedule_str: str):
        """Schedule a recurring task."""
        # Simple cron-like scheduling implementation
        # In production, use a proper cron library like APScheduler
        
        def schedule_task():
            new_task = PipelineTask(
                id=f"{task.agent_type}_scheduled_{uuid.uuid4().hex[:8]}",
                name=task.name,
                description=task.description,
                priority=task.priority,
                agent_type=task.agent_type,
                function_name=task.function_name,
                parameters=task.parameters.copy(),
                dependencies=task.dependencies.copy(),
                created_at=datetime.now(),
            )
            self.add_task(new_task)
        
        # Basic schedule parsing
        # This is simplified - use APScheduler for production
        if "*/5" in schedule_str:  # Every 5 minutes
            threading.Timer(300, schedule_task).start()
        elif "*/15" in schedule_str:  # Every 15 minutes
            threading.Timer(900, schedule_task).start()
        elif "*/30" in schedule_str:  # Every 30 minutes
            threading.Timer(1800, schedule_task).start()
        
        # Execute immediately for first time
        schedule_task()
    
    def add_task(self, task: PipelineTask):
        """Add a task to the pipeline queue."""
        # Priority queue uses tuple (priority, task)
        self.task_queue.put((task.priority.value, task))
        logger.info(f"📝 Added task: {task.name} (Priority: {task.priority.name})")
    
    async def start_pipeline(self):
        """Start the automation pipeline."""
        logger.info("🚀 Starting Full Automation Pipeline...")
        
        # Initialize all components
        await self.initialize_components()
        
        # Set status to running
        self.status = PipelineStatus.RUNNING
        self.running = True
        
        # Start main pipeline loop
        self.pipeline_thread = threading.Thread(target=self._pipeline_loop, daemon=True)
        self.pipeline_thread.start()
        
        # Start monitoring threads
        self._start_monitoring_threads()
        
        logger.info("✅ Full Automation Pipeline started successfully")
    
    def _pipeline_loop(self):
        """Main pipeline execution loop."""
        while self.running:
            try:
                # Get next task from queue (with timeout)
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Execute task
                asyncio.run(self._execute_task(task))
                
            except Exception as e:
                logger.error(f"❌ Pipeline loop error: {e}")
                time.sleep(1)
    
    async def _execute_task(self, task: PipelineTask):
        """Execute a pipeline task."""
        task.started_at = datetime.now()
        self.active_tasks[task.id] = task
        
        logger.info(f"🔄 Executing task: {task.name}")
        
        try:
            # Get the appropriate agent
            if task.agent_type in self.agents:
                agent = self.agents[task.agent_type]
                
                # Execute the task function
                if hasattr(agent, task.function_name):
                    func = getattr(agent, task.function_name)
                    
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        func(**task.parameters),
                        timeout=task.timeout
                    )
                    
                    task.result = result
                    task.status = "completed"
                    self.metrics.successful_tasks += 1
                    
                    logger.info(f"✅ Task completed: {task.name}")
                    
                else:
                    raise AttributeError(f"Function {task.function_name} not found in agent {task.agent_type}")
            else:
                raise ValueError(f"Agent {task.agent_type} not available")
                
        except asyncio.TimeoutError:
            task.error = f"Task timed out after {task.timeout} seconds"
            task.status = "timeout"
            self.metrics.failed_tasks += 1
            logger.error(f"⏰ Task timed out: {task.name}")
            
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self.metrics.failed_tasks += 1
            logger.error(f"❌ Task failed: {task.name} - {e}")
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "retrying"
                logger.info(f"🔄 Retrying task: {task.name} (Attempt {task.retry_count}/{task.max_retries})")
                
                # Re-queue the task
                self.task_queue.put((task.priority.value, task))
                return
        
        finally:
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
            self.task_history.append(task)
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Update metrics
            self.metrics.total_tasks_executed += 1
            
            # Save task to database
            await self._save_task(task)
    
    def _start_monitoring_threads(self):
        """Start monitoring and optimization threads."""
        
        # Health check thread
        def health_check_loop():
            while self.running:
                try:
                    health_status = self._check_system_health()
                    if not health_status["healthy"]:
                        asyncio.run(self._trigger_self_healing(health_status))
                except Exception as e:
                    logger.error(f"❌ Health check error: {e}")
                
                time.sleep(self.config.get("health_check_interval", 60))
        
        # Metrics update thread
        def metrics_update_loop():
            while self.running:
                try:
                    self._update_pipeline_metrics()
                    asyncio.run(self._save_metrics())
                except Exception as e:
                    logger.error(f"❌ Metrics update error: {e}")
                
                time.sleep(self.config.get("metrics_update_interval", 300))
        
        # Optimization thread
        def optimization_loop():
            while self.running:
                try:
                    if self.status == PipelineStatus.RUNNING:
                        asyncio.run(self._optimize_pipeline())
                except Exception as e:
                    logger.error(f"❌ Optimization error: {e}")
                
                time.sleep(self.config.get("optimization_interval", 3600))
        
        # Start threads
        threading.Thread(target=health_check_loop, daemon=True).start()
        threading.Thread(target=metrics_update_loop, daemon=True).start()
        threading.Thread(target=optimization_loop, daemon=True).start()
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        issues = []
        
        # Check error rate
        if self.metrics.total_tasks_executed > 0:
            error_rate = self.metrics.failed_tasks / self.metrics.total_tasks_executed
            if error_rate > self.config.get("monitoring", {}).get("alert_thresholds", {}).get(
                "error_rate", 0.1
            ):
                issues.append(f"High error rate: {error_rate:.2%}")
        
        # Check agent performance
        for agent_name, status in self.agent_status.items():
            if status["success_rate"] < 0.8:
                issues.append(
                    f"Agent {agent_name} has low success rate: {status['success_rate']:.2%}"
                )
        
        # Check queue size
        if self.task_queue.qsize() > 100:
            issues.append(f"Task queue is large: {self.task_queue.qsize()} tasks")
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _trigger_self_healing(self, health_status: Dict[str, Any]):
        """Trigger self-healing mechanisms."""
        logger.info("🔧 Triggering self-healing mechanisms...")
        
        for issue in health_status["issues"]:
            if "error rate" in issue:
                # Reduce worker count to prevent overload
                self.config["max_workers"] = max(1, self.config["max_workers"] - 1)
                logger.info(f"🔧 Reduced max workers to {self.config['max_workers']}")
            
            elif "success rate" in issue:
                # Restart problematic agents
                for agent_name in self.agent_status:
                    if self.agent_status[agent_name]["success_rate"] < 0.8:
                        await self._restart_agent(agent_name)
            
            elif "queue" in issue:
                # Increase worker count to handle backlog
                if self.config["max_workers"] < 20:
                    self.config["max_workers"] += 2
                    logger.info(f"🔧 Increased max workers to {self.config['max_workers']}")
    
    async def _restart_agent(self, agent_name: str):
        """Restart a problematic agent."""
        logger.info(f"🔄 Restarting agent: {agent_name}")
        
        try:
            # Remove existing agent
            if agent_name in self.agents:
                del self.agents[agent_name]
            
            # Re-register agent
            await self._register_agents()
            
            logger.info(f"✅ Agent restarted: {agent_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart agent {agent_name}: {e}")
    
    def _update_pipeline_metrics(self):
        """Update pipeline performance metrics."""
        # Calculate automation efficiency
        if self.metrics.total_tasks_executed > 0:
            self.metrics.automation_efficiency = (
                self.metrics.successful_tasks / self.metrics.total_tasks_executed
            )
        
        # Calculate uptime percentage
        uptime = (datetime.now() - self.start_time).total_seconds()
        total_time = uptime  # Simplified - in reality, track downtime
        self.metrics.uptime_percentage = (uptime / total_time) * 100 if total_time > 0 else 100
        
        # Calculate average execution time
        if self.completed_tasks:
            execution_times = [
                (t.completed_at - t.started_at).total_seconds()
                for t in self.completed_tasks
                if t.completed_at and t.started_at
            ]
            if execution_times:
                self.metrics.average_execution_time = sum(execution_times) / len(execution_times)
        
        # Update timestamp
        self.metrics.last_updated = datetime.now()
    
    async def _optimize_pipeline(self):
        """Optimize pipeline performance."""
        logger.info("⚡ Running pipeline optimization...")
        
        self.optimization_cycles += 1
        
        try:
            # Analyze performance patterns
            performance_data = await self._analyze_performance_patterns()
            
            # Optimize task scheduling
            await self._optimize_task_scheduling(performance_data)
            
            # Optimize resource allocation
            await self._optimize_resource_allocation(performance_data)
            
            # Save updated configuration
            self._save_config(self.config)
            
            logger.info(f"✅ Pipeline optimization completed (Cycle {self.optimization_cycles})")
            
        except Exception as e:
            logger.error(f"❌ Pipeline optimization failed: {e}")
    
    async def _analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns for optimization."""
        # Analyze agent performance
        agent_performance = {}
        
        for agent_name, status in self.agent_status.items():
            agent_performance[agent_name] = {
                "success_rate": status["success_rate"],
                "average_response_time": status["average_response_time"],
                "total_executions": status["total_executions"],
            }
        
        # Analyze hourly performance patterns
        hourly_performance = {}  # Would analyze by hour of day
        
        return {
            "agent_performance": agent_performance,
            "hourly_performance": hourly_performance,
            "overall_efficiency": self.metrics.automation_efficiency,
        }
    
    async def _optimize_task_scheduling(self, performance_data: Dict[str, Any]):
        """Optimize task scheduling based on performance data."""
        # Optimize high-performing agents
        for agent_name, perf in performance_data["agent_performance"].items():
            if perf["success_rate"] > 0.9 and perf["average_response_time"] < 30:
                # Increase frequency for high-performing agents
                if agent_name in self.config["agent_configs"]:
                    # Could adjust schedule here
                    logger.info(f"📈 Optimizing schedule for high-performing agent: {agent_name}")
    
    async def _optimize_resource_allocation(self, performance_data: Dict[str, Any]):
        """Optimize resource allocation based on performance."""
        # Adjust worker count based on queue size and performance
        queue_size = self.task_queue.qsize()
        
        if queue_size > 50 and self.metrics.automation_efficiency > 0.8:
            # Increase workers if queue is large and performance is good
            self.config["max_workers"] = min(20, self.config["max_workers"] + 1)
            logger.info(f"📈 Increased max workers to {self.config['max_workers']}")
        
        elif queue_size < 10 and self.config["max_workers"] > 5:
            # Decrease workers if queue is small
            self.config["max_workers"] = max(5, self.config["max_workers"] - 1)
            logger.info(f"📉 Decreased max workers to {self.config['max_workers']}")
    
    async def _save_task(self, task: PipelineTask):
        """Save task to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO tasks (
                    id, name, description, priority, agent_type, function_name,
                    parameters, dependencies, retry_count, max_retries, timeout,
                    scheduled_time, created_at, started_at, completed_at,
                    status, result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id, task.name, task.description, task.priority.value,
                    task.agent_type, task.function_name,
                    json.dumps(task.parameters), json.dumps(task.dependencies),
                    task.retry_count, task.max_retries, task.timeout,
                    task.scheduled_time.isoformat() if task.scheduled_time else None,
                    task.created_at.isoformat() if task.created_at else None,
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.status, json.dumps(task.result) if task.result else None,
                    task.error
                )
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save task {task.id}: {e}")
    
    async def _save_metrics(self):
        """Save metrics to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO metrics (
                    timestamp, total_tasks_executed, successful_tasks, failed_tasks,
                    average_execution_time, revenue_generated, cost_saved,
                    decisions_made, automation_efficiency, uptime_percentage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    self.metrics.total_tasks_executed,
                    self.metrics.successful_tasks,
                    self.metrics.failed_tasks,
                    self.metrics.average_execution_time,
                    self.metrics.revenue_generated,
                    self.metrics.cost_saved,
                    self.metrics.decisions_made,
                    self.metrics.automation_efficiency,
                    self.metrics.uptime_percentage
                )
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to save metrics: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop the automation pipeline gracefully."""
        logger.info("🛑 Stopping Full Automation Pipeline...")
        
        self.running = False
        self.status = PipelineStatus.STOPPED
        
        # Wait for active tasks to complete
        timeout = 30  # seconds
        start_time = time.time()
        
        while self.active_tasks and (time.time() - start_time) < timeout:
            logger.info(f"⏳ Waiting for {len(self.active_tasks)} active tasks to complete...")
            time.sleep(1)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Full Automation Pipeline stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            "status": self.status.value,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "metrics": asdict(self.metrics),
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "agent_status": self.agent_status,
            "optimization_cycles": self.optimization_cycles,
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            "pipeline_status": self.get_status(),
            "task_statistics": {
                "total_executed": self.metrics.total_tasks_executed,
                "successful": self.metrics.successful_tasks,
                "failed": self.metrics.failed_tasks,
                "success_rate": self.metrics.successful_tasks
                / max(self.metrics.total_tasks_executed, 1),
                "average_execution_time": self.metrics.average_execution_time,
            },
            "business_impact": {
                "revenue_generated": self.metrics.revenue_generated,
                "cost_saved": self.metrics.cost_saved,
                "decisions_made": self.metrics.decisions_made,
                "automation_efficiency": self.metrics.automation_efficiency,
            },
            "agent_performance": self.agent_status,
            "system_health": self._check_system_health(),
        }


def main():
    """Main function to run the full automation pipeline."""
    
    import asyncio
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("pipeline.log"), logging.StreamHandler()],
    )
    
    async def run_pipeline():
        pipeline = FullAutomationPipeline()
        
        try:
            # Start the pipeline
            await pipeline.start_pipeline()
            
            # Keep running until interrupted
            while pipeline.running:
                await asyncio.sleep(1)
                
                # Log status periodically
                if int(time.time()) % 300 == 0:
                    status = pipeline.get_status()
                    logger.info(
                        f"📊 Pipeline Status: {status['status']} | Tasks: {status['active_tasks']} active, {status['queue_size']} queued"
                    )
        
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
        finally:
            pipeline.stop_pipeline()
    
    # Run the pipeline
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
