#!/usr/bin/env python3
"""
TRAE.AI Base Agentic Framework

This module defines the foundational base classes for the TRAE.AI agentic system.
These classes provide the core architecture for autonomous agents that can plan,
execute, and audit tasks within the system.

Base Classes:
- PlannerAgent: Responsible for task planning and strategy
- ExecutorAgent: Handles task execution and implementation
- AuditorAgent: Performs quality assurance and compliance checking

Author: TRAE.AI System
Version: 1.0.0
Date: 2024
"""

import abc
import asyncio
import uuid
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json
import logging

# Import utilities
from backend.secret_store import SecretStore
from utils.logger import get_logger, PerformanceTimer
from backend.agents.base44_agent_protocol import Base44AgentProtocol, TaskContext, AgentMode, ConfirmationLevel
from backend.integrations.ollama_integration import OllamaIntegration


class AgentStatus(Enum):
    """Enumeration of possible agent statuses."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AUDITING = "auditing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskPriority(Enum):
    """Enumeration of task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class AgentCapability(Enum):
    """Enumeration of agent capabilities."""
    PLANNING = "planning"
    EXECUTION = "execution"
    AUDITING = "auditing"
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    MARKETING = "marketing"
    QUALITY_ASSURANCE = "quality_assurance"
    SYSTEM_MANAGEMENT = "system_management"
    ANALYSIS = "analysis"


class BaseAgent(Base44AgentProtocol):
    """
    Abstract base class for all TRAE.AI agents.
    
    This class provides the foundational structure and common functionality
    that all agents in the TRAE.AI system must implement.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.task_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_execution_time': 0.0,
            'success_rate': 0.0
        }
        
        # Initialize logger and secret store
        self.logger = get_logger(f"agent.{self.name.lower()}")
        self.secret_store = SecretStore()
        
        # Initialize configuration system
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'state.json')
        self._config_cache = None
        self._config_last_loaded = None
        
        self.logger.info(f"Agent {self.name} ({self.agent_id}) initialized")
    
    @property
    @abc.abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """
        Return the list of capabilities this agent possesses.
        
        Returns:
            List of AgentCapability enums
        """
        pass
    
    @property
    def is_busy(self) -> bool:
        """Check if the agent is currently busy."""
        return self.status not in [AgentStatus.IDLE, AgentStatus.COMPLETED, AgentStatus.FAILED]
    
    @property
    def uptime(self) -> float:
        """Get the agent's uptime in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from state.json with caching."""
        try:
            # Check if we need to reload (cache is empty or file has been modified)
            if self._config_cache is None or self._should_reload_config():
                with open(self.config_path, 'r') as f:
                    self._config_cache = json.load(f)
                self._config_last_loaded = datetime.now()
                self.logger.debug(f"Configuration loaded from {self.config_path}")
            
            return self._config_cache
        except FileNotFoundError:
            self.logger.warning(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _should_reload_config(self) -> bool:
        """Check if configuration should be reloaded based on file modification time."""
        if self._config_last_loaded is None:
            return True
        
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self.config_path))
            return file_mtime > self._config_last_loaded
        except OSError:
            return True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration when config file is unavailable."""
        return {
            "go_live": False,
            "master_automation": False,
            "toggles": {
                "channels": {"enabled": False},
                "monetization": {"enabled": False},
                "syndication": {"enabled": False},
                "autonomous_directives": {"enabled": False}
            }
        }
    
    def is_action_allowed(self, action_type: str, specific_action: str = None) -> bool:
        """Check if a specific action is allowed based on current configuration."""
        config = self._load_configuration()
        
        # Check master automation switch
        if not config.get("master_automation", False):
            self.logger.debug(f"Action {action_type} blocked: master_automation is disabled")
            return False
        
        # Check go_live switch for production actions
        if action_type in ['publish', 'deploy', 'monetize', 'syndicate'] and not config.get("go_live", False):
            self.logger.debug(f"Action {action_type} blocked: go_live is disabled")
            return False
        
        # Check specific toggle switches
        toggles = config.get("toggles", {})
        
        action_toggle_map = {
            'channel': 'channels',
            'monetization': 'monetization', 
            'monetize': 'monetization',
            'syndication': 'syndication',
            'syndicate': 'syndication',
            'autonomous': 'autonomous_directives',
            'content_creation': 'autonomous_directives',
            'marketing': 'autonomous_directives'
        }
        
        toggle_key = action_toggle_map.get(action_type)
        if toggle_key and toggle_key in toggles:
            if not toggles[toggle_key].get("enabled", False):
                self.logger.debug(f"Action {action_type} blocked: {toggle_key} toggle is disabled")
                return False
        
        self.logger.debug(f"Action {action_type} allowed")
        return True
    
    def update_status(self, status: AgentStatus, message: Optional[str] = None):
        """
        Update the agent's status.
        
        Args:
            status: New status for the agent
            message: Optional status message
        """
        old_status = self.status
        self.status = status
        self.last_activity = datetime.now()
        
        log_message = f"Agent {self.name} status changed: {old_status.value} -> {status.value}"
        if message:
            log_message += f" - {message}"
        
        self.logger.info(log_message)
    
    def record_task_completion(self, task_id: str, success: bool, execution_time: float, details: Optional[Dict] = None):
        """
        Record the completion of a task for performance tracking.
        
        Args:
            task_id: Unique identifier of the completed task
            success: Whether the task was completed successfully
            execution_time: Time taken to execute the task in seconds
            details: Optional additional details about the task
        """
        task_record = {
            'task_id': task_id,
            'success': success,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.task_history.append(task_record)
        
        # Update performance metrics
        if success:
            self.performance_metrics['tasks_completed'] += 1
        else:
            self.performance_metrics['tasks_failed'] += 1
        
        total_tasks = self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed']
        self.performance_metrics['success_rate'] = self.performance_metrics['tasks_completed'] / total_tasks if total_tasks > 0 else 0.0
        
        # Update average execution time
        if len(self.task_history) > 0:
            total_time = sum(record['execution_time'] for record in self.task_history)
            self.performance_metrics['average_execution_time'] = total_time / len(self.task_history)
        
        self.logger.info(f"Task {task_id} recorded: success={success}, time={execution_time:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the agent's performance metrics.
        
        Returns:
            Dictionary containing performance statistics
        """
        return {
            'agent_id': self.agent_id,
            'agent_name': self.name,
            'status': self.status.value,
            'uptime_seconds': self.uptime,
            'capabilities': [cap.value for cap in self.capabilities],
            'performance_metrics': self.performance_metrics.copy(),
            'recent_tasks': self.task_history[-10:] if self.task_history else []
        }
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the Base44 Agent Protocol.
        
        Args:
            task: Task dictionary containing task details
            
        Returns:
            Dictionary containing task results
        """
        # Create task context for Base44 protocol
        task_context = TaskContext(
            task_id=task.get('id', str(uuid.uuid4())),
            task_type=task.get('type', 'unknown'),
            priority=task.get('priority', 'medium'),
            requires_confirmation=task.get('requires_confirmation', False),
            confirmation_level=task.get('confirmation_level', ConfirmationLevel.NONE),
            metadata=task.get('metadata', {})
        )
        
        # Use Base44 protocol to process the task
        return await self.process_task_with_protocol(task, task_context)
    
    @abc.abstractmethod
    async def _execute_with_monitoring(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Execute task with monitoring (Base44 protocol requirement).
        
        Args:
            task: Task dictionary
            context: Task context
            
        Returns:
            Task execution result
        """
        pass
    
    @abc.abstractmethod
    async def _rephrase_task(self, task: Dict[str, Any], context: TaskContext) -> str:
        """
        Rephrase task for confirmation (Base44 protocol requirement).
        
        Args:
            task: Task dictionary
            context: Task context
            
        Returns:
            Rephrased task description
        """
        pass
    
    @abc.abstractmethod
    async def _validate_rephrase_accuracy(self, original_task: Dict[str, Any], rephrased: str, context: TaskContext) -> bool:
        """
        Validate rephrase accuracy (Base44 protocol requirement).
        
        Args:
            original_task: Original task dictionary
            rephrased: Rephrased task description
            context: Task context
            
        Returns:
            True if rephrase is accurate
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.status.value})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}', name='{self.name}', status='{self.status.value}')"


class PlannerAgent(BaseAgent):
    """
    PlannerAgent implements the OODA loop (Observe, Orient, Decide, Act) strategic doctrine.
    
    This agent serves as the system's brain, using the OODA loop methodology to:
    - Observe: Gather data from ResearchAgent and system state
    - Orient: Analyze and synthesize information to understand the situation
    - Decide: Formulate strategic plans and tactical decisions
    - Act: Populate task_queue with specific jobs for other agents
    
    The OODA loop enables rapid, adaptive decision-making in dynamic environments.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        super().__init__(agent_id, name or "PlannerAgent")
        self.planning_strategies: Dict[str, Any] = {
            'default': 'sequential',
            'parallel_threshold': 3,
            'priority_weighting': True
        }
        
        # Sovereign Engine Workflow Automation
        self.workflow_automation = {
            'active_workflows': {},
            'behavioral_triggers': {},
            'customer_journeys': {},
            'automation_rules': {
                'new_subscriber_sequence': {
                    'enabled': True,
                    'tasks': [
                        {'type': 'SEND_EMAIL', 'template': 'welcome_email_1', 'delay_hours': 0},
                        {'type': 'SEND_EMAIL', 'template': 'follow_up_1', 'delay_hours': 48},
                        {'type': 'SEND_EMAIL', 'template': 'affiliate_offer', 'delay_hours': 120}
                    ]
                },
                'product_click_followup': {
                    'enabled': True,
                    'trigger': 'affiliate_link_click',
                    'tasks': [
                        {'type': 'SEND_EMAIL', 'template': 'product_guide', 'delay_hours': 2}
                    ]
                }
            }
        }
        
        # RSS Intelligence Integration
        self.rss_intelligence = {
            'trending_topics': [],
            'topic_momentum': {},
            'content_opportunities': [],
            'last_intelligence_update': None,
            'intelligence_refresh_interval': 1800  # 30 minutes
        }
        
        # Dynamic Content Scheduling
        self.content_scheduling = {
            'base_schedule': {},
            'dynamic_adjustments': [],
            'trend_multipliers': {},
            'scheduling_rules': {
                'high_momentum_boost': 2.0,
                'trending_topic_priority': 'high',
                'min_trend_score': 0.7
            }
        }
        
        # OODA Loop state management
        self.ooda_state = {
            'current_phase': 'observe',  # observe, orient, decide, act
            'cycle_count': 0,
            'last_cycle_time': None,
            'cycle_duration': 3600,  # 1 hour default cycle
            'observations': [],
            'orientation_data': {},
            'observation_history': [],
            'decisions': [],
            'actions_taken': []
        }
        
        # Strategic context
        self.strategic_context = {
            'market_conditions': {},
            'competitive_landscape': {},
            'resource_availability': {},
            'performance_metrics': {},
            'risk_assessment': {},
            'opportunity_matrix': {}
        }
        
        # Planning templates and frameworks
        self.planning_frameworks = {
            'content_calendar': self._create_content_calendar_template(),
            'marketing_campaign': self._create_marketing_campaign_template(),
            'research_agenda': self._create_research_agenda_template(),
            'quality_assurance': self._create_qa_template()
        }
        
        # Active plans and history
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self.planning_history: List[Dict[str, Any]] = []
        
        # Initialize database connection for workflow automation
        self.db_path = "data/trae_master.db"
        
        # Initialize Ollama integration for political neutrality vetting
        try:
            ollama_config = {
                'ollama_endpoint': 'http://localhost:11434',
                'default_model': 'llama2:7b',
                'max_concurrent_requests': 3,
                'cache_enabled': True,
                'cache_ttl': 1800
            }
            self.ollama = OllamaIntegration(ollama_config)
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama integration: {e}")
            self.ollama = None
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.PLANNING]
    
    async def _execute_with_monitoring(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Execute planning task with monitoring.
        
        Args:
            task: Task dictionary containing planning requirements
            context: Task context
            
        Returns:
            Dictionary containing the execution plan
        """
        start_time = time.time()
        
        # Check if autonomous planning is allowed
        if not self.is_action_allowed('autonomous_planning'):
            return {
                'success': False,
                'error': 'Autonomous planning is disabled in configuration',
                'planning_time': 0,
                'agent_id': self.agent_id,
                'task_id': context.task_id
            }
        
        try:
            self.update_status(AgentStatus.PLANNING, f"Planning task {context.task_id}")
            
            with PerformanceTimer(f"agent_initialization_{self.name}") as timer:
                # Extract task requirements
                requirements = task.get('requirements', {})
                priority = TaskPriority(task.get('priority', TaskPriority.MEDIUM.value))
                
                # Create execution plan
                plan = await self._create_execution_plan(requirements, priority)
                
                # Validate the plan
                validation_result = await self._validate_plan(plan)
                
                if not validation_result['valid']:
                    raise ValueError(f"Plan validation failed: {validation_result['errors']}")
                
                result = {
                    'success': True,
                    'plan': plan,
                    'validation': validation_result,
                    'planning_time': timer.elapsed_time,
                    'agent_id': self.agent_id
                }
                
                self.update_status(AgentStatus.COMPLETED, f"Planning completed for task {context.task_id}")
                self.record_task_completion(context.task_id, True, time.time() - start_time, result)
                
                return result
                
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'planning_time': time.time() - start_time,
                'agent_id': self.agent_id
            }
            
            self.logger.error(f"Planning failed for task {context.task_id}: {e}")
            self.update_status(AgentStatus.FAILED, f"Planning failed: {e}")
            self.record_task_completion(context.task_id, False, time.time() - start_time, error_result)
            
            return error_result
    
    async def _rephrase_task(self, task: Dict[str, Any], context: TaskContext) -> str:
        """
        Rephrase planning task for confirmation.
        
        Args:
            task: Task dictionary
            context: Task context
            
        Returns:
            Rephrased task description
        """
        requirements = task.get('requirements', {})
        task_type = task.get('type', 'planning')
        
        # Generate human-readable description of the planning task
        description = f"I will create a {task_type} plan with the following requirements:\n"
        
        if 'content_type' in requirements:
            description += f"- Content Type: {requirements['content_type']}\n"
        if 'target_audience' in requirements:
            description += f"- Target Audience: {requirements['target_audience']}\n"
        if 'timeline' in requirements:
            description += f"- Timeline: {requirements['timeline']}\n"
        if 'budget' in requirements:
            description += f"- Budget: {requirements['budget']}\n"
        if 'channel' in requirements:
            description += f"- Channel: {requirements['channel']}\n"
        
        description += f"\nThis plan will include step-by-step execution instructions with priority level: {context.priority}"
        
        return description
    
    async def _validate_rephrase_accuracy(self, original_task: Dict[str, Any], rephrased: str, context: TaskContext) -> bool:
        """
        Validate rephrase accuracy for planning tasks.
        
        Args:
            original_task: Original task dictionary
            rephrased: Rephrased task description
            context: Task context
            
        Returns:
            True if rephrase is accurate
        """
        # Check if key elements from original task are present in rephrased version
        requirements = original_task.get('requirements', {})
        
        # Validate that important requirements are mentioned
        accuracy_checks = [
            # Check if content type is mentioned if present
            requirements.get('content_type', '') == '' or requirements['content_type'].lower() in rephrased.lower(),
            # Check if target audience is mentioned if present
            requirements.get('target_audience', '') == '' or requirements['target_audience'].lower() in rephrased.lower(),
            # Check if task type is mentioned
            original_task.get('type', 'planning').lower() in rephrased.lower(),
            # Check if priority is mentioned
            context.priority.lower() in rephrased.lower(),
            # Check if channel is mentioned if present
            requirements.get('channel', '') == '' or requirements['channel'].lower() in rephrased.lower()
        ]
        
        # Return True if at least 75% of checks pass
        return sum(accuracy_checks) >= len(accuracy_checks) * 0.75
    
    async def _create_execution_plan(self, requirements: Dict[str, Any], priority: TaskPriority) -> Dict[str, Any]:
        """
        Create an execution plan based on requirements.
        
        Args:
            requirements: Task requirements dictionary
            priority: Task priority level
            
        Returns:
            Execution plan dictionary
        """
        # Placeholder implementation - to be expanded based on specific requirements
        plan = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'priority': priority.value,
            'requirements': requirements,
            'steps': [],
            'estimated_duration': 0,
            'required_agents': [],
            'dependencies': [],
            'resources': []
        }
        
        # Analyze requirements and create steps
        task_type = requirements.get('type', 'generic')
        target_channel = requirements.get('channel', '')
        
        # PROTECTED CHANNEL PROTOCOL: The Right Perspective locked workflow
        if target_channel == 'The Right Perspective' or requirements.get('protected_channel') == 'The Right Perspective':
            self.logger.info("PROTECTED CHANNEL: Activating locked workflow for The Right Perspective")
            plan = await self._create_protected_right_perspective_plan(requirements, priority)
            return plan
        
        if task_type == 'content_creation':
            plan['steps'] = [
                {'id': 1, 'action': 'research_topic', 'agent': 'ResearchAgent', 'duration': 300},
                {'id': 2, 'action': 'create_content', 'agent': 'ContentAgent', 'duration': 600},
                {'id': 3, 'action': 'quality_check', 'agent': 'QAAgent', 'duration': 180}
            ]
            plan['required_agents'] = ['ResearchAgent', 'ContentAgent', 'QAAgent']
            plan['estimated_duration'] = 1080
        
        elif task_type == 'digital_product_creation':
            # Day One Monetization workflow - automatically includes marketing
            plan['steps'] = [
                {'id': 1, 'action': 'research_topic', 'agent': 'ResearchAgent', 'duration': 300},
                {'id': 2, 'action': 'create_product', 'agent': 'ContentAgent', 'duration': 1200},
                {'id': 3, 'action': 'quality_check', 'agent': 'QAAgent', 'duration': 180},
                {'id': 4, 'action': 'generate_marketing_package', 'agent': 'MarketingAgent', 'duration': 600, 'marketing_type': 'ecommerce_marketing'}
            ]
            plan['required_agents'] = ['ResearchAgent', 'ContentAgent', 'QAAgent', 'MarketingAgent']
            plan['estimated_duration'] = 2280
            plan['monetization_enabled'] = True
            plan['auto_marketing'] = True
        
        elif task_type == 'system_maintenance':
            plan['steps'] = [
                {'id': 1, 'action': 'system_check', 'agent': 'SystemAgent', 'duration': 120},
                {'id': 2, 'action': 'perform_maintenance', 'agent': 'SystemAgent', 'duration': 300},
                {'id': 3, 'action': 'verify_system', 'agent': 'SystemAgent', 'duration': 60}
            ]
            plan['required_agents'] = ['SystemAgent']
            plan['estimated_duration'] = 480
        
        else:
            # Generic plan
            plan['steps'] = [
                {'id': 1, 'action': 'analyze_task', 'agent': 'SystemAgent', 'duration': 60},
                {'id': 2, 'action': 'execute_task', 'agent': 'ExecutorAgent', 'duration': 300},
                {'id': 3, 'action': 'audit_result', 'agent': 'AuditorAgent', 'duration': 120}
            ]
            plan['required_agents'] = ['SystemAgent', 'ExecutorAgent', 'AuditorAgent']
            plan['estimated_duration'] = 480
        
        self.logger.info(f"Created execution plan with {len(plan['steps'])} steps")
        return plan
    
    async def _create_protected_right_perspective_plan(self, requirements: Dict[str, Any], priority: TaskPriority) -> Dict[str, Any]:
        """
        PROTECTED CHANNEL PROTOCOL: Create locked execution plan for The Right Perspective.
        
        This method enforces the specific workflow sequence:
        1. breaking_news_watcher.py (trigger content based on breaking news)
        2. evidence table in right_perspective.db (require facts/receipts)
        3. humor_style_db.py (inject unique tone and style)
        
        This workflow is LOCKED and cannot be modified by system agents.
        """
        self.logger.warning("PROTECTED CHANNEL: Creating locked workflow for The Right Perspective")
        
        # Validate protected channel status
        if not await self._validate_right_perspective_protection():
            raise RuntimeError("PROTECTED CHANNEL VIOLATION: The Right Perspective protection compromised")
        
        plan = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'priority': priority.value,
            'requirements': requirements,
            'channel': 'The Right Perspective',
            'protected_channel': True,
            'locked_workflow': True,
            'modification_prohibited': True,
            'steps': [
                {
                    'id': 1,
                    'action': 'trigger_breaking_news_analysis',
                    'agent': 'ResearchAgent',
                    'tool': 'breaking_news_watcher.py',
                    'duration': 300,
                    'description': 'Monitor breaking news and identify content opportunities',
                    'protected': True,
                    'required': True
                },
                {
                    'id': 2,
                    'action': 'gather_evidence_receipts',
                    'agent': 'ResearchAgent',
                    'tool': 'right_perspective.db:evidence',
                    'duration': 240,
                    'description': 'Collect factual evidence and receipts from database',
                    'protected': True,
                    'required': True,
                    'validation': 'evidence_required'
                },
                {
                    'id': 3,
                    'action': 'generate_humor_style_content',
                    'agent': 'ContentAgent',
                    'tool': 'humor_style_db.py',
                    'duration': 420,
                    'description': 'Generate witty/sarcastic banter using protected humor styles',
                    'protected': True,
                    'required': True,
                    'persona_lock': 'The Right Perspective Host'
                },
                {
                    'id': 4,
                    'action': 'protected_quality_check',
                    'agent': 'QAAgent',
                    'duration': 180,
                    'description': 'Validate content maintains The Right Perspective formula',
                    'protected': True,
                    'validation_rules': ['tone_consistency', 'evidence_integration', 'humor_style_compliance']
                }
            ],
            'required_agents': ['ResearchAgent', 'ContentAgent', 'QAAgent'],
            'estimated_duration': 1140,
            'dependencies': [
                {'from_step': 1, 'to_step': 2, 'type': 'sequential'},
                {'from_step': 2, 'to_step': 3, 'type': 'sequential'},
                {'from_step': 3, 'to_step': 4, 'type': 'sequential'}
            ],
            'resources': [
                'breaking_news_watcher.py',
                'right_perspective.db',
                'humor_style_db.py'
            ],
            'protection_rules': {
                'workflow_modification': 'PROHIBITED',
                'step_reordering': 'PROHIBITED',
                'agent_substitution': 'PROHIBITED',
                'persona_modification': 'PROHIBITED',
                'cross_promotion': 'PROHIBITED'
            },
            'validation_checkpoints': [
                {'step': 2, 'requirement': 'evidence_data_present'},
                {'step': 3, 'requirement': 'humor_style_applied'},
                {'step': 4, 'requirement': 'tone_consistency_verified'}
            ]
        }
        
        self.logger.info("PROTECTED CHANNEL: Locked workflow created for The Right Perspective")
        return plan
    
    async def _validate_right_perspective_protection(self) -> bool:
        """
        Validate that The Right Perspective channel maintains its protected status.
        
        Returns:
            True if protection is intact, False if compromised
        """
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = Path("./data/right_perspective.db")
            if not db_path.exists():
                self.logger.error("PROTECTION BREACH: right_perspective.db not found")
                return False
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check channel protection
                cursor.execute(
                    "SELECT notes FROM channels WHERE channel_name = 'The Right Perspective'"
                )
                result = cursor.fetchone()
                
                if not result or "PROTECTED CHANNEL" not in result[0]:
                    self.logger.error("PROTECTION BREACH: The Right Perspective channel protection compromised")
                    return False
                
                # Check persona protection
                cursor.execute(
                    "SELECT writing_style_description FROM author_personas WHERE channel_name = 'The Right Perspective'"
                )
                result = cursor.fetchone()
                
                if not result or "PROTECTED READ-ONLY PERSONA" not in result[0]:
                    self.logger.error("PROTECTION BREACH: The Right Perspective persona protection compromised")
                    return False
                
                self.logger.info("PROTECTED CHANNEL: The Right Perspective protection validated")
                return True
                
        except Exception as e:
            self.logger.error(f"PROTECTION ERROR: Failed to validate The Right Perspective protection: {e}")
            return False
    
    def _observe_for_planning(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """OODA Loop - Observe phase: Gather relevant data for planning."""
        observations = {
            'requirements': requirements,
            'system_state': self._get_system_state(),
            'resource_availability': self._assess_resource_availability(),
            'current_workload': len(self.active_plans),
            'timestamp': datetime.now().isoformat()
        }
        return observations
    
    def _orient_planning_context(self, observations: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """OODA Loop - Orient phase: Analyze and synthesize information."""
        orientation = {
            'task_complexity': self._assess_task_complexity(requirements),
            'resource_constraints': self._identify_constraints(observations),
            'strategic_alignment': self._check_strategic_alignment(requirements),
            'risk_factors': self._identify_risks(requirements, observations),
            'opportunities': self._identify_opportunities(requirements, observations)
        }
        return orientation
    
    def _decide_plan_structure(self, orientation: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """OODA Loop - Decide phase: Make strategic decisions about plan structure."""
        task_type = requirements.get('type', 'generic')
        complexity = orientation.get('task_complexity', 'medium')
        
        if task_type == 'content_creation':
            tasks = [
                {'id': 1, 'action': 'research_topic', 'agent': 'ResearchAgent', 'duration': 300},
                {'id': 2, 'action': 'create_content', 'agent': 'ContentAgent', 'duration': 600},
                {'id': 3, 'action': 'quality_check', 'agent': 'QAAgent', 'duration': 180}
            ]
            duration = 1080
        elif task_type == 'system_maintenance':
            tasks = [
                {'id': 1, 'action': 'system_check', 'agent': 'SystemAgent', 'duration': 120},
                {'id': 2, 'action': 'perform_maintenance', 'agent': 'SystemAgent', 'duration': 300},
                {'id': 3, 'action': 'verify_system', 'agent': 'SystemAgent', 'duration': 60}
            ]
            duration = 480
        else:
            tasks = [
                {'id': 1, 'action': 'analyze_task', 'agent': 'SystemAgent', 'duration': 60},
                {'id': 2, 'action': 'execute_task', 'agent': 'ExecutorAgent', 'duration': 300},
                {'id': 3, 'action': 'audit_result', 'agent': 'AuditorAgent', 'duration': 120}
            ]
            duration = 480
        
        decisions = {
            'tasks': tasks,
            'dependencies': self._calculate_dependencies(tasks),
            'duration': duration,
            'execution_strategy': 'sequential' if complexity == 'high' else 'parallel'
        }
        return decisions
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for observation."""
        import psutil
        import os
        
        try:
            # Get actual system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate system load category
            if cpu_percent < 30:
                load_category = 'low'
            elif cpu_percent < 70:
                load_category = 'medium'
            else:
                load_category = 'high'
            
            # Determine resource availability
            memory_available_gb = memory.available / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            
            if memory_available_gb > 4 and disk_free_gb > 10:
                resources = 'high'
            elif memory_available_gb > 2 and disk_free_gb > 5:
                resources = 'medium'
            else:
                resources = 'low'
            
            return {
                'active_agents': len([agent for agent in getattr(self, '_active_agents', [])]),
                'system_load': cpu_percent / 100.0,
                'load_category': load_category,
                'available_resources': resources,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'disk_free_gb': round(disk_free_gb, 2),
                'cpu_count': psutil.cpu_count(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to get system state: {e}")
            # Fallback to basic info
            return {
                'active_agents': 1,
                'system_load': 0.5,
                'load_category': 'medium',
                'available_resources': 'medium',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _assess_resource_availability(self) -> Dict[str, Any]:
        """Assess available resources for planning."""
        import psutil
        
        try:
            # Get system resource information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Assess compute resources
            if cpu_percent < 50:
                compute_status = 'available'
            elif cpu_percent < 80:
                compute_status = 'limited'
            else:
                compute_status = 'constrained'
            
            # Assess memory availability
            memory_available_gb = memory.available / (1024**3)
            if memory_available_gb > 4:
                memory_status = 'abundant'
            elif memory_available_gb > 2:
                memory_status = 'adequate'
            else:
                memory_status = 'limited'
            
            # Assess storage
            disk_free_gb = disk.free / (1024**3)
            if disk_free_gb > 20:
                storage_status = 'abundant'
            elif disk_free_gb > 10:
                storage_status = 'sufficient'
            elif disk_free_gb > 5:
                storage_status = 'limited'
            else:
                storage_status = 'critical'
            
            # Assess agent capacity based on current workload
            active_tasks = len(getattr(self, 'active_tasks', []))
            max_concurrent = getattr(self, 'max_concurrent_tasks', 5)
            
            if active_tasks < max_concurrent * 0.5:
                agent_capacity = 'high'
            elif active_tasks < max_concurrent * 0.8:
                agent_capacity = 'medium'
            else:
                agent_capacity = 'low'
            
            return {
                'compute_resources': compute_status,
                'memory_resources': memory_status,
                'storage': storage_status,
                'agent_capacity': agent_capacity,
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'active_tasks': active_tasks,
                'max_concurrent_tasks': max_concurrent,
                'can_accept_new_tasks': active_tasks < max_concurrent,
                'resource_score': self._calculate_resource_score(cpu_percent, memory.percent, (disk.used / disk.total) * 100),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to assess resource availability: {e}")
            # Fallback assessment
            return {
                'compute_resources': 'available',
                'memory_resources': 'adequate',
                'storage': 'sufficient',
                'agent_capacity': 'medium',
                'can_accept_new_tasks': True,
                'resource_score': 0.7,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_resource_score(self, cpu_percent: float, memory_percent: float, disk_percent: float) -> float:
        """Calculate overall resource availability score (0.0 to 1.0)."""
        # Invert percentages so higher availability = higher score
        cpu_score = max(0, (100 - cpu_percent) / 100)
        memory_score = max(0, (100 - memory_percent) / 100)
        disk_score = max(0, (100 - disk_percent) / 100)
        
        # Weighted average (CPU and memory are more important for agent tasks)
        return (cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2)
    
    def _assess_task_complexity(self, requirements: Dict[str, Any]) -> str:
        """Assess the complexity of the task."""
        task_type = requirements.get('type', 'generic')
        if task_type in ['system_maintenance', 'security_audit']:
            return 'high'
        elif task_type in ['content_creation', 'research']:
            return 'medium'
        else:
            return 'low'
    
    def _identify_constraints(self, observations: Dict[str, Any]) -> List[str]:
        """Identify resource and operational constraints."""
        constraints = []
        if observations.get('current_workload', 0) > 10:
            constraints.append('high_workload')
        return constraints
    
    def _check_strategic_alignment(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check alignment with strategic objectives."""
        return {
            'aligned': True,
            'strategic_value': 'medium',
            'business_impact': 'positive'
        }
    
    def _identify_risks(self, requirements: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential risks in the planning context."""
        risks = []
        if requirements.get('priority') == 'emergency':
            risks.append({
                'type': 'time_pressure',
                'severity': 'high',
                'mitigation': 'allocate_additional_resources'
            })
        return risks
    
    def _identify_opportunities(self, requirements: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify opportunities for optimization or improvement."""
        opportunities = []
        if observations.get('current_workload', 0) < 3:
            opportunities.append({
                'type': 'parallel_execution',
                'benefit': 'faster_completion',
                'feasibility': 'high'
            })
        return opportunities
    
    def _calculate_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate task dependencies."""
        dependencies = []
        for i, task in enumerate(tasks[1:], 1):
            dependencies.append({
                'task_id': task['id'],
                'depends_on': [tasks[i-1]['id']]
            })
        return dependencies
    
    def _create_content_calendar_template(self) -> Dict[str, Any]:
        """Create content calendar planning template."""
        return {
            'type': 'content_calendar',
            'phases': ['research', 'creation', 'review', 'publication'],
            'default_duration': 2400,  # 40 minutes
            'required_agents': ['ResearchAgent', 'ContentAgent', 'QAAgent']
        }
    
    def _create_marketing_campaign_template(self) -> Dict[str, Any]:
        """Create marketing campaign planning template."""
        return {
            'type': 'marketing_campaign',
            'phases': ['strategy', 'content_creation', 'execution', 'analysis'],
            'default_duration': 7200,  # 2 hours
            'required_agents': ['PlannerAgent', 'ContentAgent', 'MarketingAgent', 'AnalyticsAgent']
        }
    
    def _create_research_agenda_template(self) -> Dict[str, Any]:
        """Create research agenda planning template."""
        return {
            'type': 'research_agenda',
            'phases': ['topic_identification', 'data_gathering', 'analysis', 'reporting'],
            'default_duration': 3600,  # 1 hour
            'required_agents': ['ResearchAgent', 'AnalyticsAgent']
        }
    
    def _create_qa_template(self) -> Dict[str, Any]:
        """Create quality assurance planning template."""
        return {
            'type': 'quality_assurance',
            'phases': ['preparation', 'testing', 'validation', 'reporting'],
            'default_duration': 1800,  # 30 minutes
            'required_agents': ['QAAgent', 'AuditorAgent']
        }
    
    def create_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan based on requirements using OODA loop methodology."""
        plan_id = str(uuid.uuid4())
        
        # Apply OODA loop to plan creation
        observations = self._observe_for_planning(requirements)
        orientation = self._orient_planning_context(observations, requirements)
        decisions = self._decide_plan_structure(orientation, requirements)
        
        plan = {
            'id': plan_id,
            'requirements': requirements,
            'created_at': datetime.now().isoformat(),
            'status': 'draft',
            'tasks': decisions.get('tasks', []),
            'dependencies': decisions.get('dependencies', []),
            'estimated_duration': decisions.get('duration', 0),
            'priority': requirements.get('priority', 'medium'),
            'ooda_context': {
                'observations': observations,
                'orientation': orientation,
                'decisions': decisions
            }
        }
        
        # Add to active plans
        self.active_plans[plan_id] = plan
        self.planning_history.append({
            'action': 'plan_created',
            'plan_id': plan_id,
            'timestamp': datetime.now().isoformat(),
            'ooda_cycle': self.ooda_state['cycle_count']
        })
        
        self.logger.info(f"Created OODA-based plan {plan_id} with {len(plan['tasks'])} tasks")
        return plan
    
    def execute_ooda_cycle(self, task_queue_manager) -> Dict[str, Any]:
        """
        Execute a complete OODA loop cycle.
        
        Args:
            task_queue_manager: TaskQueueManager instance for task creation
            
        Returns:
            Dictionary containing cycle results
        """
        cycle_start = datetime.now()
        self.ooda_state['cycle_count'] += 1
        
        try:
            # OBSERVE: Gather data from system and environment
            observations = self._observe_system_state(task_queue_manager)
            self.ooda_state['observations'] = observations
            
            # ORIENT: Analyze and synthesize information
            orientation = self._orient_strategic_context(observations)
            self.ooda_state['orientation_data'] = orientation
            
            # DECIDE: Make strategic decisions
            decisions = self._decide_actions(orientation, observations)
            self.ooda_state['decisions'] = decisions
            
            # ACT: Execute decisions by populating task queue
            actions = self._act_on_decisions(decisions, task_queue_manager)
            self.ooda_state['actions_taken'] = actions
            
            # Update cycle state
            self.ooda_state['current_phase'] = 'observe'  # Reset for next cycle
            self.ooda_state['last_cycle_time'] = cycle_start.isoformat()
            
            cycle_result = {
                'cycle_id': self.ooda_state['cycle_count'],
                'duration': (datetime.now() - cycle_start).total_seconds(),
                'observations_count': len(observations),
                'decisions_made': len(decisions),
                'actions_taken': len(actions),
                'status': 'completed'
            }
            
            self.logger.info(f"OODA cycle {self.ooda_state['cycle_count']} completed in {cycle_result['duration']:.2f}s")
            return cycle_result
            
        except Exception as e:
            self.logger.error(f"OODA cycle failed: {str(e)}")
            return {
                'cycle_id': self.ooda_state['cycle_count'],
                'status': 'failed',
                'error': str(e)
            }
    
    def _observe_system_state(self, task_queue_manager) -> Dict[str, Any]:
        """
        OODA Loop - Observe: Gather comprehensive system data.
        """
        observations = {
            'timestamp': datetime.now().isoformat(),
            'observation_id': str(uuid.uuid4()),
            'task_queue_status': self._observe_task_queue(task_queue_manager),
            'agent_performance': self._observe_agent_performance(),
            'system_metrics': self._observe_system_metrics(),
            'market_conditions': self._observe_market_conditions(),
            'content_performance': self._observe_content_performance(),
            'resource_utilization': self._observe_resource_utilization()
        }
        
        # Update OODA state with observations
        self.ooda_state['last_observation'] = observations
        self.ooda_state['observation_history'].append(observations)
        
        # Keep only last 10 observations for memory efficiency
        if len(self.ooda_state['observation_history']) > 10:
            self.ooda_state['observation_history'] = self.ooda_state['observation_history'][-10:]
        
        return observations
    
    def _orient_strategic_context(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """
        OODA Loop - Orient: Analyze observations and update strategic context.
        """
        orientation = {
            'situation_assessment': self._assess_current_situation(observations),
            'trend_analysis': self._analyze_trends(observations),
            'opportunity_identification': self._identify_strategic_opportunities(observations),
            'threat_assessment': self._assess_threats(observations),
            'resource_optimization': self._optimize_resource_allocation(observations),
            'performance_gaps': self._identify_performance_gaps(observations)
        }
        
        # Update strategic context
        self.strategic_context.update({
            'last_updated': datetime.now().isoformat(),
            'orientation_data': orientation
        })
        
        return orientation
    
    def _decide_actions(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        OODA Loop - Decide: Make strategic decisions based on orientation.
        """
        decision_id = str(uuid.uuid4())
        decisions = []
        
        # Research-driven decisions
        research_decisions = self._decide_research_actions(orientation, observations)
        decisions.extend(research_decisions)
        
        # Content strategy decisions
        content_decisions = self._decide_content_strategy(orientation, observations)
        decisions.extend(content_decisions)
        
        # Marketing decisions
        marketing_decisions = self._decide_marketing_actions(orientation, observations)
        decisions.extend(marketing_decisions)
        
        # Web automation decisions
        automation_decisions = self._decide_automation_actions(orientation, observations)
        decisions.extend(automation_decisions)
        
        # System optimization decisions
        system_decisions = self._decide_system_optimizations(orientation, observations)
        decisions.extend(system_decisions)
        
        # Quality assurance decisions
        qa_decisions = self._decide_qa_actions(orientation, observations)
        decisions.extend(qa_decisions)
        
        # Store decision in OODA state
        self.ooda_state['last_decision'] = {
            'id': decision_id,
            'timestamp': datetime.now().isoformat(),
            'decisions_count': len(decisions),
            'decision_types': list(set([d.get('type', 'unknown') for d in decisions]))
        }
        
        # Maintain decision history (last 5 decisions)
        if 'decision_history' not in self.ooda_state:
            self.ooda_state['decision_history'] = []
        self.ooda_state['decision_history'].append(self.ooda_state['last_decision'])
        if len(self.ooda_state['decision_history']) > 5:
            self.ooda_state['decision_history'].pop(0)
        
        return decisions
    
    def _act_on_decisions(self, decisions: List[Dict[str, Any]], task_queue_manager) -> List[Dict[str, Any]]:
        """
        OODA Loop - Act: Execute decisions by creating tasks in the queue.
        """
        actions_taken = []
        
        for decision in decisions:
            try:
                task_id = task_queue_manager.create_task(
                    task_type=decision['task_type'],
                    priority=decision.get('priority', 'medium'),
                    payload=decision['payload'],
                    assigned_agent=decision.get('assigned_agent'),
                    scheduled_at=decision.get('scheduled_at')
                )
                
                actions_taken.append({
                    'decision_id': decision.get('id'),
                    'task_id': task_id,
                    'action_type': decision['task_type'],
                    'status': 'created',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Failed to create task for decision {decision.get('id')}: {str(e)}")
                actions_taken.append({
                    'decision_id': decision.get('id'),
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return actions_taken
    
    # OODA Loop Supporting Methods
    def _observe_task_queue(self, task_queue_manager) -> Dict[str, Any]:
        """Observe current task queue status."""
        try:
            pending_tasks = task_queue_manager.get_tasks(status='pending')
            in_progress_tasks = task_queue_manager.get_tasks(status='in_progress')
            completed_tasks = task_queue_manager.get_tasks(status='completed', limit=50)
            
            return {
                'pending_count': len(pending_tasks),
                'in_progress_count': len(in_progress_tasks),
                'completed_today': len([t for t in completed_tasks if self._is_today(t.get('completed_at'))]),
                'queue_health': 'healthy' if len(pending_tasks) < 20 else 'congested'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'unavailable'}
    
    def _observe_agent_performance(self) -> Dict[str, Any]:
        """Observe agent performance metrics."""
        return {
            'active_agents': 5,  # Placeholder
            'average_task_completion_time': 300,  # 5 minutes
            'success_rate': 0.95,
            'bottlenecks': []
        }
    
    def _observe_system_metrics(self) -> Dict[str, Any]:
        """Observe system performance metrics."""
        return {
            'cpu_usage': 0.6,
            'memory_usage': 0.4,
            'disk_usage': 0.3,
            'network_latency': 50  # ms
        }
    
    def _observe_market_conditions(self) -> Dict[str, Any]:
        """Observe market and competitive conditions including RSS intelligence."""
        # Get RSS intelligence from Research Agent
        rss_intelligence = self._get_rss_intelligence()
        
        return {
            'trending_topics': rss_intelligence.get('trending_topics', ['AI', 'automation', 'productivity']),
            'topic_momentum': rss_intelligence.get('topic_momentum', {}),
            'content_opportunities': rss_intelligence.get('content_opportunities', []),
            'competitor_activity': 'moderate',
            'market_sentiment': 'positive'
        }
    
    def _observe_content_performance(self) -> Dict[str, Any]:
        """Observe content performance metrics."""
        return {
            'recent_engagement': 0.8,
            'content_quality_score': 0.9,
            'publication_frequency': 'optimal'
        }
    
    def _observe_resource_utilization(self) -> Dict[str, Any]:
        """Observe resource utilization."""
        return {
            'compute_resources': 'available',
            'storage_capacity': 'sufficient',
            'api_quotas': 'within_limits'
        }
    
    def _assess_current_situation(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the current operational situation."""
        task_queue = observations.get('task_queue_status', {})
        system_metrics = observations.get('system_metrics', {})
        
        situation = 'normal'
        if task_queue.get('queue_health') == 'congested':
            situation = 'overloaded'
        elif system_metrics.get('cpu_usage', 0) > 0.8:
            situation = 'resource_constrained'
        
        return {
            'overall_status': situation,
            'priority_areas': ['task_queue_management', 'resource_optimization'],
            'immediate_actions_needed': situation != 'normal'
        }
    
    def _analyze_trends(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends from observations."""
        return {
            'task_completion_trend': 'stable',
            'resource_usage_trend': 'increasing',
            'content_performance_trend': 'improving'
        }
    
    def _identify_strategic_opportunities(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify strategic opportunities."""
        opportunities = []
        
        market_conditions = observations.get('market_conditions', {})
        if 'AI' in market_conditions.get('trending_topics', []):
            opportunities.append({
                'type': 'content_opportunity',
                'description': 'Create AI-focused content',
                'priority': 'high',
                'estimated_impact': 'high'
            })
        
        return opportunities
    
    def _assess_threats(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess potential threats."""
        threats = []
        
        task_queue = observations.get('task_queue_status', {})
        if task_queue.get('queue_health') == 'congested':
            threats.append({
                'type': 'operational_threat',
                'description': 'Task queue congestion',
                'severity': 'medium',
                'mitigation': 'increase_processing_capacity'
            })
        
        return threats
    
    def _optimize_resource_allocation(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resource allocation based on observations."""
        return {
            'recommended_adjustments': [],
            'priority_reallocation': 'content_creation',
            'efficiency_improvements': ['parallel_processing']
        }
    
    def _identify_performance_gaps(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance gaps."""
        gaps = []
        
        agent_performance = observations.get('agent_performance', {})
        if agent_performance.get('success_rate', 1.0) < 0.9:
            gaps.append({
                'area': 'agent_reliability',
                'current_performance': agent_performance.get('success_rate'),
                'target_performance': 0.95,
                'improvement_actions': ['error_handling_enhancement']
            })
        
        return gaps
    
    def _decide_research_actions(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make research and market intelligence decisions."""
        decisions = []
        
        # Breaking news monitoring
        if observations.get('market_volatility', 0) > 0.7:
            decisions.append({
                'id': f"research_{len(decisions) + 1}",
                'task_type': 'research',
                'priority': 'high',
                'payload': {
                    'action': 'monitor_breaking_news',
                    'focus_sectors': orientation.get('target_markets', []),
                    'alert_threshold': 0.8
                },
                'assigned_agent': 'ResearchAgent'
            })
        
        # Competitor analysis
        last_competitor_scan = observations.get('last_competitor_analysis')
        if not self._is_today(last_competitor_scan):
            decisions.append({
                'id': f"research_{len(decisions) + 1}",
                'task_type': 'research',
                'priority': 'medium',
                'payload': {
                    'action': 'analyze_competitors',
                    'competitors': orientation.get('key_competitors', []),
                    'analysis_depth': 'comprehensive'
                },
                'assigned_agent': 'ResearchAgent'
            })
        
        return decisions
    
    def _decide_automation_actions(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make web automation decisions."""
        decisions = []
        
        # Affiliate signup automation
        pending_signups = observations.get('pending_affiliate_signups', [])
        if pending_signups:
            decisions.append({
                'id': f"automation_{len(decisions) + 1}",
                'task_type': 'automation',
                'priority': 'medium',
                'payload': {
                    'action': 'automate_affiliate_signups',
                    'platforms': pending_signups,
                    'stealth_level': 'high'
                },
                'assigned_agent': 'WebAutomationAgent'
            })
        
        # Content tool automation
        if observations.get('content_backlog', 0) > 10:
            decisions.append({
                'id': f"automation_{len(decisions) + 1}",
                'task_type': 'automation',
                'priority': 'low',
                'payload': {
                    'action': 'automate_content_tools',
                    'tools': ['spechelo_pro', 'thumbnail_blaster'],
                    'batch_size': 5
                },
                'assigned_agent': 'WebAutomationAgent'
            })
        
        return decisions
    
    def _decide_content_strategy(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make content strategy decisions with political neutrality vetting."""
        decisions = []
        
        opportunities = orientation.get('opportunity_identification', [])
        for opportunity in opportunities:
            if opportunity.get('type') == 'content_opportunity':
                topic = opportunity.get('description')
                target_channel = opportunity.get('channel', 'general')
                
                # Apply political neutrality vetting for non-Right Perspective channels
                if target_channel != 'The Right Perspective':
                    is_political = self._vet_topic_for_political_content(topic)
                    if is_political:
                        # Reject political topics for neutral channels
                        logger.info(f"Political topic '{topic}' rejected for neutral channel '{target_channel}'")
                        continue
                
                decisions.append({
                    'id': f"content_{len(decisions) + 1}",
                    'task_type': 'content',
                    'priority': opportunity.get('priority', 'medium'),
                    'payload': {
                        'action': 'create_content',
                        'topic': topic,
                        'target_audience': 'general',
                        'content_type': 'article',
                        'channel': target_channel
                    },
                    'assigned_agent': 'ContentAgent'
                })
        
        return decisions
    
    def _vet_topic_for_political_content(self, topic: str) -> bool:
        """Vet a topic for political content using Ollama LLM.
        
        Args:
            topic: The topic to analyze
            
        Returns:
            bool: True if topic contains political content, False otherwise
        """
        if not self.ollama or not topic:
            return False
            
        try:
            # Political neutrality vetting prompt
            vetting_prompt = f"""
Analyze the following topic for political content. A topic is considered political if it:
- Discusses political parties, candidates, or elections
- Takes partisan stances on policy issues
- Involves electoral politics or political ideologies
- Contains political commentary or opinion

Topic: "{topic}"

Respond with only "POLITICAL" if the topic contains political content, or "NEUTRAL" if it does not.
"""
            
            response = self.ollama.query(
                prompt=vetting_prompt,
                model='llama2:7b',
                max_tokens=10,
                temperature=0.1
            )
            
            if response and response.content:
                result = response.content.strip().upper()
                return result == 'POLITICAL'
                
        except Exception as e:
            logger.warning(f"Political vetting failed for topic '{topic}': {e}")
            # Fallback: check for obvious political keywords
            political_keywords = [
                'election', 'vote', 'democrat', 'republican', 'biden', 'trump',
                'congress', 'senate', 'political', 'politics', 'campaign',
                'conservative', 'liberal', 'partisan', 'policy debate'
            ]
            topic_lower = topic.lower()
            return any(keyword in topic_lower for keyword in political_keywords)
            
        return False
    
    def _decide_marketing_actions(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make marketing strategy decisions including Twitter engagement."""
        decisions = []
        
        market_conditions = observations.get('market_conditions', {})
        content_performance = observations.get('content_performance', {})
        
        # Traditional marketing optimization
        if market_conditions.get('market_sentiment') == 'positive':
            decisions.append({
                'id': f"marketing_{len(decisions) + 1}",
                'task_type': 'marketing',
                'priority': 'medium',
                'payload': {
                    'action': 'optimize_campaigns',
                    'focus_areas': market_conditions.get('trending_topics', []),
                    'budget_allocation': 'increase'
                },
                'assigned_agent': 'MarketingAgent'
            })
        
        # Twitter promotion for new content
        if content_performance.get('new_videos_count', 0) > 0:
            decisions.append({
                'id': f"twitter_promotion_{len(decisions) + 1}",
                'task_type': 'marketing',
                'priority': 'high',
                'payload': {
                    'action': 'twitter_promotion',
                    'promotion_type': 'youtube_upload',
                    'content_count': content_performance.get('new_videos_count', 0)
                },
                'assigned_agent': 'MarketingAgent'
            })
        
        # Twitter engagement for community building
        trending_topics = market_conditions.get('trending_topics', [])
        if trending_topics:
            decisions.append({
                'id': f"twitter_engagement_{len(decisions) + 1}",
                'task_type': 'marketing',
                'priority': 'medium',
                'payload': {
                    'action': 'twitter_engagement',
                    'engagement_type': 'topic_monitoring',
                    'topics': trending_topics[:3],  # Focus on top 3 trending topics
                    'engagement_goal': 'community_building'
                },
                'assigned_agent': 'MarketingAgent'
            })
        
        # Daily Twitter engagement cycle
        current_hour = datetime.now().hour
        if current_hour in [9, 13, 17]:  # Peak engagement hours
            decisions.append({
                'id': f"twitter_daily_{len(decisions) + 1}",
                'task_type': 'marketing',
                'priority': 'medium',
                'payload': {
                    'action': 'twitter_engagement',
                    'engagement_type': 'conversation_search',
                    'search_keywords': market_conditions.get('trending_topics', ['AI', 'automation', 'productivity']),
                    'engagement_goal': 'thought_leadership'
                },
                'assigned_agent': 'MarketingAgent'
            })
        
        return decisions
    
    def _decide_system_optimizations(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make system optimization decisions."""
        decisions = []
        
        threats = orientation.get('threat_assessment', [])
        for threat in threats:
            if threat.get('type') == 'operational_threat':
                decisions.append({
                    'id': f"system_{len(decisions) + 1}",
                    'task_type': 'system',
                    'priority': 'high',
                    'payload': {
                        'action': 'optimize_performance',
                        'target_area': 'task_queue',
                        'optimization_type': threat.get('mitigation')
                    },
                    'assigned_agent': 'SystemAgent'
                })
        
        return decisions
    
    def _decide_qa_actions(self, orientation: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make quality assurance decisions."""
        decisions = []
        
        performance_gaps = orientation.get('performance_gaps', [])
        for gap in performance_gaps:
            if gap.get('area') == 'agent_reliability':
                decisions.append({
                    'id': f"qa_{len(decisions) + 1}",
                    'task_type': 'qa',
                    'priority': 'high',
                    'payload': {
                        'action': 'quality_audit',
                        'focus_area': gap.get('area'),
                        'target_improvement': gap.get('target_performance')
                    },
                    'assigned_agent': 'QAAgent'
                })
        
        return decisions
    
    def _is_today(self, timestamp_str: Optional[str]) -> bool:
        """Check if timestamp is from today."""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp.date() == datetime.now().date()
        except:
            return False
    
    def _get_rss_intelligence(self) -> Dict[str, Any]:
        """Get RSS intelligence from Research Agent for dynamic content scheduling."""
        try:
            # Import here to avoid circular imports
            from backend.agents.research_tools import BreakingNewsWatcher
            
            # Check if we need to refresh intelligence
            current_time = time.time()
            if (self.rss_intelligence['last_intelligence_update'] is None or 
                current_time - self.rss_intelligence['last_intelligence_update'] > self.rss_intelligence['intelligence_refresh_interval']):
                
                # Use singleton RSS intelligence engine to prevent redundant loading
                if not hasattr(self, '_rss_engine_singleton'):
                    self._rss_engine_singleton = BreakingNewsWatcher()
                rss_engine = self._rss_engine_singleton
                
                # Get trending topics
                trending_topics = rss_engine.get_trending_topics(limit=10)
                
                # Get latest intelligence briefing
                intelligence_briefing = rss_engine.get_intelligence_briefing("general", max_articles=5)
                
                # Calculate topic momentum
                topic_momentum = self._calculate_topic_momentum(trending_topics)
                
                # Identify content opportunities
                content_opportunities = self._identify_content_opportunities(trending_topics, topic_momentum)
                
                # Update cached intelligence
                self.rss_intelligence.update({
                    'trending_topics': [topic['keyword'] for topic in trending_topics],
                    'topic_momentum': topic_momentum,
                    'content_opportunities': content_opportunities,
                    'intelligence_briefing': intelligence_briefing,
                    'last_intelligence_update': current_time
                })
            
            return self.rss_intelligence
            
        except Exception as e:
            # Fallback to default values if RSS intelligence fails
            return {
                'trending_topics': ['AI', 'automation', 'productivity'],
                'topic_momentum': {},
                'content_opportunities': [],
                'intelligence_briefing': None
            }
    
    def _calculate_topic_momentum(self, trending_topics: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate momentum scores for trending topics."""
        momentum = {}
        
        for topic in trending_topics:
            keyword = topic.get('keyword', '')
            frequency = topic.get('frequency', 0)
            trend_score = topic.get('trend_score', 0.0)
            
            # Calculate momentum based on frequency and trend score
            momentum_score = (frequency * 0.6) + (trend_score * 0.4)
            momentum[keyword] = momentum_score
        
        return momentum
    
    def _identify_content_opportunities(self, trending_topics: List[Dict[str, Any]], topic_momentum: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify content opportunities based on RSS intelligence."""
        opportunities = []
        min_trend_score = self.content_scheduling['scheduling_rules']['min_trend_score']
        
        for topic in trending_topics:
            keyword = topic.get('keyword', '')
            momentum_score = topic_momentum.get(keyword, 0.0)
            
            if momentum_score >= min_trend_score:
                opportunity = {
                    'topic': keyword,
                    'momentum_score': momentum_score,
                    'priority': 'high' if momentum_score > 0.8 else 'medium',
                    'content_type': 'video',
                    'suggested_angle': self._suggest_content_angle(keyword),
                    'urgency': 'immediate' if momentum_score > 0.9 else 'scheduled'
                }
                opportunities.append(opportunity)
        
        # Sort by momentum score (highest first)
        opportunities.sort(key=lambda x: x['momentum_score'], reverse=True)
        
        return opportunities[:5]  # Return top 5 opportunities
    
    def _suggest_content_angle(self, topic: str) -> str:
        """Suggest content angle based on topic."""
        # Simple content angle suggestions based on topic keywords
        angle_map = {
            'AI': 'How AI is transforming industries',
            'automation': 'The future of work and automation',
            'productivity': 'Productivity hacks that actually work',
            'technology': 'Latest tech trends you need to know',
            'business': 'Business strategies for modern entrepreneurs'
        }
        
        for keyword, angle in angle_map.items():
            if keyword.lower() in topic.lower():
                return angle
        
        return f"Deep dive into {topic} trends"
    
    def create_dynamic_content_schedule(self, base_schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Create dynamic content schedule based on RSS intelligence."""
        # Get current RSS intelligence
        rss_intelligence = self._get_rss_intelligence()
        content_opportunities = rss_intelligence.get('content_opportunities', [])
        
        # Start with base schedule
        dynamic_schedule = base_schedule.copy()
        adjustments = []
        
        # Process high-priority content opportunities
        for opportunity in content_opportunities:
            if opportunity.get('priority') == 'high' and opportunity.get('urgency') == 'immediate':
                # Create immediate content task
                content_task = {
                    'id': f"rss_content_{int(time.time())}",
                    'type': 'content_creation',
                    'topic': opportunity['topic'],
                    'angle': opportunity['suggested_angle'],
                    'priority': 'high',
                    'source': 'rss_intelligence',
                    'momentum_score': opportunity['momentum_score'],
                    'deadline': 'within_24_hours'
                }
                
                # Add to schedule
                if 'urgent_content' not in dynamic_schedule:
                    dynamic_schedule['urgent_content'] = []
                dynamic_schedule['urgent_content'].append(content_task)
                
                adjustments.append({
                    'type': 'urgent_content_added',
                    'topic': opportunity['topic'],
                    'reason': f"High momentum detected (score: {opportunity['momentum_score']:.2f})"
                })
        
        # Store adjustments for tracking
        self.content_scheduling['dynamic_adjustments'] = adjustments
        
        return {
            'schedule': dynamic_schedule,
            'adjustments': adjustments,
            'intelligence_source': 'rss_feeds',
            'last_updated': time.time()
        }
    
    async def _validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an execution plan.
        
        Args:
            plan: Execution plan to validate
            
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['id', 'steps', 'required_agents', 'estimated_duration']
        for field in required_fields:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        if 'steps' in plan:
            if not plan['steps']:
                errors.append("Plan must contain at least one step")
            
            for i, step in enumerate(plan['steps']):
                if 'action' not in step:
                    errors.append(f"Step {i+1} missing 'action' field")
                if 'agent' not in step:
                    errors.append(f"Step {i+1} missing 'agent' field")
        
        # Check estimated duration
        if plan.get('estimated_duration', 0) <= 0:
            warnings.append("Estimated duration should be greater than 0")
        
        # Check for very long execution times
        if plan.get('estimated_duration', 0) > 3600:  # 1 hour
            warnings.append("Plan has very long estimated duration (>1 hour)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validated_at': datetime.now().isoformat()
        }
    
    # Sovereign Engine Workflow Automation Methods
    
    async def handle_contact_event(self, event_type: str, contact_id: str, event_data: Dict[str, Any], task_queue_manager) -> Dict[str, Any]:
        """
        Handle contact events and trigger appropriate workflow automation.
        
        Args:
            event_type: Type of event (NEW_SUBSCRIBER, LINK_CLICK, EMAIL_OPEN, etc.)
            contact_id: ID of the contact
            event_data: Additional event data
            task_queue_manager: TaskQueueManager instance
            
        Returns:
            Dictionary containing automation results
        """
        try:
            automation_results = []
            
            # Handle new subscriber workflow
            if event_type == 'NEW_SUBSCRIBER':
                result = await self._trigger_new_subscriber_workflow(contact_id, event_data, task_queue_manager)
                automation_results.append(result)
            
            # Handle behavioral triggers
            elif event_type in ['LINK_CLICK', 'EMAIL_OPEN', 'WEBSITE_VISIT']:
                result = await self._process_behavioral_trigger(event_type, contact_id, event_data, task_queue_manager)
                automation_results.append(result)
            
            # Handle affiliate link clicks
            elif event_type == 'AFFILIATE_LINK_CLICK':
                result = await self._trigger_product_followup_workflow(contact_id, event_data, task_queue_manager)
                automation_results.append(result)
            
            return {
                'success': True,
                'event_processed': event_type,
                'contact_id': contact_id,
                'automations_triggered': len(automation_results),
                'results': automation_results
            }
            
        except Exception as e:
            self.logger.error(f"Error handling contact event {event_type} for contact {contact_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'event_type': event_type,
                'contact_id': contact_id
            }
    
    async def _trigger_new_subscriber_workflow(self, contact_id: str, event_data: Dict[str, Any], task_queue_manager) -> Dict[str, Any]:
        """
        Trigger the new subscriber welcome sequence.
        """
        try:
            workflow_config = self.workflow_automation['automation_rules']['new_subscriber_sequence']
            
            if not workflow_config.get('enabled', False):
                return {'success': False, 'reason': 'New subscriber workflow disabled'}
            
            tasks_created = []
            current_time = datetime.now()
            
            for task_config in workflow_config['tasks']:
                # Calculate scheduled time
                delay_hours = task_config.get('delay_hours', 0)
                scheduled_time = current_time + timedelta(hours=delay_hours)
                
                # Create task in queue
                task_data = {
                    'type': 'MARKETING',
                    'subtype': task_config['type'],
                    'contact_id': contact_id,
                    'template': task_config['template'],
                    'workflow': 'new_subscriber_sequence',
                    'scheduled_time': scheduled_time.isoformat(),
                    'priority': 'MEDIUM',
                    'agent_type': 'MarketingAgent'
                }
                
                task_id = task_queue_manager.add_task(
                    task_type='MARKETING',
                    task_data=task_data,
                    priority='MEDIUM',
                    agent_id=None,
                    agent_type='MarketingAgent'
                )
                
                tasks_created.append({
                    'task_id': task_id,
                    'type': task_config['type'],
                    'template': task_config['template'],
                    'scheduled_time': scheduled_time.isoformat()
                })
            
            # Store workflow in active workflows
            workflow_id = str(uuid.uuid4())
            self.workflow_automation['active_workflows'][workflow_id] = {
                'type': 'new_subscriber_sequence',
                'contact_id': contact_id,
                'created_at': current_time.isoformat(),
                'tasks': tasks_created,
                'status': 'active'
            }
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'tasks_created': len(tasks_created),
                'tasks': tasks_created
            }
            
        except Exception as e:
            self.logger.error(f"Error triggering new subscriber workflow: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _trigger_product_followup_workflow(self, contact_id: str, event_data: Dict[str, Any], task_queue_manager) -> Dict[str, Any]:
        """
        Trigger product-specific follow-up workflow based on affiliate link clicks.
        """
        try:
            workflow_config = self.workflow_automation['automation_rules']['product_click_followup']
            
            if not workflow_config.get('enabled', False):
                return {'success': False, 'reason': 'Product followup workflow disabled'}
            
            # Extract product information from event data
            product_info = event_data.get('product_info', {})
            affiliate_link = event_data.get('affiliate_link', '')
            
            tasks_created = []
            current_time = datetime.now()
            
            for task_config in workflow_config['tasks']:
                # Calculate scheduled time
                delay_hours = task_config.get('delay_hours', 0)
                scheduled_time = current_time + timedelta(hours=delay_hours)
                
                # Create personalized task data
                task_data = {
                    'type': 'MARKETING',
                    'subtype': task_config['type'],
                    'contact_id': contact_id,
                    'template': task_config['template'],
                    'workflow': 'product_click_followup',
                    'product_info': product_info,
                    'affiliate_link': affiliate_link,
                    'scheduled_time': scheduled_time.isoformat(),
                    'priority': 'HIGH',
                    'agent_type': 'MarketingAgent'
                }
                
                task_id = task_queue_manager.add_task(
                    task_type='MARKETING',
                    task_data=task_data,
                    priority='HIGH',
                    agent_id=None,
                    agent_type='MarketingAgent'
                )
                
                tasks_created.append({
                    'task_id': task_id,
                    'type': task_config['type'],
                    'template': task_config['template'],
                    'scheduled_time': scheduled_time.isoformat()
                })
            
            # Store workflow in active workflows
            workflow_id = str(uuid.uuid4())
            self.workflow_automation['active_workflows'][workflow_id] = {
                'type': 'product_click_followup',
                'contact_id': contact_id,
                'product_info': product_info,
                'created_at': current_time.isoformat(),
                'tasks': tasks_created,
                'status': 'active'
            }
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'tasks_created': len(tasks_created),
                'tasks': tasks_created
            }
            
        except Exception as e:
            self.logger.error(f"Error triggering product followup workflow: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _process_behavioral_trigger(self, event_type: str, contact_id: str, event_data: Dict[str, Any], task_queue_manager) -> Dict[str, Any]:
        """
        Process behavioral triggers and create dynamic follow-up tasks.
        """
        try:
            # Check for existing behavioral patterns
            contact_behavior = await self._analyze_contact_behavior(contact_id)
            
            # Determine appropriate follow-up actions based on behavior
            follow_up_actions = self._determine_behavioral_followup(event_type, contact_behavior, event_data)
            
            tasks_created = []
            current_time = datetime.now()
            
            for action in follow_up_actions:
                # Calculate scheduled time
                delay_hours = action.get('delay_hours', 1)
                scheduled_time = current_time + timedelta(hours=delay_hours)
                
                # Create behavioral follow-up task
                task_data = {
                    'type': 'MARKETING',
                    'subtype': action['type'],
                    'contact_id': contact_id,
                    'template': action['template'],
                    'workflow': 'behavioral_trigger',
                    'trigger_event': event_type,
                    'behavior_analysis': contact_behavior,
                    'scheduled_time': scheduled_time.isoformat(),
                    'priority': action.get('priority', 'MEDIUM'),
                    'agent_type': 'MarketingAgent'
                }
                
                task_id = task_queue_manager.add_task(
                    task_type='MARKETING',
                    task_data=task_data,
                    priority=action.get('priority', 'MEDIUM'),
                    agent_id=None,
                    agent_type='MarketingAgent'
                )
                
                tasks_created.append({
                    'task_id': task_id,
                    'type': action['type'],
                    'template': action['template'],
                    'scheduled_time': scheduled_time.isoformat()
                })
            
            return {
                'success': True,
                'trigger_event': event_type,
                'tasks_created': len(tasks_created),
                'tasks': tasks_created
            }
            
        except Exception as e:
            self.logger.error(f"Error processing behavioral trigger: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _analyze_contact_behavior(self, contact_id: str) -> Dict[str, Any]:
        """
        Analyze contact behavior patterns from the contact_events table.
        """
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent contact events
                cursor.execute("""
                    SELECT event_type, event_data, created_at
                    FROM contact_events
                    WHERE contact_id = ?
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (contact_id,))
                
                events = cursor.fetchall()
                
                # Analyze behavior patterns
                behavior_analysis = {
                    'total_events': len(events),
                    'email_opens': 0,
                    'link_clicks': 0,
                    'website_visits': 0,
                    'engagement_score': 0,
                    'last_activity': None,
                    'preferred_topics': [],
                    'activity_pattern': 'unknown'
                }
                
                if events:
                    behavior_analysis['last_activity'] = events[0][2]
                    
                    for event in events:
                        event_type = event[0]
                        if event_type == 'EMAIL_OPEN':
                            behavior_analysis['email_opens'] += 1
                        elif event_type == 'LINK_CLICK':
                            behavior_analysis['link_clicks'] += 1
                        elif event_type == 'WEBSITE_VISIT':
                            behavior_analysis['website_visits'] += 1
                    
                    # Calculate engagement score
                    total_interactions = behavior_analysis['email_opens'] + behavior_analysis['link_clicks'] + behavior_analysis['website_visits']
                    behavior_analysis['engagement_score'] = min(total_interactions / 10.0, 1.0)  # Normalize to 0-1
                    
                    # Determine activity pattern
                    if behavior_analysis['engagement_score'] > 0.7:
                        behavior_analysis['activity_pattern'] = 'highly_engaged'
                    elif behavior_analysis['engagement_score'] > 0.3:
                        behavior_analysis['activity_pattern'] = 'moderately_engaged'
                    else:
                        behavior_analysis['activity_pattern'] = 'low_engagement'
                
                return behavior_analysis
                
        except Exception as e:
            self.logger.error(f"Error analyzing contact behavior: {str(e)}")
            return {
                'total_events': 0,
                'engagement_score': 0,
                'activity_pattern': 'unknown',
                'error': str(e)
            }
    
    def _determine_behavioral_followup(self, event_type: str, behavior_analysis: Dict[str, Any], event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Determine appropriate follow-up actions based on behavioral analysis.
        """
        follow_up_actions = []
        engagement_score = behavior_analysis.get('engagement_score', 0)
        activity_pattern = behavior_analysis.get('activity_pattern', 'unknown')
        
        # High engagement users get premium content
        if activity_pattern == 'highly_engaged':
            if event_type == 'EMAIL_OPEN':
                follow_up_actions.append({
                    'type': 'SEND_EMAIL',
                    'template': 'premium_content_offer',
                    'delay_hours': 4,
                    'priority': 'HIGH'
                })
            elif event_type == 'LINK_CLICK':
                follow_up_actions.append({
                    'type': 'SEND_EMAIL',
                    'template': 'exclusive_offer',
                    'delay_hours': 2,
                    'priority': 'HIGH'
                })
        
        # Moderate engagement users get nurturing content
        elif activity_pattern == 'moderately_engaged':
            if event_type == 'EMAIL_OPEN':
                follow_up_actions.append({
                    'type': 'SEND_EMAIL',
                    'template': 'educational_content',
                    'delay_hours': 24,
                    'priority': 'MEDIUM'
                })
        
        # Low engagement users get re-engagement campaigns
        elif activity_pattern == 'low_engagement':
            if event_type == 'EMAIL_OPEN':  # Rare event for low engagement
                follow_up_actions.append({
                    'type': 'SEND_EMAIL',
                    'template': 'reengagement_campaign',
                    'delay_hours': 12,
                    'priority': 'MEDIUM'
                })
        
        return follow_up_actions
    
    async def monitor_workflow_automation(self, task_queue_manager) -> Dict[str, Any]:
        """
        Monitor and manage active workflow automations.
        """
        try:
            # Check for new contact events that need processing
            new_events = await self._check_for_new_contact_events()
            
            automation_results = []
            for event in new_events:
                result = await self.handle_contact_event(
                    event['event_type'],
                    event['contact_id'],
                    event['event_data'],
                    task_queue_manager
                )
                automation_results.append(result)
            
            # Clean up completed workflows
            await self._cleanup_completed_workflows()
            
            return {
                'success': True,
                'events_processed': len(new_events),
                'active_workflows': len(self.workflow_automation['active_workflows']),
                'automation_results': automation_results
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring workflow automation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _check_for_new_contact_events(self) -> List[Dict[str, Any]]:
        """
        Check for new contact events that haven't been processed for automation.
        """
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get unprocessed events (events without automation_processed flag)
                cursor.execute("""
                    SELECT id, contact_id, event_type, event_data, created_at
                    FROM contact_events
                    WHERE automation_processed IS NULL OR automation_processed = 0
                    ORDER BY created_at ASC
                    LIMIT 100
                """)
                
                events = cursor.fetchall()
                
                # Mark events as processed
                event_ids = [str(event[0]) for event in events]
                if event_ids:
                    placeholders = ','.join(['?' for _ in event_ids])
                    cursor.execute(f"""
                        UPDATE contact_events
                        SET automation_processed = 1
                        WHERE id IN ({placeholders})
                    """, event_ids)
                    conn.commit()
                
                # Convert to dictionaries
                processed_events = []
                for event in events:
                    try:
                        event_data = json.loads(event[3]) if event[3] else {}
                    except json.JSONDecodeError:
                        event_data = {}
                    
                    processed_events.append({
                        'id': event[0],
                        'contact_id': event[1],
                        'event_type': event[2],
                        'event_data': event_data,
                        'created_at': event[4]
                    })
                
                return processed_events
                
        except Exception as e:
            self.logger.error(f"Error checking for new contact events: {str(e)}")
            return []
    
    async def _cleanup_completed_workflows(self):
        """
        Clean up completed or expired workflows.
        """
        try:
            current_time = datetime.now()
            workflows_to_remove = []
            
            for workflow_id, workflow in self.workflow_automation['active_workflows'].items():
                # Check if workflow is older than 30 days
                created_at = datetime.fromisoformat(workflow['created_at'])
                if (current_time - created_at).days > 30:
                    workflows_to_remove.append(workflow_id)
                    continue
                
                # Check if all tasks in workflow are completed
                # This would require checking task status in the task queue
                # For now, we'll keep workflows active for monitoring
            
            # Remove expired workflows
            for workflow_id in workflows_to_remove:
                del self.workflow_automation['active_workflows'][workflow_id]
                self.logger.info(f"Cleaned up expired workflow: {workflow_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up workflows: {str(e)}")


class ExecutorAgent(BaseAgent):
    """
    ExecutorAgent handles task execution and implementation.
    
    This agent takes execution plans from PlannerAgent and carries out
    the actual work required to complete tasks using all integrated tools.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        super().__init__(agent_id, name or "ExecutorAgent")
        self.execution_context: Dict[str, Any] = {}
        self.max_concurrent_tasks = 3
        self.current_tasks: List[str] = []
        
        # Initialize all tool integrations
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all integrated tools for task execution."""
        try:
            # Content Creation Tools
            from backend.content.vidscript_pro import VidScriptPro
            from backend.content.automated_author import AutomatedAuthor
            from backend.content.animate_avatar import AnimateAvatar
            from backend.content.ai_inpainting import AIInpainting
            from backend.content.blender_compositor import BlenderCompositor
            from backend.content.audio_postprod import AudioPostProduction
            from backend.content.ai_video_editor import AIVideoEditor
            
            # Research Tools
            from backend.agents.research_tools import CompetitorAnalyzer, MarketValidator, BreakingNewsWatcher
            
            # Marketing Tools
            from backend.agents.marketing_tools import DayOneBlitzStrategy, RelentlessOptimizationLoop, AffiliateManager, CrossPromotionManager
            
            # Web Automation Tools
            from backend.agents.web_automation_tools import StealthOperations, SpecheloPro, ThumbnailBlaster, AffiliateSignupAutomator, WebAutomationAgent
            
            # Initialize tool instances
            self.tools = {
                # Content Creation
                'vidscript_pro': VidScriptPro(),
                'automated_author': AutomatedAuthor(),
                'animate_avatar': AnimateAvatar(),
                'ai_inpainting': AIInpainting(),
                'blender_compositor': BlenderCompositor(),
                'audio_postprod': AudioPostProduction(),
                'ai_video_editor': AIVideoEditor(),
                
                # Research
                'breaking_news_watcher': BreakingNewsWatcher(),
                'competitor_analyzer': CompetitorAnalyzer(),
                'market_validator': MarketValidator(),
                
                # Marketing
                'day_one_blitz': DayOneBlitzStrategy(),
                'optimization_loop': RelentlessOptimizationLoop(),
                'affiliate_manager': AffiliateManager(),
                'cross_promotion': CrossPromotionManager(),
                
                # Web Automation
                'stealth_operations': StealthOperations(),
                'spechelo_pro': SpecheloPro(StealthOperations()),
                'thumbnail_blaster': ThumbnailBlaster(StealthOperations()),
                'affiliate_signup': AffiliateSignupAutomator(StealthOperations()),
                'web_automation': WebAutomationAgent()
            }
            
            self.logger.info(f"Initialized {len(self.tools)} tools for ExecutorAgent")
            
        except ImportError as e:
            self.logger.warning(f"Some tools could not be imported: {e}")
            self.tools = {}
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.EXECUTION,
            AgentCapability.CONTENT_CREATION,
            AgentCapability.RESEARCH,
            AgentCapability.MARKETING
        ]
    
    async def _execute_with_monitoring(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Execute task with comprehensive monitoring and error handling.
        
        Args:
            task: Task dictionary containing execution details
            context: Task execution context
            
        Returns:
            Dictionary containing execution results
        """
        start_time = time.time()
        task_id = task.get('id', str(uuid.uuid4()))
        
        # Check if autonomous execution is allowed
        if not self.is_action_allowed('autonomous_execution'):
            return {
                'success': False,
                'error': 'Autonomous execution is disabled in configuration',
                'execution_time': 0,
                'agent_id': self.agent_id,
                'task_id': task_id
            }
        
        try:
            self.update_status(AgentStatus.EXECUTING, f"Executing task {task_id}")
            
            # Check if we can take on more tasks
            if len(self.current_tasks) >= self.max_concurrent_tasks:
                raise RuntimeError(f"Agent at maximum capacity ({self.max_concurrent_tasks} tasks)")
            
            self.current_tasks.append(task_id)
            
            with PerformanceTimer(f"executor_task_{task.get('type', 'unknown')}") as timer:
                # Extract execution plan
                plan = task.get('plan', {})
                if not plan:
                    raise ValueError("No execution plan provided")
                
                # Execute the plan
                execution_result = await self._execute_plan(plan)
                
                result = {
                    'success': True,
                    'execution_result': execution_result,
                    'execution_time': timer.elapsed_time,
                    'agent_id': self.agent_id
                }
                
                self.update_status(AgentStatus.COMPLETED, f"Execution completed for task {task_id}")
                self.record_task_completion(task_id, True, time.time() - start_time, result)
                
                return result
                
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'agent_id': self.agent_id
            }
            
            self.logger.error(f"Execution failed for task {task_id}: {e}")
            self.update_status(AgentStatus.FAILED, f"Execution failed: {e}")
            self.record_task_completion(task_id, False, time.time() - start_time, error_result)
            
            return error_result
        finally:
            # Clean up task from current tasks list
            if task_id in self.current_tasks:
                self.current_tasks.remove(task_id)
    
    async def _rephrase_task(self, task: Dict[str, Any], context: TaskContext) -> str:
        """
        Rephrase execution task for clarity and confirmation.
        
        Args:
            task: Original task dictionary
            context: Task execution context
            
        Returns:
            Rephrased task description
        """
        task_type = task.get('type', 'unknown')
        plan = task.get('plan', {})
        steps = plan.get('steps', [])
        
        if task_type == 'content_creation':
            return f"I will execute a content creation workflow with {len(steps)} steps, including script generation, video production, and automated publishing."
        elif task_type == 'marketing_campaign':
            return f"I will launch a marketing campaign with {len(steps)} automated steps, including landing page creation, email sequences, and social media promotion."
        elif task_type == 'research_analysis':
            return f"I will conduct research analysis with {len(steps)} steps, including data collection, trend analysis, and report generation."
        else:
            return f"I will execute a {task_type} task with {len(steps)} automated steps as defined in the execution plan."
    
    async def _validate_rephrase_accuracy(self, original_task: Dict[str, Any], rephrased: str, context: TaskContext) -> bool:
        """
        Validate that the rephrased task accurately represents the original.
        
        Args:
            original_task: Original task dictionary
            rephrased: Rephrased task description
            context: Task execution context
            
        Returns:
            True if rephrase is accurate, False otherwise
        """
        task_type = original_task.get('type', 'unknown')
        plan = original_task.get('plan', {})
        steps = plan.get('steps', [])
        
        # Check if key elements are mentioned in rephrase
        accuracy_checks = [
            task_type.lower() in rephrased.lower(),
            str(len(steps)) in rephrased,
            'steps' in rephrased.lower() or 'workflow' in rephrased.lower()
        ]
        
        # Additional specific checks based on task type
        if task_type == 'content_creation':
            accuracy_checks.append(any(keyword in rephrased.lower() for keyword in ['content', 'script', 'video', 'production']))
        elif task_type == 'marketing_campaign':
            accuracy_checks.append(any(keyword in rephrased.lower() for keyword in ['marketing', 'campaign', 'promotion', 'email']))
        elif task_type == 'research_analysis':
            accuracy_checks.append(any(keyword in rephrased.lower() for keyword in ['research', 'analysis', 'data', 'report']))
        
        # Require at least 80% accuracy
        accuracy_score = sum(accuracy_checks) / len(accuracy_checks)
        return accuracy_score >= 0.8
    
    async def _execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plan by running its steps.
        
        Args:
            plan: Execution plan dictionary
            
        Returns:
            Execution result dictionary
        """
        steps = plan.get('steps', [])
        step_results = []
        
        for step in steps:
            step_id = step.get('id')
            action = step.get('action')
            
            self.logger.info(f"Executing step {step_id}: {action}")
            
            # Simulate step execution - to be replaced with actual implementation
            step_start = time.time()
            
            # Placeholder execution logic
            step_result = await self._execute_step(step)
            
            step_duration = time.time() - step_start
            
            step_results.append({
                'step_id': step_id,
                'action': action,
                'success': step_result.get('success', True),
                'duration': step_duration,
                'result': step_result
            })
            
            # Day One Monetization: Auto-trigger marketing after content creation
            if (step_result.get('success', True) and 
                'content' in action.lower() and 
                ('create' in action.lower() or 'generate' in action.lower())):
                await self._trigger_marketing_automation(plan, step, step_result)
            
            # If step failed, stop execution
            if not step_result.get('success', True):
                self.logger.error(f"Step {step_id} failed: {step_result.get('error')}")
                break
        
        return {
            'plan_id': plan.get('id'),
            'steps_executed': len(step_results),
            'total_steps': len(steps),
            'step_results': step_results,
            'overall_success': all(result['success'] for result in step_results)
        }
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step using integrated tools.
        
        Args:
            step: Step dictionary
            
        Returns:
            Step execution result
        """
        action = step.get('action')
        tool_name = step.get('tool')
        parameters = step.get('parameters', {})
        
        try:
            # Route to appropriate tool based on action type
            if tool_name and tool_name in self.tools:
                tool = self.tools[tool_name]
                result = await self._execute_tool_action(tool, action, parameters)
            else:
                # Handle generic actions
                result = await self._execute_generic_action(action, parameters)
            
            return {
                'success': True,
                'action': action,
                'tool': tool_name,
                'message': f"Successfully executed {action}",
                'data': result
            }
            
        except Exception as e:
            self.logger.error(f"Step execution failed for {action}: {str(e)}")
            return {
                'success': False,
                'action': action,
                'tool': tool_name,
                'error': str(e),
                'data': {}
            }
    
    async def _execute_tool_action(self, tool, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action using specific tool."""
        try:
            # Content Creation Tools
            if hasattr(tool, 'create_script_project') and 'script' in action.lower():
                return await tool.create_script_project(parameters)
            elif hasattr(tool, 'create_project') and 'content' in action.lower():
                return await tool.create_project(parameters)
            elif hasattr(tool, 'create_animation_job') and 'animation' in action.lower():
                return await tool.create_animation_job(parameters)
            elif hasattr(tool, 'create_inpainting_job') and 'inpaint' in action.lower():
                return await tool.create_inpainting_job(parameters)
            elif hasattr(tool, 'create_composite_job') and 'composite' in action.lower():
                return await tool.create_composite_job(parameters)
            elif hasattr(tool, 'create_audio_job') and 'audio' in action.lower():
                return await tool.create_audio_job(parameters)
            elif hasattr(tool, 'create_editing_job') and 'edit' in action.lower():
                return await tool.create_editing_job(parameters)
            
            # Research Tools
            elif hasattr(tool, 'monitor_feeds') and 'news' in action.lower():
                return await tool.monitor_feeds(parameters)
            elif hasattr(tool, 'analyze_competitor') and 'competitor' in action.lower():
                return await tool.analyze_competitor(parameters)
            elif hasattr(tool, 'validate_market') and 'market' in action.lower():
                return await tool.validate_market(parameters)
            
            # Marketing Tools
            elif hasattr(tool, 'launch_campaign') and 'campaign' in action.lower():
                return await tool.launch_campaign(parameters)
            elif hasattr(tool, 'optimize_performance') and 'optimize' in action.lower():
                return await tool.optimize_performance(parameters)
            elif hasattr(tool, 'manage_affiliates') and 'affiliate' in action.lower():
                return await tool.manage_affiliates(parameters)
            elif hasattr(tool, 'generate_cross_promotion') and 'promotion' in action.lower():
                return await tool.generate_cross_promotion(parameters)
            
            # Web Automation Tools
            elif hasattr(tool, 'execute_stealth_operation') and 'stealth' in action.lower():
                return await tool.execute_stealth_operation(parameters)
            elif hasattr(tool, 'automate_workflow') and 'automate' in action.lower():
                return await tool.automate_workflow(parameters)
            
            # Generic tool execution
            else:
                # Try to find a method that matches the action
                method_name = action.lower().replace(' ', '_')
                if hasattr(tool, method_name):
                    method = getattr(tool, method_name)
                    if callable(method):
                        return await method(parameters) if asyncio.iscoroutinefunction(method) else method(parameters)
                
                return {'message': f'Action {action} executed on {tool.__class__.__name__}', 'parameters': parameters}
                
        except Exception as e:
            raise Exception(f"Tool execution failed: {str(e)}")
    
    async def _execute_generic_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic actions that don't require specific tools."""
        # Simulate work for generic actions
        await asyncio.sleep(0.1)
        
        return {
            'message': f'Generic action {action} completed',
            'parameters': parameters,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _trigger_marketing_automation(self, plan: Dict[str, Any], completed_step: Dict[str, Any], step_result: Dict[str, Any]):
        """
        Trigger automatic marketing task creation after content creation completion.
        Implements the Day One Monetization workflow.
        
        Args:
            plan: The execution plan containing the completed step
            completed_step: The step that just completed successfully
            step_result: The result of the completed step
        """
        try:
            # Import here to avoid circular imports
            from backend.task_queue_manager import TaskQueueManager, TaskType, TaskPriority
            
            # Extract product information from the completed step
            product_info = {
                'product_name': completed_step.get('parameters', {}).get('title', 'New Digital Product'),
                'product_type': completed_step.get('parameters', {}).get('type', 'digital_product'),
                'content_path': step_result.get('data', {}).get('output_path', ''),
                'plan_id': plan.get('id'),
                'step_id': completed_step.get('id')
            }
            
            # Create marketing task payload
            marketing_payload = {
                'marketing_type': 'ecommerce_marketing',
                'action': 'generate_complete_package',
                'product_info': product_info,
                'automation_trigger': 'day_one_monetization',
                'source_plan': plan.get('id'),
                'source_step': completed_step.get('id')
            }
            
            # Initialize task queue manager
            task_manager = TaskQueueManager()
            
            # Add marketing task to queue
            marketing_task_id = await task_manager.add_task(
                task_type=TaskType.MARKETING,
                payload=marketing_payload,
                priority=TaskPriority.HIGH,
                assigned_agent='MarketingAgent',
                metadata={
                    'automation_type': 'day_one_monetization',
                    'triggered_by': f"content_creation_{completed_step.get('id')}",
                    'product_name': product_info['product_name']
                }
            )
            
            self.logger.info(f"Day One Monetization: Created marketing task {marketing_task_id} for product '{product_info['product_name']}'")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger marketing automation: {str(e)}")
            # Don't fail the main execution if marketing automation fails
    
    async def _simulate_work(self, duration: float):
        """
        Simulate realistic work execution with progress tracking and resource monitoring.
        
        Args:
            duration: Duration to simulate work in seconds
        """
        import asyncio
        import random
        
        start_time = time.time()
        total_steps = max(1, int(duration * 10))  # 10 steps per second
        step_duration = duration / total_steps
        
        try:
            for step in range(total_steps):
                # Simulate variable processing time with realistic fluctuations
                actual_step_time = step_duration * random.uniform(0.8, 1.2)
                
                # Update progress
                progress = (step + 1) / total_steps
                self.metrics['current_progress'] = progress
                
                # Simulate CPU and memory usage during work
                if hasattr(self, 'logger'):
                    if step % 20 == 0:  # Log every 2 seconds
                        self.logger.debug(f"Work simulation progress: {progress:.1%}")
                
                # Realistic work simulation with small delays
                await asyncio.sleep(min(actual_step_time, 0.1))
                
                # Simulate occasional brief pauses (like real work patterns)
                if random.random() < 0.1:  # 10% chance of brief pause
                    await asyncio.sleep(0.05)
            
            # Record completion metrics
            actual_duration = time.time() - start_time
            self.metrics['last_work_duration'] = actual_duration
            self.metrics['work_efficiency'] = duration / actual_duration if actual_duration > 0 else 1.0
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Work simulation interrupted: {e}")
            raise


class AuditorAgent(BaseAgent):
    """
    AuditorAgent performs quality assurance and compliance checking.
    
    This agent reviews completed tasks, ensures they meet quality standards,
    and verifies compliance with system rules and regulations.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        super().__init__(agent_id, name or "AuditorAgent")
        self.audit_criteria: Dict[str, Any] = {
            'quality_threshold': 0.8,
            'compliance_checks': True,
            'performance_validation': True,
            'security_scan': True
        }
        self.audit_history: List[Dict[str, Any]] = []
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.AUDITING, AgentCapability.QUALITY_ASSURANCE]
    
    async def _execute_with_monitoring(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Execute audit task with comprehensive monitoring and Base44 protocol compliance.
        
        Args:
            task: Task dictionary containing audit requirements
            context: Task execution context with mode and confirmation settings
            
        Returns:
            Dictionary containing audit results
        """
        start_time = time.time()
        task_id = task.get('id', str(uuid.uuid4()))
        
        # Check if autonomous auditing is allowed
        if not self.is_action_allowed('autonomous_auditing'):
            return {
                'success': False,
                'error': 'Autonomous auditing is disabled in configuration',
                'audit_time': 0,
                'agent_id': self.agent_id,
                'task_id': task_id
            }
        
        try:
            self.update_status(AgentStatus.AUDITING, f"Auditing task {task_id}")
            
            with PerformanceTimer(f"auditor_task_{task.get('type', 'unknown')}") as timer:
                # Extract audit target
                audit_target = task.get('audit_target', {})
                if not audit_target:
                    raise ValueError("No audit target provided")
                
                # Perform audit with Base44 protocol monitoring
                audit_result = await self._perform_audit(audit_target)
                
                # Store audit in history
                audit_record = {
                    'task_id': task_id,
                    'audit_result': audit_result,
                    'timestamp': datetime.now().isoformat(),
                    'auditor_id': self.agent_id,
                    'context': {
                        'mode': context.mode.value,
                        'confirmation_level': context.confirmation_level.value
                    }
                }
                self.audit_history.append(audit_record)
                
                result = {
                    'success': True,
                    'audit_result': audit_result,
                    'audit_time': timer.elapsed_time,
                    'agent_id': self.agent_id,
                    'protocol_compliance': True
                }
                
                self.update_status(AgentStatus.COMPLETED, f"Audit completed for task {task_id}")
                self.record_task_completion(task_id, True, time.time() - start_time, result)
                
                return result
                
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'audit_time': time.time() - start_time,
                'agent_id': self.agent_id,
                'protocol_compliance': False
            }
            
            self.logger.error(f"Audit failed for task {task_id}: {e}")
            self.update_status(AgentStatus.FAILED, f"Audit failed: {e}")
            self.record_task_completion(task_id, False, time.time() - start_time, error_result)
            
            return error_result
    
    async def _rephrase_task(self, task: Dict[str, Any], context: TaskContext) -> str:
        """
        Rephrase audit task for confirmation using Base44 protocol.
        
        Args:
            task: Original task dictionary
            context: Task execution context
            
        Returns:
            Human-readable rephrased task description
        """
        task_type = task.get('type', 'audit')
        audit_target = task.get('audit_target', {})
        target_type = audit_target.get('type', 'unknown')
        
        if task_type == 'quality_audit':
            return f"Perform comprehensive quality audit on {target_type} to ensure compliance with quality standards and identify improvement opportunities."
        elif task_type == 'security_audit':
            return f"Conduct security audit on {target_type} to identify vulnerabilities, assess risk levels, and recommend security enhancements."
        elif task_type == 'performance_audit':
            return f"Execute performance audit on {target_type} to analyze efficiency metrics, identify bottlenecks, and suggest optimizations."
        elif task_type == 'compliance_audit':
            return f"Run compliance audit on {target_type} to verify adherence to regulatory requirements and internal policies."
        else:
            return f"Execute comprehensive audit on {target_type} covering quality, security, performance, and compliance aspects."
    
    async def _validate_rephrase_accuracy(self, original_task: Dict[str, Any], rephrased: str, context: TaskContext) -> bool:
        """
        Validate that the rephrased task accurately represents the original audit task.
        
        Args:
            original_task: Original task dictionary
            rephrased: Rephrased task description
            context: Task execution context
            
        Returns:
            True if rephrase is accurate, False otherwise
        """
        # Extract key elements from original task
        task_type = original_task.get('type', 'audit').lower()
        audit_target = original_task.get('audit_target', {})
        target_type = audit_target.get('type', 'unknown').lower()
        
        # Check if rephrased version contains essential elements
        rephrased_lower = rephrased.lower()
        
        # Verify audit type is mentioned
        audit_type_mentioned = any(audit_type in rephrased_lower for audit_type in [
            'quality', 'security', 'performance', 'compliance', 'comprehensive', 'audit'
        ])
        
        # Verify target type is mentioned
        target_mentioned = target_type in rephrased_lower or 'unknown' in rephrased_lower
        
        # Verify action words are present
        action_mentioned = any(action in rephrased_lower for action in [
            'perform', 'conduct', 'execute', 'run', 'analyze', 'assess', 'identify'
        ])
        
        # Calculate accuracy score
        accuracy_score = sum([
            audit_type_mentioned,
            target_mentioned,
            action_mentioned
        ]) / 3.0
        
        return accuracy_score >= 0.7  # 70% accuracy threshold
    
    async def _perform_audit(self, audit_target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a comprehensive audit of the target.
        
        Args:
            audit_target: Target to audit
            
        Returns:
            Audit result dictionary
        """
        audit_results = {
            'overall_score': 0.0,
            'quality_score': 0.0,
            'compliance_score': 0.0,
            'performance_score': 0.0,
            'security_score': 0.0,
            'issues': [],
            'recommendations': [],
            'passed': False
        }
        
        # Quality audit
        quality_result = await self._audit_quality(audit_target)
        audit_results['quality_score'] = quality_result['score']
        audit_results['issues'].extend(quality_result.get('issues', []))
        
        # Compliance audit
        compliance_result = await self._audit_compliance(audit_target)
        audit_results['compliance_score'] = compliance_result['score']
        audit_results['issues'].extend(compliance_result.get('issues', []))
        
        # Performance audit
        performance_result = await self._audit_performance(audit_target)
        audit_results['performance_score'] = performance_result['score']
        audit_results['issues'].extend(performance_result.get('issues', []))
        
        # Security audit
        security_result = await self._audit_security(audit_target)
        audit_results['security_score'] = security_result['score']
        audit_results['issues'].extend(security_result.get('issues', []))
        
        # Calculate overall score
        scores = [
            audit_results['quality_score'],
            audit_results['compliance_score'],
            audit_results['performance_score'],
            audit_results['security_score']
        ]
        audit_results['overall_score'] = sum(scores) / len(scores)
        
        # Determine if audit passed
        audit_results['passed'] = audit_results['overall_score'] >= self.audit_criteria['quality_threshold']
        
        # Generate recommendations
        if not audit_results['passed']:
            audit_results['recommendations'] = await self._generate_recommendations(audit_results)
        
        self.logger.info(f"Audit completed with overall score: {audit_results['overall_score']:.2f}")
        return audit_results
    
    async def _audit_quality(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive quality audit."""
        issues = []
        quality_score = 1.0
        
        try:
            # Check task completion status
            if target.get('status') != 'completed':
                issues.append(f"Task status is '{target.get('status')}', expected 'completed'")
                quality_score -= 0.3
            
            # Validate required outputs
            required_outputs = target.get('required_outputs', [])
            actual_outputs = target.get('outputs', {})
            
            for required_output in required_outputs:
                if required_output not in actual_outputs:
                    issues.append(f"Missing required output: {required_output}")
                    quality_score -= 0.2
                elif not actual_outputs[required_output]:
                    issues.append(f"Empty output for: {required_output}")
                    quality_score -= 0.1
            
            # Check execution time reasonableness
            execution_time = target.get('execution_time', 0)
            expected_time = target.get('estimated_time', 0)
            
            if expected_time > 0 and execution_time > expected_time * 3:
                issues.append(f"Execution time ({execution_time}s) significantly exceeds estimate ({expected_time}s)")
                quality_score -= 0.1
            
            # Validate output quality metrics
            if 'quality_metrics' in actual_outputs:
                metrics = actual_outputs['quality_metrics']
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        if isinstance(value, (int, float)) and value < 0.7:
                            issues.append(f"Quality metric '{metric}' below threshold: {value}")
                            quality_score -= 0.1
            
            # Check for error indicators
            if target.get('errors'):
                error_count = len(target['errors'])
                issues.append(f"Task completed with {error_count} errors")
                quality_score -= min(0.3, error_count * 0.1)
            
            # Ensure score doesn't go below 0
            quality_score = max(0.0, quality_score)
            
            self.logger.info(f"Quality audit completed with score: {quality_score:.2f}")
            return {
                'score': quality_score,
                'issues': issues,
                'metrics': {
                    'completion_status': target.get('status'),
                    'output_completeness': len(actual_outputs) / max(1, len(required_outputs)),
                    'execution_efficiency': min(1.0, expected_time / max(1, execution_time)) if expected_time > 0 else 1.0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Quality audit failed: {str(e)}")
            return {
                'score': 0.0,
                'issues': [f"Audit error: {str(e)}"],
                'metrics': {}
            }
    
    async def _audit_compliance(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Perform compliance audit against standards and requirements."""
        issues = []
        compliance_score = 1.0
        
        try:
            # Check task type compliance
            task_type = target.get('type', '')
            required_fields = self._get_required_fields_for_task_type(task_type)
            
            for field in required_fields:
                if field not in target:
                    issues.append(f"Missing required field for {task_type}: {field}")
                    compliance_score -= 0.2
            
            # Validate data format compliance
            outputs = target.get('outputs', {})
            for output_key, output_value in outputs.items():
                validation_result = self._validate_output_format(output_key, output_value)
                if not validation_result['valid']:
                    issues.extend(validation_result['issues'])
                    compliance_score -= 0.1
            
            # Check workflow compliance
            workflow_steps = target.get('workflow_steps', [])
            if workflow_steps:
                for step in workflow_steps:
                    if not step.get('completed'):
                        issues.append(f"Workflow step not completed: {step.get('name', 'Unknown')}")
                        compliance_score -= 0.15
            
            # Validate approval requirements
            if target.get('requires_approval', False):
                if not target.get('approved_by'):
                    issues.append("Task requires approval but no approver recorded")
                    compliance_score -= 0.3
            
            # Check documentation compliance
            if task_type in ['content_creation', 'research', 'marketing']:
                if not target.get('documentation'):
                    issues.append("Task type requires documentation but none provided")
                    compliance_score -= 0.1
            
            # Validate timestamp compliance
            created_at = target.get('created_at')
            completed_at = target.get('completed_at')
            
            if created_at and completed_at:
                if completed_at < created_at:
                    issues.append("Completion timestamp before creation timestamp")
                    compliance_score -= 0.2
            
            compliance_score = max(0.0, compliance_score)
            
            self.logger.info(f"Compliance audit completed with score: {compliance_score:.2f}")
            return {
                'score': compliance_score,
                'issues': issues,
                'compliance_checks': {
                    'required_fields': len(required_fields) - len([f for f in required_fields if f not in target]),
                    'workflow_completion': len([s for s in workflow_steps if s.get('completed')]) / max(1, len(workflow_steps)),
                    'approval_status': 'approved' if target.get('approved_by') else 'pending' if target.get('requires_approval') else 'not_required'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Compliance audit failed: {str(e)}")
            return {
                'score': 0.0,
                'issues': [f"Audit error: {str(e)}"],
                'compliance_checks': {}
            }
    
    async def _audit_performance(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Perform performance audit of task execution."""
        issues = []
        performance_score = 1.0
        
        try:
            # Analyze execution time performance
            execution_time = target.get('execution_time', 0)
            estimated_time = target.get('estimated_time', 0)
            
            if estimated_time > 0:
                time_ratio = execution_time / estimated_time
                if time_ratio > 2.0:
                    issues.append(f"Execution time ({execution_time}s) significantly exceeded estimate ({estimated_time}s)")
                    performance_score -= 0.3
                elif time_ratio > 1.5:
                    issues.append(f"Execution time ({execution_time}s) moderately exceeded estimate ({estimated_time}s)")
                    performance_score -= 0.1
            
            # Check resource utilization
            resource_usage = target.get('resource_usage', {})
            if resource_usage:
                cpu_usage = resource_usage.get('cpu_percent', 0)
                memory_usage = resource_usage.get('memory_mb', 0)
                
                if cpu_usage > 90:
                    issues.append(f"High CPU usage detected: {cpu_usage}%")
                    performance_score -= 0.2
                
                if memory_usage > 1000:  # 1GB threshold
                    issues.append(f"High memory usage detected: {memory_usage}MB")
                    performance_score -= 0.1
            
            # Evaluate output quality vs time trade-off
            outputs = target.get('outputs', {})
            quality_metrics = outputs.get('quality_metrics', {})
            
            if quality_metrics and execution_time > 0:
                avg_quality = sum(quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
                efficiency_ratio = avg_quality / (execution_time / 60)  # Quality per minute
                
                if efficiency_ratio < 0.1:
                    issues.append(f"Low efficiency ratio: {efficiency_ratio:.3f} quality/minute")
                    performance_score -= 0.15
            
            # Check for performance bottlenecks
            bottlenecks = target.get('performance_bottlenecks', [])
            if bottlenecks:
                issues.extend([f"Performance bottleneck: {b}" for b in bottlenecks])
                performance_score -= min(0.3, len(bottlenecks) * 0.1)
            
            # Analyze retry attempts
            retry_count = target.get('retry_count', 0)
            if retry_count > 0:
                issues.append(f"Task required {retry_count} retries")
                performance_score -= min(0.2, retry_count * 0.05)
            
            # Check concurrent task handling
            concurrent_tasks = target.get('concurrent_tasks', 1)
            if concurrent_tasks > 1:
                concurrency_efficiency = target.get('concurrency_efficiency', 1.0)
                if concurrency_efficiency < 0.7:
                    issues.append(f"Low concurrency efficiency: {concurrency_efficiency:.2f}")
                    performance_score -= 0.1
            
            performance_score = max(0.0, performance_score)
            
            self.logger.info(f"Performance audit completed with score: {performance_score:.2f}")
            return {
                'score': performance_score,
                'issues': issues,
                'performance_metrics': {
                    'execution_time': execution_time,
                    'time_efficiency': min(1.0, estimated_time / max(1, execution_time)) if estimated_time > 0 else 1.0,
                    'resource_efficiency': 1.0 - (cpu_usage / 100) * 0.5 if cpu_usage else 1.0,
                    'retry_rate': retry_count,
                    'bottleneck_count': len(bottlenecks)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Performance audit failed: {str(e)}")
            return {
                'score': 0.0,
                'issues': [f"Audit error: {str(e)}"],
                'performance_metrics': {}
            }
    
    async def _audit_security(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security audit."""
        issues = []
        security_score = 1.0
        
        try:
            # Check for sensitive data exposure
            outputs = target.get('outputs', {})
            for output_key, output_value in outputs.items():
                if self._contains_sensitive_data(output_value):
                    issues.append(f"Potential sensitive data exposure in output: {output_key}")
                    security_score -= 0.3
            
            # Validate input sanitization
            inputs = target.get('inputs', {})
            for input_key, input_value in inputs.items():
                if not self._is_input_sanitized(input_value):
                    issues.append(f"Unsanitized input detected: {input_key}")
                    security_score -= 0.2
            
            # Check authentication and authorization
            if target.get('requires_auth', False):
                if not target.get('authenticated_user'):
                    issues.append("Task requires authentication but no user authenticated")
                    security_score -= 0.4
                
                user_permissions = target.get('user_permissions', [])
                required_permissions = target.get('required_permissions', [])
                
                for perm in required_permissions:
                    if perm not in user_permissions:
                        issues.append(f"Missing required permission: {perm}")
                        security_score -= 0.2
            
            # Validate data encryption
            if target.get('contains_pii', False):
                if not target.get('encrypted', False):
                    issues.append("Task contains PII but data is not encrypted")
                    security_score -= 0.3
            
            # Check for secure communication
            external_calls = target.get('external_calls', [])
            for call in external_calls:
                if not call.get('url', '').startswith('https://'):
                    issues.append(f"Insecure HTTP call detected: {call.get('url')}")
                    security_score -= 0.2
            
            # Validate access logging
            if not target.get('access_logged', False) and target.get('requires_audit_trail', False):
                issues.append("Task requires audit trail but access not logged")
                security_score -= 0.1
            
            # Check for SQL injection vulnerabilities
            if 'database_queries' in outputs:
                queries = outputs['database_queries']
                if isinstance(queries, list):
                    for query in queries:
                        if self._has_sql_injection_risk(query):
                            issues.append(f"Potential SQL injection risk in query")
                            security_score -= 0.3
            
            # Validate file access permissions
            file_operations = target.get('file_operations', [])
            for operation in file_operations:
                if not self._is_file_access_secure(operation):
                    issues.append(f"Insecure file access: {operation.get('path')}")
                    security_score -= 0.2
            
            # Check for cross-site scripting (XSS) vulnerabilities
            if 'html_content' in outputs:
                html_content = outputs['html_content']
                if self._has_xss_vulnerability(html_content):
                    issues.append("Potential XSS vulnerability in HTML content")
                    security_score -= 0.3
            
            security_score = max(0.0, security_score)
            
            self.logger.info(f"Security audit completed with score: {security_score:.2f}")
            return {
                'score': security_score,
                'issues': issues,
                'security_checks': {
                    'authentication_status': 'authenticated' if target.get('authenticated_user') else 'anonymous',
                    'encryption_status': 'encrypted' if target.get('encrypted') else 'unencrypted',
                    'external_calls_secure': all(call.get('url', '').startswith('https://') for call in external_calls),
                    'audit_trail_enabled': target.get('access_logged', False),
                    'sensitive_data_protected': not any(self._contains_sensitive_data(v) for v in outputs.values())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Security audit failed: {str(e)}")
            return {
                'score': 0.0,
                'issues': [f"Audit error: {str(e)}"],
                'security_checks': {}
            }
    
    async def _generate_recommendations(self, audit_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on audit results."""
        recommendations = []
        
        if audit_results['quality_score'] < 0.8:
            recommendations.append("Improve code quality and documentation")
        
        if audit_results['performance_score'] < 0.8:
            recommendations.append("Optimize performance bottlenecks")
        
        if audit_results['security_score'] < 0.9:
            recommendations.append("Address security vulnerabilities")
        
        return recommendations
    
    def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent audit history.
        
        Args:
            limit: Maximum number of audit records to return
            
        Returns:
            List of recent audit records
        """
        return self.audit_history[-limit:] if self.audit_history else []
    
    def _get_required_fields_for_task_type(self, task_type: str) -> List[str]:
        """Get required fields for a specific task type."""
        field_requirements = {
            'content_creation': ['title', 'content', 'target_audience', 'created_at'],
            'research': ['topic', 'sources', 'findings', 'methodology'],
            'marketing': ['campaign_name', 'target_audience', 'channels', 'budget'],
            'system_maintenance': ['system_component', 'maintenance_type', 'completion_status'],
            'quality_assurance': ['test_cases', 'test_results', 'pass_criteria'],
            'planning': ['objectives', 'timeline', 'resources', 'deliverables']
        }
        return field_requirements.get(task_type, ['id', 'type', 'status', 'created_at'])
    
    def _validate_output_format(self, output_key: str, output_value: Any) -> Dict[str, Any]:
        """Validate the format of task outputs."""
        issues = []
        valid = True
        
        # Check for empty or null outputs
        if output_value is None or (isinstance(output_value, str) and not output_value.strip()):
            issues.append(f"Output '{output_key}' is empty or null")
            valid = False
        
        # Validate specific output formats
        if output_key == 'content' and isinstance(output_value, str):
            if len(output_value) < 10:
                issues.append(f"Content output too short: {len(output_value)} characters")
                valid = False
        
        elif output_key == 'url' and isinstance(output_value, str):
            if not (output_value.startswith('http://') or output_value.startswith('https://')):
                issues.append(f"Invalid URL format: {output_value}")
                valid = False
        
        elif output_key == 'email' and isinstance(output_value, str):
            if '@' not in output_value or '.' not in output_value:
                issues.append(f"Invalid email format: {output_value}")
                valid = False
        
        elif output_key in ['date', 'timestamp'] and isinstance(output_value, str):
            try:
                from datetime import datetime
                datetime.fromisoformat(output_value.replace('Z', '+00:00'))
            except ValueError:
                issues.append(f"Invalid date/timestamp format: {output_value}")
                valid = False
        
        return {'valid': valid, 'issues': issues}
    
    def _contains_sensitive_data(self, data: Any) -> bool:
        """Check if data contains sensitive information."""
        if not isinstance(data, str):
            data = str(data)
        
        sensitive_patterns = [
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b(?:password|pwd|pass|secret|key|token)\s*[:=]\s*\S+\b',  # Passwords/keys
            r'\b(?:api[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*\S+\b'  # API keys
        ]
        
        import re
        for pattern in sensitive_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return True
        
        return False
    
    def _is_input_sanitized(self, input_value: Any) -> bool:
        """Check if input has been properly sanitized."""
        if not isinstance(input_value, str):
            return True  # Non-string inputs are considered safe
        
        # Check for common injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'\b(union|select|insert|update|delete|drop|create|alter)\b',  # SQL keywords
            r'[\'\";]',  # SQL injection characters
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, input_value, re.IGNORECASE):
                return False
        
        return True
    
    def _has_sql_injection_risk(self, query: str) -> bool:
        """Check if a database query has SQL injection risks."""
        if not isinstance(query, str):
            return False
        
        # Look for unparameterized queries with user input
        risky_patterns = [
            r"'\s*\+\s*",  # String concatenation
            r'"\s*\+\s*',  # String concatenation
            r'\$\{.*?\}',  # Template literals
            r'%s.*%s',  # Python string formatting
            r'\?.*\?'  # Suspicious parameter patterns
        ]
        
        import re
        for pattern in risky_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def _is_file_access_secure(self, operation: Dict[str, Any]) -> bool:
        """Check if file access operation is secure."""
        path = operation.get('path', '')
        operation_type = operation.get('type', '')
        
        # Check for directory traversal
        if '../' in path or '..\\' in path:
            return False
        
        # Check for access to sensitive system files
        sensitive_paths = [
            '/etc/passwd', '/etc/shadow', '/etc/hosts',
            'C:\\Windows\\System32', 'C:\\Windows\\SysWOW64',
            '/proc/', '/sys/', '/dev/'
        ]
        
        for sensitive_path in sensitive_paths:
            if path.startswith(sensitive_path):
                return False
        
        # Check for write operations to system directories
        if operation_type in ['write', 'delete', 'modify']:
            system_dirs = ['/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/', 'C:\\Program Files']
            for sys_dir in system_dirs:
                if path.startswith(sys_dir):
                    return False
        
        return True
    
    def _has_xss_vulnerability(self, html_content: str) -> bool:
        """Check if HTML content has XSS vulnerabilities."""
        if not isinstance(html_content, str):
            return False
        
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=\s*["\'][^"\'>]*["\']',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>'
        ]
        
        import re
        for pattern in xss_patterns:
            if re.search(pattern, html_content, re.IGNORECASE | re.DOTALL):
                return True
        
        return False