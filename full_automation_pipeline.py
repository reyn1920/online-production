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

Author: TRAE.AI System
Version: 2.0.0
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import uuid
import schedule
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal
import sys
from contextlib import asynccontextmanager

# Import our AI CEO components
try:
    from ai_ceo_master_controller import AICEOMasterController
    from autonomous_decision_engine import AutonomousDecisionEngine, DecisionRecommendation
    from automation_controller import AutomationController
    from api_manager import APIManager
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
        
        # Threading and execution
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 10))
        self.running = False
        self.pipeline_thread = None
        
        # AI Components
        self.ai_ceo = None
        self.decision_engine = None
        self.automation_controller = None
        self.api_manager = None
        
        # Agent registry
        self.agents = {}
        self.agent_status = {}
        
        # Performance tracking
        self.performance_history = []
        self.optimization_cycles = 0
        
        # Database for persistence
        self.db_path = "pipeline.db"
        self._init_database()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 Full Automation Pipeline initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {
                'max_workers': 10,
                'task_timeout': 300,
                'max_retries': 3,
                'optimization_interval': 3600,  # 1 hour
                'health_check_interval': 60,  # 1 minute
                'metrics_update_interval': 300,  # 5 minutes
                'auto_scaling': True,
                'performance_threshold': 0.8,
                'error_threshold': 0.1,
                'agent_configs': {
                    'marketing_agent': {
                        'enabled': True,
                        'schedule': '*/15 * * * *',  # Every 15 minutes
                        'priority': 'high'
                    },
                    'financial_agent': {
                        'enabled': True,
                        'schedule': '0 */6 * * *',  # Every 6 hours
                        'priority': 'high'
                    },
                    'monetization_agent': {
                        'enabled': True,
                        'schedule': '*/30 * * * *',  # Every 30 minutes
                        'priority': 'medium'
                    },
                    'stealth_automation_agent': {
                        'enabled': True,
                        'schedule': '*/5 * * * *',  # Every 5 minutes
                        'priority': 'critical'
                    },
                    'content_agent': {
                        'enabled': True,
                        'schedule': '0 */2 * * *',  # Every 2 hours
                        'priority': 'medium'
                    }
                },
                'decision_engine': {
                    'enabled': True,
                    'analysis_interval': 1800,  # 30 minutes
                    'auto_execute_threshold': 0.9
                },
                'api_discovery': {
                    'enabled': True,
                    'discovery_interval': 7200,  # 2 hours
                    'auto_integrate': True
                },
                'monitoring': {
                    'enabled': True,
                    'alert_thresholds': {
                        'error_rate': 0.1,
                        'response_time': 5.0,
                        'cpu_usage': 0.8,
                        'memory_usage': 0.8
                    }
                }
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
    
    def _init_database(self):
        """Initialize pipeline database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pipeline tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_tasks (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                priority INTEGER,
                agent_type TEXT,
                function_name TEXT,
                parameters TEXT,
                dependencies TEXT,
                retry_count INTEGER,
                max_retries INTEGER,
                timeout INTEGER,
                scheduled_time TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT,
                result TEXT,
                error TEXT
            )
        ''')
        
        # Pipeline metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                timestamp TEXT PRIMARY KEY,
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
        ''')
        
        # Agent status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_status (
                agent_name TEXT PRIMARY KEY,
                status TEXT,
                last_execution TEXT,
                success_rate REAL,
                average_response_time REAL,
                total_executions INTEGER,
                last_error TEXT,
                updated_at TEXT
            )
        ''')
        
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
            
            # Register agents
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
        agent_configs = self.config.get('agent_configs', {})
        
        for agent_name, config in agent_configs.items():
            if config.get('enabled', True):
                try:
                    # Dynamically import and register agent
                    agent_module = __import__(agent_name)
                    agent_class = getattr(agent_module, agent_name.title().replace('_', ''))
                    
                    self.agents[agent_name] = agent_class()
                    self.agent_status[agent_name] = {
                        'status': 'ready',
                        'last_execution': None,
                        'success_rate': 1.0,
                        'total_executions': 0,
                        'average_response_time': 0.0
                    }
                    
                    logger.info(f"📋 Registered agent: {agent_name}")
                    
                except ImportError:
                    logger.warning(f"⚠️ Agent {agent_name} not available")
                except Exception as e:
                    logger.error(f"❌ Failed to register agent {agent_name}: {e}")
    
    def _setup_scheduled_tasks(self):
        """Setup scheduled tasks for agents."""
        agent_configs = self.config.get('agent_configs', {})
        
        for agent_name, config in agent_configs.items():
            if config.get('enabled', True) and 'schedule' in config:
                schedule_str = config['schedule']
                priority = TaskPriority[config.get('priority', 'medium').upper()]
                
                # Create recurring task
                task = PipelineTask(
                    id=f"{agent_name}_scheduled_{uuid.uuid4().hex[:8]}",
                    name=f"Scheduled {agent_name} execution",
                    description=f"Automated execution of {agent_name}",
                    priority=priority,
                    agent_type=agent_name,
                    function_name="execute",
                    parameters={},
                    dependencies=[],
                    created_at=datetime.now()
                )
                
                # Schedule the task (simplified scheduling)
                self._schedule_recurring_task(task, schedule_str)
    
    def _schedule_recurring_task(self, task: PipelineTask, schedule_str: str):
        """Schedule a recurring task."""
        # Simplified cron-like scheduling
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
                created_at=datetime.now()
            )
            self.add_task(new_task)
        
        # Parse schedule string and set up timer
        # This is a simplified implementation
        if "*/5" in schedule_str:  # Every 5 minutes
            threading.Timer(300, schedule_task).start()
        elif "*/15" in schedule_str:  # Every 15 minutes
            threading.Timer(900, schedule_task).start()
        elif "*/30" in schedule_str:  # Every 30 minutes
            threading.Timer(1800, schedule_task).start()
        
        # Schedule the first execution
        schedule_task()
    
    def add_task(self, task: PipelineTask):
        """Add a task to the pipeline queue."""
        # Priority queue uses tuples (priority, task)
        self.task_queue.put((task.priority.value, task))
        logger.info(f"📝 Added task: {task.name} (Priority: {task.priority.name})")
    
    async def start_pipeline(self):
        """Start the automation pipeline."""
        logger.info("🚀 Starting Full Automation Pipeline...")
        
        try:
            # Initialize components
            await self.initialize_components()
            
            # Start pipeline
            self.running = True
            self.status = PipelineStatus.RUNNING
            
            # Start main pipeline thread
            self.pipeline_thread = threading.Thread(target=self._run_pipeline_loop, daemon=True)
            self.pipeline_thread.start()
            
            # Start monitoring threads
            self._start_monitoring_threads()
            
            # Start decision engine
            await self._start_decision_engine()
            
            logger.info("✅ Full Automation Pipeline started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start pipeline: {e}")
            self.status = PipelineStatus.ERROR
            raise
    
    def _run_pipeline_loop(self):
        """Main pipeline execution loop."""
        logger.info("🔄 Pipeline execution loop started")
        
        while self.running:
            try:
                # Get next task from queue (with timeout)
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Execute task
                asyncio.run(self._execute_task(task))
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Error in pipeline loop: {e}")
                time.sleep(1)
        
        logger.info("🛑 Pipeline execution loop stopped")
    
    async def _execute_task(self, task: PipelineTask):
        """Execute a pipeline task."""
        task.started_at = datetime.now()
        task.status = "running"
        self.active_tasks[task.id] = task
        
        logger.info(f"⚡ Executing task: {task.name}")
        
        try:
            # Check dependencies
            if not await self._check_dependencies(task):
                task.status = "waiting"
                # Re-queue the task
                self.task_queue.put((task.priority.value, task))
                return
            
            # Execute the task
            result = await self._run_agent_function(task)
            
            # Task completed successfully
            task.completed_at = datetime.now()
            task.status = "completed"
            task.result = result
            
            # Update metrics
            self.metrics.successful_tasks += 1
            self.metrics.total_tasks_executed += 1
            
            # Update agent status
            await self._update_agent_status(task.agent_type, True, task.started_at, task.completed_at)
            
            logger.info(f"✅ Task completed: {task.name}")
            
        except Exception as e:
            # Task failed
            task.error = str(e)
            task.status = "failed"
            task.retry_count += 1
            
            logger.error(f"❌ Task failed: {task.name} - {e}")
            
            # Retry if possible
            if task.retry_count < task.max_retries:
                logger.info(f"🔄 Retrying task: {task.name} (Attempt {task.retry_count + 1})")
                # Re-queue with delay
                threading.Timer(30, lambda: self.task_queue.put((task.priority.value, task))).start()
            else:
                # Max retries reached
                self.metrics.failed_tasks += 1
                self.metrics.total_tasks_executed += 1
                await self._update_agent_status(task.agent_type, False, task.started_at, datetime.now())
        
        finally:
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Add to completed tasks
            self.completed_tasks.append(task)
            self.task_history.append(task)
            
            # Save task to database
            await self._save_task(task)
    
    async def _check_dependencies(self, task: PipelineTask) -> bool:
        """Check if task dependencies are satisfied."""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            # Check if dependency task is completed
            dep_completed = any(
                t.id == dep_id and t.status == "completed" 
                for t in self.completed_tasks
            )
            if not dep_completed:
                return False
        
        return True
    
    async def _run_agent_function(self, task: PipelineTask) -> Any:
        """Run the specified agent function."""
        agent_name = task.agent_type
        function_name = task.function_name
        parameters = task.parameters
        
        # Get the agent
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not registered")
        
        agent = self.agents[agent_name]
        
        # Get the function
        if not hasattr(agent, function_name):
            raise ValueError(f"Agent {agent_name} does not have function {function_name}")
        
        func = getattr(agent, function_name)
        
        # Execute the function
        if asyncio.iscoroutinefunction(func):
            result = await func(**parameters)
        else:
            result = func(**parameters)
        
        return result
    
    async def _update_agent_status(self, agent_name: str, success: bool, start_time: datetime, end_time: datetime):
        """Update agent performance status."""
        if agent_name not in self.agent_status:
            return
        
        status = self.agent_status[agent_name]
        
        # Update execution count
        status['total_executions'] += 1
        
        # Update success rate
        if success:
            status['success_rate'] = (
                (status['success_rate'] * (status['total_executions'] - 1) + 1.0) / 
                status['total_executions']
            )
        else:
            status['success_rate'] = (
                (status['success_rate'] * (status['total_executions'] - 1)) / 
                status['total_executions']
            )
        
        # Update response time
        execution_time = (end_time - start_time).total_seconds()
        status['average_response_time'] = (
            (status['average_response_time'] * (status['total_executions'] - 1) + execution_time) / 
            status['total_executions']
        )
        
        # Update last execution
        status['last_execution'] = end_time.isoformat()
        status['status'] = 'active' if success else 'error'
        
        # Save to database
        await self._save_agent_status(agent_name, status)
    
    def _start_monitoring_threads(self):
        """Start monitoring and maintenance threads."""
        # Health check thread
        health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        health_thread.start()
        
        # Metrics update thread
        metrics_thread = threading.Thread(target=self._metrics_update_loop, daemon=True)
        metrics_thread.start()
        
        # Optimization thread
        optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        optimization_thread.start()
        
        logger.info("📊 Monitoring threads started")
    
    def _health_check_loop(self):
        """Continuous health checking."""
        interval = self.config.get('health_check_interval', 60)
        
        while self.running:
            try:
                # Check system health
                health_status = self._check_system_health()
                
                if not health_status['healthy']:
                    logger.warning(f"⚠️ System health issues detected: {health_status['issues']}")
                    # Trigger self-healing if needed
                    asyncio.run(self._trigger_self_healing(health_status))
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error in health check: {e}")
                time.sleep(interval)
    
    def _metrics_update_loop(self):
        """Continuous metrics updating."""
        interval = self.config.get('metrics_update_interval', 300)
        
        while self.running:
            try:
                # Update pipeline metrics
                self._update_pipeline_metrics()
                
                # Save metrics to database
                asyncio.run(self._save_metrics())
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error updating metrics: {e}")
                time.sleep(interval)
    
    def _optimization_loop(self):
        """Continuous pipeline optimization."""
        interval = self.config.get('optimization_interval', 3600)
        
        while self.running:
            try:
                # Run optimization cycle
                asyncio.run(self._optimize_pipeline())
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error in optimization: {e}")
                time.sleep(interval)
    
    async def _start_decision_engine(self):
        """Start the autonomous decision engine."""
        if not self.config.get('decision_engine', {}).get('enabled', True):
            return
        
        async def decision_loop():
            interval = self.config.get('decision_engine', {}).get('analysis_interval', 1800)
            
            while self.running:
                try:
                    # Analyze business state
                    business_metrics = await self._collect_business_metrics()
                    business_state = await self.decision_engine.analyze_business_state(business_metrics)
                    
                    # Generate recommendations
                    recommendations = await self.decision_engine.generate_decision_recommendations(business_state)
                    
                    # Execute high-confidence recommendations
                    auto_threshold = self.config.get('decision_engine', {}).get('auto_execute_threshold', 0.9)
                    
                    for rec in recommendations:
                        if rec.opportunity_score.confidence_level >= auto_threshold:
                            await self._execute_decision(rec)
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"❌ Error in decision engine: {e}")
                    await asyncio.sleep(60)
        
        # Start decision engine in background
        asyncio.create_task(decision_loop())
        logger.info("🧠 Decision engine started")
    
    async def _collect_business_metrics(self) -> Dict[str, Any]:
        """Collect current business metrics for decision making."""
        # This would collect real metrics from various sources
        # For now, return simulated metrics
        return {
            'daily_revenue': self.metrics.revenue_generated,
            'conversion_rate': 0.03,  # 3%
            'profit_margin': 0.25,    # 25%
            'operational_costs': 100.0,
            'total_revenue': self.metrics.revenue_generated * 30,  # Monthly estimate
            'active_campaigns': len([t for t in self.active_tasks.values() if 'marketing' in t.agent_type]),
            'growth_rate': 0.1,       # 10%
            'automation_efficiency': self.metrics.automation_efficiency,
            'system_uptime': self.metrics.uptime_percentage
        }
    
    async def _execute_decision(self, recommendation: DecisionRecommendation):
        """Execute a decision recommendation."""
        logger.info(f"🎯 Executing decision: {recommendation.title}")
        
        try:
            # Create tasks for recommended actions
            for action in recommendation.recommended_actions:
                task = PipelineTask(
                    id=f"decision_{recommendation.id}_{uuid.uuid4().hex[:8]}",
                    name=f"Decision Action: {action['description']}",
                    description=f"Executing action from decision: {recommendation.title}",
                    priority=TaskPriority.HIGH,
                    agent_type=self._map_action_to_agent(action['type']),
                    function_name="execute_action",
                    parameters=action,
                    dependencies=[],
                    created_at=datetime.now()
                )
                
                self.add_task(task)
            
            # Save decision execution
            await self.decision_engine.save_recommendation(recommendation)
            
            # Update metrics
            self.metrics.decisions_made += 1
            
            logger.info(f"✅ Decision executed: {recommendation.title}")
            
        except Exception as e:
            logger.error(f"❌ Failed to execute decision: {e}")
    
    def _map_action_to_agent(self, action_type: str) -> str:
        """Map action type to appropriate agent."""
        mapping = {
            'marketing_campaign': 'marketing_agent',
            'email_campaign': 'marketing_agent',
            'content_optimization': 'content_agent',
            'api_optimization': 'stealth_automation_agent',
            'resource_consolidation': 'stealth_automation_agent',
            'automation_enhancement': 'stealth_automation_agent',
            'channel_expansion': 'marketing_agent',
            'audience_research': 'marketing_agent',
            'content_localization': 'content_agent',
            'process_automation': 'stealth_automation_agent',
            'performance_optimization': 'stealth_automation_agent',
            'workflow_enhancement': 'stealth_automation_agent',
            'financial_hedging': 'financial_agent',
            'operational_backup': 'stealth_automation_agent',
            'market_diversification': 'marketing_agent'
        }
        
        return mapping.get(action_type, 'stealth_automation_agent')
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        issues = []
        
        # Check error rate
        if self.metrics.total_tasks_executed > 0:
            error_rate = self.metrics.failed_tasks / self.metrics.total_tasks_executed
            if error_rate > self.config.get('monitoring', {}).get('alert_thresholds', {}).get('error_rate', 0.1):
                issues.append(f"High error rate: {error_rate:.2%}")
        
        # Check agent status
        for agent_name, status in self.agent_status.items():
            if status['success_rate'] < 0.8:
                issues.append(f"Agent {agent_name} has low success rate: {status['success_rate']:.2%}")
        
        # Check queue size
        if self.task_queue.qsize() > 100:
            issues.append(f"Task queue is large: {self.task_queue.qsize()} tasks")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _trigger_self_healing(self, health_status: Dict[str, Any]):
        """Trigger self-healing mechanisms."""
        logger.info("🔧 Triggering self-healing mechanisms...")
        
        for issue in health_status['issues']:
            if "error rate" in issue:
                # Reduce task execution rate
                self.config['max_workers'] = max(1, self.config['max_workers'] - 1)
                logger.info(f"🔧 Reduced max workers to {self.config['max_workers']}")
            
            elif "success rate" in issue:
                # Restart problematic agents
                for agent_name in self.agent_status:
                    if self.agent_status[agent_name]['success_rate'] < 0.8:
                        await self._restart_agent(agent_name)
            
            elif "queue" in issue:
                # Increase workers if possible
                if self.config['max_workers'] < 20:
                    self.config['max_workers'] += 2
                    logger.info(f"🔧 Increased max workers to {self.config['max_workers']}")
    
    async def _restart_agent(self, agent_name: str):
        """Restart a problematic agent."""
        logger.info(f"🔄 Restarting agent: {agent_name}")
        
        try:
            # Re-initialize the agent
            if agent_name in self.agents:
                del self.agents[agent_name]
            
            # Re-register the agent
            await self._register_agents()
            
            logger.info(f"✅ Agent restarted: {agent_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart agent {agent_name}: {e}")
    
    def _update_pipeline_metrics(self):
        """Update pipeline performance metrics."""
        # Calculate automation efficiency
        if self.metrics.total_tasks_executed > 0:
            self.metrics.automation_efficiency = self.metrics.successful_tasks / self.metrics.total_tasks_executed
        
        # Calculate uptime
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
            
            # Update configuration
            self._save_config(self.config)
            
            logger.info(f"✅ Pipeline optimization completed (Cycle {self.optimization_cycles})")
            
        except Exception as e:
            logger.error(f"❌ Pipeline optimization failed: {e}")
    
    async def _analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns for optimization."""
        # Analyze task execution patterns
        agent_performance = {}
        
        for agent_name, status in self.agent_status.items():
            agent_performance[agent_name] = {
                'success_rate': status['success_rate'],
                'average_response_time': status['average_response_time'],
                'total_executions': status['total_executions']
            }
        
        # Analyze time-based patterns
        hourly_performance = {}  # Would analyze by hour of day
        
        return {
            'agent_performance': agent_performance,
            'hourly_performance': hourly_performance,
            'overall_efficiency': self.metrics.automation_efficiency
        }
    
    async def _optimize_task_scheduling(self, performance_data: Dict[str, Any]):
        """Optimize task scheduling based on performance data."""
        # Adjust scheduling for high-performing agents
        for agent_name, perf in performance_data['agent_performance'].items():
            if perf['success_rate'] > 0.9 and perf['average_response_time'] < 30:
                # Increase frequency for high-performing agents
                if agent_name in self.config['agent_configs']:
                    # This is a simplified optimization
                    logger.info(f"📈 Optimizing schedule for high-performing agent: {agent_name}")
    
    async def _optimize_resource_allocation(self, performance_data: Dict[str, Any]):
        """Optimize resource allocation based on performance."""
        # Adjust worker count based on queue size and performance
        queue_size = self.task_queue.qsize()
        
        if queue_size > 50 and self.metrics.automation_efficiency > 0.8:
            # Increase workers
            self.config['max_workers'] = min(20, self.config['max_workers'] + 1)
            logger.info(f"📈 Increased max workers to {self.config['max_workers']}")
        
        elif queue_size < 10 and self.config['max_workers'] > 5:
            # Decrease workers
            self.config['max_workers'] = max(5, self.config['max_workers'] - 1)
            logger.info(f"📉 Decreased max workers to {self.config['max_workers']}")
    
    async def _save_task(self, task: PipelineTask):
        """Save task to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO pipeline_tasks (
                    id, name, description, priority, agent_type, function_name,
                    parameters, dependencies, retry_count, max_retries, timeout,
                    scheduled_time, created_at, started_at, completed_at,
                    status, result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.description, task.priority.value,
                task.agent_type, task.function_name,
                json.dumps(task.parameters), json.dumps(task.dependencies),
                task.retry_count, task.max_retries, task.timeout,
                task.scheduled_time.isoformat() if task.scheduled_time else None,
                task.created_at.isoformat() if task.created_at else None,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.status,
                json.dumps(task.result) if task.result else None,
                task.error
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving task: {e}")
    
    async def _save_metrics(self):
        """Save metrics to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO pipeline_metrics (
                    timestamp, total_tasks_executed, successful_tasks, failed_tasks,
                    average_execution_time, revenue_generated, cost_saved,
                    decisions_made, automation_efficiency, uptime_percentage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.metrics.last_updated.isoformat(),
                self.metrics.total_tasks_executed,
                self.metrics.successful_tasks,
                self.metrics.failed_tasks,
                self.metrics.average_execution_time,
                self.metrics.revenue_generated,
                self.metrics.cost_saved,
                self.metrics.decisions_made,
                self.metrics.automation_efficiency,
                self.metrics.uptime_percentage
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    async def _save_agent_status(self, agent_name: str, status: Dict[str, Any]):
        """Save agent status to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO agent_status (
                    agent_name, status, last_execution, success_rate,
                    average_response_time, total_executions, last_error, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_name,
                status['status'],
                status['last_execution'],
                status['success_rate'],
                status['average_response_time'],
                status['total_executions'],
                status.get('last_error'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving agent status: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop the automation pipeline gracefully."""
        logger.info("🛑 Stopping Full Automation Pipeline...")
        
        self.running = False
        self.status = PipelineStatus.STOPPED
        
        # Wait for active tasks to complete (with timeout)
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
            'status': self.status.value,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'metrics': asdict(self.metrics),
            'active_tasks': len(self.active_tasks),
            'queue_size': self.task_queue.qsize(),
            'agent_status': self.agent_status,
            'optimization_cycles': self.optimization_cycles
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            'pipeline_status': self.get_status(),
            'task_statistics': {
                'total_executed': self.metrics.total_tasks_executed,
                'successful': self.metrics.successful_tasks,
                'failed': self.metrics.failed_tasks,
                'success_rate': self.metrics.successful_tasks / max(self.metrics.total_tasks_executed, 1),
                'average_execution_time': self.metrics.average_execution_time
            },
            'business_impact': {
                'revenue_generated': self.metrics.revenue_generated,
                'cost_saved': self.metrics.cost_saved,
                'decisions_made': self.metrics.decisions_made,
                'automation_efficiency': self.metrics.automation_efficiency
            },
            'agent_performance': self.agent_status,
            'system_health': self._check_system_health()
        }


def main():
    """Main function to run the full automation pipeline."""
    import asyncio
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pipeline.log'),
            logging.StreamHandler()
        ]
    )
    
    async def run_pipeline():
        pipeline = FullAutomationPipeline()
        
        try:
            # Start the pipeline
            await pipeline.start_pipeline()
            
            # Keep running until interrupted
            while pipeline.running:
                await asyncio.sleep(1)
                
                # Print status every 5 minutes
                if int(time.time()) % 300 == 0:
                    status = pipeline.get_status()
                    logger.info(f"📊 Pipeline Status: {status['status']} | Tasks: {status['active_tasks']} active, {status['queue_size']} queued")
        
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