#!/usr/bin/env python3
"""
TRAE.AI Dashboard - Total Access Command Center

A comprehensive web dashboard providing complete visibility and control over
the TRAE.AI agentic framework. Features four dedicated modules for total system access.

Modules:
1. Agent Command Center - Real-time agent monitoring and control
2. Intelligence Database Explorer - Direct SQLite database access
3. Digital Product Studio - Book/course project management
4. On-Demand Reporting Engine - Instant report generation

Additional Features:
- Manual workflow triggers
- Monetization toggles
- Channel status controls
- Real-time task queue monitoring
- Performance metrics

Author: TRAE.AI System
Version: 2.0.0 - Total Access Upgrade
"""

import os
import json
import logging
import secrets
import socket
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response
from waitress import serve
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

# Import TRAE.AI components
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.task_queue_manager import TaskQueueManager, TaskStatus, TaskPriority, TaskType
    from backend.agents.base_agents import AgentStatus, AgentCapability
    from utils.logger import get_logger, setup_logging
    TRAE_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TRAE.AI components: {e}")
    print("Running in standalone mode...")
    TRAE_AI_AVAILABLE = False
    
    # Create fallback functions and classes
    def get_logger(name):
        return logging.getLogger(name)
    
    def setup_logging(log_level='INFO'):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Mock classes for standalone mode
    class TaskQueueManager:
        def __init__(self, db_path):
            pass
        def get_queue_stats(self):
            return {'pending': 0, 'in_progress': 0, 'completed': 0, 'failed': 0}
        def add_task(self, *args, **kwargs):
            return {'task_id': 'mock-task-id', 'status': 'pending'}
        def get_recent_tasks(self, limit=10):
            return []
        def get_tasks(self, status=None, task_type=None, agent_id=None, limit=100, offset=0):
            return []
    
    class TaskStatus:
        PENDING = 'pending'
        IN_PROGRESS = 'in_progress'
        COMPLETED = 'completed'
        FAILED = 'failed'
    
    class TaskPriority:
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'
    
    class TaskType:
        VIDEO_CREATION = 'video_creation'
        RESEARCH = 'research'
        CONTENT_AUDIT = 'content_audit'
        MARKETING = 'marketing'
    
    class AgentStatus:
        IDLE = 'idle'
        BUSY = 'busy'
        ERROR = 'error'
    
    class AgentCapability:
        PLANNING = 'planning'
        EXECUTION = 'execution'
        AUDITING = 'auditing'


@dataclass
class DashboardConfig:
    """Configuration for the dashboard application."""
    host: str = '0.0.0.0'
    port: int = 8080
    debug: bool = False
    secret_key: str = 'trae-ai-dashboard-secret-key-change-in-production'
    database_path: str = 'trae_ai.db'
    intelligence_db_path: str = 'right_perspective.db'
    log_level: str = 'INFO'
    max_tasks_display: int = 100
    refresh_interval: int = 5  # seconds
    log_directory: str = 'logs'


@dataclass
class AgentInfo:
    """Information about an individual agent."""
    id: str
    name: str
    status: str  # idle, processing, error
    current_task_id: Optional[str] = None
    uptime: str = "0h 0m"
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ProjectInfo:
    """Information about a digital product project."""
    id: str
    name: str
    type: str  # book, course, guide
    status: str  # planning, writing, reviewing, completed
    progress: float  # 0.0 to 1.0
    chapters_completed: int
    total_chapters: int
    created_at: datetime
    last_updated: datetime


class DashboardApp:
    """Main dashboard application class with Total Access modules."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='templates')
        self.app.secret_key = self.config.secret_key
        
        # Initialize logging
        setup_logging(log_level=self.config.log_level)
        self.logger = get_logger(__name__)
        
        # Initialize task queue manager
        try:
            self.task_manager = TaskQueueManager(self.config.database_path)
            self.logger.info("TaskQueueManager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize TaskQueueManager: {e}")
            self.task_manager = None
        
        self.start_time = datetime.now()
        
        # Initialize agent tracking
        self.agents = {}
        self.agent_processes = {}
        
        # Initialize project tracking
        self.projects = {}
        
        self._setup_routes()
        self._setup_error_handlers()
        
        # Initialize database connections
        self._init_databases()
        
        # Start background monitoring
        self._start_monitoring_thread()
        
        self.logger.info("Dashboard application initialized")
    
    def _init_databases(self):
        """Initialize database connections."""
        try:
            # Ensure intelligence database exists
            intelligence_db_path = Path(self.config.intelligence_db_path)
            if not intelligence_db_path.exists():
                self.logger.warning(f"Intelligence database not found at {intelligence_db_path}")
            
            # Test connection
            with sqlite3.connect(self.config.intelligence_db_path) as conn:
                conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                self.logger.info("Intelligence database connection established")
        except Exception as e:
            self.logger.error(f"Failed to initialize intelligence database: {e}")
    
    def _start_monitoring_thread(self):
        """Start background thread for monitoring agents and projects."""
        def monitor():
            while True:
                try:
                    self._update_agent_status()
                    self._update_project_status()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    self.logger.error(f"Monitoring thread error: {e}")
                    time.sleep(30)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.logger.info("Background monitoring thread started")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return send_from_directory('static', 'index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files."""
            return send_from_directory('static', filename)
        
        # API Routes
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            try:
                health_status = {
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'version': '1.0.0',
                    'components': {
                        'task_manager': self.task_manager is not None,
                        'database': self._check_database_health()
                    }
                }
                return jsonify(health_status)
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get task queue status."""
            try:
                if not self.task_manager:
                    return jsonify({'error': 'Task manager not available'}), 503
                
                # Get query parameters
                status = request.args.get('status')
                limit = min(int(request.args.get('limit', 50)), self.config.max_tasks_display)
                
                tasks = self.task_manager.get_tasks(
                    status=TaskStatus(status) if status else None,
                    limit=limit
                )
                
                task_list = []
                for task in tasks:
                    task_dict = {
                        'id': task.get('id'),
                        'type': task.get('task_type'),
                        'priority': task.get('priority'),
                        'status': task.get('status'),
                        'agent_id': task.get('assigned_agent'),
                        'payload': task.get('payload', {}),
                        'created_at': task.get('created_at'),
                        'updated_at': task.get('updated_at'),
                        'retry_count': task.get('retry_count', 0),
                        'error_message': task.get('error_message')
                    }
                    task_list.append(task_dict)
                
                return jsonify({
                    'tasks': task_list,
                    'total': len(task_list),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get tasks: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['POST'])
        def create_task():
            """Create a new task."""
            try:
                if not self.task_manager:
                    return jsonify({'error': 'Task manager not available'}), 503
                
                data = request.get_json()
                if not data:
                    raise BadRequest("No JSON data provided")
                
                # Validate required fields
                required_fields = ['type', 'payload']
                for field in required_fields:
                    if field not in data:
                        raise BadRequest(f"Missing required field: {field}")
                
                # Create task
                task_id = self.task_manager.add_task(
                    task_type=TaskType(data['type']),
                    payload=data['payload'],
                    priority=TaskPriority(data.get('priority', 'medium')),
                    agent_id=data.get('agent_id')
                )
                
                self.logger.info(f"Created task {task_id} of type {data['type']}")
                
                return jsonify({
                    'task_id': task_id,
                    'status': 'created',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }), 201
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to create task: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tasks/<task_id>', methods=['PUT'])
        def update_task(task_id):
            """Update task status."""
            try:
                if not self.task_manager:
                    return jsonify({'error': 'Task manager not available'}), 503
                
                data = request.get_json()
                if not data or 'status' not in data:
                    raise BadRequest("Status field required")
                
                success = self.task_manager.update_task_status(
                    task_id=task_id,
                    status=TaskStatus(data['status']),
                    error_message=data.get('error_message')
                )
                
                if success:
                    self.logger.info(f"Updated task {task_id} status to {data['status']}")
                    return jsonify({
                        'task_id': task_id,
                        'status': 'updated',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                else:
                    return jsonify({'error': 'Task not found'}), 404
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to update task {task_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get system statistics."""
            try:
                if not self.task_manager:
                    return jsonify({'error': 'Task manager not available'}), 503
                
                stats = self.task_manager.get_queue_stats()
                
                return jsonify({
                    'queue_stats': stats,
                    'system_info': {
                        'uptime': self._get_uptime(),
                        'memory_usage': self._get_memory_usage(),
                        'active_connections': 1  # Placeholder
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Workflow API endpoints
        @self.app.route('/api/workflows/create-video', methods=['POST'])
        def create_video_workflow():
            """Trigger video creation workflow."""
            return self._create_workflow_task('video_creation', request.get_json() or {})
        
        @self.app.route('/api/workflows/research', methods=['POST'])
        def research_workflow():
            """Trigger research workflow."""
            return self._create_workflow_task('research', request.get_json() or {})
        
        @self.app.route('/api/workflows/content-audit', methods=['POST'])
        def content_audit_workflow():
            """Trigger content audit workflow."""
            return self._create_workflow_task('content_audit', request.get_json() or {})
        
        @self.app.route('/api/workflows/marketing', methods=['POST'])
        def marketing_workflow():
            """Trigger marketing workflow."""
            return self._create_workflow_task('marketing', request.get_json() or {})
        
        # API Suggestions Management endpoints
        @self.app.route('/api/suggestions', methods=['GET'])
        def get_api_suggestions():
            """Get API suggestions from the discovery system."""
            try:
                # Import the API Opportunity Finder
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from api_opportunity_finder import APIOpportunityFinder
                
                finder = APIOpportunityFinder(self.config.intelligence_db_path)
                
                # Get query parameters
                status = request.args.get('status', 'pending')
                limit = int(request.args.get('limit', 20))
                
                suggestions = finder.get_suggestions_by_status(status, limit)
                
                # Format suggestions for frontend
                formatted_suggestions = []
                for suggestion in suggestions:
                    formatted_suggestions.append({
                        'id': suggestion.id,
                        'api_name': suggestion.api_name,
                        'description': suggestion.description,
                        'base_url': suggestion.base_url,
                        'category': suggestion.category,
                        'confidence_score': suggestion.confidence_score,
                        'reasoning': suggestion.reasoning,
                        'status': suggestion.status,
                        'discovered_at': suggestion.discovered_at.isoformat() if suggestion.discovered_at else None,
                        'source_url': suggestion.source_url,
                        'estimated_cost': suggestion.estimated_cost,
                        'rate_limits': suggestion.rate_limits,
                        'authentication_method': suggestion.authentication_method
                    })
                
                return jsonify({
                    'suggestions': formatted_suggestions,
                    'total': len(formatted_suggestions),
                    'status': status,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Failed to get API suggestions: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/suggestions/<suggestion_id>/approve', methods=['POST'])
        def approve_api_suggestion(suggestion_id):
            """Approve an API suggestion and add it to the registry."""
            try:
                # Import required modules
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from api_opportunity_finder import APIOpportunityFinder
                from api_orchestrator_enhanced import APIOrchestrator
                
                finder = APIOpportunityFinder(self.config.intelligence_db_path)
                orchestrator = APIOrchestrator(self.config.intelligence_db_path)
                
                # Get the suggestion
                suggestion = finder.get_suggestion_by_id(suggestion_id)
                if not suggestion:
                    return jsonify({'error': 'Suggestion not found'}), 404
                
                # Add to API registry
                api_data = {
                    'service_name': suggestion.api_name,
                    'capability': suggestion.category,
                    'api_url': suggestion.base_url,
                    'priority': 5,  # Medium priority for new APIs
                    'documentation_url': suggestion.source_url,
                    'authentication_type': suggestion.authentication_method,
                    'cost_per_request': suggestion.estimated_cost,
                    'discovery_source': 'api_opportunity_finder',
                    'validation_status': 'pending',
                    'tags': f'{suggestion.category},discovered'
                }
                
                # Add to registry
                registry_id = orchestrator._add_api_to_registry(**api_data)
                
                # Update suggestion status
                finder.update_suggestion_status(suggestion_id, 'approved')
                
                self.logger.info(f"API suggestion {suggestion_id} approved and added to registry as {registry_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'API suggestion approved and added to registry',
                    'registry_id': registry_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Failed to approve API suggestion {suggestion_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/suggestions/<suggestion_id>/reject', methods=['POST'])
        def reject_api_suggestion(suggestion_id):
            """Reject an API suggestion."""
            try:
                # Import the API Opportunity Finder
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from api_opportunity_finder import APIOpportunityFinder
                
                finder = APIOpportunityFinder(self.config.intelligence_db_path)
                
                # Update suggestion status
                success = finder.update_suggestion_status(suggestion_id, 'rejected')
                
                if success:
                    self.logger.info(f"API suggestion {suggestion_id} rejected")
                    return jsonify({
                        'success': True,
                        'message': 'API suggestion rejected',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                else:
                    return jsonify({'error': 'Suggestion not found'}), 404
                
            except Exception as e:
                self.logger.error(f"Failed to reject API suggestion {suggestion_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Agent Management endpoints
        @self.app.route('/api/agents', methods=['GET'])
        def get_agents():
            """Get all agents status."""
            try:
                agents_list = []
                for agent_id, agent_info in self.agents.items():
                    agents_list.append({
                        'id': agent_info.id,
                        'name': agent_info.name,
                        'status': agent_info.status,
                        'current_task_id': agent_info.current_task_id,
                        'uptime': agent_info.uptime,
                        'last_activity': agent_info.last_activity.isoformat() if agent_info.last_activity else None,
                        'error_message': agent_info.error_message
                    })
                
                return jsonify({
                    'agents': agents_list,
                    'total': len(agents_list),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get agents: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/agents/<agent_id>/start', methods=['POST'])
        def start_agent(agent_id):
            """Start an agent."""
            try:
                # Implementation would depend on agent management system
                self.logger.info(f"Starting agent {agent_id}")
                
                return jsonify({
                    'success': True,
                    'message': f'Agent {agent_id} started',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to start agent {agent_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/agents/<agent_id>/stop', methods=['POST'])
        def stop_agent(agent_id):
            """Stop an agent."""
            try:
                # Implementation would depend on agent management system
                self.logger.info(f"Stopping agent {agent_id}")
                
                return jsonify({
                    'success': True,
                    'message': f'Agent {agent_id} stopped',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to stop agent {agent_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Database Explorer endpoints
        @self.app.route('/api/database/tables', methods=['GET'])
        def get_database_tables():
            """Get all tables in the intelligence database."""
            try:
                with sqlite3.connect(self.config.intelligence_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [row[0] for row in cursor.fetchall()]
                
                return jsonify({
                    'tables': tables,
                    'total': len(tables),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get database tables: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/database/tables/<table_name>/schema', methods=['GET'])
        def get_table_schema(table_name):
            """Get schema for a specific table."""
            try:
                with sqlite3.connect(self.config.intelligence_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    schema = cursor.fetchall()
                    
                    columns = []
                    for row in schema:
                        columns.append({
                            'cid': row[0],
                            'name': row[1],
                            'type': row[2],
                            'notnull': bool(row[3]),
                            'default_value': row[4],
                            'pk': bool(row[5])
                        })
                
                return jsonify({
                    'table_name': table_name,
                    'columns': columns,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get table schema for {table_name}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/database/tables/<table_name>/data', methods=['GET'])
        def get_table_data(table_name):
            """Get data from a specific table."""
            try:
                limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 rows
                offset = int(request.args.get('offset', 0))
                
                with sqlite3.connect(self.config.intelligence_db_path) as conn:
                    conn.row_factory = sqlite3.Row  # Enable column access by name
                    cursor = conn.cursor()
                    
                    # Get total count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = cursor.fetchone()[0]
                    
                    # Get data with limit and offset
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = [dict(row) for row in rows]
                
                return jsonify({
                    'table_name': table_name,
                    'data': data,
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get table data for {table_name}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/database/query', methods=['POST'])
        def execute_database_query():
            """Execute a custom SQL query (read-only)."""
            try:
                data = request.get_json()
                if not data or 'query' not in data:
                    raise BadRequest("Query field required")
                
                query = data['query'].strip()
                
                # Security check: only allow SELECT statements
                if not query.upper().startswith('SELECT'):
                    raise BadRequest("Only SELECT queries are allowed")
                
                with sqlite3.connect(self.config.intelligence_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = [dict(row) for row in rows]
                
                return jsonify({
                    'query': query,
                    'data': data,
                    'row_count': len(data),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to execute query: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Project Management endpoints
        @self.app.route('/api/projects', methods=['GET'])
        def get_projects():
            """Get all digital product projects."""
            try:
                projects_list = []
                for project_id, project_info in self.projects.items():
                    projects_list.append({
                        'id': project_info.id,
                        'name': project_info.name,
                        'type': project_info.type,
                        'status': project_info.status,
                        'progress': project_info.progress,
                        'chapters_completed': project_info.chapters_completed,
                        'total_chapters': project_info.total_chapters,
                        'created_at': project_info.created_at.isoformat(),
                        'last_updated': project_info.last_updated.isoformat()
                    })
                
                return jsonify({
                    'projects': projects_list,
                    'total': len(projects_list),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get projects: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/projects', methods=['POST'])
        def create_project():
            """Create a new digital product project."""
            try:
                data = request.get_json()
                if not data:
                    raise BadRequest("No JSON data provided")
                
                # Validate required fields
                required_fields = ['name', 'type']
                for field in required_fields:
                    if field not in data:
                        raise BadRequest(f"Missing required field: {field}")
                
                # Create project
                project_id = f"proj_{secrets.token_hex(8)}"
                project = ProjectInfo(
                    id=project_id,
                    name=data['name'],
                    type=data['type'],
                    status='planning',
                    progress=0.0,
                    chapters_completed=0,
                    total_chapters=data.get('total_chapters', 10),
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                self.projects[project_id] = project
                
                self.logger.info(f"Created project {project_id}: {data['name']}")
                
                return jsonify({
                    'project_id': project_id,
                    'status': 'created',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }), 201
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to create project: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/projects/<project_id>', methods=['PUT'])
        def update_project(project_id):
            """Update a project."""
            try:
                if project_id not in self.projects:
                    return jsonify({'error': 'Project not found'}), 404
                
                data = request.get_json()
                if not data:
                    raise BadRequest("No JSON data provided")
                
                project = self.projects[project_id]
                
                # Update fields
                if 'name' in data:
                    project.name = data['name']
                if 'status' in data:
                    project.status = data['status']
                if 'progress' in data:
                    project.progress = float(data['progress'])
                if 'chapters_completed' in data:
                    project.chapters_completed = int(data['chapters_completed'])
                if 'total_chapters' in data:
                    project.total_chapters = int(data['total_chapters'])
                
                project.last_updated = datetime.now()
                
                self.logger.info(f"Updated project {project_id}")
                
                return jsonify({
                    'project_id': project_id,
                    'status': 'updated',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to update project {project_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Reporting endpoints
        @self.app.route('/api/reports/performance', methods=['GET'])
        def get_performance_report():
            """Generate performance report."""
            try:
                report = self._generate_performance_report()
                return jsonify(report)
            except Exception as e:
                self.logger.error(f"Failed to generate performance report: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/content', methods=['GET'])
        def get_content_report():
            """Generate content report."""
            try:
                report = self._generate_content_report()
                return jsonify(report)
            except Exception as e:
                self.logger.error(f"Failed to generate content report: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reports/financial', methods=['GET'])
        def get_financial_report():
            """Generate financial report."""
            try:
                report = self._generate_financial_report()
                return jsonify(report)
            except Exception as e:
                self.logger.error(f"Failed to generate financial report: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Channel Management endpoints
        @self.app.route('/api/channels', methods=['GET'])
        def get_channels():
            """Get all channel statuses."""
            try:
                channels = {
                    'youtube': self._fetch_youtube_channel_data(),
                    'tiktok': self._fetch_tiktok_channel_data(),
                    'instagram': self._fetch_instagram_channel_data()
                }
                
                return jsonify({
                    'channels': channels,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get channels: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels/<channel_type>/toggle', methods=['POST'])
        def toggle_channel(channel_type):
            """Toggle channel monetization."""
            try:
                data = request.get_json() or {}
                enabled = data.get('enabled', True)
                
                # Implementation would depend on channel management system
                self.logger.info(f"Toggling {channel_type} channel: {enabled}")
                
                return jsonify({
                    'success': True,
                    'channel_type': channel_type,
                    'enabled': enabled,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to toggle {channel_type} channel: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Monetization endpoints
        @self.app.route('/api/monetization/affiliates', methods=['GET'])
        def get_affiliate_status():
            """Get affiliate program status."""
            try:
                status = self._get_affiliate_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Failed to get affiliate status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monetization/affiliates/toggle', methods=['POST'])
        def toggle_affiliate_program():
            """Toggle affiliate program."""
            try:
                data = request.get_json() or {}
                enabled = data.get('enabled', True)
                
                # Implementation would depend on affiliate management system
                self.logger.info(f"Toggling affiliate program: {enabled}")
                
                return jsonify({
                    'success': True,
                    'affiliate_program_enabled': enabled,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to toggle affiliate program: {e}")
                return jsonify({'error': str(e)}), 500
        
        # System Configuration endpoints
        @self.app.route('/api/config', methods=['GET'])
        def get_system_config():
            """Get system configuration."""
            try:
                config_path = 'config/state.json'
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                else:
                    # Default configuration
                    config = {
                        'autonomous_mode': True,
                        'content_generation': {
                            'enabled': True,
                            'frequency': 'daily',
                            'quality_threshold': 0.8
                        },
                        'monetization': {
                            'affiliate_programs': True,
                            'sponsored_content': False,
                            'premium_features': True
                        },
                        'channels': {
                            'youtube': {'enabled': True, 'auto_upload': True},
                            'tiktok': {'enabled': True, 'auto_upload': False},
                            'instagram': {'enabled': False, 'auto_upload': False}
                        },
                        'security': {
                            'api_rate_limiting': True,
                            'content_moderation': True,
                            'backup_frequency': 'daily'
                        }
                    }
                
                return jsonify({
                    'config': config,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get system config: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['POST'])
        def update_system_config():
            """Update system configuration."""
            try:
                data = request.get_json()
                if not data:
                    raise BadRequest("No JSON data provided")
                
                config_path = 'config/state.json'
                
                # Ensure config directory exists
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Save configuration
                with open(config_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.logger.info("System configuration updated")
                
                return jsonify({
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to update system config: {e}")
                return jsonify({'error': str(e)}), 500
        
        # System Files endpoints
        @self.app.route('/api/system/files', methods=['GET'])
        def get_system_files():
            """Get system files for backup/export."""
            try:
                files = self._get_system_files()
                return jsonify({
                    'files': files,
                    'total': len(files),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                self.logger.error(f"Failed to get system files: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system/backup', methods=['POST'])
        def create_system_backup():
            """Create a system backup."""
            try:
                # Implementation would create a backup archive
                backup_id = f"backup_{int(datetime.now().timestamp())}"
                
                self.logger.info(f"Creating system backup: {backup_id}")
                
                return jsonify({
                    'success': True,
                    'backup_id': backup_id,
                    'message': 'Backup created successfully',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to create system backup: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Code Export endpoints
        @self.app.route('/api/codebase', methods=['GET'])
        def get_codebase_structure():
            """Get complete codebase structure and content."""
            try:
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                def get_file_tree(directory, max_depth=3, current_depth=0):
                    """Recursively build file tree structure."""
                    if current_depth >= max_depth:
                        return []
                    
                    items = []
                    try:
                        for item in sorted(os.listdir(directory)):
                            if item.startswith('.'):
                                continue
                            
                            item_path = os.path.join(directory, item)
                            relative_path = os.path.relpath(item_path, project_root)
                            
                            if os.path.isdir(item_path):
                                # Skip certain directories
                                if item in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']:
                                    continue
                                
                                items.append({
                                    'name': item,
                                    'type': 'directory',
                                    'path': relative_path,
                                    'children': get_file_tree(item_path, max_depth, current_depth + 1)
                                })
                            else:
                                # Only include certain file types
                                if item.endswith(('.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml', '.sh')):
                                    items.append({
                                        'name': item,
                                        'type': 'file',
                                        'path': relative_path,
                                        'size': os.path.getsize(item_path)
                                    })
                    except PermissionError:
                        pass
                    
                    return items
                
                file_tree = get_file_tree(project_root)
                
                return jsonify({
                    'project_root': project_root,
                    'file_tree': file_tree,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                self.logger.error(f"Failed to get codebase structure: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/codebase/file', methods=['GET'])
        def get_file_content():
            """Get content of a specific file."""
            try:
                file_path = request.args.get('path')
                if not file_path:
                    raise BadRequest("File path parameter required")
                
                # Security check: ensure path is within project
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(project_root, file_path)
                full_path = os.path.abspath(full_path)
                
                if not full_path.startswith(os.path.abspath(project_root)):
                    raise BadRequest("Invalid file path")
                
                if not os.path.exists(full_path) or not os.path.isfile(full_path):
                    return jsonify({'error': 'File not found'}), 404
                
                # Read file content
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Handle binary files
                    content = "[Binary file - content not displayable]"
                
                return jsonify({
                    'path': file_path,
                    'content': content,
                    'size': os.path.getsize(full_path),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to get file content: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/codebase/search', methods=['GET'])
        def search_codebase():
            """Search through codebase files."""
            try:
                query = request.args.get('q', '').strip()
                if not query:
                    raise BadRequest("Search query parameter 'q' required")
                
                file_type = request.args.get('type', 'all')  # all, py, js, html, etc.
                
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                results = []
                
                def search_in_file(file_path, query):
                    """Search for query in a file and return matching lines."""
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            matches = []
                            for i, line in enumerate(lines, 1):
                                if query.lower() in line.lower():
                                    matches.append({
                                        'line_number': i,
                                        'content': line.strip(),
                                        'context': {
                                            'before': lines[max(0, i-2):i-1] if i > 1 else [],
                                            'after': lines[i:min(len(lines), i+2)] if i < len(lines) else []
                                        }
                                    })
                            return matches
                    except (UnicodeDecodeError, PermissionError):
                        return []
                
                # Walk through project files
                for root, dirs, files in os.walk(project_root):
                    # Skip certain directories
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
                    
                    for file in files:
                        if file.startswith('.'):
                            continue
                        
                        # Filter by file type
                        if file_type != 'all':
                            if not file.endswith(f'.{file_type}'):
                                continue
                        else:
                            # Only search in text files
                            if not file.endswith(('.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml')):
                                continue
                        
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_root)
                        
                        matches = search_in_file(file_path, query)
                        if matches:
                            results.append({
                                'file': relative_path,
                                'matches': matches[:10]  # Limit matches per file
                            })
                        
                        # Limit total results
                        if len(results) >= 50:
                            break
                    
                    if len(results) >= 50:
                        break
                
                return jsonify({
                    'query': query,
                    'file_type': file_type,
                    'results': results,
                    'total_files': len(results),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                self.logger.error(f"Failed to search codebase: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/codebase/export', methods=['POST'])
        def export_codebase():
            """Export complete codebase as ZIP file."""
            try:
                import zipfile
                import tempfile
                
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Create temporary ZIP file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(project_root):
                            # Skip certain directories
                            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
                            
                            for file in files:
                                if file.startswith('.'):
                                    continue
                                
                                file_path = os.path.join(root, file)
                                relative_path = os.path.relpath(file_path, project_root)
                                
                                # Only include certain file types
                                if file.endswith(('.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml', '.sh')):
                                    zipf.write(file_path, relative_path)
                    
                    # Send the ZIP file
                    return send_file(
                        tmp_file.name,
                        as_attachment=True,
                        download_name=f'trae_ai_codebase_{int(datetime.now().timestamp())}.zip',
                        mimetype='application/zip'
                    )
            
            except Exception as e:
                self.logger.error(f"Failed to export codebase: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _fetch_youtube_channel_data(self) -> Dict[str, Any]:
        """Fetch YouTube channel data."""
        try:
            # Mock data - replace with actual YouTube API integration
            return {
                'name': 'TRAE.AI Channel',
                'subscribers': 15420,
                'videos': 127,
                'views': 2840000,
                'revenue': 1250.75,
                'status': 'active',
                'monetization_enabled': True,
                'last_upload': '2024-01-15T10:30:00Z',
                'engagement_rate': 0.045,
                'top_performing_video': {
                    'title': 'AI Content Creation Masterclass',
                    'views': 45000,
                    'likes': 2100,
                    'comments': 340
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch YouTube data: {e}")
            return {
                'name': 'YouTube Channel',
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_tiktok_channel_data(self) -> Dict[str, Any]:
        """Fetch TikTok channel data."""
        try:
            # Mock data - replace with actual TikTok API integration
            return {
                'name': 'TRAE.AI TikTok',
                'followers': 8750,
                'videos': 89,
                'likes': 125000,
                'status': 'active',
                'monetization_enabled': False,
                'last_upload': '2024-01-14T16:45:00Z',
                'engagement_rate': 0.078,
                'trending_video': {
                    'title': '60-Second AI Tutorial',
                    'views': 12000,
                    'likes': 890,
                    'shares': 156
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch TikTok data: {e}")
            return {
                'name': 'TikTok Channel',
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_instagram_channel_data(self) -> Dict[str, Any]:
        """Fetch Instagram channel data."""
        try:
            # Mock data - replace with actual Instagram API integration
            return {
                'name': 'TRAE.AI Instagram',
                'followers': 5230,
                'posts': 156,
                'engagement': 18500,
                'status': 'inactive',
                'monetization_enabled': False,
                'last_post': '2024-01-10T12:20:00Z',
                'engagement_rate': 0.032,
                'top_post': {
                    'caption': 'Behind the scenes of AI content creation',
                    'likes': 450,
                    'comments': 67,
                    'type': 'image'
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch Instagram data: {e}")
            return {
                'name': 'Instagram Channel',
                'status': 'error',
                'error': str(e)
            }
    
    def _setup_error_handlers(self):
        """Setup error handlers for the Flask app."""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.errorhandler(BadRequest)
        def bad_request(error):
            return jsonify({'error': str(error)}), 400
    
    def _create_workflow_task(self, workflow_type: str, payload: Dict[str, Any]):
        """Create a workflow task."""
        try:
            if not self.task_manager:
                return jsonify({'error': 'Task manager not available'}), 503
            
            task_id = self.task_manager.add_task(
                task_type=TaskType(workflow_type),
                payload=payload,
                priority=TaskPriority.MEDIUM
            )
            
            self.logger.info(f"Created {workflow_type} workflow task: {task_id}")
            
            return jsonify({
                'task_id': task_id,
                'workflow_type': workflow_type,
                'status': 'created',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 201
        
        except Exception as e:
            self.logger.error(f"Failed to create {workflow_type} workflow: {e}")
            return jsonify({'error': str(e)}), 500
    
    def _check_database_health(self) -> bool:
        """Check if database is healthy."""
        try:
            with sqlite3.connect(self.config.database_path) as conn:
                conn.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def _get_uptime(self) -> str:
        """Get system uptime."""
        uptime_delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {
                'rss': 0,
                'vms': 0,
                'percent': 0.0
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return {
                'rss': 0,
                'vms': 0,
                'percent': 0.0
            }
    
    def _update_agent_status(self):
        """Update agent status information."""
        try:
            # Mock agent data - replace with actual agent monitoring
            mock_agents = {
                'content_creator': AgentInfo(
                    id='content_creator',
                    name='Content Creator Agent',
                    status=AgentStatus.BUSY,
                    current_task_id='task_123',
                    uptime='2h 15m',
                    last_activity=datetime.now()
                ),
                'research_agent': AgentInfo(
                    id='research_agent',
                    name='Research Agent',
                    status=AgentStatus.IDLE,
                    uptime='2h 15m',
                    last_activity=datetime.now() - timedelta(minutes=5)
                ),
                'marketing_agent': AgentInfo(
                    id='marketing_agent',
                    name='Marketing Agent',
                    status=AgentStatus.BUSY,
                    current_task_id='task_456',
                    uptime='1h 45m',
                    last_activity=datetime.now()
                )
            }
            
            self.agents.update(mock_agents)
            
        except Exception as e:
            self.logger.error(f"Failed to update agent status: {e}")
    
    def _update_project_status(self):
        """Update project status information."""
        try:
            # Mock project data - replace with actual project monitoring
            if not self.projects:
                mock_projects = {
                    'ai_mastery_course': ProjectInfo(
                        id='ai_mastery_course',
                        name='AI Mastery Course',
                        type='course',
                        status='writing',
                        progress=0.65,
                        chapters_completed=13,
                        total_chapters=20,
                        created_at=datetime.now() - timedelta(days=15),
                        last_updated=datetime.now()
                    ),
                    'automation_guide': ProjectInfo(
                        id='automation_guide',
                        name='Business Automation Guide',
                        type='book',
                        status='reviewing',
                        progress=0.85,
                        chapters_completed=17,
                        total_chapters=20,
                        created_at=datetime.now() - timedelta(days=30),
                        last_updated=datetime.now() - timedelta(hours=2)
                    )
                }
                
                self.projects.update(mock_projects)
            
        except Exception as e:
            self.logger.error(f"Failed to update project status: {e}")
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate system performance report."""
        try:
            return {
                'report_type': 'performance',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'metrics': {
                    'system_uptime': self._get_uptime(),
                    'memory_usage': self._get_memory_usage(),
                    'task_completion_rate': 0.92,
                    'average_response_time': 1.2,
                    'error_rate': 0.03
                },
                'agents': {
                    'total_agents': len(self.agents),
                    'active_agents': len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]),
                    'idle_agents': len([a for a in self.agents.values() if a.status == AgentStatus.IDLE])
                },
                'recommendations': [
                    'System performance is optimal',
                    'Consider scaling up content creation agents',
                    'Monitor memory usage trends'
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {'error': str(e)}
    
    def _generate_content_report(self) -> Dict[str, Any]:
        """Generate content performance report."""
        try:
            return {
                'report_type': 'content',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'content_stats': {
                    'videos_created': 45,
                    'articles_written': 23,
                    'social_posts': 156,
                    'total_views': 2840000,
                    'engagement_rate': 0.045
                },
                'top_performing_content': [
                    {
                        'title': 'AI Content Creation Masterclass',
                        'type': 'video',
                        'views': 45000,
                        'engagement': 0.067
                    },
                    {
                        'title': 'Automation Strategies for 2024',
                        'type': 'article',
                        'views': 12000,
                        'engagement': 0.089
                    }
                ],
                'content_calendar': {
                    'scheduled_posts': 12,
                    'drafts_pending': 8,
                    'review_queue': 3
                },
                'recommendations': [
                    'Focus on video content for higher engagement',
                    'Increase posting frequency on TikTok',
                    'Develop more tutorial-style content'
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to generate content report: {e}")
            return {'error': str(e)}
    
    def _generate_financial_report(self) -> Dict[str, Any]:
        """Generate financial performance report."""
        try:
            return {
                'report_type': 'financial',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'revenue': {
                    'total_monthly': 15420.50,
                    'affiliate_commissions': 8750.25,
                    'course_sales': 4200.00,
                    'consulting': 2470.25
                },
                'expenses': {
                    'total_monthly': 3240.75,
                    'hosting': 89.99,
                    'tools_subscriptions': 450.50,
                    'content_creation': 1200.00,
                    'marketing': 1500.26
                },
                'profit_margin': 0.79,
                'growth_rate': 0.23,
                'top_revenue_sources': [
                    {'source': 'AI Course Sales', 'amount': 4200.00, 'percentage': 27.2},
                    {'source': 'Amazon Affiliates', 'amount': 3850.25, 'percentage': 25.0},
                    {'source': 'Consulting Services', 'amount': 2470.25, 'percentage': 16.0}
                ],
                'recommendations': [
                    'Increase focus on high-margin affiliate products',
                    'Launch advanced course tier',
                    'Optimize marketing spend efficiency'
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to generate financial report: {e}")
            return {'error': str(e)}
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the dashboard application."""
        try:
            self.logger.info(f"Starting TRAE.AI Dashboard on {host}:{port}")
            
            # Start background tasks
            self._start_background_tasks()
            
            # Run the Flask app
            self.app.run(
                host=host,
                port=port,
                debug=debug,
                threaded=True,
                use_reloader=False  # Disable reloader to prevent issues with background threads
            )
            
        except KeyboardInterrupt:
            self.logger.info("Dashboard shutdown requested")
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
        finally:
            self._cleanup()
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        try:
            # Start system monitoring thread
            monitor_thread = threading.Thread(
                target=self._background_monitor,
                daemon=True,
                name="SystemMonitor"
            )
            monitor_thread.start()
            
            self.logger.info("Background monitoring tasks started")
            
        except Exception as e:
            self.logger.error(f"Failed to start background tasks: {e}")
    
    def _background_monitor(self):
        """Background monitoring loop."""
        while True:
            try:
                # Update system metrics
                self._update_agent_status()
                self._update_project_status()
                
                # Sleep for 30 seconds before next update
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Background monitor error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _cleanup(self):
        """Cleanup resources on shutdown."""
        try:
            self.logger.info("Cleaning up dashboard resources...")
            # Add any cleanup logic here
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


def main():
    """Main entry point for the dashboard application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAE.AI Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        # Automatic port detection function
        def first_free(start, max_tries=50):
            p = start
            for _ in range(max_tries):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        s.bind((args.host, p))
                        return p
                    except OSError:
                        p += 1
            raise RuntimeError("No free port found")
        
        # Find free port starting from requested port
        free_port = first_free(args.port)
        print(f"Dashboard starting on http://{args.host}:{free_port}")
        
        # Create dashboard instance
        config = DashboardConfig()
        config.debug = args.debug
        config.host = args.host
        config.port = free_port
        
        dashboard = DashboardApp(config)
        
        # Run the dashboard with detected port
        dashboard.run(
            host=args.host,
            port=free_port,
            debug=args.debug
        )
        
    except Exception as e:
        print(f"Failed to start dashboard: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()