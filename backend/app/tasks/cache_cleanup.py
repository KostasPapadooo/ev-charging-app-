from app.core.celery_config.celery_app import celery_app
from app.repositories.station_repository import station_repository
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    name="app.tasks.cache_cleanup.cleanup_old_cache",
    queue="maintenance_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def cleanup_old_cache(self):
    """
    Clean up old cached station data.
    Removes stations that haven't been updated in the last 24 hours.
    """
    try:
        # Run async operations in sync context
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_async_cleanup_cache())
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_cache task: {e}")
        raise self.retry(exc=e)

async def _async_cleanup_cache():
    """Async implementation of cache cleanup"""
    try:
        # Initialize repository
        await station_repository.initialize()
        
        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Delete old cached data
        deleted_count = await station_repository.cleanup_old_cache(hours=24)
        
        logger.info(f"Successfully cleaned up {deleted_count} old cached records")
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} old cached records",
            "cutoff_time": cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in _async_cleanup_cache: {e}")
        raise 