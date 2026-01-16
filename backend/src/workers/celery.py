"""
Celery Configuration
Celery configuration for background task processing.
"""

import os
from celery import Celery
from src.core.config import settings

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.core.config")

# Create Celery app
celery_app = Celery(
    "vck",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone=settings.TIMEZONE if hasattr(settings, "TIMEZONE") else "UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={},
    
    # Task routing
    task_routes={
        "src.workers.tasks.send_sms": {"queue": "notifications"},
        "src.workers.tasks.send_email": {"queue": "notifications"},
        "src.workers.tasks.send_push_notification": {"queue": "notifications"},
        "src.workers.tasks.bulk_operation": {"queue": "bulk"},
        "src.workers.tasks.ml_inference": {"queue": "ml"},
    },
)


# =============================================================================
# Celery Task Base Class
# =============================================================================

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import logging

logger = logging.getLogger(__name__)


class BaseCeleryTask(celery_app.Task):
    """Base class for Celery tasks with common functionality."""
    
    abstract = True
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}", exc_info=einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying after {exc}: {einfo}")


# =============================================================================
# Import tasks after app configuration
# =============================================================================

from src.workers.tasks import (
    send_sms,
    send_email,
    send_push_notification,
    bulk_operation,
    ml_inference,
)


# =============================================================================
# Celery Beat Configuration
# =============================================================================

def configure_beat_schedule():
    """Configure periodic tasks for Celery Beat."""
    from src.workers.models import TaskType
    
    beat_schedule = {}
    
    # Add periodic tasks here
    # Example:
    # beat_schedule["task-name"] = {
    #     "task": "src.workers.tasks.task_name",
    #     "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
    #     "args": (),
    #     "kwargs": {},
    # }
    
    celery_app.conf.beat_schedule = beat_schedule


# Call configuration
configure_beat_schedule()
