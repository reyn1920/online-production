# celery_app.py - Celery configuration for distributed task processing

import os

from celery import Celery
from dotenv import load_dotenv
from kombu import Queue

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379 / 0")
BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
celery_app = Celery(
    "online_production",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "tasks.content_generation",
        "tasks.business_automation",
        "tasks.platform_integration",
        "tasks.document_processing",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "tasks.content_generation.*": {"queue": "content"},
        "tasks.business_automation.*": {"queue": "business"},
        "tasks.platform_integration.*": {"queue": "platform"},
        "tasks.document_processing.*": {"queue": "documents"},
    },
    # Queue definitions
    task_queues=(
        Queue("content", routing_key="content"),
        Queue("business", routing_key="business"),
        Queue("platform", routing_key="platform"),
        Queue("documents", routing_key="documents"),
        Queue("default", routing_key="default"),
    ),
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "analyze - market - trends": {
            "task": "tasks.business_automation.analyze_market_trends",
            "schedule": 3600.0,  # Every hour
        },
        "optimize - business - performance": {
            "task": "tasks.business_automation.optimize_business_performance",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "sync - platform - data": {
            "task": "tasks.platform_integration.sync_all_platforms",
            "schedule": 900.0,  # Every 15 minutes
        },
    },
)

# Task annotations for resource allocation
celery_app.conf.task_annotations = {
    "tasks.content_generation.generate_ai_content": {
        "rate_limit": "10 / m",
        "time_limit": 300,  # 5 minutes
        "soft_time_limit": 240,  # 4 minutes
    },
    "tasks.business_automation.launch_business": {
        "rate_limit": "5 / m",
        "time_limit": 600,  # 10 minutes
        "soft_time_limit": 540,  # 9 minutes
    },
    "tasks.platform_integration.upload_to_platform": {
        "rate_limit": "20 / m",
        "time_limit": 180,  # 3 minutes
        "soft_time_limit": 150,  # 2.5 minutes
    },
    "tasks.document_processing.convert_document": {
        "rate_limit": "30 / m",
        "time_limit": 120,  # 2 minutes
        "soft_time_limit": 90,  # 1.5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
