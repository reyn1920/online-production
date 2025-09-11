#!/usr/bin/env python3
"""
TRAE.AI Task Queue System - Database-Backed Resilient Operations Management

A robust, database-backed task queue system designed for resilience and
autonomous operation. Provides task scheduling, priority management,
retry logic, and failure recovery for the TRAE.AI agent ecosystem.

Key Features:
- SQLite-based persistence for reliability
- Priority-based task scheduling
- Automatic retry with exponential backoff
- Dead letter queue for failed tasks
- Task dependencies and workflows
- Real-time monitoring and metrics
- Agent coordination and load balancing
"""

import hashlib
import json
import logging
import queue
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Task status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class TaskPriority(Enum):
    """Task priority levels"""

    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Task:
    """Task definition"""

    task_id: str
    task_type: str
    agent_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    dependencies: List[str]
    max_retries: int
    retry_count: int
    status: TaskStatus
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskMetrics:
    """Task execution metrics"""

    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    dead_letter_tasks: int
    average_execution_time: float
    success_rate: float
    throughput_per_hour: float


@dataclass
class AgentWorker:
    """Agent worker definition"""

    worker_id: str
    agent_type: str
    status: str  # 'active', 'idle', 'busy', 'offline'
    current_task_id: Optional[str]
    tasks_completed: int
    last_heartbeat: datetime
    capabilities: List[str]
    max_concurrent_tasks: int
    current_load: int


class TaskQueue:
    """Database-backed resilient task queue system"""

    def __init__(self, db_path: str = "data/right_perspective.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_database()

        # Queue management
        self.running = False
        self.scheduler_thread = None
        self.worker_threads = {}
        self.agent_registry = {}

        # Configuration
        self.max_workers_per_agent = 3
        self.heartbeat_timeout = 300  # 5 minutes
        self.retry_delays = [30, 120, 300, 900, 1800]  # Exponential backoff
        self.cleanup_interval = 3600  # 1 hour

        # Metrics
        self.metrics_cache = {}
        self.last_metrics_update = datetime.now()

        # Task handlers registry
        self.task_handlers: Dict[str, Callable] = {}

        # Internal queues for different priorities
        self.priority_queues = {
            TaskPriority.URGENT: queue.PriorityQueue(),
            TaskPriority.HIGH: queue.PriorityQueue(),
            TaskPriority.MEDIUM: queue.PriorityQueue(),
            TaskPriority.LOW: queue.PriorityQueue(),
        }

    def initialize_database(self):
        """Initialize task queue database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    max_retries INTEGER NOT NULL,
                    retry_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    scheduled_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result TEXT,
                    metadata TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_workers (
                    worker_id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_task_id TEXT,
                    tasks_completed INTEGER NOT NULL,
                    last_heartbeat TIMESTAMP NOT NULL,
                    capabilities TEXT NOT NULL,
                    max_concurrent_tasks INTEGER NOT NULL,
                    current_load INTEGER NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    dependency_id TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                    FOREIGN KEY (dependency_id) REFERENCES tasks (task_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """
            )

            # Create indexes for performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_agent_type ON tasks (agent_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_at ON tasks (scheduled_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workers_agent_type ON agent_workers (agent_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workers_status ON agent_workers (status)"
            )

    def start(self):
        """Start the task queue system"""
        if self.running:
            return

        self.running = True

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # Start metrics thread
        self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
        self.metrics_thread.start()

        self.logger.info("Task queue system started")

    def stop(self):
        """Stop the task queue system"""
        self.running = False

        # Stop all worker threads
        for worker_thread in self.worker_threads.values():
            if worker_thread.is_alive():
                worker_thread.join(timeout=5)

        self.logger.info("Task queue system stopped")

    def submit_task(
        self,
        task_type: str,
        agent_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: List[str] = None,
        max_retries: int = 3,
        scheduled_at: datetime = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Submit a new task to the queue"""

        task_id = str(uuid.uuid4())

        if dependencies is None:
            dependencies = []

        if scheduled_at is None:
            scheduled_at = datetime.now()

        if metadata is None:
            metadata = {}

        task = Task(
            task_id=task_id,
            task_type=task_type,
            agent_type=agent_type,
            priority=priority,
            payload=payload,
            dependencies=dependencies,
            max_retries=max_retries,
            retry_count=0,
            status=TaskStatus.PENDING,
            scheduled_at=scheduled_at,
            started_at=None,
            completed_at=None,
            error_message=None,
            result=None,
            metadata=metadata,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._save_task(task)

        # Add to appropriate priority queue if ready to run
        if self._are_dependencies_satisfied(task_id):
            self.priority_queues[priority].put((scheduled_at.timestamp(), task_id))

        self.logger.info(f"Task submitted: {task_id} ({task_type})")
        return task_id

    def submit_workflow(self, workflow_definition: Dict[str, Any]) -> List[str]:
        """Submit a workflow (multiple dependent tasks)"""
        task_ids = []
        task_map = {}

        # First pass: create all tasks
        for step in workflow_definition["steps"]:
            task_id = self.submit_task(
                task_type=step["task_type"],
                agent_type=step["agent_type"],
                payload=step["payload"],
                priority=TaskPriority(step.get("priority", TaskPriority.MEDIUM.value)),
                max_retries=step.get("max_retries", 3),
                metadata=step.get("metadata", {}),
            )
            task_ids.append(task_id)
            task_map[step["step_id"]] = task_id

        # Second pass: set up dependencies
        for i, step in enumerate(workflow_definition["steps"]):
            if "depends_on" in step:
                dependencies = [task_map[dep] for dep in step["depends_on"]]
                self._update_task_dependencies(task_ids[i], dependencies)

        self.logger.info(f"Workflow submitted: {len(task_ids)} tasks")
        return task_ids

    def register_agent(
        self,
        agent_type: str,
        agent_instance: Any,
        capabilities: List[str] = None,
        max_concurrent_tasks: int = 1,
    ) -> str:
        """Register an agent worker"""
        worker_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"

        if capabilities is None:
            capabilities = []

        worker = AgentWorker(
            worker_id=worker_id,
            agent_type=agent_type,
            status="active",
            current_task_id=None,
            tasks_completed=0,
            last_heartbeat=datetime.now(),
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            current_load=0,
        )

        self.agent_registry[worker_id] = {"worker": worker, "instance": agent_instance}

        self._save_agent_worker(worker)

        # Start worker thread
        worker_thread = threading.Thread(
            target=self._worker_loop, args=(worker_id,), daemon=True
        )
        worker_thread.start()
        self.worker_threads[worker_id] = worker_thread

        self.logger.info(f"Agent registered: {worker_id} ({agent_type})")
        return worker_id

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a task handler function"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"Task handler registered: {task_type}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and details"""
        task = self._get_task(task_id)
        if task:
            return {
                "task_id": task["task_id"],
                "status": task["status"],
                "progress": self._calculate_task_progress(task),
                "created_at": task["created_at"],
                "started_at": task["started_at"],
                "completed_at": task["completed_at"],
                "error_message": task["error_message"],
                "retry_count": task["retry_count"],
                "max_retries": task["max_retries"],
            }
        return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        task = self._get_task(task_id)
        if not task:
            return False

        if task["status"] in [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]:
            self._update_task_status(task_id, TaskStatus.CANCELLED)
            self.logger.info(f"Task cancelled: {task_id}")
            return True

        return False

    def get_queue_metrics(self) -> TaskMetrics:
        """Get current queue metrics"""
        # Update metrics if cache is stale
        if datetime.now() - self.last_metrics_update > timedelta(minutes=1):
            self._update_metrics_cache()

        return TaskMetrics(**self.metrics_cache)

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        status = {}

        for worker_id, agent_data in self.agent_registry.items():
            worker = agent_data["worker"]
            status[worker_id] = {
                "agent_type": worker.agent_type,
                "status": worker.status,
                "current_task_id": worker.current_task_id,
                "tasks_completed": worker.tasks_completed,
                "current_load": worker.current_load,
                "max_concurrent_tasks": worker.max_concurrent_tasks,
                "last_heartbeat": worker.last_heartbeat.isoformat(),
                "capabilities": worker.capabilities,
            }

        return status

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Process tasks from priority queues
                for priority in TaskPriority:
                    if not self.priority_queues[priority].empty():
                        try:
                            scheduled_time, task_id = self.priority_queues[
                                priority
                            ].get_nowait()

                            # Check if it's time to run the task
                            if datetime.fromtimestamp(scheduled_time) <= datetime.now():
                                self._schedule_task_for_execution(task_id)
                            else:
                                # Put it back if not ready
                                self.priority_queues[priority].put(
                                    (scheduled_time, task_id)
                                )

                        except queue.Empty:
                            continue

                # Check for tasks that need to be retried
                self._check_retry_tasks()

                # Check for stuck tasks
                self._check_stuck_tasks()

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)

    def _worker_loop(self, worker_id: str):
        """Worker loop for processing tasks"""
        while self.running and worker_id in self.agent_registry:
            try:
                worker_data = self.agent_registry[worker_id]
                worker = worker_data["worker"]
                agent_instance = worker_data["instance"]

                # Update heartbeat
                worker.last_heartbeat = datetime.now()
                self._update_agent_heartbeat(worker_id)

                # Check if worker can take more tasks
                if worker.current_load >= worker.max_concurrent_tasks:
                    time.sleep(2)
                    continue

                # Get next task for this agent type
                task_id = self._get_next_task_for_agent(worker.agent_type)

                if task_id:
                    self._execute_task(task_id, worker_id, agent_instance)
                else:
                    # No tasks available, wait
                    worker.status = "idle"
                    time.sleep(5)

            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(10)

    def _execute_task(self, task_id: str, worker_id: str, agent_instance: Any):
        """Execute a single task"""
        try:
            # Update task and worker status
            self._update_task_status(task_id, TaskStatus.RUNNING)
            self._log_task_execution(task_id, worker_id, "started")

            worker_data = self.agent_registry[worker_id]
            worker = worker_data["worker"]
            worker.status = "busy"
            worker.current_task_id = task_id
            worker.current_load += 1

            # Get task details
            task = self._get_task(task_id)
            if not task:
                raise Exception(f"Task not found: {task_id}")

            # Execute task
            start_time = datetime.now()

            # Try registered handler first
            if task["task_type"] in self.task_handlers:
                handler = self.task_handlers[task["task_type"]]
                result = handler(json.loads(task["payload"]))
            else:
                # Use agent's execute_task method
                result = agent_instance.execute_task(json.loads(task["payload"]))

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Update task with result
            self._update_task_completion(task_id, result, execution_time)
            self._log_task_execution(
                task_id, worker_id, "completed", {"execution_time": execution_time}
            )

            # Update worker
            worker.status = "active"
            worker.current_task_id = None
            worker.current_load -= 1
            worker.tasks_completed += 1

            self.logger.info(f"Task completed: {task_id} in {execution_time:.2f}s")

        except Exception as e:
            # Handle task failure
            self._handle_task_failure(task_id, worker_id, str(e))

    def _handle_task_failure(self, task_id: str, worker_id: str, error_message: str):
        """Handle task execution failure"""
        task = self._get_task(task_id)
        if not task:
            return

        retry_count = task["retry_count"] + 1

        if retry_count <= task["max_retries"]:
            # Schedule for retry with exponential backoff
            delay_index = min(retry_count - 1, len(self.retry_delays) - 1)
            retry_delay = self.retry_delays[delay_index]
            retry_time = datetime.now() + timedelta(seconds=retry_delay)

            self._update_task_retry(task_id, retry_count, error_message, retry_time)
            self._log_task_execution(
                task_id,
                worker_id,
                "failed_retry_scheduled",
                {"error": error_message, "retry_delay": retry_delay},
            )

            self.logger.warning(
                f"Task failed, scheduling retry {retry_count}/{task['max_retries']}: {task_id}"
            )
        else:
            # Move to dead letter queue
            self._update_task_status(task_id, TaskStatus.DEAD_LETTER)
            self._log_task_execution(
                task_id, worker_id, "moved_to_dead_letter", {"error": error_message}
            )

            self.logger.error(f"Task moved to dead letter queue: {task_id}")

        # Update worker
        if worker_id in self.agent_registry:
            worker = self.agent_registry[worker_id]["worker"]
            worker.status = "active"
            worker.current_task_id = None
            worker.current_load -= 1

    def _cleanup_loop(self):
        """Cleanup loop for maintenance tasks"""
        while self.running:
            try:
                # Clean up old completed tasks
                cutoff_date = datetime.now() - timedelta(days=7)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        DELETE FROM tasks 
                        WHERE status = 'completed' AND completed_at < ?
                    """,
                        (cutoff_date.isoformat(),),
                    )

                # Clean up old execution logs
                log_cutoff_date = datetime.now() - timedelta(days=30)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        DELETE FROM task_execution_log 
                        WHERE timestamp < ?
                    """,
                        (log_cutoff_date.isoformat(),),
                    )

                # Remove offline workers
                timeout_cutoff = datetime.now() - timedelta(
                    seconds=self.heartbeat_timeout
                )
                offline_workers = []

                for worker_id, agent_data in self.agent_registry.items():
                    if agent_data["worker"].last_heartbeat < timeout_cutoff:
                        offline_workers.append(worker_id)

                for worker_id in offline_workers:
                    self._remove_offline_worker(worker_id)

                time.sleep(self.cleanup_interval)

            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                time.sleep(300)

    def _metrics_loop(self):
        """Metrics update loop"""
        while self.running:
            try:
                self._update_metrics_cache()
                time.sleep(60)  # Update every minute
            except Exception as e:
                self.logger.error(f"Metrics update error: {e}")
                time.sleep(60)

    # Database helper methods
    def _save_task(self, task: Task):
        """Save task to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks
                (task_id, task_type, agent_type, priority, payload, dependencies,
                 max_retries, retry_count, status, scheduled_at, started_at,
                 completed_at, error_message, result, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.task_id,
                    task.task_type,
                    task.agent_type,
                    task.priority.value,
                    json.dumps(task.payload),
                    json.dumps(task.dependencies),
                    task.max_retries,
                    task.retry_count,
                    task.status.value,
                    task.scheduled_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.error_message,
                    json.dumps(task.result) if task.result else None,
                    json.dumps(task.metadata),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )

    def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    def _update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tasks 
                SET status = ?, updated_at = ?
                WHERE task_id = ?
            """,
                (status.value, datetime.now().isoformat(), task_id),
            )

    def _update_task_completion(
        self, task_id: str, result: Dict[str, Any], execution_time: float
    ):
        """Update task with completion data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tasks 
                SET status = 'completed', completed_at = ?, result = ?, updated_at = ?
                WHERE task_id = ?
            """,
                (
                    datetime.now().isoformat(),
                    json.dumps(result),
                    datetime.now().isoformat(),
                    task_id,
                ),
            )

    def _update_task_retry(
        self, task_id: str, retry_count: int, error_message: str, retry_time: datetime
    ):
        """Update task for retry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tasks 
                SET status = 'retrying', retry_count = ?, error_message = ?, 
                    scheduled_at = ?, updated_at = ?
                WHERE task_id = ?
            """,
                (
                    retry_count,
                    error_message,
                    retry_time.isoformat(),
                    datetime.now().isoformat(),
                    task_id,
                ),
            )

    def _save_agent_worker(self, worker: AgentWorker):
        """Save agent worker to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_workers
                (worker_id, agent_type, status, current_task_id, tasks_completed,
                 last_heartbeat, capabilities, max_concurrent_tasks, current_load)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    worker.worker_id,
                    worker.agent_type,
                    worker.status,
                    worker.current_task_id,
                    worker.tasks_completed,
                    worker.last_heartbeat.isoformat(),
                    json.dumps(worker.capabilities),
                    worker.max_concurrent_tasks,
                    worker.current_load,
                ),
            )

    def _log_task_execution(
        self, task_id: str, worker_id: str, action: str, details: Dict[str, Any] = None
    ):
        """Log task execution event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO task_execution_log
                (task_id, worker_id, action, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    worker_id,
                    action,
                    json.dumps(details) if details else None,
                    datetime.now().isoformat(),
                ),
            )

    def _are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if task dependencies are satisfied"""
        task = self._get_task(task_id)
        if not task:
            return False

        dependencies = json.loads(task["dependencies"])
        if not dependencies:
            return True

        with sqlite3.connect(self.db_path) as conn:
            for dep_id in dependencies:
                cursor = conn.execute(
                    "SELECT status FROM tasks WHERE task_id = ?", (dep_id,)
                )
                row = cursor.fetchone()
                if not row or row[0] != "completed":
                    return False

        return True

    def _get_next_task_for_agent(self, agent_type: str) -> Optional[str]:
        """Get next available task for agent type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT task_id FROM tasks 
                WHERE agent_type = ? AND status = 'pending' 
                AND scheduled_at <= ?
                ORDER BY priority ASC, scheduled_at ASC
                LIMIT 1
            """,
                (agent_type, datetime.now().isoformat()),
            )

            row = cursor.fetchone()
            if row:
                task_id = row[0]
                # Check dependencies
                if self._are_dependencies_satisfied(task_id):
                    return task_id

        return None

    def _schedule_task_for_execution(self, task_id: str):
        """Schedule task for execution by updating its status"""
        if self._are_dependencies_satisfied(task_id):
            self._update_task_status(task_id, TaskStatus.PENDING)

    def _check_retry_tasks(self):
        """Check for tasks that need to be retried"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT task_id FROM tasks 
                WHERE status = 'retrying' AND scheduled_at <= ?
            """,
                (datetime.now().isoformat(),),
            )

            for row in cursor.fetchall():
                task_id = row[0]
                self._update_task_status(task_id, TaskStatus.PENDING)

    def _check_stuck_tasks(self):
        """Check for tasks that appear to be stuck"""
        stuck_timeout = datetime.now() - timedelta(hours=1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT task_id FROM tasks 
                WHERE status = 'running' AND started_at < ?
            """,
                (stuck_timeout.isoformat(),),
            )

            for row in cursor.fetchall():
                task_id = row[0]
                self.logger.warning(f"Detected stuck task: {task_id}")
                self._handle_task_failure(
                    task_id, "system", "Task timeout - marked as stuck"
                )

    def _update_metrics_cache(self):
        """Update metrics cache"""
        with sqlite3.connect(self.db_path) as conn:
            # Get task counts by status
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) FROM tasks 
                GROUP BY status
            """
            )

            status_counts = dict(cursor.fetchall())

            total_tasks = sum(status_counts.values())
            completed_tasks = status_counts.get("completed", 0)

            # Calculate success rate
            success_rate = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            # Calculate average execution time
            cursor = conn.execute(
                """
                SELECT AVG(julianday(completed_at) - julianday(started_at)) * 86400
                FROM tasks 
                WHERE status = 'completed' AND started_at IS NOT NULL
            """
            )

            avg_execution_time = cursor.fetchone()[0] or 0

            # Calculate throughput (tasks per hour in last 24 hours)
            last_24h = datetime.now() - timedelta(hours=24)
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM tasks 
                WHERE status = 'completed' AND completed_at > ?
            """,
                (last_24h.isoformat(),),
            )

            completed_last_24h = cursor.fetchone()[0]
            throughput_per_hour = completed_last_24h / 24

            self.metrics_cache = {
                "total_tasks": total_tasks,
                "pending_tasks": status_counts.get("pending", 0),
                "running_tasks": status_counts.get("running", 0),
                "completed_tasks": completed_tasks,
                "failed_tasks": status_counts.get("failed", 0),
                "dead_letter_tasks": status_counts.get("dead_letter", 0),
                "average_execution_time": avg_execution_time,
                "success_rate": success_rate,
                "throughput_per_hour": throughput_per_hour,
            }

            self.last_metrics_update = datetime.now()

    def _calculate_task_progress(self, task: Dict[str, Any]) -> float:
        """Calculate task progress percentage"""
        status = task["status"]

        if status == "pending":
            return 0.0
        elif status == "running":
            return 50.0
        elif status == "completed":
            return 100.0
        elif status in ["failed", "cancelled", "dead_letter"]:
            return 0.0
        elif status == "retrying":
            return 25.0

        return 0.0

    def _update_task_dependencies(self, task_id: str, dependencies: List[str]):
        """Update task dependencies"""
        with sqlite3.connect(self.db_path) as conn:
            # Update task record
            conn.execute(
                """
                UPDATE tasks SET dependencies = ?, updated_at = ?
                WHERE task_id = ?
            """,
                (json.dumps(dependencies), datetime.now().isoformat(), task_id),
            )

            # Add dependency records
            for dep_id in dependencies:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO task_dependencies
                    (task_id, dependency_id, created_at)
                    VALUES (?, ?, ?)
                """,
                    (task_id, dep_id, datetime.now().isoformat()),
                )

    def _update_agent_heartbeat(self, worker_id: str):
        """Update agent heartbeat"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE agent_workers 
                SET last_heartbeat = ?
                WHERE worker_id = ?
            """,
                (datetime.now().isoformat(), worker_id),
            )

    def _remove_offline_worker(self, worker_id: str):
        """Remove offline worker"""
        if worker_id in self.agent_registry:
            del self.agent_registry[worker_id]

        if worker_id in self.worker_threads:
            del self.worker_threads[worker_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM agent_workers WHERE worker_id = ?", (worker_id,))

        self.logger.info(f"Removed offline worker: {worker_id}")


if __name__ == "__main__":
    # Test the Task Queue
    task_queue = TaskQueue()
    task_queue.start()

    # Register a simple task handler
    def test_handler(payload):
        print(f"Processing task: {payload}")
        time.sleep(2)
        return {"success": True, "processed": payload}

    task_queue.register_task_handler("test_task", test_handler)

    # Submit some test tasks
    task_ids = []
    for i in range(5):
        task_id = task_queue.submit_task(
            task_type="test_task",
            agent_type="TestAgent",
            payload={"data": f"test_data_{i}"},
            priority=TaskPriority.MEDIUM,
        )
        task_ids.append(task_id)

    # Submit a workflow
    workflow = {
        "steps": [
            {
                "step_id": "step1",
                "task_type": "test_task",
                "agent_type": "TestAgent",
                "payload": {"data": "workflow_step_1"},
                "priority": TaskPriority.HIGH.value,
            },
            {
                "step_id": "step2",
                "task_type": "test_task",
                "agent_type": "TestAgent",
                "payload": {"data": "workflow_step_2"},
                "depends_on": ["step1"],
            },
        ]
    }

    workflow_task_ids = task_queue.submit_workflow(workflow)

    # Monitor for a bit
    try:
        for _ in range(30):
            metrics = task_queue.get_queue_metrics()
            print(
                f"Queue metrics: {metrics.pending_tasks} pending, {metrics.completed_tasks} completed"
            )
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        task_queue.stop()
