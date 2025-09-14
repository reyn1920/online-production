#!/usr/bin/env python3
"""
TRAE.AI Orchestrator - Main Coordination Service
Handles agent coordination, task distribution, and system monitoring
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import psutil
import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Configuration


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/trae_ai")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

    # Services
    CONTENT_AGENT_URL = os.getenv("CONTENT_AGENT_URL", "http://content_agent:8001")
    MARKETING_AGENT_URL = os.getenv("MARKETING_AGENT_URL", "http://marketing_agent:8002")
    MONETIZATION_BUNDLE_URL = os.getenv(
        "MONETIZATION_BUNDLE_URL", "http://monetization_bundle:8003"
    )
    REVENUE_TRACKER_URL = os.getenv("REVENUE_TRACKER_URL", "http://revenue_tracker:8004")

    # System
    USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MASTER_API_KEY = os.getenv("MASTER_API_KEY", "trae-ai-master-key-2024")

    # Performance
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "300"))

    # Monitoring
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))


config = Config()

# Database Models
Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    task_type = Column(String, index=True)
    status = Column(String, default="pending")
    priority = Column(Integer, default=5)
    agent = Column(String)
    payload = Column(JSON)
    result = Column(JSON)
    error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    labels = Column(JSON)


class AgentStatus(Base):
    __tablename__ = "agent_status"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, unique=True, index=True)
    status = Column(String)  # online, offline, error
    last_heartbeat = Column(DateTime)
    health_score = Column(Float, default=1.0)
    active_tasks = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    metadata = Column(JSON)


# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models


class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task to execute")
    agent: str = Field(..., description="Target agent for the task")
    priority: int = Field(5, description="Task priority (1-10, higher is more urgent)")
    payload: Dict[str, Any] = Field(..., description="Task payload")
    max_retries: int = Field(3, description="Maximum retry attempts")
    timeout: int = Field(300, description="Task timeout in seconds")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_completion: Optional[datetime] = None


class SystemStatus(BaseModel):
    status: str
    timestamp: datetime
    agents: Dict[str, Dict[str, Any]]
    active_tasks: int
    completed_tasks_today: int
    system_load: float
    memory_usage: float
    uptime: str


class ContentCreationRequest(BaseModel):
    topic: str = Field(..., description="Content topic")
    content_type: str = Field("video", description="Type of content to create")
    style: str = Field("informative", description="Content style")
    duration: int = Field(60, description="Content duration in seconds")
    include_avatar: bool = Field(True, description="Include AI avatar")
    voice_style: str = Field("professional", description="Voice style for TTS")
    auto_publish: bool = Field(False, description="Auto-publish to platforms")


class MarketingCampaignRequest(BaseModel):
    campaign_name: str = Field(..., description="Campaign name")
    campaign_type: str = Field(..., description="Type of marketing campaign")
    target_audience: str = Field(..., description="Target audience description")
    channels: List[str] = Field(..., description="Marketing channels to use")
    budget: float = Field(..., description="Campaign budget")
    duration_days: int = Field(30, description="Campaign duration in days")
    objectives: List[str] = Field(..., description="Campaign objectives")


# Metrics
task_counter = Counter("orchestrator_tasks_total", "Total tasks processed", ["agent", "status"])
task_duration = Histogram(
    "orchestrator_task_duration_seconds", "Task processing duration", ["agent"]
)
active_tasks_gauge = Gauge("orchestrator_active_tasks", "Currently active tasks")
agent_health_gauge = Gauge("orchestrator_agent_health", "Agent health score", ["agent"])

# Redis connection
redis_client = None

# HTTP client
http_client = None

# Scheduler
scheduler = AsyncIOScheduler()

# Task queue
task_queue = asyncio.Queue(maxsize=1000)


class TraeAIOrchestrator:
    def __init__(self):
        self.agents = {
            "content_agent": config.CONTENT_AGENT_URL,
            "marketing_agent": config.MARKETING_AGENT_URL,
            "monetization_bundle": config.MONETIZATION_BUNDLE_URL,
            "revenue_tracker": config.REVENUE_TRACKER_URL,
        }
        self.active_tasks = {}
        self.task_workers = []
        self.system_start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize the orchestrator"""
        global redis_client, http_client

        # Initialize Redis
        redis_client = redis.from_url(config.REDIS_URL)

        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)

        # Start task workers
        for i in range(config.MAX_CONCURRENT_TASKS):
            worker = asyncio.create_task(self.task_worker(f"worker-{i}"))
            self.task_workers.append(worker)

        # Start scheduler
        scheduler.start()

        # Schedule periodic tasks
        scheduler.add_job(
            self.health_check_agents,
            CronTrigger(second="*/30"),  # Every 30 seconds
            id="health_check",
        )

        scheduler.add_job(
            self.cleanup_old_tasks,
            CronTrigger(hour=2),  # Daily at 2 AM
            id="cleanup_tasks",
        )

        scheduler.add_job(
            self.generate_system_report,
            CronTrigger(hour="*/6"),  # Every 6 hours
            id="system_report",
        )

        logger.info("TRAE.AI Orchestrator initialized successfully")

    async def shutdown(self):
        """Shutdown the orchestrator"""
        # Stop scheduler
        scheduler.shutdown()

        # Cancel task workers
        for worker in self.task_workers:
            worker.cancel()

        # Close connections
        if http_client:
            await http_client.aclose()
        if redis_client:
            await redis_client.close()

        logger.info("TRAE.AI Orchestrator shutdown complete")

    async def task_worker(self, worker_name: str):
        """Background task worker"""
        logger.info(f"Task worker {worker_name} started")

        while True:
            try:
                # Get task from queue
                task_data = await task_queue.get()

                if task_data is None:  # Shutdown signal
                    break

                await self.execute_task(task_data)
                task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task worker {worker_name} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Task worker {worker_name} stopped")

    async def execute_task(self, task_data: Dict[str, Any]):
        """Execute a task"""
        task_id = task_data["task_id"]
        agent = task_data["agent"]
        task_type = task_data["task_type"]
        payload = task_data["payload"]

        start_time = datetime.utcnow()

        try:
            # Update task status
            await self.update_task_status(task_id, "running", started_at=start_time)

            # Execute task on agent
            result = await self.call_agent(agent, task_type, payload)

            # Update task with result
            await self.update_task_status(
                task_id, "completed", result=result, completed_at=datetime.utcnow()
            )

            # Update metrics
            task_counter.labels(agent=agent, status="completed").inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            task_duration.labels(agent=agent).observe(duration)

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            # Handle task failure
            await self.handle_task_failure(task_id, str(e))
            task_counter.labels(agent=agent, status="failed").inc()
            logger.error(f"Task {task_id} failed: {e}")

    async def call_agent(
        self, agent: str, task_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an agent to execute a task"""
        if agent not in self.agents:
            raise ValueError(f"Unknown agent: {agent}")

        agent_url = self.agents[agent]
        endpoint = f"{agent_url}/api/execute"

        request_data = {"task_type": task_type, "payload": payload}

        async with http_client as client:
            response = await client.post(endpoint, json=request_data, timeout=config.TASK_TIMEOUT)
            response.raise_for_status()
            return response.json()

    async def update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status in database"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                task.status = status
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                db.commit()
        finally:
            db.close()

    async def handle_task_failure(self, task_id: str, error: str):
        """Handle task failure with retry logic"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                task.retry_count += 1
                task.error = error

                if task.retry_count < task.max_retries:
                    # Retry task
                    task.status = "pending"
                    await task_queue.put(
                        {
                            "task_id": task_id,
                            "agent": task.agent,
                            "task_type": task.task_type,
                            "payload": task.payload,
                        }
                    )
                    logger.info(
                        f"Task {task_id} queued for retry ({task.retry_count}/{task.max_retries})"
                    )
                else:
                    # Mark as failed
                    task.status = "failed"
                    task.completed_at = datetime.utcnow()
                    logger.error(
                        f"Task {task_id} failed permanently after {task.retry_count} retries"
                    )

                db.commit()
        finally:
            db.close()

    async def health_check_agents(self):
        """Check health of all agents"""
        db = SessionLocal()
        try:
            for agent_name, agent_url in self.agents.items():
                try:
                    async with http_client as client:
                        response = await client.get(f"{agent_url}/health", timeout=10)
                        health_score = 1.0 if response.status_code == 200 else 0.5
                        status = "online" if response.status_code == 200 else "degraded"
                except Exception:
                    health_score = 0.0
                    status = "offline"

                # Update agent status
                agent_status = (
                    db.query(AgentStatus).filter(AgentStatus.agent_name == agent_name).first()
                )

                if not agent_status:
                    agent_status = AgentStatus(
                        agent_name=agent_name,
                        status=status,
                        health_score=health_score,
                        last_heartbeat=datetime.utcnow(),
                    )
                    db.add(agent_status)
                else:
                    agent_status.status = status
                    agent_status.health_score = health_score
                    agent_status.last_heartbeat = datetime.utcnow()

                # Update metrics
                agent_health_gauge.labels(agent=agent_name).set(health_score)

            db.commit()
        finally:
            db.close()

    async def cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=config.METRICS_RETENTION_DAYS)

        db = SessionLocal()
        try:
            deleted_count = (
                db.query(Task)
                .filter(
                    Task.completed_at < cutoff_date,
                    Task.status.in_(["completed", "failed"]),
                )
                .delete()
            )

            db.commit()
            logger.info(f"Cleaned up {deleted_count} old tasks")
        finally:
            db.close()

    async def generate_system_report(self):
        """Generate system performance report"""
        db = SessionLocal()
        try:
            # Get task statistics
            total_tasks = db.query(Task).count()
            completed_tasks = db.query(Task).filter(Task.status == "completed").count()
            failed_tasks = db.query(Task).filter(Task.status == "failed").count()
            active_tasks = db.query(Task).filter(Task.status.in_(["pending", "running"])).count()

            # Get agent health
            agents_health = db.query(AgentStatus).all()

            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_uptime": str(datetime.utcnow() - self.system_start_time),
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                    "active": active_tasks,
                    "success_rate": (completed_tasks / max(total_tasks, 1)) * 100,
                },
                "agents": {
                    agent.agent_name: {
                        "status": agent.status,
                        "health_score": agent.health_score,
                        "active_tasks": agent.active_tasks,
                        "total_completed": agent.total_tasks_completed,
                        "error_count": agent.error_count,
                    }
                    for agent in agents_health
                },
            }

            # Store report in Redis
            await redis_client.setex("system_report", 3600, str(report))  # 1 hour TTL

            logger.info("System report generated")

        finally:
            db.close()


# Initialize orchestrator
orchestrator = TraeAIOrchestrator()


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await orchestrator.initialize()
    yield
    # Shutdown
    await orchestrator.shutdown()


app = FastAPI(
    title="TRAE.AI Orchestrator",
    description="Central coordination service for TRAE.AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "orchestrator",
        "version": "1.0.0",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


@app.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get comprehensive system status"""
    # Get agent statuses
    agents_status = db.query(AgentStatus).all()
    agents_dict = {}

    for agent in agents_status:
        agents_dict[agent.agent_name] = {
            "status": agent.status,
            "health_score": agent.health_score,
            "last_heartbeat": (agent.last_heartbeat.isoformat() if agent.last_heartbeat else None),
            "active_tasks": agent.active_tasks,
            "total_completed": agent.total_tasks_completed,
            "error_count": agent.error_count,
        }

    # Get task counts
    active_tasks = db.query(Task).filter(Task.status.in_(["pending", "running"])).count()
    completed_today = (
        db.query(Task)
        .filter(Task.completed_at >= datetime.utcnow().date(), Task.status == "completed")
        .count()
    )

    return SystemStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        agents=agents_dict,
        active_tasks=active_tasks,
        completed_tasks_today=completed_today,
        system_load=psutil.cpu_percent(interval=1) / 100.0,
        memory_usage=psutil.virtual_memory().percent / 100.0,
        uptime=str(datetime.utcnow() - orchestrator.system_start_time),
    )


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest, db: Session = Depends(get_db)):
    """Create a new task"""

    import uuid

    task_id = str(uuid.uuid4())

    # Create task in database
    task = Task(
        task_id=task_id,
        task_type=task_request.task_type,
        agent=task_request.agent,
        priority=task_request.priority,
        payload=task_request.payload,
        max_retries=task_request.max_retries,
        status="pending",
    )

    db.add(task)
    db.commit()

    # Add to task queue
    await task_queue.put(
        {
            "task_id": task_id,
            "agent": task_request.agent,
            "task_type": task_request.task_type,
            "payload": task_request.payload,
        }
    )

    # Update metrics
    active_tasks_gauge.inc()

    return TaskResponse(
        task_id=task_id,
        status="queued",
        message="Task queued for execution",
        estimated_completion=datetime.utcnow() + timedelta(seconds=task_request.timeout),
    )


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get task status"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.task_id,
        "status": task.status,
        "task_type": task.task_type,
        "agent": task.agent,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result": task.result,
        "error": task.error,
        "retry_count": task.retry_count,
    }


@app.post("/api/content/create")
async def create_content(request: ContentCreationRequest, background_tasks: BackgroundTasks):
    """Create content using the content agent"""
    task_request = TaskRequest(
        task_type="create_content",
        agent="content_agent",
        priority=7,
        payload=request.dict(),
    )

    # Create task
    db = SessionLocal()
    try:
        response = await create_task(task_request, db)
        return response
    finally:
        db.close()


@app.post("/api/marketing/campaign")
async def create_marketing_campaign(request: MarketingCampaignRequest):
    """Create marketing campaign using the marketing agent"""
    task_request = TaskRequest(
        task_type="create_campaign",
        agent="marketing_agent",
        priority=6,
        payload=request.dict(),
    )

    # Create task
    db = SessionLocal()
    try:
        response = await create_task(task_request, db)
        return response
    finally:
        db.close()


@app.post("/api/monetization/ebook")
async def create_ebook(topic: str, pages: int = 50):
    """Create ebook using monetization bundle"""
    task_request = TaskRequest(
        task_type="create_ebook",
        agent="monetization_bundle",
        priority=5,
        payload={"topic": topic, "pages": pages},
    )

    # Create task
    db = SessionLocal()
    try:
        response = await create_task(task_request, db)
        return response
    finally:
        db.close()


@app.get("/api/revenue/analytics")
async def get_revenue_analytics():
    """Get revenue analytics from revenue tracker"""
    try:
        async with http_client as client:
            response = await client.get(f"{config.REVENUE_TRACKER_URL}/api/analytics")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Revenue tracker unavailable: {e}")


@app.get("/api/system/report")
async def get_system_report():
    """Get cached system report"""
    try:
        report = await redis_client.get("system_report")
        if report:
            return eval(report)  # Convert string back to dict
        else:
            return {"message": "No recent report available"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unable to retrieve report: {e}")


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting TRAE.AI Orchestrator")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Mock mode: {config.USE_MOCK}")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)
