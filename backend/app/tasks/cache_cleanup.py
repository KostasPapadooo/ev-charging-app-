from datetime import datetime, timedelta
import logging
from app.repositories.station_repository import station_repository

logger = logging.getLogger(__name__)

async def cleanup_expired_cache():
    """
    Καθαρισμός παλιών cached δεδομένων από τη βάση.
    Εκτελείται περιοδικά ως background task.
    """
    try:
        # Διαγραφή δεδομένων παλιότερων από 1 ώρα
        expiration_threshold = datetime.utcnow() - timedelta(hours=1)
        deleted_count = await station_repository.cleanup_old_cache(expiration_threshold)
        logger.info(f"Cache cleanup completed. Removed {deleted_count} expired stations.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")
        raise 