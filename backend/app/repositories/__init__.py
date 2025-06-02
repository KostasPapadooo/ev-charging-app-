# from app.repositories.station_repository import station_repository
from app.repositories.user_repository import user_repository
from app.repositories.event_repository import event_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.station_repository import station_repository
from app.repositories.analytics_repository import analytics_repository
import logging

logger = logging.getLogger(__name__)

class Repositories:
    def __init__(self):
        self.users = user_repository
        self.events = event_repository
        self.notifications = notification_repository
        self.stations = station_repository
        self.analytics = analytics_repository

    async def init_all(self):
        """Initialize all repositories"""
        try:
            # Initialize repositories that need async setup
            await self.stations.initialize()
            await self.analytics.initialize()
            
            # Test basic connections for others
            await self.users.collection.find_one()
            await self.events.collection.find_one()
            await self.notifications.collection.find_one()
            
            logger.info("All repositories initialized successfully")
        except Exception as e:
            logger.error(f"Repository initialization error: {e}")
            raise

# Create singleton instance
repositories = Repositories()

async def init_repositories():
    """Initialize all repositories"""
    try:
        await repositories.init_all()
        logger.info("All repositories initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing repositories: {e}")
        raise

# Global repositories dictionary
repositories_dict = {
    'station': station_repository,
    'analytics': analytics_repository
} 