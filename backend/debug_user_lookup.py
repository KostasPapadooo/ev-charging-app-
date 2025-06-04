#!/usr/bin/env python3
"""
Debug user lookup to find why the user is not found
"""
import asyncio
import logging
from bson import ObjectId

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_user_lookup():
    """Debug user lookup in database"""
    try:
        # Initialize database connection
        from app.database.connection import connect_to_mongo, get_database
        await connect_to_mongo()
        
        db = get_database()
        users_collection = db.users
        
        # The problematic user ID from logs
        target_user_id = "684052c9d9de8c70981a6b06"
        target_email = "lolis@lula.com"
        
        logger.info("=== DATABASE DEBUG REPORT ===")
        
        # 1. Check total users in collection
        total_users = await users_collection.count_documents({})
        logger.info(f"Total users in collection: {total_users}")
        
        # 2. List all user emails and IDs
        logger.info("All users in database:")
        async for user_doc in users_collection.find({}, {"email": 1, "_id": 1}):
            logger.info(f"  - Email: {user_doc.get('email')}, ID: {user_doc.get('_id')}")
        
        # 3. Check if user exists by email
        logger.info(f"\n=== SEARCHING FOR USER: {target_email} ===")
        user_by_email = await users_collection.find_one({"email": target_email})
        if user_by_email:
            logger.info(f"✅ User found by email!")
            logger.info(f"  - ID: {user_by_email['_id']}")
            logger.info(f"  - ID type: {type(user_by_email['_id'])}")
            logger.info(f"  - ID str: {str(user_by_email['_id'])}")
            logger.info(f"  - Email: {user_by_email['email']}")
            
            # Check if this matches the target ID
            actual_id_str = str(user_by_email['_id'])
            if actual_id_str == target_user_id:
                logger.info(f"✅ ID matches the target ID: {target_user_id}")
            else:
                logger.warning(f"❌ ID MISMATCH!")
                logger.warning(f"  Expected: {target_user_id}")
                logger.warning(f"  Actual:   {actual_id_str}")
        else:
            logger.error(f"❌ User NOT found by email: {target_email}")
        
        # 4. Try to find user by the target ID in different formats
        logger.info(f"\n=== SEARCHING BY ID: {target_user_id} ===")
        
        # Try as string
        user_by_str = await users_collection.find_one({"_id": target_user_id})
        if user_by_str:
            logger.info(f"✅ User found by string ID")
        else:
            logger.info(f"❌ User NOT found by string ID")
        
        # Try as ObjectId
        try:
            target_object_id = ObjectId(target_user_id)
            user_by_obj_id = await users_collection.find_one({"_id": target_object_id})
            if user_by_obj_id:
                logger.info(f"✅ User found by ObjectId!")
                logger.info(f"  - Email: {user_by_obj_id['email']}")
            else:
                logger.info(f"❌ User NOT found by ObjectId")
        except Exception as e:
            logger.error(f"❌ Error converting to ObjectId: {e}")
        
        # 5. Test our repository method
        logger.info(f"\n=== TESTING REPOSITORY METHOD ===")
        from app.repositories import repositories
        await repositories.init_all()
        
        # Test by email
        repo_user_by_email = await repositories.users.find_by_email(target_email)
        if repo_user_by_email:
            logger.info(f"✅ Repository found user by email!")
            logger.info(f"  - ID: {repo_user_by_email.id}")
            logger.info(f"  - ID type: {type(repo_user_by_email.id)}")
            logger.info(f"  - ID str: {str(repo_user_by_email.id)}")
            
            # Test by ID
            repo_user_by_id = await repositories.users.get_by_id(str(repo_user_by_email.id))
            if repo_user_by_id:
                logger.info(f"✅ Repository found user by ID!")
                logger.info(f"  - Email: {repo_user_by_id.email}")
            else:
                logger.error(f"❌ Repository FAILED to find user by ID!")
        else:
            logger.error(f"❌ Repository FAILED to find user by email!")
        
        # 6. Test the exact ID from the logs
        logger.info(f"\n=== TESTING EXACT PROBLEMATIC ID ===")
        repo_user_by_problem_id = await repositories.users.get_by_id(target_user_id)
        if repo_user_by_problem_id:
            logger.info(f"✅ Repository found user by problematic ID!")
            logger.info(f"  - Email: {repo_user_by_problem_id.email}")
        else:
            logger.error(f"❌ Repository FAILED with problematic ID: {target_user_id}")
        
        logger.info("=== DEBUG REPORT COMPLETE ===")
        
    except Exception as e:
        logger.error(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_user_lookup()) 