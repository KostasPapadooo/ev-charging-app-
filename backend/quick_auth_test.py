#!/usr/bin/env python3
"""
Quick authentication test
"""
import asyncio
import logging
import requests
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_auth():
    """Test authentication via HTTP requests"""
    
    # Test data
    email = "lolis@lula.com"
    password = "123456"  # Adjust if different
    
    logger.info(f"Testing authentication for: {email}")
    
    try:
        # 1. Test login
        login_data = {
            "username": email,
            "password": password
        }
        
        logger.info("1. Testing login...")
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result["access_token"]
            logger.info(f"✅ Login successful! Token received.")
            logger.info(f"User info: {login_result['user']['email']} (ID: {login_result['user']['id']})")
            
            # 2. Test /me endpoint
            logger.info("2. Testing /api/auth/me endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                me_result = me_response.json()
                logger.info(f"✅ /me endpoint successful!")
                logger.info(f"User: {me_result['email']} (ID: {me_result['id']})")
                logger.info("🎉 Authentication flow works correctly!")
            else:
                logger.error(f"❌ /me endpoint failed: {me_response.status_code}")
                logger.error(f"Response: {me_response.text}")
                
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        
if __name__ == "__main__":
    asyncio.run(test_auth()) 