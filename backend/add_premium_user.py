#!/usr/bin/env python3
"""
Add a premium test user to the database
"""
import asyncio
from getpass import getpass
from app.repositories import user_repository, repositories
from app.database.connection import connect_to_mongo, close_mongo_connection

async def add_premium_user():
    """
    Standalone script to create a new premium user.
    Prompts for email and password.
    """
    try:
        # 1. Connect to the database
        await connect_to_mongo()
        
        # 2. Initialize repositories (which depend on the DB connection)
        await repositories.init_all()

        print("--- Create a new premium user ---")
        email = input("Enter user's email: ")
        password = getpass("Enter user's password: ")
        first_name = input("Enter user's first name: ")
        last_name = input("Enter user's last name: ")

        # Check if user already exists
        existing_user = await user_repository.find_by_email(email)
        if existing_user:
            print(f"❌ User with email {email} already exists.")
            return

        # Create the user
        user = await user_repository.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone="+1234567890", # Default phone
            subscription_tier="premium"
        )
        
        print(f"✅ Premium user '{user.first_name} {user.last_name}' with email '{user.email}' created successfully!")
        print(f"User ID: {user.id}")

    except Exception as e:
        print(f"❌ Error creating premium user: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 3. Ensure the database connection is closed
        await close_mongo_connection()
        print("--- Script finished ---")

if __name__ == "__main__":
    asyncio.run(add_premium_user()) 