from celery import Celery
from app.core.beat_config import beat_schedule

celery_app = Celery(
    'ev_charging',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.tasks.realtime_tasks', 'app.tasks.batch_tasks']
)

# Ρυθμίσεις για τον Celery Beat
celery_app.conf.beat_schedule = beat_schedule

celery_app.conf.timezone = 'UTC' 