#!/usr / bin / env python3
"""
TRAE.AI n8n Workflow Orchestration Integration

Provides seamless integration between n8n workflow automation platform
and the TRAE.AI agent ecosystem for visual workflow design and execution.

Features:
- n8n API client for workflow management
- Visual workflow to agent task translation
- Real - time workflow execution monitoring
- Webhook integration for external triggers
- Credential management and security
- Workflow templates and versioning

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore


class WorkflowStatus(Enum):
    """n8n workflow execution status."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"
    CANCELED = "canceled"


class NodeType(Enum):
    """n8n node types mapped to TRAE.AI agents."""

    TRIGGER = "trigger"
    RESEARCH = "research"
    CONTENT = "content"
    MARKETING = "marketing"
    SYSTEM = "system"
    QA = "qa"
    WEBHOOK = "webhook"
    HTTP_REQUEST = "http_request"
    CODE = "code"
    IF = "if"
    MERGE = "merge"
    WAIT = "wait"


@dataclass
class WorkflowExecution:
    """Represents an n8n workflow execution."""

    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    mode: str = "trigger"
    retry_of: Optional[str] = None
    retry_count: int = 0


@dataclass
class WorkflowNode:
    """Represents an n8n workflow node."""

    id: str
    name: str
    type: str
    type_version: float
    position: List[float]
    parameters: Dict[str, Any]
    credentials: Optional[Dict[str, str]] = None
    webhook_id: Optional[str] = None
    disabled: bool = False


@dataclass
class WorkflowConnection:
    """Represents connections between workflow nodes."""

    source_node: str
    source_output: str
    target_node: str
    target_input: str


@dataclass
class N8nWorkflow:
    """Represents a complete n8n workflow."""

    id: str
    name: str
    active: bool
    nodes: List[WorkflowNode]
    connections: List[WorkflowConnection]
    created_at: datetime
    updated_at: datetime
    tags: List[str] = None
    settings: Optional[Dict[str, Any]] = None
    static_data: Optional[Dict[str, Any]] = None


class N8nIntegration:
    """
    Comprehensive n8n workflow orchestration integration with
    TRAE.AI agent system bridge and visual workflow management.
    """

    def __init__(
        self,
        n8n_base_url: str = "http://localhost:5678",
        secrets_db_path: str = "data / secrets.sqlite",
    ):
        self.logger = setup_logger("n8n_integration")
        self.secret_store = SecretStore(secrets_db_path)
        self.base_url = n8n_base_url.rstrip("/")

        # Load credentials
        self.credentials = self._load_credentials()

        # Initialize database
        self.db_path = "data / n8n_workflows.sqlite"
        self._init_database()

        # Configure HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set authentication headers
        if self.credentials.get("api_key"):
            self.session.headers.update({"X - N8N - API - KEY": self.credentials["api_key"]})

        # Workflow cache
        self.workflows_cache = {}
        self.executions_cache = {}

        # Agent type mapping
        self.agent_type_mapping = {
            "research": "ResearchAgent",
            "content": "ContentAgent",
            "marketing": "MarketingAgent",
            "system": "SystemAgent",
            "qa": "QAAgent",
            "planner": "PlannerAgent",
        }

        self.logger.info("n8n integration initialized successfully")

    def _load_credentials(self) -> Dict[str, str]:
        """Load n8n API credentials from secure storage."""
        try:
            with self.secret_store as store:
                credentials = {
                    "api_key": store.get_secret("N8N_API_KEY"),
                    "webhook_url": store.get_secret("N8N_WEBHOOK_URL"),
                    "username": store.get_secret("N8N_USERNAME"),
                    "password": store.get_secret("N8N_PASSWORD"),
                }

                missing_creds = [
                    k
                    for k, v in credentials.items()
                    if not v and k != "username" and k != "password"
                ]
                if missing_creds:
                    self.logger.warning(f"Missing n8n credentials: {missing_creds}")

                return credentials

        except Exception as e:
            self.logger.error(f"Failed to load n8n credentials: {e}")
            return {}

    def _init_database(self):
        """Initialize n8n workflow tracking database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Workflows table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        active BOOLEAN DEFAULT FALSE,
                        nodes TEXT,
                        connections TEXT,
                        settings TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        tags TEXT,
                        agent_mapping TEXT
                )
            """
            )

            # Executions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                        workflow_id TEXT,
                        status TEXT,
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        data TEXT,
                        error TEXT,
                        mode TEXT DEFAULT 'trigger',
                        retry_count INTEGER DEFAULT 0,
                        FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                )
            """
            )

            # Agent tasks mapping table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_task_mapping (
                    id TEXT PRIMARY KEY,
                        execution_id TEXT,
                        node_id TEXT,
                        agent_type TEXT,
                        task_id TEXT,
                        status TEXT,
                        created_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        result TEXT,
                        FOREIGN KEY (execution_id) REFERENCES executions (id)
                )
            """
            )

            conn.commit()

    async def health_check(self) -> Dict[str, Any]:
        """Check n8n instance health and connectivity."""
        try:
            response = self.session.get(f"{self.base_url}/healthz", timeout=10)

            if response.status_code == 200:
                # Get additional info
                info_response = self.session.get(f"{self.base_url}/rest / login", timeout=5)

                return {
                    "status": "healthy",
                    "url": self.base_url,
                    "response_time": response.elapsed.total_seconds(),
                    "version": response.headers.get("X - N8N - Version", "unknown"),
                    "authenticated": bool(self.credentials.get("api_key")),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"n8n health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_workflows(self, active_only: bool = False) -> List[N8nWorkflow]:
        """Retrieve all workflows from n8n instance."""
        try:
            params = {"active": "true"} if active_only else {}
            response = self.session.get(
                f"{self.base_url}/rest / workflows", params=params, timeout=30
            )

            if response.status_code == 200:
                workflows_data = response.json()
                workflows = []

                for workflow_data in workflows_data:
                    workflow = self._parse_workflow(workflow_data)
                    workflows.append(workflow)

                    # Cache workflow
                    self.workflows_cache[workflow.id] = workflow

                    # Store in database
                    await self._store_workflow(workflow)

                self.logger.info(f"Retrieved {len(workflows)} workflows from n8n")
                return workflows
            else:
                self.logger.error(f"Failed to get workflows: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error retrieving workflows: {e}")
            return []

    async def get_workflow(self, workflow_id: str) -> Optional[N8nWorkflow]:
        """Retrieve a specific workflow by ID."""
        try:
            # Check cache first
            if workflow_id in self.workflows_cache:
                return self.workflows_cache[workflow_id]

            response = self.session.get(
                f"{self.base_url}/rest / workflows/{workflow_id}", timeout=15
            )

            if response.status_code == 200:
                workflow_data = response.json()
                workflow = self._parse_workflow(workflow_data)

                # Cache workflow
                self.workflows_cache[workflow_id] = workflow

                # Store in database
                await self._store_workflow(workflow)

                return workflow
            else:
                self.logger.error(
                    f"Failed to get workflow {workflow_id}: HTTP {response.status_code}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error retrieving workflow {workflow_id}: {e}")
            return None

    async def execute_workflow(
        self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecution]:
        """Execute a workflow with optional input data."""
        try:
            payload = {}
            if input_data:
                payload["data"] = input_data

            response = self.session.post(
                f"{self.base_url}/rest / workflows/{workflow_id}/execute",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                execution_data = response.json()
                execution = self._parse_execution(execution_data)

                # Cache execution
                self.executions_cache[execution.id] = execution

                # Store in database
                await self._store_execution(execution)

                # Start monitoring execution
                asyncio.create_task(self._monitor_execution(execution.id))

                self.logger.info(f"Started workflow execution {execution.id}")
                return execution
            else:
                self.logger.error(f"Failed to execute workflow: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error executing workflow {workflow_id}: {e}")
            return None

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status and results."""
        try:
            # Check cache first
            if execution_id in self.executions_cache:
                cached_execution = self.executions_cache[execution_id]
                if cached_execution.status in [
                    WorkflowStatus.SUCCESS,
                    WorkflowStatus.ERROR,
                    WorkflowStatus.CANCELED,
                ]:
                    return cached_execution

            response = self.session.get(
                f"{self.base_url}/rest / executions/{execution_id}", timeout=15
            )

            if response.status_code == 200:
                execution_data = response.json()
                execution = self._parse_execution(execution_data)

                # Update cache
                self.executions_cache[execution_id] = execution

                # Update database
                await self._store_execution(execution)

                return execution
            else:
                self.logger.error(
                    f"Failed to get execution {execution_id}: HTTP {response.status_code}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error retrieving execution {execution_id}: {e}")
            return None

    async def create_webhook_workflow(
        self, name: str, webhook_path: str, agent_tasks: List[Dict[str, Any]]
    ) -> Optional[N8nWorkflow]:
        """Create a new webhook - triggered workflow with agent tasks."""
        try:
            # Build workflow nodes
            nodes = []
            connections = []

            # Webhook trigger node
            webhook_node = {
                "id": str(uuid.uuid4()),
                "name": "Webhook",
                "type": "n8n - nodes - base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "path": webhook_path,
                    "httpMethod": "POST",
                    "responseMode": "onReceived",
                },
                "webhookId": str(uuid.uuid4()),
            }
            nodes.append(webhook_node)

            # Create agent task nodes
            prev_node_id = webhook_node["id"]
            x_pos = 450

            for i, task in enumerate(agent_tasks):
                task_node = {
                    "id": str(uuid.uuid4()),
                    "name": f"Agent Task {i + 1}",
                    "type": "n8n - nodes - base.httpRequest",
                    "typeVersion": 1,
                    "position": [x_pos, 300],
                    "parameters": {
                        "url": f"http://localhost:8000 / api / agents/{task['agent_type']}/execute",
                        "method": "POST",
                        "jsonParameters": True,
                        "options": {},
                        "bodyParametersJson": json.dumps(task.get("parameters", {})),
                    },
                }
                nodes.append(task_node)

                # Add connection from previous node
                connections.append(
                    {
                        "source_node": prev_node_id,
                        "source_output": "main",
                        "target_node": task_node["id"],
                        "target_input": "main",
                    }
                )

                prev_node_id = task_node["id"]
                x_pos += 200

            # Create workflow payload
            workflow_payload = {
                "name": name,
                "active": True,
                "nodes": nodes,
                "connections": self._format_connections(connections),
                "settings": {"executionOrder": "v1"},
                "tags": ["trae - ai", "agent - workflow"],
            }

            response = self.session.post(
                f"{self.base_url}/rest / workflows", json=workflow_payload, timeout=30
            )

            if response.status_code == 200:
                workflow_data = response.json()
                workflow = self._parse_workflow(workflow_data)

                # Cache and store
                self.workflows_cache[workflow.id] = workflow
                await self._store_workflow(workflow)

                self.logger.info(f"Created webhook workflow: {workflow.id}")
                return workflow
            else:
                self.logger.error(f"Failed to create workflow: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating webhook workflow: {e}")
            return None

    def _parse_workflow(self, workflow_data: Dict[str, Any]) -> N8nWorkflow:
        """Parse n8n workflow data into WorkflowNode objects."""
        nodes = []
        for node_data in workflow_data.get("nodes", []):
            node = WorkflowNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                type_version=node_data.get("typeVersion", 1),
                position=node_data.get("position", [0, 0]),
                parameters=node_data.get("parameters", {}),
                credentials=node_data.get("credentials"),
                webhook_id=node_data.get("webhookId"),
                disabled=node_data.get("disabled", False),
            )
            nodes.append(node)

        connections = []
        conn_data = workflow_data.get("connections", {})
        for source_node, outputs in conn_data.items():
            for output_name, targets in outputs.items():
                for target in targets:
                    connection = WorkflowConnection(
                        source_node=source_node,
                        source_output=output_name,
                        target_node=target["node"],
                        target_input=target["type"],
                    )
                    connections.append(connection)

        return N8nWorkflow(
            id=workflow_data["id"],
            name=workflow_data["name"],
            active=workflow_data.get("active", False),
            nodes=nodes,
            connections=connections,
            created_at=datetime.fromisoformat(
                workflow_data.get("createdAt", datetime.now().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                workflow_data.get("updatedAt", datetime.now().isoformat())
            ),
            tags=workflow_data.get("tags", []),
            settings=workflow_data.get("settings"),
            static_data=workflow_data.get("staticData"),
        )

    def _parse_execution(self, execution_data: Dict[str, Any]) -> WorkflowExecution:
        """Parse n8n execution data into WorkflowExecution object."""
        status_map = {
            "new": WorkflowStatus.WAITING,
            "running": WorkflowStatus.RUNNING,
            "success": WorkflowStatus.SUCCESS,
            "error": WorkflowStatus.ERROR,
            "canceled": WorkflowStatus.CANCELED,
            "waiting": WorkflowStatus.WAITING,
        }

        return WorkflowExecution(
            id=execution_data["id"],
            workflow_id=execution_data["workflowId"],
            status=status_map.get(execution_data.get("status"), WorkflowStatus.WAITING),
            started_at=datetime.fromisoformat(
                execution_data.get("startedAt", datetime.now().isoformat())
            ),
            finished_at=(
                datetime.fromisoformat(execution_data["finishedAt"])
                if execution_data.get("finishedAt")
                else None
            ),
            data=execution_data.get("data"),
            error=execution_data.get("error"),
            mode=execution_data.get("mode", "trigger"),
            retry_of=execution_data.get("retryOf"),
            retry_count=execution_data.get("retryCount", 0),
        )

    def _format_connections(self, connections: List[Dict[str, str]]) -> Dict[str, Any]:
        """Format connections for n8n API."""
        formatted = {}

        for conn in connections:
            source = conn["source_node"]
            output = conn["source_output"]

            if source not in formatted:
                formatted[source] = {}
            if output not in formatted[source]:
                formatted[source][output] = []

            formatted[source][output].append(
                {"node": conn["target_node"], "type": conn["target_input"], "index": 0}
            )

        return formatted

    async def _store_workflow(self, workflow: N8nWorkflow):
        """Store workflow in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO workflows
                    (id,
    name,
    active,
    nodes,
    connections,
    settings,
    created_at,
    updated_at,
    tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        workflow.id,
                        workflow.name,
                        workflow.active,
                        json.dumps([asdict(node) for node in workflow.nodes]),
                        json.dumps([asdict(conn) for conn in workflow.connections]),
                        json.dumps(workflow.settings) if workflow.settings else None,
                        workflow.created_at.isoformat(),
                        workflow.updated_at.isoformat(),
                        json.dumps(workflow.tags) if workflow.tags else None,
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing workflow: {e}")

    async def _store_execution(self, execution: WorkflowExecution):
        """Store execution in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO executions
                    (id,
    workflow_id,
    status,
    started_at,
    finished_at,
    data,
    error,
    mode,
    retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        execution.id,
                        execution.workflow_id,
                        execution.status.value,
                        execution.started_at.isoformat(),
                        (execution.finished_at.isoformat() if execution.finished_at else None),
                        json.dumps(execution.data) if execution.data else None,
                        execution.error,
                        execution.mode,
                        execution.retry_count,
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing execution: {e}")

    async def _monitor_execution(self, execution_id: str):
        """Monitor execution progress and update status."""
        try:
            while True:
                execution = await self.get_execution(execution_id)
                if not execution:
                    break

                if execution.status in [
                    WorkflowStatus.SUCCESS,
                    WorkflowStatus.ERROR,
                    WorkflowStatus.CANCELED,
                ]:
                    self.logger.info(
                        f"Execution {execution_id} completed with status: {execution.status.value}"
                    )
                    break

                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            self.logger.error(f"Error monitoring execution {execution_id}: {e}")


# Example usage and testing
if __name__ == "__main__":

    async def test_n8n_integration():
        n8n = N8nIntegration()

        # Health check
        health = await n8n.health_check()
        print(f"n8n Health: {health}")

        # Get workflows
        workflows = await n8n.get_workflows()
        print(f"Found {len(workflows)} workflows")

        # Create a test webhook workflow
        agent_tasks = [
            {
                "agent_type": "research",
                "parameters": {
                    "query": "AI trends 2024",
                    "sources": ["google_trends", "reddit"],
                },
            },
            {
                "agent_type": "content",
                "parameters": {
                    "content_type": "blog_post",
                    "topic": "AI trends research results",
                },
            },
        ]

        workflow = await n8n.create_webhook_workflow(
            name="TRAE.AI Research to Content Pipeline",
            webhook_path="trae - ai - research",
            agent_tasks=agent_tasks,
        )

        if workflow:
            print(f"Created workflow: {workflow.name} ({workflow.id})")

    # Run test
    asyncio.run(test_n8n_integration())
