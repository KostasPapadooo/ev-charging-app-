"""
Migration script to add favorite_stations field to existing users
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.connection import get_database

async def migrate_users_add_favorites():
    """Add favorite_stations field to all existing users who don't have it"""
    try:
        db = get_database()
        users_collection = db.users
        
        # Update all users who don't have the favorite_stations field
        result = await users_collection.update_many(
            {"favorite_stations": {"$exists": False}},
            {"$set": {"favorite_stations": []}}
        )
        
        print(f"Updated {result.modified_count} users with favorite_stations field")
        
        # Verify the update
        total_users = await users_collection.count_documents({})
        users_with_favorites = await users_collection.count_documents({"favorite_stations": {"$exists": True}})
        
        print(f"Total users: {total_users}")
        print(f"Users with favorite_stations field: {users_with_favorites}")
        
        if total_users == users_with_favorites:
            print("✅ Migration completed successfully! All users now have the favorite_stations field.")
        else:
            print("⚠️  Some users may still be missing the favorite_stations field.")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_users_add_favorites()) 