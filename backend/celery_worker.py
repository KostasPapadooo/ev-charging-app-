import asyncio
import logging
from typing import Optional
from app.core.celery_config.celery_app import celery_app
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize event loop for MongoDB connection
def init_mongodb() -> Optional[str]:
    """Initialize MongoDB connection"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(connect_to_mongo())
        logger.info("✅ Successfully connected to MongoDB")
        return None
    except Exception as e:
        error_msg = f"❌ Failed to connect to MongoDB: {str(e)}"
        logger.error(error_msg)
        return error_msg

def init_worker():
    """Initialize Celery worker with proper configuration"""
    try:
        # Initialize MongoDB connection
        error = init_mongodb()
        if error:
            raise Exception(error)
        
        # Configure Celery queues and tasks
        celery_app.conf.task_queues = {
            'batch_queue': {
                'exchange': 'batch_queue',
                'routing_key': 'batch_queue',
            },
            'maintenance_queue': {
                'exchange': 'maintenance_queue',
                'routing_key': 'maintenance_queue',
            }
        }
        
        # Set task routes
        celery_app.conf.task_routes = {
            'app.tasks.batch_tasks.*': {'queue': 'batch_queue'},
            'app.tasks.cache_cleanup.*': {'queue': 'maintenance_queue'}
        }
        
        logger.info("✅ Celery worker initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize worker: {str(e)}")
        raise

if __name__ == '__main__':
    init_worker()
    celery_app.start() 