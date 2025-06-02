# from app.repositories.station_repository import station_repository
from app.repositories.user_repository import user_repository
from app.repositories.event_repository import event_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.station_repository import station_repository

class Repositories:
    def __init__(self):
        self.users = user_repository
        self.events = event_repository
        self.notifications = notification_repository
        self.stations = station_repository  # Instance, not module!
        # self.historical = HistoricalStationRepository()  # Will add later

    async def init_all(self):
        """Initialize all repositories"""
        try:
            # Test connections
            await self.users.collection.find_one()
            await self.stations.collection.find_one()
            await self.events.collection.find_one()
            await self.notifications.collection.find_one()
            # await self.historical.collection.find_one()  # Will add later
            print("All repositories initialized successfully")
        except Exception as e:
            print(f"Repository initialization error: {e}")
            raise

# Create singleton instance
repositories = Repositories()

async def init_repositories():
    """Initialize repositories - call this on startup"""
    await repositories.init_all() 