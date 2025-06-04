#!/usr/bin/env python3
"""
Debug script to test authentication flow
"""
import asyncio
import logging
from datetime import timedelta
from jose import jwt
from bson import ObjectId

from app.core.config import settings
from app.repositories import repositories
from app.api.auth import create_access_token, get_user_by_email

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_auth_flow():
    """Test the complete authentication flow"""
    try:
        # Initialize database connection first
        from app.database.connection import connect_to_mongo
        await connect_to_mongo()
        
        # Initialize repositories
        await repositories.init_all()
        
        # Test email from the user's message - CORRECTED EMAIL
        test_email = "lolis@lula.com"
        
        logger.info(f"Testing authentication for user: {test_email}")
        
        # 1. Test user lookup by email
        user = await get_user_by_email(test_email)
        if not user:
            logger.error(f"User {test_email} not found!")
            return
        
        logger.info(f"User found: {user.email} (ID: {user.id})")
        logger.info(f"User ID type: {type(user.id)}")
        logger.info(f"User ID str: {str(user.id)}")
        logger.info(f"User has favorite_stations: {'favorite_stations' in user.__dict__}")
        logger.info(f"Favorite stations: {getattr(user, 'favorite_stations', 'NOT FOUND')}")
        
        # 2. Test token creation
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": str(user.id),
                "subscription_tier": user.subscription_tier
            }, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token created successfully")
        logger.info(f"Secret key configured: {'*' * 10}")
        logger.info(f"Algorithm: {settings.algorithm}")
        logger.info(f"Token expires in: {settings.access_token_expire_minutes} minutes")
        
        # 3. Test token decoding
        payload = jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
        logger.info(f"Decoded token payload: {payload}")
        
        user_id_from_token = payload.get("user_id")
        logger.info(f"User ID from token: {user_id_from_token}")
        logger.info(f"User ID from token type: {type(user_id_from_token)}")
        
        # 4. Test user lookup by ID (this is where the error occurs)
        logger.info(f"Testing user lookup by ID: {user_id_from_token}")
        user_by_id = await repositories.users.get_by_id(user_id_from_token)
        
        if user_by_id:
            logger.info(f"✅ SUCCESS: User found by ID: {user_by_id.email}")
            logger.info(f"User data: ID={user_by_id.id}, Email={user_by_id.email}")
        else:
            logger.error(f"❌ FAILED: User not found by ID: {user_id_from_token}")
            
            # Try direct MongoDB query for debugging
            logger.info("Attempting direct MongoDB query...")
            from app.database.connection import get_database
            db = get_database()
            
            # Try with ObjectId
            try:
                obj_id = ObjectId(user_id_from_token)
                doc = await db.users.find_one({"_id": obj_id})
                if doc:
                    logger.info(f"✅ Direct query with ObjectId found user: {doc.get('email')}")
                else:
                    logger.error(f"❌ Direct query with ObjectId failed")
            except Exception as e:
                logger.error(f"❌ ObjectId conversion error: {e}")
            
            # Try with string
            doc = await db.users.find_one({"_id": user_id_from_token})
            if doc:
                logger.info(f"✅ Direct query with string found user: {doc.get('email')}")
            else:
                logger.error(f"❌ Direct query with string failed")
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_flow()) 