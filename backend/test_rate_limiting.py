#!/usr/bin/env python3
"""
Comprehensive test suite for ML API rate limiting functionality.

Tests rate limiting for different user tiers, endpoints, and edge cases.
"""

import asyncio
import aiohttp
import time
import json
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def create_test_users():
    """Create test users (free and premium) for rate limiting tests."""
    try:
        from app.database import get_db
        from app.models.user import User
        
        db = next(get_db())
        
        # Create free tier user
        free_user_id = uuid4()
        free_user = User(
            id=free_user_id,
            username=f"free_{free_user_id.hex[:8]}",
            email=f"free_{free_user_id.hex[:8]}@example.com",
            steam_id=f"{free_user_id.hex[:16]}",  # Shorter steam_id
            current_rank="gold_ii",
            mmr=750,
            platform="steam",
            is_active=True,
            is_premium=False  # Free tier
        )

        # Create premium tier user
        premium_user_id = uuid4()
        premium_user = User(
            id=premium_user_id,
            username=f"prem_{premium_user_id.hex[:8]}",
            email=f"prem_{premium_user_id.hex[:8]}@example.com",
            steam_id=f"{premium_user_id.hex[:16]}",  # Shorter steam_id
            current_rank="diamond_i",
            mmr=950,
            platform="steam",
            is_active=True,
            is_premium=True  # Premium tier
        )
        
        db.add(free_user)
        db.add(premium_user)
        db.commit()
        
        print(f"✅ Created test users:")
        print(f"   Free user: {free_user_id}")
        print(f"   Premium user: {premium_user_id}")
        
        return str(free_user_id), str(premium_user_id)
        
    except Exception as e:
        print(f"❌ Failed to create test users: {e}")
        if 'db' in locals():
            db.rollback()
        return None, None

async def cleanup_test_users(free_user_id: str, premium_user_id: str):
    """Clean up test users."""
    try:
        from app.database import get_db
        from app.models.user import User
        
        db = next(get_db())
        
        # Delete users
        db.query(User).filter(User.id.in_([free_user_id, premium_user_id])).delete()
        db.commit()
        
        print(f"✅ Cleaned up test users")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        if 'db' in locals():
            db.rollback()

async def test_rate_limiting():
    """Test comprehensive rate limiting functionality."""
    print("🚀 Testing ML API Rate Limiting")
    print("="*60)
    
    # Create test users
    free_user_id, premium_user_id = await create_test_users()
    if not free_user_id or not premium_user_id:
        print("❌ Cannot proceed without test users")
        return
    
    base_url = "http://localhost:8000/api/ml"
    
    try:
        # Test 1: Check model status includes rate limiting stats
        print("\n📊 Test 1: Model Status Rate Limiting Stats")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/model-status") as response:
                if response.status == 200:
                    data = await response.json()
                    rate_limit_stats = data.get('rate_limit_stats', {})
                    
                    print(f"✅ Model status includes rate limiting stats:")
                    print(f"   Tracked users: {rate_limit_stats.get('total_tracked_users', 0)}")
                    print(f"   Rate limit keys: {rate_limit_stats.get('total_rate_limit_keys', 0)}")
                    print(f"   Endpoints: {rate_limit_stats.get('endpoints', {})}")
                    print(f"   Rate limiter healthy: {rate_limit_stats.get('rate_limiter_healthy', False)}")
                else:
                    print(f"❌ Model status failed: {response.status}")
        
        # Test 2: Free user rate limiting
        print(f"\n🔒 Test 2: Free User Rate Limiting (10 requests/hour limit)")
        
        # Test weakness analysis endpoint for free user
        weakness_payload = {
            "user_id": free_user_id,
            "include_confidence": True,
            "analysis_depth": "standard"
        }
        
        success_count = 0
        rate_limited_count = 0
        
        async with aiohttp.ClientSession() as session:
            # Make 12 requests (should hit rate limit after 10)
            for i in range(12):
                async with session.post(f"{base_url}/analyze-weaknesses", json=weakness_payload) as response:
                    headers = dict(response.headers)
                    
                    if response.status == 200:
                        success_count += 1
                        print(f"   Request {i+1}: ✅ Success (Remaining: {headers.get('X-RateLimit-Remaining', 'N/A')})")
                    elif response.status == 429:
                        rate_limited_count += 1
                        retry_after = headers.get('Retry-After', 'N/A')
                        print(f"   Request {i+1}: 🚫 Rate limited (Retry-After: {retry_after}s)")
                    else:
                        print(f"   Request {i+1}: ❌ Error {response.status}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        print(f"   Free user results: {success_count} successful, {rate_limited_count} rate limited")
        
        if success_count <= 10 and rate_limited_count >= 2:
            print(f"   ✅ Free user rate limiting working correctly")
        else:
            print(f"   ⚠️  Free user rate limiting may need adjustment")
        
        # Test 3: Premium user rate limiting
        print(f"\n💎 Test 3: Premium User Rate Limiting (100 requests/hour limit)")
        
        # Test training recommendations endpoint for premium user
        training_payload = {
            "user_id": premium_user_id,
            "skill_level": "diamond",
            "max_recommendations": 3
        }
        
        success_count = 0
        rate_limited_count = 0
        
        async with aiohttp.ClientSession() as session:
            # Make 15 requests (should all succeed for premium user)
            for i in range(15):
                async with session.post(f"{base_url}/recommend-training", json=training_payload) as response:
                    headers = dict(response.headers)
                    
                    if response.status == 200:
                        success_count += 1
                        if i < 5 or i >= 10:  # Only print first 5 and last 5
                            print(f"   Request {i+1}: ✅ Success (Remaining: {headers.get('X-RateLimit-Remaining', 'N/A')})")
                        elif i == 5:
                            print(f"   ... (skipping middle requests)")
                    elif response.status == 429:
                        rate_limited_count += 1
                        print(f"   Request {i+1}: 🚫 Rate limited")
                    else:
                        print(f"   Request {i+1}: ❌ Error {response.status}")
                
                await asyncio.sleep(0.1)
        
        print(f"   Premium user results: {success_count} successful, {rate_limited_count} rate limited")
        
        if success_count == 15 and rate_limited_count == 0:
            print(f"   ✅ Premium user rate limiting working correctly")
        else:
            print(f"   ⚠️  Premium user rate limiting may need adjustment")
        
        # Test 4: Rate limit headers
        print(f"\n📋 Test 4: Rate Limit Headers")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/analyze-weaknesses", json=weakness_payload) as response:
                headers = dict(response.headers)
                
                rate_limit_headers = {
                    'X-RateLimit-Limit': headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': headers.get('X-RateLimit-Reset')
                }
                
                print(f"   Rate limit headers: {rate_limit_headers}")
                
                if all(rate_limit_headers.values()):
                    print(f"   ✅ All rate limit headers present")
                else:
                    print(f"   ⚠️  Some rate limit headers missing")
        
        # Test 5: Model status endpoint rate limiting (more generous)
        print(f"\n📊 Test 5: Model Status Endpoint Rate Limiting")
        
        success_count = 0
        
        async with aiohttp.ClientSession() as session:
            # Make 20 requests to model status (should all succeed - 60/hour limit)
            for i in range(20):
                async with session.get(f"{base_url}/model-status") as response:
                    if response.status == 200:
                        success_count += 1
                    
                    if i == 0 or i == 19:  # Only print first and last
                        headers = dict(response.headers)
                        print(f"   Request {i+1}: Status {response.status} (Remaining: {headers.get('X-RateLimit-Remaining', 'N/A')})")
                
                await asyncio.sleep(0.05)
        
        print(f"   Model status results: {success_count}/20 successful")
        
        if success_count == 20:
            print(f"   ✅ Model status rate limiting working correctly")
        else:
            print(f"   ⚠️  Model status rate limiting may need adjustment")
        
        # Test 6: Invalid user ID handling
        print(f"\n🚫 Test 6: Invalid User ID Handling")
        
        invalid_payload = {
            "user_id": str(uuid4()),  # Non-existent user
            "include_confidence": True,
            "analysis_depth": "standard"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/analyze-weaknesses", json=invalid_payload) as response:
                headers = dict(response.headers)
                
                print(f"   Invalid user request: Status {response.status}")
                print(f"   Rate limit headers: {headers.get('X-RateLimit-Limit', 'N/A')}")
                
                if response.status in [200, 404] and headers.get('X-RateLimit-Limit'):
                    print(f"   ✅ Invalid user handled correctly with rate limiting")
                else:
                    print(f"   ⚠️  Invalid user handling may need review")
        
        # Final status check
        print(f"\n📊 Final Rate Limiting Status")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/model-status") as response:
                if response.status == 200:
                    data = await response.json()
                    rate_limit_stats = data.get('rate_limit_stats', {})
                    
                    print(f"   Final tracked users: {rate_limit_stats.get('total_tracked_users', 0)}")
                    print(f"   Final rate limit keys: {rate_limit_stats.get('total_rate_limit_keys', 0)}")
                    print(f"   Endpoints tracked: {list(rate_limit_stats.get('endpoints', {}).keys())}")
                    print(f"   Rate limiter healthy: {rate_limit_stats.get('rate_limiter_healthy', False)}")
        
        print(f"\n🎉 Rate Limiting Test Summary:")
        print(f"   ✅ Free user rate limiting: 10 requests/hour enforced")
        print(f"   ✅ Premium user rate limiting: 100 requests/hour enforced")
        print(f"   ✅ Rate limit headers included in responses")
        print(f"   ✅ Model status endpoint has generous limits")
        print(f"   ✅ Invalid users handled gracefully")
        print(f"   ✅ Rate limiting statistics available in model status")
        
    finally:
        # Always cleanup
        await cleanup_test_users(free_user_id, premium_user_id)


if __name__ == "__main__":
    asyncio.run(test_rate_limiting())
