from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    celery_app = Celery(
        'ev_charging',
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            'app.tasks.batch_tasks'
        ]
    )
    logger.info("Celery app created with broker and backend.")
    logger.info(f"Celery include: {celery_app.conf.include}")

except Exception as e:
    logger.error(f"Error creating Celery app: {e}", exc_info=True)
    raise

# Load Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
    task_acks_late=True,
    task_default_retry_delay=300,  # 5 minutes retry delay
    task_max_retries=3,
    task_ignore_result=False,
    result_expires=86400,  # Results expire after 24 hours
)

# Autodiscover tasks in all installed apps
# This will automatically find tasks in app/tasks/*.py
celery_app.autodiscover_tasks(['app.tasks'])

# Log Celery configuration
logger.info("Celery configuration loaded with Redis broker and backend")

CELERY_IMPORTS = (
    'app.tasks.batch_tasks',
    'app.tasks.user_tasks',
    'app.tasks.realtime_tasks'
) 