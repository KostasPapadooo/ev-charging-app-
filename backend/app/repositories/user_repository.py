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
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            doc = await self.collection.find_one({"email": email})
            if doc:
                return self.model_class(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def create_user(self, email: str, password: str, first_name: str, last_name: str, **kwargs) -> User:
        """Create new user with hashed password"""
        try:
            hashed_password = pwd_context.hash(password)
            user_data = {
                "email": email,
                "password_hash": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                **kwargs
            }
            user = User(**user_data)
            return await self.create(user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_by_email(email)
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
    
    async def verify_user(self, user_id: str) -> Optional[User]:
        """Mark user as verified"""
        return await self.update_by_id(user_id, {"is_verified": True})

# Singleton instance
user_repository = UserRepository() 