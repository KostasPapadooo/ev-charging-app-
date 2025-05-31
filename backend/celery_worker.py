import os
import sys
import logging
import app.tasks.batch_tasks  # Explicitly import the tasks module

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_config import celery_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure tasks are loaded
# This line is crucial to register the tasks with Celery
celery_app.autodiscover_tasks(['app.tasks'], force=True)

logger.info("Starting Celery worker...")

# Start the worker
if __name__ == "__main__":
    celery_app.start(argv=['worker', '--loglevel=info']) 