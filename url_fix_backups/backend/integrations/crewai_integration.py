#!/usr / bin / env python3
"""
TRAE.AI CrewAI Agent Framework Integration

Provides seamless integration between CrewAI multi - agent framework
and the TRAE.AI ecosystem for coordinated agent collaboration.

Features:
- CrewAI agent creation and management
- Multi - agent task coordination
- Role - based agent specialization
- Collaborative workflow execution
- Agent communication protocols
- Performance monitoring and analytics

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore

try:

    from crewai import Agent, Crew, Process, Task
    from crewai.tools import BaseTool
    from langchain.chat_models import ChatOpenAI
    from langchain.llms import OpenAI

    CREWAI_AVAILABLE = True
except ImportError:
    # Fallback for when CrewAI is not installed
    CREWAI_AVAILABLE = False


    class Agent:


        def __init__(self, **kwargs):
            pass


    class Task:


        def __init__(self, **kwargs):
            pass


    class Crew:


        def __init__(self, **kwargs):
            pass


    class Process:
        sequential = "sequential"
        hierarchical = "hierarchical"


    class BaseTool:


        def __init__(self, **kwargs):
            pass


class AgentRole(Enum):
    """Specialized agent roles in CrewAI framework."""

    RESEARCHER = "researcher"
    CONTENT_CREATOR = "content_creator"
    MARKETING_SPECIALIST = "marketing_specialist"
    DATA_ANALYST = "data_analyst"
    PROJECT_MANAGER = "project_manager"
    QA_SPECIALIST = "qa_specialist"
    SYSTEM_ARCHITECT = "system_architect"
    BUSINESS_STRATEGIST = "business_strategist"


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrewStatus(Enum):
    """Crew execution status."""

    IDLE = "idle"
    ASSEMBLING = "assembling"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass


class AgentConfig:
    """Configuration for a CrewAI agent."""

    role: str
    goal: str
    backstory: str
    tools: List[str] = None
    llm_config: Dict[str, Any] = None
    max_iter: int = 10
    max_execution_time: Optional[int] = None
    verbose: bool = True
    allow_delegation: bool = True
    memory: bool = True

@dataclass


class TaskConfig:
    """Configuration for a CrewAI task."""

    description: str
    expected_output: str
    agent_role: str
    tools: List[str] = None
    context: List[str] = None
    output_file: Optional[str] = None
    callback: Optional[str] = None

@dataclass


class CrewConfig:
    """Configuration for a CrewAI crew."""

    name: str
    agents: List[AgentConfig]
    tasks: List[TaskConfig]
    process: str = "sequential"
    verbose: bool = True
    memory: bool = True
    cache: bool = True
    max_rpm: Optional[int] = None
    language: str = "en"

@dataclass


class CrewExecution:
    """Represents a crew execution instance."""

    id: str
    crew_name: str
    status: CrewStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class TraeAITool(BaseTool):
    """Custom tool that bridges CrewAI with TRAE.AI capabilities."""


    def __init__(self, name: str, description: str, func: Callable, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.func = func


    def _run(self, *args, **kwargs):
        """Execute the tool function."""
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"


    async def _arun(self, *args, **kwargs):
        """Async execution of the tool function."""
        return self._run(*args, **kwargs)


class CrewAIIntegration:
    """
    Comprehensive CrewAI framework integration with TRAE.AI
    for multi - agent coordination and collaborative task execution.
    """


    def __init__(self, secrets_db_path: str = "data / secrets.sqlite"):
        self.logger = setup_logger("crewai_integration")
        self.secret_store = SecretStore(secrets_db_path)

        # Check CrewAI availability
        if not CREWAI_AVAILABLE:
            self.logger.warning(
                "CrewAI not installed. Install with: pip install crewai"
            )

        # Load credentials
        self.credentials = self._load_credentials()

        # Initialize database
        self.db_path = "data / crewai_executions.sqlite"
        self._init_database()

        # Agent and crew registries
        self.agents_registry = {}
        self.crews_registry = {}
        self.tools_registry = {}
        self.executions_cache = {}

        # Thread pool for concurrent execution
        self.executor = ThreadPoolExecutor(max_workers = 4)

        # Initialize default tools
        self._register_default_tools()

        # Initialize default agent configurations
        self._init_default_agents()

        self.logger.info("CrewAI integration initialized successfully")


    def _load_credentials(self) -> Dict[str, str]:
        """Load API credentials for LLM providers."""
        try:
            with self.secret_store as store:
                credentials = {
                    "openai_api_key": store.get_secret("OPENAI_API_KEY"),
                        "anthropic_api_key": store.get_secret("ANTHROPIC_API_KEY"),
                        "google_api_key": store.get_secret("GOOGLE_API_KEY"),
                        "huggingface_api_key": store.get_secret("HUGGINGFACE_API_KEY"),
                        }

                # Set environment variables for CrewAI
                for key, value in credentials.items():
                    if value:
                        os.environ[key.upper()] = value

                return credentials

        except Exception as e:
            self.logger.error(f"Failed to load CrewAI credentials: {e}")
            return {}


    def _init_database(self):
        """Initialize CrewAI execution tracking database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok = True)

        with sqlite3.connect(self.db_path) as conn:
            # Crew executions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crew_executions (
                    id TEXT PRIMARY KEY,
                        crew_name TEXT NOT NULL,
                        status TEXT,
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        results TEXT,
                        error TEXT,
                        metrics TEXT,
                        config TEXT
                )
            """
            )

            # Agent performance table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id TEXT PRIMARY KEY,
                        execution_id TEXT,
                        agent_role TEXT,
                        task_description TEXT,
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        success BOOLEAN,
                        output_quality REAL,
                        execution_time REAL,
                        tokens_used INTEGER,
                        FOREIGN KEY (execution_id) REFERENCES crew_executions (id)
                )
            """
            )

            # Task tracking table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_tracking (
                    id TEXT PRIMARY KEY,
                        execution_id TEXT,
                        task_description TEXT,
                        agent_role TEXT,
                        status TEXT,
                        created_at TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        output TEXT,
                        dependencies TEXT,
                        FOREIGN KEY (execution_id) REFERENCES crew_executions (id)
                )
            """
            )

            conn.commit()


    def _register_default_tools(self):
        """Register default tools for CrewAI agents."""
        # Research tools
        self.register_tool(
            "web_search",
                "Search the web for information on a given topic",
                self._web_search_tool,
                )

        self.register_tool(
            "file_writer", "Write content to a file", self._file_writer_tool
        )

        self.register_tool(
            "data_analyzer",
                "Analyze data and generate insights",
                self._data_analyzer_tool,
                )

        self.register_tool(
            "content_generator",
                "Generate various types of content",
                self._content_generator_tool,
                )

        self.register_tool(
            "api_caller", "Make API calls to external services", self._api_caller_tool
        )


    def _init_default_agents(self):
        """Initialize default agent configurations."""
        default_agents = {
            AgentRole.RESEARCHER: AgentConfig(
                role="Senior Research Analyst",
                    goal="Conduct comprehensive research \
    and provide accurate, well - sourced information",
                    backstory="You are a seasoned research analyst with expertise in gathering, analyzing, \
    and synthesizing information from multiple sources. You excel at identifying trends, patterns, \
    and insights that others might miss.",
                    tools=["web_search", "data_analyzer"],
                    allow_delegation = True,
                    ),
                AgentRole.CONTENT_CREATOR: AgentConfig(
                role="Creative Content Specialist",
                    goal="Create engaging, high - quality content across multiple formats \
    and platforms",
                    backstory="You are a versatile content creator with a talent for crafting compelling narratives, engaging copy, \
    and multimedia content that resonates with target audiences.",
                    tools=["content_generator", "file_writer"],
                    allow_delegation = False,
                    ),
                AgentRole.MARKETING_SPECIALIST: AgentConfig(
                role="Digital Marketing Strategist",
                    goal="Develop \
    and execute effective marketing strategies to maximize reach \
    and engagement",
                    backstory="You are a data - driven marketing professional with deep understanding of digital channels, audience psychology, \
    and conversion optimization.",
                    tools=["web_search", "data_analyzer", "api_caller"],
                    allow_delegation = True,
                    ),
                AgentRole.DATA_ANALYST: AgentConfig(
                role="Senior Data Scientist",
                    goal="Extract actionable insights from complex datasets \
    and provide data - driven recommendations",
                    backstory="You are an experienced data scientist with expertise in statistical analysis, machine learning, \
    and data visualization. You excel at turning raw data into strategic insights.",
                    tools=["data_analyzer", "file_writer"],
                    allow_delegation = False,
                    ),
                AgentRole.PROJECT_MANAGER: AgentConfig(
                role="Agile Project Manager",
                    goal="Coordinate team efforts, manage timelines, \
    and ensure successful project delivery",
                    backstory="You are an experienced project manager with a track record of delivering complex projects on time \
    and within budget. You excel at resource allocation \
    and risk management.",
                    tools=["file_writer", "api_caller"],
                    allow_delegation = True,
                    ),
                }

        for role, config in default_agents.items():
            self.register_agent_config(role.value, config)


    def register_tool(self, name: str, description: str, func: Callable):
        """Register a custom tool for use by CrewAI agents."""
        tool = TraeAITool(name = name, description = description, func = func)
        self.tools_registry[name] = tool
        self.logger.info(f"Registered tool: {name}")


    def register_agent_config(self, role: str, config: AgentConfig):
        """Register an agent configuration."""
        self.agents_registry[role] = config
        self.logger.info(f"Registered agent config: {role}")


    def create_agent(
        self, role: str, custom_config: Optional[AgentConfig] = None
    ) -> Optional[Agent]:
        """Create a CrewAI agent with specified role."""
        if not CREWAI_AVAILABLE:
            self.logger.error("CrewAI not available")
            return None

        try:
            config = custom_config or self.agents_registry.get(role)
            if not config:
                self.logger.error(f"No configuration found for agent role: {role}")
                return None

            # Get tools for agent
            agent_tools = []
            if config.tools:
                for tool_name in config.tools:
                    if tool_name in self.tools_registry:
                        agent_tools.append(self.tools_registry[tool_name])

            # Configure LLM
            llm = None
            if self.credentials.get("openai_api_key"):
                llm = ChatOpenAI(
                    model="gpt - 4",
                        temperature = 0.7,
                        openai_api_key = self.credentials["openai_api_key"],
                        )

            agent = Agent(
                role = config.role,
                    goal = config.goal,
                    backstory = config.backstory,
                    tools = agent_tools,
                    llm = llm,
                    max_iter = config.max_iter,
                    max_execution_time = config.max_execution_time,
                    verbose = config.verbose,
                    allow_delegation = config.allow_delegation,
                    memory = config.memory,
                    )

            self.logger.info(f"Created agent: {config.role}")
            return agent

        except Exception as e:
            self.logger.error(f"Error creating agent {role}: {e}")
            return None


    def create_task(self, config: TaskConfig, agent: Agent) -> Optional[Task]:
        """Create a CrewAI task."""
        if not CREWAI_AVAILABLE:
            self.logger.error("CrewAI not available")
            return None

        try:
            # Get tools for task
            task_tools = []
            if config.tools:
                for tool_name in config.tools:
                    if tool_name in self.tools_registry:
                        task_tools.append(self.tools_registry[tool_name])

            task = Task(
                description = config.description,
                    expected_output = config.expected_output,
                    agent = agent,
                    tools = task_tools,
                    context = config.context,
                    output_file = config.output_file,
                    callback = config.callback,
                    )

            self.logger.info(f"Created task: {config.description[:50]}...")
            return task

        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return None


    def create_crew(self, config: CrewConfig) -> Optional[Crew]:
        """Create a CrewAI crew with agents and tasks."""
        if not CREWAI_AVAILABLE:
            self.logger.error("CrewAI not available")
            return None

        try:
            # Create agents
            agents = []
            agents_map = {}

            for agent_config in config.agents:
                agent = self.create_agent(agent_config.role, agent_config)
                if agent:
                    agents.append(agent)
                    agents_map[agent_config.role] = agent

            if not agents:
                self.logger.error("No agents created for crew")
                return None

            # Create tasks
            tasks = []
            for task_config in config.tasks:
                agent = agents_map.get(task_config.agent_role)
                if agent:
                    task = self.create_task(task_config, agent)
                    if task:
                        tasks.append(task)

            if not tasks:
                self.logger.error("No tasks created for crew")
                return None

            # Determine process type
            process_type = Process.sequential
            if config.process == "hierarchical":
                process_type = Process.hierarchical

            crew = Crew(
                agents = agents,
                    tasks = tasks,
                    process = process_type,
                    verbose = config.verbose,
                    memory = config.memory,
                    cache = config.cache,
                    max_rpm = config.max_rpm,
                    language = config.language,
                    )

            # Register crew
            self.crews_registry[config.name] = crew

            self.logger.info(
                f"Created crew: {config.name} with {len(agents)} agents \
    and {len(tasks)} tasks"
            )
            return crew

        except Exception as e:
            self.logger.error(f"Error creating crew {config.name}: {e}")
            return None


    async def execute_crew(
        self, crew_name: str, inputs: Optional[Dict[str, Any]] = None
    ) -> Optional[CrewExecution]:
        """Execute a crew asynchronously."""
        try:
            crew = self.crews_registry.get(crew_name)
            if not crew:
                self.logger.error(f"Crew not found: {crew_name}")
                return None

            execution_id = str(uuid.uuid4())
            execution = CrewExecution(
                id = execution_id,
                    crew_name = crew_name,
                    status = CrewStatus.EXECUTING,
                    started_at = datetime.now(),
                    )

            # Store execution
            self.executions_cache[execution_id] = execution
            await self._store_execution(execution)

            # Execute crew in thread pool
            future = self.executor.submit(self._execute_crew_sync, crew, inputs or {})

            # Monitor execution
            asyncio.create_task(self._monitor_crew_execution(execution_id, future))

            self.logger.info(f"Started crew execution: {execution_id}")
            return execution

        except Exception as e:
            self.logger.error(f"Error executing crew {crew_name}: {e}")
            return None


    def _execute_crew_sync(self, crew: Crew, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute crew synchronously in thread."""
        try:
            result = crew.kickoff(inputs = inputs)
            return {
                "success": True,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            return {
                "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    }


    async def _monitor_crew_execution(self, execution_id: str, future):
        """Monitor crew execution progress."""
        try:
            # Wait for completion
            result = await asyncio.get_event_loop().run_in_executor(None, future.result)

            # Update execution
            execution = self.executions_cache.get(execution_id)
            if execution:
                execution.finished_at = datetime.now()
                execution.results = result

                if result.get("success"):
                    execution.status = CrewStatus.COMPLETED
                else:
                    execution.status = CrewStatus.FAILED
                    execution.error = result.get("error")

                # Update database
                await self._store_execution(execution)

                self.logger.info(
                    f"Crew execution {execution_id} completed with status: {execution.status.value}"
                )

        except Exception as e:
            self.logger.error(f"Error monitoring crew execution {execution_id}: {e}")

            # Update execution with error
                execution = self.executions_cache.get(execution_id)
            if execution:
                execution.status = CrewStatus.FAILED
                execution.error = str(e)
                execution.finished_at = datetime.now()
                await self._store_execution(execution)


    async def get_execution(self, execution_id: str) -> Optional[CrewExecution]:
        """Get crew execution status and results."""
        return self.executions_cache.get(execution_id)


    async def _store_execution(self, execution: CrewExecution):
        """Store execution in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO crew_executions
                    (id,
    crew_name,
    status,
    started_at,
    finished_at,
    results,
    error,
    metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        execution.id,
                            execution.crew_name,
                            execution.status.value,
                            execution.started_at.isoformat(),
                            (
                            execution.finished_at.isoformat()
                            if execution.finished_at
                            else None
                        ),
                            json.dumps(execution.results) if execution.results else None,
                            execution.error,
                            json.dumps(execution.metrics) if execution.metrics else None,
                            ),
                        )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing execution: {e}")

    # Tool implementations


    def _web_search_tool(self, query: str) -> str:
        """Web search tool implementation."""
        try:
            # This would integrate with actual search APIs
            return (
                f"Search results for: {query}\\n[Placeholder for actual search results]"
            )
        except Exception as e:
            return f"Search error: {str(e)}"


    def _file_writer_tool(self, filename: str, content: str) -> str:
        """File writer tool implementation."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok = True)
            with open(filename, "w", encoding="utf - 8") as f:
                f.write(content)
            return f"Successfully wrote content to {filename}"
        except Exception as e:
            return f"File write error: {str(e)}"


    def _data_analyzer_tool(self, data: str) -> str:
        """Data analyzer tool implementation."""
        try:
            # This would integrate with actual data analysis capabilities
            return (
                f"Analysis of data: {data[:100]}...\\n[Placeholder for actual analysis]"
            )
        except Exception as e:
            return f"Analysis error: {str(e)}"


    def _content_generator_tool(self, content_type: str, topic: str) -> str:
        """Content generator tool implementation."""
        try:
            # This would integrate with actual content generation
            return f"Generated {content_type} about {topic}\\n[Placeholder for actual content]"
        except Exception as e:
            return f"Content generation error: {str(e)}"


    def _api_caller_tool(
        self, url: str, method: str = "GET", data: Optional[Dict] = None
    ) -> str:
        """API caller tool implementation."""
        try:
            # This would make actual API calls
            return f"API call to {url} with method {method}\\n[Placeholder for actual response]"
        except Exception as e:
            return f"API call error: {str(e)}"

# Example usage and testing
if __name__ == "__main__":


    async def test_crewai_integration():
        crewai = CrewAIIntegration()

        # Create a research crew
        crew_config = CrewConfig(
            name="Research and Content Crew",
                agents=[
                AgentConfig(
                    role="researcher",
                        goal="Research AI trends for 2024",
                        backstory="Expert AI researcher",
                        tools=["web_search", "data_analyzer"],
                        ),
                    AgentConfig(
                    role="content_creator",
                        goal="Create engaging content from research",
                        backstory="Creative content specialist",
                        tools=["content_generator", "file_writer"],
                        ),
                    ],
                tasks=[
                TaskConfig(
                    description="Research the latest AI trends for 2024",
                        expected_output="Comprehensive report on AI trends",
                        agent_role="researcher",
                        ),
                    TaskConfig(
                    description="Create a blog post from the research findings",
                        expected_output="Engaging blog post about AI trends",
                        agent_role="content_creator",
                        ),
                    ],
                )

        crew = crewai.create_crew(crew_config)
        if crew:
            print(f"Created crew: {crew_config.name}")

            # Execute crew
            execution = await crewai.execute_crew("Research and Content Crew")
            if execution:
                print(f"Started execution: {execution.id}")

                # Wait for completion
                while execution.status in [CrewStatus.ASSEMBLING, CrewStatus.EXECUTING]:
                    await asyncio.sleep(2)
                    execution = await crewai.get_execution(execution.id)

                print(f"Execution completed with status: {execution.status.value}")
                if execution.results:
                    print(f"Results: {execution.results}")

    # Run test
    asyncio.run(test_crewai_integration())