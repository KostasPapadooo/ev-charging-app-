from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.user import User
from passlib.context import CryptContext
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository(BaseRepository[User]):
    def __init__(self):
        # Lazy initialization
        self._collection = None
        self._model_class = User
    
    @property
    def collection(self):
        if self._collection is None:
            from app.database.connection import get_database
            db = get_database()
            self._collection = db.users
        return self._collection
    
    @property
    def model_class(self):
        return self._model_class
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            doc = await self.collection.find_one({"email": email})
            if doc:
                return self.model_class(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email - alias for get_user_by_email"""
        return await self.get_user_by_email(email)

    async def create_user(self, email: str, password: str, first_name: str, last_name: str, phone: str, subscription_tier: str) -> User:
        """Create new user with hashed password"""
        try:
            hashed_password = pwd_context.hash(password)
            user_data = {
                "email": email,
                "password_hash": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "subscription_tier": subscription_tier,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "favorite_stations": []  # Initialize empty favorite stations list
            }
            user = User(**user_data)
            return await self.create(user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_user_by_email(email)
            if user and pwd_context.verify(password, user.password_hash):
                # Update last login
                await self.update_by_id(user.id, {"last_login": datetime.utcnow()})
                return user
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            raise
    
    async def update_user_preferences(self, user_id: str, preferences: dict) -> Optional[User]:
        """Update user preferences"""
        return await self.update_by_id(user_id, {"preferences": preferences})

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login timestamp"""
        return await self.update_by_id(user_id, {"last_login": datetime.utcnow()})

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            from bson import ObjectId
            doc = None
            
            # First try as ObjectId if it's a valid ObjectId string
            if ObjectId.is_valid(user_id):
                obj_id = ObjectId(user_id)
                doc = await self.collection.find_one({"_id": obj_id})
                logger.debug(f"Tried ObjectId lookup for {user_id}: {'found' if doc else 'not found'}")
            
            # If not found and user_id is not already an ObjectId, try as string
            if doc is None and not ObjectId.is_valid(user_id):
                doc = await self.collection.find_one({"_id": user_id})
                logger.debug(f"Tried string lookup for {user_id}: {'found' if doc else 'not found'}")
            
            if doc:
                return self.model_class(**doc)
            
            logger.warning(f"User not found with ID: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise

    async def update_favorite_station(self, user_id: str, station_id: str, action: str) -> Optional[User]:
        """Add or remove a station from user's favorites"""
        try:
            from bson import ObjectId
            
            # Convert user_id to ObjectId if valid, otherwise use as string
            query_id = user_id
            if ObjectId.is_valid(user_id):
                query_id = ObjectId(user_id)
                logger.debug(f"Using ObjectId for user lookup: {user_id}")
            else:
                logger.debug(f"Using string for user lookup: {user_id}")

            update_operation = {
                'add': {'$addToSet': {'favorite_stations': station_id}},
                'remove': {'$pull': {'favorite_stations': station_id}}
            }.get(action)

            if not update_operation:
                raise ValueError(f"Invalid action: {action}")

            # First check if user exists before trying to update
            existing_user = await self.collection.find_one({"_id": query_id})
            if not existing_user:
                logger.error(f"User not found for ID: {user_id} (query_id: {query_id})")
                # Try alternative lookup method
                if ObjectId.is_valid(user_id):
                    # Try as string if ObjectId failed
                    existing_user = await self.collection.find_one({"_id": user_id})
                    if existing_user:
                        query_id = user_id
                        logger.info(f"Found user using string ID: {user_id}")
                else:
                    # Try as ObjectId if string failed
                    try:
                        alt_query_id = ObjectId(user_id)
                        existing_user = await self.collection.find_one({"_id": alt_query_id})
                        if existing_user:
                            query_id = alt_query_id
                            logger.info(f"Found user using ObjectId: {user_id}")
                    except:
                        pass
                
                if not existing_user:
                    logger.error(f"User definitely not found with any method for ID: {user_id}")
                    return None

            doc = await self.collection.find_one_and_update(
                {"_id": query_id},
                update_operation,
                return_document=True
            )

            # --- Analytics logging ---
            try:
                from app.repositories.analytics_repository import analytics_repository
                from datetime import datetime
                now = datetime.utcnow()
                await analytics_repository.log_event({
                    "event_type": "favorite_change",
                    "user_id": str(query_id),
                    "station_id": station_id,
                    "action": action,
                    "date": now.strftime("%Y-%m-%d"),
                    "computed_at": now,
                    "metrics": {
                        "total_sessions": 0,
                        "avg_session_duration": 0.0,
                        "peak_hours": [],
                        "utilization_rate": 0.0,
                        "revenue_eur": 0.0,
                        "unique_users": 0,
                        "busiest_connector_type": None
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to log favorite_change event: {e}")
            # ------------------------

            if doc:
                logger.info(f"Successfully updated favorite station for user {user_id}")
                return self.model_class(**doc)
            else:
                logger.error(f"Failed to update favorite station for user {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error updating favorite station for user {user_id}: {e}")
            raise

# Singleton instance
user_repository = UserRepository() 