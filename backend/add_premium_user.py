#!/usr/bin/env python3
"""
Add a premium test user to the database
"""
import asyncio
from app.repositories import repositories

async def add_premium_user():
    """Add a premium test user"""
    try:
        # Initialize database connection
        await repositories.init_all()
        
        # Check if user already exists
        existing_user = await repositories.users.find_by_email("premium@test.com")
        if existing_user:
            print("Premium test user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Subscription tier: {existing_user.subscription_tier}")
            return
        
        # Create premium user
        premium_user = await repositories.users.create_user(
            email="premium@test.com",
            password="testpass123",
            first_name="Premium",
            last_name="User",
            phone="+1234567890",
            subscription_tier="premium"
        )
        
        print("✅ Premium test user created successfully!")
        print(f"Email: {premium_user.email}")
        print(f"Password: testpass123")
        print(f"Subscription tier: {premium_user.subscription_tier}")
        print(f"ID: {premium_user.id}")
        
    except Exception as e:
        print(f"❌ Error creating premium user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_premium_user()) 