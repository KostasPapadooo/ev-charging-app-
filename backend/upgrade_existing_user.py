#!/usr/bin/env python3
"""
Upgrade existing test user to premium subscription
"""
import asyncio
from app.repositories import repositories

async def upgrade_user_to_premium():
    """Upgrade existing user to premium"""
    try:
        # Initialize database connection
        await repositories.init_all()
        
        # Find existing test user
        user_email = "testuser1@example.com"  # From the logs
        existing_user = await repositories.users.find_by_email(user_email)
        
        if not existing_user:
            print(f"❌ User {user_email} not found!")
            return
        
        print(f"Found user: {existing_user.email}")
        print(f"Current subscription tier: {existing_user.subscription_tier}")
        
        if existing_user.subscription_tier == "premium":
            print("✅ User is already premium!")
            return
        
        # Update to premium
        updated_user = await repositories.users.update_by_id(
            str(existing_user.id), 
            {"subscription_tier": "premium"}
        )
        
        if updated_user:
            print("✅ User successfully upgraded to premium!")
            print(f"Email: {updated_user.email}")
            print(f"New subscription tier: {updated_user.subscription_tier}")
            print(f"ID: {updated_user.id}")
        else:
            print("❌ Failed to upgrade user")
        
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(upgrade_user_to_premium()) 