"""
Celery application configuration for RocketTrainer background tasks.
"""
from celery import Celery
from app.config import settings
import structlog

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "rockettrainer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.replay_processing",
        "app.tasks.ml_training"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.replay_processing.*": {"queue": "replay_processing"},
        "app.tasks.ml_training.*": {"queue": "ml_training"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Result backend settings
    result_expires=3600,       # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task autodiscovery
celery_app.autodiscover_tasks()

logger.info("Celery app configured", 
           broker=settings.redis_url,
           queues=["replay_processing", "ml_training"])
